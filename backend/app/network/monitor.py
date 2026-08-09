import asyncio
import ipaddress
import socket
import threading
from dataclasses import replace
from typing import Optional

import psutil

from .alert_engine import alert_engine
from .models import NetworkConnection
from .reputation import reputation_service


class NetworkMonitor:
    def __init__(
        self,
        poll_interval_seconds: float = 2.0,
    ):
        self.poll_interval_seconds = (
            poll_interval_seconds
        )

        self._connections: list[
            NetworkConnection
        ] = []

        self._lock = threading.Lock()

        self._running = False

        self._enrichment_task: Optional[
            asyncio.Task
        ] = None


    # =========================================================
    # MONITOR
    # =========================================================

    async def start(self) -> None:

        if self._running:
            return

        self._running = True

        while self._running:

            try:

                connections = (
                    await asyncio.to_thread(
                        self._collect_connections
                    )
                )

                # Immediately publish socket information.
                with self._lock:
                    self._connections = (
                        connections
                    )

                public_ips = list({
                    connection.remote_ip
                    for connection in connections
                    if (
                        connection.endpoint_scope
                        == "PUBLIC"
                        and connection.remote_ip
                    )
                })

                # ASN lookup runs independently of
                # socket collection.
                if (
                    public_ips
                    and (
                        self._enrichment_task
                        is None
                        or
                        self._enrichment_task.done()
                    )
                ):

                    self._enrichment_task = (
                        asyncio.create_task(
                            self._enrich_public_ips(
                                public_ips
                            )
                        )
                    )

            except Exception as exc:

                print(
                    "[Ghost NetworkMonitor] "
                    f"{exc}"
                )

            await asyncio.sleep(
                self.poll_interval_seconds
            )


    def stop(self) -> None:

        self._running = False

        if (
            self._enrichment_task
            is not None
            and
            not self._enrichment_task.done()
        ):

            self._enrichment_task.cancel()


    # =========================================================
    # SNAPSHOT
    # =========================================================

    def get_connections(
        self,
    ) -> list[NetworkConnection]:

        with self._lock:

            return list(
                self._connections
            )


    # =========================================================
    # SOCKET COLLECTION
    # =========================================================

    def _collect_connections(
        self,
    ) -> list[NetworkConnection]:

        results: list[
            NetworkConnection
        ] = []

        connections = (
            psutil.net_connections(
                kind="inet"
            )
        )

        for conn in connections:

            if not conn.raddr:
                continue

            (
                local_ip,
                local_port,
            ) = self._address_parts(
                conn.laddr
            )

            (
                remote_ip,
                remote_port,
            ) = self._address_parts(
                conn.raddr
            )

            if not remote_ip:
                continue

            protocol = (
                self._get_protocol(
                    conn.type
                )
            )

            endpoint_scope = (
                self._classify_ip(
                    remote_ip
                )
            )

            lifecycle = (
                self._classify_lifecycle(
                    protocol=protocol,
                    status=conn.status,
                )
            )

            pid = None

            if (
                conn.pid is not None
                and conn.pid > 0
            ):
                pid = conn.pid

            process_name = None
            process_path = None

            if pid is not None:

                (
                    process_name,
                    process_path,
                ) = (
                    self._get_process_info(
                        pid
                    )
                )

            connection = (
                NetworkConnection(
                    protocol=protocol,

                    local_ip=local_ip,
                    local_port=local_port,

                    remote_ip=remote_ip,
                    remote_port=remote_port,

                    status=(
                        conn.status
                        or "NONE"
                    ),

                    pid=pid,

                    process_name=
                        process_name,

                    process_path=
                        process_path,

                    endpoint_scope=
                        endpoint_scope,

                    lifecycle=
                        lifecycle,

                    asn=None,

                    organization=None,

                    isp=None,

                    domain=None,

                    enrichment_status=(
                        "PENDING"
                        if (
                            endpoint_scope
                            == "PUBLIC"
                        )
                        else
                        "NOT_APPLICABLE"
                    ),
                )
            )

            results.append(
                connection
            )

        return results


    # =========================================================
    # ASN ENRICHMENT
    # =========================================================

    async def _enrich_public_ips(
        self,
        public_ips: list[str],
    ) -> None:

        try:

            enrichments = (
                await asyncio.to_thread(
                    reputation_service.lookup_many,
                    public_ips,
                )
            )

        except asyncio.CancelledError:
            return

        except Exception as exc:

            print(
                "[Ghost ReputationService] "
                f"{exc}"
            )

            return


        with self._lock:

            enriched_connections: list[
                NetworkConnection
            ] = []

            for connection in self._connections:

                if (
                    connection.endpoint_scope
                    != "PUBLIC"
                ):

                    enriched_connections.append(
                        connection
                    )

                    continue

                enrichment = (
                    enrichments.get(
                        connection.remote_ip
                    )
                )

                if not enrichment:

                    enriched_connections.append(
                        connection
                    )

                    continue

                enriched_connection = replace(
                    connection,

                    asn=
                        enrichment.get(
                            "asn"
                        ),

                    organization=
                        enrichment.get(
                            "organization"
                        ),

                    isp=
                        enrichment.get(
                            "isp"
                        ),

                    domain=
                        enrichment.get(
                            "domain"
                        ),

                    enrichment_status=
                        enrichment.get(
                            "enrichment_status",
                            "UNAVAILABLE",
                        ),
                )

                enriched_connections.append(
                    enriched_connection
                )

            self._connections = (
                enriched_connections
            )

            alert_snapshot = list(
                self._connections
            )


        # Decision layer runs AFTER enrichment.
        #
        # This is intentionally outside the monitor lock.
        try:

            alert_engine.observe(
                alert_snapshot
            )

        except Exception as exc:

            print(
                "[Ghost AlertEngine] "
                f"{exc}"
            )


    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _address_parts(
        address,
    ) -> tuple[str, int]:

        if not address:
            return "", 0

        try:

            return (
                address.ip,
                address.port,
            )

        except AttributeError:

            return (
                address[0],
                address[1],
            )


    @staticmethod
    def _get_protocol(
        socket_type: int,
    ) -> str:

        if (
            socket_type
            == socket.SOCK_STREAM
        ):
            return "TCP"

        if (
            socket_type
            == socket.SOCK_DGRAM
        ):
            return "UDP"

        return "UNKNOWN"


    @staticmethod
    def _classify_ip(
        ip: str,
    ) -> str:

        try:

            normalized_ip = (
                ip.split(
                    "%",
                    1,
                )[0]
            )

            address = (
                ipaddress.ip_address(
                    normalized_ip
                )
            )

        except ValueError:

            return "PRIVATE_LAN"

        if address.is_loopback:
            return "LOOPBACK"

        if not address.is_global:
            return "PRIVATE_LAN"

        return "PUBLIC"


    @staticmethod
    def _classify_lifecycle(
        protocol: str,
        status: str,
    ) -> str:

        normalized_status = (
            status or "NONE"
        ).upper()

        if protocol == "UDP":
            return "ACTIVE"

        active_states = {
            "ESTABLISHED",
            "SYN_SENT",
            "SYN_RECV",
        }

        closing_states = {
            "FIN_WAIT1",
            "FIN_WAIT2",
            "CLOSE_WAIT",
            "CLOSING",
            "LAST_ACK",
        }

        stale_states = {
            "TIME_WAIT",
            "CLOSED",
        }

        if (
            normalized_status
            in active_states
        ):
            return "ACTIVE"

        if (
            normalized_status
            in closing_states
        ):
            return "CLOSING"

        if (
            normalized_status
            in stale_states
        ):
            return "CLOSED_STALE"

        return "ACTIVE"


    @staticmethod
    def _get_process_info(
        pid: int,
    ) -> tuple[
        Optional[str],
        Optional[str],
    ]:

        try:

            process = (
                psutil.Process(
                    pid
                )
            )

            name = process.name()

            try:

                path = process.exe()

            except (
                psutil.AccessDenied,
                psutil.NoSuchProcess,
            ):

                path = None

            return (
                name,
                path,
            )

        except (
            psutil.AccessDenied,
            psutil.NoSuchProcess,
            psutil.ZombieProcess,
        ):

            return (
                None,
                None,
            )