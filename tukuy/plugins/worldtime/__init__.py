"""World time and timezone plugin.

Provides async skills for looking up current time in any timezone
using the WorldTimeAPI (free, no key required).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "http://worldtimeapi.org/api"


# -- Skills ------------------------------------------------------------------


@skill(
    name="world_time",
    display_name="World Time",
    description="Get the current time for a timezone (WorldTimeAPI, free, no key required).",
    category="worldtime",
    tags=["time", "timezone", "clock", "world"],
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
async def world_time(
    timezone: str = "America/New_York",
    timeout: int = 15,
) -> dict:
    """Get the current time for a timezone.

    Args:
        timezone: IANA timezone (e.g. ``"America/New_York"``, ``"Europe/London"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    timezone = timezone.strip()
    url = f"{_BASE_URL}/timezone/{timezone}"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Timezone not found (status {resp.status_code})", "timezone": timezone, "success": False}
        data = resp.json()

    return {
        "timezone": data.get("timezone", timezone),
        "datetime": data.get("datetime", ""),
        "date": data.get("datetime", "")[:10],
        "time": data.get("datetime", "")[11:19],
        "utc_offset": data.get("utc_offset", ""),
        "utc_datetime": data.get("utc_datetime", ""),
        "day_of_week": data.get("day_of_week"),
        "day_of_year": data.get("day_of_year"),
        "week_number": data.get("week_number"),
        "abbreviation": data.get("abbreviation", ""),
        "dst": data.get("dst", False),
        "success": True,
    }


@skill(
    name="time_by_ip",
    display_name="Time by IP",
    description="Get the current time for your IP address location (WorldTimeAPI, free, no key required).",
    category="worldtime",
    tags=["time", "ip", "location"],
    icon="clock",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def time_by_ip() -> dict:
    """Get the current time based on the caller's IP address."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"{_BASE_URL}/ip"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    return {
        "timezone": data.get("timezone", ""),
        "datetime": data.get("datetime", ""),
        "utc_offset": data.get("utc_offset", ""),
        "abbreviation": data.get("abbreviation", ""),
        "client_ip": data.get("client_ip", ""),
        "dst": data.get("dst", False),
        "success": True,
    }


@skill(
    name="list_timezones",
    display_name="List Timezones",
    description="List all available IANA timezones (WorldTimeAPI, free, no key required).",
    category="worldtime",
    tags=["timezone", "list", "iana"],
    icon="list",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def list_timezones() -> dict:
    """Fetch all available IANA timezone identifiers."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"{_BASE_URL}/timezone"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    return {
        "timezones": data,
        "count": len(data),
        "success": True,
    }


class WorldTimePlugin(TransformerPlugin):
    """Plugin providing world time and timezone skills."""

    def __init__(self):
        super().__init__("worldtime")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "world_time": world_time.__skill__,
            "time_by_ip": time_by_ip.__skill__,
            "list_timezones": list_timezones.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="worldtime",
            display_name="World Time",
            description="Look up current time in any timezone via WorldTimeAPI.",
            icon="clock",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
