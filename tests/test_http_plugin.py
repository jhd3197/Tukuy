"""Tests for the HTTP plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.http import HttpPlugin, ParseResponseTransformer, http_request
from tukuy.skill import SkillResult
from tukuy.safety import SafetyPolicy


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── ParseResponseTransformer ─────────────────────────────────────────────


class TestParseResponse:
    def test_full_response(self):
        t = ParseResponseTransformer("parse_response")
        result = t.transform({
            "status_code": 200,
            "headers": {"content-type": "application/json"},
            "body": '{"ok": true}',
        })
        assert result.value["status_code"] == 200
        assert result.value["ok"] is True
        assert result.value["body"] == '{"ok": true}'

    def test_error_response(self):
        t = ParseResponseTransformer("parse_response")
        result = t.transform({"status_code": 404, "body": "Not Found"})
        assert result.value["ok"] is False

    def test_missing_fields(self):
        t = ParseResponseTransformer("parse_response")
        result = t.transform({})
        assert result.value["status_code"] is None
        assert result.value["ok"] is False

    def test_content_key_fallback(self):
        t = ParseResponseTransformer("parse_response")
        result = t.transform({"status_code": 200, "content": "data"})
        assert result.value["body"] == "data"


# ── http_request skill ───────────────────────────────────────────────────


class TestHttpRequestSkill:
    def test_descriptor(self):
        sk = http_request.__skill__
        assert sk.descriptor.name == "http_request"
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = http_request.__skill__.invoke("http://example.com", policy=policy)
        assert result.failed
        assert "network" in result.error.lower()


# ── Plugin registration ──────────────────────────────────────────────────


class TestHttpPlugin:
    def test_plugin_name(self):
        plugin = HttpPlugin()
        assert plugin.name == "http"

    def test_has_transformer(self):
        plugin = HttpPlugin()
        assert "parse_response" in plugin.transformers

    def test_has_skill(self):
        plugin = HttpPlugin()
        assert "http_request" in plugin.skills


# ── Integration via TukuyTransformer ─────────────────────────────────────


class TestHttpIntegration:
    def test_parse_response(self, transformer):
        resp = {"status_code": 200, "body": "ok"}
        result = transformer.transform(resp, ["parse_response"])
        assert result["ok"] is True
