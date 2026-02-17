"""URL shortener plugin.

Provides async skills for shortening URLs using the is.gd API (free, no key).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://is.gd"


# -- Skills ------------------------------------------------------------------


@skill(
    name="shorten_url",
    display_name="Shorten URL",
    description="Shorten a URL using is.gd (free, no key required, unlimited).",
    category="url_shortener",
    tags=["url", "shorten", "link", "utility"],
    icon="link",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
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
async def shorten_url(
    url: str,
    timeout: int = 15,
) -> dict:
    """Shorten a long URL.

    Args:
        url: The URL to shorten.
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url_str = url.strip()
    if not url_str:
        return {"error": "URL must not be empty.", "success": False}

    api_url = f"{_BASE_URL}/create.php"
    params = {"format": "json", "url": url_str}

    check_host(api_url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(api_url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    if "shorturl" not in data:
        return {"error": data.get("errormessage", "Failed to shorten URL"), "original_url": url_str, "success": False}

    return {
        "original_url": url_str,
        "short_url": data["shorturl"],
        "success": True,
    }


class UrlShortenerPlugin(TransformerPlugin):
    """Plugin providing URL shortening skills."""

    def __init__(self):
        super().__init__("url_shortener")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "shorten_url": shorten_url.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="url_shortener",
            display_name="URL Shortener",
            description="Shorten URLs using the is.gd API.",
            icon="link",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
