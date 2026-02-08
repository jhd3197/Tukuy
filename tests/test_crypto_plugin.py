"""Tests for the Crypto plugin."""

import hashlib
import hmac
import re

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.crypto import (
    CryptoPlugin,
    HashTextTransformer,
    Base64EncodeTransformer,
    Base64DecodeTransformer,
    UuidGenerateTransformer,
    HmacSignTransformer,
)


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── Transformer class tests ────────────────────────────────────────────────


class TestHashTextTransformer:
    def test_sha256_default(self):
        t = HashTextTransformer("hash_text")
        result = t.transform("hello")
        expected = hashlib.sha256(b"hello").hexdigest()
        assert result.value == expected

    def test_md5(self):
        t = HashTextTransformer("hash_text", algorithm="md5")
        result = t.transform("hello")
        expected = hashlib.md5(b"hello").hexdigest()
        assert result.value == expected

    def test_sha512(self):
        t = HashTextTransformer("hash_text", algorithm="sha512")
        result = t.transform("hello")
        expected = hashlib.sha512(b"hello").hexdigest()
        assert result.value == expected

    def test_validates_string(self):
        t = HashTextTransformer("hash_text")
        assert t.validate("hello") is True
        assert t.validate(123) is False


class TestBase64EncodeTransformer:
    def test_encode(self):
        t = Base64EncodeTransformer("base64_encode")
        result = t.transform("hello world")
        assert result.value == "aGVsbG8gd29ybGQ="

    def test_encode_empty(self):
        t = Base64EncodeTransformer("base64_encode")
        result = t.transform("")
        assert result.value == ""


class TestBase64DecodeTransformer:
    def test_decode(self):
        t = Base64DecodeTransformer("base64_decode")
        result = t.transform("aGVsbG8gd29ybGQ=")
        assert result.value == "hello world"


class TestUuidGenerateTransformer:
    def test_uuid4(self):
        t = UuidGenerateTransformer("uuid_generate")
        result = t.transform("")
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        assert re.match(uuid_pattern, result.value)

    def test_uuid_unique(self):
        t = UuidGenerateTransformer("uuid_generate")
        r1 = t.transform("")
        r2 = t.transform("")
        assert r1.value != r2.value

    def test_accepts_any_input(self):
        t = UuidGenerateTransformer("uuid_generate")
        assert t.validate(None) is True
        assert t.validate(42) is True


class TestHmacSignTransformer:
    def test_hmac_sha256(self):
        t = HmacSignTransformer("hmac_sign", key="secret", algorithm="sha256")
        result = t.transform("hello")
        expected = hmac.new(b"secret", b"hello", "sha256").hexdigest()
        assert result.value == expected

    def test_hmac_md5(self):
        t = HmacSignTransformer("hmac_sign", key="key", algorithm="md5")
        result = t.transform("data")
        expected = hmac.new(b"key", b"data", "md5").hexdigest()
        assert result.value == expected


# ── Plugin registration test ──────────────────────────────────────────────


class TestCryptoPlugin:
    def test_plugin_name(self):
        plugin = CryptoPlugin()
        assert plugin.name == "crypto"

    def test_has_all_transformers(self):
        plugin = CryptoPlugin()
        names = set(plugin.transformers.keys())
        assert names == {"hash_text", "base64_encode", "base64_decode", "uuid_generate", "hmac_sign"}


# ── Integration tests via TukuyTransformer ────────────────────────────────


class TestCryptoIntegration:
    def test_hash_text(self, transformer):
        result = transformer.transform("hello", ["hash_text"])
        assert result == hashlib.sha256(b"hello").hexdigest()

    def test_hash_text_with_algorithm(self, transformer):
        result = transformer.transform("hello", [{"function": "hash_text", "algorithm": "md5"}])
        assert result == hashlib.md5(b"hello").hexdigest()

    def test_base64_roundtrip(self, transformer):
        encoded = transformer.transform("hello world", ["base64_encode"])
        decoded = transformer.transform(encoded, ["base64_decode"])
        assert decoded == "hello world"

    def test_uuid_generate(self, transformer):
        result = transformer.transform("", ["uuid_generate"])
        assert len(result) == 36  # UUID format

    def test_hmac_sign(self, transformer):
        result = transformer.transform("msg", [{"function": "hmac_sign", "key": "k"}])
        expected = hmac.new(b"k", b"msg", "sha256").hexdigest()
        assert result == expected
