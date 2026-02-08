"""Tests for Phase 5: Smart Composition (Chain / Branch / Parallel).

Covers:
  - Chain: sequential execution with string, dict, callable, Skill, and
    BaseTransformer steps; nested sub-chains; context passing; __call__; __add__
  - Branch: true path, false path, pass-through when no false_path
  - Parallel: dict merge, list merge, first-success merge, custom callable merge,
    duplicate step names
  - Async variants: arun for Chain, Branch, and Parallel; asyncio.gather
    concurrency in Parallel
  - Factory functions: branch(), parallel() with aliases
  - Error handling: unknown transformer, missing function key, unknown step type,
    skill failure propagation
  - Integration: complex chains combining Branch + Parallel
"""

import asyncio

import pytest

from tukuy.chain import (
    Chain,
    Branch,
    Parallel,
    branch,
    parallel,
    _step_name,
)
from tukuy.base import BaseTransformer, ChainableTransformer
from tukuy.async_base import AsyncBaseTransformer
from tukuy.skill import Skill, SkillDescriptor, skill
from tukuy.plugins.base import PluginRegistry
from tukuy.types import TransformContext, TransformResult


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

class UpperTransformer(BaseTransformer):
    def validate(self, value):
        return isinstance(value, str)

    def _transform(self, value, context=None):
        return value.upper()


class AddSuffixTransformer(BaseTransformer):
    def __init__(self, suffix="!"):
        super().__init__("add_suffix")
        self.suffix = suffix

    def validate(self, value):
        return isinstance(value, str)

    def _transform(self, value, context=None):
        return value + self.suffix


class AsyncUpperTransformer(AsyncBaseTransformer):
    def validate(self, value):
        return isinstance(value, str)

    async def _transform(self, value, context=None):
        await asyncio.sleep(0)
        return value.upper()


def double(x):
    return x * 2


async def async_double(x):
    await asyncio.sleep(0)
    return x * 2


# ---------------------------------------------------------------------------
# Chain basics
# ---------------------------------------------------------------------------

class TestChainBasics:
    """Sequential execution through the chain."""

    def test_string_steps(self):
        chain = Chain(["strip", "lowercase"])
        assert chain.run("  HELLO  ") == "hello"

    def test_dict_steps(self):
        chain = Chain([
            "strip",
            {"function": "truncate", "length": 3, "suffix": ""},
        ])
        assert chain.run("  Hello World  ") == "Hel"

    def test_mixed_string_and_dict(self):
        chain = Chain([
            "strip",
            "lowercase",
            {"function": "replace", "from": "hello", "to": "hi"},
        ])
        assert chain.run("  HELLO  ") == "hi"

    def test_callable_steps(self):
        chain = Chain([
            str.strip,
            str.lower,
        ])
        assert chain.run("  HELLO  ") == "hello"

    def test_lambda_steps(self):
        chain = Chain([
            lambda v: v.strip(),
            lambda v: v.upper(),
        ])
        assert chain.run("  hello  ") == "HELLO"

    def test_base_transformer_steps(self):
        chain = Chain([
            UpperTransformer("upper"),
            AddSuffixTransformer("!"),
        ])
        assert chain.run("hello") == "HELLO!"

    def test_skill_instance_step(self):
        @skill
        def exclaim(text: str) -> str:
            return text + "!"

        chain = Chain([exclaim.__skill__])
        assert chain.run("hello") == "hello!"

    def test_skill_decorated_fn_step(self):
        @skill
        def exclaim(text: str) -> str:
            return text + "!"

        chain = Chain([exclaim])
        assert chain.run("hello") == "hello!"

    def test_empty_chain(self):
        chain = Chain([])
        assert chain.run("hello") == "hello"

    def test_single_step(self):
        chain = Chain(["strip"])
        assert chain.run("  hi  ") == "hi"

    def test_context_shared_across_steps(self):
        """Context dict should be shared and mutable across steps."""
        def set_ctx(value):
            # We can't easily access context from a plain callable,
            # so test via a BaseTransformer that writes to context.
            return value

        class ContextWriter(BaseTransformer):
            def validate(self, value):
                return True

            def _transform(self, value, context=None):
                if context is not None:
                    context["seen"] = value
                return value

        class ContextReader(BaseTransformer):
            def validate(self, value):
                return True

            def _transform(self, value, context=None):
                if context is not None:
                    return context.get("seen", "NOT_FOUND")
                return value

        ctx = {}
        chain = Chain([ContextWriter("w"), ContextReader("r")])
        result = chain.run("ping", context=ctx)
        assert result == "ping"
        assert ctx["seen"] == "ping"

    def test_chain_with_explicit_registry(self):
        from tukuy import TukuyTransformer
        t = TukuyTransformer()
        chain = Chain(["strip", "lowercase"], registry=t.registry)
        assert chain.run("  HI  ") == "hi"

    def test_nested_list_subchain(self):
        """A list/tuple step is treated as an inline sub-chain."""
        chain = Chain([
            "strip",
            ["lowercase", lambda v: v + "!"],
        ])
        assert chain.run("  HELLO  ") == "hello!"

    def test_nested_chain_instance(self):
        inner = Chain(["strip", "lowercase"])
        outer = Chain([inner, lambda v: v + "!"])
        assert outer.run("  HELLO  ") == "hello!"

    def test_call_dunder(self):
        chain = Chain(["strip"])
        assert chain("  hi  ") == "hi"

    def test_add_chains(self):
        c1 = Chain(["strip"])
        c2 = Chain(["lowercase"])
        combined = c1 + c2
        assert combined.run("  HELLO  ") == "hello"
        # Originals unchanged
        assert len(c1.steps) == 1
        assert len(c2.steps) == 1

    def test_repr(self):
        chain = Chain(["strip", "lowercase"])
        assert "Chain" in repr(chain)
        assert "strip" in repr(chain)


# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------

class TestBranch:
    """Conditional routing via Branch."""

    def test_true_path(self):
        chain = Chain([
            "strip",
            branch(
                on_match=lambda v: v.startswith("h"),
                true_path=[lambda v: v.upper()],
                false_path=[lambda v: v.lower()],
            ),
        ])
        assert chain.run("  hello  ") == "HELLO"

    def test_false_path(self):
        chain = Chain([
            "strip",
            branch(
                on_match=lambda v: v.startswith("h"),
                true_path=[lambda v: v.upper()],
                false_path=[lambda v: v + "!!!"],
            ),
        ])
        assert chain.run("  world  ") == "world!!!"

    def test_no_false_path_passthrough(self):
        """If false_path is None, value passes through unchanged."""
        chain = Chain([
            "strip",
            branch(
                on_match=lambda v: v.startswith("x"),
                true_path=[lambda v: v.upper()],
            ),
        ])
        assert chain.run("  hello  ") == "hello"

    def test_branch_with_registered_transformers(self):
        chain = Chain([
            "strip",
            branch(
                on_match=lambda v: len(v) > 5,
                true_path=["uppercase"],
                false_path=["lowercase"],
            ),
        ])
        assert chain.run("  Hello World  ") == "HELLO WORLD"
        assert chain.run("  Hi  ") == "hi"

    def test_nested_branches(self):
        chain = Chain([
            branch(
                on_match=lambda v: isinstance(v, str),
                true_path=[
                    branch(
                        on_match=lambda v: len(v) > 3,
                        true_path=[lambda v: "long"],
                        false_path=[lambda v: "short"],
                    )
                ],
                false_path=[lambda v: "not_string"],
            ),
        ])
        assert chain.run("hello") == "long"
        assert chain.run("hi") == "short"

    def test_branch_repr(self):
        b = Branch(
            on_match=lambda v: True,
            true_path=["strip"],
            false_path=["lowercase"],
        )
        assert "Branch" in repr(b)

    def test_branch_factory_returns_branch(self):
        b = branch(on_match=lambda v: True, true_path=["strip"])
        assert isinstance(b, Branch)


# ---------------------------------------------------------------------------
# Parallel
# ---------------------------------------------------------------------------

class TestParallel:
    """Fan-out / fan-in via Parallel."""

    def test_dict_merge(self):
        chain = Chain([
            parallel(
                steps=[
                    lambda v: v.upper(),
                    lambda v: v.lower(),
                    lambda v: len(v),
                ],
                merge="dict",
            ),
        ])
        result = chain.run("Hello")
        assert isinstance(result, dict)
        assert "HELLO" in result.values()
        assert "hello" in result.values()
        assert 5 in result.values()

    def test_dict_merge_with_named_transformers(self):
        chain = Chain([
            parallel(
                steps=["uppercase", "lowercase"],
                merge="dict",
            ),
        ])
        result = chain.run("Hello")
        assert result["uppercase"] == "HELLO"
        assert result["lowercase"] == "hello"

    def test_list_merge(self):
        chain = Chain([
            parallel(
                steps=[
                    lambda v: v.upper(),
                    lambda v: v.lower(),
                ],
                merge="list",
            ),
        ])
        result = chain.run("Hello")
        assert result == ["HELLO", "hello"]

    def test_first_merge_success(self):
        """First merge returns the first successful result."""
        chain = Chain([
            parallel(
                steps=[
                    lambda v: v.upper(),
                    lambda v: v.lower(),
                ],
                merge="first",
            ),
        ])
        assert chain.run("Hello") == "HELLO"

    def test_first_merge_fallback(self):
        """First merge skips failures and returns first success."""
        def fail_step(v):
            raise ValueError("intentional failure")

        chain = Chain([
            parallel(
                steps=[
                    fail_step,
                    lambda v: v.upper(),
                ],
                merge="first",
            ),
        ])
        assert chain.run("hello") == "HELLO"

    def test_first_merge_all_fail(self):
        def fail_a(v):
            raise ValueError("fail_a")

        def fail_b(v):
            raise ValueError("fail_b")

        chain = Chain([
            parallel(steps=[fail_a, fail_b], merge="first"),
        ])
        with pytest.raises(RuntimeError, match="All 2 parallel steps failed"):
            chain.run("hello")

    def test_custom_callable_merge(self):
        def merge_fn(results_dict):
            return " + ".join(str(v) for v in results_dict.values())

        chain = Chain([
            parallel(
                steps=[
                    lambda v: v.upper(),
                    lambda v: v.lower(),
                ],
                merge=merge_fn,
            ),
        ])
        result = chain.run("Hello")
        assert "HELLO" in result
        assert "hello" in result
        assert " + " in result

    def test_duplicate_step_names(self):
        """Duplicate names get de-duplicated with index suffix."""
        chain = Chain([
            parallel(
                steps=[
                    lambda v: v + "1",
                    lambda v: v + "2",
                ],
                merge="dict",
            ),
        ])
        result = chain.run("x")
        # Both lambdas have the same __name__ ("<lambda>"), so one
        # gets an index suffix.
        assert len(result) == 2
        assert set(result.values()) == {"x1", "x2"}

    def test_parallel_with_base_transformers(self):
        chain = Chain([
            parallel(
                steps=[
                    UpperTransformer("upper"),
                    AddSuffixTransformer("?"),
                ],
                merge="dict",
            ),
        ])
        result = chain.run("hello")
        assert result["upper"] == "HELLO"
        assert result["add_suffix"] == "hello?"

    def test_parallel_repr(self):
        p = Parallel(steps=["a", "b"], merge="list")
        assert "Parallel" in repr(p)

    def test_parallel_factory_returns_parallel(self):
        p = parallel(steps=["a", "b"])
        assert isinstance(p, Parallel)

    def test_parallel_extractors_alias(self):
        """The `extractors` kwarg is an alias for `steps`."""
        p = parallel(extractors=["a", "b"])
        assert p.steps == ["a", "b"]

    def test_parallel_merge_strategy_alias(self):
        """The `merge_strategy` kwarg is an alias for `merge`."""
        p = parallel(steps=["a"], merge_strategy="list")
        assert p.merge == "list"

    def test_unknown_merge_strategy(self):
        chain = Chain([
            Parallel(steps=[lambda v: v], merge="bogus"),
        ])
        with pytest.raises(ValueError, match="Unknown merge strategy"):
            chain.run("x")


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------

class TestAsync:
    """Async execution via Chain.arun()."""

    @pytest.mark.asyncio
    async def test_arun_with_sync_steps(self):
        chain = Chain(["strip", "lowercase"])
        result = await chain.arun("  HELLO  ")
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_arun_with_async_callable(self):
        chain = Chain([
            async_double,
            async_double,
        ])
        result = await chain.arun(3)
        assert result == 12

    @pytest.mark.asyncio
    async def test_arun_with_mixed_sync_async(self):
        chain = Chain([
            lambda v: v.strip(),
            async_double,
        ])
        # async_double on string " hi " stripped → "hi" doubled → "hihi"
        # Wait, strip returns " hi " → "hi", then double("hi") → "hihi"
        # Actually we're chaining: strip gives "hi", then async_double("hi") = "hihi"
        result = await chain.arun(" hi ")
        assert result == "hihi"

    @pytest.mark.asyncio
    async def test_arun_branch(self):
        chain = Chain([
            branch(
                on_match=lambda v: v > 0,
                true_path=[lambda v: v * 10],
                false_path=[lambda v: v * -1],
            ),
        ])
        assert await chain.arun(5) == 50
        assert await chain.arun(-3) == 3

    @pytest.mark.asyncio
    async def test_arun_parallel_dict(self):
        chain = Chain([
            parallel(
                steps=[
                    lambda v: v.upper(),
                    lambda v: v.lower(),
                ],
                merge="dict",
            ),
        ])
        result = await chain.arun("Hello")
        assert "HELLO" in result.values()
        assert "hello" in result.values()

    @pytest.mark.asyncio
    async def test_arun_parallel_concurrent(self):
        """Parallel.arun uses asyncio.gather for actual concurrency."""
        call_order = []

        async def slow_upper(v):
            call_order.append("upper_start")
            await asyncio.sleep(0.05)
            call_order.append("upper_end")
            return v.upper()

        async def slow_lower(v):
            call_order.append("lower_start")
            await asyncio.sleep(0.05)
            call_order.append("lower_end")
            return v.lower()

        chain = Chain([
            parallel(steps=[slow_upper, slow_lower], merge="list"),
        ])
        result = await chain.arun("Hello")
        assert result == ["HELLO", "hello"]
        # Both should start before either ends (concurrent)
        assert call_order.index("lower_start") < call_order.index("upper_end")

    @pytest.mark.asyncio
    async def test_arun_parallel_first_merge(self):
        async def fail_step(v):
            raise ValueError("fail")

        async def ok_step(v):
            return v.upper()

        chain = Chain([
            parallel(steps=[fail_step, ok_step], merge="first"),
        ])
        result = await chain.arun("hello")
        assert result == "HELLO"

    @pytest.mark.asyncio
    async def test_arun_parallel_first_all_fail(self):
        async def fail_a(v):
            raise ValueError("a")

        async def fail_b(v):
            raise ValueError("b")

        chain = Chain([
            parallel(steps=[fail_a, fail_b], merge="first"),
        ])
        with pytest.raises(RuntimeError, match="All 2 parallel steps failed"):
            await chain.arun("hello")

    @pytest.mark.asyncio
    async def test_arun_with_async_base_transformer(self):
        chain = Chain([AsyncUpperTransformer("async_upper")])
        result = await chain.arun("hello")
        assert result == "HELLO"

    @pytest.mark.asyncio
    async def test_arun_with_skill(self):
        @skill
        def exclaim(text: str) -> str:
            return text + "!"

        chain = Chain([exclaim])
        result = await chain.arun("hello")
        assert result == "hello!"

    @pytest.mark.asyncio
    async def test_arun_nested_chain(self):
        inner = Chain([lambda v: v.upper()])
        outer = Chain([inner, lambda v: v + "!"])
        result = await outer.arun("hello")
        assert result == "HELLO!"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrors:
    """Error propagation and messaging."""

    def test_unknown_string_transformer(self):
        chain = Chain(["nonexistent_transformer_xyz"])
        with pytest.raises(ValueError, match="Unknown transformer"):
            chain.run("hello")

    def test_unknown_dict_transformer(self):
        chain = Chain([{"function": "nonexistent_xyz"}])
        with pytest.raises(ValueError, match="Unknown transformer"):
            chain.run("hello")

    def test_dict_without_function_key(self):
        chain = Chain([{"name": "oops"}])
        with pytest.raises(ValueError, match="must have a 'function' key"):
            chain.run("hello")

    def test_unknown_step_type(self):
        chain = Chain([12345])
        with pytest.raises(TypeError, match="Cannot resolve step"):
            chain.run("hello")

    def test_skill_failure_propagation(self):
        @skill(idempotent=False)
        def bad_skill(text: str) -> str:
            raise ValueError("intentional error")

        chain = Chain([bad_skill])
        with pytest.raises(RuntimeError, match="intentional error"):
            chain.run("hello")

    def test_transformer_failure_propagation(self):
        class FailTransformer(BaseTransformer):
            def validate(self, value):
                return True

            def _transform(self, value, context=None):
                raise ValueError("transformer boom")

        chain = Chain([FailTransformer("fail")])
        # The error comes from TransformResult wrapping
        with pytest.raises(Exception):
            chain.run("hello")


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestIntegration:
    """Complex chains combining multiple composition primitives."""

    def test_branch_then_parallel(self):
        """Branch selects a path, then parallel fans out."""
        chain = Chain([
            "strip",
            branch(
                on_match=lambda v: len(v) > 5,
                true_path=[
                    parallel(
                        steps=[
                            lambda v: v.upper(),
                            lambda v: v.lower(),
                        ],
                        merge="list",
                    ),
                ],
                false_path=[lambda v: [v]],
            ),
        ])
        assert chain.run("  Hello World  ") == ["HELLO WORLD", "hello world"]
        assert chain.run("  Hi  ") == ["Hi"]

    def test_parallel_then_process(self):
        """Parallel produces dict, next step consumes it."""
        chain = Chain([
            parallel(
                steps=[
                    lambda v: v.upper(),
                    lambda v: len(v),
                ],
                merge="dict",
            ),
            lambda d: f"{list(d.values())[0]}({list(d.values())[1]})",
        ])
        result = chain.run("hello")
        assert result == "HELLO(5)"

    def test_multiple_branches_in_sequence(self):
        chain = Chain([
            branch(
                on_match=lambda v: v > 0,
                true_path=[lambda v: v * 2],
                false_path=[lambda v: 0],
            ),
            branch(
                on_match=lambda v: v > 10,
                true_path=[lambda v: "big"],
                false_path=[lambda v: "small"],
            ),
        ])
        assert chain.run(6) == "big"
        assert chain.run(3) == "small"
        assert chain.run(-1) == "small"

    def test_chain_as_step_in_parallel(self):
        """A Chain instance can be a step inside Parallel."""
        upper_chain = Chain([lambda v: v.upper()])
        lower_chain = Chain([lambda v: v.lower()])

        chain = Chain([
            parallel(
                steps=[upper_chain, lower_chain],
                merge="list",
            ),
        ])
        result = chain.run("Hello")
        assert result == ["HELLO", "hello"]

    @pytest.mark.asyncio
    async def test_async_complex_pipeline(self):
        """Full async pipeline with branch + parallel."""
        chain = Chain([
            lambda v: v.strip(),
            branch(
                on_match=lambda v: "@" in v,
                true_path=[
                    parallel(
                        steps=[
                            lambda v: v.split("@")[0],
                            lambda v: v.split("@")[1],
                        ],
                        merge="list",
                    ),
                ],
                false_path=[lambda v: [v, "N/A"]],
            ),
        ])
        result = await chain.arun("  user@example.com  ")
        assert result == ["user", "example.com"]

        result2 = await chain.arun("  no-email  ")
        assert result2 == ["no-email", "N/A"]


# ---------------------------------------------------------------------------
# _step_name helper
# ---------------------------------------------------------------------------

class TestStepName:
    def test_string(self):
        assert _step_name("strip") == "strip"

    def test_dict(self):
        assert _step_name({"function": "truncate", "length": 5}) == "truncate"

    def test_callable(self):
        assert _step_name(double) == "double"

    def test_lambda(self):
        name = _step_name(lambda x: x)
        assert name == "<lambda>"

    def test_skill_instance(self):
        @skill(name="my_skill")
        def fn(x: str) -> str:
            return x

        assert _step_name(fn.__skill__) == "my_skill"

    def test_skill_decorated_fn(self):
        @skill(name="my_skill")
        def fn(x: str) -> str:
            return x

        assert _step_name(fn) == "my_skill"

    def test_base_transformer(self):
        assert _step_name(UpperTransformer("upper")) == "upper"
