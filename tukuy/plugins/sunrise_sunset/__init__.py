"""Sunrise/sunset plugin.

Provides async skills for looking up sunrise, sunset, and daylight times
for any location using the Sunrise-Sunset API (free, no key required).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.sunrisesunset.io/json"


# -- Skills ------------------------------------------------------------------


@skill(
    name="sunrise_sunset",
    display_name="Sunrise & Sunset",
    description="Get sunrise, sunset, and daylight times for a location (free, no key required).",
    category="sunrise_sunset",
    tags=["sunrise", "sunset", "daylight", "solar", "astronomy"],
    icon="sun",
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
async def sunrise_sunset(
    latitude: float,
    longitude: float,
    date: str = "today",
    timezone: str = "UTC",
    timeout: int = 15,
) -> dict:
    """Get sunrise, sunset, and related solar times for a location.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
        date: Date in YYYY-MM-DD format or ``"today"`` (default).
        timezone: IANA timezone (e.g. ``"America/New_York"``). Default ``"UTC"``.
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    params = {
        "lat": latitude,
        "lng": longitude,
        "date": date,
        "timezone": timezone,
    }

    check_host(_BASE_URL)
    async with httpx.AsyncClient() as client:
        resp = await client.get(_BASE_URL, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    if data.get("status") != "OK":
        return {"error": data.get("status", "Unknown error"), "success": False}

    results = data.get("results", {})
    return {
        "latitude": latitude,
        "longitude": longitude,
        "date": date,
        "timezone": timezone,
        "sunrise": results.get("sunrise"),
        "sunset": results.get("sunset"),
        "dawn": results.get("dawn"),
        "dusk": results.get("dusk"),
        "solar_noon": results.get("solar_noon"),
        "day_length": results.get("day_length"),
        "golden_hour": results.get("golden_hour"),
        "success": True,
    }


class SunriseSunsetPlugin(TransformerPlugin):
    """Plugin providing sunrise/sunset lookup skills."""

    def __init__(self):
        super().__init__("sunrise_sunset")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "sunrise_sunset": sunrise_sunset.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="sunrise_sunset",
            display_name="Sunrise/Sunset",
            description="Look up sunrise, sunset, and daylight times for any location.",
            icon="sun",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
