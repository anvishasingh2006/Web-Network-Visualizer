import asyncio
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    BeautifulSoup = None

import httpx

from security import RobotGuard, validate_url_safety


def normalize_url(url: str) -> str:
    """
    Normalizes a URL by stripping fragments, trailing slashes,
    and converting schemes/hostnames to lower case.
    """
    if not isinstance(url, str):
        return ""

    candidate = url.strip()
    if not candidate:
        return ""

    parsed = urlparse(candidate)
    # Strip fragments (#section) and normalize path
    path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.params,
        parsed.query,
        ""  # Drop fragment
    ))
    return normalized


@dataclass
class CrawlResult:
    start_url: str
    nodes: set[str] = field(default_factory=set)
    edges: list[tuple[str, str]] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


class AsyncCrawler:
    def __init__(
        self,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 50,
        max_concurrency: int = 5,
        user_agent: str = "WebNetworkVisualiser/1.0"
    ):
        self.start_url = normalize_url(start_url)
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.robot_guard = RobotGuard(user_agent=user_agent)
        
        parsed = urlparse(self.start_url)
        self.target_domain = parsed.netloc

        self.visited: set[str] = set()
        self.result = CrawlResult(start_url=self.start_url)
        self.queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()

    def _is_same_domain(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.lower() == self.target_domain.lower()

    def _extract_links_from_html(self, html: str, base_url: str) -> list[str]:
        """Extract same-domain links with a built-in fallback when bs4 is unavailable."""
        extracted_links: list[str] = []

        if BeautifulSoup is not None:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all("a", href=True):
                raw_href = tag["href"].strip()
                absolute_url = normalize_url(urljoin(base_url, raw_href))
                if absolute_url.startswith(("http://", "https://")) and self._is_same_domain(absolute_url):
                    extracted_links.append(absolute_url)
            return extracted_links

        href_pattern = re.compile(r"<a\b[^>]*\bhref\s*=\s*['\"]?([^'\"\s>#]+)", re.IGNORECASE)
        for match in href_pattern.finditer(html):
            raw_href = match.group(1).strip()
            absolute_url = normalize_url(urljoin(base_url, raw_href))
            if absolute_url.startswith(("http://", "https://")) and self._is_same_domain(absolute_url):
                extracted_links.append(absolute_url)
        return extracted_links

    async def _fetch_and_parse(self, client: httpx.AsyncClient, url: str) -> list[str]:
        """Fetches HTML and extracts valid same-domain links."""
        # 1. Check SSRF safety
        if not await validate_url_safety(url):
            self.result.errors[url] = "Blocked by SSRF security guard"
            return []

        # 2. Check robots.txt compliance
        if not await self.robot_guard.can_fetch(client, url):
            self.result.errors[url] = "Disallowed by robots.txt"
            return []

        try:
            async with self.semaphore:
                response = await client.get(url, timeout=10.0, follow_redirects=True)

            if response.status_code != 200 or "text/html" not in response.headers.get("content-type", ""):
                return []

            return self._extract_links_from_html(response.text, url)

        except Exception as err:
            self.result.errors[url] = str(err)
            return []

    async def crawl(self) -> CrawlResult:
        """Main BFS crawling loop using asyncio workers."""
        await self.queue.put((self.start_url, 0))
        self.visited.add(self.start_url)
        self.result.nodes.add(self.start_url)

        headers = {"User-Agent": self.robot_guard.user_agent}

        async with httpx.AsyncClient(headers=headers, verify=True) as client:
            while not self.queue.empty() and len(self.visited) < self.max_pages:
                current_url, depth = await self.queue.get()

                if depth >= self.max_depth:
                    self.queue.task_done()
                    continue

                links = await self._fetch_and_parse(client, current_url)

                for link in links:
                    if link in self.visited:
                        self.result.edges.append((current_url, link))
                        continue

                    if len(self.visited) < self.max_pages:
                        self.result.nodes.add(link)
                        self.result.edges.append((current_url, link))
                        self.visited.add(link)
                        await self.queue.put((link, depth + 1))

                self.queue.task_done()

        return self.result