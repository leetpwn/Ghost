import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .models import NetworkConnection


class AlertEngine:
    """
    Learns normal process -> network owner relationships.

    Example relationship:

        firefox.exe -> Google LLC / AS15169

    Ghost alerts when a process later establishes a relationship
    with an ASN/organization it has never seen before.

    Important:
    "New" does NOT automatically mean "malicious".
    """

    def __init__(self):
        self._lock = threading.Lock()

        self._alerts: list[dict] = []

        self._known_relationships: set[str] = set()

        self._process_cooldowns: dict[str, float] = {}

        self._max_alerts = 100

        # Prevent multiple alerts for the same process in a short
        # period when an application contacts several new services.
        self._process_cooldown_seconds = 30

        backend_root = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        self._data_directory = (
            backend_root / "data"
        )

        self._baseline_file = (
            self._data_directory
            / "known_network_relationships.json"
        )

        self._data_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._baseline_exists = (
            self._baseline_file.exists()
        )

        self._load_baseline()


    # =========================================================
    # OBSERVATION
    # =========================================================

    def observe(
        self,
        connections: list[NetworkConnection],
    ) -> None:

        eligible_connections = [
            connection
            for connection in connections
            if self._eligible(connection)
        ]

        if not eligible_connections:
            return

        # -----------------------------------------------------
        # FIRST RUN
        #
        # The very first time Ghost runs, everything currently
        # connected becomes the initial baseline.
        #
        # We DO NOT alert on the user's existing environment.
        # -----------------------------------------------------

        if not self._baseline_exists:

            with self._lock:

                for connection in eligible_connections:

                    relationship = (
                        self._relationship_key(
                            connection
                        )
                    )

                    self._known_relationships.add(
                        relationship
                    )

                self._save_baseline_locked()

                self._baseline_exists = True

            print(
                "[Ghost AlertEngine] "
                "Initial network baseline created."
            )

            return


        # -----------------------------------------------------
        # NORMAL OBSERVATION
        # -----------------------------------------------------

        changed = False

        with self._lock:

            for connection in eligible_connections:

                relationship = (
                    self._relationship_key(
                        connection
                    )
                )

                if (
                    relationship
                    in self._known_relationships
                ):
                    continue

                # Once observed, remember the relationship even
                # if the alert itself is suppressed by cooldown.
                self._known_relationships.add(
                    relationship
                )

                changed = True

                process_identity = (
                    self._process_identity(
                        connection
                    )
                )

                if self._process_in_cooldown(
                    process_identity
                ):
                    continue

                alert = self._build_alert(
                    connection
                )

                self._alerts.append(
                    alert
                )

                if (
                    len(self._alerts)
                    > self._max_alerts
                ):
                    self._alerts = (
                        self._alerts[
                            -self._max_alerts:
                        ]
                    )

                self._process_cooldowns[
                    process_identity
                ] = time.monotonic()

            if changed:
                self._save_baseline_locked()


    # =========================================================
    # ALERT QUEUE
    # =========================================================

    def pop_alerts(
        self,
    ) -> list[dict]:

        with self._lock:

            alerts = list(
                self._alerts
            )

            self._alerts.clear()

            return alerts


    # =========================================================
    # ELIGIBILITY
    # =========================================================

    @staticmethod
    def _eligible(
        connection: NetworkConnection,
    ) -> bool:

        if (
            connection.endpoint_scope
            != "PUBLIC"
        ):
            return False

        if (
            connection.lifecycle
            != "ACTIVE"
        ):
            return False

        # Wait until ASN enrichment is complete.
        if (
            connection.enrichment_status
            != "OK"
        ):
            return False

        if not connection.organization:
            return False

        if not connection.process_name:
            return False

        return True


    # =========================================================
    # RELATIONSHIP IDENTIFICATION
    # =========================================================

    @staticmethod
    def _process_identity(
        connection: NetworkConnection,
    ) -> str:

        if connection.process_path:
            return (
                connection.process_path
                .strip()
                .lower()
            )

        return (
            connection.process_name
            or "unknown"
        ).strip().lower()


    def _relationship_key(
        self,
        connection: NetworkConnection,
    ) -> str:

        process = (
            self._process_identity(
                connection
            )
        )

        if connection.asn:
            owner = (
                f"asn:{connection.asn}"
            )

        else:
            owner = (
                "org:"
                + (
                    connection.organization
                    or "unknown"
                )
                .strip()
                .lower()
            )

        return (
            f"{process}|{owner}"
        )


    # =========================================================
    # COOLDOWN
    # =========================================================

    def _process_in_cooldown(
        self,
        process_identity: str,
    ) -> bool:

        previous = (
            self._process_cooldowns.get(
                process_identity
            )
        )

        if previous is None:
            return False

        elapsed = (
            time.monotonic()
            - previous
        )

        return (
            elapsed
            < self._process_cooldown_seconds
        )


    # =========================================================
    # ALERT CREATION
    # =========================================================

    def _build_alert(
        self,
        connection: NetworkConnection,
    ) -> dict:

        severity = (
            self._calculate_severity(
                connection
            )
        )

        return {
            "type":
                "NEW_NETWORK_RELATIONSHIP",

            "severity":
                severity,

            "title":
                "New outbound connection",

            "process_name":
                connection.process_name
                or "Unknown process",

            "process_path":
                connection.process_path
                or "",

            "pid":
                connection.pid,

            "remote_ip":
                connection.remote_ip,

            "remote_port":
                connection.remote_port,

            "organization":
                connection.organization
                or "Unknown owner",

            "isp":
                connection.isp
                or "",

            "domain":
                connection.domain
                or "",

            "asn":
                connection.asn,

            "message":
                self._build_message(
                    connection
                ),

            "virustotal_url":
                connection.virustotal_url
                or "",

            "created_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }


    @staticmethod
    def _calculate_severity(
        connection: NetworkConnection,
    ) -> str:

        # Missing executable attribution deserves
        # more attention.
        if not connection.process_path:
            return "WARNING"

        # Unusual destination ports deserve more
        # attention than standard web traffic.
        common_ports = {
            80,
            443,
            53,
            123,
        }

        if (
            connection.remote_port
            not in common_ports
        ):
            return "WARNING"

        return "NOTICE"


    @staticmethod
    def _build_message(
        connection: NetworkConnection,
    ) -> str:

        owner = (
            connection.organization
            or "Unknown owner"
        )

        asn_text = ""

        if connection.asn:
            asn_text = (
                f" (AS{connection.asn})"
            )

        return (
            f"{connection.process_name} connected to "
            f"{owner}{asn_text}"
        )


    # =========================================================
    # PERSISTENCE
    # =========================================================

    def _load_baseline(
        self,
    ) -> None:

        if not self._baseline_file.exists():
            return

        try:

            with self._baseline_file.open(
                "r",
                encoding="utf-8",
            ) as file:

                payload = json.load(
                    file
                )

            relationships = (
                payload.get(
                    "known_relationships",
                    [],
                )
            )

            self._known_relationships = set(
                relationships
            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:

            print(
                "[Ghost AlertEngine] "
                f"Could not load baseline: {error}"
            )

            self._known_relationships = set()


    def _save_baseline_locked(
        self,
    ) -> None:

        payload = {
            "version": 1,

            "known_relationships":
                sorted(
                    self._known_relationships
                ),
        }

        temporary_file = (
            self._baseline_file
            .with_suffix(".tmp")
        )

        try:

            with temporary_file.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    payload,
                    file,
                    indent=2,
                )

            temporary_file.replace(
                self._baseline_file
            )

        except OSError as error:

            print(
                "[Ghost AlertEngine] "
                f"Could not save baseline: {error}"
            )


alert_engine = AlertEngine()