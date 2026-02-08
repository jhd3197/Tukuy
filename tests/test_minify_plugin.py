"""Tests for the Minify plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.minify import (
    MinifyPlugin,
    MinifyHtmlTransformer,
    MinifyCssTransformer,
    MinifyJsTransformer,
    PrettifyHtmlTransformer,
)


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── MinifyHtmlTransformer ────────────────────────────────────────────────


class TestMinifyHtml:
    def test_removes_comments(self):
        t = MinifyHtmlTransformer("minify_html")
        result = t.transform("<div><!-- comment --><p>text</p></div>")
        assert "<!-- comment -->" not in result.value
        assert "<p>text</p>" in result.value

    def test_collapses_whitespace(self):
        t = MinifyHtmlTransformer("minify_html")
        html = "<div>   \n   <p>  text  </p>   \n   </div>"
        result = t.transform(html)
        assert "   " not in result.value
        assert "<div>" in result.value

    def test_preserves_pre_blocks(self):
        t = MinifyHtmlTransformer("minify_html")
        html = "<pre>  keep   spaces  </pre>"
        result = t.transform(html)
        assert "  keep   spaces  " in result.value

    def test_preserves_script_blocks(self):
        t = MinifyHtmlTransformer("minify_html")
        html = "<script>  var x = 1;  </script>"
        result = t.transform(html)
        assert "var x = 1;" in result.value

    def test_shorter_than_original(self):
        t = MinifyHtmlTransformer("minify_html")
        html = """
        <html>
            <head>
                <title>Test</title>
            </head>
            <body>
                <!-- Main content -->
                <div class="container">
                    <p>Hello world</p>
                </div>
            </body>
        </html>
        """
        result = t.transform(html)
        assert len(result.value) < len(html)


# ── MinifyCssTransformer ────────────────────────────────────────────────


class TestMinifyCss:
    def test_removes_comments(self):
        t = MinifyCssTransformer("minify_css")
        result = t.transform("/* comment */ body { color: red; }")
        assert "/* comment */" not in result.value
        assert "color:red" in result.value

    def test_removes_whitespace(self):
        t = MinifyCssTransformer("minify_css")
        css = "body {\n    color: red;\n    background: blue;\n}"
        result = t.transform(css)
        assert "\n" not in result.value
        assert "color:red" in result.value

    def test_removes_trailing_semicolons(self):
        t = MinifyCssTransformer("minify_css")
        result = t.transform("body { color: red; }")
        assert ";}" not in result.value

    def test_shorter_than_original(self):
        t = MinifyCssTransformer("minify_css")
        css = """
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background-color: #333;
            color: white;
        }
        """
        result = t.transform(css)
        assert len(result.value) < len(css)


# ── MinifyJsTransformer ─────────────────────────────────────────────────


class TestMinifyJs:
    def test_removes_single_line_comments(self):
        t = MinifyJsTransformer("minify_js")
        result = t.transform("var x = 1; // comment\nvar y = 2;")
        assert "// comment" not in result.value
        assert "x" in result.value
        assert "y" in result.value

    def test_removes_multi_line_comments(self):
        t = MinifyJsTransformer("minify_js")
        result = t.transform("/* block */\nvar x = 1;")
        assert "/* block */" not in result.value

    def test_preserves_strings(self):
        t = MinifyJsTransformer("minify_js")
        result = t.transform('var x = "hello world";')
        assert '"hello world"' in result.value

    def test_preserves_single_quoted_strings(self):
        t = MinifyJsTransformer("minify_js")
        result = t.transform("var x = 'hello // not a comment';")
        assert "'hello // not a comment'" in result.value

    def test_shorter_than_original(self):
        t = MinifyJsTransformer("minify_js")
        js = """
        // Initialize the app
        function init() {
            var container = document.getElementById('app');
            container.innerHTML = '<h1>Hello</h1>';

            /* Set up events */
            container.addEventListener('click', function() {
                console.log('clicked');
            });
        }
        """
        result = t.transform(js)
        assert len(result.value) < len(js)


# ── PrettifyHtmlTransformer ─────────────────────────────────────────────


class TestPrettifyHtml:
    def test_adds_indentation(self):
        t = PrettifyHtmlTransformer("prettify_html")
        html = "<html><head><title>T</title></head><body><div><p>Hi</p></div></body></html>"
        result = t.transform(html)
        lines = result.value.split("\n")
        assert len(lines) > 1
        # Some lines should be indented
        indented = [l for l in lines if l.startswith("  ")]
        assert len(indented) > 0

    def test_custom_indent(self):
        t = PrettifyHtmlTransformer("prettify_html", indent="\t")
        html = "<html><body><div>text</div></body></html>"
        result = t.transform(html)
        assert "\t" in result.value

    def test_preserves_pre_blocks(self):
        t = PrettifyHtmlTransformer("prettify_html")
        html = "<div><pre>  keep  spacing  </pre></div>"
        result = t.transform(html)
        assert "  keep  spacing  " in result.value


# ── Plugin registration ──────────────────────────────────────────────────


class TestMinifyPlugin:
    def test_plugin_name(self):
        plugin = MinifyPlugin()
        assert plugin.name == "minify"

    def test_has_all_transformers(self):
        plugin = MinifyPlugin()
        names = set(plugin.transformers.keys())
        assert names == {"minify_html", "minify_css", "minify_js", "prettify_html"}


# ── Integration tests via TukuyTransformer ────────────────────────────────


class TestMinifyIntegration:
    def test_minify_html(self, transformer):
        html = "<div>  <!-- comment -->  <p>text</p>  </div>"
        result = transformer.transform(html, ["minify_html"])
        assert "<!-- comment -->" not in result

    def test_minify_css(self, transformer):
        css = "body { color: red; }"
        result = transformer.transform(css, ["minify_css"])
        assert "color:red" in result

    def test_minify_js(self, transformer):
        js = "var x = 1; // comment"
        result = transformer.transform(js, ["minify_js"])
        assert "// comment" not in result
