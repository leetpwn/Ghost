from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class NetworkConnection:
    protocol: str

    local_ip: str
    local_port: int

    remote_ip: str
    remote_port: int

    status: str

    pid: Optional[int]
    process_name: Optional[str]
    process_path: Optional[str]

    endpoint_scope: str
    lifecycle: str

    # Network ownership / ASN enrichment
    asn: Optional[int]
    organization: Optional[str]
    isp: Optional[str]
    domain: Optional[str]

    enrichment_status: str

    @property
    def virustotal_url(
        self,
    ) -> Optional[str]:
        """
        VirusTotal lookups are only useful for public IP addresses.
        """

        if self.endpoint_scope != "PUBLIC":
            return None

        return (
            "https://www.virustotal.com/"
            "gui/ip-address/"
            f"{self.remote_ip}"
        )

    def to_dict(
        self,
    ) -> dict:
        """
        Convert the connection into the JSON-ready structure
        returned by FastAPI.
        """

        data = asdict(self)

        data["virustotal_url"] = (
            self.virustotal_url
        )

        return data