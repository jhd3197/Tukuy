"""Profanity filter plugin.

Provides async skills for content moderation and profanity filtering
using the PurgoMalum API (free, no key required).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://www.purgomalum.com/service"


# -- Skills ------------------------------------------------------------------


@skill(
    name="profanity_filter",
    display_name="Profanity Filter",
    description="Filter profanity from text, replacing bad words with a fill character (PurgoMalum, free, no key).",
    category="profanity",
    tags=["profanity", "filter", "moderation", "text", "safety"],
    icon="shield",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
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
async def profanity_filter(
    text: str,
    fill_char: str = "*",
    add_words: str = "",
    timeout: int = 15,
) -> dict:
    """Filter profanity from text.

    Args:
        text: The text to filter.
        fill_char: Character to replace profanity with (default ``"*"``).
        add_words: Comma-separated list of extra words to filter.
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    if not text.strip():
        return {"error": "Text must not be empty.", "success": False}

    url = f"{_BASE_URL}/json"
    params = {"text": text, "fill_char": fill_char}
    if add_words.strip():
        params["add"] = add_words.strip()

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    return {
        "original": text,
        "filtered": data.get("result", text),
        "success": True,
    }


@skill(
    name="profanity_check",
    display_name="Check Profanity",
    description="Check if text contains profanity (PurgoMalum, free, no key required).",
    category="profanity",
    tags=["profanity", "check", "moderation", "safety"],
    icon="shield",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def profanity_check(text: str, add_words: str = "") -> dict:
    """Check whether text contains profanity.

    Args:
        text: The text to check.
        add_words: Comma-separated extra words to consider profane.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    if not text.strip():
        return {"error": "Text must not be empty.", "success": False}

    url = f"{_BASE_URL}/containsprofanity"
    params = {"text": text}
    if add_words.strip():
        params["add"] = add_words.strip()

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        result_text = resp.text.strip().lower()

    return {
        "text": text,
        "contains_profanity": result_text == "true",
        "success": True,
    }


class ProfanityPlugin(TransformerPlugin):
    """Plugin providing profanity filtering and detection skills."""

    def __init__(self):
        super().__init__("profanity")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "profanity_filter": profanity_filter.__skill__,
            "profanity_check": profanity_check.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="profanity",
            display_name="Profanity Filter",
            description="Filter and detect profanity in text via PurgoMalum API.",
            icon="shield",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
