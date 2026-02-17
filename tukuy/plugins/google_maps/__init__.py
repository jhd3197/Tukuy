"""Google Maps Platform plugin.

Provides async skills for the Google Maps Platform APIs including Places
search, place details, directions, distance matrix, geocoding, reverse
geocoding, and static map URL generation.

Requires ``httpx`` (optional dependency, imported lazily at call time)
and a ``GOOGLE_MAPS_API_KEY`` environment variable.
"""

import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://maps.googleapis.com/maps/api"

_API_KEY_ERROR = (
    "GOOGLE_MAPS_API_KEY env var is required. "
    "Get a key at https://console.cloud.google.com/google/maps-apis"
)

_HTTPX_ERROR = "httpx is required. Install with: pip install httpx"

_DEFAULT_TIMEOUT = 15

_CONFIG_PARAMS = [
    ConfigParam(
        name="api_key",
        display_name="Google Maps API Key",
        description="Google Maps Platform API key. Falls back to GOOGLE_MAPS_API_KEY env var.",
        type="secret",
        placeholder="your-google-maps-api-key",
    ),
    ConfigParam(
        name="timeout",
        display_name="Timeout",
        description="Request timeout in seconds.",
        type="number",
        default=_DEFAULT_TIMEOUT,
        min=1,
        max=60,
        unit="seconds",
    ),
]


# ── Helpers ────────────────────────────────────────────────────────────────


def _get_api_key() -> Optional[str]:
    """Read the Google Maps API key from the environment."""
    return os.environ.get("GOOGLE_MAPS_API_KEY")


def _parse_place(raw: dict) -> dict:
    """Normalise a Google Places result into a compact dict."""
    geometry = raw.get("geometry", {})
    location = geometry.get("location", {})
    return {
        "name": raw.get("name", ""),
        "address": raw.get("formatted_address", ""),
        "rating": raw.get("rating"),
        "user_ratings_total": raw.get("user_ratings_total"),
        "location": {
            "lat": location.get("lat"),
            "lng": location.get("lng"),
        },
        "place_id": raw.get("place_id", ""),
        "types": raw.get("types", []),
        "business_status": raw.get("business_status", ""),
        "price_level": raw.get("price_level"),
    }


def _parse_route(raw: dict) -> dict:
    """Normalise a Google Directions route into a compact dict."""
    legs = raw.get("legs", [])
    steps = []
    total_distance = ""
    total_duration = ""

    if legs:
        leg = legs[0]
        total_distance = leg.get("distance", {}).get("text", "")
        total_duration = leg.get("duration", {}).get("text", "")
        for step in leg.get("steps", []):
            steps.append({
                "instruction": step.get("html_instructions", ""),
                "distance": step.get("distance", {}).get("text", ""),
                "duration": step.get("duration", {}).get("text", ""),
                "travel_mode": step.get("travel_mode", ""),
            })

    return {
        "summary": raw.get("summary", ""),
        "distance": total_distance,
        "duration": total_duration,
        "steps": steps,
        "overview_polyline": raw.get("overview_polyline", {}).get("points", ""),
        "warnings": raw.get("warnings", []),
        "copyrights": raw.get("copyrights", ""),
    }


class FormatDirectionsTransformer(ChainableTransformer[dict, str]):
    """Format a directions result dict into a human-readable step-by-step string."""

    def validate(self, value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        # Accept either a single route dict or a full response with "routes" list
        if "steps" in value:
            return True
        if "routes" in value and isinstance(value["routes"], list):
            return True
        return False

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        # If this is a full response dict, extract the first route
        if "routes" in value and isinstance(value["routes"], list):
            routes = value["routes"]
            if not routes:
                return "No routes found."
            route = routes[0]
        else:
            route = value

        lines: List[str] = []

        summary = route.get("summary", "")
        distance = route.get("distance", "")
        duration = route.get("duration", "")

        if summary:
            lines.append(f"Route: {summary}")
        if distance and duration:
            lines.append(f"Total: {distance} ({duration})")
        elif distance:
            lines.append(f"Total distance: {distance}")
        elif duration:
            lines.append(f"Total duration: {duration}")

        lines.append("")

        steps = route.get("steps", [])
        for i, step in enumerate(steps, 1):
            instruction = step.get("instruction", "")
            step_distance = step.get("distance", "")
            step_duration = step.get("duration", "")
            detail = ""
            if step_distance and step_duration:
                detail = f" ({step_distance}, {step_duration})"
            elif step_distance:
                detail = f" ({step_distance})"
            elif step_duration:
                detail = f" ({step_duration})"
            lines.append(f"{i}. {instruction}{detail}")

        warnings = route.get("warnings", [])
        if warnings:
            lines.append("")
            for warning in warnings:
                lines.append(f"Warning: {warning}")

        return "\n".join(lines)


# ── Skills ─────────────────────────────────────────────────────────────────


@skill(
    name="maps_places_search",
    display_name="Search Places",
    description="Search for places using the Google Places API (requires GOOGLE_MAPS_API_KEY env var).",
    category="maps",
    tags=["google", "maps", "places", "search", "location"],
    icon="search",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_CONFIG_PARAMS,
)
async def maps_places_search(
    query: str,
    location: str = "",
    radius: int = 5000,
    type: str = "",
) -> dict:
    """Search for places using Google Places Text Search API.

    Args:
        query: Search query string (e.g. "restaurants in Sydney").
        location: Latitude,longitude to bias results (e.g. "33.8688,151.2093").
        radius: Search radius in meters (default 5000).
        type: Place type filter (e.g. "restaurant", "cafe", "hotel").
    """
    try:
        import httpx
    except ImportError:
        return {"error": _HTTPX_ERROR, "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": _API_KEY_ERROR, "success": False}

    url = f"{_BASE_URL}/place/textsearch/json"
    check_host(url)

    params: Dict[str, Any] = {
        "query": query,
        "key": api_key,
        "radius": radius,
    }
    if location:
        params["location"] = location
    if type:
        params["type"] = type

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=_DEFAULT_TIMEOUT)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        status = data.get("status", "")
        if status != "OK":
            error_msg = data.get("error_message", status)
            if status == "ZERO_RESULTS":
                return {"query": query, "places": [], "total": 0, "success": True}
            return {"error": f"Google Maps API error: {error_msg}", "status": status, "success": False}
        results = data.get("results", [])
        places = [_parse_place(r) for r in results]
        return {
            "query": query,
            "places": places,
            "total": len(places),
            "success": True,
        }


@skill(
    name="maps_place_details",
    display_name="Place Details",
    description="Get full details for a place by its place_id (requires GOOGLE_MAPS_API_KEY env var).",
    category="maps",
    tags=["google", "maps", "places", "details", "reviews"],
    icon="info",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_CONFIG_PARAMS,
)
async def maps_place_details(
    place_id: str,
    fields: str = "name,formatted_address,formatted_phone_number,rating,reviews,opening_hours,website,url,geometry,photos,types,price_level",
) -> dict:
    """Get detailed information about a place.

    Args:
        place_id: Google Maps place ID (e.g. "ChIJN1t_tDeuEmsRUsoyG83frY4").
        fields: Comma-separated list of place data fields to return.
    """
    try:
        import httpx
    except ImportError:
        return {"error": _HTTPX_ERROR, "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": _API_KEY_ERROR, "success": False}

    url = f"{_BASE_URL}/place/details/json"
    check_host(url)

    params: Dict[str, Any] = {
        "place_id": place_id,
        "fields": fields,
        "key": api_key,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=_DEFAULT_TIMEOUT)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        status = data.get("status", "")
        if status != "OK":
            error_msg = data.get("error_message", status)
            return {"error": f"Google Maps API error: {error_msg}", "status": status, "success": False}
        result = data.get("result", {})

        # Normalise geometry for convenience
        geometry = result.get("geometry", {})
        location = geometry.get("location", {})

        # Normalise opening hours
        opening_hours = result.get("opening_hours", {})
        hours_info = None
        if opening_hours:
            hours_info = {
                "open_now": opening_hours.get("open_now"),
                "weekday_text": opening_hours.get("weekday_text", []),
            }

        # Normalise reviews
        raw_reviews = result.get("reviews", [])
        reviews = []
        for review in raw_reviews:
            reviews.append({
                "author": review.get("author_name", ""),
                "rating": review.get("rating"),
                "text": review.get("text", ""),
                "time": review.get("relative_time_description", ""),
            })

        # Normalise photos
        raw_photos = result.get("photos", [])
        photos = []
        for photo in raw_photos:
            ref = photo.get("photo_reference", "")
            if ref:
                photo_url = (
                    f"{_BASE_URL}/place/photo"
                    f"?maxwidth=800&photo_reference={ref}&key={api_key}"
                )
                photos.append({
                    "photo_reference": ref,
                    "url": photo_url,
                    "width": photo.get("width"),
                    "height": photo.get("height"),
                    "attributions": photo.get("html_attributions", []),
                })

        return {
            "place_id": place_id,
            "name": result.get("name", ""),
            "address": result.get("formatted_address", ""),
            "phone": result.get("formatted_phone_number", ""),
            "rating": result.get("rating"),
            "user_ratings_total": result.get("user_ratings_total"),
            "price_level": result.get("price_level"),
            "website": result.get("website", ""),
            "google_maps_url": result.get("url", ""),
            "location": {
                "lat": location.get("lat"),
                "lng": location.get("lng"),
            },
            "types": result.get("types", []),
            "opening_hours": hours_info,
            "reviews": reviews,
            "photos": photos,
            "success": True,
        }


@skill(
    name="maps_directions",
    display_name="Get Directions",
    description="Get directions between two points using the Google Directions API (requires GOOGLE_MAPS_API_KEY env var).",
    category="maps",
    tags=["google", "maps", "directions", "route", "navigation"],
    icon="navigation",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_CONFIG_PARAMS,
)
async def maps_directions(
    origin: str,
    destination: str,
    mode: str = "driving",
    alternatives: bool = False,
) -> dict:
    """Get directions between an origin and destination.

    Args:
        origin: Starting point (address or lat,lng).
        destination: Ending point (address or lat,lng).
        mode: Travel mode — "driving", "walking", "bicycling", or "transit".
        alternatives: Whether to return alternative routes.
    """
    try:
        import httpx
    except ImportError:
        return {"error": _HTTPX_ERROR, "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": _API_KEY_ERROR, "success": False}

    url = f"{_BASE_URL}/directions/json"
    check_host(url)

    params: Dict[str, Any] = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "alternatives": str(alternatives).lower(),
        "key": api_key,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=_DEFAULT_TIMEOUT)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        status = data.get("status", "")
        if status != "OK":
            error_msg = data.get("error_message", status)
            if status == "NOT_FOUND":
                return {
                    "error": "One or both locations could not be found.",
                    "status": status,
                    "success": False,
                }
            if status == "ZERO_RESULTS":
                return {
                    "error": "No route found between the specified locations.",
                    "status": status,
                    "success": False,
                }
            return {"error": f"Google Maps API error: {error_msg}", "status": status, "success": False}

        raw_routes = data.get("routes", [])
        routes = [_parse_route(r) for r in raw_routes]
        return {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "routes": routes,
            "total_routes": len(routes),
            "success": True,
        }


@skill(
    name="maps_distance_matrix",
    display_name="Distance Matrix",
    description="Calculate distances and durations between multiple origins and destinations (requires GOOGLE_MAPS_API_KEY env var).",
    category="maps",
    tags=["google", "maps", "distance", "matrix", "duration"],
    icon="grid",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_CONFIG_PARAMS,
)
async def maps_distance_matrix(
    origins: str,
    destinations: str,
    mode: str = "driving",
) -> dict:
    """Calculate travel distance and time for multiple origins and destinations.

    Args:
        origins: Pipe-separated origins (e.g. "New York|Boston|Philadelphia").
        destinations: Pipe-separated destinations (e.g. "Washington DC|Baltimore").
        mode: Travel mode — "driving", "walking", "bicycling", or "transit".
    """
    try:
        import httpx
    except ImportError:
        return {"error": _HTTPX_ERROR, "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": _API_KEY_ERROR, "success": False}

    url = f"{_BASE_URL}/distancematrix/json"
    check_host(url)

    params: Dict[str, Any] = {
        "origins": origins,
        "destinations": destinations,
        "mode": mode,
        "key": api_key,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=_DEFAULT_TIMEOUT)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        status = data.get("status", "")
        if status != "OK":
            error_msg = data.get("error_message", status)
            return {"error": f"Google Maps API error: {error_msg}", "status": status, "success": False}

        origin_addresses = data.get("origin_addresses", [])
        destination_addresses = data.get("destination_addresses", [])
        raw_rows = data.get("rows", [])

        matrix: List[List[dict]] = []
        for row in raw_rows:
            elements = []
            for element in row.get("elements", []):
                el_status = element.get("status", "")
                if el_status == "OK":
                    elements.append({
                        "distance": element.get("distance", {}).get("text", ""),
                        "distance_meters": element.get("distance", {}).get("value"),
                        "duration": element.get("duration", {}).get("text", ""),
                        "duration_seconds": element.get("duration", {}).get("value"),
                        "status": "OK",
                    })
                else:
                    elements.append({
                        "distance": None,
                        "distance_meters": None,
                        "duration": None,
                        "duration_seconds": None,
                        "status": el_status,
                    })
            matrix.append(elements)

        return {
            "origin_addresses": origin_addresses,
            "destination_addresses": destination_addresses,
            "matrix": matrix,
            "mode": mode,
            "success": True,
        }


@skill(
    name="maps_geocode",
    display_name="Geocode Address",
    description="Convert an address to coordinates using the Google Geocoding API (requires GOOGLE_MAPS_API_KEY env var).",
    category="maps",
    tags=["google", "maps", "geocode", "address", "coordinates"],
    icon="map-pin",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_CONFIG_PARAMS,
)
async def maps_geocode(address: str) -> dict:
    """Forward geocode an address to coordinates.

    Args:
        address: The address to geocode (e.g. "1600 Amphitheatre Parkway, Mountain View, CA").
    """
    try:
        import httpx
    except ImportError:
        return {"error": _HTTPX_ERROR, "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": _API_KEY_ERROR, "success": False}

    url = f"{_BASE_URL}/geocode/json"
    check_host(url)

    params: Dict[str, Any] = {
        "address": address,
        "key": api_key,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=_DEFAULT_TIMEOUT)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        status = data.get("status", "")
        if status != "OK":
            error_msg = data.get("error_message", status)
            if status == "ZERO_RESULTS":
                return {"query": address, "error": "No results found.", "success": False}
            return {"error": f"Google Maps API error: {error_msg}", "status": status, "success": False}

        results = data.get("results", [])
        if not results:
            return {"query": address, "error": "No results found.", "success": False}

        result = results[0]
        geometry = result.get("geometry", {})
        location = geometry.get("location", {})

        # Parse address components
        raw_components = result.get("address_components", [])
        components: Dict[str, str] = {}
        for comp in raw_components:
            types = comp.get("types", [])
            name = comp.get("long_name", "")
            short = comp.get("short_name", "")
            if "country" in types:
                components["country"] = name
                components["country_code"] = short
            elif "administrative_area_level_1" in types:
                components["state"] = name
            elif "locality" in types:
                components["city"] = name
            elif "postal_code" in types:
                components["postcode"] = short
            elif "route" in types:
                components["road"] = name
            elif "street_number" in types:
                components["street_number"] = name

        return {
            "query": address,
            "formatted_address": result.get("formatted_address", ""),
            "lat": location.get("lat"),
            "lng": location.get("lng"),
            "components": components,
            "place_id": result.get("place_id", ""),
            "location_type": geometry.get("location_type", ""),
            "success": True,
        }


@skill(
    name="maps_reverse_geocode",
    display_name="Reverse Geocode",
    description="Convert coordinates to an address using the Google Geocoding API (requires GOOGLE_MAPS_API_KEY env var).",
    category="maps",
    tags=["google", "maps", "geocode", "reverse", "coordinates", "address"],
    icon="map",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_CONFIG_PARAMS,
)
async def maps_reverse_geocode(latitude: float, longitude: float) -> dict:
    """Reverse geocode coordinates to an address.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
    """
    try:
        import httpx
    except ImportError:
        return {"error": _HTTPX_ERROR, "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": _API_KEY_ERROR, "success": False}

    url = f"{_BASE_URL}/geocode/json"
    check_host(url)

    params: Dict[str, Any] = {
        "latlng": f"{latitude},{longitude}",
        "key": api_key,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=_DEFAULT_TIMEOUT)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        status = data.get("status", "")
        if status != "OK":
            error_msg = data.get("error_message", status)
            if status == "ZERO_RESULTS":
                return {
                    "latitude": latitude,
                    "longitude": longitude,
                    "error": "No results found.",
                    "success": False,
                }
            return {"error": f"Google Maps API error: {error_msg}", "status": status, "success": False}

        results = data.get("results", [])
        if not results:
            return {
                "latitude": latitude,
                "longitude": longitude,
                "error": "No results found.",
                "success": False,
            }

        result = results[0]

        # Parse address components
        raw_components = result.get("address_components", [])
        components: Dict[str, str] = {}
        for comp in raw_components:
            types = comp.get("types", [])
            name = comp.get("long_name", "")
            short = comp.get("short_name", "")
            if "country" in types:
                components["country"] = name
                components["country_code"] = short
            elif "administrative_area_level_1" in types:
                components["state"] = name
            elif "locality" in types:
                components["city"] = name
            elif "postal_code" in types:
                components["postcode"] = short
            elif "route" in types:
                components["road"] = name
            elif "street_number" in types:
                components["street_number"] = name

        return {
            "latitude": latitude,
            "longitude": longitude,
            "formatted_address": result.get("formatted_address", ""),
            "components": components,
            "place_id": result.get("place_id", ""),
            "success": True,
        }


@skill(
    name="maps_static_map",
    display_name="Static Map URL",
    description="Generate a Google Static Maps image URL (requires GOOGLE_MAPS_API_KEY env var).",
    category="maps",
    tags=["google", "maps", "static", "image", "url"],
    icon="image",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=False,
    required_imports=[],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="Google Maps API Key",
            description="Google Maps Platform API key. Falls back to GOOGLE_MAPS_API_KEY env var.",
            type="secret",
            placeholder="your-google-maps-api-key",
        ),
    ],
)
async def maps_static_map(
    center: str,
    zoom: int = 13,
    size: str = "600x400",
    markers: str = "",
) -> dict:
    """Generate a Google Static Maps image URL.

    Args:
        center: Center of the map (address or lat,lng).
        zoom: Zoom level (0 = world, 21 = building). Default is 13.
        size: Image dimensions as WIDTHxHEIGHT (e.g. "600x400").
        markers: Marker descriptors (e.g. "color:red|label:A|New York").
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": _API_KEY_ERROR, "success": False}

    params: Dict[str, Any] = {
        "center": center,
        "zoom": zoom,
        "size": size,
        "key": api_key,
    }
    if markers:
        params["markers"] = markers

    url = f"{_BASE_URL}/staticmap?{urlencode(params)}"
    return {
        "url": url,
        "center": center,
        "zoom": zoom,
        "size": size,
        "success": True,
    }


# ── Plugin class ───────────────────────────────────────────────────────────


class GoogleMapsPlugin(TransformerPlugin):
    """Plugin providing Google Maps Platform skills and transformers."""

    def __init__(self):
        super().__init__("google_maps")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_directions": lambda _: FormatDirectionsTransformer("format_directions"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "maps_places_search": maps_places_search.__skill__,
            "maps_place_details": maps_place_details.__skill__,
            "maps_directions": maps_directions.__skill__,
            "maps_distance_matrix": maps_distance_matrix.__skill__,
            "maps_geocode": maps_geocode.__skill__,
            "maps_reverse_geocode": maps_reverse_geocode.__skill__,
            "maps_static_map": maps_static_map.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="google_maps",
            display_name="Google Maps",
            description="Google Maps Platform integration — places search, directions, geocoding, distance matrix, and static maps.",
            icon="map",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
