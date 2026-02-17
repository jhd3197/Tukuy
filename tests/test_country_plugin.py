"""Tests for the Country plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.country import (
    CountryPlugin,
    CountryFlagTransformer,
    country_info,
    country_search,
    country_all,
)
from tukuy.safety import SafetyPolicy


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── CountryFlagTransformer ─────────────────────────────────────────────────


class TestCountryFlag:
    def test_extracts_flag(self):
        t = CountryFlagTransformer("country_flag")
        result = t.transform({"flag_emoji": "\U0001f1eb\U0001f1f7", "name": "France"})
        assert result.value == "\U0001f1eb\U0001f1f7"

    def test_empty_flag(self):
        t = CountryFlagTransformer("country_flag")
        result = t.transform({"flag_emoji": ""})
        assert result.value == ""

    def test_invalid_input(self):
        t = CountryFlagTransformer("country_flag")
        assert t.validate("not a dict") is False
        assert t.validate({"no_flag": True}) is False


# ── country_info skill ─────────────────────────────────────────────────────


class TestCountryInfoSkill:
    def test_descriptor(self):
        sk = country_info.__skill__
        assert sk.descriptor.name == "country_info"
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = country_info.__skill__.invoke("France", policy=policy)
        assert result.failed
        assert "network" in result.error.lower()


# ── country_search skill ──────────────────────────────────────────────────


class TestCountrySearchSkill:
    def test_descriptor(self):
        sk = country_search.__skill__
        assert sk.descriptor.name == "country_search"
        assert sk.descriptor.is_async is True


# ── country_all skill ─────────────────────────────────────────────────────


class TestCountryAllSkill:
    def test_descriptor(self):
        sk = country_all.__skill__
        assert sk.descriptor.name == "country_all"
        assert sk.descriptor.is_async is True


# ── Plugin registration ────────────────────────────────────────────────────


class TestCountryPlugin:
    def test_plugin_name(self):
        plugin = CountryPlugin()
        assert plugin.name == "country"

    def test_has_transformer(self):
        plugin = CountryPlugin()
        assert "country_flag" in plugin.transformers

    def test_has_skills(self):
        plugin = CountryPlugin()
        names = set(plugin.skills.keys())
        assert names == {"country_info", "country_search", "country_all"}

    def test_manifest(self):
        plugin = CountryPlugin()
        m = plugin.manifest
        assert m.name == "country"
        assert m.group == "Integrations"


# ── Integration via TukuyTransformer ───────────────────────────────────────


class TestCountryIntegration:
    def test_country_flag(self, transformer):
        result = transformer.transform({"flag_emoji": "\U0001f1fa\U0001f1f8"}, ["country_flag"])
        assert result == "\U0001f1fa\U0001f1f8"
