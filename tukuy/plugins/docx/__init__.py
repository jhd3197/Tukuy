"""Word document (DOCX) processing plugin.

Provides reading, writing, and conversion of Word documents.

Requires ``python-docx`` (optional, fails gracefully at runtime).
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...skill import skill


# ── Transformers ──────────────────────────────────────────────────────────

class DocxToTextTransformer(ChainableTransformer[str, str]):
    """Extract plain text from a DOCX file.

    Input is a file path. Returns all paragraph text concatenated.
    Requires ``python-docx``.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        try:
            from docx import Document
        except ImportError:
            return "[error] python-docx is required. Install with: pip install python-docx"

        doc = Document(value)
        parts = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                parts.append(text)

        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                parts.append(" | ".join(cells))

        return "\n\n".join(parts)


class DocxToMarkdownTransformer(ChainableTransformer[str, str]):
    """Convert a DOCX file to Markdown.

    Input is a file path. Converts headings, bold, italic, lists, and
    tables to Markdown syntax.
    Requires ``python-docx``.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        try:
            from docx import Document
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            return "[error] python-docx is required. Install with: pip install python-docx"

        doc = Document(value)
        md_parts: List[str] = []

        for para in doc.paragraphs:
            style_name = (para.style.name or "").lower()
            text = self._convert_runs(para)

            if not text.strip():
                md_parts.append("")
                continue

            # Headings
            if style_name.startswith("heading"):
                try:
                    level = int(style_name.replace("heading", "").strip())
                except ValueError:
                    level = 1
                md_parts.append(f"{'#' * level} {text}")
            # List items
            elif style_name.startswith("list"):
                md_parts.append(f"- {text}")
            elif para.style.name == "List Number" or "number" in style_name:
                md_parts.append(f"1. {text}")
            else:
                md_parts.append(text)

        # Tables
        for table in doc.tables:
            if not table.rows:
                continue
            # Header row
            headers = [cell.text.strip() for cell in table.rows[0].cells]
            md_parts.append("| " + " | ".join(headers) + " |")
            md_parts.append("| " + " | ".join("---" for _ in headers) + " |")
            # Data rows
            for row in table.rows[1:]:
                cells = [cell.text.strip() for cell in row.cells]
                md_parts.append("| " + " | ".join(cells) + " |")
            md_parts.append("")

        return "\n".join(md_parts)

    @staticmethod
    def _convert_runs(para) -> str:
        """Convert paragraph runs to Markdown, preserving bold/italic."""
        parts = []
        for run in para.runs:
            text = run.text
            if not text:
                continue
            if run.bold and run.italic:
                text = f"***{text}***"
            elif run.bold:
                text = f"**{text}**"
            elif run.italic:
                text = f"*{text}*"
            parts.append(text)
        # Fallback if no runs
        if not parts:
            return para.text
        return "".join(parts)


class DocxExtractMetadataTransformer(ChainableTransformer[str, dict]):
    """Extract metadata from a DOCX file.

    Input is a file path. Returns title, author, dates, word count, etc.
    Requires ``python-docx``.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        try:
            from docx import Document
        except ImportError:
            return {"error": "python-docx is required. Install with: pip install python-docx"}

        doc = Document(value)
        props = doc.core_properties

        # Count words
        word_count = 0
        para_count = 0
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                para_count += 1
                word_count += len(text.split())

        return {
            "path": value,
            "title": props.title or "",
            "author": props.author or "",
            "subject": props.subject or "",
            "keywords": props.keywords or "",
            "created": str(props.created) if props.created else "",
            "modified": str(props.modified) if props.modified else "",
            "last_modified_by": props.last_modified_by or "",
            "revision": props.revision,
            "paragraph_count": para_count,
            "word_count": word_count,
            "table_count": len(doc.tables),
        }


# ── Skills ────────────────────────────────────────────────────────────────

@skill(
    name="docx_read",
    description="Read a Word document and return its text, structure, and metadata.",
    category="docx",
    tags=["docx", "word", "document"],
    idempotent=True,
    requires_filesystem=True,
    required_imports=["docx"],
)
def docx_read(path: str) -> dict:
    """Read a Word document."""
    p = Path(path)
    if not p.exists():
        return {"path": path, "error": "File not found", "exists": False}

    try:
        from docx import Document
    except ImportError:
        return {"error": "python-docx is required. Install with: pip install python-docx"}

    doc = Document(path)
    props = doc.core_properties

    paragraphs = []
    word_count = 0
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            style = para.style.name or "Normal"
            paragraphs.append({"text": text, "style": style})
            word_count += len(text.split())

    tables = []
    for table in doc.tables:
        if not table.rows:
            continue
        headers = [cell.text.strip() for cell in table.rows[0].cells]
        rows = []
        for row in table.rows[1:]:
            row_dict = {}
            for i, cell in enumerate(row.cells):
                key = headers[i] if i < len(headers) else f"col_{i}"
                row_dict[key] = cell.text.strip()
            rows.append(row_dict)
        tables.append({"headers": headers, "rows": rows, "row_count": len(rows)})

    return {
        "path": path,
        "exists": True,
        "title": props.title or "",
        "author": props.author or "",
        "paragraphs": paragraphs,
        "paragraph_count": len(paragraphs),
        "word_count": word_count,
        "tables": tables,
        "table_count": len(tables),
    }


@skill(
    name="docx_write",
    description="Create a Word document from structured content (headings, paragraphs, lists, tables).",
    category="docx",
    tags=["docx", "word", "document"],
    side_effects=True,
    requires_filesystem=True,
    required_imports=["docx"],
)
def docx_write(
    path: str,
    content: list,
    title: str = "",
    author: str = "",
) -> dict:
    """Create a Word document from structured content.

    ``content`` is a list of blocks, each a dict with "type" and type-specific fields:
      - {"type": "heading", "text": "...", "level": 1}
      - {"type": "paragraph", "text": "..."}
      - {"type": "list", "items": ["...", "..."]}
      - {"type": "table", "headers": [...], "rows": [[...], ...]}
    """
    try:
        from docx import Document
    except ImportError:
        return {"error": "python-docx is required. Install with: pip install python-docx"}

    doc = Document()

    if title:
        doc.core_properties.title = title
    if author:
        doc.core_properties.author = author

    for block in content:
        block_type = block.get("type", "paragraph")

        if block_type == "heading":
            level = block.get("level", 1)
            doc.add_heading(block.get("text", ""), level=level)

        elif block_type == "paragraph":
            doc.add_paragraph(block.get("text", ""))

        elif block_type == "list":
            for item in block.get("items", []):
                doc.add_paragraph(item, style="List Bullet")

        elif block_type == "table":
            headers = block.get("headers", [])
            rows = block.get("rows", [])
            if headers:
                table = doc.add_table(rows=1, cols=len(headers))
                table.style = "Table Grid"
                # Header row
                for i, header in enumerate(headers):
                    table.rows[0].cells[i].text = str(header)
                # Data rows
                for row_data in rows:
                    row = table.add_row()
                    for i, cell_val in enumerate(row_data if isinstance(row_data, (list, tuple)) else row_data.values()):
                        if i < len(headers):
                            row.cells[i].text = str(cell_val)

    doc.save(path)
    return {
        "path": path,
        "blocks_written": len(content),
        "title": title,
        "success": True,
    }


class DocxPlugin(TransformerPlugin):
    """Plugin providing Word document processing."""

    def __init__(self):
        super().__init__("docx")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "docx_to_text": lambda _: DocxToTextTransformer("docx_to_text"),
            "docx_to_markdown": lambda _: DocxToMarkdownTransformer("docx_to_markdown"),
            "docx_extract_metadata": lambda _: DocxExtractMetadataTransformer("docx_extract_metadata"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "docx_read": docx_read.__skill__,
            "docx_write": docx_write.__skill__,
        }
