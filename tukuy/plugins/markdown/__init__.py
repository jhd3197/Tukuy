"""Markdown analysis plugin.

Provides transformers for extracting structured data from Markdown:
frontmatter, headings/TOC, links, tables, and basic linting.

Pure stdlib — no external dependencies.
"""

import json
import re
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


class ExtractFrontmatterTransformer(ChainableTransformer[str, dict]):
    """Extract YAML frontmatter from a Markdown document.

    Returns ``{"frontmatter": {...}, "content": "..."}``.
    If no frontmatter is found, ``frontmatter`` is an empty dict.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        # Match --- delimited frontmatter at start of document
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", value, re.DOTALL)
        if not match:
            return {"frontmatter": {}, "content": value}

        raw_fm = match.group(1)
        content = match.group(2)

        # Simple YAML-like parser for common frontmatter (key: value pairs)
        fm: Dict[str, Any] = {}
        for line in raw_fm.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip()
                # Remove surrounding quotes
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                    val = val[1:-1]
                # Try to parse simple types
                if val.lower() in ("true", "yes"):
                    fm[key] = True
                elif val.lower() in ("false", "no"):
                    fm[key] = False
                elif re.match(r"^-?\d+$", val):
                    fm[key] = int(val)
                elif re.match(r"^-?\d+\.\d+$", val):
                    fm[key] = float(val)
                elif val.startswith("[") and val.endswith("]"):
                    # Simple inline list: [a, b, c]
                    items = [i.strip().strip("\"'") for i in val[1:-1].split(",")]
                    fm[key] = [i for i in items if i]
                else:
                    fm[key] = val

        return {"frontmatter": fm, "content": content}


class ExtractHeadingsTransformer(ChainableTransformer[str, list]):
    """Extract all headings from Markdown, producing a TOC-like structure.

    Returns a list of ``{"level": int, "text": str, "slug": str}``.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> list:
        headings = []
        # Skip code blocks
        text = re.sub(r"```.*?```", "", value, flags=re.DOTALL)

        for match in re.finditer(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE):
            level = len(match.group(1))
            raw_text = match.group(2).strip()
            # Strip inline formatting for slug
            slug = re.sub(r"[^\w\s-]", "", raw_text.lower())
            slug = re.sub(r"[\s]+", "-", slug).strip("-")
            headings.append({"level": level, "text": raw_text, "slug": slug})

        return headings


class ExtractLinksTransformer(ChainableTransformer[str, list]):
    """Extract all links from Markdown.

    Returns a list of ``{"text": str, "url": str, "type": str}``.
    Type is "inline", "reference", or "autolink".
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> list:
        links: List[Dict[str, str]] = []
        # Skip code blocks
        text = re.sub(r"```.*?```", "", value, flags=re.DOTALL)

        # Inline links: [text](url)
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            links.append({"text": m.group(1), "url": m.group(2), "type": "inline"})

        # Reference links: [text][ref]
        for m in re.finditer(r"\[([^\]]+)\]\[([^\]]+)\]", text):
            links.append({"text": m.group(1), "url": m.group(2), "type": "reference"})

        # Autolinks: <url>
        for m in re.finditer(r"<(https?://[^>]+)>", text):
            links.append({"text": m.group(1), "url": m.group(1), "type": "autolink"})

        # Bare URLs
        for m in re.finditer(r"(?<![(<\[])https?://[^\s)\]>]+", text):
            url = m.group(0)
            # Avoid duplicating inline link URLs
            if not any(l["url"] == url for l in links):
                links.append({"text": url, "url": url, "type": "autolink"})

        return links


class ExtractTablesTransformer(ChainableTransformer[str, list]):
    """Extract Markdown tables as lists of dicts.

    Returns a list of tables, each being a list of row-dicts keyed by
    header names.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> list:
        tables: List[List[Dict[str, str]]] = []

        # Match table blocks: header row, separator row, data rows
        table_pattern = re.compile(
            r"^(\|.+\|)\s*\n(\|[-:| ]+\|)\s*\n((?:\|.+\|\s*\n?)+)",
            re.MULTILINE,
        )

        for m in table_pattern.finditer(value):
            header_line = m.group(1).strip()
            data_block = m.group(3).strip()

            headers = [h.strip() for h in header_line.strip("|").split("|")]

            rows = []
            for row_line in data_block.splitlines():
                row_line = row_line.strip()
                if not row_line:
                    continue
                cells = [c.strip() for c in row_line.strip("|").split("|")]
                row = {}
                for i, header in enumerate(headers):
                    row[header] = cells[i] if i < len(cells) else ""
                rows.append(row)

            tables.append(rows)

        return tables


class MarkdownLintTransformer(ChainableTransformer[str, dict]):
    """Basic Markdown linting.

    Checks for common issues:
    - Multiple top-level headings
    - Heading level skips (e.g. h1 -> h3)
    - Trailing whitespace
    - Missing blank line before headings
    - Long lines (configurable)
    - Consecutive blank lines

    Returns ``{"issues": [...], "issue_count": int, "pass": bool}``.
    """

    def __init__(self, name: str, max_line_length: int = 120):
        super().__init__(name)
        self.max_line_length = max_line_length

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        issues: List[Dict[str, Any]] = []
        lines = value.split("\n")

        h1_count = 0
        prev_heading_level = 0
        prev_line_blank = True
        consecutive_blanks = 0

        for i, line in enumerate(lines, 1):
            # Trailing whitespace
            if line != line.rstrip():
                issues.append({"line": i, "rule": "trailing-whitespace", "message": "Trailing whitespace"})

            # Long lines (skip code blocks and URLs)
            if len(line) > self.max_line_length and not line.strip().startswith("```") and "http" not in line:
                issues.append({
                    "line": i,
                    "rule": "line-length",
                    "message": f"Line length {len(line)} exceeds {self.max_line_length}",
                })

            # Consecutive blank lines
            if line.strip() == "":
                consecutive_blanks += 1
                if consecutive_blanks > 1:
                    issues.append({"line": i, "rule": "consecutive-blanks", "message": "Multiple consecutive blank lines"})
                prev_line_blank = True
                continue
            else:
                consecutive_blanks = 0

            # Heading checks
            heading_match = re.match(r"^(#{1,6})\s+", line)
            if heading_match:
                level = len(heading_match.group(1))

                if level == 1:
                    h1_count += 1
                    if h1_count > 1:
                        issues.append({"line": i, "rule": "multiple-h1", "message": "Multiple top-level headings"})

                if prev_heading_level > 0 and level > prev_heading_level + 1:
                    issues.append({
                        "line": i,
                        "rule": "heading-skip",
                        "message": f"Heading level skipped from h{prev_heading_level} to h{level}",
                    })

                if not prev_line_blank and i > 1:
                    issues.append({
                        "line": i,
                        "rule": "no-blank-before-heading",
                        "message": "Missing blank line before heading",
                    })

                prev_heading_level = level

            prev_line_blank = False

        return {
            "issues": issues,
            "issue_count": len(issues),
            "pass": len(issues) == 0,
        }


class MarkdownPlugin(TransformerPlugin):
    """Plugin providing Markdown analysis transformers."""

    def __init__(self):
        super().__init__("markdown")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "extract_frontmatter": lambda _: ExtractFrontmatterTransformer("extract_frontmatter"),
            "extract_headings": lambda _: ExtractHeadingsTransformer("extract_headings"),
            "extract_links": lambda _: ExtractLinksTransformer("extract_links"),
            "extract_tables": lambda _: ExtractTablesTransformer("extract_tables"),
            "markdown_lint": lambda params: MarkdownLintTransformer(
                "markdown_lint",
                max_line_length=params.get("max_line_length", 120),
            ),
        }
