"""Name prediction plugin.

Provides async skills for predicting age, gender, and nationality from
first names using Agify, Genderize, and Nationalize APIs (free, no key, 1000/day each).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel


# -- Skills ------------------------------------------------------------------


@skill(
    name="predict_age",
    display_name="Predict Age",
    description="Predict the age of a person from their first name (Agify API, free, no key, 1000/day).",
    category="name_predict",
    tags=["name", "age", "prediction", "demographics"],
    icon="user",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def predict_age(name: str, country_id: str = "") -> dict:
    """Predict the likely age of a person given their first name.

    Args:
        name: First name to analyze.
        country_id: Optional ISO 3166-1 alpha-2 country code for localization.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    name = name.strip()
    if not name:
        return {"error": "Name must not be empty.", "success": False}

    url = "https://api.agify.io"
    params = {"name": name}
    if country_id.strip():
        params["country_id"] = country_id.strip().upper()

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Agify API returned status {resp.status_code}", "success": False}
        data = resp.json()

    return {
        "name": data.get("name", name),
        "age": data.get("age"),
        "count": data.get("count", 0),
        "country_id": data.get("country_id", country_id or None),
        "success": data.get("age") is not None,
    }


@skill(
    name="predict_gender",
    display_name="Predict Gender",
    description="Predict the gender of a person from their first name (Genderize API, free, no key, 1000/day).",
    category="name_predict",
    tags=["name", "gender", "prediction", "demographics"],
    icon="user",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def predict_gender(name: str, country_id: str = "") -> dict:
    """Predict the likely gender of a person given their first name.

    Args:
        name: First name to analyze.
        country_id: Optional ISO country code for localization.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    name = name.strip()
    if not name:
        return {"error": "Name must not be empty.", "success": False}

    url = "https://api.genderize.io"
    params = {"name": name}
    if country_id.strip():
        params["country_id"] = country_id.strip().upper()

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Genderize API returned status {resp.status_code}", "success": False}
        data = resp.json()

    return {
        "name": data.get("name", name),
        "gender": data.get("gender"),
        "probability": data.get("probability"),
        "count": data.get("count", 0),
        "country_id": data.get("country_id", country_id or None),
        "success": data.get("gender") is not None,
    }


@skill(
    name="predict_nationality",
    display_name="Predict Nationality",
    description="Predict the nationality of a person from their first name (Nationalize API, free, no key, 1000/day).",
    category="name_predict",
    tags=["name", "nationality", "prediction", "demographics"],
    icon="globe",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def predict_nationality(name: str) -> dict:
    """Predict the likely nationality of a person given their first name.

    Args:
        name: First name to analyze.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    name = name.strip()
    if not name:
        return {"error": "Name must not be empty.", "success": False}

    url = "https://api.nationalize.io"
    params = {"name": name}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Nationalize API returned status {resp.status_code}", "success": False}
        data = resp.json()

    countries = []
    for c in data.get("country", []):
        countries.append({
            "country_id": c.get("country_id", ""),
            "probability": c.get("probability", 0),
        })

    return {
        "name": data.get("name", name),
        "count": data.get("count", 0),
        "countries": countries,
        "top_country": countries[0]["country_id"] if countries else None,
        "top_probability": countries[0]["probability"] if countries else None,
        "success": bool(countries),
    }


@skill(
    name="name_analysis",
    display_name="Full Name Analysis",
    description="Get age, gender, and nationality predictions for a name (all three APIs, free, no key).",
    category="name_predict",
    tags=["name", "analysis", "demographics"],
    icon="user",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def name_analysis(name: str, country_id: str = "") -> dict:
    """Run all three name predictions (age, gender, nationality) at once.

    Args:
        name: First name to analyze.
        country_id: Optional ISO country code for age/gender localization.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    name = name.strip()
    if not name:
        return {"error": "Name must not be empty.", "success": False}

    age_result = await predict_age(name, country_id)
    gender_result = await predict_gender(name, country_id)
    nationality_result = await predict_nationality(name)

    return {
        "name": name,
        "age": age_result.get("age"),
        "gender": gender_result.get("gender"),
        "gender_probability": gender_result.get("probability"),
        "nationalities": nationality_result.get("countries", []),
        "top_nationality": nationality_result.get("top_country"),
        "success": True,
    }


class NamePredictPlugin(TransformerPlugin):
    """Plugin providing name-based prediction skills."""

    def __init__(self):
        super().__init__("name_predict")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "predict_age": predict_age.__skill__,
            "predict_gender": predict_gender.__skill__,
            "predict_nationality": predict_nationality.__skill__,
            "name_analysis": name_analysis.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="name_predict",
            display_name="Name Predict",
            description="Predict age, gender, and nationality from first names via Agify, Genderize, and Nationalize.",
            icon="user",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
