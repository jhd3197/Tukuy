"""Wayback Machine plugin.

Provides async skills for checking if URLs are archived in the Internet
Archive's Wayback Machine (free, no key required).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://archive.org/wayback/available"


# -- Skills ------------------------------------------------------------------


@skill(
    name="wayback_check",
    display_name="Wayback Check",
    description="Check if a URL is archived in the Wayback Machine (Internet Archive, free, no key).",
    category="wayback",
    tags=["wayback", "archive", "internet", "history", "url"],
    icon="clock",
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
async def wayback_check(
    url: str,
    timestamp: str = "",
    timeout: int = 15,
) -> dict:
    """Check if a URL has been archived by the Wayback Machine.

    Args:
        url: The URL to check.
        timestamp: Optional timestamp (YYYYMMDD or YYYYMMDDhhmmss) to find
                   the closest snapshot to that date.
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url_str = url.strip()
    if not url_str:
        return {"error": "URL must not be empty.", "success": False}

    params = {"url": url_str}
    if timestamp.strip():
        params["timestamp"] = timestamp.strip()

    check_host(_BASE_URL)
    async with httpx.AsyncClient() as client:
        resp = await client.get(_BASE_URL, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Wayback API returned status {resp.status_code}", "success": False}
        data = resp.json()

    snapshots = data.get("archived_snapshots", {})
    closest = snapshots.get("closest", {})

    if not closest:
        return {
            "url": url_str,
            "archived": False,
            "success": True,
        }

    return {
        "url": url_str,
        "archived": closest.get("available", False),
        "archive_url": closest.get("url", ""),
        "timestamp": closest.get("timestamp", ""),
        "status": closest.get("status", ""),
        "success": True,
    }


class WaybackPlugin(TransformerPlugin):
    """Plugin providing Wayback Machine archive check skills."""

    def __init__(self):
        super().__init__("wayback")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "wayback_check": wayback_check.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="wayback",
            display_name="Wayback Machine",
            description="Check if URLs are archived in the Internet Archive's Wayback Machine.",
            icon="clock",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
