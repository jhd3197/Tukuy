"""QR code plugin.

Provides an async ``qr_generate`` skill and a ``qr_url`` transformer
using the goqr.me API (free, no key, no limits).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import base64
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.qrserver.com/v1"


class QrUrlTransformer(ChainableTransformer[str, str]):
    """Build a QR code image URL from a data string."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, str) and len(value) > 0

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        params = urlencode({"data": value, "size": "300x300", "format": "png"})
        return f"{_BASE_URL}/create-qr-code/?{params}"


# ── Skills ─────────────────────────────────────────────────────────────────


@skill(
    name="qr_generate",
    display_name="Generate QR Code",
    description="Generate a QR code image from text or a URL (goqr.me, free, no key required).",
    category="qrcode",
    tags=["qr", "qrcode", "barcode", "image"],
    icon="qr-code",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="default_size",
            display_name="Default Size",
            description="Default image size in pixels (NxN).",
            type="number",
            default=300,
            min=50,
            max=1000,
            unit="px",
        ),
        ConfigParam(
            name="default_format",
            display_name="Image Format",
            description="Output image format.",
            type="select",
            default="png",
            options=["png", "svg", "jpg", "gif"],
        ),
        ConfigParam(
            name="timeout",
            display_name="Timeout",
            description="Request timeout.",
            type="number",
            default=15,
            min=1,
            max=60,
            unit="seconds",
        ),
    ],
)
async def qr_generate(
    data: str,
    size: int = 300,
    format: str = "png",
    color: str = "000000",
    bgcolor: str = "ffffff",
    margin: int = 4,
) -> dict:
    """Generate a QR code and return the image URL and base64-encoded bytes."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    size = max(50, min(size, 1000))
    params = {
        "data": data,
        "size": f"{size}x{size}",
        "format": format,
        "color": color.lstrip("#"),
        "bgcolor": bgcolor.lstrip("#"),
        "margin": margin,
    }

    url = f"{_BASE_URL}/create-qr-code/"
    check_host(url)

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        image_bytes = resp.content
        content_type = resp.headers.get("content-type", f"image/{format}")
        image_url = str(resp.url)
        return {
            "data": data,
            "image_url": image_url,
            "image_base64": base64.b64encode(image_bytes).decode("ascii"),
            "content_type": content_type,
            "size": size,
            "format": format,
            "bytes": len(image_bytes),
            "success": True,
        }


@skill(
    name="qr_read",
    display_name="Read QR Code",
    description="Decode a QR code from an image URL (goqr.me, free, no key required).",
    category="qrcode",
    tags=["qr", "qrcode", "decode", "read"],
    icon="scan",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def qr_read(image_url: str) -> dict:
    """Decode a QR code from an image URL."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"{_BASE_URL}/read-qr-code/"
    check_host(url)
    check_host(image_url)

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={"fileurl": image_url}, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        # The API returns a list of symbol results
        symbols = []
        for item in data:
            for sym in item.get("symbol", []):
                if sym.get("data"):
                    symbols.append({
                        "data": sym["data"],
                        "error": sym.get("error"),
                    })
        decoded = symbols[0]["data"] if symbols else None
        return {
            "image_url": image_url,
            "decoded": decoded,
            "symbols": symbols,
            "success": decoded is not None,
        }


class QrCodePlugin(TransformerPlugin):
    """Plugin providing QR code generation/reading skills and URL transformer."""

    def __init__(self):
        super().__init__("qrcode")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "qr_url": lambda _: QrUrlTransformer("qr_url"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "qr_generate": qr_generate.__skill__,
            "qr_read": qr_read.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="qrcode",
            display_name="QR Code",
            description="Generate and read QR codes via goqr.me API.",
            icon="qr-code",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
