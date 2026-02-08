"""Minification and prettification plugin.

Provides transformers for minifying HTML, CSS, and JavaScript, plus
a basic HTML prettifier.

Pure stdlib — no external dependencies (regex-based).
"""

import re
from typing import Any, Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


class MinifyHtmlTransformer(ChainableTransformer[str, str]):
    """Minify HTML by removing comments, collapsing whitespace, and
    removing optional attributes.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        text = value

        # Preserve <pre>, <code>, <script>, <style> blocks
        preserved = {}
        counter = 0
        for tag in ("pre", "code", "script", "style", "textarea"):
            for match in re.finditer(
                rf"(<{tag}[^>]*>)([\s\S]*?)(</{tag}>)", text, re.IGNORECASE
            ):
                placeholder = f"\x00PRESERVE{counter}\x00"
                preserved[placeholder] = match.group(0)
                text = text.replace(match.group(0), placeholder, 1)
                counter += 1

        # Remove HTML comments (but keep conditional comments)
        text = re.sub(r"<!--(?!\[if)[\s\S]*?-->", "", text)

        # Collapse whitespace between tags
        text = re.sub(r">\s+<", "><", text)

        # Collapse multiple whitespace to single space
        text = re.sub(r"\s{2,}", " ", text)

        # Remove whitespace around = in attributes
        text = re.sub(r"\s*=\s*", "=", text)

        # Remove optional quotes around simple attribute values
        text = re.sub(r'=(["\'])([a-zA-Z0-9_-]+)\1', r"=\2", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        # Restore preserved blocks
        for placeholder, original in preserved.items():
            text = text.replace(placeholder, original)

        return text


class MinifyCssTransformer(ChainableTransformer[str, str]):
    """Minify CSS by removing comments, whitespace, and redundant semicolons."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        text = value

        # Remove CSS comments
        text = re.sub(r"/\*[\s\S]*?\*/", "", text)

        # Remove newlines and excess whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove space around punctuation
        text = re.sub(r"\s*{\s*", "{", text)
        text = re.sub(r"\s*}\s*", "}", text)
        text = re.sub(r"\s*;\s*", ";", text)
        text = re.sub(r"\s*:\s*", ":", text)
        text = re.sub(r"\s*,\s*", ",", text)

        # Remove last semicolons before }
        text = re.sub(r";}", "}", text)

        # Remove space around selectors
        text = re.sub(r"\s*>\s*", ">", text)
        text = re.sub(r"\s*\+\s*", "+", text)
        text = re.sub(r"\s*~\s*", "~", text)

        return text.strip()


class MinifyJsTransformer(ChainableTransformer[str, str]):
    """Basic JavaScript minification.

    Removes single-line comments, multi-line comments, and excess whitespace.
    This is a basic minifier — it does not perform AST-level optimizations.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        text = value

        # Preserve strings (single-quoted, double-quoted, template literals)
        strings = {}
        counter = 0

        def preserve_string(match):
            nonlocal counter
            placeholder = f"\x00STR{counter}\x00"
            strings[placeholder] = match.group(0)
            counter += 1
            return placeholder

        # Preserve regex literals, template literals, and quoted strings
        text = re.sub(r'`[\s\S]*?`', preserve_string, text)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', preserve_string, text)
        text = re.sub(r"'(?:[^'\\]|\\.)*'", preserve_string, text)

        # Remove single-line comments
        text = re.sub(r"//[^\n]*", "", text)

        # Remove multi-line comments
        text = re.sub(r"/\*[\s\S]*?\*/", "", text)

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove space around operators and punctuation
        text = re.sub(r"\s*([{}();\[\],=+\-*/<>!&|?:])\s*", r"\1", text)

        # Restore a single space where needed (before keywords after })
        text = re.sub(r"}(else|catch|finally|while)", r"} \1", text)

        # Restore strings
        for placeholder, original in strings.items():
            text = text.replace(placeholder, original)

        return text.strip()


class PrettifyHtmlTransformer(ChainableTransformer[str, str]):
    """Prettify (format) HTML with proper indentation.

    Adds newlines and indentation for readability.
    """

    def __init__(self, name: str, indent: str = "  "):
        super().__init__(name)
        self.indent = indent

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        # Inline elements that shouldn't get their own line
        inline_tags = frozenset({
            "a", "abbr", "b", "bdi", "bdo", "br", "cite", "code", "data",
            "em", "i", "kbd", "mark", "q", "s", "samp", "small", "span",
            "strong", "sub", "sup", "time", "u", "var", "wbr",
        })

        # Void elements
        void_tags = frozenset({
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr",
        })

        # Pre-formatted tags to preserve as-is
        pre_tags = frozenset({"pre", "code", "script", "style", "textarea"})

        # Preserve pre-formatted blocks
        preserved = {}
        counter = 0
        text = value
        for tag in pre_tags:
            for match in re.finditer(
                rf"(<{tag}[^>]*>)([\s\S]*?)(</{tag}>)", text, re.IGNORECASE
            ):
                placeholder = f"\x00PRETTY{counter}\x00"
                preserved[placeholder] = match.group(0)
                text = text.replace(match.group(0), placeholder, 1)
                counter += 1

        # Normalize whitespace
        text = re.sub(r">\s+<", ">\n<", text)
        text = re.sub(r"\s+", " ", text)

        # Add newlines around block tags
        text = re.sub(r"(<(?!/)(?!(?:" + "|".join(inline_tags) + r")\b)(\w+)[^>]*>)", r"\n\1", text)
        text = re.sub(r"(</(?!(?:" + "|".join(inline_tags) + r")\b)(\w+)>)", r"\1\n", text)

        # Now indent
        lines = text.split("\n")
        result = []
        depth = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check if this is a closing tag
            is_close = stripped.startswith("</")
            # Check if this is a self-closing or void tag
            tag_match = re.match(r"</?(\w+)", stripped)
            tag_name = tag_match.group(1).lower() if tag_match else ""
            is_void = tag_name in void_tags
            is_self_closing = stripped.endswith("/>")

            if is_close:
                depth = max(0, depth - 1)

            result.append(self.indent * depth + stripped)

            if (
                not is_close
                and not is_void
                and not is_self_closing
                and tag_match
                and stripped.startswith("<")
                and not stripped.startswith("<!")
                and tag_name not in inline_tags
            ):
                depth += 1

        text = "\n".join(result)

        # Restore preserved blocks
        for placeholder, original in preserved.items():
            text = text.replace(placeholder, original)

        return text.strip()


class MinifyPlugin(TransformerPlugin):
    """Plugin providing minification and prettification transformers."""

    def __init__(self):
        super().__init__("minify")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "minify_html": lambda _: MinifyHtmlTransformer("minify_html"),
            "minify_css": lambda _: MinifyCssTransformer("minify_css"),
            "minify_js": lambda _: MinifyJsTransformer("minify_js"),
            "prettify_html": lambda params: PrettifyHtmlTransformer(
                "prettify_html",
                indent=params.get("indent", "  "),
            ),
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest
        return PluginManifest(
            name="minify",
            display_name="Minify",
            description="Minify and prettify HTML, CSS, and JavaScript.",
            icon="minimize",
            group="Web",
        )
