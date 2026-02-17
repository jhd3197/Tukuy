"""Open-Meteo weather plugin.

Provides async skills for weather forecasts and current conditions using
the Open-Meteo API (free, no key required, unlimited for non-commercial).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.open-meteo.com/v1"

_WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Freezing light drizzle", 57: "Freezing dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Freezing light rain", 67: "Freezing heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _describe_weather_code(code: Optional[int]) -> str:
    """Convert a WMO weather code to a human-readable description."""
    if code is None:
        return "Unknown"
    return _WMO_CODES.get(code, f"Code {code}")


# -- Skills ------------------------------------------------------------------


@skill(
    name="weather_current",
    display_name="Current Weather",
    description="Get current weather conditions for a location (Open-Meteo, free, no key required).",
    category="open_meteo",
    tags=["weather", "current", "temperature", "forecast"],
    icon="cloud",
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
async def weather_current(
    latitude: float,
    longitude: float,
    temperature_unit: str = "celsius",
    timeout: int = 15,
) -> dict:
    """Get current weather conditions for a latitude/longitude.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
        temperature_unit: ``"celsius"`` or ``"fahrenheit"`` (default celsius).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"{_BASE_URL}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure",
        "temperature_unit": temperature_unit,
        "wind_speed_unit": "kmh",
    }

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Open-Meteo returned status {resp.status_code}", "success": False}
        data = resp.json()

    current = data.get("current", {})
    temp_unit = "F" if temperature_unit == "fahrenheit" else "C"

    return {
        "latitude": data.get("latitude", latitude),
        "longitude": data.get("longitude", longitude),
        "timezone": data.get("timezone", ""),
        "temperature": current.get("temperature_2m"),
        "temperature_unit": temp_unit,
        "apparent_temperature": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation_mm": current.get("precipitation"),
        "weather_code": current.get("weather_code"),
        "weather_description": _describe_weather_code(current.get("weather_code")),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_direction": current.get("wind_direction_10m"),
        "pressure_hpa": current.get("surface_pressure"),
        "time": current.get("time", ""),
        "success": True,
    }


@skill(
    name="weather_forecast",
    display_name="Weather Forecast",
    description="Get a multi-day weather forecast for a location (Open-Meteo, free, no key required).",
    category="open_meteo",
    tags=["weather", "forecast", "daily", "weekly"],
    icon="cloud-sun",
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
    """Get a daily weather forecast.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
        days: Number of forecast days (1-16, default 7).
        temperature_unit: ``"celsius"`` or ``"fahrenheit"``.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    days = max(1, min(days, 16))
    url = f"{_BASE_URL}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,sunrise,sunset",
        "temperature_unit": temperature_unit,
        "wind_speed_unit": "kmh",
        "forecast_days": days,
    }

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Open-Meteo returned status {resp.status_code}", "success": False}
        data = resp.json()

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    temp_unit = "F" if temperature_unit == "fahrenheit" else "C"

    forecast = []
    for i, date in enumerate(dates):
        forecast.append({
            "date": date,
            "weather": _describe_weather_code(daily.get("weather_code", [None])[i] if i < len(daily.get("weather_code", [])) else None),
            "temp_max": daily.get("temperature_2m_max", [None])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
            "temp_min": daily.get("temperature_2m_min", [None])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
            "precipitation_mm": daily.get("precipitation_sum", [None])[i] if i < len(daily.get("precipitation_sum", [])) else None,
            "wind_max_kmh": daily.get("wind_speed_10m_max", [None])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,
            "sunrise": daily.get("sunrise", [None])[i] if i < len(daily.get("sunrise", [])) else None,
            "sunset": daily.get("sunset", [None])[i] if i < len(daily.get("sunset", [])) else None,
        })

    return {
        "latitude": data.get("latitude", latitude),
        "longitude": data.get("longitude", longitude),
        "timezone": data.get("timezone", ""),
        "temperature_unit": temp_unit,
        "forecast": forecast,
        "days": len(forecast),
        "success": True,
    }


@skill(
    name="weather_hourly",
    display_name="Hourly Weather",
    description="Get hourly weather forecast for a location (Open-Meteo, free, no key required).",
    category="open_meteo",
    tags=["weather", "hourly", "forecast"],
    icon="clock",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def weather_hourly(
    latitude: float,
    longitude: float,
    hours: int = 24,
    temperature_unit: str = "celsius",
) -> dict:
    """Get hourly weather forecast.

    Args:
        latitude: Latitude.
        longitude: Longitude.
        hours: Number of hours to forecast (default 24, max 384).
        temperature_unit: ``"celsius"`` or ``"fahrenheit"``.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"{_BASE_URL}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m",
        "temperature_unit": temperature_unit,
        "wind_speed_unit": "kmh",
        "forecast_hours": min(hours, 384),
    }

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Open-Meteo returned status {resp.status_code}", "success": False}
        data = resp.json()

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temp_unit = "F" if temperature_unit == "fahrenheit" else "C"

    forecast = []
    for i, t in enumerate(times[:hours]):
        forecast.append({
            "time": t,
            "temperature": hourly.get("temperature_2m", [None])[i] if i < len(hourly.get("temperature_2m", [])) else None,
            "humidity": hourly.get("relative_humidity_2m", [None])[i] if i < len(hourly.get("relative_humidity_2m", [])) else None,
            "precipitation_probability": hourly.get("precipitation_probability", [None])[i] if i < len(hourly.get("precipitation_probability", [])) else None,
            "weather": _describe_weather_code(hourly.get("weather_code", [None])[i] if i < len(hourly.get("weather_code", [])) else None),
            "wind_speed_kmh": hourly.get("wind_speed_10m", [None])[i] if i < len(hourly.get("wind_speed_10m", [])) else None,
        })

    return {
        "latitude": data.get("latitude", latitude),
        "longitude": data.get("longitude", longitude),
        "timezone": data.get("timezone", ""),
        "temperature_unit": temp_unit,
        "forecast": forecast,
        "hours": len(forecast),
        "success": True,
    }


class OpenMeteoPlugin(TransformerPlugin):
    """Plugin providing weather skills via Open-Meteo (no key needed)."""

    def __init__(self):
        super().__init__("open_meteo")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "weather_current": weather_current.__skill__,
            "weather_forecast": weather_forecast.__skill__,
            "weather_hourly": weather_hourly.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="open_meteo",
            display_name="Open-Meteo Weather",
            description="Weather forecasts, current conditions, and hourly data via Open-Meteo (free, no key).",
            icon="cloud",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
