"""Skill contract system for Tukuy — declared-upfront skill descriptors, results, and invocation."""

import inspect
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
# Context-injection helpers
# ---------------------------------------------------------------------------

def _has_context_param(fn: Callable) -> Optional[str]:
    """Return the parameter name annotated as ``SkillContext``, or *None*.

    We check by annotation name string to avoid a hard circular import
    of ``context.py`` at module level.
    """
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError):
        return None

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        ann = param.annotation
        if ann is inspect.Parameter.empty:
            continue
        # Check by class identity (if already imported) or name string
        ann_name = getattr(ann, "__name__", None) or getattr(ann, "__qualname__", str(ann))
        if ann_name == "SkillContext":
            return name
    return None


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
# Schema inference from function signatures
# ---------------------------------------------------------------------------


def _infer_schemas(fn: Callable) -> tuple:
    """Infer (input_schema, output_schema) from a function's type annotations.

    Skips ``self``, ``cls``, and ``SkillContext`` parameters by name /
    annotation.  Returns ``None`` for any annotation that
    ``_resolve_schema`` cannot handle (complex generics, etc.).
    """
    sig = inspect.signature(fn)

    # --- input schema: first non-self/cls/context parameter's annotation ---
    input_schema = None
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        # Skip SkillContext parameters
        ann = param.annotation
        if ann is not inspect.Parameter.empty:
            ann_name = getattr(ann, "__name__", None) or getattr(ann, "__qualname__", str(ann))
            if ann_name == "SkillContext":
                continue
        if ann is not inspect.Parameter.empty:
            try:
                input_schema = _resolve_schema(ann)
            except (TypeError, Exception):
                input_schema = None
        break  # only consider the first eligible parameter

    # --- output schema: return annotation ----------------------------------
    output_schema = None
    if sig.return_annotation is not inspect.Signature.empty:
        try:
            output_schema = _resolve_schema(sig.return_annotation)
        except (TypeError, Exception):
            output_schema = None

    return (input_schema, output_schema)


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
    """Binds a :class:`SkillDescriptor` to a callable and provides ``invoke()``.

    When the wrapped function has a parameter annotated as
    :class:`~tukuy.context.SkillContext`, it will be automatically injected
    if a ``context`` keyword argument is passed to :meth:`invoke` /
    :meth:`ainvoke`.
    """

    descriptor: SkillDescriptor
    fn: Callable

    # Cached on first call
    _ctx_param: Optional[str] = field(default=None, init=False, repr=False)
    _ctx_param_checked: bool = field(default=False, init=False, repr=False)

    @property
    def _context_param_name(self) -> Optional[str]:
        """Lazily resolve whether ``fn`` expects a SkillContext parameter."""
        if not self._ctx_param_checked:
            self._ctx_param = _has_context_param(self.fn)
            self._ctx_param_checked = True
        return self._ctx_param

    def _inject_context(self, args: tuple, kwargs: dict) -> tuple:
        """If the function accepts a SkillContext, inject it from *kwargs*.

        The caller passes ``context=<SkillContext>`` as an extra kwarg.
        We pop it and inject it under the correct parameter name.
        Returns ``(args, kwargs)`` — possibly mutated.
        """
        ctx = kwargs.pop("context", None)
        param_name = self._context_param_name
        if param_name is not None and ctx is not None:
            kwargs[param_name] = ctx
        return args, kwargs

    def invoke(self, *args: Any, **kwargs: Any) -> SkillResult:
        """Invoke the skill, timing execution and catching exceptions.

        If the callable returns a ``TransformResult``, it is automatically
        lifted into a ``SkillResult``.

        Pass ``context=<SkillContext>`` to provide a context instance.  It
        will be injected into the function if it has a matching parameter.

        Pass ``policy=<SafetyPolicy>`` to validate against a specific policy.
        If not provided, the active policy from :func:`~tukuy.safety.get_policy`
        is used.  If no policy is active, the skill runs unrestricted.
        """
        # Safety enforcement
        policy = kwargs.pop("policy", None)
        if policy is None:
            from .safety import get_policy
            policy = get_policy()
        if policy is not None:
            from .safety import SafetyError
            violations = policy.validate(self.descriptor)
            if violations:
                return SkillResult(
                    error=str(SafetyError(violations)),
                    success=False,
                    retryable=False,
                    metadata={"safety_violations": [str(v) for v in violations]},
                )

        args, kwargs = self._inject_context(args, kwargs)
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

    async def ainvoke(self, *args: Any, **kwargs: Any) -> SkillResult:
        """Async version of :meth:`invoke`.

        If the wrapped callable is a coroutine function its result is awaited;
        otherwise it is called synchronously (so sync skills work with
        ``ainvoke`` too).

        Pass ``context=<SkillContext>`` to provide a context instance.

        Pass ``policy=<SafetyPolicy>`` to validate against a specific policy.
        If not provided, the active policy from :func:`~tukuy.safety.get_policy`
        is used.
        """
        # Safety enforcement
        policy = kwargs.pop("policy", None)
        if policy is None:
            from .safety import get_policy
            policy = get_policy()
        if policy is not None:
            from .safety import SafetyError
            violations = policy.validate(self.descriptor)
            if violations:
                return SkillResult(
                    error=str(SafetyError(violations)),
                    success=False,
                    retryable=False,
                    metadata={"safety_violations": [str(v) for v in violations]},
                )

        args, kwargs = self._inject_context(args, kwargs)
        start = time.perf_counter()
        try:
            raw = self.fn(*args, **kwargs)
            if inspect.isawaitable(raw):
                raw = await raw
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


# ---------------------------------------------------------------------------
# @skill decorator
# ---------------------------------------------------------------------------


def skill(
    fn=None,
    *,
    name=None,
    description=None,
    version="0.1.0",
    input_schema=None,
    output_schema=None,
    category="general",
    tags=None,
    examples=None,
    is_async=None,
    estimated_latency_ms=None,
    idempotent=False,
    side_effects=False,
    required_imports=None,
    requires_network=False,
    requires_filesystem=False,
):
    """Decorator that turns a function into a skill.

    Supports three calling conventions::

        @skill
        def my_fn(x: int) -> str: ...

        @skill()
        def my_fn(x: int) -> str: ...

        @skill(name="custom", tags=["text"])
        def my_fn(x: int) -> str: ...

    The decorated function remains directly callable.  A ``Skill`` instance is
    attached as ``fn.__skill__``.
    """

    def _attach(func):
        resolved_name = name if name is not None else func.__name__
        resolved_description = description if description is not None else (func.__doc__ or "").strip()
        resolved_is_async = is_async if is_async is not None else inspect.iscoroutinefunction(func)

        inferred_input, inferred_output = _infer_schemas(func)
        resolved_input_schema = input_schema if input_schema is not None else inferred_input
        resolved_output_schema = output_schema if output_schema is not None else inferred_output

        descriptor = SkillDescriptor(
            name=resolved_name,
            description=resolved_description,
            version=version,
            input_schema=resolved_input_schema,
            output_schema=resolved_output_schema,
            category=category,
            tags=tags if tags is not None else [],
            examples=examples if examples is not None else [],
            is_async=resolved_is_async,
            estimated_latency_ms=estimated_latency_ms,
            idempotent=idempotent,
            side_effects=side_effects,
            required_imports=required_imports if required_imports is not None else [],
            requires_network=requires_network,
            requires_filesystem=requires_filesystem,
        )

        func.__skill__ = Skill(descriptor=descriptor, fn=func)
        return func

    if fn is not None:
        # Bare @skill usage
        return _attach(fn)

    # @skill() or @skill(name=...) usage
    return _attach


__all__ = [
    "SkillExample",
    "SkillDescriptor",
    "SkillResult",
    "Skill",
    "skill",
]
