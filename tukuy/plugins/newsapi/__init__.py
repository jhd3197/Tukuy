"""NewsAPI plugin.

Provides async news headline search, article search, and source listing
via the NewsAPI v2 (free tier: 100 requests/day).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import datetime
import os
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://newsapi.org/v2"


def _get_api_key() -> Optional[str]:
    """Read the NewsAPI key from the environment."""
    return os.environ.get("NEWSAPI_API_KEY")


def _relative_time(iso_datetime_str: Optional[str]) -> str:
    """Convert an ISO 8601 datetime string to a human-readable relative time.

    Returns strings like ``"2 hours ago"``, ``"yesterday"``, ``"3 days ago"``.
    Handles ``None`` and malformed values gracefully.
    """
    if not iso_datetime_str:
        return "unknown"
    try:
        # Strip trailing 'Z' and parse
        cleaned = iso_datetime_str.replace("Z", "+00:00")
        published = datetime.datetime.fromisoformat(cleaned)
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now - published

        seconds = int(delta.total_seconds())
        if seconds < 0:
            return "just now"
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        days = hours // 24
        if days == 1:
            return "yesterday"
        if days < 30:
            return f"{days} days ago"
        months = days // 30
        if months == 1:
            return "1 month ago"
        if months < 12:
            return f"{months} months ago"
        years = months // 12
        return f"{years} year{'s' if years != 1 else ''} ago"
    except (ValueError, TypeError):
        return "unknown"


def _parse_article(raw: dict) -> dict:
    """Normalise a NewsAPI article object into a clean dict."""
    source = raw.get("source") or {}
    published_at = raw.get("publishedAt")
    return {
        "title": raw.get("title") or "",
        "source_name": source.get("name") or "",
        "description": raw.get("description") or "",
        "url": raw.get("url") or "",
        "image_url": raw.get("urlToImage") or "",
        "published_at": published_at or "",
        "published_relative": _relative_time(published_at),
        "author": raw.get("author") or "",
    }


class FormatArticleTransformer(ChainableTransformer[dict, str]):
    """Format a news article dict into a summary line.

    Output format: ``"Source Name -- Title here -- 2h ago -- url"``
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "title" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        source = value.get("source_name", "")
        title = value.get("title", "")
        relative = value.get("published_relative", "")
        url = value.get("url", "")
        parts = [source, title, relative, url]
        return " \u2014 ".join(p for p in parts if p)


# -- Skills -----------------------------------------------------------------


@skill(
    name="news_headlines",
    display_name="Top Headlines",
    description=(
        "Get top news headlines by country and category via NewsAPI v2 "
        "(requires NEWSAPI_API_KEY env var). Free tier: 100 requests/day, "
        "articles up to 24 h old, max 100 results."
    ),
    category="news",
    tags=["news", "headlines", "top", "breaking"],
    icon="newspaper",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="NewsAPI Key",
            description="NewsAPI key. Falls back to NEWSAPI_API_KEY env var.",
            type="secret",
            placeholder="your-newsapi-key",
        ),
        ConfigParam(
            name="timeout",
            display_name="Timeout",
            description="Request timeout.",
            type="number",
            default=15,
            min=1,
            max=60,
            unit="seconds",
        ),
    ],
)
async def news_headlines(
    country: str = "us",
    category: str = "",
    query: str = "",
    page_size: int = 5,
) -> dict:
    """Fetch top headlines, optionally filtered by country, category, or query."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "NEWSAPI_API_KEY env var is required. Get a free key at https://newsapi.org",
            "success": False,
        }

    endpoint = f"{_BASE_URL}/top-headlines"
    params: Dict[str, Any] = {
        "country": country,
        "pageSize": page_size,
    }
    if category:
        params["category"] = category
    if query:
        params["q"] = query

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            endpoint,
            params=params,
            headers={"X-Api-Key": api_key},
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        if data.get("status") == "error":
            return {"error": data.get("message", "Unknown API error"), "code": data.get("code"), "success": False}
        raw_articles = data.get("articles", [])
        articles = [_parse_article(a) for a in raw_articles]
        return {
            "articles": articles,
            "totalResults": data.get("totalResults", 0),
            "count": len(articles),
            "country": country,
            "category": category or "all",
            "success": True,
        }


@skill(
    name="news_search",
    display_name="Search News",
    description=(
        "Search all news articles by keyword via NewsAPI v2 "
        "(requires NEWSAPI_API_KEY env var). Free tier: 100 requests/day, "
        "articles up to 24 h old, max 100 results."
    ),
    category="news",
    tags=["news", "search", "articles", "query"],
    icon="newspaper",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="NewsAPI Key",
            description="NewsAPI key. Falls back to NEWSAPI_API_KEY env var.",
            type="secret",
            placeholder="your-newsapi-key",
        ),
        ConfigParam(
            name="timeout",
            display_name="Timeout",
            description="Request timeout.",
            type="number",
            default=15,
            min=1,
            max=60,
            unit="seconds",
        ),
    ],
)
async def news_search(
    query: str,
    from_date: str = "",
    to_date: str = "",
    sort_by: str = "relevancy",
    language: str = "en",
    page_size: int = 5,
) -> dict:
    """Search all articles matching the given query."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "NEWSAPI_API_KEY env var is required. Get a free key at https://newsapi.org",
            "success": False,
        }

    endpoint = f"{_BASE_URL}/everything"
    params: Dict[str, Any] = {
        "q": query,
        "sortBy": sort_by,
        "language": language,
        "pageSize": page_size,
    }
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            endpoint,
            params=params,
            headers={"X-Api-Key": api_key},
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        if data.get("status") == "error":
            return {"error": data.get("message", "Unknown API error"), "code": data.get("code"), "success": False}
        raw_articles = data.get("articles", [])
        articles = [_parse_article(a) for a in raw_articles]
        return {
            "articles": articles,
            "totalResults": data.get("totalResults", 0),
            "count": len(articles),
            "query": query,
            "sort_by": sort_by,
            "language": language,
            "success": True,
        }


@skill(
    name="news_sources",
    display_name="News Sources",
    description=(
        "List available news sources from NewsAPI v2 "
        "(requires NEWSAPI_API_KEY env var). Free tier: 100 requests/day."
    ),
    category="news",
    tags=["news", "sources", "publishers"],
    icon="list",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="NewsAPI Key",
            description="NewsAPI key. Falls back to NEWSAPI_API_KEY env var.",
            type="secret",
            placeholder="your-newsapi-key",
        ),
        ConfigParam(
            name="timeout",
            display_name="Timeout",
            description="Request timeout.",
            type="number",
            default=15,
            min=1,
            max=60,
            unit="seconds",
        ),
    ],
)
async def news_sources(
    category: str = "",
    language: str = "",
    country: str = "",
) -> dict:
    """List available news sources, optionally filtered."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "NEWSAPI_API_KEY env var is required. Get a free key at https://newsapi.org",
            "success": False,
        }

    endpoint = f"{_BASE_URL}/top-headlines/sources"
    params: Dict[str, Any] = {}
    if category:
        params["category"] = category
    if language:
        params["language"] = language
    if country:
        params["country"] = country

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            endpoint,
            params=params,
            headers={"X-Api-Key": api_key},
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        if data.get("status") == "error":
            return {"error": data.get("message", "Unknown API error"), "code": data.get("code"), "success": False}
        raw_sources = data.get("sources", [])
        sources = [
            {
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "url": s.get("url", ""),
                "category": s.get("category", ""),
                "language": s.get("language", ""),
                "country": s.get("country", ""),
            }
            for s in raw_sources
        ]
        return {
            "sources": sources,
            "count": len(sources),
            "success": True,
        }


class NewsApiPlugin(TransformerPlugin):
    """Plugin providing news skills and article formatting transformer."""

    def __init__(self):
        super().__init__("newsapi")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_article": lambda _: FormatArticleTransformer("format_article"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "news_headlines": news_headlines.__skill__,
            "news_search": news_search.__skill__,
            "news_sources": news_sources.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="newsapi",
            display_name="NewsAPI",
            description="Top headlines, article search, and source listing via NewsAPI v2.",
            icon="newspaper",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
