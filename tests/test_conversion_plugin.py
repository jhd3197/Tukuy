"""Tests for the Conversion plugin."""

import json

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.conversion import (
    ConversionPlugin,
    CsvToJsonTransformer,
    JsonToCsvTransformer,
    MarkdownToHtmlTransformer,
    HtmlToMarkdownTransformer,
)


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── CsvToJsonTransformer ──────────────────────────────────────────────────


class TestCsvToJson:
    def test_basic(self):
        t = CsvToJsonTransformer("csv_to_json")
        result = t.transform("name,age\nAlice,30\nBob,25")
        data = json.loads(result.value)
        assert len(data) == 2
        assert data[0] == {"name": "Alice", "age": "30"}
        assert data[1] == {"name": "Bob", "age": "25"}

    def test_custom_delimiter(self):
        t = CsvToJsonTransformer("csv_to_json", delimiter=";")
        result = t.transform("a;b\n1;2")
        data = json.loads(result.value)
        assert data[0] == {"a": "1", "b": "2"}

    def test_single_row(self):
        t = CsvToJsonTransformer("csv_to_json")
        result = t.transform("col1,col2\na,b")
        data = json.loads(result.value)
        assert len(data) == 1


# ── JsonToCsvTransformer ──────────────────────────────────────────────────


class TestJsonToCsv:
    def test_basic(self):
        t = JsonToCsvTransformer("json_to_csv")
        input_json = json.dumps([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
        result = t.transform(input_json)
        lines = result.value.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows
        assert "name" in lines[0]
        assert "Alice" in lines[1]

    def test_empty_array_fails(self):
        t = JsonToCsvTransformer("json_to_csv")
        result = t.transform("[]")
        assert result.failed

    def test_roundtrip(self):
        csv_text = "x,y\n1,2\n3,4"
        t1 = CsvToJsonTransformer("csv_to_json")
        json_str = t1.transform(csv_text).value
        t2 = JsonToCsvTransformer("json_to_csv")
        csv_result = t2.transform(json_str).value
        assert "x" in csv_result
        assert "1" in csv_result


# ── YamlToJson / JsonToYaml ──────────────────────────────────────────────


class TestYamlConversion:
    @pytest.fixture(autouse=True)
    def _skip_without_yaml(self):
        pytest.importorskip("yaml")

    def test_yaml_to_json(self):
        from tukuy.plugins.conversion import YamlToJsonTransformer

        t = YamlToJsonTransformer("yaml_to_json")
        result = t.transform("name: Alice\nage: 30")
        data = json.loads(result.value)
        assert data == {"name": "Alice", "age": 30}

    def test_json_to_yaml(self):
        from tukuy.plugins.conversion import JsonToYamlTransformer

        t = JsonToYamlTransformer("json_to_yaml")
        result = t.transform('{"name": "Alice"}')
        assert "name: Alice" in result.value

    def test_yaml_to_json_integration(self, transformer):
        result = transformer.transform("key: value", ["yaml_to_json"])
        data = json.loads(result)
        assert data == {"key": "value"}


# ── MarkdownToHtml ────────────────────────────────────────────────────────


class TestMarkdownToHtml:
    def test_heading(self):
        t = MarkdownToHtmlTransformer("markdown_to_html")
        result = t.transform("# Hello")
        assert "<h1>Hello</h1>" in result.value

    def test_bold(self):
        t = MarkdownToHtmlTransformer("markdown_to_html")
        result = t.transform("**bold**")
        assert "<strong>bold</strong>" in result.value

    def test_italic(self):
        t = MarkdownToHtmlTransformer("markdown_to_html")
        result = t.transform("*italic*")
        assert "<em>italic</em>" in result.value

    def test_link(self):
        t = MarkdownToHtmlTransformer("markdown_to_html")
        result = t.transform("[text](http://example.com)")
        assert '<a href="http://example.com">text</a>' in result.value

    def test_code_block(self):
        t = MarkdownToHtmlTransformer("markdown_to_html")
        result = t.transform("```python\nprint('hi')\n```")
        assert "<pre><code>" in result.value
        assert "print('hi')" in result.value


# ── HtmlToMarkdown ────────────────────────────────────────────────────────


class TestHtmlToMarkdown:
    def test_heading(self):
        t = HtmlToMarkdownTransformer("html_to_markdown")
        result = t.transform("<h1>Hello</h1>")
        assert "# Hello" in result.value

    def test_bold(self):
        t = HtmlToMarkdownTransformer("html_to_markdown")
        result = t.transform("<strong>bold</strong>")
        assert "**bold**" in result.value

    def test_link(self):
        t = HtmlToMarkdownTransformer("html_to_markdown")
        result = t.transform('<a href="http://example.com">text</a>')
        assert "[text](http://example.com)" in result.value


# ── TomlToJson ────────────────────────────────────────────────────────────


class TestTomlToJson:
    def test_basic(self):
        try:
            import tomllib
        except ImportError:
            try:
                import tomli
            except ImportError:
                pytest.skip("No TOML library available")

        from tukuy.plugins.conversion import TomlToJsonTransformer

        t = TomlToJsonTransformer("toml_to_json")
        result = t.transform('[section]\nkey = "value"')
        data = json.loads(result.value)
        assert data == {"section": {"key": "value"}}


# ── Plugin registration ──────────────────────────────────────────────────


class TestConversionPlugin:
    def test_plugin_name(self):
        plugin = ConversionPlugin()
        assert plugin.name == "conversion"

    def test_has_all_transformers(self):
        plugin = ConversionPlugin()
        names = set(plugin.transformers.keys())
        expected = {
            "csv_to_json", "json_to_csv", "yaml_to_json", "json_to_yaml",
            "markdown_to_html", "html_to_markdown", "toml_to_json",
        }
        assert names == expected


# ── Integration tests via TukuyTransformer ────────────────────────────────


class TestConversionIntegration:
    def test_csv_to_json(self, transformer):
        result = transformer.transform("a,b\n1,2", ["csv_to_json"])
        data = json.loads(result)
        assert data[0] == {"a": "1", "b": "2"}

    def test_markdown_to_html(self, transformer):
        result = transformer.transform("# Title", ["markdown_to_html"])
        assert "<h1>Title</h1>" in result

    def test_html_to_markdown(self, transformer):
        result = transformer.transform("<h2>Sub</h2>", ["html_to_markdown"])
        assert "## Sub" in result
