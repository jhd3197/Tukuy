"""Smart composition primitives -- Chain, Branch, Parallel.

Phase 5 of the Tukuy roadmap: replace linear-only chains with richer
composition patterns including conditional branching and fan-out/fan-in.

Usage::

    from tukuy import Chain, branch, parallel

    # Sequential
    chain = Chain(["strip", "lowercase"])
    result = chain.run("  HELLO  ")  # "hello"

    # Branching
    chain = Chain([
        "strip",
        branch(
            on_match=lambda v: "@" in v,
            true_path=["email_validator"],
            false_path=["url_validator"],
        ),
    ])

    # Parallel fan-out
    chain = Chain([
        parallel(
            steps=["extract_dates", "extract_emails"],
            merge="dict",
        ),
    ])
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional, Union
from logging import getLogger

from .types import TransformContext
from .context import SkillContext
from .plugins.base import PluginRegistry
from .registry import get_shared_registry
from .base import BaseTransformer
from .async_base import AsyncBaseTransformer

logger = getLogger(__name__)


def _ensure_skill_context(context: dict) -> SkillContext:
    """Return a SkillContext backed by *context*.

    If *context* already contains a ``__skill_context__`` key that is a
    SkillContext, return it.  Otherwise create one backed by the dict and
    store it for subsequent lookups.
    """
    existing = context.get("__skill_context__")
    if isinstance(existing, SkillContext):
        return existing
    ctx = SkillContext.from_dict(context)
    context["__skill_context__"] = ctx
    return ctx


def _step_name(step: Any) -> str:
    """Derive a key name from a step (used for Parallel dict-merge keys)."""
    if isinstance(step, str):
        return step
    if isinstance(step, dict):
        return step.get("function", "unknown")
    # Avoid circular import at module level
    from .skill import Skill

    if isinstance(step, Skill):
        return step.descriptor.name
    if callable(step) and hasattr(step, "__skill__"):
        return step.__skill__.descriptor.name
    if isinstance(step, (BaseTransformer, AsyncBaseTransformer)):
        return step.name
    if callable(step):
        return getattr(step, "__name__", "callable")
    return "unknown"


# ---------------------------------------------------------------------------
# Step resolution -- sync
# ---------------------------------------------------------------------------

def _resolve_and_run(step: Any, registry: PluginRegistry, value: Any, context: dict) -> Any:
    """Resolve a single step and execute it synchronously."""
    from .skill import Skill

    skill_ctx = _ensure_skill_context(context)

    # Composition primitives
    if isinstance(step, Branch):
        return step._run(value, context, registry)
    if isinstance(step, Parallel):
        return step._run(value, context, registry)
    if isinstance(step, Chain):
        return step.run(value, context)
    if isinstance(step, (list, tuple)):
        sub = Chain(list(step), registry=registry)
        return sub.run(value, context)

    # String -> registered transformer
    if isinstance(step, str):
        factory = registry.get_transformer(step)
        if factory is None:
            raise ValueError(f"Unknown transformer: {step!r}")
        transformer = factory({})
        result = transformer.transform(value, context)
        if result.failed:
            raise result.error
        return result.value

    # Dict -> parametrized registered transformer
    if isinstance(step, dict):
        func_name = step.get("function")
        if not func_name:
            raise ValueError(f"Dict step must have a 'function' key: {step}")
        params = {k: v for k, v in step.items() if k != "function"}
        factory = registry.get_transformer(func_name)
        if factory is None:
            raise ValueError(f"Unknown transformer: {func_name!r}")
        transformer = factory(params)
        result = transformer.transform(value, context)
        if result.failed:
            raise result.error
        return result.value

    # Skill instance
    if isinstance(step, Skill):
        sr = step.invoke(value, context=skill_ctx)
        if sr.failed:
            raise RuntimeError(sr.error)
        return sr.value

    # @skill-decorated callable
    if callable(step) and hasattr(step, "__skill__"):
        sr = step.__skill__.invoke(value, context=skill_ctx)
        if sr.failed:
            raise RuntimeError(sr.error)
        return sr.value

    # BaseTransformer / AsyncBaseTransformer instance
    if isinstance(step, (BaseTransformer, AsyncBaseTransformer)):
        result = step.transform(value, context)
        if result.failed:
            raise result.error
        return result.value

    # Plain callable
    if callable(step):
        return step(value)

    raise TypeError(f"Cannot resolve step of type {type(step).__name__}: {step!r}")


# ---------------------------------------------------------------------------
# Step resolution -- async
# ---------------------------------------------------------------------------

async def _async_resolve_and_run(
    step: Any, registry: PluginRegistry, value: Any, context: dict
) -> Any:
    """Resolve a single step and execute it asynchronously."""
    from .skill import Skill

    skill_ctx = _ensure_skill_context(context)

    # Composition primitives
    if isinstance(step, Branch):
        return await step._arun(value, context, registry)
    if isinstance(step, Parallel):
        return await step._arun(value, context, registry)
    if isinstance(step, Chain):
        return await step.arun(value, context)
    if isinstance(step, (list, tuple)):
        sub = Chain(list(step), registry=registry)
        return await sub.arun(value, context)

    # String -> registered transformer
    if isinstance(step, str):
        factory = registry.get_transformer(step)
        if factory is None:
            raise ValueError(f"Unknown transformer: {step!r}")
        transformer = factory({})
        result = transformer.transform(value, context)
        if asyncio.iscoroutine(result):
            result = await result
        if result.failed:
            raise result.error
        return result.value

    # Dict -> parametrized registered transformer
    if isinstance(step, dict):
        func_name = step.get("function")
        if not func_name:
            raise ValueError(f"Dict step must have a 'function' key: {step}")
        params = {k: v for k, v in step.items() if k != "function"}
        factory = registry.get_transformer(func_name)
        if factory is None:
            raise ValueError(f"Unknown transformer: {func_name!r}")
        transformer = factory(params)
        result = transformer.transform(value, context)
        if asyncio.iscoroutine(result):
            result = await result
        if result.failed:
            raise result.error
        return result.value

    # Skill instance
    if isinstance(step, Skill):
        sr = await step.ainvoke(value, context=skill_ctx)
        if sr.failed:
            raise RuntimeError(sr.error)
        return sr.value

    # @skill-decorated callable
    if callable(step) and hasattr(step, "__skill__"):
        sr = await step.__skill__.ainvoke(value, context=skill_ctx)
        if sr.failed:
            raise RuntimeError(sr.error)
        return sr.value

    # BaseTransformer / AsyncBaseTransformer instance
    if isinstance(step, (BaseTransformer, AsyncBaseTransformer)):
        result = step.transform(value, context)
        if asyncio.iscoroutine(result):
            result = await result
        if result.failed:
            raise result.error
        return result.value

    # Plain callable (maybe async)
    if callable(step):
        result = step(value)
        if inspect.isawaitable(result):
            result = await result
        return result

    raise TypeError(f"Cannot resolve step of type {type(step).__name__}: {step!r}")


# ---------------------------------------------------------------------------
# Chain
# ---------------------------------------------------------------------------

class Chain:
    """Execute a sequence of steps, passing each result to the next.

    Steps can be transformer names (strings), parametrized transforms (dicts),
    :class:`Branch` / :class:`Parallel` instances, :class:`~tukuy.skill.Skill`
    instances, plain callables, or nested ``Chain`` objects.

    Parameters
    ----------
    steps : list
        Ordered list of steps to execute.
    registry : PluginRegistry, optional
        Registry used to resolve transformer names.  If *None*, a default
        registry with all built-in plugins is created lazily.
    """

    def __init__(self, steps: List[Any], registry: Optional[PluginRegistry] = None):
        self.steps = list(steps)
        self._registry = registry

    @property
    def registry(self) -> PluginRegistry:
        if self._registry is None:
            self._registry = get_shared_registry()
        return self._registry

    def run(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute the chain synchronously.

        Parameters
        ----------
        value : Any
            The initial input value.
        context : dict, optional
            Shared context passed through all steps.

        Returns
        -------
        Any
            The final result after all steps.

        Raises
        ------
        ValueError
            If a transformer name is not found in the registry.
        RuntimeError
            If a skill invocation fails.
        TypeError
            If a step type is not recognised.
        """
        ctx = context if context is not None else {}
        current = value
        for step in self.steps:
            current = _resolve_and_run(step, self.registry, current, ctx)
        return current

    async def arun(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute the chain asynchronously.

        Async transformers and skills are awaited.  Sync ones are called
        normally.  :class:`Parallel` steps use ``asyncio.gather`` for
        concurrency.
        """
        ctx = context if context is not None else {}
        current = value
        for step in self.steps:
            current = await _async_resolve_and_run(step, self.registry, current, ctx)
        return current

    def __call__(self, value: Any) -> Any:
        """Shortcut for ``self.run(value)``."""
        return self.run(value)

    def __add__(self, other: "Chain") -> "Chain":
        """Concatenate two chains."""
        if isinstance(other, Chain):
            return Chain(self.steps + other.steps, registry=self._registry)
        return NotImplemented

    def __repr__(self) -> str:
        return f"Chain(steps={self.steps!r})"


# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------

class Branch:
    """Conditional step that routes to one of two paths.

    Parameters
    ----------
    on_match : callable
        Predicate ``f(value) -> bool``.
    true_path : list
        Steps to execute when the predicate returns *True*.
    false_path : list, optional
        Steps to execute when the predicate returns *False*.
        If *None*, the value passes through unchanged.
    """

    def __init__(
        self,
        on_match: Callable[[Any], bool],
        true_path: List[Any],
        false_path: Optional[List[Any]] = None,
    ):
        self.on_match = on_match
        self.true_path = list(true_path)
        self.false_path = list(false_path) if false_path is not None else None

    # -- internal (called by Chain via _resolve_and_run) ---------------------

    def _run(self, value: Any, context: dict, registry: PluginRegistry) -> Any:
        if self.on_match(value):
            sub = Chain(self.true_path, registry=registry)
            return sub.run(value, context)
        if self.false_path is not None:
            sub = Chain(self.false_path, registry=registry)
            return sub.run(value, context)
        return value

    async def _arun(self, value: Any, context: dict, registry: PluginRegistry) -> Any:
        if self.on_match(value):
            sub = Chain(self.true_path, registry=registry)
            return await sub.arun(value, context)
        if self.false_path is not None:
            sub = Chain(self.false_path, registry=registry)
            return await sub.arun(value, context)
        return value

    def __repr__(self) -> str:
        return (
            f"Branch(true_path={self.true_path!r}, "
            f"false_path={self.false_path!r})"
        )


# ---------------------------------------------------------------------------
# Parallel
# ---------------------------------------------------------------------------

class Parallel:
    """Fan-out step that runs multiple steps on the same input and merges.

    Parameters
    ----------
    steps : list
        Steps to run in parallel (each receives the same input value).
    merge : str or callable
        Merge strategy for combining results:

        - ``"dict"``  -- ``{step_name: result, ...}``
        - ``"list"``  -- ``[result, ...]``
        - ``"first"`` -- first successful result (sequential fallback in sync,
          concurrent race in async)
        - callable     -- ``f(results_dict) -> merged_value``
    """

    def __init__(
        self,
        steps: List[Any],
        merge: Union[str, Callable] = "dict",
    ):
        self.steps = list(steps)
        self.merge = merge

    # -- internal (called by Chain via _resolve_and_run) ---------------------

    def _run(self, value: Any, context: dict, registry: PluginRegistry) -> Any:
        if self.merge == "first":
            return self._run_first(value, context, registry)

        skill_ctx = _ensure_skill_context(context)

        results_dict: Dict[str, Any] = {}
        results_list: List[Any] = []
        for i, step in enumerate(self.steps):
            name = _step_name(step)
            # Create scoped context for each parallel branch
            branch_ctx = skill_ctx.scope(f"parallel_{i}")
            branch_dict = context.copy()
            branch_dict["__skill_context__"] = branch_ctx
            result = _resolve_and_run(step, registry, value, branch_dict)
            # Merge scoped writes back into root
            if name in results_dict:
                name = f"{name}_{len(results_list)}"
            results_dict[name] = result
            results_list.append(result)

        return self._apply_merge(results_dict, results_list)

    def _run_first(self, value: Any, context: dict, registry: PluginRegistry) -> Any:
        """Run steps sequentially; return first success."""
        last_error: Optional[BaseException] = None
        for step in self.steps:
            try:
                return _resolve_and_run(step, registry, value, context)
            except Exception as exc:
                last_error = exc
                continue
        raise RuntimeError(
            f"All {len(self.steps)} parallel steps failed"
        ) from last_error

    async def _arun(self, value: Any, context: dict, registry: PluginRegistry) -> Any:
        if self.merge == "first":
            return await self._arun_first(value, context, registry)

        skill_ctx = _ensure_skill_context(context)

        # Create scoped context dicts for each parallel branch
        branch_contexts = []
        for i in range(len(self.steps)):
            branch_ctx = skill_ctx.scope(f"parallel_{i}")
            branch_dict = context.copy()
            branch_dict["__skill_context__"] = branch_ctx
            branch_contexts.append(branch_dict)

        tasks = [
            _async_resolve_and_run(step, registry, value, branch_contexts[i])
            for i, step in enumerate(self.steps)
        ]
        results_list = list(await asyncio.gather(*tasks))

        results_dict: Dict[str, Any] = {}
        for i, step in enumerate(self.steps):
            name = _step_name(step)
            if name in results_dict:
                name = f"{name}_{i}"
            results_dict[name] = results_list[i]

        return self._apply_merge(results_dict, results_list)

    async def _arun_first(
        self, value: Any, context: dict, registry: PluginRegistry
    ) -> Any:
        """Run all steps concurrently; return first non-error result."""
        tasks = [
            _async_resolve_and_run(step, registry, value, context)
            for step in self.steps
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if not isinstance(r, BaseException):
                return r
        # All failed -- raise from the last exception
        last_exc = next(
            (r for r in reversed(results) if isinstance(r, BaseException)), None
        )
        raise RuntimeError(
            f"All {len(self.steps)} parallel steps failed"
        ) from last_exc

    def _apply_merge(
        self, results_dict: Dict[str, Any], results_list: List[Any]
    ) -> Any:
        if self.merge == "dict":
            return results_dict
        if self.merge == "list":
            return results_list
        if callable(self.merge):
            return self.merge(results_dict)
        raise ValueError(f"Unknown merge strategy: {self.merge!r}")

    def __repr__(self) -> str:
        return f"Parallel(steps={self.steps!r}, merge={self.merge!r})"


# ---------------------------------------------------------------------------
# Factory functions (match the FEEDBACK.md API)
# ---------------------------------------------------------------------------

def branch(
    on_match: Callable[[Any], bool],
    true_path: List[Any],
    false_path: Optional[List[Any]] = None,
) -> Branch:
    """Create a :class:`Branch` step.

    Example::

        branch(
            on_match=lambda v: "@" in v,
            true_path=["email_validator"],
            false_path=["url_validator"],
        )
    """
    return Branch(on_match=on_match, true_path=true_path, false_path=false_path)


def parallel(
    steps: Optional[List[Any]] = None,
    *,
    extractors: Optional[List[Any]] = None,
    merge: Union[str, Callable] = "dict",
    merge_strategy: Optional[Union[str, Callable]] = None,
) -> Parallel:
    """Create a :class:`Parallel` step.

    Accepts *steps* or *extractors* (alias) and *merge* or *merge_strategy*
    (alias).

    Example::

        parallel(
            steps=["extract_dates", "extract_emails"],
            merge="dict",
        )

        parallel(
            extractors=["extract_dates", "extract_emails"],
            merge_strategy="dict",
        )
    """
    actual_steps = steps if steps is not None else (
        extractors if extractors is not None else []
    )
    actual_merge = merge_strategy if merge_strategy is not None else merge
    return Parallel(steps=actual_steps, merge=actual_merge)


__all__ = [
    "Chain",
    "Branch",
    "Parallel",
    "branch",
    "parallel",
]
