"""Tests for the Translate plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.translate import (
    TranslatePlugin,
    ExtractTranslationTransformer,
    translate_text,
    translate_batch,
    translate_usage,
)
from tukuy.safety import SafetyPolicy


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── ExtractTranslationTransformer ──────────────────────────────────────────


class TestExtractTranslation:
    def test_extracts_text(self):
        t = ExtractTranslationTransformer("extract_translation")
        result = t.transform({"translated": "Hola mundo", "detected_source": "EN"})
        assert result.value == "Hola mundo"

    def test_empty_translation(self):
        t = ExtractTranslationTransformer("extract_translation")
        result = t.transform({"translated": ""})
        assert result.value == ""

    def test_invalid_input(self):
        t = ExtractTranslationTransformer("extract_translation")
        assert t.validate("not a dict") is False
        assert t.validate({"no_translated": True}) is False


# ── translate_text skill ───────────────────────────────────────────────────


class TestTranslateTextSkill:
    def test_descriptor(self):
        sk = translate_text.__skill__
        assert sk.descriptor.name == "translate_text"
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = translate_text.__skill__.invoke("hello", "ES", policy=policy)
        assert result.failed
        assert "network" in result.error.lower()


# ── translate_batch skill ─────────────────────────────────────────────────


class TestTranslateBatchSkill:
    def test_descriptor(self):
        sk = translate_batch.__skill__
        assert sk.descriptor.name == "translate_batch"
        assert sk.descriptor.is_async is True


# ── translate_usage skill ─────────────────────────────────────────────────


class TestTranslateUsageSkill:
    def test_descriptor(self):
        sk = translate_usage.__skill__
        assert sk.descriptor.name == "translate_usage"
        assert sk.descriptor.is_async is True


# ── Plugin registration ────────────────────────────────────────────────────


class TestTranslatePlugin:
    def test_plugin_name(self):
        plugin = TranslatePlugin()
        assert plugin.name == "translate"

    def test_has_transformer(self):
        plugin = TranslatePlugin()
        assert "extract_translation" in plugin.transformers

    def test_has_skills(self):
        plugin = TranslatePlugin()
        names = set(plugin.skills.keys())
        assert names == {"translate_text", "translate_batch", "translate_usage"}

    def test_manifest(self):
        plugin = TranslatePlugin()
        m = plugin.manifest
        assert m.name == "translate"
        assert m.group == "Integrations"


# ── Integration via TukuyTransformer ───────────────────────────────────────


class TestTranslateIntegration:
    def test_extract_translation(self, transformer):
        result = transformer.transform({"translated": "Bonjour"}, ["extract_translation"])
        assert result == "Bonjour"
