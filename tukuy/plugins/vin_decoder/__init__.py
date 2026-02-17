"""VIN decoder plugin.

Provides async skills for decoding Vehicle Identification Numbers using
the NHTSA vPIC API (free, no key required, unlimited).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles"


# -- Skills ------------------------------------------------------------------


@skill(
    name="vin_decode",
    display_name="Decode VIN",
    description="Decode a Vehicle Identification Number to get make, model, year, and specs (NHTSA, free, no key).",
    category="vin_decoder",
    tags=["vin", "vehicle", "car", "decode", "automotive"],
    icon="truck",
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
async def vin_decode(
    vin: str,
    model_year: int = 0,
    timeout: int = 15,
) -> dict:
    """Decode a VIN (Vehicle Identification Number).

    Args:
        vin: The 17-character VIN.
        model_year: Optional model year for better accuracy.
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    vin = vin.strip().upper()
    if not vin:
        return {"error": "VIN must not be empty.", "success": False}

    url = f"{_BASE_URL}/DecodeVin/{vin}"
    params = {"format": "json"}
    if model_year > 0:
        params["modelyear"] = model_year

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"NHTSA API returned status {resp.status_code}", "success": False}
        data = resp.json()

    results = data.get("Results", [])
    # Build a flat dict from the variable/value pairs
    decoded = {}
    errors = []
    for item in results:
        var_name = item.get("Variable", "")
        value = item.get("Value")
        error_code = item.get("ValueId", "")
        if value and str(value).strip():
            decoded[var_name] = value
        if item.get("ErrorCode") and item["ErrorCode"] not in ("0", 0):
            errors.append(item.get("ErrorText", ""))

    # Extract the most useful fields
    return {
        "vin": vin,
        "make": decoded.get("Make", ""),
        "model": decoded.get("Model", ""),
        "model_year": decoded.get("Model Year", ""),
        "body_class": decoded.get("Body Class", ""),
        "vehicle_type": decoded.get("Vehicle Type", ""),
        "drive_type": decoded.get("Drive Type", ""),
        "fuel_type": decoded.get("Fuel Type - Primary", ""),
        "engine_cylinders": decoded.get("Engine Number of Cylinders", ""),
        "engine_displacement_l": decoded.get("Displacement (L)", ""),
        "engine_hp": decoded.get("Engine Brake (hp) From", ""),
        "transmission": decoded.get("Transmission Style", ""),
        "doors": decoded.get("Doors", ""),
        "plant_country": decoded.get("Plant Country", ""),
        "plant_city": decoded.get("Plant City", ""),
        "manufacturer": decoded.get("Manufacturer Name", ""),
        "all_fields": decoded,
        "errors": [e for e in errors if e],
        "success": bool(decoded.get("Make")),
    }


class VinDecoderPlugin(TransformerPlugin):
    """Plugin providing VIN decoding skills."""

    def __init__(self):
        super().__init__("vin_decoder")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "vin_decode": vin_decode.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="vin_decoder",
            display_name="VIN Decoder",
            description="Decode Vehicle Identification Numbers via the NHTSA vPIC API.",
            icon="truck",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
