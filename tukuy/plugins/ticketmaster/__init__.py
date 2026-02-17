"""Ticketmaster Events plugin.

Provides async event search, event details, venue search, venue events,
and artist/attraction event lookup via the Ticketmaster Discovery API v2
(free tier: 5,000 calls/day, 5 req/sec).

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

_BASE_URL = "https://app.ticketmaster.com/discovery/v2"


def _get_api_key() -> Optional[str]:
    """Read the Ticketmaster API key from the environment."""
    return os.environ.get("TICKETMASTER_API_KEY")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _pick_image(images: Optional[List[dict]], preferred_ratio: str = "16_9", min_width: int = 500) -> Optional[str]:
    """Pick the best image URL from Ticketmaster's image array.

    Prefers images with the given ratio and at least *min_width* pixels wide.
    Falls back to the first image if no preferred match is found.
    """
    if not images:
        return None
    # Try to find one matching the preferred ratio and minimum width
    for img in images:
        if img.get("ratio") == preferred_ratio and (img.get("width", 0) or 0) >= min_width:
            return img.get("url")
    # Fallback: any image with the preferred ratio
    for img in images:
        if img.get("ratio") == preferred_ratio:
            return img.get("url")
    # Last resort: first image
    return images[0].get("url") if images else None


def _format_event_date(local_date: Optional[str], local_time: Optional[str]) -> str:
    """Format ``'2026-03-15'`` + ``'20:00:00'`` into ``'Sat Mar 15, 8:00 PM'``.

    Returns ``'Time TBD'`` suffix when time is missing, and ``'Date TBD'`` when
    the date is also missing.
    """
    if not local_date:
        return "Date TBD"
    try:
        dt = datetime.datetime.strptime(local_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return local_date  # Return raw string if unparseable

    date_part = dt.strftime("%a %b %d").replace(" 0", " ")  # "Sat Mar 15"

    if not local_time:
        return f"{date_part}, Time TBD"

    try:
        time_dt = datetime.datetime.strptime(local_time, "%H:%M:%S")
        time_part = time_dt.strftime("%I:%M %p").lstrip("0")  # "8:00 PM"
    except (ValueError, TypeError):
        time_part = local_time

    return f"{date_part}, {time_part}"


def _format_price_range(price_ranges: Optional[List[dict]]) -> str:
    """Format priceRanges array into ``'$75-$250'`` or ``'Price TBD'``."""
    if not price_ranges:
        return "Price TBD"
    pr = price_ranges[0]
    min_price = pr.get("min")
    max_price = pr.get("max")
    currency = pr.get("currency", "USD")
    symbol = "$" if currency == "USD" else f"{currency} "
    if min_price is not None and max_price is not None:
        if min_price == max_price:
            return f"{symbol}{min_price:g}"
        return f"{symbol}{min_price:g}-{symbol}{max_price:g}"
    if min_price is not None:
        return f"From {symbol}{min_price:g}"
    if max_price is not None:
        return f"Up to {symbol}{max_price:g}"
    return "Price TBD"


def _parse_event(raw: dict) -> dict:
    """Extract a clean event dict from a deeply nested Ticketmaster event."""
    dates = raw.get("dates", {})
    start = dates.get("start", {})
    status = dates.get("status", {})

    embedded = raw.get("_embedded", {})
    venues = embedded.get("venues", [])
    venue = venues[0] if venues else {}

    price_ranges = raw.get("priceRanges", [])
    classifications = raw.get("classifications", [])
    classification = classifications[0] if classifications else {}

    return {
        "name": raw.get("name"),
        "event_id": raw.get("id"),
        "date": start.get("localDate"),
        "time": start.get("localTime"),
        "status": status.get("code"),
        "venue_name": venue.get("name"),
        "city": venue.get("city", {}).get("name"),
        "state": venue.get("state", {}).get("stateCode"),
        "price_min": price_ranges[0].get("min") if price_ranges else None,
        "price_max": price_ranges[0].get("max") if price_ranges else None,
        "url": raw.get("url"),
        "image_url": _pick_image(raw.get("images")),
        "genre": classification.get("genre", {}).get("name"),
        "segment": classification.get("segment", {}).get("name"),
    }


def _parse_venue(raw: dict) -> dict:
    """Extract a clean venue dict from a nested Ticketmaster venue."""
    location = raw.get("location", {})
    upcoming = raw.get("upcomingEvents", {})
    return {
        "name": raw.get("name"),
        "venue_id": raw.get("id"),
        "address": raw.get("address", {}).get("line1"),
        "city": raw.get("city", {}).get("name"),
        "state": raw.get("state", {}).get("stateCode"),
        "postal_code": raw.get("postalCode"),
        "country": raw.get("country", {}).get("countryCode"),
        "url": raw.get("url"),
        "location": {
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
        } if location else None,
        "upcoming_events": upcoming.get("_total", 0) if upcoming else 0,
    }


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------


class FormatEventTransformer(ChainableTransformer[dict, str]):
    """Format an event dict into a one-line human-readable string.

    Output example::

        Taylor Swift | The Eras Tour -- SoFi Stadium, Los Angeles -- Sat Mar 15, 8:00 PM -- $75-$250 -- https://...
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "name" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        name = value.get("name", "Unknown Event")
        venue_name = value.get("venue_name", "")
        city = value.get("city", "")
        date_str = _format_event_date(value.get("date"), value.get("time"))
        price_str = _format_price_range(value.get("priceRanges") or (
            [{"min": value.get("price_min"), "max": value.get("price_max")}]
            if value.get("price_min") is not None or value.get("price_max") is not None
            else None
        ))
        url = value.get("url", "")

        venue_part = ", ".join(p for p in [venue_name, city] if p)
        parts = [name]
        if venue_part:
            parts.append(venue_part)
        parts.append(date_str)
        parts.append(price_str)
        if url:
            parts.append(url)
        return " -- ".join(parts)


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@skill(
    name="events_search",
    display_name="Search Events",
    description="Search for events on Ticketmaster by keyword, city, date range, or genre.",
    category="events",
    tags=["events", "concerts", "sports", "ticketmaster", "tickets"],
    icon="ticket",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Ticketmaster API key (or set TICKETMASTER_API_KEY env var).",
            type="secret",
            placeholder="your-ticketmaster-api-key",
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
async def events_search(
    keyword: str = "",
    city: str = "",
    start_date: str = "",
    end_date: str = "",
    genre: str = "",
    sort: str = "date,asc",
    size: int = 10,
) -> dict:
    """Search for events on Ticketmaster."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "TICKETMASTER_API_KEY env var is required. Get a free key at https://developer.ticketmaster.com",
            "success": False,
        }

    params: Dict[str, Any] = {"apikey": api_key, "sort": sort, "size": size}
    if keyword:
        params["keyword"] = keyword
    if city:
        params["city"] = city
    if start_date:
        params["startDateTime"] = f"{start_date}T00:00:00Z"
    if end_date:
        params["endDateTime"] = f"{end_date}T23:59:59Z"
    if genre:
        params["classificationName"] = genre

    endpoint = f"{_BASE_URL}/events.json"
    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    embedded = data.get("_embedded", {})
    raw_events = embedded.get("events", [])
    events = [_parse_event(ev) for ev in raw_events]
    total = data.get("page", {}).get("totalElements", len(events))

    return {"events": events, "total": total, "success": True}


@skill(
    name="event_details",
    display_name="Event Details",
    description="Get full details for a specific Ticketmaster event by its ID.",
    category="events",
    tags=["events", "details", "ticketmaster"],
    icon="ticket",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Ticketmaster API key (or set TICKETMASTER_API_KEY env var).",
            type="secret",
            placeholder="your-ticketmaster-api-key",
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
async def event_details(event_id: str) -> dict:
    """Get full details for a Ticketmaster event."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "TICKETMASTER_API_KEY env var is required. Get a free key at https://developer.ticketmaster.com",
            "success": False,
        }

    endpoint = f"{_BASE_URL}/events/{event_id}.json"
    params = {"apikey": api_key}

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    dates = data.get("dates", {})
    start = dates.get("start", {})
    status = dates.get("status", {})
    sales = data.get("sales", {}).get("public", {})

    embedded = data.get("_embedded", {})
    venues = embedded.get("venues", [])
    venue_raw = venues[0] if venues else {}
    venue = _parse_venue(venue_raw) if venue_raw else None

    attractions = embedded.get("attractions", [])
    lineup = [{"name": a.get("name"), "id": a.get("id")} for a in attractions]

    classifications = data.get("classifications", [])

    return {
        "name": data.get("name"),
        "id": data.get("id"),
        "date": start.get("localDate"),
        "time": start.get("localTime"),
        "timezone": dates.get("timezone"),
        "on_sale_status": status.get("code"),
        "venue": venue,
        "price_ranges": data.get("priceRanges"),
        "url": data.get("url"),
        "images": data.get("images"),
        "sale_start": sales.get("startDateTime"),
        "sale_end": sales.get("endDateTime"),
        "seatmap_url": data.get("seatmap", {}).get("staticUrl"),
        "info": data.get("info"),
        "pleaseNote": data.get("pleaseNote"),
        "accessibility": data.get("accessibility"),
        "lineup": lineup,
        "classifications": classifications,
        "success": True,
    }


@skill(
    name="venue_search",
    display_name="Search Venues",
    description="Search for venues on Ticketmaster by keyword, city, or state.",
    category="events",
    tags=["venues", "locations", "ticketmaster"],
    icon="calendar",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Ticketmaster API key (or set TICKETMASTER_API_KEY env var).",
            type="secret",
            placeholder="your-ticketmaster-api-key",
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
async def venue_search(
    keyword: str = "",
    city: str = "",
    state_code: str = "",
    size: int = 10,
) -> dict:
    """Search for venues on Ticketmaster."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "TICKETMASTER_API_KEY env var is required. Get a free key at https://developer.ticketmaster.com",
            "success": False,
        }

    params: Dict[str, Any] = {"apikey": api_key, "size": size}
    if keyword:
        params["keyword"] = keyword
    if city:
        params["city"] = city
    if state_code:
        params["stateCode"] = state_code

    endpoint = f"{_BASE_URL}/venues.json"
    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    embedded = data.get("_embedded", {})
    raw_venues = embedded.get("venues", [])
    venues = [_parse_venue(v) for v in raw_venues]
    total = data.get("page", {}).get("totalElements", len(venues))

    return {"venues": venues, "total": total, "success": True}


@skill(
    name="venue_events",
    display_name="Venue Events",
    description="Get upcoming events at a specific Ticketmaster venue.",
    category="events",
    tags=["events", "venues", "ticketmaster"],
    icon="calendar",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Ticketmaster API key (or set TICKETMASTER_API_KEY env var).",
            type="secret",
            placeholder="your-ticketmaster-api-key",
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
async def venue_events(venue_id: str, size: int = 10) -> dict:
    """Get upcoming events at a specific venue."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "TICKETMASTER_API_KEY env var is required. Get a free key at https://developer.ticketmaster.com",
            "success": False,
        }

    params: Dict[str, Any] = {
        "apikey": api_key,
        "venueId": venue_id,
        "size": size,
        "sort": "date,asc",
    }

    endpoint = f"{_BASE_URL}/events.json"
    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    embedded = data.get("_embedded", {})
    raw_events = embedded.get("events", [])
    events = [_parse_event(ev) for ev in raw_events]
    total = data.get("page", {}).get("totalElements", len(events))

    return {"venue_id": venue_id, "events": events, "total": total, "success": True}


@skill(
    name="artist_events",
    display_name="Artist Events",
    description="Find upcoming events for a specific artist or attraction on Ticketmaster.",
    category="events",
    tags=["events", "artist", "concerts", "ticketmaster"],
    icon="ticket",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Ticketmaster API key (or set TICKETMASTER_API_KEY env var).",
            type="secret",
            placeholder="your-ticketmaster-api-key",
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
async def artist_events(keyword: str, size: int = 10) -> dict:
    """Find upcoming events for a specific artist or attraction."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "TICKETMASTER_API_KEY env var is required. Get a free key at https://developer.ticketmaster.com",
            "success": False,
        }

    # Step 1: Search for the attraction by keyword
    attraction_endpoint = f"{_BASE_URL}/attractions.json"
    attraction_params = {"apikey": api_key, "keyword": keyword, "size": 1}

    check_host(attraction_endpoint)
    async with httpx.AsyncClient() as client:
        attr_resp = await client.get(attraction_endpoint, params=attraction_params, timeout=15)
        if not attr_resp.is_success:
            return {"error": f"Attraction search returned status {attr_resp.status_code}", "success": False}
        attr_data = attr_resp.json()

    attr_embedded = attr_data.get("_embedded", {})
    attractions = attr_embedded.get("attractions", [])
    if not attractions:
        return {
            "error": f"No attraction found matching '{keyword}'",
            "attraction_name": None,
            "attraction_id": None,
            "events": [],
            "total": 0,
            "success": False,
        }

    attraction = attractions[0]
    attraction_id = attraction.get("id")
    attraction_name = attraction.get("name")

    # Step 2: Search events for the found attraction
    events_endpoint = f"{_BASE_URL}/events.json"
    events_params: Dict[str, Any] = {
        "apikey": api_key,
        "attractionId": attraction_id,
        "size": size,
        "sort": "date,asc",
    }

    check_host(events_endpoint)
    async with httpx.AsyncClient() as client:
        ev_resp = await client.get(events_endpoint, params=events_params, timeout=15)
        if not ev_resp.is_success:
            return {"error": f"Event search returned status {ev_resp.status_code}", "success": False}
        ev_data = ev_resp.json()

    ev_embedded = ev_data.get("_embedded", {})
    raw_events = ev_embedded.get("events", [])
    events = [_parse_event(ev) for ev in raw_events]
    total = ev_data.get("page", {}).get("totalElements", len(events))

    return {
        "attraction_name": attraction_name,
        "attraction_id": attraction_id,
        "events": events,
        "total": total,
        "success": True,
    }


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------


class TicketmasterPlugin(TransformerPlugin):
    """Plugin providing Ticketmaster Discovery API skills and event formatting."""

    def __init__(self):
        super().__init__("ticketmaster")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_event": lambda _: FormatEventTransformer("format_event"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "events_search": events_search.__skill__,
            "event_details": event_details.__skill__,
            "venue_search": venue_search.__skill__,
            "venue_events": venue_events.__skill__,
            "artist_events": artist_events.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="ticketmaster",
            display_name="Ticketmaster",
            description="Search events, venues, and artist tours via the Ticketmaster Discovery API.",
            icon="ticket",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
