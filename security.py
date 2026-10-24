import asyncio
import ipaddress
import socket
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import httpx

# Private and reserved IP networks (SSRF prevention)
RESERVED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


async def is_safe_ip(ip_str: str) -> bool:
    """Check if an IP address belongs to any reserved/private range."""
    if not isinstance(ip_str, str):
        return False

    candidate = ip_str.strip()
    if not candidate:
        return False

    try:
        ip = ipaddress.ip_address(candidate)
        return not any(ip in net for net in RESERVED_NETWORKS)
    except (TypeError, ValueError):
        return False


async def validate_url_safety(url: str) -> bool:
    """
    Validates URL scheme and resolves hostname to IP to ensure it's not pointing
    to a private or internal network address (SSRF mitigation).
    """
    if not isinstance(url, str):
        return False

    candidate = url.strip()
    if not candidate:
        return False

    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    hostname = hostname.strip().lower()

    try:
        loop = asyncio.get_running_loop()
        # Non-blocking DNS resolution
        addr_info = await loop.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)

        for family, _, _, _, sockaddr in addr_info:
            ip = sockaddr[0]
            if not await is_safe_ip(ip):
                return False
        return True
    except (socket.gaierror, OSError, ValueError):
        return False


class RobotGuard:
    """Fetches and respects robots.txt rules for a target domain."""

    def __init__(self, user_agent: str = "WebNetworkVisualiser/1.0"):
        self.user_agent = user_agent
        self.parsers: dict[str, RobotFileParser] = {}

    async def can_fetch(self, client: httpx.AsyncClient, url: str) -> bool:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain not in self.parsers:
            robot_url = f"{domain}/robots.txt"
            parser = RobotFileParser()
            try:
                response = await client.get(robot_url, timeout=5.0)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                else:
                    parser.allow_all = True
            except Exception:
                parser.allow_all = True

            self.parsers[domain] = parser

        return self.parsers[domain].can_fetch(self.user_agent, url)