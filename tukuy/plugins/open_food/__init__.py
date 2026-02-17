"""Open Food Facts plugin.

Provides async skills for looking up food/nutrition data by barcode
using the Open Food Facts API (free, no key required, unlimited).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://world.openfoodfacts.org/api/v2"


# -- Skills ------------------------------------------------------------------


@skill(
    name="food_barcode",
    display_name="Food Barcode Lookup",
    description="Look up food/nutrition info by barcode (Open Food Facts, free, no key required).",
    category="open_food",
    tags=["food", "nutrition", "barcode", "health"],
    icon="utensils",
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
async def food_barcode(
    barcode: str,
    timeout: int = 15,
) -> dict:
    """Look up food product information by barcode.

    Args:
        barcode: Product barcode (EAN/UPC).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    barcode = barcode.strip()
    if not barcode:
        return {"error": "Barcode must not be empty.", "success": False}

    url = f"{_BASE_URL}/product/{barcode}"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=timeout)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    if data.get("status") != 1:
        return {"error": "Product not found.", "barcode": barcode, "success": False}

    product = data.get("product", {})
    nutrients = product.get("nutriments", {})

    return {
        "barcode": barcode,
        "name": product.get("product_name", ""),
        "brand": product.get("brands", ""),
        "categories": product.get("categories", ""),
        "quantity": product.get("quantity", ""),
        "image_url": product.get("image_url", ""),
        "ingredients_text": product.get("ingredients_text", ""),
        "allergens": product.get("allergens", ""),
        "nutriscore_grade": product.get("nutriscore_grade", ""),
        "ecoscore_grade": product.get("ecoscore_grade", ""),
        "nutrition_per_100g": {
            "energy_kcal": nutrients.get("energy-kcal_100g"),
            "fat": nutrients.get("fat_100g"),
            "saturated_fat": nutrients.get("saturated-fat_100g"),
            "carbohydrates": nutrients.get("carbohydrates_100g"),
            "sugars": nutrients.get("sugars_100g"),
            "fiber": nutrients.get("fiber_100g"),
            "proteins": nutrients.get("proteins_100g"),
            "salt": nutrients.get("salt_100g"),
            "sodium": nutrients.get("sodium_100g"),
        },
        "countries": product.get("countries", ""),
        "success": True,
    }


@skill(
    name="food_search",
    display_name="Search Food Products",
    description="Search for food products by name (Open Food Facts, free, no key required).",
    category="open_food",
    tags=["food", "search", "nutrition"],
    icon="search",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def food_search(query: str, limit: int = 10) -> dict:
    """Search for food products by name.

    Args:
        query: Product name or keywords.
        limit: Maximum number of results (default 10).
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    query = query.strip()
    if not query:
        return {"error": "Query must not be empty.", "success": False}

    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": min(limit, 50),
    }

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    products = []
    for p in data.get("products", [])[:limit]:
        products.append({
            "name": p.get("product_name", ""),
            "brand": p.get("brands", ""),
            "barcode": p.get("code", ""),
            "nutriscore": p.get("nutriscore_grade", ""),
            "categories": p.get("categories", ""),
            "image_url": p.get("image_small_url", ""),
        })

    return {
        "query": query,
        "products": products,
        "total_found": data.get("count", 0),
        "count": len(products),
        "success": True,
    }


class OpenFoodPlugin(TransformerPlugin):
    """Plugin providing food/nutrition lookup skills."""

    def __init__(self):
        super().__init__("open_food")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "food_barcode": food_barcode.__skill__,
            "food_search": food_search.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="open_food",
            display_name="Open Food Facts",
            description="Look up food products and nutrition data by barcode or search via Open Food Facts.",
            icon="utensils",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
