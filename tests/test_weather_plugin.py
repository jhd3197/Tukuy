"""Tests for the Weather plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.weather import (
    WeatherPlugin,
    WeatherSummaryTransformer,
    weather_current,
    weather_forecast,
    weather_historical,
)
from tukuy.safety import SafetyPolicy


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── WeatherSummaryTransformer ──────────────────────────────────────────────


class TestWeatherSummary:
    def test_full(self):
        t = WeatherSummaryTransformer("weather_summary")
        result = t.transform({
            "temperature": 22.5,
            "temperature_unit": "°C",
            "condition": "Partly cloudy",
            "humidity": 65,
        })
        assert result.value == "22.5°C, Partly cloudy, 65% humidity"

    def test_no_humidity(self):
        t = WeatherSummaryTransformer("weather_summary")
        result = t.transform({
            "temperature": 72,
            "temperature_unit": "°F",
            "condition": "Clear sky",
        })
        assert result.value == "72°F, Clear sky"

    def test_minimal(self):
        t = WeatherSummaryTransformer("weather_summary")
        result = t.transform({"temperature": 10})
        assert "10" in result.value

    def test_invalid_input(self):
        t = WeatherSummaryTransformer("weather_summary")
        assert t.validate("not a dict") is False
        assert t.validate({"no_temp": 1}) is False


# ── weather_current skill ─────────────────────────────────────────────────


class TestWeatherCurrentSkill:
    def test_descriptor(self):
        sk = weather_current.__skill__
        assert sk.descriptor.name == "weather_current"
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = weather_current.__skill__.invoke(40.71, -74.01, policy=policy)
        assert result.failed
        assert "network" in result.error.lower()


# ── weather_forecast skill ────────────────────────────────────────────────


class TestWeatherForecastSkill:
    def test_descriptor(self):
        sk = weather_forecast.__skill__
        assert sk.descriptor.name == "weather_forecast"
        assert sk.descriptor.is_async is True


# ── weather_historical skill ──────────────────────────────────────────────


class TestWeatherHistoricalSkill:
    def test_descriptor(self):
        sk = weather_historical.__skill__
        assert sk.descriptor.name == "weather_historical"
        assert sk.descriptor.is_async is True


# ── Plugin registration ────────────────────────────────────────────────────


class TestWeatherPlugin:
    def test_plugin_name(self):
        plugin = WeatherPlugin()
        assert plugin.name == "weather"

    def test_has_transformer(self):
        plugin = WeatherPlugin()
        assert "weather_summary" in plugin.transformers

    def test_has_skills(self):
        plugin = WeatherPlugin()
        names = set(plugin.skills.keys())
        assert names == {"weather_current", "weather_forecast", "weather_historical"}

    def test_manifest(self):
        plugin = WeatherPlugin()
        m = plugin.manifest
        assert m.name == "weather"
        assert m.group == "Integrations"


# ── Integration via TukuyTransformer ───────────────────────────────────────


class TestWeatherIntegration:
    def test_weather_summary(self, transformer):
        data = {"temperature": 25, "temperature_unit": "°C", "condition": "Clear sky"}
        result = transformer.transform(data, ["weather_summary"])
        assert result == "25°C, Clear sky"
