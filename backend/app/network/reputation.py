import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


class ReputationService:
    """
    Enrich public IP addresses with network ownership information.

    Important:
    This is identity/context enrichment, NOT malware detection.

    Results are cached for the lifetime of Ghost so we do not query
    the enrichment provider every time NetworkMonitor polls.
    """

    API_BASE = "https://ipwho.is/"

    def __init__(
        self,
        timeout_seconds: float = 3.0,
        max_workers: int = 8,
    ):
        self.timeout_seconds = timeout_seconds
        self.max_workers = max_workers

        self._cache: dict[str, dict] = {}
        self._lock = threading.Lock()

    def lookup_many(
        self,
        ips: list[str],
    ) -> dict[str, dict]:

        unique_ips = list(
            dict.fromkeys(ips)
        )

        if not unique_ips:
            return {}

        missing_ips: list[str] = []

        with self._lock:
            for ip in unique_ips:
                if ip not in self._cache:
                    missing_ips.append(ip)

        if missing_ips:
            worker_count = min(
                self.max_workers,
                len(missing_ips),
            )

            with ThreadPoolExecutor(
                max_workers=worker_count
            ) as executor:

                future_to_ip = {
                    executor.submit(
                        self._fetch,
                        ip,
                    ): ip
                    for ip in missing_ips
                }

                for future in as_completed(
                    future_to_ip
                ):
                    ip = future_to_ip[
                        future
                    ]

                    try:
                        result = (
                            future.result()
                        )

                    except Exception:
                        result = (
                            self._empty_result(
                                "FAILED"
                            )
                        )

                    with self._lock:
                        self._cache[
                            ip
                        ] = result

        results: dict[str, dict] = {}

        with self._lock:
            for ip in unique_ips:
                results[ip] = dict(
                    self._cache.get(
                        ip,
                        self._empty_result(
                            "UNAVAILABLE"
                        ),
                    )
                )

        return results

    def _fetch(
        self,
        ip: str,
    ) -> dict:

        encoded_ip = urllib.parse.quote(
            ip,
            safe=":",
        )

        url = (
            f"{self.API_BASE}"
            f"{encoded_ip}"
            "?fields="
            "success,"
            "message,"
            "connection"
        )

        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": "Ghost/0.4",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:

                payload = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
        ):
            return self._empty_result(
                "FAILED"
            )

        if not payload.get(
            "success",
            False,
        ):
            return self._empty_result(
                "FAILED"
            )

        connection = payload.get(
            "connection"
        ) or {}

        return {
            "asn":
                connection.get("asn"),

            "organization":
                connection.get("org"),

            "isp":
                connection.get("isp"),

            "domain":
                connection.get("domain"),

            "enrichment_status":
                "OK",
        }

    @staticmethod
    def _empty_result(
        status: str,
    ) -> dict:

        return {
            "asn": None,
            "organization": None,
            "isp": None,
            "domain": None,
            "enrichment_status": status,
        }


reputation_service = ReputationService()