"""HTML validation plugin.

Provides transformers for validating HTML structure, semantic correctness,
and accessibility (WCAG) compliance.

Pure stdlib — no external dependencies (regex-based).
"""

import re
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


# Tags that do not need closing
VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})

# Semantic landmark tags
LANDMARK_TAGS = frozenset({
    "header", "footer", "main", "nav", "aside", "section", "article",
})


class ValidateHtmlTransformer(ChainableTransformer[str, dict]):
    """Validate HTML for structural correctness.

    Returns a dict with:

    - ``valid`` — True if no errors found
    - ``errors`` — list of error message strings
    - ``warnings`` — list of warning message strings
    - ``stats`` — dict with counts (tags, void tags, unclosed tags, etc.)
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        errors: List[str] = []
        warnings: List[str] = []

        # Strip comments and scripts/style content for tag analysis
        html = re.sub(r"<!--[\s\S]*?-->", "", value)
        html_for_tags = re.sub(r"<(script|style)[^>]*>[\s\S]*?</\1>", "", html, flags=re.IGNORECASE)

        # Find all tags
        tag_pattern = re.compile(r"<(/?)(\w+)([^>]*)(/?)>", re.IGNORECASE)
        all_tags = tag_pattern.findall(html_for_tags)

        open_stack: List[str] = []
        tag_count = 0
        void_count = 0

        for is_close, tag_name, attrs, self_close in all_tags:
            tag_lower = tag_name.lower()
            tag_count += 1

            if tag_lower in VOID_ELEMENTS:
                void_count += 1
                continue

            if self_close == "/":
                # Self-closing (XHTML style)
                continue

            if is_close == "/":
                # Closing tag
                if not open_stack:
                    errors.append(f"Unexpected closing tag </{tag_lower}> with no matching open tag")
                elif open_stack[-1] == tag_lower:
                    open_stack.pop()
                else:
                    # Try to find a match deeper in the stack
                    if tag_lower in open_stack:
                        while open_stack and open_stack[-1] != tag_lower:
                            unclosed = open_stack.pop()
                            errors.append(f"Unclosed tag <{unclosed}>")
                        if open_stack:
                            open_stack.pop()
                    else:
                        errors.append(f"Unexpected closing tag </{tag_lower}> with no matching open tag")
            else:
                # Opening tag
                open_stack.append(tag_lower)

        for unclosed in reversed(open_stack):
            errors.append(f"Unclosed tag <{unclosed}>")

        # Check for DOCTYPE
        if not re.search(r"<!DOCTYPE\s+html", value, re.IGNORECASE):
            warnings.append("Missing <!DOCTYPE html> declaration")

        # Check for <html> root
        if not re.search(r"<html[\s>]", value, re.IGNORECASE):
            warnings.append("Missing <html> root element")

        # Check for <head> and <body>
        if not re.search(r"<head[\s>]", value, re.IGNORECASE):
            warnings.append("Missing <head> element")
        if not re.search(r"<body[\s>]", value, re.IGNORECASE):
            warnings.append("Missing <body> element")

        # Check for <title>
        if not re.search(r"<title[^>]*>", value, re.IGNORECASE):
            warnings.append("Missing <title> element")

        # Check for lang attribute on <html>
        html_tag = re.search(r"<html([^>]*)>", value, re.IGNORECASE)
        if html_tag and "lang=" not in html_tag.group(1).lower():
            warnings.append('<html> element missing lang attribute')

        # Check for charset meta
        if not re.search(r'<meta[^>]+charset=', value, re.IGNORECASE):
            warnings.append("Missing charset meta tag")

        # Check for semantic landmarks
        has_landmarks = any(
            re.search(rf"<{tag}[\s>]", value, re.IGNORECASE)
            for tag in LANDMARK_TAGS
        )
        if not has_landmarks:
            warnings.append("No semantic landmark elements found (header, main, nav, footer, etc.)")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": {
                "total_tags": tag_count,
                "void_tags": void_count,
                "unclosed_tags": len([e for e in errors if "Unclosed" in e]),
            },
        }


class ValidateAccessibilityTransformer(ChainableTransformer[str, dict]):
    """Validate HTML for WCAG accessibility compliance.

    Checks for:
    - Images missing alt text
    - Form inputs missing labels
    - Missing heading hierarchy (h1-h6 order)
    - Missing ARIA landmarks
    - Links with non-descriptive text
    - Missing skip navigation link
    - Color contrast hints (flags inline color styles)

    Returns a dict with ``score`` (0-100), ``issues``, and ``passes``.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        issues: List[Dict[str, str]] = []
        passes: List[str] = []

        # 1. Images without alt text
        imgs = re.findall(r"<img([^>]*)>", value, re.IGNORECASE)
        imgs_without_alt = [
            img for img in imgs
            if not re.search(r'\balt\s*=', img, re.IGNORECASE)
        ]
        if imgs_without_alt:
            issues.append({
                "rule": "img-alt",
                "severity": "error",
                "message": f"{len(imgs_without_alt)} image(s) missing alt attribute",
            })
        elif imgs:
            passes.append("All images have alt attributes")

        # 2. Form inputs without labels or aria-label
        inputs = re.findall(r"<input([^>]*)>", value, re.IGNORECASE)
        unlabeled_inputs = []
        for inp in inputs:
            inp_lower = inp.lower()
            # Skip hidden and submit/button inputs
            if 'type="hidden"' in inp_lower or "type='hidden'" in inp_lower:
                continue
            if 'type="submit"' in inp_lower or 'type="button"' in inp_lower:
                continue
            has_id = re.search(r'\bid\s*=\s*["\'](\w+)', inp, re.IGNORECASE)
            has_aria = re.search(r'\baria-label', inp, re.IGNORECASE)
            has_title = re.search(r'\btitle\s*=', inp, re.IGNORECASE)
            if has_id:
                # Check if a <label for="id"> exists
                input_id = has_id.group(1)
                if not re.search(rf'<label[^>]+for\s*=\s*["\']?{re.escape(input_id)}', value, re.IGNORECASE):
                    if not has_aria and not has_title:
                        unlabeled_inputs.append(inp)
            elif not has_aria and not has_title:
                unlabeled_inputs.append(inp)

        if unlabeled_inputs:
            issues.append({
                "rule": "input-label",
                "severity": "error",
                "message": f"{len(unlabeled_inputs)} form input(s) missing associated label or aria-label",
            })
        elif inputs:
            passes.append("All form inputs have labels")

        # 3. Heading hierarchy
        headings = re.findall(r"<h([1-6])[\s>]", value, re.IGNORECASE)
        heading_levels = [int(h) for h in headings]
        if heading_levels:
            if heading_levels[0] != 1:
                issues.append({
                    "rule": "heading-order",
                    "severity": "warning",
                    "message": f"First heading is h{heading_levels[0]}, expected h1",
                })
            for i in range(1, len(heading_levels)):
                if heading_levels[i] > heading_levels[i - 1] + 1:
                    issues.append({
                        "rule": "heading-order",
                        "severity": "warning",
                        "message": f"Heading level skipped: h{heading_levels[i-1]} followed by h{heading_levels[i]}",
                    })
                    break
            if not any(i for i in issues if i["rule"] == "heading-order"):
                passes.append("Heading hierarchy is correct")
        else:
            issues.append({
                "rule": "heading-order",
                "severity": "warning",
                "message": "No headings found in the document",
            })

        # 4. ARIA landmarks / semantic elements
        has_main = bool(re.search(r'<main[\s>]|role\s*=\s*["\']main["\']', value, re.IGNORECASE))
        has_nav = bool(re.search(r'<nav[\s>]|role\s*=\s*["\']navigation["\']', value, re.IGNORECASE))
        if has_main:
            passes.append("Has main landmark")
        else:
            issues.append({
                "rule": "landmark-main",
                "severity": "warning",
                "message": "Missing <main> or role='main' landmark",
            })
        if has_nav:
            passes.append("Has navigation landmark")

        # 5. Links with non-descriptive text
        links = re.findall(r"<a[^>]*>(.*?)</a>", value, re.IGNORECASE | re.DOTALL)
        bad_link_texts = {"click here", "here", "read more", "more", "link"}
        non_descriptive = [
            link for link in links
            if re.sub(r"<[^>]+>", "", link).strip().lower() in bad_link_texts
        ]
        if non_descriptive:
            issues.append({
                "rule": "link-name",
                "severity": "warning",
                "message": f"{len(non_descriptive)} link(s) with non-descriptive text (e.g. 'click here')",
            })
        elif links:
            passes.append("All links have descriptive text")

        # 6. Skip navigation
        has_skip_nav = bool(re.search(
            r'<a[^>]+href\s*=\s*["\']#(main|content|skip)',
            value, re.IGNORECASE,
        ))
        if has_skip_nav:
            passes.append("Has skip navigation link")
        else:
            issues.append({
                "rule": "skip-nav",
                "severity": "warning",
                "message": "Missing skip navigation link",
            })

        # 7. Viewport meta tag
        has_viewport = bool(re.search(
            r'<meta[^>]+name\s*=\s*["\']viewport["\']',
            value, re.IGNORECASE,
        ))
        if has_viewport:
            passes.append("Has viewport meta tag")
        else:
            issues.append({
                "rule": "viewport",
                "severity": "warning",
                "message": "Missing viewport meta tag for responsive design",
            })

        # Calculate score
        total_checks = len(issues) + len(passes)
        score = round(len(passes) / total_checks * 100) if total_checks else 100

        return {
            "score": score,
            "issues": issues,
            "passes": passes,
            "total_checks": total_checks,
        }


class HtmlValidatePlugin(TransformerPlugin):
    """Plugin providing HTML validation and accessibility checking."""

    def __init__(self):
        super().__init__("html_validate")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "validate_html": lambda _: ValidateHtmlTransformer("validate_html"),
            "validate_accessibility": lambda _: ValidateAccessibilityTransformer(
                "validate_accessibility",
            ),
        }
