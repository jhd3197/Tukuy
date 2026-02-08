"""Tests for the Code Extraction plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.code_extract import (
    CodeExtractPlugin,
    ExtractFencedFilesTransformer,
    ExtractHtmlDocumentTransformer,
    StripReasoningPreambleTransformer,
)


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── ExtractFencedFilesTransformer ─────────────────────────────────────────


class TestExtractFencedFiles:
    def test_single_html_block(self):
        t = ExtractFencedFilesTransformer("extract_fenced_files")
        text = "Here is the code:\n```html\n<h1>Hello</h1>\n```"
        result = t.transform(text)
        assert result.value == {"index.html": "<h1>Hello</h1>"}

    def test_multiple_blocks(self):
        t = ExtractFencedFilesTransformer("extract_fenced_files")
        text = "```html\n<html></html>\n```\n```css\nbody{}\n```\n```js\nalert(1)\n```"
        result = t.transform(text)
        assert "index.html" in result.value
        assert "styles.css" in result.value
        assert "script.js" in result.value

    def test_javascript_maps_to_script_js(self):
        t = ExtractFencedFilesTransformer("extract_fenced_files")
        text = "```javascript\nconsole.log('hi')\n```"
        result = t.transform(text)
        assert "script.js" in result.value

    def test_duplicate_filenames_get_suffix(self):
        t = ExtractFencedFilesTransformer("extract_fenced_files")
        text = "```html\nfirst\n```\n```html\nsecond\n```"
        result = t.transform(text)
        assert "index.html" in result.value
        assert "index_2.html" in result.value

    def test_unknown_language_skipped(self):
        t = ExtractFencedFilesTransformer("extract_fenced_files")
        text = "```rust\nfn main() {}\n```"
        result = t.transform(text)
        assert result.value == {}

    def test_no_fences_returns_empty(self):
        t = ExtractFencedFilesTransformer("extract_fenced_files")
        result = t.transform("no code here")
        assert result.value == {}

    def test_custom_lang_map(self):
        t = ExtractFencedFilesTransformer(
            "extract_fenced_files",
            lang_map={"rust": "main.rs", "go": "main.go"},
        )
        text = "```rust\nfn main() {}\n```"
        result = t.transform(text)
        assert result.value == {"main.rs": "fn main() {}"}

    def test_python_block(self):
        t = ExtractFencedFilesTransformer("extract_fenced_files")
        text = "```python\nprint('hello')\n```"
        result = t.transform(text)
        assert "main.py" in result.value


# ── ExtractHtmlDocumentTransformer ────────────────────────────────────────


class TestExtractHtmlDocument:
    def test_full_document(self):
        t = ExtractHtmlDocumentTransformer("extract_html_document")
        text = "Some preamble\n<!DOCTYPE html><html><head></head><body></body></html>\nMore text"
        result = t.transform(text)
        assert result.value["found"] is True
        assert "<!DOCTYPE html>" in result.value["html"]
        assert "</html>" in result.value["html"]

    def test_extracts_style_blocks(self):
        t = ExtractHtmlDocumentTransformer("extract_html_document")
        html = "<!DOCTYPE html><html><head><style>body { color: red; }</style></head><body></body></html>"
        result = t.transform(html)
        assert "body { color: red; }" in result.value["styles"]

    def test_extracts_script_blocks(self):
        t = ExtractHtmlDocumentTransformer("extract_html_document")
        html = '<!DOCTYPE html><html><head></head><body><script>alert("hi")</script></body></html>'
        result = t.transform(html)
        assert 'alert("hi")' in result.value["scripts"]

    def test_skips_external_scripts(self):
        t = ExtractHtmlDocumentTransformer("extract_html_document")
        html = '<!DOCTYPE html><html><head><script src="app.js"></script></head><body></body></html>'
        result = t.transform(html)
        assert result.value["scripts"] == ""

    def test_no_html_found(self):
        t = ExtractHtmlDocumentTransformer("extract_html_document")
        result = t.transform("Just some text, no HTML document")
        assert result.value["found"] is False
        assert result.value["html"] == ""

    def test_strips_wrapping_code_fence(self):
        t = ExtractHtmlDocumentTransformer("extract_html_document")
        text = "```html\n<!DOCTYPE html><html><body></body></html>\n```"
        result = t.transform(text)
        assert result.value["found"] is True

    def test_html_without_doctype(self):
        t = ExtractHtmlDocumentTransformer("extract_html_document")
        text = "<html><head></head><body></body></html>"
        result = t.transform(text)
        assert result.value["found"] is True


# ── StripReasoningPreambleTransformer ─────────────────────────────────────


class TestStripReasoningPreamble:
    def test_strips_before_code_fence(self):
        t = StripReasoningPreambleTransformer("strip_reasoning_preamble")
        text = "Let me think about this...\n\nOkay here's the code:\n```html\n<h1>Hi</h1>\n```"
        result = t.transform(text)
        assert result.value.startswith("```html")

    def test_strips_before_html(self):
        t = StripReasoningPreambleTransformer("strip_reasoning_preamble")
        text = "I'll create a page\n<!DOCTYPE html><html></html>"
        result = t.transform(text)
        assert result.value.startswith("<!DOCTYPE html>")

    def test_preserves_if_starts_with_fence(self):
        t = StripReasoningPreambleTransformer("strip_reasoning_preamble")
        text = "```html\n<h1>Hi</h1>\n```"
        result = t.transform(text)
        assert result.value == text

    def test_preserves_if_no_code(self):
        t = StripReasoningPreambleTransformer("strip_reasoning_preamble")
        text = "Just some thinking text"
        result = t.transform(text)
        assert result.value == text

    def test_css_fence(self):
        t = StripReasoningPreambleTransformer("strip_reasoning_preamble")
        text = "thinking...\n```css\nbody{}\n```"
        result = t.transform(text)
        assert result.value.startswith("```css")


# ── Plugin registration ──────────────────────────────────────────────────


class TestCodeExtractPlugin:
    def test_plugin_name(self):
        plugin = CodeExtractPlugin()
        assert plugin.name == "code_extract"

    def test_has_all_transformers(self):
        plugin = CodeExtractPlugin()
        names = set(plugin.transformers.keys())
        assert names == {"extract_fenced_files", "extract_html_document", "strip_reasoning_preamble"}


# ── Integration tests via TukuyTransformer ────────────────────────────────


class TestCodeExtractIntegration:
    def test_extract_fenced_files(self, transformer):
        text = "```html\n<h1>Hi</h1>\n```\n```css\nbody{}\n```"
        result = transformer.transform(text, ["extract_fenced_files"])
        assert "index.html" in result
        assert "styles.css" in result

    def test_extract_html_document(self, transformer):
        text = "preamble\n<!DOCTYPE html><html><body></body></html>"
        result = transformer.transform(text, ["extract_html_document"])
        assert result["found"] is True

    def test_strip_reasoning_preamble(self, transformer):
        text = "thinking...\n```html\n<h1>Hi</h1>\n```"
        result = transformer.transform(text, ["strip_reasoning_preamble"])
        assert result.startswith("```html")
