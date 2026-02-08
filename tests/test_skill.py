"""Tests for tukuy.skill — SkillExample, SkillDescriptor, SkillResult, Skill."""

import pytest

from tukuy.skill import (
    Skill,
    SkillDescriptor,
    SkillExample,
    SkillResult,
    _infer_schemas,
    _resolve_schema,
    skill,
)
from tukuy.types import TransformResult


# ── helpers ──────────────────────────────────────────────────────────────────


def _add_one(x: int) -> int:
    return x + 1


def _failing_fn(x: int) -> int:
    raise ValueError("boom")


def _transform_result_fn(x: int) -> TransformResult:
    return TransformResult(value=x * 2)


def _transform_result_error_fn(x: int) -> TransformResult:
    return TransformResult(error=Exception("transform failed"))


class _FakePydanticV2:
    """Duck-typed Pydantic v2 model (has ``model_json_schema``)."""

    @classmethod
    def model_json_schema(cls):
        return {"type": "object", "properties": {"name": {"type": "string"}}}


class _FakePydanticV1:
    """Duck-typed Pydantic v1 model (has ``schema``)."""

    @classmethod
    def schema(cls):
        return {"type": "object", "properties": {"age": {"type": "integer"}}}


# ── TestSkillExample ─────────────────────────────────────────────────────────


class TestSkillExample:
    def test_creation(self):
        ex = SkillExample(input="hello", output="HELLO", description="upper")
        assert ex.input == "hello"
        assert ex.output == "HELLO"
        assert ex.description == "upper"

    def test_default_description(self):
        ex = SkillExample(input=1, output=2)
        assert ex.description == ""

    def test_to_dict(self):
        ex = SkillExample(input="a", output="b", description="desc")
        d = ex.to_dict()
        assert d == {"input": "a", "output": "b", "description": "desc"}


# ── TestResolveSchema ────────────────────────────────────────────────────────


class TestResolveSchema:
    def test_none_passthrough(self):
        assert _resolve_schema(None) is None

    def test_dict_passthrough(self):
        schema = {"type": "object"}
        assert _resolve_schema(schema) is schema

    def test_str_type(self):
        assert _resolve_schema(str) == {"type": "string"}

    def test_int_type(self):
        assert _resolve_schema(int) == {"type": "integer"}

    def test_float_type(self):
        assert _resolve_schema(float) == {"type": "number"}

    def test_bool_type(self):
        assert _resolve_schema(bool) == {"type": "boolean"}

    def test_list_type(self):
        assert _resolve_schema(list) == {"type": "array"}

    def test_dict_type(self):
        assert _resolve_schema(dict) == {"type": "object"}

    def test_bytes_type(self):
        result = _resolve_schema(bytes)
        assert result["type"] == "string"
        assert result["contentEncoding"] == "base64"

    def test_pydantic_v2_duck(self):
        result = _resolve_schema(_FakePydanticV2)
        assert result == {"type": "object", "properties": {"name": {"type": "string"}}}

    def test_pydantic_v1_duck(self):
        result = _resolve_schema(_FakePydanticV1)
        assert result == {"type": "object", "properties": {"age": {"type": "integer"}}}

    def test_unsupported_raises(self):
        with pytest.raises(TypeError, match="Cannot resolve schema"):
            _resolve_schema(42)


# ── TestSkillDescriptor ──────────────────────────────────────────────────────


class TestSkillDescriptor:
    def test_minimal_creation(self):
        sd = SkillDescriptor(name="test", description="A test skill")
        assert sd.name == "test"
        assert sd.description == "A test skill"
        assert sd.version == "0.1.0"
        assert sd.input_schema is None
        assert sd.output_schema is None
        assert sd.category == "general"
        assert sd.tags == []
        assert sd.examples == []
        assert sd.is_async is False
        assert sd.idempotent is False
        assert sd.side_effects is False
        assert sd.requires_network is False
        assert sd.requires_filesystem is False

    def test_schema_resolution_python_types(self):
        sd = SkillDescriptor(name="x", description="x", input_schema=str, output_schema=int)
        assert sd.input_schema == {"type": "string"}
        assert sd.output_schema == {"type": "integer"}

    def test_schema_resolution_dict_passthrough(self):
        schema = {"type": "array", "items": {"type": "string"}}
        sd = SkillDescriptor(name="x", description="x", input_schema=schema)
        assert sd.input_schema is schema

    def test_schema_resolution_pydantic_v2(self):
        sd = SkillDescriptor(name="x", description="x", input_schema=_FakePydanticV2)
        assert sd.input_schema == {"type": "object", "properties": {"name": {"type": "string"}}}

    def test_tag_normalization(self):
        sd = SkillDescriptor(name="x", description="x", tags=["Text", "UPPER", "MiXeD"])
        assert sd.tags == ["text", "upper", "mixed"]

    def test_to_dict(self):
        ex = SkillExample(input="a", output="b")
        sd = SkillDescriptor(
            name="s",
            description="d",
            version="1.0",
            input_schema=str,
            output_schema=int,
            category="text",
            tags=["Tag"],
            examples=[ex],
            is_async=True,
            estimated_latency_ms=50,
            idempotent=True,
            side_effects=True,
            required_imports=["re"],
            requires_network=True,
            requires_filesystem=True,
        )
        d = sd.to_dict()
        assert d["name"] == "s"
        assert d["description"] == "d"
        assert d["version"] == "1.0"
        assert d["input_schema"] == {"type": "string"}
        assert d["output_schema"] == {"type": "integer"}
        assert d["category"] == "text"
        assert d["tags"] == ["tag"]
        assert d["examples"] == [{"input": "a", "output": "b", "description": ""}]
        assert d["is_async"] is True
        assert d["estimated_latency_ms"] == 50
        assert d["idempotent"] is True
        assert d["side_effects"] is True
        assert d["required_imports"] == ["re"]
        assert d["requires_network"] is True
        assert d["requires_filesystem"] is True

    def test_from_metadata(self):
        """Bridge from TransformerMetadata → SkillDescriptor."""
        from tukuy.core.introspection import TransformerMetadata, TransformerCategory

        meta = TransformerMetadata(
            name="upper",
            plugin="text",
            description="Uppercase text",
            category=TransformerCategory.TEXT_PROCESSING,
            version="v2",
            tags={"text", "case-conversion"},
            examples=["'hello' → 'HELLO'"],
        )
        sd = SkillDescriptor.from_metadata(meta)
        assert sd.name == "upper"
        assert sd.description == "Uppercase text"
        assert sd.version == "v2"
        assert sd.category == "text_processing"
        assert set(sd.tags) == {"text", "case-conversion"}
        assert len(sd.examples) == 1
        assert sd.examples[0].input == "'hello' → 'HELLO'"


# ── TestSkillResult ──────────────────────────────────────────────────────────


class TestSkillResult:
    def test_success_result(self):
        r = SkillResult(value=42, success=True)
        assert r.value == 42
        assert r.success is True
        assert r.failed is False
        assert r.error is None

    def test_error_result(self):
        r = SkillResult(error="bad input", success=False)
        assert r.failed is True
        assert r.error == "bad input"
        assert r.value is None

    def test_duration_and_metadata(self):
        r = SkillResult(value=1, duration_ms=12.5, metadata={"key": "val"})
        assert r.duration_ms == 12.5
        assert r.metadata == {"key": "val"}

    def test_retryable_default_false(self):
        r = SkillResult(value=1)
        assert r.retryable is False

    def test_to_transform_result_success(self):
        sr = SkillResult(value="ok", success=True)
        tr = sr.to_transform_result()
        assert isinstance(tr, TransformResult)
        assert tr.value == "ok"
        assert tr.success is True

    def test_to_transform_result_error(self):
        sr = SkillResult(error="fail", success=False)
        tr = sr.to_transform_result()
        assert tr.failed is True
        assert str(tr.error) == "fail"

    def test_from_transform_result_success(self):
        tr = TransformResult(value=99)
        sr = SkillResult.from_transform_result(tr)
        assert sr.value == 99
        assert sr.success is True

    def test_from_transform_result_error(self):
        tr = TransformResult(error=Exception("oops"))
        sr = SkillResult.from_transform_result(tr)
        assert sr.success is False
        assert sr.error == "oops"


# ── TestSkill ────────────────────────────────────────────────────────────────


class TestSkill:
    def _make_skill(self, fn=None, *, idempotent=False):
        desc = SkillDescriptor(name="test_skill", description="test", idempotent=idempotent)
        return Skill(descriptor=desc, fn=fn or _add_one)

    def test_invoke_success(self):
        skill = self._make_skill()
        result = skill.invoke(5)
        assert result.success is True
        assert result.value == 6
        assert result.duration_ms is not None
        assert result.duration_ms >= 0

    def test_invoke_error(self):
        skill = self._make_skill(fn=_failing_fn)
        result = skill.invoke(5)
        assert result.success is False
        assert "boom" in result.error
        assert result.duration_ms is not None

    def test_invoke_error_not_retryable_by_default(self):
        skill = self._make_skill(fn=_failing_fn, idempotent=False)
        result = skill.invoke(1)
        assert result.retryable is False

    def test_invoke_error_retryable_when_idempotent(self):
        skill = self._make_skill(fn=_failing_fn, idempotent=True)
        result = skill.invoke(1)
        assert result.retryable is True

    def test_invoke_transform_result_success(self):
        skill = self._make_skill(fn=_transform_result_fn)
        result = skill.invoke(5)
        assert result.success is True
        assert result.value == 10
        assert result.duration_ms is not None

    def test_invoke_transform_result_error(self):
        skill = self._make_skill(fn=_transform_result_error_fn)
        result = skill.invoke(5)
        assert result.success is False
        assert "transform failed" in result.error

    def test_skill_descriptor_accessible(self):
        s = self._make_skill()
        assert s.descriptor.name == "test_skill"


# ── TestInferSchemas ────────────────────────────────────────────────────────


class TestInferSchemas:
    def test_infer_from_typed_function(self):
        def f(x: int) -> str:
            pass

        inp, out = _infer_schemas(f)
        assert inp == {"type": "integer"}
        assert out == {"type": "string"}

    def test_infer_skips_self(self):
        def f(self, x: float) -> bool:
            pass

        inp, out = _infer_schemas(f)
        assert inp == {"type": "number"}
        assert out == {"type": "boolean"}

    def test_infer_skips_cls(self):
        def f(cls, x: dict) -> list:
            pass

        inp, out = _infer_schemas(f)
        assert inp == {"type": "object"}
        assert out == {"type": "array"}

    def test_infer_no_annotations(self):
        def f(x):
            pass

        inp, out = _infer_schemas(f)
        assert inp is None
        assert out is None

    def test_infer_only_return(self):
        def f(x) -> int:
            pass

        inp, out = _infer_schemas(f)
        assert inp is None
        assert out == {"type": "integer"}

    def test_infer_only_input(self):
        def f(x: str):
            pass

        inp, out = _infer_schemas(f)
        assert inp == {"type": "string"}
        assert out is None

    def test_infer_complex_input_ignored(self):
        from typing import Optional

        def f(x: Optional[str]) -> int:
            pass

        inp, out = _infer_schemas(f)
        assert inp is None
        assert out == {"type": "integer"}

    def test_infer_complex_return_ignored(self):
        from typing import Optional

        def f(x: int) -> Optional[str]:
            pass

        inp, out = _infer_schemas(f)
        assert inp == {"type": "integer"}
        assert out is None

    def test_infer_no_parameters(self):
        def f() -> str:
            pass

        inp, out = _infer_schemas(f)
        assert inp is None
        assert out == {"type": "string"}


# ── TestSkillDecorator ──────────────────────────────────────────────────────


class TestSkillDecorator:
    def test_bare_decorator(self):
        @skill
        def my_fn(x: int) -> str:
            return str(x)

        assert hasattr(my_fn, "__skill__")
        assert my_fn.__skill__.descriptor.name == "my_fn"

    def test_empty_parens_decorator(self):
        @skill()
        def my_fn(x: int) -> str:
            return str(x)

        assert hasattr(my_fn, "__skill__")
        assert my_fn.__skill__.descriptor.name == "my_fn"

    def test_custom_name(self):
        @skill(name="custom")
        def my_fn(x):
            return x

        assert my_fn.__skill__.descriptor.name == "custom"

    def test_all_kwargs(self):
        ex = SkillExample(input=1, output=2)

        @skill(
            name="all_kwargs",
            description="full desc",
            version="2.0.0",
            input_schema=str,
            output_schema=int,
            category="text",
            tags=["Tag", "UPPER"],
            examples=[ex],
            is_async=True,
            estimated_latency_ms=100,
            idempotent=True,
            side_effects=True,
            required_imports=["os"],
            requires_network=True,
            requires_filesystem=True,
        )
        def my_fn(x):
            return x

        d = my_fn.__skill__.descriptor
        assert d.name == "all_kwargs"
        assert d.description == "full desc"
        assert d.version == "2.0.0"
        assert d.input_schema == {"type": "string"}
        assert d.output_schema == {"type": "integer"}
        assert d.category == "text"
        assert d.tags == ["tag", "upper"]
        assert d.examples == [ex]
        assert d.is_async is True
        assert d.estimated_latency_ms == 100
        assert d.idempotent is True
        assert d.side_effects is True
        assert d.required_imports == ["os"]
        assert d.requires_network is True
        assert d.requires_filesystem is True

    def test_function_still_callable(self):
        @skill
        def add_one(x: int) -> int:
            return x + 1

        assert add_one(5) == 6

    def test_description_from_docstring(self):
        @skill
        def my_fn(x):
            """This is the description."""
            return x

        assert my_fn.__skill__.descriptor.description == "This is the description."

    def test_no_docstring_empty_description(self):
        @skill
        def my_fn(x):
            return x

        assert my_fn.__skill__.descriptor.description == ""

    def test_multiline_docstring_stripped(self):
        @skill
        def my_fn(x):
            """
            Multi-line docstring.
            """
            return x

        assert my_fn.__skill__.descriptor.description == "Multi-line docstring."

    def test_async_detection(self):
        @skill
        async def my_async_fn(x: int) -> str:
            return str(x)

        assert my_async_fn.__skill__.descriptor.is_async is True

    def test_sync_detection(self):
        @skill
        def my_sync_fn(x: int) -> str:
            return str(x)

        assert my_sync_fn.__skill__.descriptor.is_async is False

    def test_explicit_is_async_override(self):
        @skill(is_async=False)
        async def my_async_fn(x):
            return x

        assert my_async_fn.__skill__.descriptor.is_async is False

    def test_schema_inference_from_annotations(self):
        @skill
        def my_fn(x: int) -> str:
            return str(x)

        assert my_fn.__skill__.descriptor.input_schema == {"type": "integer"}
        assert my_fn.__skill__.descriptor.output_schema == {"type": "string"}

    def test_explicit_schema_overrides_inferred(self):
        @skill(input_schema=dict, output_schema=list)
        def my_fn(x: int) -> str:
            return str(x)

        assert my_fn.__skill__.descriptor.input_schema == {"type": "object"}
        assert my_fn.__skill__.descriptor.output_schema == {"type": "array"}

    def test_complex_annotation_yields_none(self):
        from typing import Optional

        @skill
        def my_fn(x: Optional[str]) -> Optional[int]:
            return None

        assert my_fn.__skill__.descriptor.input_schema is None
        assert my_fn.__skill__.descriptor.output_schema is None

    def test_skill_attribute_is_skill_instance(self):
        @skill
        def my_fn(x):
            return x

        assert isinstance(my_fn.__skill__, Skill)

    def test_invoke_produces_skill_result(self):
        @skill
        def add_one(x: int) -> int:
            return x + 1

        result = add_one.__skill__.invoke(5)
        assert isinstance(result, SkillResult)
        assert result.success is True
        assert result.value == 6

    def test_tags_normalized_lowercase(self):
        @skill(tags=["Text", "UPPER", "MiXeD"])
        def my_fn(x):
            return x

        assert my_fn.__skill__.descriptor.tags == ["text", "upper", "mixed"]

    def test_lambda_support(self):
        fn = skill(lambda x: x)
        assert hasattr(fn, "__skill__")
        assert fn.__skill__.descriptor.name == "<lambda>"
        assert fn(42) == 42

    def test_method_with_self_skips_self(self):
        @skill
        def method(self, x: float) -> bool:
            return True

        assert method.__skill__.descriptor.input_schema == {"type": "number"}
        assert method.__skill__.descriptor.output_schema == {"type": "boolean"}
