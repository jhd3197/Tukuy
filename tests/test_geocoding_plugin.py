"""Tests for the Geocoding plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.geocoding import (
    GeocodingPlugin,
    FormatCoordinatesTransformer,
    geocode,
    reverse_geocode,
    geocode_batch,
)
from tukuy.safety import SafetyPolicy


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── FormatCoordinatesTransformer ───────────────────────────────────────────


class TestFormatCoordinates:
    def test_basic(self):
        t = FormatCoordinatesTransformer("format_coordinates")
        result = t.transform({"lat": 37.422, "lng": -122.084})
        assert result.value == "37.422, -122.084"

    def test_zero(self):
        t = FormatCoordinatesTransformer("format_coordinates")
        result = t.transform({"lat": 0, "lng": 0})
        assert result.value == "0, 0"

    def test_invalid_input(self):
        t = FormatCoordinatesTransformer("format_coordinates")
        assert t.validate("not a dict") is False
        assert t.validate({"lat": 1}) is False
        assert t.validate({"lng": 1}) is False
        assert t.validate({"lat": 1, "lng": 2}) is True


# ── geocode skill ──────────────────────────────────────────────────────────


class TestGeocodeSkill:
    def test_descriptor(self):
        sk = geocode.__skill__
        assert sk.descriptor.name == "geocode"
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = geocode.__skill__.invoke("New York", policy=policy)
        assert result.failed
        assert "network" in result.error.lower()


# ── reverse_geocode skill ─────────────────────────────────────────────────


class TestReverseGeocodeSkill:
    def test_descriptor(self):
        sk = reverse_geocode.__skill__
        assert sk.descriptor.name == "reverse_geocode"
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = reverse_geocode.__skill__.invoke(40.71, -74.01, policy=policy)
        assert result.failed


# ── geocode_batch skill ───────────────────────────────────────────────────


class TestGeocodeBatchSkill:
    def test_descriptor(self):
        sk = geocode_batch.__skill__
        assert sk.descriptor.name == "geocode_batch"
        assert sk.descriptor.is_async is True


# ── Plugin registration ────────────────────────────────────────────────────


class TestGeocodingPlugin:
    def test_plugin_name(self):
        plugin = GeocodingPlugin()
        assert plugin.name == "geocoding"

    def test_has_transformer(self):
        plugin = GeocodingPlugin()
        assert "format_coordinates" in plugin.transformers

    def test_has_skills(self):
        plugin = GeocodingPlugin()
        names = set(plugin.skills.keys())
        assert names == {"geocode", "reverse_geocode", "geocode_batch"}

    def test_manifest(self):
        plugin = GeocodingPlugin()
        m = plugin.manifest
        assert m.name == "geocoding"
        assert m.group == "Integrations"


# ── Integration via TukuyTransformer ───────────────────────────────────────


class TestGeocodingIntegration:
    def test_format_coordinates(self, transformer):
        result = transformer.transform({"lat": 48.8566, "lng": 2.3522}, ["format_coordinates"])
        assert result == "48.8566, 2.3522"
