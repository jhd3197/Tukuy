"""Diff and text comparison plugin.

Provides unified diffs, similarity scoring, and fuzzy matching.
Pure stdlib — no external dependencies.
"""

import difflib
from typing import Any, Dict, List, Optional, Union

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


class UnifiedDiffTransformer(ChainableTransformer[dict, str]):
    """Generate a unified diff between two strings.

    Expects input as ``{"a": "...", "b": "..."}`` or a two-element list.
    """

    def __init__(self, name: str, context_lines: int = 3):
        super().__init__(name)
        self.context_lines = context_lines

    def validate(self, value: Any) -> bool:
        if isinstance(value, dict):
            return "a" in value and "b" in value
        if isinstance(value, (list, tuple)):
            return len(value) >= 2
        return False

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        if isinstance(value, (list, tuple)):
            a, b = str(value[0]), str(value[1])
        else:
            a, b = str(value["a"]), str(value["b"])

        a_lines = a.splitlines(keepends=True)
        b_lines = b.splitlines(keepends=True)

        diff = difflib.unified_diff(
            a_lines,
            b_lines,
            fromfile="a",
            tofile="b",
            n=self.context_lines,
        )
        return "".join(diff)


class SimilarityScoreTransformer(ChainableTransformer[dict, float]):
    """Compute similarity ratio between two strings using SequenceMatcher.

    Expects input as ``{"a": "...", "b": "..."}`` or a two-element list.
    Returns a float between 0.0 (no match) and 1.0 (identical).
    """

    def validate(self, value: Any) -> bool:
        if isinstance(value, dict):
            return "a" in value and "b" in value
        if isinstance(value, (list, tuple)):
            return len(value) >= 2
        return False

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> float:
        if isinstance(value, (list, tuple)):
            a, b = str(value[0]), str(value[1])
        else:
            a, b = str(value["a"]), str(value["b"])

        return difflib.SequenceMatcher(None, a, b).ratio()


class FuzzyMatchTransformer(ChainableTransformer[dict, list]):
    """Find the closest matches to a query from a list of candidates.

    Expects input as ``{"query": "...", "candidates": ["...", ...]}``.
    Returns a list of ``{"match": str, "score": float}`` dicts.
    """

    def __init__(self, name: str, n: int = 3, cutoff: float = 0.6):
        super().__init__(name)
        self.n = n
        self.cutoff = cutoff

    def validate(self, value: Any) -> bool:
        return (
            isinstance(value, dict)
            and "query" in value
            and "candidates" in value
            and isinstance(value["candidates"], list)
        )

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> list:
        query = str(value["query"])
        candidates = [str(c) for c in value["candidates"]]
        matches = difflib.get_close_matches(query, candidates, n=self.n, cutoff=self.cutoff)
        result = []
        for m in matches:
            score = difflib.SequenceMatcher(None, query, m).ratio()
            result.append({"match": m, "score": round(score, 4)})
        return result


class ApplyPatchTransformer(ChainableTransformer[dict, str]):
    """Apply a unified diff patch to a source string.

    Expects input as ``{"source": "...", "patch": "..."}``.
    Uses a simple line-based approach for standard unified diffs.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "source" in value and "patch" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        source_lines = value["source"].splitlines(keepends=True)
        patch_text = value["patch"]

        # Parse hunks from unified diff
        hunks = []
        current_hunk = None
        for line in patch_text.splitlines(keepends=True):
            if line.startswith("@@"):
                # Parse @@ -start,count +start,count @@
                import re
                m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if m:
                    current_hunk = {
                        "old_start": int(m.group(1)) - 1,
                        "lines": [],
                    }
                    hunks.append(current_hunk)
            elif current_hunk is not None:
                if line.startswith("---") or line.startswith("+++"):
                    continue
                current_hunk["lines"].append(line)

        if not hunks:
            return value["source"]

        # Apply hunks in reverse order to preserve line numbers
        result = list(source_lines)
        for hunk in reversed(hunks):
            idx = hunk["old_start"]
            new_lines = []
            remove_count = 0
            for line in hunk["lines"]:
                if line.startswith("-"):
                    remove_count += 1
                elif line.startswith("+"):
                    content = line[1:]
                    if not content.endswith("\n"):
                        content += "\n"
                    new_lines.append(content)
                elif line.startswith(" "):
                    content = line[1:]
                    if not content.endswith("\n"):
                        content += "\n"
                    new_lines.append(content)
                    remove_count += 1

            result[idx : idx + remove_count] = new_lines

        return "".join(result)


class CharDiffTransformer(ChainableTransformer[dict, list]):
    """Character-level diff between two strings.

    Expects input as ``{"a": "...", "b": "..."}`` or a two-element list.
    Returns a list of ``{"tag": str, "a": str, "b": str}`` operations.
    Tags: "equal", "replace", "insert", "delete".
    """

    def validate(self, value: Any) -> bool:
        if isinstance(value, dict):
            return "a" in value and "b" in value
        if isinstance(value, (list, tuple)):
            return len(value) >= 2
        return False

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> list:
        if isinstance(value, (list, tuple)):
            a, b = str(value[0]), str(value[1])
        else:
            a, b = str(value["a"]), str(value["b"])

        matcher = difflib.SequenceMatcher(None, a, b)
        ops = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            ops.append({
                "tag": tag,
                "a": a[i1:i2],
                "b": b[j1:j2],
            })
        return ops


class DiffPlugin(TransformerPlugin):
    """Plugin providing diff and text comparison transformers."""

    def __init__(self):
        super().__init__("diff")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "unified_diff": lambda params: UnifiedDiffTransformer(
                "unified_diff",
                context_lines=params.get("context_lines", 3),
            ),
            "similarity_score": lambda _: SimilarityScoreTransformer("similarity_score"),
            "fuzzy_match": lambda params: FuzzyMatchTransformer(
                "fuzzy_match",
                n=params.get("n", 3),
                cutoff=params.get("cutoff", 0.6),
            ),
            "apply_patch": lambda _: ApplyPatchTransformer("apply_patch"),
            "char_diff": lambda _: CharDiffTransformer("char_diff"),
        }
