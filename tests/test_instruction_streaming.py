"""Tests for Instruction streaming support (astream + on_delta)."""

import asyncio
import json
import pytest

from tukuy.instruction import (
    Instruction,
    InstructionChunk,
    InstructionDescriptor,
    instruction,
)
from tukuy.skill import SkillResult
from tukuy.context import SkillContext


# ---------------------------------------------------------------------------
# Mock backends
# ---------------------------------------------------------------------------


class MockStreamingBackend:
    """Backend that supports both complete() and stream()."""

    def __init__(self, chunks=None, response_text="full response"):
        self.chunks = chunks or [
            {"type": "delta", "text": "Hello"},
            {"type": "delta", "text": " World"},
            {"type": "done", "text": "Hello World", "meta": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "cost": 0.001,
                "model": "mock-streaming",
            }},
        ]
        self.response_text = response_text
        self.last_prompt = None
        self.complete_called = False
        self.stream_called = False

    async def complete(self, prompt, **kwargs):
        self.complete_called = True
        self.last_prompt = prompt
        return {
            "text": self.response_text,
            "meta": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "cost": 0.001,
                "model": "mock",
            },
        }

    async def stream(self, prompt, **kwargs):
        self.stream_called = True
        self.last_prompt = prompt
        for chunk in self.chunks:
            yield chunk


class MockNonStreamingBackend:
    """Backend that only supports complete() — no stream method."""

    def __init__(self, response_text="non-streaming response"):
        self.response_text = response_text
        self.complete_called = False

    async def complete(self, prompt, **kwargs):
        self.complete_called = True
        return {
            "text": self.response_text,
            "meta": {
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "cost": 0.0005,
                "model": "mock-non-streaming",
            },
        }


class MockErrorStreamingBackend:
    """Backend whose stream() raises an exception."""

    async def complete(self, prompt, **kwargs):
        return {
            "text": "fallback",
            "meta": {"prompt_tokens": 0, "completion_tokens": 0, "cost": 0, "model": "mock"},
        }

    async def stream(self, prompt, **kwargs):
        yield {"type": "delta", "text": "partial"}
        raise RuntimeError("stream exploded")


def _make_context(backend):
    return SkillContext(config={"llm_backend": backend})


# ---------------------------------------------------------------------------
# InstructionChunk dataclass
# ---------------------------------------------------------------------------


class TestInstructionChunk:
    def test_delta_chunk(self):
        chunk = InstructionChunk(type="delta", text="hello")
        assert chunk.type == "delta"
        assert chunk.text == "hello"
        assert chunk.result is None

    def test_done_chunk(self):
        sr = SkillResult(value="done", success=True)
        chunk = InstructionChunk(type="done", text="full text", result=sr)
        assert chunk.type == "done"
        assert chunk.text == "full text"
        assert chunk.result is sr

    def test_import_from_top_level(self):
        from tukuy import InstructionChunk as IC
        assert IC is InstructionChunk


# ---------------------------------------------------------------------------
# astream() tests
# ---------------------------------------------------------------------------


class TestAstream:
    @pytest.mark.asyncio
    async def test_yields_deltas_then_done(self):
        backend = MockStreamingBackend()
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        chunks = []
        async for chunk in my_instr.__instruction__.astream(text="hello", context=ctx):
            chunks.append(chunk)

        assert backend.stream_called is True
        assert backend.complete_called is False

        # Should have delta chunks + one done chunk
        deltas = [c for c in chunks if c.type == "delta"]
        dones = [c for c in chunks if c.type == "done"]
        assert len(deltas) == 2
        assert deltas[0].text == "Hello"
        assert deltas[1].text == " World"
        assert len(dones) == 1
        assert dones[0].result is not None
        assert dones[0].result.success is True
        assert dones[0].result.value == "Hello World"
        assert dones[0].text == "Hello World"

    @pytest.mark.asyncio
    async def test_fallback_to_complete_when_no_stream(self):
        backend = MockNonStreamingBackend("fallback result")
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        chunks = []
        async for chunk in my_instr.__instruction__.astream(text="hello", context=ctx):
            chunks.append(chunk)

        assert backend.complete_called is True
        assert len(chunks) == 1
        assert chunks[0].type == "done"
        assert chunks[0].result.success is True
        assert chunks[0].result.value == "fallback result"
        assert chunks[0].text == "fallback result"

    @pytest.mark.asyncio
    async def test_done_chunk_has_valid_skill_result_metadata(self):
        backend = MockStreamingBackend()
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        async for chunk in my_instr.__instruction__.astream(text="hello", context=ctx):
            if chunk.type == "done":
                assert chunk.result.metadata.get("model") == "mock-streaming"
                assert chunk.result.metadata.get("prompt_tokens") == 10
                assert chunk.result.metadata.get("completion_tokens") == 20
                assert chunk.result.duration_ms is not None
                assert chunk.result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_post_processor_runs_on_final_text(self):
        backend = MockStreamingBackend(chunks=[
            {"type": "delta", "text": '{"key":'},
            {"type": "delta", "text": ' "value"}'},
            {"type": "done", "text": '{"key": "value"}', "meta": {
                "prompt_tokens": 5, "completion_tokens": 10, "cost": 0.001, "model": "mock",
            }},
        ])
        ctx = _make_context(backend)

        @instruction(prompt="Extract: {text}", output_format="json")
        def extract(result: dict) -> dict:
            result["processed"] = True
            return result

        chunks = []
        async for chunk in extract.__instruction__.astream(text="data", context=ctx):
            chunks.append(chunk)

        done = [c for c in chunks if c.type == "done"][0]
        assert done.result.success is True
        assert done.result.value == {"key": "value", "processed": True}

    @pytest.mark.asyncio
    async def test_json_output_format_parses_full_response(self):
        backend = MockStreamingBackend(chunks=[
            {"type": "delta", "text": '{"count": 42}'},
            {"type": "done", "text": '{"count": 42}', "meta": {
                "prompt_tokens": 5, "completion_tokens": 5, "cost": 0.0, "model": "mock",
            }},
        ])
        ctx = _make_context(backend)

        @instruction(prompt="Count: {text}", output_format="json")
        def count(text: str):
            pass

        chunks = []
        async for chunk in count.__instruction__.astream(text="items", context=ctx):
            chunks.append(chunk)

        done = [c for c in chunks if c.type == "done"][0]
        assert done.result.success is True
        assert done.result.value == {"count": 42}

    @pytest.mark.asyncio
    async def test_error_handling_yields_done_with_error(self):
        backend = MockErrorStreamingBackend()
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        chunks = []
        async for chunk in my_instr.__instruction__.astream(text="hello", context=ctx):
            chunks.append(chunk)

        # May have a delta before the error, then a done with error
        done = [c for c in chunks if c.type == "done"]
        assert len(done) == 1
        assert done[0].result.success is False
        assert "stream exploded" in done[0].result.error

    @pytest.mark.asyncio
    async def test_missing_context_yields_error_done(self):
        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        chunks = []
        async for chunk in my_instr.__instruction__.astream(text="hello"):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].type == "done"
        assert chunks[0].result.success is False
        assert "SkillContext" in chunks[0].result.error

    @pytest.mark.asyncio
    async def test_missing_llm_backend_yields_error_done(self):
        ctx = SkillContext(config={})

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        chunks = []
        async for chunk in my_instr.__instruction__.astream(text="hello", context=ctx):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].type == "done"
        assert chunks[0].result.success is False
        assert "llm_backend" in chunks[0].result.error

    @pytest.mark.asyncio
    async def test_missing_prompt_variable_yields_error_done(self):
        backend = MockStreamingBackend()
        ctx = _make_context(backend)

        @instruction(prompt="Do {text} with {mode}")
        def my_instr(text: str):
            pass

        chunks = []
        async for chunk in my_instr.__instruction__.astream(text="hello", context=ctx):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].type == "done"
        assert chunks[0].result.success is False
        assert "Missing prompt variable" in chunks[0].result.error

    @pytest.mark.asyncio
    async def test_list_output_format(self):
        backend = MockStreamingBackend(chunks=[
            {"type": "delta", "text": "- Apple\n- Banana"},
            {"type": "done", "text": "- Apple\n- Banana\n- Cherry", "meta": {
                "prompt_tokens": 5, "completion_tokens": 10, "cost": 0.0, "model": "mock",
            }},
        ])
        ctx = _make_context(backend)

        @instruction(prompt="List: {topic}", output_format="list")
        def list_items(topic: str):
            pass

        chunks = []
        async for chunk in list_items.__instruction__.astream(topic="fruits", context=ctx):
            chunks.append(chunk)

        done = [c for c in chunks if c.type == "done"][0]
        assert done.result.success is True
        assert done.result.value == ["Apple", "Banana", "Cherry"]


# ---------------------------------------------------------------------------
# ainvoke() with on_delta callback
# ---------------------------------------------------------------------------


class TestAinvokeOnDelta:
    @pytest.mark.asyncio
    async def test_on_delta_fires_for_each_chunk(self):
        backend = MockStreamingBackend()
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        deltas = []
        result = await my_instr.__instruction__.ainvoke(
            text="hello",
            context=ctx,
            on_delta=lambda t: deltas.append(t),
        )

        assert result.success is True
        assert result.value == "Hello World"
        assert deltas == ["Hello", " World"]

    @pytest.mark.asyncio
    async def test_on_delta_async_callback(self):
        backend = MockStreamingBackend()
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        deltas = []

        async def async_cb(text):
            deltas.append(text)

        result = await my_instr.__instruction__.ainvoke(
            text="hello",
            context=ctx,
            on_delta=async_cb,
        )

        assert result.success is True
        assert deltas == ["Hello", " World"]

    @pytest.mark.asyncio
    async def test_on_delta_with_non_streaming_backend_falls_back(self):
        backend = MockNonStreamingBackend("plain result")
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        deltas = []
        result = await my_instr.__instruction__.ainvoke(
            text="hello",
            context=ctx,
            on_delta=lambda t: deltas.append(t),
        )

        # Should fall back to complete(), no deltas fired
        assert result.success is True
        assert result.value == "plain result"
        assert deltas == []
        assert backend.complete_called is True

    @pytest.mark.asyncio
    async def test_ainvoke_without_on_delta_still_works(self):
        backend = MockStreamingBackend()
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        result = await my_instr.__instruction__.ainvoke(text="hello", context=ctx)
        assert result.success is True
        # Without on_delta, uses the complete() path
        assert backend.complete_called is True
        assert backend.stream_called is False

    @pytest.mark.asyncio
    async def test_on_delta_none_uses_complete_path(self):
        backend = MockStreamingBackend()
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        result = await my_instr.__instruction__.ainvoke(
            text="hello",
            context=ctx,
            on_delta=None,
        )
        assert result.success is True
        assert backend.complete_called is True
        assert backend.stream_called is False
