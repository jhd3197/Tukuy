"""Compression and archive plugin.

Skills-only plugin for creating and extracting zip/tar archives,
and gzip compress/decompress transformers.

Pure stdlib — no external dependencies.
All skills declare ``requires_filesystem=True`` for SafetyPolicy enforcement.
"""

import gzip
import io
import os
import tarfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...skill import skill


# ── Transformers ──────────────────────────────────────────────────────────

class GzipCompressTransformer(ChainableTransformer[str, bytes]):
    """Compress a string using gzip."""

    def __init__(self, name: str, level: int = 9):
        super().__init__(name)
        self.level = level

    def validate(self, value: str) -> bool:
        return isinstance(value, (str, bytes))

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> bytes:
        data = value.encode("utf-8") if isinstance(value, str) else value
        return gzip.compress(data, compresslevel=self.level)


class GzipDecompressTransformer(ChainableTransformer[bytes, str]):
    """Decompress gzip data back to a string."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, (bytes, str))

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        data = value if isinstance(value, bytes) else value.encode("latin-1")
        return gzip.decompress(data).decode("utf-8")


# ── Skills ────────────────────────────────────────────────────────────────

@skill(
    name="zip_create",
    description="Create a zip archive from a list of files or a directory.",
    category="compression",
    tags=["zip", "archive", "compress"],
    side_effects=True,
    requires_filesystem=True,
)
def zip_create(
    paths: list,
    output: str = "archive.zip",
    base_dir: str = "",
) -> dict:
    """Create a zip archive."""
    out_path = Path(output)
    files_added = []

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            src = Path(p)
            if src.is_dir():
                for root, _, files in os.walk(src):
                    for f in files:
                        full = Path(root) / f
                        arcname = str(full.relative_to(base_dir)) if base_dir else str(full)
                        zf.write(full, arcname)
                        files_added.append(arcname)
            elif src.is_file():
                arcname = str(src.relative_to(base_dir)) if base_dir else src.name
                zf.write(src, arcname)
                files_added.append(arcname)

    return {
        "path": str(out_path),
        "files_added": len(files_added),
        "size": out_path.stat().st_size,
    }


@skill(
    name="zip_extract",
    description="Extract a zip archive to a directory.",
    category="compression",
    tags=["zip", "archive", "extract"],
    side_effects=True,
    requires_filesystem=True,
)
def zip_extract(path: str, output_dir: str = ".") -> dict:
    """Extract a zip archive."""
    src = Path(path)
    if not src.exists():
        return {"path": path, "error": "File not found"}

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(src, "r") as zf:
        # Security: check for path traversal
        for member in zf.namelist():
            member_path = out / member
            if not str(member_path.resolve()).startswith(str(out.resolve())):
                return {"path": path, "error": f"Path traversal detected: {member}"}
        zf.extractall(out)
        extracted = zf.namelist()

    return {
        "path": path,
        "output_dir": str(out),
        "files_extracted": len(extracted),
        "files": extracted[:50],  # cap listing
    }


@skill(
    name="zip_list",
    description="List contents of a zip archive without extracting.",
    category="compression",
    tags=["zip", "archive", "list"],
    idempotent=True,
    requires_filesystem=True,
)
def zip_list(path: str) -> dict:
    """List zip archive contents."""
    src = Path(path)
    if not src.exists():
        return {"path": path, "error": "File not found"}

    with zipfile.ZipFile(src, "r") as zf:
        entries = []
        for info in zf.infolist():
            entries.append({
                "name": info.filename,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "is_dir": info.is_dir(),
            })

    return {
        "path": path,
        "entries": entries,
        "count": len(entries),
        "total_size": sum(e["size"] for e in entries),
    }


@skill(
    name="tar_create",
    description="Create a tar archive (optionally gzipped) from files or a directory.",
    category="compression",
    tags=["tar", "archive", "compress"],
    side_effects=True,
    requires_filesystem=True,
)
def tar_create(
    paths: list,
    output: str = "archive.tar.gz",
    compress: bool = True,
) -> dict:
    """Create a tar archive."""
    mode = "w:gz" if compress else "w"
    out_path = Path(output)
    files_added = 0

    with tarfile.open(out_path, mode) as tf:
        for p in paths:
            src = Path(p)
            if src.exists():
                tf.add(src, arcname=src.name)
                if src.is_dir():
                    files_added += sum(1 for _ in src.rglob("*") if _.is_file())
                else:
                    files_added += 1

    return {
        "path": str(out_path),
        "files_added": files_added,
        "compressed": compress,
        "size": out_path.stat().st_size,
    }


@skill(
    name="tar_extract",
    description="Extract a tar archive to a directory.",
    category="compression",
    tags=["tar", "archive", "extract"],
    side_effects=True,
    requires_filesystem=True,
)
def tar_extract(path: str, output_dir: str = ".") -> dict:
    """Extract a tar archive."""
    src = Path(path)
    if not src.exists():
        return {"path": path, "error": "File not found"}

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    with tarfile.open(src, "r:*") as tf:
        # Security: check for path traversal
        for member in tf.getmembers():
            member_path = out / member.name
            if not str(member_path.resolve()).startswith(str(out.resolve())):
                return {"path": path, "error": f"Path traversal detected: {member.name}"}
        tf.extractall(out, filter="data")
        extracted = [m.name for m in tf.getmembers()]

    return {
        "path": path,
        "output_dir": str(out),
        "files_extracted": len(extracted),
        "files": extracted[:50],
    }


class CompressionPlugin(TransformerPlugin):
    """Plugin providing compression and archive operations."""

    def __init__(self):
        super().__init__("compression")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "gzip_compress": lambda params: GzipCompressTransformer(
                "gzip_compress",
                level=params.get("level", 9),
            ),
            "gzip_decompress": lambda _: GzipDecompressTransformer("gzip_decompress"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "zip_create": zip_create.__skill__,
            "zip_extract": zip_extract.__skill__,
            "zip_list": zip_list.__skill__,
            "tar_create": tar_create.__skill__,
            "tar_extract": tar_extract.__skill__,
        }
