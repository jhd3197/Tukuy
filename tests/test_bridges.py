"""Tests for tukuy.bridges — OpenAI & Anthropic agent bridge."""

import json

import pytest

from tukuy.skill import Skill, SkillDescriptor, SkillResult, skill
from tukuy.bridges import (
    to_openai_tool,
    to_anthropic_tool,
    to_openai_tools,
    to_anthropic_tools,
    format_result_openai,
    format_result_anthropic,
    dispatch_openai,
    dispatch_anthropic,
    _get_first_param_name,
    _wrap_as_parameters,
    _normalize,
    _serialize_result_value,
)


# ── Module-level test fixtures ────────────────────────────────────────────


@skill
def greet(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"


@skill(
    input_schema={
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    }
)
def add_two(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@skill
def get_time() -> str:
    """Return current time."""
    return "12:00"


@skill(idempotent=True)
def fail_skill(x: str) -> str:
    """Always fails."""
    raise ValueError("boom")


@skill
def untyped(x):
    """Untyped skill."""
    return x


# ── TestGetFirstParamName ─────────────────────────────────────────────────


class TestGetFirstParamName:
    def test_simple_function(self):
        def f(name: str) -> str:
            pass

        assert _get_first_param_name(f) == "name"

    def test_skips_self(self):
        def f(self, data: int):
            pass

        assert _get_first_param_name(f) == "data"

    def test_skips_cls(self):
        def f(cls, value: str):
            pass

        assert _get_first_param_name(f) == "value"

    def test_no_params_fallback(self):
        def f():
            pass

        assert _get_first_param_name(f) == "input"

    def test_multiple_params_returns_first(self):
        def f(a: int, b: int, c: int):
            pass

        assert _get_first_param_name(f) == "a"

    def test_only_self_fallback(self):
        def f(self):
            pass

        assert _get_first_param_name(f) == "input"


# ── TestWrapAsParameters ──────────────────────────────────────────────────


class TestWrapAsParameters:
    def _make_skill(self, fn, input_schema=None):
        desc = SkillDescriptor(name="test", description="test", input_schema=input_schema)
        return Skill(descriptor=desc, fn=fn)

    def test_none_schema_empty_object(self):
        def f():
            pass

        s = self._make_skill(f, input_schema=None)
        result = _wrap_as_parameters(s)
        assert result == {"type": "object", "properties": {}}

    def test_simple_type_wrapped(self):
        def f(name):
            pass

        s = self._make_skill(f, input_schema={"type": "string"})
        result = _wrap_as_parameters(s)
        assert result == {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }

    def test_object_with_properties_passthrough(self):
        schema = {
            "type": "object",
            "properties": {"a": {"type": "integer"}},
            "required": ["a"],
        }

        def f(a):
            pass

        s = self._make_skill(f, input_schema=schema)
        result = _wrap_as_parameters(s)
        assert result is schema

    def test_bare_object_without_properties_wrapped(self):
        def f(data):
            pass

        s = self._make_skill(f, input_schema={"type": "object"})
        result = _wrap_as_parameters(s)
        assert result == {
            "type": "object",
            "properties": {"data": {"type": "object"}},
            "required": ["data"],
        }

    def test_param_name_from_function(self):
        def process(text):
            pass

        s = self._make_skill(process, input_schema={"type": "string"})
        result = _wrap_as_parameters(s)
        assert "text" in result["properties"]
        assert result["required"] == ["text"]


# ── TestNormalize ─────────────────────────────────────────────────────────


class TestNormalize:
    def test_skill_instance_passthrough(self):
        desc = SkillDescriptor(name="test", description="test")
        s = Skill(descriptor=desc, fn=lambda x: x)
        assert _normalize(s) is s

    def test_decorated_function_extracts_skill(self):
        s = _normalize(greet)
        assert isinstance(s, Skill)
        assert s.descriptor.name == "greet"

    def test_invalid_input_raises(self):
        with pytest.raises(TypeError, match="Expected a Skill"):
            _normalize("not a skill")

    def test_plain_function_raises(self):
        def plain(x):
            return x

        with pytest.raises(TypeError, match="Expected a Skill"):
            _normalize(plain)


# ── TestSerializeResultValue ──────────────────────────────────────────────


class TestSerializeResultValue:
    def test_json_serializable(self):
        result = SkillResult(value={"key": "val"}, success=True)
        assert _serialize_result_value(result) == json.dumps({"key": "val"})

    def test_none_value(self):
        result = SkillResult(value=None, success=True)
        assert _serialize_result_value(result) == ""

    def test_error_result(self):
        result = SkillResult(error="something went wrong", success=False)
        assert _serialize_result_value(result) == "something went wrong"

    def test_error_result_none_error(self):
        result = SkillResult(error=None, success=False)
        assert _serialize_result_value(result) == "Unknown error"

    def test_non_serializable_fallback(self):
        class Custom:
            def __str__(self):
                return "custom_repr"

        result = SkillResult(value=Custom(), success=True)
        assert _serialize_result_value(result) == "custom_repr"

    def test_string_value_json_quoted(self):
        result = SkillResult(value="hello", success=True)
        assert _serialize_result_value(result) == '"hello"'

    def test_integer_value(self):
        result = SkillResult(value=42, success=True)
        assert _serialize_result_value(result) == "42"


# ── TestToOpenaiTool ──────────────────────────────────────────────────────


class TestToOpenaiTool:
    def test_correct_structure(self):
        tool = to_openai_tool(greet)
        assert tool["type"] == "function"
        assert "function" in tool
        assert tool["function"]["name"] == "greet"
        assert tool["function"]["description"] == "Greet someone."
        assert "parameters" in tool["function"]

    def test_simple_type_wrapped(self):
        tool = to_openai_tool(greet)
        params = tool["function"]["parameters"]
        assert params["type"] == "object"
        assert "name" in params["properties"]
        assert params["properties"]["name"] == {"type": "string"}
        assert params["required"] == ["name"]

    def test_object_schema_passthrough(self):
        tool = to_openai_tool(add_two)
        params = tool["function"]["parameters"]
        assert "a" in params["properties"]
        assert "b" in params["properties"]

    def test_no_schema_empty_parameters(self):
        tool = to_openai_tool(get_time)
        params = tool["function"]["parameters"]
        assert params == {"type": "object", "properties": {}}

    def test_accepts_decorated_fn(self):
        tool = to_openai_tool(greet)
        assert tool["function"]["name"] == "greet"

    def test_accepts_skill_instance(self):
        tool = to_openai_tool(greet.__skill__)
        assert tool["function"]["name"] == "greet"


# ── TestToAnthropicTool ───────────────────────────────────────────────────


class TestToAnthropicTool:
    def test_correct_structure(self):
        tool = to_anthropic_tool(greet)
        assert tool["name"] == "greet"
        assert tool["description"] == "Greet someone."
        assert "input_schema" in tool

    def test_no_type_function_envelope(self):
        tool = to_anthropic_tool(greet)
        assert "type" not in tool

    def test_simple_type_wrapped(self):
        tool = to_anthropic_tool(greet)
        schema = tool["input_schema"]
        assert schema["type"] == "object"
        assert "name" in schema["properties"]

    def test_accepts_decorated_function(self):
        tool = to_anthropic_tool(add_two)
        assert tool["name"] == "add_two"


# ── TestBatchConversion ───────────────────────────────────────────────────


class TestBatchConversion:
    def test_empty_list(self):
        assert to_openai_tools([]) == []
        assert to_anthropic_tools([]) == []

    def test_multiple_skills_correct_count(self):
        skills = [greet, add_two, get_time]
        assert len(to_openai_tools(skills)) == 3
        assert len(to_anthropic_tools(skills)) == 3

    def test_openai_tools_structure(self):
        tools = to_openai_tools([greet, add_two])
        for t in tools:
            assert t["type"] == "function"
            assert "function" in t

    def test_anthropic_tools_structure(self):
        tools = to_anthropic_tools([greet, add_two])
        for t in tools:
            assert "name" in t
            assert "input_schema" in t


# ── TestFormatResultOpenai ────────────────────────────────────────────────


class TestFormatResultOpenai:
    def test_success(self):
        result = SkillResult(value={"greeting": "hi"}, success=True)
        msg = format_result_openai("call_123", result)
        assert msg["role"] == "tool"
        assert msg["tool_call_id"] == "call_123"
        assert msg["content"] == json.dumps({"greeting": "hi"})

    def test_error(self):
        result = SkillResult(error="bad input", success=False)
        msg = format_result_openai("call_456", result)
        assert msg["content"] == "bad input"

    def test_none_value_empty_content(self):
        result = SkillResult(value=None, success=True)
        msg = format_result_openai("call_789", result)
        assert msg["content"] == ""

    def test_non_serializable_fallback(self):
        class Obj:
            def __str__(self):
                return "obj_string"

        result = SkillResult(value=Obj(), success=True)
        msg = format_result_openai("call_000", result)
        assert msg["content"] == "obj_string"


# ── TestFormatResultAnthropic ─────────────────────────────────────────────


class TestFormatResultAnthropic:
    def test_success(self):
        result = SkillResult(value="ok", success=True)
        msg = format_result_anthropic("toolu_123", result)
        assert msg["type"] == "tool_result"
        assert msg["tool_use_id"] == "toolu_123"
        assert msg["content"] == '"ok"'

    def test_error_has_is_error(self):
        result = SkillResult(error="fail", success=False)
        msg = format_result_anthropic("toolu_456", result)
        assert msg["is_error"] is True
        assert msg["content"] == "fail"

    def test_success_no_is_error_key(self):
        result = SkillResult(value=42, success=True)
        msg = format_result_anthropic("toolu_789", result)
        assert "is_error" not in msg

    def test_none_value_empty_content(self):
        result = SkillResult(value=None, success=True)
        msg = format_result_anthropic("toolu_000", result)
        assert msg["content"] == ""


# ── TestDispatchOpenai ────────────────────────────────────────────────────


class TestDispatchOpenai:
    def _make_tool_call(self, name, arguments, call_id="call_abc"):
        return {
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": arguments},
        }

    def test_basic_dispatch(self):
        tool_call = self._make_tool_call("greet", json.dumps({"name": "Alice"}))
        result = dispatch_openai(tool_call, {"greet": greet})
        assert result["role"] == "tool"
        assert result["tool_call_id"] == "call_abc"
        assert json.loads(result["content"]) == "Hello, Alice!"

    def test_json_string_parsed(self):
        tool_call = self._make_tool_call("greet", '{"name": "Bob"}')
        result = dispatch_openai(tool_call, {"greet": greet})
        assert "Bob" in result["content"]

    def test_unknown_tool(self):
        tool_call = self._make_tool_call("nonexistent", "{}")
        result = dispatch_openai(tool_call, {"greet": greet})
        assert "Unknown tool: nonexistent" in result["content"]

    def test_invalid_json(self):
        tool_call = self._make_tool_call("greet", "not json{{{")
        result = dispatch_openai(tool_call, {"greet": greet})
        assert "Invalid JSON" in result["content"]

    def test_multi_param_object_schema(self):
        tool_call = self._make_tool_call("add_two", json.dumps({"a": 3, "b": 4}))
        result = dispatch_openai(tool_call, {"add_two": add_two})
        assert json.loads(result["content"]) == 7

    def test_skill_exception_returns_error(self):
        tool_call = self._make_tool_call("fail_skill", json.dumps({"x": "test"}))
        result = dispatch_openai(tool_call, {"fail_skill": fail_skill})
        assert "boom" in result["content"]

    def test_decorated_function_in_skills_dict(self):
        tool_call = self._make_tool_call("greet", json.dumps({"name": "Eve"}))
        result = dispatch_openai(tool_call, {"greet": greet})
        assert "Eve" in result["content"]

    def test_skill_instance_in_skills_dict(self):
        tool_call = self._make_tool_call("greet", json.dumps({"name": "Zoe"}))
        result = dispatch_openai(tool_call, {"greet": greet.__skill__})
        assert "Zoe" in result["content"]

    def test_no_params_skill(self):
        tool_call = self._make_tool_call("get_time", "{}")
        result = dispatch_openai(tool_call, {"get_time": get_time})
        assert json.loads(result["content"]) == "12:00"


# ── TestDispatchAnthropic ─────────────────────────────────────────────────


class TestDispatchAnthropic:
    def _make_tool_use(self, name, input_data, use_id="toolu_abc"):
        return {"type": "tool_use", "id": use_id, "name": name, "input": input_data}

    def test_basic_dispatch(self):
        tool_use = self._make_tool_use("greet", {"name": "Alice"})
        result = dispatch_anthropic(tool_use, {"greet": greet})
        assert result["type"] == "tool_result"
        assert result["tool_use_id"] == "toolu_abc"
        assert json.loads(result["content"]) == "Hello, Alice!"

    def test_unknown_tool(self):
        tool_use = self._make_tool_use("nonexistent", {})
        result = dispatch_anthropic(tool_use, {"greet": greet})
        assert "Unknown tool: nonexistent" in result["content"]
        assert result["is_error"] is True

    def test_multi_param_dispatch(self):
        tool_use = self._make_tool_use("add_two", {"a": 10, "b": 20})
        result = dispatch_anthropic(tool_use, {"add_two": add_two})
        assert json.loads(result["content"]) == 30

    def test_empty_input(self):
        tool_use = self._make_tool_use("get_time", {})
        result = dispatch_anthropic(tool_use, {"get_time": get_time})
        assert json.loads(result["content"]) == "12:00"

    def test_decorated_function_in_skills_dict(self):
        tool_use = self._make_tool_use("greet", {"name": "Eve"})
        result = dispatch_anthropic(tool_use, {"greet": greet})
        assert "Eve" in result["content"]

    def test_error_has_is_error_flag(self):
        tool_use = self._make_tool_use("fail_skill", {"x": "test"})
        result = dispatch_anthropic(tool_use, {"fail_skill": fail_skill})
        assert result["is_error"] is True
        assert "boom" in result["content"]


# ── TestRoundTrip ─────────────────────────────────────────────────────────


class TestRoundTrip:
    def test_openai_round_trip(self):
        # 1. Create tool definition
        tool_def = to_openai_tool(greet)
        assert tool_def["function"]["name"] == "greet"

        # 2. Simulate assistant tool call
        tool_call = {
            "id": "call_rt1",
            "type": "function",
            "function": {
                "name": tool_def["function"]["name"],
                "arguments": json.dumps({"name": "World"}),
            },
        }

        # 3. Dispatch
        result = dispatch_openai(tool_call, {"greet": greet})

        # 4. Verify
        assert result["role"] == "tool"
        assert result["tool_call_id"] == "call_rt1"
        assert json.loads(result["content"]) == "Hello, World!"

    def test_anthropic_round_trip(self):
        # 1. Create tool definition
        tool_def = to_anthropic_tool(greet)
        assert tool_def["name"] == "greet"

        # 2. Simulate assistant tool use
        tool_use = {
            "type": "tool_use",
            "id": "toolu_rt1",
            "name": tool_def["name"],
            "input": {"name": "World"},
        }

        # 3. Dispatch
        result = dispatch_anthropic(tool_use, {"greet": greet})

        # 4. Verify
        assert result["type"] == "tool_result"
        assert result["tool_use_id"] == "toolu_rt1"
        assert json.loads(result["content"]) == "Hello, World!"
        assert "is_error" not in result

    def test_openai_error_round_trip(self):
        tool_call = {
            "id": "call_err1",
            "type": "function",
            "function": {
                "name": "fail_skill",
                "arguments": json.dumps({"x": "test"}),
            },
        }
        result = dispatch_openai(tool_call, {"fail_skill": fail_skill})
        assert result["role"] == "tool"
        assert "boom" in result["content"]

    def test_anthropic_error_round_trip(self):
        tool_use = {
            "type": "tool_use",
            "id": "toolu_err1",
            "name": "fail_skill",
            "input": {"x": "test"},
        }
        result = dispatch_anthropic(tool_use, {"fail_skill": fail_skill})
        assert result["type"] == "tool_result"
        assert result["is_error"] is True
        assert "boom" in result["content"]
