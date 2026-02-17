"""Chart generation plugin.

Provides async skills for generating chart images using the QuickChart API
(free, no key required, open source).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import json as _json
from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://quickchart.io"


# -- Skills ------------------------------------------------------------------


@skill(
    name="chart_url",
    display_name="Generate Chart URL",
    description="Generate a chart image URL from a Chart.js config (QuickChart, free, no key required).",
    category="quickchart",
    tags=["chart", "graph", "visualization", "image"],
    icon="bar-chart",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=False,
    config_params=[
        ConfigParam(
            name="width",
            display_name="Width",
            description="Chart width in pixels.",
            type="number",
            default=500,
            min=100,
            max=2000,
            unit="px",
        ),
        ConfigParam(
            name="height",
            display_name="Height",
            description="Chart height in pixels.",
            type="number",
            default=300,
            min=100,
            max=2000,
            unit="px",
        ),
    ],
)
async def chart_url(
    chart_config: str,
    width: int = 500,
    height: int = 300,
    background_color: str = "white",
) -> dict:
    """Build a QuickChart URL for a Chart.js configuration.

    Args:
        chart_config: Chart.js config as a JSON string.
        width: Chart width in pixels.
        height: Chart height in pixels.
        background_color: Background color (default white).
    """
    chart_config = chart_config.strip()
    if not chart_config:
        return {"error": "Chart config must not be empty.", "success": False}

    try:
        _json.loads(chart_config)
    except _json.JSONDecodeError as e:
        return {"error": f"Invalid JSON config: {e}", "success": False}

    from urllib.parse import quote
    encoded = quote(chart_config)
    url = f"{_BASE_URL}/chart?c={encoded}&w={width}&h={height}&bkg={background_color}"

    return {
        "chart_url": url,
        "width": width,
        "height": height,
        "success": True,
    }


@skill(
    name="chart_simple",
    display_name="Simple Chart",
    description="Generate a simple chart URL from labels and values (QuickChart, free, no key required).",
    category="quickchart",
    tags=["chart", "simple", "bar", "line", "pie"],
    icon="bar-chart",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=False,
)
async def chart_simple(
    chart_type: str = "bar",
    labels: str = "",
    values: str = "",
    title: str = "",
    width: int = 500,
    height: int = 300,
) -> dict:
    """Generate a simple chart from comma-separated labels and values.

    Args:
        chart_type: Chart type: bar, line, pie, doughnut, radar, polarArea.
        labels: Comma-separated labels (e.g. ``"Jan,Feb,Mar"``).
        values: Comma-separated numeric values (e.g. ``"10,20,30"``).
        title: Optional chart title.
        width: Chart width in pixels.
        height: Chart height in pixels.
    """
    label_list = [l.strip() for l in labels.split(",") if l.strip()]
    try:
        value_list = [float(v.strip()) for v in values.split(",") if v.strip()]
    except ValueError:
        return {"error": "Values must be comma-separated numbers.", "success": False}

    if not label_list or not value_list:
        return {"error": "Both labels and values are required.", "success": False}

    config = {
        "type": chart_type,
        "data": {
            "labels": label_list,
            "datasets": [{"label": title or "Data", "data": value_list}],
        },
    }
    if title:
        config["options"] = {"plugins": {"title": {"display": True, "text": title}}}

    config_str = _json.dumps(config, separators=(",", ":"))
    return await chart_url(chart_config=config_str, width=width, height=height)


@skill(
    name="chart_render",
    display_name="Render Chart",
    description="Render a chart image (binary) from a Chart.js config via QuickChart POST API (free, no key).",
    category="quickchart",
    tags=["chart", "render", "image", "png"],
    icon="image",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def chart_render(
    chart_config: str,
    width: int = 500,
    height: int = 300,
    format: str = "png",
) -> dict:
    """Render a chart to a short URL via QuickChart's POST API.

    Args:
        chart_config: Chart.js config as a JSON string.
        width: Chart width in pixels.
        height: Chart height in pixels.
        format: Output format (png or svg).
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    chart_config = chart_config.strip()
    if not chart_config:
        return {"error": "Chart config must not be empty.", "success": False}

    try:
        config_obj = _json.loads(chart_config)
    except _json.JSONDecodeError as e:
        return {"error": f"Invalid JSON config: {e}", "success": False}

    url = f"{_BASE_URL}/chart/create"
    payload = {
        "chart": config_obj,
        "width": width,
        "height": height,
        "format": format,
        "backgroundColor": "white",
    }

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=30)
        if not resp.is_success:
            return {"error": f"QuickChart API returned status {resp.status_code}", "success": False}
        data = resp.json()

    return {
        "chart_url": data.get("url", ""),
        "width": width,
        "height": height,
        "format": format,
        "success": bool(data.get("url")),
    }


class QuickChartPlugin(TransformerPlugin):
    """Plugin providing chart generation skills via QuickChart."""

    def __init__(self):
        super().__init__("quickchart")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "chart_url": chart_url.__skill__,
            "chart_simple": chart_simple.__skill__,
            "chart_render": chart_render.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="quickchart",
            display_name="QuickChart",
            description="Generate chart images from data via the QuickChart API.",
            icon="bar-chart",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
