"""Cryptographic transformation plugin.

Provides hashing, encoding, UUID generation, and HMAC signing.
Pure stdlib — no external dependencies.
"""

import base64
import hashlib
import hmac as _hmac
import uuid as _uuid
from typing import Any, Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


class HashTextTransformer(ChainableTransformer[str, str]):
    """Hash a string using the specified algorithm."""

    def __init__(self, name: str, algorithm: str = "sha256"):
        super().__init__(name)
        self.algorithm = algorithm.lower()

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        h = hashlib.new(self.algorithm)
        h.update(value.encode("utf-8"))
        return h.hexdigest()


class Base64EncodeTransformer(ChainableTransformer[str, str]):
    """Encode a string to base64."""

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return base64.b64encode(value.encode("utf-8")).decode("ascii")


class Base64DecodeTransformer(ChainableTransformer[str, str]):
    """Decode a base64 string."""

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return base64.b64decode(value.encode("ascii")).decode("utf-8")


class UuidGenerateTransformer(ChainableTransformer[Any, str]):
    """Generate a UUID (v4 by default). Input value is ignored."""

    def __init__(self, name: str, version: int = 4):
        super().__init__(name)
        self.version = version

    def validate(self, value: Any) -> bool:
        return True

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        if self.version == 1:
            return str(_uuid.uuid1())
        return str(_uuid.uuid4())


class HmacSignTransformer(ChainableTransformer[str, str]):
    """Sign a string with HMAC using the specified key and algorithm."""

    def __init__(self, name: str, key: str = "", algorithm: str = "sha256"):
        super().__init__(name)
        self.key = key
        self.algorithm = algorithm.lower()

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return _hmac.new(
            self.key.encode("utf-8"),
            value.encode("utf-8"),
            self.algorithm,
        ).hexdigest()


class CryptoPlugin(TransformerPlugin):
    """Plugin providing cryptographic transformations."""

    def __init__(self):
        super().__init__("crypto")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "hash_text": lambda params: HashTextTransformer(
                "hash_text",
                algorithm=params.get("algorithm", "sha256"),
            ),
            "base64_encode": lambda _: Base64EncodeTransformer("base64_encode"),
            "base64_decode": lambda _: Base64DecodeTransformer("base64_decode"),
            "uuid_generate": lambda params: UuidGenerateTransformer(
                "uuid_generate",
                version=params.get("version", 4),
            ),
            "hmac_sign": lambda params: HmacSignTransformer(
                "hmac_sign",
                key=params.get("key", ""),
                algorithm=params.get("algorithm", "sha256"),
            ),
        }
