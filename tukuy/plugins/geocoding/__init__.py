"""Geocoding plugin.

Provides async ``geocode``, ``reverse_geocode``, and ``geocode_batch``
skills using the OpenCage API (2 500 requests/day free).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import os
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.opencagedata.com/geocode/v1/json"


class FormatCoordinatesTransformer(ChainableTransformer[dict, str]):
    """Format a geocoding result dict into a 'lat, lng' string."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "lat" in value and "lng" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        return f"{value['lat']}, {value['lng']}"


def _get_api_key() -> Optional[str]:
    """Read the OpenCage API key from the environment."""
    return os.environ.get("OPENCAGE_API_KEY")


def _parse_result(raw: dict) -> dict:
    """Normalise an OpenCage result object."""
    geometry = raw.get("geometry", {})
    components = raw.get("components", {})
    return {
        "formatted": raw.get("formatted", ""),
        "lat": geometry.get("lat"),
        "lng": geometry.get("lng"),
        "components": {
            "country": components.get("country", ""),
            "country_code": components.get("country_code", ""),
            "state": components.get("state", ""),
            "city": components.get("city") or components.get("town") or components.get("village", ""),
            "postcode": components.get("postcode", ""),
            "road": components.get("road", ""),
        },
        "confidence": raw.get("confidence"),
        "timezone": (raw.get("annotations") or {}).get("timezone", {}).get("name", ""),
    }


# ── Skills ─────────────────────────────────────────────────────────────────


@skill(
    name="geocode",
    display_name="Geocode Address",
    description="Convert an address to coordinates using OpenCage API (requires OPENCAGE_API_KEY env var).",
    category="geocoding",
    tags=["geocode", "address", "coordinates", "maps"],
    icon="map-pin",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="OpenCage API Key",
            description="OpenCage API key. Falls back to OPENCAGE_API_KEY env var.",
            type="secret",
            placeholder="your-opencage-api-key",
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
async def geocode(address: str, language: str = "en", limit: int = 1) -> dict:
    """Forward geocode: address string to coordinates."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": "OPENCAGE_API_KEY env var is required. Get a free key at https://opencagedata.com", "success": False}

    check_host(_BASE_URL)
    params = {
        "q": address,
        "key": api_key,
        "language": language,
        "limit": limit,
        "no_annotations": 0,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(_BASE_URL, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return {"query": address, "error": "No results found", "success": False}
        parsed = _parse_result(results[0])
        parsed["query"] = address
        parsed["success"] = True
        return parsed


@skill(
    name="reverse_geocode",
    display_name="Reverse Geocode",
    description="Convert coordinates to an address using OpenCage API (requires OPENCAGE_API_KEY env var).",
    category="geocoding",
    tags=["geocode", "reverse", "coordinates", "address"],
    icon="map",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def reverse_geocode(latitude: float, longitude: float, language: str = "en") -> dict:
    """Reverse geocode: coordinates to address."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": "OPENCAGE_API_KEY env var is required.", "success": False}

    check_host(_BASE_URL)
    params = {
        "q": f"{latitude},{longitude}",
        "key": api_key,
        "language": language,
        "no_annotations": 0,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(_BASE_URL, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return {"latitude": latitude, "longitude": longitude, "error": "No results found", "success": False}
        parsed = _parse_result(results[0])
        parsed["query_lat"] = latitude
        parsed["query_lng"] = longitude
        parsed["success"] = True
        return parsed


@skill(
    name="geocode_batch",
    display_name="Batch Geocode",
    description="Geocode multiple addresses sequentially (OpenCage API).",
    category="geocoding",
    tags=["geocode", "batch", "address"],
    icon="map-pin",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def geocode_batch(addresses: list, language: str = "en") -> dict:
    """Geocode a list of addresses sequentially."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": "OPENCAGE_API_KEY env var is required.", "success": False}

    check_host(_BASE_URL)
    results = []

    async with httpx.AsyncClient() as client:
        for addr in addresses:
            params = {
                "q": addr,
                "key": api_key,
                "language": language,
                "limit": 1,
                "no_annotations": 1,
            }
            resp = await client.get(_BASE_URL, params=params, timeout=15)
            if resp.is_success:
                data = resp.json()
                items = data.get("results", [])
                if items:
                    parsed = _parse_result(items[0])
                    parsed["query"] = addr
                    parsed["success"] = True
                    results.append(parsed)
                else:
                    results.append({"query": addr, "error": "No results", "success": False})
            else:
                results.append({"query": addr, "error": f"Status {resp.status_code}", "success": False})

    succeeded = sum(1 for r in results if r.get("success"))
    return {
        "results": results,
        "total": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "success": True,
    }


class GeocodingPlugin(TransformerPlugin):
    """Plugin providing geocoding skills via OpenCage API."""

    def __init__(self):
        super().__init__("geocoding")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_coordinates": lambda _: FormatCoordinatesTransformer("format_coordinates"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "geocode": geocode.__skill__,
            "reverse_geocode": reverse_geocode.__skill__,
            "geocode_batch": geocode_batch.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="geocoding",
            display_name="Geocoding",
            description="Forward and reverse geocoding via OpenCage API.",
            icon="map-pin",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
