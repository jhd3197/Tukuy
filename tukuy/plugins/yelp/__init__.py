"""Yelp Fusion plugin.

Provides async ``yelp_search``, ``yelp_details``, ``yelp_reviews``,
``yelp_match``, and ``yelp_autocomplete`` skills using the Yelp Fusion API.

Requires ``httpx`` (optional dependency, imported lazily at call time)
and a ``YELP_API_KEY`` environment variable.
"""

import os
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.yelp.com/v3"

_METERS_PER_MILE = 1609.34


def _get_api_key() -> Optional[str]:
    """Read the Yelp API key from the environment."""
    return os.environ.get("YELP_API_KEY")


def _auth_headers() -> dict:
    """Build Authorization header dict for Bearer token auth."""
    key = _get_api_key()
    return {"Authorization": f"Bearer {key}"} if key else {}


def _format_rating(rating: Optional[float]) -> str:
    """Format a numeric rating as star characters."""
    if rating is None:
        return ""
    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    return "\u2605" * full + ("\u00bd" if half else "")


def _format_price(price: Optional[str]) -> str:
    """Return the price string as-is (already dollar signs) or empty."""
    return price if price else ""


def _meters_to_miles(meters: Optional[float]) -> Optional[float]:
    """Convert metres to miles, rounded to 1 decimal place."""
    if meters is None:
        return None
    return round(meters / _METERS_PER_MILE, 1)


def _parse_categories(categories: Optional[List[dict]]) -> List[str]:
    """Extract category titles from a Yelp categories list."""
    if not categories:
        return []
    return [c.get("title", "") for c in categories if c.get("title")]


def _parse_location(location: Optional[dict]) -> str:
    """Build a single-line address string from a Yelp location dict."""
    if not location:
        return ""
    parts = []
    addr = location.get("address1", "")
    if addr:
        parts.append(addr)
    city = location.get("city", "")
    state = location.get("state", "")
    zip_code = location.get("zip_code", "")
    city_state = ", ".join(p for p in [city, state] if p)
    if city_state:
        parts.append(city_state)
    if zip_code:
        parts.append(zip_code)
    return ", ".join(parts)


def _parse_business(biz: dict) -> dict:
    """Normalise a Yelp business object into a clean flat dict."""
    location = biz.get("location") or {}
    return {
        "id": biz.get("id", ""),
        "name": biz.get("name", ""),
        "rating": biz.get("rating"),
        "rating_display": _format_rating(biz.get("rating")),
        "review_count": biz.get("review_count", 0),
        "price": _format_price(biz.get("price")),
        "distance_miles": _meters_to_miles(biz.get("distance")),
        "location": _parse_location(location),
        "phone": biz.get("display_phone", biz.get("phone", "")),
        "url": biz.get("url", ""),
        "categories": _parse_categories(biz.get("categories")),
        "image_url": biz.get("image_url", ""),
        "is_closed": biz.get("is_closed", False),
    }


def _parse_hours(hours: Optional[List[dict]]) -> List[dict]:
    """Parse the hours array from a Yelp business detail response."""
    if not hours:
        return []
    result = []
    for entry in hours:
        for open_block in entry.get("open", []):
            result.append({
                "day": open_block.get("day"),
                "start": open_block.get("start", ""),
                "end": open_block.get("end", ""),
                "is_overnight": open_block.get("is_overnight", False),
            })
    return result


# ── Transformer ────────────────────────────────────────────────────────────


class FormatBusinessTransformer(ChainableTransformer[dict, str]):
    """Format a Yelp business dict into a human-readable one-liner.

    Example output::

        Restaurant Name -- 4.5 (342 reviews) -- $$ -- 0.3 mi -- Open
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "name" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        parts = [value.get("name", "Unknown")]

        rating = value.get("rating")
        review_count = value.get("review_count")
        if rating is not None:
            rating_str = str(rating)
            if review_count is not None:
                rating_str += f" ({review_count} reviews)"
            parts.append(rating_str)

        price = value.get("price")
        if price:
            parts.append(price)

        distance = value.get("distance_miles")
        if distance is not None:
            parts.append(f"{distance} mi")

        is_closed = value.get("is_closed")
        if is_closed is not None:
            parts.append("Closed" if is_closed else "Open")

        return " \u2014 ".join(parts)


# ── Skills ─────────────────────────────────────────────────────────────────


@skill(
    name="yelp_search",
    display_name="Yelp Search",
    description="Search for businesses on Yelp by term, location, category, price, and radius.",
    category="local_business",
    tags=["yelp", "restaurants", "businesses", "local", "search"],
    icon="utensils",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="Yelp API Key",
            description="Yelp Fusion API key. Falls back to YELP_API_KEY env var.",
            type="secret",
            placeholder="your-yelp-api-key",
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
async def yelp_search(
    term: str,
    location: str,
    categories: str = "",
    price: str = "",
    radius: int = 0,
    sort_by: str = "best_match",
    limit: int = 5,
) -> dict:
    """Search for businesses on Yelp."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "YELP_API_KEY env var is required. Get a key at https://www.yelp.com/developers",
            "success": False,
        }

    endpoint = f"{_BASE_URL}/businesses/search"
    params: Dict[str, Any] = {
        "term": term,
        "location": location,
        "sort_by": sort_by,
        "limit": max(1, min(limit, 50)),
    }
    if categories:
        params["categories"] = categories
    if price:
        params["price"] = price
    if radius > 0:
        params["radius"] = min(radius, 40000)

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            endpoint,
            params=params,
            headers=_auth_headers(),
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        businesses = [_parse_business(b) for b in data.get("businesses", [])]
        return {
            "term": term,
            "location": location,
            "businesses": businesses,
            "total": data.get("total", 0),
            "count": len(businesses),
            "success": True,
        }


@skill(
    name="yelp_details",
    display_name="Yelp Business Details",
    description="Get full details for a business on Yelp by its ID.",
    category="local_business",
    tags=["yelp", "business", "details", "hours", "photos"],
    icon="store",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="Yelp API Key",
            description="Yelp Fusion API key. Falls back to YELP_API_KEY env var.",
            type="secret",
            placeholder="your-yelp-api-key",
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
async def yelp_details(business_id: str) -> dict:
    """Get full details for a Yelp business."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "YELP_API_KEY env var is required. Get a key at https://www.yelp.com/developers",
            "success": False,
        }

    endpoint = f"{_BASE_URL}/businesses/{business_id}"

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            endpoint,
            headers=_auth_headers(),
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        biz = resp.json()
        location = biz.get("location") or {}
        coordinates = biz.get("coordinates") or {}
        return {
            "id": biz.get("id", ""),
            "name": biz.get("name", ""),
            "rating": biz.get("rating"),
            "rating_display": _format_rating(biz.get("rating")),
            "review_count": biz.get("review_count", 0),
            "price": _format_price(biz.get("price")),
            "phone": biz.get("display_phone", biz.get("phone", "")),
            "url": biz.get("url", ""),
            "categories": _parse_categories(biz.get("categories")),
            "image_url": biz.get("image_url", ""),
            "photos": biz.get("photos", []),
            "is_closed": biz.get("is_closed", False),
            "location": _parse_location(location),
            "coordinates": {
                "latitude": coordinates.get("latitude"),
                "longitude": coordinates.get("longitude"),
            },
            "hours": _parse_hours(biz.get("hours")),
            "is_open_now": (biz.get("hours") or [{}])[0].get("is_open_now", None) if biz.get("hours") else None,
            "transactions": biz.get("transactions", []),
            "special_hours": biz.get("special_hours", []),
            "success": True,
        }


@skill(
    name="yelp_reviews",
    display_name="Yelp Reviews",
    description="Get up to 3 reviews for a Yelp business (API limit).",
    category="local_business",
    tags=["yelp", "reviews", "ratings", "feedback"],
    icon="message-square",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="Yelp API Key",
            description="Yelp Fusion API key. Falls back to YELP_API_KEY env var.",
            type="secret",
            placeholder="your-yelp-api-key",
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
async def yelp_reviews(business_id: str, sort_by: str = "yelp_sort") -> dict:
    """Get reviews for a Yelp business (max 3 per API limits)."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "YELP_API_KEY env var is required. Get a key at https://www.yelp.com/developers",
            "success": False,
        }

    endpoint = f"{_BASE_URL}/businesses/{business_id}/reviews"
    params: Dict[str, Any] = {}
    if sort_by in ("yelp_sort", "newest"):
        params["sort_by"] = sort_by

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            endpoint,
            params=params,
            headers=_auth_headers(),
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        raw_reviews = data.get("reviews", [])
        reviews = []
        for r in raw_reviews:
            user = r.get("user") or {}
            reviews.append({
                "rating": r.get("rating"),
                "rating_display": _format_rating(r.get("rating")),
                "text": r.get("text", ""),
                "user_name": user.get("name", ""),
                "user_image_url": user.get("image_url", ""),
                "time_created": r.get("time_created", ""),
                "url": r.get("url", ""),
            })
        return {
            "business_id": business_id,
            "reviews": reviews,
            "total": data.get("total", 0),
            "count": len(reviews),
            "success": True,
        }


@skill(
    name="yelp_match",
    display_name="Yelp Business Match",
    description="Match a business on Yelp by name and location to find its Yelp ID.",
    category="local_business",
    tags=["yelp", "match", "business", "lookup"],
    icon="search",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="Yelp API Key",
            description="Yelp Fusion API key. Falls back to YELP_API_KEY env var.",
            type="secret",
            placeholder="your-yelp-api-key",
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
async def yelp_match(name: str, city: str, state: str, country: str) -> dict:
    """Match a business by name and location on Yelp."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "YELP_API_KEY env var is required. Get a key at https://www.yelp.com/developers",
            "success": False,
        }

    endpoint = f"{_BASE_URL}/businesses/matches"
    params: Dict[str, str] = {
        "name": name,
        "city": city,
        "state": state,
        "country": country,
    }

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            endpoint,
            params=params,
            headers=_auth_headers(),
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        matches = data.get("businesses", [])
        if not matches:
            return {
                "name": name,
                "city": city,
                "state": state,
                "country": country,
                "error": "No matching business found",
                "success": False,
            }
        best = matches[0]
        location = best.get("location") or {}
        return {
            "id": best.get("id", ""),
            "name": best.get("name", ""),
            "phone": best.get("display_phone", best.get("phone", "")),
            "location": _parse_location(location),
            "categories": _parse_categories(best.get("categories")),
            "url": best.get("url", ""),
            "query_name": name,
            "query_city": city,
            "query_state": state,
            "query_country": country,
            "matches_found": len(matches),
            "success": True,
        }


@skill(
    name="yelp_autocomplete",
    display_name="Yelp Autocomplete",
    description="Get autocomplete suggestions for businesses, terms, and categories on Yelp.",
    category="local_business",
    tags=["yelp", "autocomplete", "search", "suggest"],
    icon="type",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="Yelp API Key",
            description="Yelp Fusion API key. Falls back to YELP_API_KEY env var.",
            type="secret",
            placeholder="your-yelp-api-key",
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
async def yelp_autocomplete(
    text: str,
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> dict:
    """Get autocomplete suggestions from Yelp."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "YELP_API_KEY env var is required. Get a key at https://www.yelp.com/developers",
            "success": False,
        }

    endpoint = f"{_BASE_URL}/autocomplete"
    params: Dict[str, Any] = {"text": text}
    if latitude != 0.0 and longitude != 0.0:
        params["latitude"] = latitude
        params["longitude"] = longitude

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            endpoint,
            params=params,
            headers=_auth_headers(),
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

        businesses = []
        for b in data.get("businesses", []):
            businesses.append({
                "id": b.get("id", ""),
                "name": b.get("name", ""),
            })

        terms = []
        for t in data.get("terms", []):
            terms.append(t.get("text", ""))

        categories = []
        for c in data.get("categories", []):
            categories.append({
                "alias": c.get("alias", ""),
                "title": c.get("title", ""),
            })

        return {
            "query": text,
            "businesses": businesses,
            "terms": terms,
            "categories": categories,
            "success": True,
        }


# ── Plugin class ───────────────────────────────────────────────────────────


class YelpPlugin(TransformerPlugin):
    """Plugin providing Yelp Fusion API skills and business formatting transformer."""

    def __init__(self):
        super().__init__("yelp")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_business": lambda _: FormatBusinessTransformer("format_business"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "yelp_search": yelp_search.__skill__,
            "yelp_details": yelp_details.__skill__,
            "yelp_reviews": yelp_reviews.__skill__,
            "yelp_match": yelp_match.__skill__,
            "yelp_autocomplete": yelp_autocomplete.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="yelp",
            display_name="Yelp",
            description="Search businesses, read reviews, and get details via Yelp Fusion API.",
            icon="utensils",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
