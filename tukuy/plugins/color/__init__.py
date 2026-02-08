"""Color utilities plugin.

Provides transformers for color manipulation, WCAG contrast ratio checking,
and palette generation.

Pure stdlib — no external dependencies.
"""

import colorsys
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color (with or without #) to (r, g, b) tuple."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r, g, b) to hex string."""
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
    )


def _relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1 definition."""
    def linearize(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def _contrast_ratio(lum1: float, lum2: float) -> float:
    """Calculate WCAG contrast ratio between two luminance values."""
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def _parse_color(color: str) -> Tuple[int, int, int]:
    """Parse a color string (hex, rgb(), or named) to (r, g, b).

    Supports: #fff, #ffffff, rgb(255,255,255), basic CSS named colors.
    """
    color = color.strip().lower()

    # Named colors (basic set)
    named = {
        "black": (0, 0, 0), "white": (255, 255, 255),
        "red": (255, 0, 0), "green": (0, 128, 0), "blue": (0, 0, 255),
        "yellow": (255, 255, 0), "cyan": (0, 255, 255), "magenta": (255, 0, 255),
        "orange": (255, 165, 0), "purple": (128, 0, 128),
        "gray": (128, 128, 128), "grey": (128, 128, 128),
    }
    if color in named:
        return named[color]

    # Hex
    if color.startswith("#"):
        return _hex_to_rgb(color)

    # rgb(r, g, b)
    rgb_match = re.match(r"rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color)
    if rgb_match:
        return int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))

    raise ValueError(f"Cannot parse color: {color!r}")


class WcagContrastTransformer(ChainableTransformer[str, dict]):
    """Check WCAG contrast ratio between two colors.

    Input: a string with two colors separated by a comma, space, or ``vs``.
    E.g. ``"#ffffff, #000000"`` or ``"white vs black"``.

    Returns a dict with ``ratio``, ``aa_normal``, ``aa_large``, ``aaa_normal``,
    ``aaa_large``, and ``level``.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        # Split on comma, "vs", or multiple spaces
        parts = re.split(r"\s*(?:,|vs\.?|\|)\s*", value.strip(), maxsplit=1)
        if len(parts) != 2:
            # Try splitting on whitespace
            parts = value.strip().split(None, 1)
        if len(parts) != 2:
            return {"error": "Provide two colors separated by comma, 'vs', or space"}

        fg = _parse_color(parts[0])
        bg = _parse_color(parts[1])

        lum_fg = _relative_luminance(*fg)
        lum_bg = _relative_luminance(*bg)
        ratio = round(_contrast_ratio(lum_fg, lum_bg), 2)

        aa_normal = ratio >= 4.5
        aa_large = ratio >= 3.0
        aaa_normal = ratio >= 7.0
        aaa_large = ratio >= 4.5

        if aaa_normal:
            level = "AAA"
        elif aa_normal:
            level = "AA"
        elif aa_large:
            level = "AA Large"
        else:
            level = "Fail"

        return {
            "foreground": _rgb_to_hex(*fg),
            "background": _rgb_to_hex(*bg),
            "ratio": ratio,
            "aa_normal": aa_normal,
            "aa_large": aa_large,
            "aaa_normal": aaa_normal,
            "aaa_large": aaa_large,
            "level": level,
        }


class HexToRgbTransformer(ChainableTransformer[str, str]):
    """Convert hex color to ``rgb(r, g, b)`` string."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        r, g, b = _hex_to_rgb(value.strip())
        return f"rgb({r}, {g}, {b})"


class RgbToHexTransformer(ChainableTransformer[str, str]):
    """Convert ``rgb(r, g, b)`` string to hex color."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        match = re.match(r"rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", value.strip())
        if not match:
            # Maybe it's just "r,g,b"
            parts = value.strip().split(",")
            if len(parts) == 3:
                return _rgb_to_hex(int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip()))
            raise ValueError(f"Cannot parse RGB: {value!r}")
        return _rgb_to_hex(int(match.group(1)), int(match.group(2)), int(match.group(3)))


class LightenTransformer(ChainableTransformer[str, str]):
    """Lighten a hex color by a given amount (0.0–1.0)."""

    def __init__(self, name: str, amount: float = 0.2):
        super().__init__(name)
        self.amount = max(0.0, min(1.0, amount))

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        r, g, b = _hex_to_rgb(value.strip())
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        l = min(1.0, l + self.amount)
        nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
        return _rgb_to_hex(round(nr * 255), round(ng * 255), round(nb * 255))


class DarkenTransformer(ChainableTransformer[str, str]):
    """Darken a hex color by a given amount (0.0–1.0)."""

    def __init__(self, name: str, amount: float = 0.2):
        super().__init__(name)
        self.amount = max(0.0, min(1.0, amount))

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        r, g, b = _hex_to_rgb(value.strip())
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        l = max(0.0, l - self.amount)
        nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
        return _rgb_to_hex(round(nr * 255), round(ng * 255), round(nb * 255))


class ColorPaletteTransformer(ChainableTransformer[str, dict]):
    """Generate a color palette from a base color.

    Returns complementary, analogous, triadic, and split-complementary colors,
    plus lighter and darker variants.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        r, g, b = _parse_color(value.strip())
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

        def hls_to_hex(hh: float, ll: float, ss: float) -> str:
            nr, ng, nb = colorsys.hls_to_rgb(hh % 1.0, max(0, min(1, ll)), max(0, min(1, ss)))
            return _rgb_to_hex(round(nr * 255), round(ng * 255), round(nb * 255))

        base_hex = _rgb_to_hex(r, g, b)

        return {
            "base": base_hex,
            "complementary": hls_to_hex(h + 0.5, l, s),
            "analogous": [
                hls_to_hex(h - 1 / 12, l, s),
                base_hex,
                hls_to_hex(h + 1 / 12, l, s),
            ],
            "triadic": [
                base_hex,
                hls_to_hex(h + 1 / 3, l, s),
                hls_to_hex(h + 2 / 3, l, s),
            ],
            "split_complementary": [
                base_hex,
                hls_to_hex(h + 5 / 12, l, s),
                hls_to_hex(h + 7 / 12, l, s),
            ],
            "lighter": [
                hls_to_hex(h, l + 0.1, s),
                hls_to_hex(h, l + 0.2, s),
                hls_to_hex(h, l + 0.3, s),
            ],
            "darker": [
                hls_to_hex(h, l - 0.1, s),
                hls_to_hex(h, l - 0.2, s),
                hls_to_hex(h, l - 0.3, s),
            ],
        }


class ColorPlugin(TransformerPlugin):
    """Plugin providing color manipulation and WCAG contrast checking."""

    def __init__(self):
        super().__init__("color")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "wcag_contrast": lambda _: WcagContrastTransformer("wcag_contrast"),
            "color_palette": lambda _: ColorPaletteTransformer("color_palette"),
            "hex_to_rgb": lambda _: HexToRgbTransformer("hex_to_rgb"),
            "rgb_to_hex": lambda _: RgbToHexTransformer("rgb_to_hex"),
            "lighten": lambda params: LightenTransformer(
                "lighten", amount=params.get("amount", 0.2),
            ),
            "darken": lambda params: DarkenTransformer(
                "darken", amount=params.get("amount", 0.2),
            ),
        }
