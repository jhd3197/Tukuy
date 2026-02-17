"""Tests for the @instruction decorator and Instruction system."""

import asyncio
import json
import pytest

from tukuy.instruction import (
    Instruction,
    InstructionDescriptor,
    LLMBackend,
    instruction,
    _extract_template_variables,
)
from tukuy.skill import SkillDescriptor, SkillResult
from tukuy.context import SkillContext
from tukuy.bridges import (
    to_openai_tool,
    to_anthropic_tool,
    dispatch_openai,
    dispatch_anthropic,
    async_dispatch_openai,
    async_dispatch_anthropic,
)
from tukuy.plugins.base import PluginRegistry, TransformerPlugin, PluginSource


# ---------------------------------------------------------------------------
# Mock LLM Backend
# ---------------------------------------------------------------------------


class MockLLMBackend:
    """Mock implementation of the LLMBackend protocol for testing."""

    def __init__(self, response_text="mock response"):
        self.response_text = response_text
        self.last_prompt = None
        self.last_system = None
        self.last_temperature = None
        self.last_max_tokens = None
        self.last_json_schema = None

    async def complete(
        self,
        prompt,
        *,
        system=None,
        temperature=None,
        max_tokens=None,
        json_schema=None,
    ):
        self.last_prompt = prompt
        self.last_system = system
        self.last_temperature = temperature
        self.last_max_tokens = max_tokens
        self.last_json_schema = json_schema
        return {
            "text": self.response_text,
            "meta": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "cost": 0.001,
                "model": "mock",
            },
        }


def _make_context(backend=None):
    """Create a SkillContext with the given LLM backend."""
    if backend is None:
        backend = MockLLMBackend()
    return SkillContext(config={"llm_backend": backend})


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestLLMBackendProtocol:
    def test_mock_conforms_to_protocol(self):
        backend = MockLLMBackend()
        assert isinstance(backend, LLMBackend)


# ---------------------------------------------------------------------------
# InstructionDescriptor
# ---------------------------------------------------------------------------


class TestInstructionDescriptor:
    def test_extends_skill_descriptor(self):
        assert issubclass(InstructionDescriptor, SkillDescriptor)

    def test_basic_creation(self):
        desc = InstructionDescriptor(
            name="test_instr",
            description="A test instruction",
            prompt="Do something with {text}",
        )
        assert desc.name == "test_instr"
        assert desc.prompt == "Do something with {text}"
        assert desc.output_format == "text"
        assert desc.requires_network is True
        assert desc.is_async is True

    def test_forces_requires_network(self):
        desc = InstructionDescriptor(
            name="test",
            description="test",
            prompt="test",
            requires_network=False,
        )
        # __post_init__ should force requires_network=True
        assert desc.requires_network is True

    def test_forces_is_async(self):
        desc = InstructionDescriptor(
            name="test",
            description="test",
            prompt="test",
            is_async=False,
        )
        # __post_init__ should force is_async=True
        assert desc.is_async is True

    def test_all_instruction_fields(self):
        desc = InstructionDescriptor(
            name="full",
            description="Full instruction",
            prompt="Analyze: {text}",
            system_prompt="You are a helpful assistant",
            output_format="json",
            model_hint="openai/gpt-4o",
            temperature=0.7,
            max_tokens=500,
            few_shot_examples=[{"input": "hello", "output": "positive"}],
        )
        assert desc.system_prompt == "You are a helpful assistant"
        assert desc.output_format == "json"
        assert desc.model_hint == "openai/gpt-4o"
        assert desc.temperature == 0.7
        assert desc.max_tokens == 500
        assert len(desc.few_shot_examples) == 1

    def test_to_dict(self):
        desc = InstructionDescriptor(
            name="test",
            description="Test instruction",
            prompt="Do: {text}",
        )
        d = desc.to_dict()
        assert d["name"] == "test"
        assert d["requires_network"] is True
        assert d["is_async"] is True


# ---------------------------------------------------------------------------
# Template variable extraction
# ---------------------------------------------------------------------------


class TestTemplateVariables:
    def test_single_variable(self):
        assert _extract_template_variables("Hello {name}") == ["name"]

    def test_multiple_variables(self):
        result = _extract_template_variables("Hello {name}, you are {age}")
        assert result == ["name", "age"]

    def test_no_variables(self):
        assert _extract_template_variables("Hello world") == []

    def test_duplicate_variables(self):
        result = _extract_template_variables("{name} is {name}")
        assert result == ["name"]


# ---------------------------------------------------------------------------
# @instruction decorator
# ---------------------------------------------------------------------------


class TestInstructionDecorator:
    def test_bare_decorator(self):
        @instruction
        def my_instr(text: str):
            pass

        assert hasattr(my_instr, "__instruction__")
        assert hasattr(my_instr, "__skill__")
        assert isinstance(my_instr.__instruction__, Instruction)
        assert my_instr.__instruction__ is my_instr.__skill__

    def test_parenthesized_decorator(self):
        @instruction()
        def my_instr(text: str):
            pass

        assert hasattr(my_instr, "__instruction__")
        assert isinstance(my_instr.__instruction__, Instruction)

    def test_parameterized_decorator(self):
        @instruction(
            name="custom_name",
            prompt="Summarize: {text}",
            output_format="text",
            description="A custom instruction",
        )
        def summarize(text: str):
            pass

        instr = summarize.__instruction__
        assert instr.descriptor.name == "custom_name"
        assert instr.descriptor.prompt == "Summarize: {text}"
        assert instr.descriptor.description == "A custom instruction"

    def test_auto_infer_name(self):
        @instruction(prompt="Do: {text}")
        def my_tool(text: str):
            pass

        assert my_tool.__instruction__.descriptor.name == "my_tool"

    def test_input_schema_from_template(self):
        @instruction(prompt="Analyze {text} with {mode}")
        def analyze(text: str, mode: str):
            pass

        schema = analyze.__instruction__.descriptor.input_schema
        assert schema is not None
        assert "text" in schema["properties"]
        assert "mode" in schema["properties"]
        assert schema["required"] == ["text", "mode"]

    def test_passthrough_body(self):
        @instruction(prompt="Summarize: {text}")
        def summarize(text: str):
            pass

        # Function body is `pass` so fn should be None (no post-processor)
        assert summarize.__instruction__.fn is None

    def test_post_processor_body(self):
        @instruction(prompt="Analyze: {text}", output_format="json")
        def analyze(result: dict) -> dict:
            result["processed"] = True
            return result

        # Function body is not `pass` so fn should be set
        assert analyze.__instruction__.fn is not None

    def test_descriptor_is_instruction_descriptor(self):
        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        assert isinstance(my_instr.__instruction__.descriptor, InstructionDescriptor)
        assert isinstance(my_instr.__instruction__.descriptor, SkillDescriptor)


# ---------------------------------------------------------------------------
# Instruction.invoke() — sync raises error
# ---------------------------------------------------------------------------


class TestInstructionInvoke:
    def test_sync_invoke_raises(self):
        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        with pytest.raises(RuntimeError, match="ainvoke"):
            my_instr.__instruction__.invoke(text="hello")


# ---------------------------------------------------------------------------
# Instruction.ainvoke() — async execution
# ---------------------------------------------------------------------------


class TestInstructionAinvoke:
    @pytest.mark.asyncio
    async def test_basic_text_output(self):
        backend = MockLLMBackend("This is a summary.")
        ctx = _make_context(backend)

        @instruction(prompt="Summarize: {text}", output_format="text")
        def summarize(text: str):
            pass

        result = await summarize.__instruction__.ainvoke(text="Hello world", context=ctx)
        assert result.success is True
        assert result.value == "This is a summary."
        assert backend.last_prompt == "Summarize: Hello world"

    @pytest.mark.asyncio
    async def test_json_output(self):
        backend = MockLLMBackend('{"sentiment": "positive", "score": 0.9}')
        ctx = _make_context(backend)

        @instruction(prompt="Analyze: {text}", output_format="json")
        def analyze(text: str):
            pass

        result = await analyze.__instruction__.ainvoke(text="Great day!", context=ctx)
        assert result.success is True
        assert result.value == {"sentiment": "positive", "score": 0.9}

    @pytest.mark.asyncio
    async def test_json_output_appends_instruction(self):
        backend = MockLLMBackend('{"key": "value"}')
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}", output_format="json")
        def do_json(text: str):
            pass

        await do_json.__instruction__.ainvoke(text="test", context=ctx)
        assert "Respond with valid JSON only." in backend.last_prompt

    @pytest.mark.asyncio
    async def test_list_output(self):
        backend = MockLLMBackend("- Apple\n- Banana\n- Cherry\n")
        ctx = _make_context(backend)

        @instruction(prompt="List fruits about: {topic}", output_format="list")
        def list_fruits(topic: str):
            pass

        result = await list_fruits.__instruction__.ainvoke(topic="tropical", context=ctx)
        assert result.success is True
        assert result.value == ["Apple", "Banana", "Cherry"]

    @pytest.mark.asyncio
    async def test_list_output_appends_instruction(self):
        backend = MockLLMBackend("- item")
        ctx = _make_context(backend)

        @instruction(prompt="List: {text}", output_format="list")
        def do_list(text: str):
            pass

        await do_list.__instruction__.ainvoke(text="test", context=ctx)
        assert "bulleted list" in backend.last_prompt

    @pytest.mark.asyncio
    async def test_markdown_output(self):
        backend = MockLLMBackend("# Title\n\nSome **bold** text.")
        ctx = _make_context(backend)

        @instruction(prompt="Format: {text}", output_format="markdown")
        def format_md(text: str):
            pass

        result = await format_md.__instruction__.ainvoke(text="test", context=ctx)
        assert result.success is True
        assert result.value == "# Title\n\nSome **bold** text."

    @pytest.mark.asyncio
    async def test_post_processor(self):
        backend = MockLLMBackend('{"sentiment": "positive"}')
        ctx = _make_context(backend)

        @instruction(prompt="Analyze: {text}", output_format="json")
        def analyze(result: dict) -> dict:
            result["processed"] = True
            return result

        res = await analyze.__instruction__.ainvoke(text="Good day!", context=ctx)
        assert res.success is True
        assert res.value == {"sentiment": "positive", "processed": True}

    @pytest.mark.asyncio
    async def test_system_prompt(self):
        backend = MockLLMBackend("response")
        ctx = _make_context(backend)

        @instruction(
            prompt="Do: {text}",
            system_prompt="You are a helpful assistant.",
        )
        def my_instr(text: str):
            pass

        await my_instr.__instruction__.ainvoke(text="hello", context=ctx)
        assert backend.last_system == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_temperature_and_max_tokens(self):
        backend = MockLLMBackend("response")
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}", temperature=0.5, max_tokens=100)
        def my_instr(text: str):
            pass

        await my_instr.__instruction__.ainvoke(text="hello", context=ctx)
        assert backend.last_temperature == 0.5
        assert backend.last_max_tokens == 100

    @pytest.mark.asyncio
    async def test_few_shot_examples(self):
        backend = MockLLMBackend("positive")
        ctx = _make_context(backend)

        @instruction(
            prompt="Classify: {text}",
            few_shot_examples=[
                {"input": "I love it", "output": "positive"},
                {"input": "I hate it", "output": "negative"},
            ],
        )
        def classify(text: str):
            pass

        await classify.__instruction__.ainvoke(text="Amazing!", context=ctx)
        assert "Input: I love it" in backend.last_prompt
        assert "Output: positive" in backend.last_prompt
        assert "Input: I hate it" in backend.last_prompt
        assert "Output: negative" in backend.last_prompt
        assert "Classify: Amazing!" in backend.last_prompt

    @pytest.mark.asyncio
    async def test_missing_context(self):
        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        result = await my_instr.__instruction__.ainvoke(text="hello")
        assert result.success is False
        assert "SkillContext" in result.error

    @pytest.mark.asyncio
    async def test_missing_llm_backend(self):
        ctx = SkillContext(config={})

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        result = await my_instr.__instruction__.ainvoke(text="hello", context=ctx)
        assert result.success is False
        assert "llm_backend" in result.error

    @pytest.mark.asyncio
    async def test_missing_prompt_variable(self):
        backend = MockLLMBackend("response")
        ctx = _make_context(backend)

        @instruction(prompt="Do {text} with {mode}")
        def my_instr(text: str):
            pass

        result = await my_instr.__instruction__.ainvoke(text="hello", context=ctx)
        assert result.success is False
        assert "Missing prompt variable" in result.error

    @pytest.mark.asyncio
    async def test_invalid_json_response(self):
        backend = MockLLMBackend("not valid json {{{")
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}", output_format="json")
        def my_instr(text: str):
            pass

        result = await my_instr.__instruction__.ainvoke(text="hello", context=ctx)
        assert result.success is False
        assert "Failed to parse LLM response as JSON" in result.error

    @pytest.mark.asyncio
    async def test_metadata_includes_llm_meta(self):
        backend = MockLLMBackend("response")
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        result = await my_instr.__instruction__.ainvoke(text="hello", context=ctx)
        assert result.success is True
        assert result.metadata.get("model") == "mock"
        assert result.metadata.get("prompt_tokens") == 10
        assert result.metadata.get("completion_tokens") == 20
        assert result.metadata.get("cost") == 0.001

    @pytest.mark.asyncio
    async def test_duration_ms_tracked(self):
        backend = MockLLMBackend("response")
        ctx = _make_context(backend)

        @instruction(prompt="Do: {text}")
        def my_instr(text: str):
            pass

        result = await my_instr.__instruction__.ainvoke(text="hello", context=ctx)
        assert result.duration_ms is not None
        assert result.duration_ms >= 0


# ---------------------------------------------------------------------------
# Bridge functions with Instructions
# ---------------------------------------------------------------------------


class TestBridges:
    def test_to_openai_tool(self):
        @instruction(
            name="summarize",
            description="Summarize text",
            prompt="Summarize: {text}",
        )
        def summarize(text: str):
            pass

        tool = to_openai_tool(summarize)
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "summarize"
        assert "text" in tool["function"]["parameters"]["properties"]

    def test_to_anthropic_tool(self):
        @instruction(
            name="summarize",
            description="Summarize text",
            prompt="Summarize: {text}",
        )
        def summarize(text: str):
            pass

        tool = to_anthropic_tool(summarize)
        assert tool["name"] == "summarize"
        assert "text" in tool["input_schema"]["properties"]

    def test_sync_dispatch_openai_errors_for_instructions(self):
        @instruction(name="my_instr", prompt="Do: {text}")
        def my_instr(text: str):
            pass

        tool_call = {
            "id": "call_1",
            "function": {
                "name": "my_instr",
                "arguments": json.dumps({"text": "hello"}),
            },
        }
        result = dispatch_openai(tool_call, {"my_instr": my_instr})
        assert "async dispatch" in result["content"].lower() or "async_dispatch" in result["content"]

    def test_sync_dispatch_anthropic_errors_for_instructions(self):
        @instruction(name="my_instr", prompt="Do: {text}")
        def my_instr(text: str):
            pass

        tool_use = {
            "id": "tu_1",
            "name": "my_instr",
            "input": {"text": "hello"},
        }
        result = dispatch_anthropic(tool_use, {"my_instr": my_instr})
        assert "async dispatch" in result["content"].lower() or "async_dispatch" in result["content"]

    @pytest.mark.asyncio
    async def test_async_dispatch_openai(self):
        backend = MockLLMBackend("summary here")
        ctx = _make_context(backend)

        @instruction(name="summarize", prompt="Summarize: {text}")
        def summarize(text: str):
            pass

        tool_call = {
            "id": "call_1",
            "function": {
                "name": "summarize",
                "arguments": json.dumps({"text": "hello world"}),
            },
        }
        result = await async_dispatch_openai(
            tool_call, {"summarize": summarize}, context=ctx,
        )
        assert result["role"] == "tool"
        assert "summary here" in result["content"]

    @pytest.mark.asyncio
    async def test_async_dispatch_anthropic(self):
        backend = MockLLMBackend("summary here")
        ctx = _make_context(backend)

        @instruction(name="summarize", prompt="Summarize: {text}")
        def summarize(text: str):
            pass

        tool_use = {
            "id": "tu_1",
            "name": "summarize",
            "input": {"text": "hello world"},
        }
        result = await async_dispatch_anthropic(
            tool_use, {"summarize": summarize}, context=ctx,
        )
        assert result["type"] == "tool_result"
        assert "summary here" in result["content"]


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------


class _InstructionPlugin(TransformerPlugin):
    """Test plugin that provides instructions."""

    def __init__(self):
        super().__init__("test_instruction_plugin", PluginSource.TUKUY)
        # Create instruction
        self._instr = Instruction(
            descriptor=InstructionDescriptor(
                name="plugin_summarize",
                description="Summarize via plugin",
                prompt="Summarize: {text}",
            ),
        )

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {"plugin_summarize": self._instr}


class TestRegistryIntegration:
    def test_instructions_in_registry(self):
        registry = PluginRegistry()
        plugin = _InstructionPlugin()
        registry.register(plugin)

        assert registry.get_instruction("plugin_summarize") is not None
        assert "plugin_summarize" in registry.instructions

    def test_instructions_appear_in_skills(self):
        registry = PluginRegistry()
        plugin = _InstructionPlugin()
        registry.register(plugin)

        # Instructions should also be visible in the skills view
        assert "plugin_summarize" in registry.skills

    def test_unregister_removes_instructions(self):
        registry = PluginRegistry()
        plugin = _InstructionPlugin()
        registry.register(plugin)

        registry.unregister("test_instruction_plugin")
        assert registry.get_instruction("plugin_summarize") is None
        assert "plugin_summarize" not in registry.skills
