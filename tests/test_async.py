"""Tests for Phase 4: Async Support.

Covers:
  - AsyncBaseTransformer / AsyncChainableTransformer / AsyncCompositeTransformer
  - Skill.ainvoke() for async and sync callables
  - Async plugin lifecycle (async_initialize / async_cleanup)
  - PluginRegistry.async_register / async_unregister
  - AsyncTukuyTransformer
  - async_dispatch_openai / async_dispatch_anthropic
"""

import asyncio
import json

import pytest

from tukuy.async_base import (
    AsyncBaseTransformer,
    AsyncChainableTransformer,
    AsyncCompositeTransformer,
)
from tukuy.base import ChainableTransformer
from tukuy.bridges import (
    async_dispatch_anthropic,
    async_dispatch_openai,
)
from tukuy.plugins.base import PluginRegistry, TransformerPlugin
from tukuy.skill import Skill, SkillDescriptor, SkillResult, skill
from tukuy.transformers import AsyncTukuyTransformer
from tukuy.types import TransformResult


# ── Async transformer fixtures ───────────────────────────────────────────


class UpperAsync(AsyncBaseTransformer):
    """Async transformer that upper-cases a string."""

    def validate(self, value):
        return isinstance(value, str)

    async def _transform(self, value, context=None):
        await asyncio.sleep(0)  # simulate async work
        return value.upper()


class StripAsync(AsyncBaseTransformer):
    """Async transformer that strips whitespace."""

    def validate(self, value):
        return isinstance(value, str)

    async def _transform(self, value, context=None):
        return value.strip()


class FailAsync(AsyncBaseTransformer):
    """Async transformer that always raises."""

    def validate(self, value):
        return True

    async def _transform(self, value, context=None):
        raise ValueError("async boom")


# Chainable variants for chain tests

class UpperChainAsync(AsyncChainableTransformer):
    def validate(self, value):
        return isinstance(value, str)

    async def _transform(self, value, context=None):
        await asyncio.sleep(0)
        return value.upper()


class StripChainAsync(AsyncChainableTransformer):
    def validate(self, value):
        return isinstance(value, str)

    async def _transform(self, value, context=None):
        return value.strip()


class FailChainAsync(AsyncChainableTransformer):
    def validate(self, value):
        return True

    async def _transform(self, value, context=None):
        raise ValueError("async boom")


# ── Sync transformer for mixed-chain tests ───────────────────────────────


class StripSync(ChainableTransformer):
    def validate(self, value):
        return isinstance(value, str)

    def _transform(self, value, context=None):
        return value.strip()


# ── TestAsyncBaseTransformer ─────────────────────────────────────────────


class TestAsyncBaseTransformer:
    @pytest.mark.asyncio
    async def test_transform_success(self):
        t = UpperAsync("upper")
        result = await t.transform("hello")
        assert result.success
        assert result.value == "HELLO"

    @pytest.mark.asyncio
    async def test_transform_validation_failure(self):
        t = UpperAsync("upper")
        result = await t.transform(123)
        assert result.failed

    @pytest.mark.asyncio
    async def test_transform_exception(self):
        t = FailAsync("fail")
        result = await t.transform("anything")
        assert result.failed

    def test_str_repr(self):
        t = UpperAsync("upper")
        assert "UpperAsync" in str(t)
        assert "upper" in repr(t)


# ── TestAsyncChainableTransformer ────────────────────────────────────────


class TestAsyncChainableTransformer:
    @pytest.mark.asyncio
    async def test_chain_two_async(self):
        strip = StripChainAsync("strip")
        upper = UpperChainAsync("upper")
        strip.chain(upper)

        result = await strip.transform("  hello  ")
        assert result.success
        assert result.value == "HELLO"

    @pytest.mark.asyncio
    async def test_chain_async_then_sync(self):
        """An async chainable followed by a sync ChainableTransformer."""
        async_strip = StripChainAsync("async_strip")
        sync_strip = StripSync("sync_strip")

        # The sync transformer doesn't modify further since already stripped,
        # but we verify the chain doesn't error.
        async_strip.chain(sync_strip)
        result = await async_strip.transform("  test  ")
        assert result.success
        assert result.value == "test"

    @pytest.mark.asyncio
    async def test_chain_stops_on_failure(self):
        fail = FailChainAsync("fail")
        upper = UpperChainAsync("upper")
        fail.chain(upper)

        result = await fail.transform("anything")
        assert result.failed

    @pytest.mark.asyncio
    async def test_no_next_returns_self_result(self):
        strip = StripChainAsync("strip")
        result = await strip.transform("  hello  ")
        assert result.value == "hello"

    def test_chain_returns_self(self):
        strip = StripChainAsync("strip")
        upper = UpperChainAsync("upper")
        returned = strip.chain(upper)
        assert returned is strip


# ── TestAsyncCompositeTransformer ────────────────────────────────────────


class TestAsyncCompositeTransformer:
    @pytest.mark.asyncio
    async def test_sequential_transforms(self):
        composite = AsyncCompositeTransformer(
            "pipeline",
            transformers=[StripAsync("strip"), UpperAsync("upper")],
        )
        result = await composite.transform("  hello  ")
        assert result.success
        assert result.value == "HELLO"

    @pytest.mark.asyncio
    async def test_mixed_sync_async(self):
        composite = AsyncCompositeTransformer(
            "mixed",
            transformers=[StripSync("sync_strip"), UpperAsync("upper")],
        )
        result = await composite.transform("  world  ")
        assert result.success
        assert result.value == "WORLD"

    @pytest.mark.asyncio
    async def test_failure_stops_chain(self):
        composite = AsyncCompositeTransformer(
            "fail_pipe",
            transformers=[FailAsync("fail"), UpperAsync("upper")],
        )
        result = await composite.transform("anything")
        assert result.failed


# ── TestSkillAinvoke ─────────────────────────────────────────────────────


class TestSkillAinvoke:
    def _make(self, fn, *, idempotent=False, is_async=False):
        desc = SkillDescriptor(name="test", description="test", idempotent=idempotent, is_async=is_async)
        return Skill(descriptor=desc, fn=fn)

    @pytest.mark.asyncio
    async def test_async_fn(self):
        async def double(x: int) -> int:
            return x * 2

        s = self._make(double, is_async=True)
        result = await s.ainvoke(5)
        assert result.success
        assert result.value == 10
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_sync_fn_via_ainvoke(self):
        def add_one(x: int) -> int:
            return x + 1

        s = self._make(add_one)
        result = await s.ainvoke(5)
        assert result.success
        assert result.value == 6

    @pytest.mark.asyncio
    async def test_async_error(self):
        async def boom(x):
            raise RuntimeError("async error")

        s = self._make(boom, is_async=True)
        result = await s.ainvoke(1)
        assert result.failed
        assert "async error" in result.error

    @pytest.mark.asyncio
    async def test_async_error_retryable_when_idempotent(self):
        async def boom(x):
            raise RuntimeError("err")

        s = self._make(boom, is_async=True, idempotent=True)
        result = await s.ainvoke(1)
        assert result.retryable is True

    @pytest.mark.asyncio
    async def test_async_transform_result_lifted(self):
        async def fn(x):
            return TransformResult(value=x * 3)

        s = self._make(fn, is_async=True)
        result = await s.ainvoke(4)
        assert result.success
        assert result.value == 12

    @pytest.mark.asyncio
    async def test_async_transform_result_error(self):
        async def fn(x):
            return TransformResult(error=Exception("tr fail"))

        s = self._make(fn, is_async=True)
        result = await s.ainvoke(1)
        assert result.failed
        assert "tr fail" in result.error


# ── TestSkillDecoratorAsync ──────────────────────────────────────────────


class TestSkillDecoratorAsync:
    @pytest.mark.asyncio
    async def test_decorated_async_fn_ainvoke(self):
        @skill
        async def async_add(x: int) -> int:
            return x + 10

        assert async_add.__skill__.descriptor.is_async is True
        result = await async_add.__skill__.ainvoke(5)
        assert result.success
        assert result.value == 15

    @pytest.mark.asyncio
    async def test_decorated_async_fn_still_returns_coroutine(self):
        @skill
        async def async_fn(x: int) -> int:
            return x

        coro = async_fn(1)
        assert asyncio.iscoroutine(coro)
        assert await coro == 1


# ── TestAsyncPluginLifecycle ─────────────────────────────────────────────


class TestAsyncPluginLifecycle:
    @pytest.mark.asyncio
    async def test_default_async_initialize_delegates_to_sync(self):
        calls = []

        class TrackingPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {}

            def initialize(self):
                calls.append("sync_init")

        plugin = TrackingPlugin("tracker")
        await plugin.async_initialize()
        assert calls == ["sync_init"]

    @pytest.mark.asyncio
    async def test_default_async_cleanup_delegates_to_sync(self):
        calls = []

        class TrackingPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {}

            def cleanup(self):
                calls.append("sync_cleanup")

        plugin = TrackingPlugin("tracker")
        await plugin.async_cleanup()
        assert calls == ["sync_cleanup"]

    @pytest.mark.asyncio
    async def test_custom_async_initialize(self):
        calls = []

        class AsyncPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {}

            async def async_initialize(self):
                await asyncio.sleep(0)
                calls.append("async_init")

        plugin = AsyncPlugin("async_plugin")
        await plugin.async_initialize()
        assert calls == ["async_init"]

    @pytest.mark.asyncio
    async def test_custom_async_cleanup(self):
        calls = []

        class AsyncPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {}

            async def async_cleanup(self):
                await asyncio.sleep(0)
                calls.append("async_cleanup")

        plugin = AsyncPlugin("async_plugin")
        await plugin.async_cleanup()
        assert calls == ["async_cleanup"]


# ── TestPluginRegistryAsync ──────────────────────────────────────────────


class TestPluginRegistryAsync:
    @pytest.mark.asyncio
    async def test_async_register(self):
        calls = []

        class TestPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {"test_t": lambda params: None}

            async def async_initialize(self):
                calls.append("async_init")

        registry = PluginRegistry()
        plugin = TestPlugin("test")
        await registry.async_register(plugin)

        assert "test" in registry.plugins
        assert "test_t" in registry.transformers
        assert calls == ["async_init"]

    @pytest.mark.asyncio
    async def test_async_register_duplicate_raises(self):
        class TestPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {}

        registry = PluginRegistry()
        plugin = TestPlugin("dup")
        await registry.async_register(plugin)

        with pytest.raises(ValueError, match="already registered"):
            await registry.async_register(TestPlugin("dup"))

    @pytest.mark.asyncio
    async def test_async_unregister(self):
        calls = []

        class TestPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {"test_t": lambda params: None}

            async def async_cleanup(self):
                calls.append("async_cleanup")

        registry = PluginRegistry()
        plugin = TestPlugin("test")
        await registry.async_register(plugin)
        await registry.async_unregister("test")

        assert "test" not in registry.plugins
        assert "test_t" not in registry.transformers
        assert "async_cleanup" in calls

    @pytest.mark.asyncio
    async def test_async_unregister_nonexistent_noop(self):
        registry = PluginRegistry()
        await registry.async_unregister("nonexistent")  # should not raise


# ── TestAsyncTukuyTransformer ────────────────────────────────────────────


class TestAsyncTukuyTransformer:
    @pytest.mark.asyncio
    async def test_basic_sync_transform_chain(self):
        t = AsyncTukuyTransformer()
        result = await t.transform("  Hello World  ", ["strip", "lowercase"])
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_dict_transform_spec(self):
        t = AsyncTukuyTransformer()
        result = await t.transform(
            "Hello World",
            [{"function": "replace", "from": "World", "to": "Tukuy"}],
        )
        assert result == "Hello Tukuy"

    @pytest.mark.asyncio
    async def test_unknown_transformer_raises(self):
        t = AsyncTukuyTransformer()
        with pytest.raises(Exception, match="Unknown transformer"):
            await t.transform("x", ["nonexistent_transform"])

    @pytest.mark.asyncio
    async def test_none_value_breaks_chain(self):
        t = AsyncTukuyTransformer()
        result = await t.transform(None, ["strip", "lowercase"])
        assert result is None

    @pytest.mark.asyncio
    async def test_register_and_unregister_plugin(self):
        class DummyPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {}

        t = AsyncTukuyTransformer()
        plugin = DummyPlugin("dummy")
        t.register_plugin(plugin)
        assert "dummy" in t.registry.plugins

        t.unregister_plugin("dummy")
        assert "dummy" not in t.registry.plugins

    @pytest.mark.asyncio
    async def test_async_register_plugin(self):
        calls = []

        class AsyncPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {}

            async def async_initialize(self):
                calls.append("init")

        t = AsyncTukuyTransformer()
        await t.async_register_plugin(AsyncPlugin("async_p"))
        assert "async_p" in t.registry.plugins
        assert calls == ["init"]

    @pytest.mark.asyncio
    async def test_async_unregister_plugin(self):
        calls = []

        class AsyncPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {}

            async def async_cleanup(self):
                calls.append("cleanup")

        t = AsyncTukuyTransformer()
        await t.async_register_plugin(AsyncPlugin("async_p"))
        await t.async_unregister_plugin("async_p")
        assert "async_p" not in t.registry.plugins
        assert calls == ["cleanup"]


# ── TestAsyncDispatchOpenai ──────────────────────────────────────────────


class TestAsyncDispatchOpenai:
    def _make_tool_call(self, name, arguments, call_id="call_async"):
        return {
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": arguments},
        }

    @pytest.mark.asyncio
    async def test_async_skill_dispatch(self):
        @skill
        async def async_greet(name: str) -> str:
            return f"Hello, {name}!"

        tool_call = self._make_tool_call("async_greet", json.dumps({"name": "Alice"}))
        result = await async_dispatch_openai(tool_call, {"async_greet": async_greet})
        assert result["role"] == "tool"
        assert json.loads(result["content"]) == "Hello, Alice!"

    @pytest.mark.asyncio
    async def test_sync_skill_via_async_dispatch(self):
        @skill
        def sync_greet(name: str) -> str:
            return f"Hi, {name}!"

        tool_call = self._make_tool_call("sync_greet", json.dumps({"name": "Bob"}))
        result = await async_dispatch_openai(tool_call, {"sync_greet": sync_greet})
        assert json.loads(result["content"]) == "Hi, Bob!"

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        tool_call = self._make_tool_call("nope", "{}")
        result = await async_dispatch_openai(tool_call, {})
        assert "Unknown tool" in result["content"]

    @pytest.mark.asyncio
    async def test_invalid_json(self):
        @skill
        def fn(x: str) -> str:
            return x

        tool_call = self._make_tool_call("fn", "not-json{{")
        result = await async_dispatch_openai(tool_call, {"fn": fn})
        assert "Invalid JSON" in result["content"]

    @pytest.mark.asyncio
    async def test_async_error(self):
        @skill(idempotent=True)
        async def fail_async(x: str) -> str:
            raise ValueError("async boom")

        tool_call = self._make_tool_call("fail_async", json.dumps({"x": "test"}))
        result = await async_dispatch_openai(tool_call, {"fail_async": fail_async})
        assert "async boom" in result["content"]


# ── TestAsyncDispatchAnthropic ───────────────────────────────────────────


class TestAsyncDispatchAnthropic:
    def _make_tool_use(self, name, input_data, use_id="toolu_async"):
        return {"type": "tool_use", "id": use_id, "name": name, "input": input_data}

    @pytest.mark.asyncio
    async def test_async_skill_dispatch(self):
        @skill
        async def async_greet(name: str) -> str:
            return f"Hello, {name}!"

        tool_use = self._make_tool_use("async_greet", {"name": "Alice"})
        result = await async_dispatch_anthropic(tool_use, {"async_greet": async_greet})
        assert result["type"] == "tool_result"
        assert json.loads(result["content"]) == "Hello, Alice!"

    @pytest.mark.asyncio
    async def test_sync_skill_via_async_dispatch(self):
        @skill
        def sync_greet(name: str) -> str:
            return f"Hi, {name}!"

        tool_use = self._make_tool_use("sync_greet", {"name": "Bob"})
        result = await async_dispatch_anthropic(tool_use, {"sync_greet": sync_greet})
        assert json.loads(result["content"]) == "Hi, Bob!"

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        tool_use = self._make_tool_use("nope", {})
        result = await async_dispatch_anthropic(tool_use, {})
        assert "Unknown tool" in result["content"]
        assert result["is_error"] is True

    @pytest.mark.asyncio
    async def test_async_error_has_is_error(self):
        @skill
        async def fail_async(x: str) -> str:
            raise ValueError("async boom")

        tool_use = self._make_tool_use("fail_async", {"x": "test"})
        result = await async_dispatch_anthropic(tool_use, {"fail_async": fail_async})
        assert result["is_error"] is True
        assert "async boom" in result["content"]


# ── TestAsyncRoundTrip ───────────────────────────────────────────────────


class TestAsyncRoundTrip:
    @pytest.mark.asyncio
    async def test_openai_async_round_trip(self):
        from tukuy.bridges import to_openai_tool

        @skill
        async def async_double(x: int) -> int:
            return x * 2

        tool_def = to_openai_tool(async_double)
        assert tool_def["function"]["name"] == "async_double"

        tool_call = {
            "id": "call_rt_async",
            "type": "function",
            "function": {
                "name": "async_double",
                "arguments": json.dumps({"x": 21}),
            },
        }
        result = await async_dispatch_openai(tool_call, {"async_double": async_double})
        assert result["role"] == "tool"
        assert json.loads(result["content"]) == 42

    @pytest.mark.asyncio
    async def test_anthropic_async_round_trip(self):
        from tukuy.bridges import to_anthropic_tool

        @skill
        async def async_double(x: int) -> int:
            return x * 2

        tool_def = to_anthropic_tool(async_double)
        assert tool_def["name"] == "async_double"

        tool_use = {
            "type": "tool_use",
            "id": "toolu_rt_async",
            "name": "async_double",
            "input": {"x": 21},
        }
        result = await async_dispatch_anthropic(tool_use, {"async_double": async_double})
        assert result["type"] == "tool_result"
        assert json.loads(result["content"]) == 42
        assert "is_error" not in result
