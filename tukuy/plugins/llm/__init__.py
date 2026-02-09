"""LLM utilities plugin.

Provides transformers for cleaning messy LLM outputs and a token estimation skill.
Pure stdlib — no external dependencies.
"""

import re
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...skill import skill, ConfigParam, ConfigScope, RiskLevel


class CleanJsonOutputTransformer(ChainableTransformer[str, str]):
    """Extract clean JSON from messy LLM responses.

    Handles code fences, ``<think>`` tags, markdown wrappers, trailing
    commas, and other common artifacts.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        text = value

        # Strip <think>...</think> blocks (greedy, multiline)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

        # Extract from code fences (```json ... ``` or ``` ... ```)
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1)

        text = text.strip()

        # Try to find the outermost JSON object or array
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            if start == -1:
                continue
            # Find matching close by counting braces/brackets
            depth = 0
            for i in range(start, len(text)):
                if text[i] == start_char:
                    depth += 1
                elif text[i] == end_char:
                    depth -= 1
                    if depth == 0:
                        text = text[start : i + 1]
                        break
            if depth == 0:
                break

        # Remove trailing commas before } or ]
        text = re.sub(r",\s*([}\]])", r"\1", text)

        return text.strip()


class StripThinkTagsTransformer(ChainableTransformer[str, str]):
    """Remove ``<think>...</think>`` blocks from text."""

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return re.sub(r"<think>.*?</think>", "", value, flags=re.DOTALL).strip()


class ExtractCodeBlocksTransformer(ChainableTransformer[str, str]):
    """Extract all fenced code blocks from text.

    Returns them joined by newlines. If no code blocks are found, returns
    the original text.
    """

    def __init__(self, name: str, language: str = ""):
        super().__init__(name)
        self.language = language

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        if self.language:
            pattern = rf"```{re.escape(self.language)}\s*\n?(.*?)\n?\s*```"
        else:
            pattern = r"```(?:\w*)\s*\n?(.*?)\n?\s*```"
        blocks = re.findall(pattern, value, re.DOTALL)
        return "\n\n".join(b.strip() for b in blocks) if blocks else value


# ── Skill ──────────────────────────────────────────────────────────────────

@skill(
    name="token_estimate",
    description="Estimate token count for a string (approx 1 token per 4 chars).",
    category="llm",
    tags=["llm", "tokens"],
    idempotent=True,
    display_name="Estimate Tokens",
    icon="hash",
    risk_level=RiskLevel.SAFE,
    group="LLM",
    config_params=[
        ConfigParam(
            name="chars_per_token",
            display_name="Chars per Token",
            description="Average characters per token for estimation.",
            type="number",
            default=4,
            min=1,
            max=10,
            step=0.5,
        ),
    ],
)
def token_estimate(text: str) -> dict:
    """Estimate token count for a string."""
    char_count = len(text)
    word_count = len(text.split())
    # Rough heuristics used by most tokenizers
    estimated_tokens = max(char_count // 4, word_count)
    return {
        "char_count": char_count,
        "word_count": word_count,
        "estimated_tokens": estimated_tokens,
    }


class LlmPlugin(TransformerPlugin):
    """Plugin providing LLM output utilities."""

    def __init__(self):
        super().__init__("llm")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "clean_json_output": lambda _: CleanJsonOutputTransformer("clean_json_output"),
            "strip_think_tags": lambda _: StripThinkTagsTransformer("strip_think_tags"),
            "extract_code_blocks": lambda params: ExtractCodeBlocksTransformer(
                "extract_code_blocks",
                language=params.get("language", ""),
            ),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "token_estimate": token_estimate.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest
        return PluginManifest(
            name="llm",
            display_name="LLM Utilities",
            description="Clean messy LLM outputs and estimate token counts.",
            icon="brain",
            group="Code",
        )
