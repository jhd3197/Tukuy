"""Tests for the Web plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.web import (
    WebPlugin,
    ExtractMetadataTransformer,
    web_fetch,
    web_search,
)
from tukuy.skill import SkillResult
from tukuy.safety import SafetyPolicy


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── ExtractMetadataTransformer ───────────────────────────────────────────


class TestExtractMetadata:
    def test_title(self):
        t = ExtractMetadataTransformer("extract_metadata")
        html = "<html><head><title>My Page</title></head></html>"
        result = t.transform(html)
        assert result.value["title"] == "My Page"

    def test_description(self):
        t = ExtractMetadataTransformer("extract_metadata")
        html = '<meta name="description" content="A description">'
        result = t.transform(html)
        assert result.value["description"] == "A description"

    def test_og_tags(self):
        t = ExtractMetadataTransformer("extract_metadata")
        html = '<meta property="og:title" content="OG Title"><meta property="og:image" content="img.png">'
        result = t.transform(html)
        assert result.value["og"]["title"] == "OG Title"
        assert result.value["og"]["image"] == "img.png"

    def test_canonical(self):
        t = ExtractMetadataTransformer("extract_metadata")
        html = '<link rel="canonical" href="https://example.com/page">'
        result = t.transform(html)
        assert result.value["canonical"] == "https://example.com/page"

    def test_empty_html(self):
        t = ExtractMetadataTransformer("extract_metadata")
        result = t.transform("")
        assert result.value == {}

    def test_full_page(self):
        t = ExtractMetadataTransformer("extract_metadata")
        html = """
        <html><head>
            <title>Test Page</title>
            <meta name="description" content="Page description">
            <meta property="og:title" content="OG Test">
            <link rel="canonical" href="https://example.com">
        </head><body></body></html>
        """
        result = t.transform(html)
        assert result.value["title"] == "Test Page"
        assert result.value["description"] == "Page description"
        assert result.value["og"]["title"] == "OG Test"
        assert result.value["canonical"] == "https://example.com"


# ── web_fetch skill ──────────────────────────────────────────────────────


class TestWebFetchSkill:
    def test_descriptor(self):
        sk = web_fetch.__skill__
        assert sk.descriptor.name == "web_fetch"
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = web_fetch.__skill__.invoke("http://example.com", policy=policy)
        assert result.failed
        assert "network" in result.error.lower()


# ── web_search skill ─────────────────────────────────────────────────────


class TestWebSearchSkill:
    def test_descriptor(self):
        sk = web_search.__skill__
        assert sk.descriptor.name == "web_search"
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = web_search.__skill__.invoke("test query", policy=policy)
        assert result.failed


# ── Plugin registration ──────────────────────────────────────────────────


class TestWebPlugin:
    def test_plugin_name(self):
        plugin = WebPlugin()
        assert plugin.name == "web"

    def test_has_transformer(self):
        plugin = WebPlugin()
        assert "extract_metadata" in plugin.transformers

    def test_has_skills(self):
        plugin = WebPlugin()
        names = set(plugin.skills.keys())
        assert names == {"web_fetch", "web_search"}


# ── Integration via TukuyTransformer ─────────────────────────────────────


class TestWebIntegration:
    def test_extract_metadata(self, transformer):
        html = "<html><head><title>Test</title></head></html>"
        result = transformer.transform(html, ["extract_metadata"])
        assert result["title"] == "Test"
