"""Tests for the HTML Validation plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.html_validate import (
    HtmlValidatePlugin,
    ValidateHtmlTransformer,
    ValidateAccessibilityTransformer,
)


@pytest.fixture
def transformer():
    return TukuyTransformer()


GOOD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Test Page</title>
</head>
<body>
    <a href="#main">Skip to main</a>
    <header><nav><a href="/">Home</a></nav></header>
    <main id="main">
        <h1>Welcome</h1>
        <h2>Section</h2>
        <p>Content here.</p>
        <img src="photo.jpg" alt="A photo">
    </main>
    <footer><p>Footer</p></footer>
</body>
</html>"""

BAD_HTML = """<html>
<head></head>
<body>
    <h3>Skipped headings</h3>
    <img src="photo.jpg">
    <input type="text">
    <a href="#">click here</a>
</body>
</html>"""


# ── ValidateHtmlTransformer ──────────────────────────────────────────────


class TestValidateHtml:
    def test_valid_html(self):
        t = ValidateHtmlTransformer("validate_html")
        result = t.transform(GOOD_HTML)
        assert result.value["valid"] is True
        assert len(result.value["errors"]) == 0

    def test_unclosed_tags(self):
        t = ValidateHtmlTransformer("validate_html")
        result = t.transform("<div><p>text</div>")
        assert result.value["valid"] is False
        unclosed = [e for e in result.value["errors"] if "Unclosed" in e]
        assert len(unclosed) > 0

    def test_missing_doctype(self):
        t = ValidateHtmlTransformer("validate_html")
        result = t.transform("<html><body></body></html>")
        assert any("DOCTYPE" in w for w in result.value["warnings"])

    def test_missing_lang(self):
        t = ValidateHtmlTransformer("validate_html")
        result = t.transform("<!DOCTYPE html><html><head><title>T</title></head><body></body></html>")
        assert any("lang" in w for w in result.value["warnings"])

    def test_missing_title(self):
        t = ValidateHtmlTransformer("validate_html")
        result = t.transform("<!DOCTYPE html><html><head></head><body></body></html>")
        assert any("title" in w.lower() for w in result.value["warnings"])

    def test_missing_charset(self):
        t = ValidateHtmlTransformer("validate_html")
        result = t.transform("<!DOCTYPE html><html><head><title>T</title></head><body></body></html>")
        assert any("charset" in w for w in result.value["warnings"])

    def test_stats(self):
        t = ValidateHtmlTransformer("validate_html")
        result = t.transform(GOOD_HTML)
        assert result.value["stats"]["total_tags"] > 0

    def test_void_elements_dont_need_closing(self):
        t = ValidateHtmlTransformer("validate_html")
        html = "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><title>T</title></head><body><br><hr><img src='x' alt='x'></body></html>"
        result = t.transform(html)
        assert result.value["valid"] is True


# ── ValidateAccessibilityTransformer ─────────────────────────────────────


class TestValidateAccessibility:
    def test_good_html_scores_high(self):
        t = ValidateAccessibilityTransformer("validate_accessibility")
        result = t.transform(GOOD_HTML)
        assert result.value["score"] >= 70
        assert len(result.value["passes"]) > 0

    def test_missing_alt(self):
        t = ValidateAccessibilityTransformer("validate_accessibility")
        result = t.transform('<img src="photo.jpg">')
        issues = [i for i in result.value["issues"] if i["rule"] == "img-alt"]
        assert len(issues) > 0

    def test_alt_present(self):
        t = ValidateAccessibilityTransformer("validate_accessibility")
        result = t.transform('<img src="photo.jpg" alt="A photo">')
        assert any("alt" in p.lower() for p in result.value["passes"])

    def test_heading_skip(self):
        t = ValidateAccessibilityTransformer("validate_accessibility")
        result = t.transform("<h1>Title</h1><h3>Skipped</h3>")
        issues = [i for i in result.value["issues"] if i["rule"] == "heading-order"]
        assert len(issues) > 0

    def test_heading_starts_at_h3(self):
        t = ValidateAccessibilityTransformer("validate_accessibility")
        result = t.transform("<h3>Wrong start</h3>")
        issues = [i for i in result.value["issues"] if i["rule"] == "heading-order"]
        assert any("h3" in i["message"] for i in issues)

    def test_non_descriptive_link(self):
        t = ValidateAccessibilityTransformer("validate_accessibility")
        result = t.transform('<a href="#">click here</a>')
        issues = [i for i in result.value["issues"] if i["rule"] == "link-name"]
        assert len(issues) > 0

    def test_missing_main_landmark(self):
        t = ValidateAccessibilityTransformer("validate_accessibility")
        result = t.transform("<div>content</div>")
        issues = [i for i in result.value["issues"] if i["rule"] == "landmark-main"]
        assert len(issues) > 0

    def test_missing_viewport(self):
        t = ValidateAccessibilityTransformer("validate_accessibility")
        result = t.transform("<html><body></body></html>")
        issues = [i for i in result.value["issues"] if i["rule"] == "viewport"]
        assert len(issues) > 0

    def test_bad_html_low_score(self):
        t = ValidateAccessibilityTransformer("validate_accessibility")
        result = t.transform(BAD_HTML)
        assert result.value["score"] < 50
        assert len(result.value["issues"]) >= 3


# ── Plugin registration ──────────────────────────────────────────────────


class TestHtmlValidatePlugin:
    def test_plugin_name(self):
        plugin = HtmlValidatePlugin()
        assert plugin.name == "html_validate"

    def test_has_all_transformers(self):
        plugin = HtmlValidatePlugin()
        names = set(plugin.transformers.keys())
        assert names == {"validate_html", "validate_accessibility"}


# ── Integration tests via TukuyTransformer ────────────────────────────────


class TestHtmlValidateIntegration:
    def test_validate_html(self, transformer):
        result = transformer.transform(GOOD_HTML, ["validate_html"])
        assert result["valid"] is True

    def test_validate_accessibility(self, transformer):
        result = transformer.transform(GOOD_HTML, ["validate_accessibility"])
        assert result["score"] >= 70
