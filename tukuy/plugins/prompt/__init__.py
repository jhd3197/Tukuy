"""Prompt engineering plugin.

Provides transformers for prompt templating, variable extraction,
prompt composition, and token-aware truncation.

Pure stdlib — no external dependencies.
"""

import re
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


class PromptTemplateTransformer(ChainableTransformer[dict, str]):
    """Render a prompt template with variable substitution.

    Expects input as ``{"template": "...", "variables": {...}}``.
    Supports ``{{var}}`` syntax with optional defaults: ``{{var|default}}``.
    """

    def __init__(self, name: str, strict: bool = False):
        super().__init__(name)
        self.strict = strict

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "template" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        template = value["template"]
        variables = value.get("variables", {})

        def replacer(match):
            expr = match.group(1).strip()
            if "|" in expr:
                var_name, default = expr.split("|", 1)
                var_name = var_name.strip()
                default = default.strip()
            else:
                var_name = expr
                default = None

            if var_name in variables:
                val = variables[var_name]
                return str(val) if not isinstance(val, str) else val

            if default is not None:
                return default
            if self.strict:
                raise ValueError(f"Missing template variable: {var_name}")
            return match.group(0)  # Leave unreplaced

        return re.sub(r"\{\{(.+?)\}\}", replacer, template)


class ExtractVariablesTransformer(ChainableTransformer[str, list]):
    """Extract all ``{{variable}}`` placeholders from a template string.

    Returns a list of ``{"name": str, "default": str|None, "required": bool}``.
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> list:
        seen = set()
        variables = []

        for match in re.finditer(r"\{\{(.+?)\}\}", value):
            expr = match.group(1).strip()
            if "|" in expr:
                name, default = expr.split("|", 1)
                name = name.strip()
                default = default.strip()
            else:
                name = expr
                default = None

            if name not in seen:
                seen.add(name)
                variables.append({
                    "name": name,
                    "default": default,
                    "required": default is None,
                })

        return variables


class PromptChainTransformer(ChainableTransformer[dict, str]):
    """Compose multiple prompt sections into a single prompt.

    Expects input as::

        {
            "sections": [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
            ],
            "separator": "\\n\\n",
            "format": "raw"  # or "chat"
        }

    With ``format="chat"``, produces ChatML-style output.
    With ``format="raw"`` (default), joins sections with separator.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "sections" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        sections = value["sections"]
        separator = value.get("separator", "\n\n")
        fmt = value.get("format", "raw")

        if fmt == "chat":
            parts = []
            for s in sections:
                role = s.get("role", "user")
                content = s.get("content", "")
                parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
            return "\n".join(parts)

        # raw format
        parts = []
        for s in sections:
            if isinstance(s, str):
                parts.append(s)
            elif isinstance(s, dict):
                content = s.get("content", "")
                role = s.get("role", "")
                if role:
                    parts.append(f"[{role.upper()}]\n{content}")
                else:
                    parts.append(content)

        return separator.join(parts)


class TruncateToTokensTransformer(ChainableTransformer[dict, str]):
    """Truncate text to fit within a token budget.

    Expects input as ``{"text": "...", "max_tokens": 1000}``.
    Uses the ~4 chars/token heuristic. Optionally preserves sentence
    boundaries when ``preserve_sentences=True``.
    """

    def __init__(self, name: str, chars_per_token: int = 4):
        super().__init__(name)
        self.chars_per_token = chars_per_token

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "text" in value and "max_tokens" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        text = value["text"]
        max_tokens = value["max_tokens"]
        preserve_sentences = value.get("preserve_sentences", False)
        suffix = value.get("suffix", "...")

        max_chars = max_tokens * self.chars_per_token

        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars]

        if preserve_sentences:
            # Find the last sentence boundary
            last_period = max(
                truncated.rfind(". "),
                truncated.rfind("! "),
                truncated.rfind("? "),
                truncated.rfind(".\n"),
                truncated.rfind("!\n"),
                truncated.rfind("?\n"),
            )
            if last_period > max_chars * 0.5:
                truncated = truncated[: last_period + 1]
                return truncated

        return truncated.rstrip() + suffix


class PromptEscapeTransformer(ChainableTransformer[str, str]):
    """Escape special characters in user input to prevent prompt injection.

    Wraps the input in delimiter tags and escapes any existing delimiters.
    """

    def __init__(self, name: str, delimiter: str = "---"):
        super().__init__(name)
        self.delimiter = delimiter

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        # Escape the delimiter within the text
        escaped = value.replace(self.delimiter, self.delimiter.replace("-", "\\-"))
        return f"{self.delimiter}\n{escaped}\n{self.delimiter}"


class PromptPlugin(TransformerPlugin):
    """Plugin providing prompt engineering transformers."""

    def __init__(self):
        super().__init__("prompt")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "prompt_template": lambda params: PromptTemplateTransformer(
                "prompt_template",
                strict=params.get("strict", False),
            ),
            "extract_variables": lambda _: ExtractVariablesTransformer("extract_variables"),
            "prompt_chain": lambda _: PromptChainTransformer("prompt_chain"),
            "truncate_to_tokens": lambda params: TruncateToTokensTransformer(
                "truncate_to_tokens",
                chars_per_token=params.get("chars_per_token", 4),
            ),
            "prompt_escape": lambda params: PromptEscapeTransformer(
                "prompt_escape",
                delimiter=params.get("delimiter", "---"),
            ),
        }
