"""Web plugin.

Provides async ``web_fetch`` and ``web_search`` skills, plus an
``extract_metadata`` transformer for parsing HTML meta tags.

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import re
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, ConfigScope, RiskLevel


class ExtractMetadataTransformer(ChainableTransformer[str, dict]):
    """Extract metadata (title, description, OG tags) from an HTML string using regex."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        metadata: Dict[str, Any] = {}

        # Title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", value, re.DOTALL | re.IGNORECASE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # Meta description
        desc_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
            value,
            re.IGNORECASE,
        )
        if not desc_match:
            desc_match = re.search(
                r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']',
                value,
                re.IGNORECASE,
            )
        if desc_match:
            metadata["description"] = desc_match.group(1).strip()

        # Open Graph tags
        og_tags: Dict[str, str] = {}
        for match in re.finditer(
            r'<meta[^>]+property=["\']og:(\w+)["\'][^>]+content=["\'](.*?)["\']',
            value,
            re.IGNORECASE,
        ):
            og_tags[match.group(1)] = match.group(2).strip()
        # Also match reversed attribute order
        for match in re.finditer(
            r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:(\w+)["\']',
            value,
            re.IGNORECASE,
        ):
            og_tags[match.group(2)] = match.group(1).strip()
        if og_tags:
            metadata["og"] = og_tags

        # Canonical URL
        canonical_match = re.search(
            r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\'](.*?)["\']',
            value,
            re.IGNORECASE,
        )
        if canonical_match:
            metadata["canonical"] = canonical_match.group(1).strip()

        return metadata


# ── Skills ─────────────────────────────────────────────────────────────────

@skill(
    name="web_fetch",
    display_name="Fetch URL",
    description="Fetch the content of a URL (async).",
    category="web",
    tags=["web", "fetch", "http"],
    icon="globe",
    risk_level=RiskLevel.SAFE,
    group="Web",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="timeout",
            display_name="Timeout",
            description="Request timeout.",
            type="number",
            default=30,
            min=1,
            max=120,
            unit="seconds",
        ),
        ConfigParam(
            name="user_agent",
            display_name="User Agent",
            description="User-Agent header sent with requests.",
            type="string",
            default="Tukuy/0.1",
            placeholder="Tukuy/0.1",
        ),
    ],
)
async def web_fetch(url: str, headers: dict = None, timeout: int = 30) -> dict:
    """Fetch a URL and return its text content."""
    check_host(url)
    try:
        import httpx
    except ImportError:
        return {
            "url": url,
            "error": "httpx is required. Install with: pip install httpx",
            "success": False,
        }

    request_headers = {"User-Agent": "Tukuy/0.1 (+https://github.com/jhd3197/tukuy)"}
    if headers:
        request_headers.update(headers)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, headers=request_headers, timeout=timeout)
        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "content": response.text,
            "content_type": response.headers.get("content-type", ""),
            "success": response.is_success,
        }


@skill(
    name="web_search",
    display_name="Web Search",
    description="Search DuckDuckGo HTML (no API key required) and return results (async).",
    category="web",
    tags=["web", "search"],
    icon="search",
    risk_level=RiskLevel.SAFE,
    group="Web",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="max_results",
            display_name="Max Results",
            description="Maximum number of search results to return.",
            type="number",
            default=5,
            min=1,
            max=50,
        ),
        ConfigParam(
            name="timeout",
            display_name="Timeout",
            description="Search request timeout.",
            type="number",
            default=15,
            min=1,
            max=60,
            unit="seconds",
        ),
        ConfigParam(
            name="blocked_domains",
            display_name="Blocked Domains",
            description="Domains to exclude from search results.",
            type="string[]",
            default=[],
            item_placeholder="e.g. example.com",
        ),
    ],
)
async def web_search(query: str, max_results: int = 5) -> dict:
    """Search DuckDuckGo HTML and parse results."""
    try:
        import httpx
    except ImportError:
        return {
            "query": query,
            "error": "httpx is required. Install with: pip install httpx",
            "results": [],
            "success": False,
        }

    search_url = "https://html.duckduckgo.com/html/"
    request_headers = {"User-Agent": "Tukuy/0.1 (+https://github.com/jhd3197/tukuy)"}

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(
            search_url,
            data={"q": query},
            headers=request_headers,
            timeout=15,
        )

        if not response.is_success:
            return {
                "query": query,
                "error": f"Search returned status {response.status_code}",
                "results": [],
                "success": False,
            }

        html = response.text
        results: List[Dict[str, str]] = []

        # Parse result snippets from DuckDuckGo HTML
        for match in re.finditer(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
            r'.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            html,
            re.DOTALL,
        ):
            if len(results) >= max_results:
                break
            href = match.group(1)
            title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            snippet = re.sub(r"<[^>]+>", "", match.group(3)).strip()
            results.append({"url": href, "title": title, "snippet": snippet})

        return {
            "query": query,
            "results": results,
            "count": len(results),
            "success": True,
        }


class WebPlugin(TransformerPlugin):
    """Plugin providing web fetch/search skills and metadata extraction."""

    def __init__(self):
        super().__init__("web")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "extract_metadata": lambda _: ExtractMetadataTransformer("extract_metadata"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "web_fetch": web_fetch.__skill__,
            "web_search": web_search.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="web",
            display_name="Web",
            description="Fetch web pages, search the internet, and extract metadata.",
            icon="globe",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
