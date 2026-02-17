"""Country data plugin.

Provides async ``country_info``, ``country_search``, and ``countries_by_region``
skills using the REST Countries API (free, no key).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://restcountries.com/v3.1"


def _parse_country(raw: dict) -> dict:
    """Normalise a REST Countries response object into a flat dict."""
    name_block = raw.get("name", {})
    currencies = raw.get("currencies", {})
    languages = raw.get("languages", {})
    return {
        "name": name_block.get("common", ""),
        "official_name": name_block.get("official", ""),
        "cca2": raw.get("cca2", ""),
        "cca3": raw.get("cca3", ""),
        "capital": (raw.get("capital") or [None])[0],
        "region": raw.get("region", ""),
        "subregion": raw.get("subregion", ""),
        "population": raw.get("population"),
        "area": raw.get("area"),
        "currencies": {code: info.get("name", "") for code, info in currencies.items()},
        "languages": languages,
        "timezones": raw.get("timezones", []),
        "borders": raw.get("borders", []),
        "flag_emoji": raw.get("flag", ""),
        "flag_png": (raw.get("flags") or {}).get("png", ""),
        "latlng": raw.get("latlng", []),
        "landlocked": raw.get("landlocked", False),
        "independent": raw.get("independent"),
    }


class CountryFlagTransformer(ChainableTransformer[dict, str]):
    """Extract the flag emoji from a country data dict."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "flag_emoji" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        return value.get("flag_emoji", "")


# ── Skills ─────────────────────────────────────────────────────────────────


@skill(
    name="country_info",
    display_name="Country Info",
    description="Get detailed information about a country by name or code (REST Countries, no key required).",
    category="country",
    tags=["country", "geography", "data"],
    icon="globe",
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
async def country_info(name: str) -> dict:
    """Look up a country by name or ISO code and return structured data."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    # Try alpha code first (2 or 3 letter), then fall back to name search
    name_stripped = name.strip()
    if len(name_stripped) in (2, 3) and name_stripped.isalpha():
        endpoint = f"{_BASE_URL}/alpha/{name_stripped}"
    else:
        endpoint = f"{_BASE_URL}/name/{name_stripped}"

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, timeout=15)
        if not resp.is_success:
            return {"query": name, "error": f"Country not found (status {resp.status_code})", "success": False}
        data = resp.json()
        items = data if isinstance(data, list) else [data]
        if not items:
            return {"query": name, "error": "No results", "success": False}
        country = _parse_country(items[0])
        country["success"] = True
        country["query"] = name
        return country


@skill(
    name="country_search",
    display_name="Search Countries",
    description="Search countries by currency, language, or region (REST Countries, no key required).",
    category="country",
    tags=["country", "search"],
    icon="search",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def country_search(
    by: str = "region",
    value: str = "europe",
) -> dict:
    """Search countries by a given field (region, currency, language, subregion, capital)."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    by = by.lower().strip()
    allowed = {"region", "currency", "lang", "subregion", "capital"}
    if by not in allowed:
        return {"error": f"'by' must be one of {sorted(allowed)}", "success": False}

    endpoint = f"{_BASE_URL}/{by}/{value.strip()}"

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, timeout=15)
        if not resp.is_success:
            return {"by": by, "value": value, "error": f"No results (status {resp.status_code})", "success": False}
        data = resp.json()
        items = data if isinstance(data, list) else [data]
        countries = [_parse_country(c) for c in items]
        return {
            "by": by,
            "value": value,
            "countries": countries,
            "count": len(countries),
            "success": True,
        }


@skill(
    name="country_all",
    display_name="All Countries",
    description="List all countries with basic info (REST Countries, no key required).",
    category="country",
    tags=["country", "list"],
    icon="list",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def country_all() -> dict:
    """Fetch a summary of all countries."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    endpoint = f"{_BASE_URL}/all?fields=name,cca2,cca3,capital,region,population,flag"

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, timeout=20)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        countries = []
        for c in data:
            name_block = c.get("name", {})
            countries.append({
                "name": name_block.get("common", ""),
                "cca2": c.get("cca2", ""),
                "cca3": c.get("cca3", ""),
                "capital": (c.get("capital") or [None])[0],
                "region": c.get("region", ""),
                "population": c.get("population"),
                "flag": c.get("flag", ""),
            })
        countries.sort(key=lambda x: x["name"])
        return {
            "countries": countries,
            "count": len(countries),
            "success": True,
        }


class CountryPlugin(TransformerPlugin):
    """Plugin providing country data skills and flag transformer."""

    def __init__(self):
        super().__init__("country")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "country_flag": lambda _: CountryFlagTransformer("country_flag"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "country_info": country_info.__skill__,
            "country_search": country_search.__skill__,
            "country_all": country_all.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="country",
            display_name="Country",
            description="Look up country information, search by region/currency/language via REST Countries API.",
            icon="globe",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
