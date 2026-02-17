"""Tests for the Currency plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.currency import (
    CurrencyPlugin,
    FormatCurrencyTransformer,
    currency_convert,
    currency_rates,
    currency_history,
)
from tukuy.safety import SafetyPolicy


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── FormatCurrencyTransformer ──────────────────────────────────────────────


class TestFormatCurrency:
    def test_basic(self):
        t = FormatCurrencyTransformer("format_currency")
        result = t.transform({"amount": 1234.5, "currency": "USD"})
        assert result.value == "1,234.50 USD"

    def test_zero(self):
        t = FormatCurrencyTransformer("format_currency")
        result = t.transform({"amount": 0, "currency": "EUR"})
        assert result.value == "0.00 EUR"

    def test_no_currency(self):
        t = FormatCurrencyTransformer("format_currency")
        result = t.transform({"amount": 42.0})
        assert result.value == "42.00"

    def test_invalid_input(self):
        t = FormatCurrencyTransformer("format_currency")
        assert t.validate("not a dict") is False
        assert t.validate({"no_amount": 1}) is False


# ── currency_convert skill ─────────────────────────────────────────────────


class TestCurrencyConvertSkill:
    def test_descriptor(self):
        sk = currency_convert.__skill__
        assert sk.descriptor.name == "currency_convert"
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = currency_convert.__skill__.invoke(100, "USD", "EUR", policy=policy)
        assert result.failed
        assert "network" in result.error.lower()


# ── currency_rates skill ───────────────────────────────────────────────────


class TestCurrencyRatesSkill:
    def test_descriptor(self):
        sk = currency_rates.__skill__
        assert sk.descriptor.name == "currency_rates"
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = currency_rates.__skill__.invoke("USD", policy=policy)
        assert result.failed


# ── currency_history skill ─────────────────────────────────────────────────


class TestCurrencyHistorySkill:
    def test_descriptor(self):
        sk = currency_history.__skill__
        assert sk.descriptor.name == "currency_history"
        assert sk.descriptor.is_async is True


# ── Plugin registration ────────────────────────────────────────────────────


class TestCurrencyPlugin:
    def test_plugin_name(self):
        plugin = CurrencyPlugin()
        assert plugin.name == "currency"

    def test_has_transformer(self):
        plugin = CurrencyPlugin()
        assert "format_currency" in plugin.transformers

    def test_has_skills(self):
        plugin = CurrencyPlugin()
        names = set(plugin.skills.keys())
        assert names == {"currency_convert", "currency_rates", "currency_history"}

    def test_manifest(self):
        plugin = CurrencyPlugin()
        m = plugin.manifest
        assert m.name == "currency"
        assert m.group == "Integrations"
        assert m.requires.network is True


# ── Integration via TukuyTransformer ───────────────────────────────────────


class TestCurrencyIntegration:
    def test_format_currency(self, transformer):
        result = transformer.transform({"amount": 99.99, "currency": "GBP"}, ["format_currency"])
        assert result == "99.99 GBP"
