"""Skill contract system for Tukuy — declared-upfront skill descriptors, results, and invocation."""

import time
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    TypeVar,
)

from .types import TransformResult

R = TypeVar("R")


# ---------------------------------------------------------------------------
# Schema resolution helper
# ---------------------------------------------------------------------------

_PYTHON_TYPE_SCHEMAS: Dict[type, Dict[str, str]] = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number"},
    bool: {"type": "boolean"},
    list: {"type": "array"},
    dict: {"type": "object"},
    bytes: {"type": "string", "contentEncoding": "base64"},
}


def _resolve_schema(schema: Any) -> Optional[Dict[str, Any]]:
    """Resolve a schema value to a JSON Schema dict.

    Accepts:
      - ``None`` → passthrough (returns ``None``)
      - A ``dict`` → passthrough (assumed to be a valid JSON Schema)
      - A Python built-in type (``str``, ``int``, …) → mapped to JSON Schema
      - A class with a ``model_json_schema()`` classmethod (Pydantic v2 duck-typing)
      - A class with a ``schema()`` classmethod (Pydantic v1 duck-typing)
    """
    if schema is None:
        return None

    if isinstance(schema, dict):
        return schema

    if isinstance(schema, type) and schema in _PYTHON_TYPE_SCHEMAS:
        return dict(_PYTHON_TYPE_SCHEMAS[schema])

    # Pydantic v2 duck-typing
    if isinstance(schema, type) and hasattr(schema, "model_json_schema"):
        return schema.model_json_schema()  # type: ignore[union-attr]

    # Pydantic v1 duck-typing
    if isinstance(schema, type) and hasattr(schema, "schema"):
        return schema.schema()  # type: ignore[union-attr]

    raise TypeError(
        f"Cannot resolve schema from {schema!r}. "
        "Expected None, dict, Python type (str/int/…), or Pydantic model class."
    )


# ---------------------------------------------------------------------------
# SkillExample
# ---------------------------------------------------------------------------

@dataclass
class SkillExample:
    """A structured example demonstrating skill usage."""

    input: Any
    output: Any
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "description": self.description,
        }


# ---------------------------------------------------------------------------
# SkillDescriptor
# ---------------------------------------------------------------------------

@dataclass
class SkillDescriptor:
    """Declared-upfront contract for a skill.

    Provides identity, typed I/O schemas, discovery metadata, operational
    hints, and safety declarations that any agent framework can consume.
    """

    # Identity
    name: str
    description: str
    version: str = "0.1.0"

    # I/O — accept Python types, dicts, or Pydantic models; resolved in __post_init__
    input_schema: Optional[Any] = None
    output_schema: Optional[Any] = None

    # Discovery
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    examples: List[SkillExample] = field(default_factory=list)

    # Operational hints
    is_async: bool = False
    estimated_latency_ms: Optional[int] = None
    idempotent: bool = False
    side_effects: bool = False

    # Safety declarations
    required_imports: List[str] = field(default_factory=list)
    requires_network: bool = False
    requires_filesystem: bool = False

    def __post_init__(self) -> None:
        # Resolve schemas to JSON Schema dicts
        self.input_schema = _resolve_schema(self.input_schema)
        self.output_schema = _resolve_schema(self.output_schema)

        # Normalize tags to lowercase
        self.tags = [t.lower() for t in self.tags]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the descriptor to a plain dict."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "category": self.category,
            "tags": self.tags,
            "examples": [e.to_dict() for e in self.examples],
            "is_async": self.is_async,
            "estimated_latency_ms": self.estimated_latency_ms,
            "idempotent": self.idempotent,
            "side_effects": self.side_effects,
            "required_imports": self.required_imports,
            "requires_network": self.requires_network,
            "requires_filesystem": self.requires_filesystem,
        }

    @classmethod
    def from_metadata(cls, metadata: Any) -> "SkillDescriptor":
        """Create a SkillDescriptor from a ``TransformerMetadata`` instance.

        This bridge lets legacy transformers participate in the skills system.
        The *metadata* parameter is typed as ``Any`` to avoid a hard import of
        the introspection module; it is expected to be a ``TransformerMetadata``.
        """
        tags = list(getattr(metadata, "tags", set()))

        examples: List[SkillExample] = []
        for ex in getattr(metadata, "examples", []):
            if isinstance(ex, str):
                examples.append(SkillExample(input=ex, output=None, description=ex))
            else:
                examples.append(SkillExample(input=ex, output=None))

        return cls(
            name=metadata.name,
            description=metadata.description,
            version=getattr(metadata, "version", "v1"),
            category=getattr(metadata, "category", "general")
            if isinstance(getattr(metadata, "category", None), str)
            else getattr(getattr(metadata, "category", None), "value", "general"),
            tags=tags,
            examples=examples,
        )


# ---------------------------------------------------------------------------
# SkillResult
# ---------------------------------------------------------------------------

@dataclass
class SkillResult(Generic[R]):
    """Container for skill invocation results.

    Richer than ``TransformResult`` — adds ``duration_ms``, ``retryable``,
    and an arbitrary ``metadata`` bag.
    """

    value: Optional[R] = None
    error: Optional[str] = None
    success: bool = True
    duration_ms: Optional[float] = None
    retryable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        return not self.success

    def to_transform_result(self) -> TransformResult:
        """Convert to a legacy ``TransformResult``."""
        if self.success:
            return TransformResult(value=self.value)
        return TransformResult(error=Exception(self.error))

    @classmethod
    def from_transform_result(cls, result: TransformResult) -> "SkillResult":
        """Create a ``SkillResult`` from a legacy ``TransformResult``."""
        if result.success:
            return cls(value=result.value, success=True)
        return cls(
            error=str(result.error) if result.error else "Unknown error",
            success=False,
        )


# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------

@dataclass
class Skill:
    """Binds a :class:`SkillDescriptor` to a callable and provides ``invoke()``."""

    descriptor: SkillDescriptor
    fn: Callable

    def invoke(self, *args: Any, **kwargs: Any) -> SkillResult:
        """Invoke the skill, timing execution and catching exceptions.

        If the callable returns a ``TransformResult``, it is automatically
        lifted into a ``SkillResult``.
        """
        start = time.perf_counter()
        try:
            raw = self.fn(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if isinstance(raw, TransformResult):
                result = SkillResult.from_transform_result(raw)
                result.duration_ms = elapsed_ms
                return result

            return SkillResult(value=raw, success=True, duration_ms=elapsed_ms)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return SkillResult(
                error=str(exc),
                success=False,
                duration_ms=elapsed_ms,
                retryable=self.descriptor.idempotent,
            )


__all__ = [
    "SkillExample",
    "SkillDescriptor",
    "SkillResult",
    "Skill",
]
