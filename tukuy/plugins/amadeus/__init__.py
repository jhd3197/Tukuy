"""Amadeus Travel plugin.

Provides async ``flight_search``, ``hotel_search``, ``airport_search``,
``flight_status``, and ``airport_routes`` skills using the Amadeus API.

Requires ``httpx`` (optional dependency, imported lazily at call time).
Authentication uses OAuth2 Client Credentials via ``AMADEUS_API_KEY``
and ``AMADEUS_API_SECRET`` environment variables.
"""

import os
import re
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL_TEST = "https://test.api.amadeus.com"
_BASE_URL_PROD = "https://api.amadeus.com"


# ── Helpers ────────────────────────────────────────────────────────────────


def _get_credentials() -> tuple:
    """Read Amadeus API key and secret from the environment."""
    api_key = os.environ.get("AMADEUS_API_KEY", "")
    api_secret = os.environ.get("AMADEUS_API_SECRET", "")
    return api_key, api_secret


async def _get_token(client, base_url: str) -> str:
    """Fetch an OAuth2 access token using client credentials.

    POSTs form-encoded credentials to the Amadeus token endpoint and
    returns the ``access_token`` string.  Raises ``RuntimeError`` on
    failure.
    """
    api_key, api_secret = _get_credentials()
    if not api_key or not api_secret:
        raise RuntimeError(
            "AMADEUS_API_KEY and AMADEUS_API_SECRET env vars are required. "
            "Get credentials at https://developers.amadeus.com"
        )

    token_url = f"{base_url}/v1/security/oauth2/token"
    check_host(token_url)

    resp = await client.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": api_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if not resp.is_success:
        raise RuntimeError(f"Token request failed with status {resp.status_code}")

    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("No access_token in token response")
    return token


def _fmt_duration(iso_duration: str) -> str:
    """Convert ISO 8601 duration ``PT2H30M`` to ``2h 30m``."""
    if not iso_duration:
        return ""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso_duration)
    if not match:
        return iso_duration
    hours = match.group(1)
    minutes = match.group(2)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else iso_duration


def _parse_flight_offer(raw: dict) -> dict:
    """Normalise an Amadeus flight offer into a clean dict."""
    price_info = raw.get("price", {})
    itineraries = []
    for itin in raw.get("itineraries", []):
        segments = []
        for seg in itin.get("segments", []):
            dep = seg.get("departure", {})
            arr = seg.get("arrival", {})
            segments.append({
                "departure_airport": dep.get("iataCode", ""),
                "departure_time": dep.get("at", ""),
                "arrival_airport": arr.get("iataCode", ""),
                "arrival_time": arr.get("at", ""),
                "carrier": seg.get("carrierCode", ""),
                "flight_number": seg.get("number", ""),
                "duration": _fmt_duration(seg.get("duration", "")),
                "stops": seg.get("numberOfStops", 0),
            })
        itineraries.append({
            "duration": _fmt_duration(itin.get("duration", "")),
            "segments": segments,
            "stops": max(0, len(segments) - 1),
        })

    # Booking class and seats from first traveler pricing
    traveler_pricings = raw.get("travelerPricings", [])
    booking_class = ""
    seats_remaining = None
    if traveler_pricings:
        fare_details = traveler_pricings[0].get("fareDetailsBySegment", [])
        if fare_details:
            booking_class = fare_details[0].get("class", "")
            avail = fare_details[0].get("availabilityClasses", [])
            if not avail:
                avail = fare_details[0].get("availability", {})
                if isinstance(avail, dict):
                    seats_remaining = avail.get("numberOfBookableSeats")
            else:
                seats_remaining = avail[0].get("numberOfBookableSeats") if avail else None
    if seats_remaining is None:
        seats_remaining = raw.get("numberOfBookableSeats")

    return {
        "price": {
            "total": price_info.get("total", ""),
            "currency": price_info.get("currency", ""),
            "grand_total": price_info.get("grandTotal", ""),
        },
        "itineraries": itineraries,
        "booking_class": booking_class,
        "seats_remaining": seats_remaining,
    }


def _parse_hotel_offer(raw: dict) -> dict:
    """Normalise an Amadeus hotel offer into a clean dict."""
    hotel = raw.get("hotel", raw)
    address = hotel.get("address", {})
    offers = raw.get("offers", [])

    price_info = {}
    check_in = ""
    check_out = ""
    room_description = ""
    cancellation_policy = ""

    if offers:
        offer = offers[0]
        price_raw = offer.get("price", {})
        price_info = {
            "total": price_raw.get("total", ""),
            "currency": price_raw.get("currency", ""),
        }
        check_in = offer.get("checkInDate", "")
        check_out = offer.get("checkOutDate", "")
        room = offer.get("room", {})
        room_desc = room.get("description", {})
        room_description = room_desc.get("text", "") if isinstance(room_desc, dict) else str(room_desc)
        cancel = offer.get("policies", {}).get("cancellation", {})
        cancellation_policy = cancel.get("description", {}).get("text", "") if isinstance(cancel.get("description"), dict) else cancel.get("type", "")

    return {
        "hotel_name": hotel.get("name", ""),
        "hotel_id": hotel.get("hotelId", raw.get("hotelId", "")),
        "address": {
            "lines": address.get("lines", []),
            "city": address.get("cityName", address.get("cityCode", "")),
            "country": address.get("countryCode", ""),
        },
        "rating": hotel.get("rating", ""),
        "price": price_info,
        "check_in": check_in,
        "check_out": check_out,
        "room_description": room_description,
        "cancellation_policy": cancellation_policy,
    }


def _parse_location(raw: dict) -> dict:
    """Normalise an Amadeus location into a clean dict."""
    geo = raw.get("geoCode", {})
    address = raw.get("address", {})
    return {
        "name": raw.get("name", ""),
        "iata_code": raw.get("iataCode", ""),
        "city": address.get("cityName", address.get("cityCode", "")),
        "country": address.get("countryCode", ""),
        "type": raw.get("subType", raw.get("type", "")),
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
    }


# ── Transformers ───────────────────────────────────────────────────────────


class FormatFlightTransformer(ChainableTransformer[dict, str]):
    """Format a parsed flight offer dict into a one-line summary.

    Example output: ``JFK -> LAX | 2 stops | 5h 30m | $342.50 USD``
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "itineraries" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        itineraries = value.get("itineraries", [])
        if not itineraries:
            return "No itinerary data"

        itin = itineraries[0]
        segments = itin.get("segments", [])
        if not segments:
            return "No segment data"

        origin = segments[0].get("departure_airport", "???")
        destination = segments[-1].get("arrival_airport", "???")
        stops = itin.get("stops", 0)
        duration = itin.get("duration", "")

        price = value.get("price", {})
        total = price.get("grand_total", price.get("total", ""))
        currency = price.get("currency", "")

        stop_label = f"{stops} stop{'s' if stops != 1 else ''}" if stops > 0 else "nonstop"
        price_str = f"${total} {currency}" if total else "Price N/A"

        return f"{origin} -> {destination} | {stop_label} | {duration} | {price_str}"


class FormatHotelTransformer(ChainableTransformer[dict, str]):
    """Format a parsed hotel offer dict into a one-line summary.

    Example output: ``Hotel Name ****  | $189/night | Free cancellation``
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "hotel_name" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        name = value.get("hotel_name", "Unknown Hotel")
        rating = value.get("rating", "")
        stars = ""
        if rating:
            try:
                stars = " " + "\u2605" * int(rating)
            except (ValueError, TypeError):
                pass

        price = value.get("price", {})
        total = price.get("total", "")
        currency = price.get("currency", "")
        price_str = f"${total}/night" if total else "Price N/A"

        cancellation = value.get("cancellation_policy", "")
        cancel_str = cancellation if cancellation else "See policy"

        return f"{name}{stars} | {price_str} | {cancel_str}"


# ── Shared config params ──────────────────────────────────────────────────

_COMMON_CONFIG = [
    ConfigParam(
        name="api_key",
        display_name="Amadeus API Key",
        description="Amadeus API key. Falls back to AMADEUS_API_KEY env var.",
        type="secret",
        placeholder="your-amadeus-api-key",
    ),
    ConfigParam(
        name="api_secret",
        display_name="Amadeus API Secret",
        description="Amadeus API secret. Falls back to AMADEUS_API_SECRET env var.",
        type="secret",
        placeholder="your-amadeus-api-secret",
    ),
    ConfigParam(
        name="environment",
        display_name="Environment",
        description="Amadeus API environment (test or production).",
        type="select",
        default="test",
        options=["test", "production"],
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
]


def _base_url(environment: str = "test") -> str:
    """Return the base URL for the given environment."""
    if environment == "production":
        return _BASE_URL_PROD
    return _BASE_URL_TEST


# ── Skills ─────────────────────────────────────────────────────────────────


@skill(
    name="flight_search",
    display_name="Search Flights",
    description="Search flight offers via Amadeus API (requires AMADEUS_API_KEY and AMADEUS_API_SECRET env vars).",
    category="travel",
    tags=["travel", "flights", "amadeus", "booking"],
    icon="plane",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def flight_search(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str = "",
    adults: int = 1,
    max_results: int = 5,
    travel_class: str = "ECONOMY",
    non_stop: bool = False,
    environment: str = "test",
) -> dict:
    """Search for flight offers between two airports."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    base = _base_url(environment)
    endpoint = f"{base}/v2/shopping/flight-offers"
    check_host(endpoint)

    try:
        async with httpx.AsyncClient() as client:
            token = await _get_token(client, base)
            params: Dict[str, Any] = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date,
                "adults": adults,
                "max": max_results,
                "travelClass": travel_class.upper(),
                "nonStop": str(non_stop).lower(),
            }
            if return_date:
                params["returnDate"] = return_date

            resp = await client.get(
                endpoint,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if not resp.is_success:
                return {"error": f"API returned status {resp.status_code}", "success": False}

            data = resp.json()
            offers = [_parse_flight_offer(o) for o in data.get("data", [])]
            return {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": departure_date,
                "return_date": return_date or None,
                "offers": offers,
                "count": len(offers),
                "success": True,
            }
    except RuntimeError as exc:
        return {"error": str(exc), "success": False}


@skill(
    name="hotel_search",
    display_name="Search Hotels",
    description="Search hotels in a city via Amadeus API (requires AMADEUS_API_KEY and AMADEUS_API_SECRET env vars).",
    category="travel",
    tags=["travel", "hotels", "amadeus", "accommodation"],
    icon="plane",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def hotel_search(
    city_code: str,
    radius: int = 5,
    radius_unit: str = "KM",
    ratings: str = "",
    amenities: str = "",
    environment: str = "test",
) -> dict:
    """Search for hotels in a city by IATA city code."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    base = _base_url(environment)
    endpoint = f"{base}/v1/reference-data/locations/hotels/by-city"
    check_host(endpoint)

    try:
        async with httpx.AsyncClient() as client:
            token = await _get_token(client, base)
            params: Dict[str, Any] = {
                "cityCode": city_code.upper(),
                "radius": radius,
                "radiusUnit": radius_unit.upper(),
            }
            if ratings:
                params["ratings"] = ratings
            if amenities:
                params["amenities"] = amenities

            resp = await client.get(
                endpoint,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if not resp.is_success:
                return {"error": f"API returned status {resp.status_code}", "success": False}

            data = resp.json()
            hotels = []
            for item in data.get("data", []):
                geo = item.get("geoCode", {})
                address = item.get("address", {})
                hotels.append({
                    "name": item.get("name", ""),
                    "hotel_id": item.get("hotelId", ""),
                    "geo_code": {
                        "latitude": geo.get("latitude"),
                        "longitude": geo.get("longitude"),
                    },
                    "address": {
                        "country": address.get("countryCode", ""),
                    },
                    "distance": item.get("distance", {}),
                })
            return {
                "city_code": city_code.upper(),
                "hotels": hotels,
                "count": len(hotels),
                "success": True,
            }
    except RuntimeError as exc:
        return {"error": str(exc), "success": False}


@skill(
    name="airport_search",
    display_name="Search Airports",
    description="Search airports and cities by keyword via Amadeus API (requires AMADEUS_API_KEY and AMADEUS_API_SECRET env vars).",
    category="travel",
    tags=["travel", "airports", "amadeus", "search"],
    icon="plane",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def airport_search(
    keyword: str,
    location_type: str = "AIRPORT",
    environment: str = "test",
) -> dict:
    """Search for airports or cities by keyword."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    base = _base_url(environment)
    endpoint = f"{base}/v1/reference-data/locations"
    check_host(endpoint)

    try:
        async with httpx.AsyncClient() as client:
            token = await _get_token(client, base)
            params: Dict[str, Any] = {
                "keyword": keyword,
                "subType": location_type.upper(),
            }

            resp = await client.get(
                endpoint,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if not resp.is_success:
                return {"error": f"API returned status {resp.status_code}", "success": False}

            data = resp.json()
            locations = [_parse_location(loc) for loc in data.get("data", [])]
            return {
                "keyword": keyword,
                "type": location_type.upper(),
                "locations": locations,
                "count": len(locations),
                "success": True,
            }
    except RuntimeError as exc:
        return {"error": str(exc), "success": False}


@skill(
    name="flight_status",
    display_name="Flight Status",
    description="Get flight status by carrier code, flight number, and date via Amadeus API (requires AMADEUS_API_KEY and AMADEUS_API_SECRET env vars).",
    category="travel",
    tags=["travel", "flights", "status", "amadeus"],
    icon="plane",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def flight_status(
    carrier_code: str,
    flight_number: str,
    date: str,
    environment: str = "test",
) -> dict:
    """Get schedule/status for a specific flight on a given date."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    base = _base_url(environment)
    endpoint = f"{base}/v2/schedule/flights"
    check_host(endpoint)

    try:
        async with httpx.AsyncClient() as client:
            token = await _get_token(client, base)
            params: Dict[str, Any] = {
                "carrierCode": carrier_code.upper(),
                "flightNumber": flight_number,
                "scheduledDepartureDate": date,
            }

            resp = await client.get(
                endpoint,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if not resp.is_success:
                return {"error": f"API returned status {resp.status_code}", "success": False}

            data = resp.json()
            flights = []
            for item in data.get("data", []):
                dep_points = item.get("flightPoints", [])
                departure = {}
                arrival = {}
                if len(dep_points) >= 1:
                    dep_p = dep_points[0]
                    dep_times = dep_p.get("departure", {})
                    departure = {
                        "airport": dep_p.get("iataCode", ""),
                        "terminal": dep_times.get("terminal", ""),
                        "scheduled_time": dep_times.get("timings", [{}])[0].get("value", "") if dep_times.get("timings") else "",
                    }
                if len(dep_points) >= 2:
                    arr_p = dep_points[-1]
                    arr_times = arr_p.get("arrival", {})
                    arrival = {
                        "airport": arr_p.get("iataCode", ""),
                        "terminal": arr_times.get("terminal", ""),
                        "scheduled_time": arr_times.get("timings", [{}])[0].get("value", "") if arr_times.get("timings") else "",
                    }

                legs = item.get("legs", [])
                aircraft = legs[0].get("aircraftEquipment", {}).get("aircraftType", "") if legs else ""

                flights.append({
                    "carrier_code": carrier_code.upper(),
                    "flight_number": flight_number,
                    "date": date,
                    "departure": departure,
                    "arrival": arrival,
                    "aircraft": aircraft,
                    "status": item.get("flightDesignator", {}).get("operationalSuffix", "SCHEDULED"),
                })

            return {
                "carrier_code": carrier_code.upper(),
                "flight_number": flight_number,
                "date": date,
                "flights": flights,
                "count": len(flights),
                "success": True,
            }
    except RuntimeError as exc:
        return {"error": str(exc), "success": False}


@skill(
    name="airport_routes",
    display_name="Airport Routes",
    description="Find direct flight destinations from an airport via Amadeus API (requires AMADEUS_API_KEY and AMADEUS_API_SECRET env vars).",
    category="travel",
    tags=["travel", "airports", "routes", "amadeus", "destinations"],
    icon="plane",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def airport_routes(
    departure_airport: str,
    environment: str = "test",
) -> dict:
    """Find all direct-flight destinations from an airport."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    base = _base_url(environment)
    endpoint = f"{base}/v1/airport/direct-destinations"
    check_host(endpoint)

    try:
        async with httpx.AsyncClient() as client:
            token = await _get_token(client, base)
            params: Dict[str, Any] = {
                "departureAirportCode": departure_airport.upper(),
            }

            resp = await client.get(
                endpoint,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if not resp.is_success:
                return {"error": f"API returned status {resp.status_code}", "success": False}

            data = resp.json()
            destinations = []
            for item in data.get("data", []):
                destinations.append({
                    "name": item.get("name", ""),
                    "iata_code": item.get("iataCode", ""),
                    "type": item.get("subType", item.get("type", "")),
                })

            return {
                "departure_airport": departure_airport.upper(),
                "destinations": destinations,
                "count": len(destinations),
                "success": True,
            }
    except RuntimeError as exc:
        return {"error": str(exc), "success": False}


# ── Plugin class ───────────────────────────────────────────────────────────


class AmadeusPlugin(TransformerPlugin):
    """Plugin providing Amadeus travel skills and flight/hotel formatters."""

    def __init__(self):
        super().__init__("amadeus")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_flight": lambda _: FormatFlightTransformer("format_flight"),
            "format_hotel": lambda _: FormatHotelTransformer("format_hotel"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "flight_search": flight_search.__skill__,
            "hotel_search": hotel_search.__skill__,
            "airport_search": airport_search.__skill__,
            "flight_status": flight_status.__skill__,
            "airport_routes": airport_routes.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="amadeus",
            display_name="Amadeus Travel",
            description="Search flights, hotels, and airports via Amadeus API.",
            icon="plane",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
