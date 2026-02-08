"""Tests for the LLM utilities plugin."""

import json

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.llm import (
    LlmPlugin,
    CleanJsonOutputTransformer,
    StripThinkTagsTransformer,
    ExtractCodeBlocksTransformer,
    token_estimate,
)
from tukuy.skill import SkillResult


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── CleanJsonOutputTransformer ─────────────────────────────────────────────


class TestCleanJsonOutput:
    def test_already_clean(self):
        t = CleanJsonOutputTransformer("clean_json_output")
        result = t.transform('{"key": "value"}')
        assert result.value == '{"key": "value"}'

    def test_code_fence(self):
        t = CleanJsonOutputTransformer("clean_json_output")
        text = '```json\n{"key": "value"}\n```'
        result = t.transform(text)
        assert json.loads(result.value) == {"key": "value"}

    def test_think_tags(self):
        t = CleanJsonOutputTransformer("clean_json_output")
        text = '<think>thinking...</think>{"key": "value"}'
        result = t.transform(text)
        assert json.loads(result.value) == {"key": "value"}

    def test_trailing_comma(self):
        t = CleanJsonOutputTransformer("clean_json_output")
        text = '{"key": "value",}'
        result = t.transform(text)
        assert json.loads(result.value) == {"key": "value"}

    def test_surrounded_by_text(self):
        t = CleanJsonOutputTransformer("clean_json_output")
        text = 'Here is the JSON: {"key": "value"} That is all.'
        result = t.transform(text)
        assert json.loads(result.value) == {"key": "value"}

    def test_array(self):
        t = CleanJsonOutputTransformer("clean_json_output")
        text = 'Result: [1, 2, 3] done'
        result = t.transform(text)
        assert json.loads(result.value) == [1, 2, 3]

    def test_code_fence_with_think(self):
        t = CleanJsonOutputTransformer("clean_json_output")
        text = '<think>let me think</think>\n```json\n{"a": 1}\n```'
        result = t.transform(text)
        assert json.loads(result.value) == {"a": 1}


# ── StripThinkTagsTransformer ─────────────────────────────────────────────


class TestStripThinkTags:
    def test_strip_tags(self):
        t = StripThinkTagsTransformer("strip_think_tags")
        result = t.transform("<think>internal</think>Hello")
        assert result.value == "Hello"

    def test_no_tags(self):
        t = StripThinkTagsTransformer("strip_think_tags")
        result = t.transform("Hello world")
        assert result.value == "Hello world"

    def test_multiple_tags(self):
        t = StripThinkTagsTransformer("strip_think_tags")
        result = t.transform("<think>one</think>A<think>two</think>B")
        assert result.value == "AB"

    def test_multiline(self):
        t = StripThinkTagsTransformer("strip_think_tags")
        text = "<think>\nthinking\nacross lines\n</think>\nAnswer"
        result = t.transform(text)
        assert result.value == "Answer"


# ── ExtractCodeBlocksTransformer ──────────────────────────────────────────


class TestExtractCodeBlocks:
    def test_single_block(self):
        t = ExtractCodeBlocksTransformer("extract_code_blocks")
        text = "text\n```python\nprint('hello')\n```\nmore text"
        result = t.transform(text)
        assert result.value == "print('hello')"

    def test_multiple_blocks(self):
        t = ExtractCodeBlocksTransformer("extract_code_blocks")
        text = "```\nblock1\n```\nmiddle\n```\nblock2\n```"
        result = t.transform(text)
        assert "block1" in result.value
        assert "block2" in result.value

    def test_no_blocks(self):
        t = ExtractCodeBlocksTransformer("extract_code_blocks")
        result = t.transform("no code blocks here")
        assert result.value == "no code blocks here"

    def test_language_filter(self):
        t = ExtractCodeBlocksTransformer("extract_code_blocks", language="python")
        text = "```python\npy_code\n```\n```js\njs_code\n```"
        result = t.transform(text)
        assert "py_code" in result.value
        assert "js_code" not in result.value


# ── token_estimate skill ──────────────────────────────────────────────────


class TestTokenEstimate:
    def test_basic(self):
        result = token_estimate.__skill__.invoke("hello world")
        assert isinstance(result, SkillResult)
        assert result.success is True
        assert result.value["char_count"] == 11
        assert result.value["word_count"] == 2
        assert result.value["estimated_tokens"] > 0

    def test_empty_string(self):
        result = token_estimate.__skill__.invoke("")
        assert result.success is True
        assert result.value["char_count"] == 0

    def test_direct_call(self):
        result = token_estimate("test string")
        assert isinstance(result, dict)
        assert "estimated_tokens" in result


# ── Plugin registration ───────────────────────────────────────────────────


class TestLlmPlugin:
    def test_plugin_name(self):
        plugin = LlmPlugin()
        assert plugin.name == "llm"

    def test_has_all_transformers(self):
        plugin = LlmPlugin()
        names = set(plugin.transformers.keys())
        assert names == {"clean_json_output", "strip_think_tags", "extract_code_blocks"}

    def test_has_skills(self):
        plugin = LlmPlugin()
        assert "token_estimate" in plugin.skills


# ── Integration tests via TukuyTransformer ────────────────────────────────


class TestLlmIntegration:
    def test_clean_json_output(self, transformer):
        result = transformer.transform(
            '```json\n{"key": "value"}\n```',
            ["clean_json_output"],
        )
        assert json.loads(result) == {"key": "value"}

    def test_strip_think_tags(self, transformer):
        result = transformer.transform(
            "<think>thinking</think>answer",
            ["strip_think_tags"],
        )
        assert result == "answer"

    def test_extract_code_blocks(self, transformer):
        result = transformer.transform(
            "text\n```\ncode\n```\nmore",
            ["extract_code_blocks"],
        )
        assert result == "code"
