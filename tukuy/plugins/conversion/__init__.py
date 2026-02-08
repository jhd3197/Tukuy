"""Data conversion plugin.

Provides transformers for converting between CSV, JSON, YAML, TOML,
Markdown, and HTML formats.

CSV and Markdown conversions use stdlib only.
YAML requires ``pyyaml`` (optional, fails gracefully at runtime).
TOML uses ``tomllib`` (Python 3.11+) or ``tomli`` (fallback).
"""

import csv
import io
import json
import re
from typing import Any, Dict, List, Optional, Union

from ...base import ChainableTransformer
from ...types import TransformContext
from ...exceptions import TransformationError
from ...plugins.base import TransformerPlugin


class CsvToJsonTransformer(ChainableTransformer[str, str]):
    """Convert a CSV string to a JSON array of objects."""

    def __init__(self, name: str, delimiter: str = ","):
        super().__init__(name)
        self.delimiter = delimiter

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        reader = csv.DictReader(io.StringIO(value), delimiter=self.delimiter)
        rows = list(reader)
        return json.dumps(rows, ensure_ascii=False)


class JsonToCsvTransformer(ChainableTransformer[str, str]):
    """Convert a JSON array of objects to a CSV string."""

    def __init__(self, name: str, delimiter: str = ","):
        super().__init__(name)
        self.delimiter = delimiter

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        data = json.loads(value)
        if not isinstance(data, list) or not data:
            raise TransformationError("Expected a non-empty JSON array of objects", value)
        fieldnames = list(data[0].keys())
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=fieldnames, delimiter=self.delimiter)
        writer.writeheader()
        writer.writerows(data)
        return out.getvalue().strip()


class YamlToJsonTransformer(ChainableTransformer[str, str]):
    """Convert a YAML string to JSON. Requires ``pyyaml``."""

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        try:
            import yaml
        except ImportError:
            raise TransformationError(
                "pyyaml is required for yaml_to_json. Install with: pip install pyyaml",
                value,
            )
        data = yaml.safe_load(value)
        return json.dumps(data, ensure_ascii=False)


class JsonToYamlTransformer(ChainableTransformer[str, str]):
    """Convert a JSON string to YAML. Requires ``pyyaml``."""

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        try:
            import yaml
        except ImportError:
            raise TransformationError(
                "pyyaml is required for json_to_yaml. Install with: pip install pyyaml",
                value,
            )
        data = json.loads(value)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True).strip()


class MarkdownToHtmlTransformer(ChainableTransformer[str, str]):
    """Convert a subset of Markdown to HTML using regex (no external deps).

    Supports: headings, bold, italic, code, code blocks, links, images,
    unordered lists, horizontal rules, and paragraphs.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        text = value

        # Code blocks (``` ... ```)
        text = re.sub(
            r"```(\w*)\n(.*?)\n```",
            lambda m: f"<pre><code>{m.group(2)}</code></pre>",
            text,
            flags=re.DOTALL,
        )

        # Inline code
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

        # Headings
        for level in range(6, 0, -1):
            pattern = r"^{} (.+)$".format("#" * level)
            text = re.sub(pattern, rf"<h{level}>\1</h{level}>", text, flags=re.MULTILINE)

        # Bold
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)

        # Italic
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)

        # Images (before links)
        text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', text)

        # Links
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

        # Unordered lists
        text = re.sub(
            r"((?:^[*\-+] .+$\n?)+)",
            lambda m: "<ul>\n"
            + "".join(
                f"<li>{line.lstrip('*-+ ')}</li>\n"
                for line in m.group(0).strip().split("\n")
            )
            + "</ul>",
            text,
            flags=re.MULTILINE,
        )

        # Horizontal rules
        text = re.sub(r"^---+$", "<hr>", text, flags=re.MULTILINE)

        # Paragraphs: wrap remaining loose lines
        lines = text.split("\n")
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("<"):
                result.append(f"<p>{stripped}</p>")
            else:
                result.append(line)
        text = "\n".join(result)

        return text.strip()


class HtmlToMarkdownTransformer(ChainableTransformer[str, str]):
    """Convert basic HTML to Markdown using regex (no external deps)."""

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        text = value

        # Code blocks
        text = re.sub(r"<pre><code>(.*?)</code></pre>", r"```\n\1\n```", text, flags=re.DOTALL)

        # Inline code
        text = re.sub(r"<code>([^<]+)</code>", r"`\1`", text)

        # Headings
        for level in range(1, 7):
            prefix = "#" * level
            text = re.sub(
                rf"<h{level}[^>]*>(.*?)</h{level}>",
                rf"{prefix} \1",
                text,
                flags=re.DOTALL,
            )

        # Bold
        text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.DOTALL)
        text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.DOTALL)

        # Italic
        text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.DOTALL)
        text = re.sub(r"<i>(.*?)</i>", r"*\1*", text, flags=re.DOTALL)

        # Images
        text = re.sub(r'<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"[^>]*/?\s*>', r"![\2](\1)", text)
        text = re.sub(r'<img[^>]+alt="([^"]*)"[^>]*src="([^"]+)"[^>]*/?\s*>', r"![\1](\2)", text)

        # Links
        text = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.DOTALL)

        # List items
        text = re.sub(r"<li>(.*?)</li>", r"- \1", text, flags=re.DOTALL)
        text = re.sub(r"</?[uo]l>", "", text)

        # Horizontal rules
        text = re.sub(r"<hr\s*/?>", "---", text)

        # Paragraphs
        text = re.sub(r"<p>(.*?)</p>", r"\1\n", text, flags=re.DOTALL)

        # Line breaks
        text = re.sub(r"<br\s*/?>", "\n", text)

        # Strip remaining tags
        text = re.sub(r"<[^>]+>", "", text)

        # Clean up excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()


class TomlToJsonTransformer(ChainableTransformer[str, str]):
    """Convert a TOML string to JSON.

    Uses ``tomllib`` (Python 3.11+) or ``tomli`` as a fallback.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError:
                raise TransformationError(
                    "tomllib (Python 3.11+) or tomli is required for toml_to_json. "
                    "Install with: pip install tomli",
                    value,
                )
        data = tomllib.loads(value)
        return json.dumps(data, ensure_ascii=False)


class ConversionPlugin(TransformerPlugin):
    """Plugin providing data format conversion transformers."""

    def __init__(self):
        super().__init__("conversion")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "csv_to_json": lambda params: CsvToJsonTransformer(
                "csv_to_json",
                delimiter=params.get("delimiter", ","),
            ),
            "json_to_csv": lambda params: JsonToCsvTransformer(
                "json_to_csv",
                delimiter=params.get("delimiter", ","),
            ),
            "yaml_to_json": lambda _: YamlToJsonTransformer("yaml_to_json"),
            "json_to_yaml": lambda _: JsonToYamlTransformer("json_to_yaml"),
            "markdown_to_html": lambda _: MarkdownToHtmlTransformer("markdown_to_html"),
            "html_to_markdown": lambda _: HtmlToMarkdownTransformer("html_to_markdown"),
            "toml_to_json": lambda _: TomlToJsonTransformer("toml_to_json"),
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest
        return PluginManifest(
            name="conversion",
            display_name="Data Conversion",
            description="Convert between CSV, JSON, YAML, TOML, Markdown, and HTML formats.",
            icon="arrow-right-left",
            group="Core",
        )
