"""Image plugin.

Provides image metadata extraction, format detection, and base64 encoding.

Skills (image_info, image_resize, image_thumbnail) require ``Pillow``
(optional, fails gracefully at runtime).  The ``detect_format`` and
``image_to_base64`` transformers work with stdlib only.
"""

import base64
import struct
from pathlib import Path
from typing import Any, Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...skill import skill


# ── Format signatures ─────────────────────────────────────────────────────

_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"RIFF": "webp",  # further check needed
    b"BM": "bmp",
    b"\x00\x00\x01\x00": "ico",
    b"II\x2a\x00": "tiff",
    b"MM\x00\x2a": "tiff",
}


def _detect_format_bytes(data: bytes) -> str:
    """Detect image format from raw bytes."""
    for sig, fmt in _SIGNATURES.items():
        if data[:len(sig)] == sig:
            if fmt == "webp" and data[8:12] == b"WEBP":
                return "webp"
            elif fmt != "webp":
                return fmt
    if data[:4] == b"RIFF":
        return "unknown"
    return "unknown"


def _get_dimensions_stdlib(data: bytes, fmt: str) -> Optional[Dict[str, int]]:
    """Try to extract dimensions without Pillow for common formats."""
    try:
        if fmt == "png" and len(data) >= 24:
            w = struct.unpack(">I", data[16:20])[0]
            h = struct.unpack(">I", data[20:24])[0]
            return {"width": w, "height": h}
        if fmt == "gif" and len(data) >= 10:
            w = struct.unpack("<H", data[6:8])[0]
            h = struct.unpack("<H", data[8:10])[0]
            return {"width": w, "height": h}
        if fmt == "bmp" and len(data) >= 26:
            w = struct.unpack("<I", data[18:22])[0]
            h = abs(struct.unpack("<i", data[22:26])[0])
            return {"width": w, "height": h}
    except Exception:
        pass
    return None


# ── Transformers ──────────────────────────────────────────────────────────

class DetectFormatTransformer(ChainableTransformer[str, dict]):
    """Detect image format from a file path.

    Returns ``{"format": str, "path": str}``.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        path = Path(value)
        if not path.exists():
            return {"format": "unknown", "path": value, "error": "File not found"}

        data = path.read_bytes()[:32]
        fmt = _detect_format_bytes(data)
        return {"format": fmt, "path": value}


class ImageToBase64Transformer(ChainableTransformer[str, str]):
    """Read an image file and return a base64-encoded data URI.

    Input is a file path. Output is ``data:<mime>;base64,...``.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        path = Path(value)
        data = path.read_bytes()
        fmt = _detect_format_bytes(data[:32])
        mime_map = {
            "png": "image/png",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
            "bmp": "image/bmp",
            "tiff": "image/tiff",
            "ico": "image/x-icon",
        }
        mime = mime_map.get(fmt, "application/octet-stream")
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{b64}"


# ── Skills ────────────────────────────────────────────────────────────────

@skill(
    name="image_info",
    description="Get image metadata: dimensions, format, file size, and EXIF data (if available).",
    category="image",
    tags=["image", "metadata"],
    idempotent=True,
    requires_filesystem=True,
)
def image_info(path: str) -> dict:
    """Get detailed image information."""
    p = Path(path)
    if not p.exists():
        return {"path": path, "error": "File not found", "exists": False}

    data = p.read_bytes()
    fmt = _detect_format_bytes(data[:32])
    result: Dict[str, Any] = {
        "path": path,
        "exists": True,
        "format": fmt,
        "file_size": len(data),
        "file_size_human": _human_size(len(data)),
    }

    # Try Pillow for rich metadata
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        with Image.open(p) as img:
            result["width"] = img.width
            result["height"] = img.height
            result["mode"] = img.mode
            result["format"] = (img.format or fmt).lower()

            # EXIF data
            exif_data = {}
            try:
                raw_exif = img._getexif()
                if raw_exif:
                    for tag_id, val in raw_exif.items():
                        tag = TAGS.get(tag_id, str(tag_id))
                        # Convert bytes to string for JSON serialization
                        if isinstance(val, bytes):
                            try:
                                val = val.decode("utf-8", errors="replace")
                            except Exception:
                                val = str(val)
                        exif_data[tag] = val
            except Exception:
                pass
            result["exif"] = exif_data

    except ImportError:
        # Fallback to stdlib dimension detection
        dims = _get_dimensions_stdlib(data, fmt)
        if dims:
            result.update(dims)
        result["note"] = "Install Pillow for full metadata support"

    return result


@skill(
    name="image_resize",
    description="Resize an image to specified dimensions. Requires Pillow.",
    category="image",
    tags=["image", "resize"],
    side_effects=True,
    requires_filesystem=True,
    required_imports=["PIL"],
)
def image_resize(
    path: str,
    width: int = 0,
    height: int = 0,
    output: str = "",
    maintain_aspect: bool = True,
) -> dict:
    """Resize an image file."""
    try:
        from PIL import Image
    except ImportError:
        return {"error": "Pillow is required. Install with: pip install Pillow"}

    p = Path(path)
    if not p.exists():
        return {"path": path, "error": "File not found"}

    with Image.open(p) as img:
        original_size = img.size

        if maintain_aspect:
            if width and not height:
                ratio = width / img.width
                height = int(img.height * ratio)
            elif height and not width:
                ratio = height / img.height
                width = int(img.width * ratio)
            elif not width and not height:
                return {"error": "Specify at least width or height"}

        resized = img.resize((width, height), Image.LANCZOS)
        out_path = output or str(p)
        resized.save(out_path)

    return {
        "path": out_path,
        "original_size": list(original_size),
        "new_size": [width, height],
    }


@skill(
    name="image_thumbnail",
    description="Create a thumbnail of an image. Requires Pillow.",
    category="image",
    tags=["image", "thumbnail"],
    side_effects=True,
    requires_filesystem=True,
    required_imports=["PIL"],
)
def image_thumbnail(
    path: str,
    max_size: int = 128,
    output: str = "",
) -> dict:
    """Create a thumbnail from an image file."""
    try:
        from PIL import Image
    except ImportError:
        return {"error": "Pillow is required. Install with: pip install Pillow"}

    p = Path(path)
    if not p.exists():
        return {"path": path, "error": "File not found"}

    with Image.open(p) as img:
        original_size = img.size
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        out_path = output or f"{p.stem}_thumb{p.suffix}"
        img.save(out_path)

    return {
        "path": out_path,
        "original_size": list(original_size),
        "thumbnail_size": [min(original_size[0], max_size), min(original_size[1], max_size)],
    }


def _human_size(size: int) -> str:
    """Format byte count as human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024
    return f"{size:.1f} TB"


class ImagePlugin(TransformerPlugin):
    """Plugin providing image metadata and manipulation."""

    def __init__(self):
        super().__init__("image")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "detect_format": lambda _: DetectFormatTransformer("detect_format"),
            "image_to_base64": lambda _: ImageToBase64Transformer("image_to_base64"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "image_info": image_info.__skill__,
            "image_resize": image_resize.__skill__,
            "image_thumbnail": image_thumbnail.__skill__,
        }
