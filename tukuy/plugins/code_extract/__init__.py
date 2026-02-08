"""Code extraction plugin.

Provides transformers for extracting code from messy LLM output:
fenced code blocks with language-to-filename mapping, full HTML document
extraction with inline style/script splitting, and reasoning preamble
stripping.

Pure stdlib — no external dependencies.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


class ExtractFencedFilesTransformer(ChainableTransformer[str, dict]):
    """Extract markdown-fenced code blocks and map them to filenames.

    Returns a dict of ``{filename: content}`` based on the fenced language
    tag.  Handles duplicate filenames by appending a numeric suffix.

    Default mapping::

        html       -> index.html
        css        -> styles.css
        js         -> script.js
        javascript -> script.js
        python     -> main.py
        json       -> data.json
        xml        -> data.xml
        svg        -> image.svg
    """

    DEFAULT_LANG_MAP = {
        "html": "index.html",
        "css": "styles.css",
        "js": "script.js",
        "javascript": "script.js",
        "python": "main.py",
        "py": "main.py",
        "json": "data.json",
        "xml": "data.xml",
        "svg": "image.svg",
        "typescript": "main.ts",
        "ts": "main.ts",
        "jsx": "app.jsx",
        "tsx": "app.tsx",
    }

    def __init__(self, name: str, lang_map: Optional[Dict[str, str]] = None):
        super().__init__(name)
        self.lang_map = lang_map if lang_map is not None else dict(self.DEFAULT_LANG_MAP)

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        pattern = r"```(\w+)\s*\n([\s\S]*?)```"
        matches = re.findall(pattern, value)
        if not matches:
            return {}

        files: Dict[str, str] = {}
        used_names: set = set()

        for lang, content in matches:
            lang_lower = lang.lower()
            filename = self.lang_map.get(lang_lower)
            if not filename:
                continue

            # Handle duplicates
            if filename in used_names:
                base, ext = filename.rsplit(".", 1)
                counter = 2
                while f"{base}_{counter}.{ext}" in used_names:
                    counter += 1
                filename = f"{base}_{counter}.{ext}"

            used_names.add(filename)
            files[filename] = content.strip()

        return files


class ExtractHtmlDocumentTransformer(ChainableTransformer[str, dict]):
    """Extract a full HTML document from mixed text.

    Returns a dict with keys:

    - ``html`` — the full HTML document (``<!DOCTYPE html>`` … ``</html>``)
    - ``styles`` — CSS extracted from inline ``<style>`` blocks (or empty)
    - ``scripts`` — JS extracted from inline ``<script>`` blocks (or empty)
    - ``found`` — boolean indicating whether an HTML document was found

    If no HTML document is found, ``html`` is empty and ``found`` is False.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        text = value.strip()

        # Strip wrapping code fences
        text = re.sub(r"^```\w*\s*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)

        # Look for a full HTML document
        html_match = re.search(
            r"(<!DOCTYPE\s+html[\s\S]*?</html>|<html[\s\S]*?</html>)",
            text,
            re.IGNORECASE,
        )

        if not html_match:
            return {"html": "", "styles": "", "scripts": "", "found": False}

        html_content = html_match.group(1)

        # Extract inline <style> blocks
        style_blocks = re.findall(
            r"<style[^>]*>([\s\S]*?)</style>", html_content, re.IGNORECASE
        )
        styles = "\n\n".join(s.strip() for s in style_blocks if s.strip())

        # Extract inline <script> blocks (skip external src scripts)
        script_blocks = re.findall(
            r"<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>", html_content, re.IGNORECASE
        )
        scripts = "\n\n".join(s.strip() for s in script_blocks if s.strip())

        return {
            "html": html_content,
            "styles": styles,
            "scripts": scripts,
            "found": True,
        }


class StripReasoningPreambleTransformer(ChainableTransformer[str, str]):
    """Strip chain-of-thought reasoning preamble before actual code output.

    Some models (e.g. Kimi K2.5, DeepSeek-R1) emit reasoning text before
    the actual code.  This transformer removes everything before the first
    code fence or HTML tag.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        text = value

        # Already starts with a code fence — nothing to strip
        if text.lstrip().startswith("```"):
            return text

        # Find the first code fence (```html, ```css, ```js, etc.)
        fence_match = re.search(r"```(?:html|css|javascript|js|python|json)\b", text, re.IGNORECASE)
        if fence_match:
            return text[fence_match.start():]

        # Find raw HTML (<!DOCTYPE or <html)
        html_match = re.search(r"<!DOCTYPE\s+html|<html[\s>]", text, re.IGNORECASE)
        if html_match:
            return text[html_match.start():]

        return text


class CodeExtractPlugin(TransformerPlugin):
    """Plugin providing code extraction transformers for LLM output."""

    def __init__(self):
        super().__init__("code_extract")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "extract_fenced_files": lambda params: ExtractFencedFilesTransformer(
                "extract_fenced_files",
                lang_map=params.get("lang_map"),
            ),
            "extract_html_document": lambda _: ExtractHtmlDocumentTransformer(
                "extract_html_document",
            ),
            "strip_reasoning_preamble": lambda _: StripReasoningPreambleTransformer(
                "strip_reasoning_preamble",
            ),
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest
        return PluginManifest(
            name="code_extract",
            display_name="Code Extract",
            description="Extract fenced code blocks, HTML documents, and strip reasoning preambles.",
            icon="file-code",
            group="Code",
        )
