"""Tests for the QR Code plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.qrcode import (
    QrCodePlugin,
    QrUrlTransformer,
    qr_generate,
    qr_read,
)
from tukuy.safety import SafetyPolicy


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── QrUrlTransformer ───────────────────────────────────────────────────────


class TestQrUrl:
    def test_generates_url(self):
        t = QrUrlTransformer("qr_url")
        result = t.transform("https://example.com")
        assert "api.qrserver.com" in result.value
        assert "example.com" in result.value

    def test_encodes_data(self):
        t = QrUrlTransformer("qr_url")
        result = t.transform("hello world")
        assert "hello" in result.value
        assert "300x300" in result.value

    def test_invalid_input(self):
        t = QrUrlTransformer("qr_url")
        assert t.validate("") is False
        assert t.validate(123) is False
        assert t.validate("valid") is True


# ── qr_generate skill ─────────────────────────────────────────────────────


class TestQrGenerateSkill:
    def test_descriptor(self):
        sk = qr_generate.__skill__
        assert sk.descriptor.name == "qr_generate"
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = qr_generate.__skill__.invoke("test", policy=policy)
        assert result.failed
        assert "network" in result.error.lower()


# ── qr_read skill ─────────────────────────────────────────────────────────


class TestQrReadSkill:
    def test_descriptor(self):
        sk = qr_read.__skill__
        assert sk.descriptor.name == "qr_read"
        assert sk.descriptor.is_async is True

    def test_blocked_by_policy(self):
        policy = SafetyPolicy(allow_network=False)
        result = qr_read.__skill__.invoke("http://example.com/qr.png", policy=policy)
        assert result.failed


# ── Plugin registration ────────────────────────────────────────────────────


class TestQrCodePlugin:
    def test_plugin_name(self):
        plugin = QrCodePlugin()
        assert plugin.name == "qrcode"

    def test_has_transformer(self):
        plugin = QrCodePlugin()
        assert "qr_url" in plugin.transformers

    def test_has_skills(self):
        plugin = QrCodePlugin()
        names = set(plugin.skills.keys())
        assert names == {"qr_generate", "qr_read"}

    def test_manifest(self):
        plugin = QrCodePlugin()
        m = plugin.manifest
        assert m.name == "qrcode"
        assert m.group == "Integrations"


# ── Integration via TukuyTransformer ───────────────────────────────────────


class TestQrCodeIntegration:
    def test_qr_url(self, transformer):
        result = transformer.transform("https://github.com", ["qr_url"])
        assert "api.qrserver.com" in result
        assert "github.com" in result
