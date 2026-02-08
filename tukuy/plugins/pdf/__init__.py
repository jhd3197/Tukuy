"""PDF processing plugin.

Provides text extraction, table extraction, metadata reading, and page
manipulation for PDF files.

Requires ``pypdf`` for basic operations and ``pdfplumber`` for table
extraction (both optional, fail gracefully at runtime).
"""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_read_path, check_write_path
from ...skill import skill


# ── Transformers ──────────────────────────────────────────────────────────

class PdfExtractTextTransformer(ChainableTransformer[str, str]):
    """Extract all text from a PDF file.

    Input is a file path. Returns the concatenated text from all pages.
    Requires ``pypdf``.
    """

    def __init__(self, name: str, pages: Optional[List[int]] = None):
        super().__init__(name)
        self.pages = pages

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # type: ignore[no-redef]
            except ImportError:
                return "[error] pypdf is required. Install with: pip install pypdf"

        reader = PdfReader(value)
        texts = []
        page_indices = self.pages if self.pages else range(len(reader.pages))
        for i in page_indices:
            if 0 <= i < len(reader.pages):
                page_text = reader.pages[i].extract_text() or ""
                texts.append(page_text)
        return "\n\n".join(texts)


class PdfExtractMetadataTransformer(ChainableTransformer[str, dict]):
    """Extract metadata from a PDF file.

    Input is a file path. Returns title, author, subject, creator, etc.
    Requires ``pypdf``.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        try:
            from pypdf import PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # type: ignore[no-redef]
            except ImportError:
                return {"error": "pypdf is required. Install with: pip install pypdf"}

        reader = PdfReader(value)
        meta = reader.metadata
        result: Dict[str, Any] = {
            "path": value,
            "page_count": len(reader.pages),
        }
        if meta:
            result["title"] = meta.get("/Title", "") or ""
            result["author"] = meta.get("/Author", "") or ""
            result["subject"] = meta.get("/Subject", "") or ""
            result["creator"] = meta.get("/Creator", "") or ""
            result["producer"] = meta.get("/Producer", "") or ""
            result["creation_date"] = str(meta.get("/CreationDate", "")) or ""
            result["modification_date"] = str(meta.get("/ModDate", "")) or ""
        return result


class PdfExtractTablesTransformer(ChainableTransformer[str, list]):
    """Extract tables from a PDF file.

    Input is a file path. Returns a list of tables, each being a list of
    rows (lists of cell values).
    Requires ``pdfplumber``.
    """

    def __init__(self, name: str, pages: Optional[List[int]] = None):
        super().__init__(name)
        self.pages = pages

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> list:
        try:
            import pdfplumber
        except ImportError:
            return [{"error": "pdfplumber is required. Install with: pip install pdfplumber"}]

        tables = []
        with pdfplumber.open(value) as pdf:
            page_indices = self.pages if self.pages else range(len(pdf.pages))
            for i in page_indices:
                if 0 <= i < len(pdf.pages):
                    page = pdf.pages[i]
                    page_tables = page.extract_tables() or []
                    for table in page_tables:
                        if table:
                            # Convert to list of dicts using first row as header
                            headers = [str(h or "").strip() for h in table[0]]
                            rows = []
                            for row in table[1:]:
                                row_dict = {}
                                for j, header in enumerate(headers):
                                    cell = str(row[j] or "").strip() if j < len(row) else ""
                                    row_dict[header] = cell
                                rows.append(row_dict)
                            tables.append({
                                "page": i + 1,
                                "headers": headers,
                                "rows": rows,
                                "row_count": len(rows),
                            })
        return tables


# ── Skills ────────────────────────────────────────────────────────────────

@skill(
    name="pdf_read",
    description="Read a PDF file and return text content, metadata, and page count.",
    category="pdf",
    tags=["pdf", "document", "extract"],
    idempotent=True,
    requires_filesystem=True,
    required_imports=["pypdf"],
)
def pdf_read(path: str, pages: Optional[list] = None) -> dict:
    """Read a PDF file and return its content."""
    path = check_read_path(path)
    p = Path(path)
    if not p.exists():
        return {"path": path, "error": "File not found", "exists": False}

    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore[no-redef]
        except ImportError:
            return {"error": "pypdf is required. Install with: pip install pypdf"}

    reader = PdfReader(path)
    page_count = len(reader.pages)

    page_indices = pages if pages else list(range(page_count))
    page_texts = []
    for i in page_indices:
        if 0 <= i < page_count:
            text = reader.pages[i].extract_text() or ""
            page_texts.append({"page": i + 1, "text": text, "char_count": len(text)})

    meta = reader.metadata
    metadata = {}
    if meta:
        metadata = {
            "title": meta.get("/Title", "") or "",
            "author": meta.get("/Author", "") or "",
            "subject": meta.get("/Subject", "") or "",
            "creator": meta.get("/Creator", "") or "",
        }

    return {
        "path": path,
        "exists": True,
        "page_count": page_count,
        "metadata": metadata,
        "pages": page_texts,
        "total_chars": sum(p["char_count"] for p in page_texts),
    }


@skill(
    name="pdf_merge",
    description="Merge multiple PDF files into one.",
    category="pdf",
    tags=["pdf", "document", "merge"],
    side_effects=True,
    requires_filesystem=True,
    required_imports=["pypdf"],
)
def pdf_merge(paths: list, output: str = "merged.pdf") -> dict:
    """Merge multiple PDF files into a single PDF."""
    for pdf_p in paths:
        check_read_path(pdf_p)
    output = check_write_path(output)
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfWriter, PdfReader  # type: ignore[no-redef]
        except ImportError:
            return {"error": "pypdf is required. Install with: pip install pypdf"}

    writer = PdfWriter()
    total_pages = 0
    files_merged = []

    for pdf_path in paths:
        p = Path(pdf_path)
        if not p.exists():
            return {"error": f"File not found: {pdf_path}"}
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)
            total_pages += 1
        files_merged.append(pdf_path)

    with open(output, "wb") as f:
        writer.write(f)

    return {
        "output": output,
        "files_merged": len(files_merged),
        "total_pages": total_pages,
        "success": True,
    }


@skill(
    name="pdf_split",
    description="Split a PDF into individual page files or a page range.",
    category="pdf",
    tags=["pdf", "document", "split"],
    side_effects=True,
    requires_filesystem=True,
    required_imports=["pypdf"],
)
def pdf_split(
    path: str,
    pages: Optional[list] = None,
    output_dir: str = ".",
) -> dict:
    """Split a PDF into separate page files."""
    path = check_read_path(path)
    output_dir = check_write_path(output_dir)
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfWriter, PdfReader  # type: ignore[no-redef]
        except ImportError:
            return {"error": "pypdf is required. Install with: pip install pypdf"}

    p = Path(path)
    if not p.exists():
        return {"path": path, "error": "File not found"}

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(path)
    page_indices = pages if pages else list(range(len(reader.pages)))
    output_files = []

    for i in page_indices:
        if 0 <= i < len(reader.pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            out_file = out / f"{p.stem}_page_{i + 1}.pdf"
            with open(out_file, "wb") as f:
                writer.write(f)
            output_files.append(str(out_file))

    return {
        "source": path,
        "output_dir": str(out),
        "files_created": output_files,
        "page_count": len(output_files),
        "success": True,
    }


@skill(
    name="pdf_page_count",
    description="Get the number of pages in a PDF file.",
    category="pdf",
    tags=["pdf", "document"],
    idempotent=True,
    requires_filesystem=True,
    required_imports=["pypdf"],
)
def pdf_page_count(path: str) -> dict:
    """Get page count of a PDF file."""
    path = check_read_path(path)
    p = Path(path)
    if not p.exists():
        return {"path": path, "error": "File not found", "exists": False}

    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore[no-redef]
        except ImportError:
            return {"error": "pypdf is required. Install with: pip install pypdf"}

    reader = PdfReader(path)
    return {
        "path": path,
        "exists": True,
        "page_count": len(reader.pages),
    }


class PdfPlugin(TransformerPlugin):
    """Plugin providing PDF processing transformers and skills."""

    def __init__(self):
        super().__init__("pdf")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "pdf_extract_text": lambda params: PdfExtractTextTransformer(
                "pdf_extract_text",
                pages=params.get("pages"),
            ),
            "pdf_extract_metadata": lambda _: PdfExtractMetadataTransformer("pdf_extract_metadata"),
            "pdf_extract_tables": lambda params: PdfExtractTablesTransformer(
                "pdf_extract_tables",
                pages=params.get("pages"),
            ),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "pdf_read": pdf_read.__skill__,
            "pdf_merge": pdf_merge.__skill__,
            "pdf_split": pdf_split.__skill__,
            "pdf_page_count": pdf_page_count.__skill__,
        }
