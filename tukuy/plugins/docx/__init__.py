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
from ...safety import check_read_path, check_write_path
from ...skill import skill, ConfigParam, ConfigScope, RiskLevel


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
    display_name="Read Document",
    icon="file-text",
    risk_level=RiskLevel.SAFE,
    group="Word",
)
def docx_read(path: str) -> dict:
    """Read a Word document."""
    path = check_read_path(path)
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
    display_name="Create Document",
    icon="file-plus",
    risk_level=RiskLevel.MODERATE,
    group="Word",
    config_params=[
        ConfigParam(
            name="default_author",
            display_name="Default Author",
            description="Author name set in document metadata when not specified.",
            type="string",
            placeholder="Author Name",
        ),
    ],
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
    path = check_write_path(path)
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


@skill(
    name="pdf_to_docx",
    description="Convert a PDF file to a Word document, preserving text and tables.",
    category="conversion",
    tags=["pdf", "docx", "word", "convert", "document"],
    side_effects=True,
    requires_filesystem=True,
    required_imports=["pypdf", "docx"],
    display_name="PDF to Word",
    icon="file-arrow-right",
    risk_level=RiskLevel.MODERATE,
    group="Word",
)
def pdf_to_docx(
    input: str,
    output: str = "",
    title: str = "",
    author: str = "",
) -> dict:
    """Convert a PDF file to a Word (.docx) document.

    Args:
        input: Path to the source PDF file.
        output: Path for the output .docx file (defaults to same name with .docx extension).
        title: Optional document title for the Word file metadata.
        author: Optional author for the Word file metadata.
    """
    input = check_read_path(input)
    p = Path(input)
    if not p.exists():
        return {"error": f"File not found: {input}"}

    if not output:
        output = str(p.with_suffix(".docx"))
    output = check_write_path(output)

    # --- Read PDF ---
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore[no-redef]
        except ImportError:
            return {"error": "pypdf is required. Install with: pip install pypdf"}

    try:
        from docx import Document
    except ImportError:
        return {"error": "python-docx is required. Install with: pip install python-docx"}

    reader = PdfReader(input)
    doc = Document()

    # Metadata
    pdf_meta = reader.metadata
    doc_title = title or (pdf_meta.get("/Title", "") if pdf_meta else "") or ""
    doc_author = author or (pdf_meta.get("/Author", "") if pdf_meta else "") or ""
    if doc_title:
        doc.core_properties.title = doc_title
    if doc_author:
        doc.core_properties.author = doc_author

    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if not text.strip():
            continue

        # Split text into paragraphs and add to doc
        paragraphs = [line.strip() for line in text.split("\n") if line.strip()]
        for para_text in paragraphs:
            doc.add_paragraph(para_text)

        # Page separator (except last page)
        if i < total_pages - 1:
            doc.add_page_break()

    # --- Extract tables via pdfplumber if available ---
    tables_extracted = 0
    try:
        import pdfplumber

        with pdfplumber.open(input) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables() or []
                for table_data in page_tables:
                    if not table_data or len(table_data) < 2:
                        continue
                    headers = [str(h or "").strip() for h in table_data[0]]
                    table = doc.add_table(rows=1, cols=len(headers))
                    table.style = "Table Grid"
                    for j, header in enumerate(headers):
                        table.rows[0].cells[j].text = header
                    for row_data in table_data[1:]:
                        row = table.add_row()
                        for j, cell_val in enumerate(row_data):
                            if j < len(headers):
                                row.cells[j].text = str(cell_val or "").strip()
                    tables_extracted += 1
    except ImportError:
        pass  # pdfplumber not installed — skip table extraction

    doc.save(output)

    return {
        "input": input,
        "output": output,
        "pages_converted": total_pages,
        "tables_extracted": tables_extracted,
        "title": doc_title,
        "success": True,
    }


@skill(
    name="docx_to_text_file",
    description="Convert a Word document to a plain text file.",
    category="conversion",
    tags=["docx", "word", "text", "convert", "document"],
    side_effects=True,
    requires_filesystem=True,
    required_imports=["docx"],
    display_name="Word to Text",
    icon="file-arrow-right",
    risk_level=RiskLevel.MODERATE,
    group="Word",
)
def docx_to_text_file(input: str, output: str = "") -> dict:
    """Convert a Word document to a plain text file.

    Args:
        input: Path to the source .docx file.
        output: Path for the output .txt file (defaults to same name with .txt extension).
    """
    input = check_read_path(input)
    p = Path(input)
    if not p.exists():
        return {"error": f"File not found: {input}"}
    if not output:
        output = str(p.with_suffix(".txt"))
    output = check_write_path(output)

    transformer = DocxToTextTransformer("docx_to_text")
    text = transformer._transform(input)
    if text.startswith("[error]"):
        return {"error": text}

    Path(output).write_text(text, encoding="utf-8")
    return {
        "input": input,
        "output": output,
        "char_count": len(text),
        "word_count": len(text.split()),
        "success": True,
    }


@skill(
    name="docx_to_markdown_file",
    description="Convert a Word document to a Markdown file.",
    category="conversion",
    tags=["docx", "word", "markdown", "convert", "document"],
    side_effects=True,
    requires_filesystem=True,
    required_imports=["docx"],
    display_name="Word to Markdown",
    icon="file-arrow-right",
    risk_level=RiskLevel.MODERATE,
    group="Word",
)
def docx_to_markdown_file(input: str, output: str = "") -> dict:
    """Convert a Word document to a Markdown file.

    Args:
        input: Path to the source .docx file.
        output: Path for the output .md file (defaults to same name with .md extension).
    """
    input = check_read_path(input)
    p = Path(input)
    if not p.exists():
        return {"error": f"File not found: {input}"}
    if not output:
        output = str(p.with_suffix(".md"))
    output = check_write_path(output)

    transformer = DocxToMarkdownTransformer("docx_to_markdown")
    md = transformer._transform(input)
    if md.startswith("[error]"):
        return {"error": md}

    Path(output).write_text(md, encoding="utf-8")
    return {
        "input": input,
        "output": output,
        "char_count": len(md),
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
            "pdf_to_docx": pdf_to_docx.__skill__,
            "docx_to_text_file": docx_to_text_file.__skill__,
            "docx_to_markdown_file": docx_to_markdown_file.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="docx",
            display_name="Word",
            description="Read, create, and convert Word documents. Supports PDF to Word conversion.",
            icon="file-text",
            group="Documents",
            requires=PluginRequirements(filesystem=True, imports=["docx"]),
        )
