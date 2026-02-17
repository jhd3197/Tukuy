"""Weather plugin.

Provides async ``weather_current``, ``weather_forecast``, and
``weather_historical`` skills using the Open-Meteo API (free, no key).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.open-meteo.com/v1"

# WMO weather interpretation codes
_WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherSummaryTransformer(ChainableTransformer[dict, str]):
    """Summarise a current-weather dict into a human-readable string."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "temperature" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        temp = value.get("temperature", "?")
        unit = value.get("temperature_unit", "°C")
        condition = value.get("condition", "")
        humidity = value.get("humidity")
        parts = [f"{temp}{unit}", condition]
        if humidity is not None:
            parts.append(f"{humidity}% humidity")
        return ", ".join(p for p in parts if p)


# ── Skills ─────────────────────────────────────────────────────────────────


@skill(
    name="weather_current",
    display_name="Current Weather",
    description="Get current weather for a location by coordinates (Open-Meteo, no key required).",
    category="weather",
    tags=["weather", "temperature", "forecast"],
    icon="cloud-sun",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="temperature_unit",
            display_name="Temperature Unit",
            description="Unit for temperature values.",
            type="select",
            default="celsius",
            options=["celsius", "fahrenheit"],
        ),
        ConfigParam(
            name="wind_speed_unit",
            display_name="Wind Speed Unit",
            description="Unit for wind speed values.",
            type="select",
            default="kmh",
            options=["kmh", "mph", "kn", "ms"],
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
async def weather_current(
    latitude: float,
    longitude: float,
    temperature_unit: str = "celsius",
    wind_speed_unit: str = "kmh",
) -> dict:
    """Fetch current weather for the given coordinates."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    endpoint = f"{_BASE_URL}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,precipitation",
        "temperature_unit": temperature_unit,
        "wind_speed_unit": wind_speed_unit,
    }

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        current = data.get("current", {})
        code = current.get("weather_code", -1)
        unit_symbol = "°F" if temperature_unit == "fahrenheit" else "°C"
        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "temperature": current.get("temperature_2m"),
            "temperature_unit": unit_symbol,
            "apparent_temperature": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "weather_code": code,
            "condition": _WMO_CODES.get(code, "Unknown"),
            "time": current.get("time"),
            "timezone": data.get("timezone"),
            "success": True,
        }


@skill(
    name="weather_forecast",
    display_name="Weather Forecast",
    description="Get a multi-day weather forecast by coordinates (Open-Meteo, no key required).",
    category="weather",
    tags=["weather", "forecast"],
    icon="cloud",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def weather_forecast(
    latitude: float,
    longitude: float,
    days: int = 7,
    temperature_unit: str = "celsius",
) -> dict:
    """Fetch a daily weather forecast for the given coordinates."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    days = max(1, min(days, 16))
    endpoint = f"{_BASE_URL}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,wind_speed_10m_max",
        "temperature_unit": temperature_unit,
        "forecast_days": days,
    }

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        forecast = []
        for i, date in enumerate(dates):
            code = (daily.get("weather_code") or [])[i] if i < len(daily.get("weather_code") or []) else None
            forecast.append({
                "date": date,
                "temp_max": (daily.get("temperature_2m_max") or [])[i] if i < len(daily.get("temperature_2m_max") or []) else None,
                "temp_min": (daily.get("temperature_2m_min") or [])[i] if i < len(daily.get("temperature_2m_min") or []) else None,
                "precipitation": (daily.get("precipitation_sum") or [])[i] if i < len(daily.get("precipitation_sum") or []) else None,
                "wind_speed_max": (daily.get("wind_speed_10m_max") or [])[i] if i < len(daily.get("wind_speed_10m_max") or []) else None,
                "weather_code": code,
                "condition": _WMO_CODES.get(code, "Unknown") if code is not None else "Unknown",
            })
        unit_symbol = "°F" if temperature_unit == "fahrenheit" else "°C"
        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "temperature_unit": unit_symbol,
            "timezone": data.get("timezone"),
            "forecast": forecast,
            "days": len(forecast),
            "success": True,
        }


@skill(
    name="weather_historical",
    display_name="Historical Weather",
    description="Get past weather data for a location and date range (Open-Meteo, no key required).",
    category="weather",
    tags=["weather", "history"],
    icon="history",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def weather_historical(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    temperature_unit: str = "celsius",
) -> dict:
    """Fetch historical daily weather for the given coordinates and date range."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    endpoint = f"{_BASE_URL}/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum",
        "temperature_unit": temperature_unit,
    }

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        history = []
        for i, date in enumerate(dates):
            code = (daily.get("weather_code") or [])[i] if i < len(daily.get("weather_code") or []) else None
            history.append({
                "date": date,
                "temp_max": (daily.get("temperature_2m_max") or [])[i] if i < len(daily.get("temperature_2m_max") or []) else None,
                "temp_min": (daily.get("temperature_2m_min") or [])[i] if i < len(daily.get("temperature_2m_min") or []) else None,
                "precipitation": (daily.get("precipitation_sum") or [])[i] if i < len(daily.get("precipitation_sum") or []) else None,
                "weather_code": code,
                "condition": _WMO_CODES.get(code, "Unknown") if code is not None else "Unknown",
            })
        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "start_date": start_date,
            "end_date": end_date,
            "history": history,
            "data_points": len(history),
            "success": True,
        }


class WeatherPlugin(TransformerPlugin):
    """Plugin providing weather skills and summary transformer."""

    def __init__(self):
        super().__init__("weather")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "weather_summary": lambda _: WeatherSummaryTransformer("weather_summary"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "weather_current": weather_current.__skill__,
            "weather_forecast": weather_forecast.__skill__,
            "weather_historical": weather_historical.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="weather",
            display_name="Weather",
            description="Current weather, forecasts, and historical data via Open-Meteo API.",
            icon="cloud-sun",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
