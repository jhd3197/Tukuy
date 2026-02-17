"""IP geolocation plugin.

Provides async skills for looking up geographic information from IP addresses
using ipapi.co (free, no key, 1000/day) and ipify (free, unlimited).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_IPAPI_URL = "https://ipapi.co"
_IPIFY_URL = "https://api.ipify.org"


# -- Skills ------------------------------------------------------------------


@skill(
    name="ip_geolocate",
    display_name="IP Geolocation",
    description="Get geographic info (country, city, timezone, ISP) from an IP address (ipapi.co, free, no key, 1000/day).",
    category="ip_geo",
    tags=["ip", "geolocation", "location", "network"],
    icon="map-pin",
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
async def ip_geolocate(
    ip: str = "",
    timeout: int = 15,
) -> dict:
    """Look up geolocation data for an IP address.

    Args:
        ip: IPv4 or IPv6 address. Leave empty for your own IP.
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    ip = ip.strip()
    if ip:
        url = f"{_IPAPI_URL}/{ip}/json/"
    else:
        url = f"{_IPAPI_URL}/json/"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=timeout)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    if data.get("error"):
        return {"error": data.get("reason", "Unknown error"), "ip": ip, "success": False}

    return {
        "ip": data.get("ip", ip),
        "city": data.get("city"),
        "region": data.get("region"),
        "region_code": data.get("region_code"),
        "country": data.get("country_name"),
        "country_code": data.get("country_code"),
        "continent": data.get("continent_code"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone"),
        "utc_offset": data.get("utc_offset"),
        "currency": data.get("currency"),
        "isp": data.get("org"),
        "asn": data.get("asn"),
        "postal": data.get("postal"),
        "languages": data.get("languages"),
        "success": True,
    }


@skill(
    name="my_ip",
    display_name="My Public IP",
    description="Get your public IP address (ipify, free, no key, unlimited).",
    category="ip_geo",
    tags=["ip", "public", "network"],
    icon="wifi",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def my_ip() -> dict:
    """Get the caller's public IP address."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"{_IPIFY_URL}?format=json"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    return {
        "ip": data.get("ip", ""),
        "success": True,
    }


class IpGeoPlugin(TransformerPlugin):
    """Plugin providing IP geolocation and public IP lookup skills."""

    def __init__(self):
        super().__init__("ip_geo")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "ip_geolocate": ip_geolocate.__skill__,
            "my_ip": my_ip.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="ip_geo",
            display_name="IP Geolocation",
            description="Look up geographic info from IP addresses via ipapi.co and ipify.",
            icon="map-pin",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
