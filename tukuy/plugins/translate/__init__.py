"""Translation plugin.

Provides async ``translate_text`` and ``detect_language`` skills using the
DeepL API Free tier (500 000 chars/month).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import os
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api-free.deepl.com/v2"

# Common language codes for reference
_LANGUAGES = {
    "BG": "Bulgarian", "CS": "Czech", "DA": "Danish", "DE": "German",
    "EL": "Greek", "EN": "English", "ES": "Spanish", "ET": "Estonian",
    "FI": "Finnish", "FR": "French", "HU": "Hungarian", "ID": "Indonesian",
    "IT": "Italian", "JA": "Japanese", "KO": "Korean", "LT": "Lithuanian",
    "LV": "Latvian", "NB": "Norwegian", "NL": "Dutch", "PL": "Polish",
    "PT": "Portuguese", "RO": "Romanian", "RU": "Russian", "SK": "Slovak",
    "SL": "Slovenian", "SV": "Swedish", "TR": "Turkish", "UK": "Ukrainian",
    "ZH": "Chinese",
}


class ExtractTranslationTransformer(ChainableTransformer[dict, str]):
    """Extract the translated text from a translation result dict."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "translated" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        return value.get("translated", "")


def _get_api_key() -> Optional[str]:
    """Read the DeepL API key from the environment."""
    return os.environ.get("DEEPL_API_KEY") or os.environ.get("DEEPL_AUTH_KEY")


# ── Skills ─────────────────────────────────────────────────────────────────


@skill(
    name="translate_text",
    display_name="Translate Text",
    description="Translate text between languages using the DeepL API (requires DEEPL_API_KEY env var).",
    category="translate",
    tags=["translate", "language", "deepl"],
    icon="languages",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="DeepL API Key",
            description="DeepL API authentication key. Falls back to DEEPL_API_KEY env var.",
            type="secret",
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx",
        ),
        ConfigParam(
            name="base_url",
            display_name="API Base URL",
            description="DeepL API base URL (free or pro).",
            type="url",
            default=_BASE_URL,
            placeholder=_BASE_URL,
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
async def translate_text(
    text: str,
    target_lang: str,
    source_lang: str = "",
    formality: str = "default",
) -> dict:
    """Translate text to the target language."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": "DEEPL_API_KEY env var is required. Get a free key at https://www.deepl.com/pro-api", "success": False}

    endpoint = f"{_BASE_URL}/translate"
    check_host(endpoint)

    payload = {
        "text": [text],
        "target_lang": target_lang.upper(),
    }
    if source_lang:
        payload["source_lang"] = source_lang.upper()
    if formality != "default":
        payload["formality"] = formality

    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(endpoint, json=payload, headers=headers, timeout=15)
        if not resp.is_success:
            return {"error": f"DeepL API returned status {resp.status_code}: {resp.text}", "success": False}
        data = resp.json()
        translations = data.get("translations", [])
        if not translations:
            return {"error": "No translation returned", "success": False}
        t = translations[0]
        return {
            "text": text,
            "translated": t.get("text", ""),
            "detected_source": t.get("detected_source_language", source_lang.upper()),
            "target_lang": target_lang.upper(),
            "success": True,
        }


@skill(
    name="translate_batch",
    display_name="Batch Translate",
    description="Translate multiple texts at once using the DeepL API.",
    category="translate",
    tags=["translate", "batch", "deepl"],
    icon="languages",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def translate_batch(
    texts: list,
    target_lang: str,
    source_lang: str = "",
) -> dict:
    """Translate a list of texts to the target language in a single request."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": "DEEPL_API_KEY env var is required.", "success": False}

    endpoint = f"{_BASE_URL}/translate"
    check_host(endpoint)

    payload = {
        "text": texts,
        "target_lang": target_lang.upper(),
    }
    if source_lang:
        payload["source_lang"] = source_lang.upper()

    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(endpoint, json=payload, headers=headers, timeout=30)
        if not resp.is_success:
            return {"error": f"DeepL API returned status {resp.status_code}", "success": False}
        data = resp.json()
        translations = data.get("translations", [])
        results = []
        for i, t in enumerate(translations):
            results.append({
                "original": texts[i] if i < len(texts) else "",
                "translated": t.get("text", ""),
                "detected_source": t.get("detected_source_language", ""),
            })
        return {
            "target_lang": target_lang.upper(),
            "translations": results,
            "count": len(results),
            "success": True,
        }


@skill(
    name="translate_usage",
    display_name="Translation Usage",
    description="Check DeepL API usage (characters used/remaining).",
    category="translate",
    tags=["translate", "usage", "deepl"],
    icon="bar-chart",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def translate_usage() -> dict:
    """Check your DeepL API usage quota."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    api_key = _get_api_key()
    if not api_key:
        return {"error": "DEEPL_API_KEY env var is required.", "success": False}

    endpoint = f"{_BASE_URL}/usage"
    check_host(endpoint)

    headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, headers=headers, timeout=15)
        if not resp.is_success:
            return {"error": f"DeepL API returned status {resp.status_code}", "success": False}
        data = resp.json()
        used = data.get("character_count", 0)
        limit = data.get("character_limit", 0)
        return {
            "characters_used": used,
            "character_limit": limit,
            "characters_remaining": limit - used,
            "usage_percent": round((used / limit) * 100, 2) if limit else 0,
            "success": True,
        }


class TranslatePlugin(TransformerPlugin):
    """Plugin providing translation skills via DeepL API."""

    def __init__(self):
        super().__init__("translate")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "extract_translation": lambda _: ExtractTranslationTransformer("extract_translation"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "translate_text": translate_text.__skill__,
            "translate_batch": translate_batch.__skill__,
            "translate_usage": translate_usage.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="translate",
            display_name="Translate",
            description="Translate text between 30+ languages via DeepL API.",
            icon="languages",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
