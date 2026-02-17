"""Postal/zip code lookup plugin.

Provides async skills for looking up location data from zip/postal codes
using the Zippopotamus API (free, no key required, 60+ countries).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.zippopotam.us"


# -- Skills ------------------------------------------------------------------


@skill(
    name="zipcode_lookup",
    display_name="Zip Code Lookup",
    description="Look up location info from a postal/zip code (Zippopotamus, free, no key, 60+ countries).",
    category="zipcode",
    tags=["zipcode", "postal", "location", "geography"],
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
async def zipcode_lookup(
    postal_code: str,
    country: str = "us",
    timeout: int = 15,
) -> dict:
    """Look up a zip/postal code and return location data.

    Args:
        postal_code: The postal or zip code (e.g. ``"90210"``, ``"SW1A 1AA"``).
        country: ISO 2-letter country code (default ``"us"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    country = country.strip().lower()
    postal_code = postal_code.strip()
    if not postal_code:
        return {"error": "Postal code must not be empty.", "success": False}

    url = f"{_BASE_URL}/{country}/{postal_code}"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Postal code not found (status {resp.status_code})", "postal_code": postal_code, "country": country, "success": False}
        data = resp.json()

    places = []
    for p in data.get("places", []):
        places.append({
            "name": p.get("place name", ""),
            "state": p.get("state", ""),
            "state_abbr": p.get("state abbreviation", ""),
            "latitude": p.get("latitude"),
            "longitude": p.get("longitude"),
        })

    return {
        "postal_code": data.get("post code", postal_code),
        "country": data.get("country", ""),
        "country_code": data.get("country abbreviation", country.upper()),
        "places": places,
        "count": len(places),
        "success": True,
    }


class ZipcodePlugin(TransformerPlugin):
    """Plugin providing postal/zip code lookup skills."""

    def __init__(self):
        super().__init__("zipcode")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "zipcode_lookup": zipcode_lookup.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="zipcode",
            display_name="Zip Code",
            description="Look up location data from postal/zip codes via Zippopotamus API.",
            icon="map-pin",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
