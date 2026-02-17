"""Public holidays plugin.

Provides async skills for looking up public holidays by country and year
using the Nager.Date API (free, no key required).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://date.nager.at/api/v3"


# -- Skills ------------------------------------------------------------------


@skill(
    name="public_holidays",
    display_name="Public Holidays",
    description="Get public holidays for a country and year (Nager.Date, free, no key required).",
    category="holidays",
    tags=["holidays", "calendar", "country", "date"],
    icon="calendar",
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
async def public_holidays(
    country_code: str,
    year: int = 2026,
    timeout: int = 15,
) -> dict:
    """Fetch public holidays for a given country and year.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. ``"US"``, ``"DE"``, ``"JP"``).
        year: The year to look up (default current year).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    country_code = country_code.strip().upper()
    if len(country_code) != 2:
        return {"error": "Country code must be a 2-letter ISO code (e.g. 'US').", "success": False}

    url = f"{_BASE_URL}/PublicHolidays/{year}/{country_code}"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=timeout)
        if not resp.is_success:
            return {"error": f"No holidays found (status {resp.status_code})", "country": country_code, "year": year, "success": False}
        data = resp.json()

    holidays = []
    for h in data:
        holidays.append({
            "date": h.get("date"),
            "name": h.get("localName", h.get("name", "")),
            "name_english": h.get("name", ""),
            "fixed": h.get("fixed", False),
            "global": h.get("global", True),
            "types": h.get("types", []),
        })

    return {
        "country": country_code,
        "year": year,
        "holidays": holidays,
        "count": len(holidays),
        "success": True,
    }


@skill(
    name="next_holiday",
    display_name="Next Holiday",
    description="Get the next upcoming public holiday for a country (Nager.Date, free, no key required).",
    category="holidays",
    tags=["holidays", "next", "upcoming"],
    icon="calendar",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def next_holiday(country_code: str) -> dict:
    """Fetch the next upcoming public holidays for a country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. ``"US"``).
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    country_code = country_code.strip().upper()
    url = f"{_BASE_URL}/NextPublicHolidays/{country_code}"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if not resp.is_success:
            return {"error": f"No upcoming holidays found (status {resp.status_code})", "success": False}
        data = resp.json()

    holidays = []
    for h in data[:5]:
        holidays.append({
            "date": h.get("date"),
            "name": h.get("localName", h.get("name", "")),
            "name_english": h.get("name", ""),
        })

    return {
        "country": country_code,
        "upcoming": holidays,
        "count": len(holidays),
        "success": True,
    }


@skill(
    name="holiday_countries",
    display_name="Available Countries",
    description="List all countries supported by the holidays API (Nager.Date, free, no key required).",
    category="holidays",
    tags=["holidays", "countries", "list"],
    icon="globe",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def holiday_countries() -> dict:
    """Fetch the list of countries supported by the Nager.Date API."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"{_BASE_URL}/AvailableCountries"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    countries = [{"code": c.get("countryCode"), "name": c.get("name")} for c in data]
    countries.sort(key=lambda x: x["name"])
    return {
        "countries": countries,
        "count": len(countries),
        "success": True,
    }


class HolidaysPlugin(TransformerPlugin):
    """Plugin providing public holiday lookup skills."""

    def __init__(self):
        super().__init__("holidays")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "public_holidays": public_holidays.__skill__,
            "next_holiday": next_holiday.__skill__,
            "holiday_countries": holiday_countries.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="holidays",
            display_name="Holidays",
            description="Look up public holidays for any country and year via Nager.Date API.",
            icon="calendar",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
