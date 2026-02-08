"""Tests for the Color utilities plugin."""

import pytest

from tukuy import TukuyTransformer
from tukuy.plugins.color import (
    ColorPlugin,
    WcagContrastTransformer,
    HexToRgbTransformer,
    RgbToHexTransformer,
    LightenTransformer,
    DarkenTransformer,
    ColorPaletteTransformer,
)


@pytest.fixture
def transformer():
    return TukuyTransformer()


# ── WcagContrastTransformer ──────────────────────────────────────────────


class TestWcagContrast:
    def test_black_on_white(self):
        t = WcagContrastTransformer("wcag_contrast")
        result = t.transform("#000000, #ffffff")
        assert result.value["ratio"] == 21.0
        assert result.value["level"] == "AAA"
        assert result.value["aa_normal"] is True
        assert result.value["aaa_normal"] is True

    def test_white_on_white(self):
        t = WcagContrastTransformer("wcag_contrast")
        result = t.transform("#ffffff, #ffffff")
        assert result.value["ratio"] == 1.0
        assert result.value["level"] == "Fail"

    def test_vs_separator(self):
        t = WcagContrastTransformer("wcag_contrast")
        result = t.transform("#000 vs #fff")
        assert result.value["ratio"] == 21.0

    def test_named_colors(self):
        t = WcagContrastTransformer("wcag_contrast")
        result = t.transform("black, white")
        assert result.value["ratio"] == 21.0

    def test_low_contrast(self):
        t = WcagContrastTransformer("wcag_contrast")
        result = t.transform("#777777, #888888")
        assert result.value["aa_normal"] is False

    def test_pipe_separator(self):
        t = WcagContrastTransformer("wcag_contrast")
        result = t.transform("#000 | #fff")
        assert result.value["ratio"] == 21.0


# ── HexToRgbTransformer ─────────────────────────────────────────────────


class TestHexToRgb:
    def test_full_hex(self):
        t = HexToRgbTransformer("hex_to_rgb")
        result = t.transform("#ff0000")
        assert result.value == "rgb(255, 0, 0)"

    def test_short_hex(self):
        t = HexToRgbTransformer("hex_to_rgb")
        result = t.transform("#f00")
        assert result.value == "rgb(255, 0, 0)"

    def test_without_hash(self):
        t = HexToRgbTransformer("hex_to_rgb")
        result = t.transform("00ff00")
        assert result.value == "rgb(0, 255, 0)"


# ── RgbToHexTransformer ─────────────────────────────────────────────────


class TestRgbToHex:
    def test_rgb_function(self):
        t = RgbToHexTransformer("rgb_to_hex")
        result = t.transform("rgb(255, 0, 0)")
        assert result.value == "#ff0000"

    def test_csv_format(self):
        t = RgbToHexTransformer("rgb_to_hex")
        result = t.transform("0, 255, 0")
        assert result.value == "#00ff00"


# ── LightenTransformer ──────────────────────────────────────────────────


class TestLighten:
    def test_lighten(self):
        t = LightenTransformer("lighten", amount=0.2)
        result = t.transform("#333333")
        # Should be lighter than original
        original_r = 0x33
        result_hex = result.value.lstrip("#")
        result_r = int(result_hex[0:2], 16)
        assert result_r > original_r

    def test_lighten_white_stays_white(self):
        t = LightenTransformer("lighten", amount=0.2)
        result = t.transform("#ffffff")
        assert result.value == "#ffffff"


# ── DarkenTransformer ───────────────────────────────────────────────────


class TestDarken:
    def test_darken(self):
        t = DarkenTransformer("darken", amount=0.2)
        result = t.transform("#cccccc")
        result_hex = result.value.lstrip("#")
        result_r = int(result_hex[0:2], 16)
        assert result_r < 0xCC

    def test_darken_black_stays_black(self):
        t = DarkenTransformer("darken", amount=0.2)
        result = t.transform("#000000")
        assert result.value == "#000000"


# ── ColorPaletteTransformer ─────────────────────────────────────────────


class TestColorPalette:
    def test_generates_palette(self):
        t = ColorPaletteTransformer("color_palette")
        result = t.transform("#3498db")
        palette = result.value
        assert "base" in palette
        assert "complementary" in palette
        assert len(palette["analogous"]) == 3
        assert len(palette["triadic"]) == 3
        assert len(palette["split_complementary"]) == 3
        assert len(palette["lighter"]) == 3
        assert len(palette["darker"]) == 3

    def test_base_matches_input(self):
        t = ColorPaletteTransformer("color_palette")
        result = t.transform("#ff0000")
        assert result.value["base"] == "#ff0000"

    def test_complementary_is_different(self):
        t = ColorPaletteTransformer("color_palette")
        result = t.transform("#ff0000")
        assert result.value["complementary"] != result.value["base"]

    def test_named_color(self):
        t = ColorPaletteTransformer("color_palette")
        result = t.transform("blue")
        # CSS "blue" is (0, 0, 255) -> #0000ff
        assert result.value["base"] == "#0000ff"

    def test_lighter_are_lighter(self):
        t = ColorPaletteTransformer("color_palette")
        result = t.transform("#555555")
        base_r = int(result.value["base"].lstrip("#")[0:2], 16)
        light_r = int(result.value["lighter"][0].lstrip("#")[0:2], 16)
        assert light_r >= base_r


# ── Plugin registration ──────────────────────────────────────────────────


class TestColorPlugin:
    def test_plugin_name(self):
        plugin = ColorPlugin()
        assert plugin.name == "color"

    def test_has_all_transformers(self):
        plugin = ColorPlugin()
        names = set(plugin.transformers.keys())
        assert names == {
            "wcag_contrast", "color_palette", "hex_to_rgb",
            "rgb_to_hex", "lighten", "darken",
        }


# ── Integration tests via TukuyTransformer ────────────────────────────────


class TestColorIntegration:
    def test_wcag_contrast(self, transformer):
        result = transformer.transform("#000, #fff", ["wcag_contrast"])
        assert result["ratio"] == 21.0

    def test_hex_to_rgb(self, transformer):
        result = transformer.transform("#ff0000", ["hex_to_rgb"])
        assert result == "rgb(255, 0, 0)"

    def test_rgb_to_hex(self, transformer):
        result = transformer.transform("rgb(0, 255, 0)", ["rgb_to_hex"])
        assert result == "#00ff00"

    def test_lighten(self, transformer):
        result = transformer.transform("#333333", [{"function": "lighten", "amount": 0.3}])
        assert result != "#333333"

    def test_color_palette(self, transformer):
        result = transformer.transform("#3498db", ["color_palette"])
        assert "complementary" in result
