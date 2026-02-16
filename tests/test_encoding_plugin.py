"""Tests for the Encoding plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.encoding import (
    EncodingPlugin,
    UrlEncodeTransformer,
    UrlDecodeTransformer,
    HexEncodeTransformer,
    HexDecodeTransformer,
    HtmlEntitiesEncodeTransformer,
    HtmlEntitiesDecodeTransformer,
    Rot13Transformer,
    UnicodeEscapeTransformer,
    UnicodeUnescapeTransformer,
)


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── Transformer class tests ────────────────────────────────────────────────


class TestUrlEncodeTransformer:
    def test_basic_encode(self):
        t = UrlEncodeTransformer("url_encode")
        result = t.transform("hello world")
        assert result.value == "hello%20world"

    def test_encode_special_chars(self):
        t = UrlEncodeTransformer("url_encode")
        result = t.transform("hello&world?foo=bar")
        assert result.value == "hello%26world%3Ffoo%3Dbar"

    def test_encode_with_safe_default(self):
        t = UrlEncodeTransformer("url_encode", safe="")
        result = t.transform("https://example.com/path")
        assert "%" in result.value
        assert "/" not in result.value or result.value.count("/") < 2

    def test_encode_with_safe_slash(self):
        t = UrlEncodeTransformer("url_encode", safe="/")
        result = t.transform("https://example.com/path")
        # Slashes should be preserved
        assert "/" in result.value

    def test_encode_empty_string(self):
        t = UrlEncodeTransformer("url_encode")
        result = t.transform("")
        assert result.value == ""

    def test_encode_unicode(self):
        t = UrlEncodeTransformer("url_encode")
        result = t.transform("hello café")
        assert "caf%C3%A9" in result.value


class TestUrlDecodeTransformer:
    def test_basic_decode(self):
        t = UrlDecodeTransformer("url_decode")
        result = t.transform("hello%20world")
        assert result.value == "hello world"

    def test_decode_special_chars(self):
        t = UrlDecodeTransformer("url_decode")
        result = t.transform("hello%26world%3Ffoo%3Dbar")
        assert result.value == "hello&world?foo=bar"

    def test_decode_empty_string(self):
        t = UrlDecodeTransformer("url_decode")
        result = t.transform("")
        assert result.value == ""

    def test_decode_unicode(self):
        t = UrlDecodeTransformer("url_decode")
        result = t.transform("hello%20caf%C3%A9")
        assert result.value == "hello café"


class TestHexEncodeTransformer:
    def test_basic_encode(self):
        t = HexEncodeTransformer("hex_encode")
        result = t.transform("hello")
        assert result.value == "68656c6c6f"

    def test_encode_empty_string(self):
        t = HexEncodeTransformer("hex_encode")
        result = t.transform("")
        assert result.value == ""

    def test_encode_unicode(self):
        t = HexEncodeTransformer("hex_encode")
        result = t.transform("café")
        # UTF-8 encoding of "café" is "636166c3a9"
        assert result.value == "636166c3a9"

    def test_encode_emoji(self):
        t = HexEncodeTransformer("hex_encode")
        result = t.transform("😀")
        # UTF-8 encoding of 😀 is f09f9880
        assert result.value == "f09f9880"


class TestHexDecodeTransformer:
    def test_basic_decode(self):
        t = HexDecodeTransformer("hex_decode")
        result = t.transform("68656c6c6f")
        assert result.value == "hello"

    def test_decode_empty_string(self):
        t = HexDecodeTransformer("hex_decode")
        result = t.transform("")
        assert result.value == ""

    def test_decode_unicode(self):
        t = HexDecodeTransformer("hex_decode")
        result = t.transform("636166c3a9")
        assert result.value == "café"

    def test_decode_emoji(self):
        t = HexDecodeTransformer("hex_decode")
        result = t.transform("f09f9880")
        assert result.value == "😀"


class TestHtmlEntitiesEncodeTransformer:
    def test_basic_encode(self):
        t = HtmlEntitiesEncodeTransformer("html_entities_encode")
        result = t.transform("<b>test</b>")
        assert result.value == "&lt;b&gt;test&lt;/b&gt;"

    def test_encode_ampersand(self):
        t = HtmlEntitiesEncodeTransformer("html_entities_encode")
        result = t.transform("hello & world")
        assert result.value == "hello &amp; world"

    def test_encode_quotes(self):
        t = HtmlEntitiesEncodeTransformer("html_entities_encode")
        result = t.transform('"hello" \'world\'')
        assert "&quot;" in result.value
        # Note: html.escape converts ' to &#x27; by default
        assert "&#x27;" in result.value or "'" in result.value

    def test_encode_empty_string(self):
        t = HtmlEntitiesEncodeTransformer("html_entities_encode")
        result = t.transform("")
        assert result.value == ""

    def test_encode_mixed_content(self):
        t = HtmlEntitiesEncodeTransformer("html_entities_encode")
        result = t.transform("<a href=\"test\">link & text</a>")
        assert "&lt;a" in result.value
        assert "&amp;" in result.value
        assert "&quot;" in result.value


class TestHtmlEntitiesDecodeTransformer:
    def test_basic_decode(self):
        t = HtmlEntitiesDecodeTransformer("html_entities_decode")
        result = t.transform("&lt;b&gt;test&lt;/b&gt;")
        assert result.value == "<b>test</b>"

    def test_decode_ampersand(self):
        t = HtmlEntitiesDecodeTransformer("html_entities_decode")
        result = t.transform("hello &amp; world")
        assert result.value == "hello & world"

    def test_decode_quotes(self):
        t = HtmlEntitiesDecodeTransformer("html_entities_decode")
        result = t.transform("&quot;hello&quot; &#x27;world&#x27;")
        assert result.value == '"hello" \'world\''

    def test_decode_empty_string(self):
        t = HtmlEntitiesDecodeTransformer("html_entities_decode")
        result = t.transform("")
        assert result.value == ""

    def test_decode_numeric_entities(self):
        t = HtmlEntitiesDecodeTransformer("html_entities_decode")
        result = t.transform("&#60;&#62;")
        assert result.value == "<>"


class TestRot13Transformer:
    def test_basic_rot13(self):
        t = Rot13Transformer("rot13")
        result = t.transform("hello")
        assert result.value == "uryyb"

    def test_rot13_mixed_case(self):
        t = Rot13Transformer("rot13")
        result = t.transform("Hello World")
        assert result.value == "Uryyb Jbeyq"

    def test_rot13_preserves_non_alpha(self):
        t = Rot13Transformer("rot13")
        result = t.transform("hello, world! 123")
        assert result.value == "uryyb, jbeyq! 123"

    def test_rot13_empty_string(self):
        t = Rot13Transformer("rot13")
        result = t.transform("")
        assert result.value == ""

    def test_rot13_is_self_inverse(self):
        t = Rot13Transformer("rot13")
        r1 = t.transform("hello world")
        r2 = t.transform(r1.value)
        assert r2.value == "hello world"


class TestUnicodeEscapeTransformer:
    def test_basic_ascii_unchanged(self):
        t = UnicodeEscapeTransformer("unicode_escape")
        result = t.transform("hello")
        assert result.value == "hello"

    def test_escape_non_ascii(self):
        t = UnicodeEscapeTransformer("unicode_escape")
        result = t.transform("café")
        assert "\\u" in result.value or "\\xe9" in result.value

    def test_escape_emoji(self):
        t = UnicodeEscapeTransformer("unicode_escape")
        result = t.transform("😀")
        # Emoji should be escaped to a sequence
        assert "\\" in result.value

    def test_escape_empty_string(self):
        t = UnicodeEscapeTransformer("unicode_escape")
        result = t.transform("")
        assert result.value == ""

    def test_escape_special_unicode(self):
        t = UnicodeEscapeTransformer("unicode_escape")
        result = t.transform("日本語")
        # Japanese characters should be escaped
        assert "\\" in result.value


class TestUnicodeUnescapeTransformer:
    def test_basic_ascii_unchanged(self):
        t = UnicodeUnescapeTransformer("unicode_unescape")
        result = t.transform("hello")
        assert result.value == "hello"

    def test_unescape_basic(self):
        t = UnicodeUnescapeTransformer("unicode_unescape")
        result = t.transform("\\u00e9")
        assert result.value == "é"

    def test_unescape_mixed_content(self):
        t = UnicodeUnescapeTransformer("unicode_unescape")
        result = t.transform("caf\\u00e9")
        assert result.value == "café"

    def test_unescape_empty_string(self):
        t = UnicodeUnescapeTransformer("unicode_unescape")
        result = t.transform("")
        assert result.value == ""


# ── Plugin registration test ──────────────────────────────────────────────


class TestEncodingPlugin:
    def test_plugin_name(self):
        plugin = EncodingPlugin()
        assert plugin.name == "encoding"

    def test_has_all_transformers(self):
        plugin = EncodingPlugin()
        names = set(plugin.transformers.keys())
        assert names == {
            "url_encode",
            "url_decode",
            "hex_encode",
            "hex_decode",
            "html_entities_encode",
            "html_entities_decode",
            "rot13",
            "unicode_escape",
            "unicode_unescape",
        }


# ── Integration tests via TukuyTransformer ────────────────────────────────


class TestEncodingIntegration:
    """Integration tests using TukuyTransformer public API."""

    # ── Basic functionality tests ──────────────────────────────────────────

    def test_url_encode_basic(self, transformer):
        result = transformer.transform("hello world", ["url_encode"])
        assert result == "hello%20world"

    def test_url_decode_basic(self, transformer):
        result = transformer.transform("hello%20world", ["url_decode"])
        assert result == "hello world"

    def test_hex_encode_basic(self, transformer):
        result = transformer.transform("hello", ["hex_encode"])
        assert result == "68656c6c6f"

    def test_hex_decode_basic(self, transformer):
        result = transformer.transform("68656c6c6f", ["hex_decode"])
        assert result == "hello"

    def test_html_entities_encode_basic(self, transformer):
        result = transformer.transform("<b>test</b>", ["html_entities_encode"])
        assert result == "&lt;b&gt;test&lt;/b&gt;"

    def test_html_entities_decode_basic(self, transformer):
        result = transformer.transform("&lt;b&gt;test&lt;/b&gt;", ["html_entities_decode"])
        assert result == "<b>test</b>"

    def test_rot13_basic(self, transformer):
        result = transformer.transform("hello", ["rot13"])
        assert result == "uryyb"

    def test_unicode_escape_basic(self, transformer):
        result = transformer.transform("café", ["unicode_escape"])
        assert "\\" in result

    def test_unicode_unescape_basic(self, transformer):
        result = transformer.transform("caf\\u00e9", ["unicode_unescape"])
        assert result == "café"

    # ── Round-trip tests ───────────────────────────────────────────────────

    def test_url_roundtrip(self, transformer):
        original = "hello world & special?chars=yes"
        encoded = transformer.transform(original, ["url_encode"])
        decoded = transformer.transform(encoded, ["url_decode"])
        assert decoded == original

    def test_hex_roundtrip(self, transformer):
        original = "hello world 123"
        encoded = transformer.transform(original, ["hex_encode"])
        decoded = transformer.transform(encoded, ["hex_decode"])
        assert decoded == original

    def test_hex_roundtrip_unicode(self, transformer):
        original = "café 😀"
        encoded = transformer.transform(original, ["hex_encode"])
        decoded = transformer.transform(encoded, ["hex_decode"])
        assert decoded == original

    def test_html_entities_roundtrip(self, transformer):
        original = '<a href="test">link & text</a>'
        encoded = transformer.transform(original, ["html_entities_encode"])
        decoded = transformer.transform(encoded, ["html_entities_decode"])
        assert decoded == original

    def test_unicode_roundtrip(self, transformer):
        original = "café"
        escaped = transformer.transform(original, ["unicode_escape"])
        unescaped = transformer.transform(escaped, ["unicode_unescape"])
        assert unescaped == original

    def test_rot13_double_application(self, transformer):
        original = "hello world"
        r1 = transformer.transform(original, ["rot13"])
        r2 = transformer.transform(r1, ["rot13"])
        assert r2 == original

    # ── Edge cases ─────────────────────────────────────────────────────────

    def test_empty_strings(self, transformer):
        """All transformers should handle empty strings gracefully."""
        assert transformer.transform("", ["url_encode"]) == ""
        assert transformer.transform("", ["url_decode"]) == ""
        assert transformer.transform("", ["hex_encode"]) == ""
        assert transformer.transform("", ["hex_decode"]) == ""
        assert transformer.transform("", ["html_entities_encode"]) == ""
        assert transformer.transform("", ["html_entities_decode"]) == ""
        assert transformer.transform("", ["rot13"]) == ""
        assert transformer.transform("", ["unicode_escape"]) == ""
        assert transformer.transform("", ["unicode_unescape"]) == ""

    def test_unicode_emoji(self, transformer):
        """Test handling of emoji characters."""
        emoji = "😀🎉"

        # Hex roundtrip
        hex_encoded = transformer.transform(emoji, ["hex_encode"])
        hex_decoded = transformer.transform(hex_encoded, ["hex_decode"])
        assert hex_decoded == emoji

        # URL encoding
        url_encoded = transformer.transform(emoji, ["url_encode"])
        url_decoded = transformer.transform(url_encoded, ["url_decode"])
        assert url_decoded == emoji

    def test_already_encoded_input(self, transformer):
        """Test encoding already-encoded strings."""
        # URL encode an already percent-encoded string
        result = transformer.transform("hello%20world", ["url_encode"])
        assert result == "hello%2520world"  # The % gets encoded

        # HTML encode already-encoded entities
        result = transformer.transform("&lt;test&gt;", ["html_entities_encode"])
        assert "&amp;" in result  # The & gets encoded again

    def test_special_characters(self, transformer):
        """Test various special characters."""
        special = "!@#$%^&*()+={}[]|\\:;\"'<>,.?/"

        # URL encoding should handle all special chars
        encoded = transformer.transform(special, ["url_encode"])
        decoded = transformer.transform(encoded, ["url_decode"])
        assert decoded == special

        # Hex encoding should handle all special chars
        hex_enc = transformer.transform(special, ["hex_encode"])
        hex_dec = transformer.transform(hex_enc, ["hex_decode"])
        assert hex_dec == special

    def test_mixed_content(self, transformer):
        """Test strings with mixed ASCII, Unicode, and special characters."""
        mixed = "Hello 世界! café & <test> 123"

        # Hex roundtrip
        hex_enc = transformer.transform(mixed, ["hex_encode"])
        hex_dec = transformer.transform(hex_enc, ["hex_decode"])
        assert hex_dec == mixed

        # URL roundtrip
        url_enc = transformer.transform(mixed, ["url_encode"])
        url_dec = transformer.transform(url_enc, ["url_decode"])
        assert url_dec == mixed

    # ── Parameter tests ────────────────────────────────────────────────────

    def test_url_encode_with_safe_parameter(self, transformer):
        """Test url_encode with safe parameter."""
        url = "https://example.com/path?query=value"

        # Default: everything gets encoded
        result1 = transformer.transform(url, ["url_encode"])
        assert "%" in result1

        # With safe="/" : slashes preserved
        result2 = transformer.transform(url, [{"function": "url_encode", "safe": "/"}])
        assert result2.count("/") == 3  # https://example.com/ has 3 slashes

        # With safe=":/" : colon and slashes preserved
        result3 = transformer.transform(url, [{"function": "url_encode", "safe": ":/"}])
        assert ":" in result3
        assert "/" in result3

    def test_url_encode_with_empty_safe(self, transformer):
        """Test url_encode with explicit empty safe parameter."""
        result = transformer.transform("hello/world", [{"function": "url_encode", "safe": ""}])
        assert "hello%2Fworld" == result

    # ── Chaining tests ─────────────────────────────────────────────────────

    def test_chain_strip_then_url_encode(self, transformer):
        """Test chaining strip with url_encode."""
        result = transformer.transform("  hello world  ", ["strip", "url_encode"])
        assert result == "hello%20world"

    def test_chain_hex_encode_then_uppercase(self, transformer):
        """Test chaining hex_encode with uppercase."""
        result = transformer.transform("hello", ["hex_encode", "uppercase"])
        assert result == "68656C6C6F"

    def test_chain_multiple_encodings(self, transformer):
        """Test chaining multiple encoding transformations."""
        # Start with text, HTML encode, then URL encode
        result = transformer.transform(
            "<test>",
            ["html_entities_encode", "url_encode"]
        )
        # <test> -> &lt;test&gt; -> &lt;test&gt; with & encoded
        assert "%26" in result or "&" in result

        # Decode in reverse order
        decoded = transformer.transform(result, ["url_decode", "html_entities_decode"])
        assert decoded == "<test>"

    def test_chain_complex_transformation(self, transformer):
        """Test complex multi-step transformation."""
        # Strip, encode to hex, then uppercase
        result = transformer.transform(
            "  hello  ",
            [
                "strip",
                "hex_encode",
                "uppercase"
            ]
        )
        assert result == "68656C6C6F"

    def test_chain_with_rot13_twice(self, transformer):
        """Test chaining rot13 twice returns original."""
        result = transformer.transform("secret message", ["rot13", "rot13"])
        assert result == "secret message"

    def test_chain_encode_decode_sequence(self, transformer):
        """Test chaining encode and decode operations."""
        original = "test data"

        # Encode with multiple methods, then decode in reverse
        result = transformer.transform(
            original,
            [
                "hex_encode",
                "url_encode",
                "url_decode",
                "hex_decode",
            ]
        )
        assert result == original

    def test_chain_with_text_transformations(self, transformer):
        """Test encoding transformations chained with text transformations."""
        result = transformer.transform(
            "  HELLO WORLD  ",
            [
                "strip",
                "lowercase",
                "url_encode",
            ]
        )
        assert result == "hello%20world"

    # ── Unicode and internationalization tests ────────────────────────────

    def test_various_unicode_scripts(self, transformer):
        """Test various Unicode scripts."""
        scripts = {
            "cyrillic": "Привет мир",
            "arabic": "مرحبا بالعالم",
            "chinese": "你好世界",
            "japanese": "こんにちは世界",
            "korean": "안녕하세요 세계",
            "greek": "Γειά σου κόσμε",
            "hebrew": "שלום עולם",
        }

        for name, text in scripts.items():
            # Hex roundtrip
            hex_enc = transformer.transform(text, ["hex_encode"])
            hex_dec = transformer.transform(hex_enc, ["hex_decode"])
            assert hex_dec == text, f"Hex roundtrip failed for {name}"

            # URL roundtrip
            url_enc = transformer.transform(text, ["url_encode"])
            url_dec = transformer.transform(url_enc, ["url_decode"])
            assert url_dec == text, f"URL roundtrip failed for {name}"
