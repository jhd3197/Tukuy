"""Encoding transformation plugin.

Provides URL, hex, HTML entity, ROT13, and Unicode escape encoding and decoding.
Pure stdlib — no external dependencies.
"""

import codecs
import html
import urllib.parse
from typing import Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin, register_transformer


# ---------------------------------------------------------------------------
# Transformer classes
# ---------------------------------------------------------------------------

@register_transformer("url_encode", safe="")
class UrlEncodeTransformer(ChainableTransformer[str, str]):
    """Percent-encode a string for use in URLs.

    By default every character that is not an unreserved RFC 3986 character
    is encoded.  Pass *safe* to preserve specific characters (e.g. ``"/"``).
    """

    def __init__(self, name: str, safe: str = ""):
        super().__init__(name)
        self.safe = safe

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return urllib.parse.quote(value, safe=self.safe)


@register_transformer("url_decode")
class UrlDecodeTransformer(ChainableTransformer[str, str]):
    """Decode a percent-encoded string."""

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return urllib.parse.unquote(value)


@register_transformer("hex_encode")
class HexEncodeTransformer(ChainableTransformer[str, str]):
    """Encode a string as a hexadecimal representation of its UTF-8 bytes."""

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return value.encode("utf-8").hex()


@register_transformer("hex_decode")
class HexDecodeTransformer(ChainableTransformer[str, str]):
    """Decode a hexadecimal string back to UTF-8 text."""

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return bytes.fromhex(value).decode("utf-8")


@register_transformer("html_entities_encode")
class HtmlEntitiesEncodeTransformer(ChainableTransformer[str, str]):
    """Escape HTML special characters (``&``, ``<``, ``>``, ``\"``, ``'``)."""

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return html.escape(value)


@register_transformer("html_entities_decode")
class HtmlEntitiesDecodeTransformer(ChainableTransformer[str, str]):
    """Unescape HTML entities back to their original characters."""

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return html.unescape(value)


@register_transformer("rot13")
class Rot13Transformer(ChainableTransformer[str, str]):
    """Apply ROT13 substitution cipher to a string."""

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return codecs.decode(value, "rot_13")


@register_transformer("unicode_escape")
class UnicodeEscapeTransformer(ChainableTransformer[str, str]):
    r"""Escape non-ASCII characters to ``\uXXXX`` sequences."""

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return value.encode("unicode_escape").decode("ascii")


@register_transformer("unicode_unescape")
class UnicodeUnescapeTransformer(ChainableTransformer[str, str]):
    r"""Unescape ``\uXXXX`` sequences back to Unicode characters."""

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return value.encode("raw_unicode_escape").decode("unicode_escape")


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class EncodingPlugin(TransformerPlugin):
    """Plugin providing encoding and decoding transformations."""

    def __init__(self):
        super().__init__("encoding")

    @property
    def transformers(self) -> Dict[str, callable]:
        return self._auto_transformers()

    @property
    def manifest(self):
        from ...manifest import PluginManifest
        return PluginManifest(
            name="encoding",
            display_name="Encoding",
            description="URL, hex, HTML entity, ROT13, and Unicode escape encoding and decoding.",
            icon="binary",
            group="Core",
        )
