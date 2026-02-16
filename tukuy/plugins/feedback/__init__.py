"""Feedback / questionnaire plugin.

Skills-only plugin providing feedback form creation, validation,
submission, analysis, and summary operations.

Pure stdlib — no external dependencies.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from ...plugins.base import TransformerPlugin
from ...skill import skill, RiskLevel


# ---------------------------------------------------------------------------
# Valid question types
# ---------------------------------------------------------------------------

_VALID_QUESTION_TYPES = {"text", "rating", "choice", "multi_choice", "yes_no", "scale"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize_question(q: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Validate and normalize a single question dict."""
    if not isinstance(q, dict):
        raise ValueError(f"Question at index {index} must be a dict")

    text = q.get("text")
    if not text or not isinstance(text, str):
        raise ValueError(f"Question at index {index} must have a non-empty 'text' string")

    qtype = q.get("type")
    if qtype not in _VALID_QUESTION_TYPES:
        raise ValueError(
            f"Question at index {index} has invalid type '{qtype}'. "
            f"Must be one of: {', '.join(sorted(_VALID_QUESTION_TYPES))}"
        )

    qid = q.get("id") or f"q{index + 1}"
    required = q.get("required", True)

    normalized: Dict[str, Any] = {
        "id": qid,
        "text": text,
        "type": qtype,
        "required": required,
    }

    if qtype == "text":
        if "max_length" in q:
            normalized["max_length"] = int(q["max_length"])
        if "placeholder" in q:
            normalized["placeholder"] = str(q["placeholder"])

    elif qtype == "rating":
        normalized["min_value"] = int(q.get("min_value", 1))
        normalized["max_value"] = int(q.get("max_value", 5))

    elif qtype == "choice":
        options = q.get("options")
        if not options or not isinstance(options, list) or len(options) == 0:
            raise ValueError(
                f"Question at index {index} (type='choice') must have a non-empty 'options' list"
            )
        normalized["options"] = [str(o) for o in options]

    elif qtype == "multi_choice":
        options = q.get("options")
        if not options or not isinstance(options, list) or len(options) == 0:
            raise ValueError(
                f"Question at index {index} (type='multi_choice') must have a non-empty 'options' list"
            )
        normalized["options"] = [str(o) for o in options]
        if "min_select" in q:
            normalized["min_select"] = int(q["min_select"])
        if "max_select" in q:
            normalized["max_select"] = int(q["max_select"])

    elif qtype == "yes_no":
        pass

    elif qtype == "scale":
        normalized["min_value"] = int(q.get("min_value", 1))
        normalized["max_value"] = int(q.get("max_value", 10))
        if "min_label" in q:
            normalized["min_label"] = str(q["min_label"])
        if "max_label" in q:
            normalized["max_label"] = str(q["max_label"])

    return normalized


def _validate_responses(form: dict, responses: Dict[str, Any]) -> List[Dict[str, str]]:
    """Validate responses against a form definition. Returns list of error dicts."""
    errors: List[Dict[str, str]] = []
    questions = form.get("questions", [])

    for q in questions:
        qid = q["id"]
        qtype = q["type"]
        required = q.get("required", True)
        answer = responses.get(qid)

        # Check required
        if answer is None:
            if required:
                errors.append({"question_id": qid, "error": "Required question not answered"})
            continue

        # Type-specific validation
        if qtype == "text":
            if not isinstance(answer, str):
                errors.append({"question_id": qid, "error": "Answer must be a string"})
                continue
            max_length = q.get("max_length")
            if max_length is not None and len(answer) > max_length:
                errors.append({
                    "question_id": qid,
                    "error": f"Answer exceeds max length of {max_length}",
                })

        elif qtype == "rating":
            if not isinstance(answer, (int, float)):
                errors.append({"question_id": qid, "error": "Answer must be a number"})
                continue
            min_val = q.get("min_value", 1)
            max_val = q.get("max_value", 5)
            if answer < min_val or answer > max_val:
                errors.append({
                    "question_id": qid,
                    "error": f"Answer must be between {min_val} and {max_val}",
                })

        elif qtype == "choice":
            if not isinstance(answer, str):
                errors.append({"question_id": qid, "error": "Answer must be a string"})
                continue
            if answer not in q.get("options", []):
                errors.append({
                    "question_id": qid,
                    "error": f"Answer must be one of: {', '.join(q['options'])}",
                })

        elif qtype == "multi_choice":
            if not isinstance(answer, list):
                errors.append({"question_id": qid, "error": "Answer must be a list"})
                continue
            options = q.get("options", [])
            for item in answer:
                if not isinstance(item, str):
                    errors.append({"question_id": qid, "error": "All selections must be strings"})
                    break
                if item not in options:
                    errors.append({
                        "question_id": qid,
                        "error": f"Invalid selection '{item}'. Must be one of: {', '.join(options)}",
                    })
                    break
            else:
                # All items valid, check min/max select
                min_select = q.get("min_select")
                max_select = q.get("max_select")
                if min_select is not None and len(answer) < min_select:
                    errors.append({
                        "question_id": qid,
                        "error": f"Must select at least {min_select} options",
                    })
                if max_select is not None and len(answer) > max_select:
                    errors.append({
                        "question_id": qid,
                        "error": f"Must select at most {max_select} options",
                    })

        elif qtype == "yes_no":
            if not isinstance(answer, bool):
                errors.append({"question_id": qid, "error": "Answer must be a boolean"})

        elif qtype == "scale":
            if not isinstance(answer, (int, float)):
                errors.append({"question_id": qid, "error": "Answer must be a number"})
                continue
            min_val = q.get("min_value", 1)
            max_val = q.get("max_value", 10)
            if answer < min_val or answer > max_val:
                errors.append({
                    "question_id": qid,
                    "error": f"Answer must be between {min_val} and {max_val}",
                })

    return errors


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@skill(
    name="feedback_create",
    description="Create a feedback form definition with typed questions.",
    category="interaction",
    tags=["feedback", "form", "questionnaire", "survey"],
    idempotent=True,
    display_name="Create Feedback Form",
    icon="clipboard-list",
    risk_level=RiskLevel.SAFE,
    group="Feedback",
)
def feedback_create(
    title: str,
    questions: List[Dict[str, Any]],
    description: str = "",
) -> dict:
    """Create a feedback form definition.

    Args:
        title: The title of the feedback form.
        questions: List of question dicts, each with 'text', 'type', and type-specific fields.
        description: Optional description for the form.
    """
    if not title or not isinstance(title, str):
        raise ValueError("Form title must be a non-empty string")
    if not questions or not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("Form must have at least one question")

    normalized = [_normalize_question(q, i) for i, q in enumerate(questions)]

    return {
        "form_id": uuid.uuid4().hex[:12],
        "title": title,
        "description": description,
        "questions": normalized,
        "question_count": len(normalized),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@skill(
    name="feedback_validate",
    description="Validate responses against a feedback form definition.",
    category="interaction",
    tags=["feedback", "validate", "questionnaire"],
    idempotent=True,
    display_name="Validate Feedback",
    icon="clipboard-list",
    risk_level=RiskLevel.SAFE,
    group="Feedback",
)
def feedback_validate(form: dict, responses: Dict[str, Any]) -> dict:
    """Validate responses against a form.

    Args:
        form: The form definition (output of feedback_create).
        responses: Dict mapping question id to the answer value.
    """
    errors = _validate_responses(form, responses)
    total = len(form.get("questions", []))
    answered = sum(1 for q in form.get("questions", []) if q["id"] in responses)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "answered": answered,
        "total": total,
    }


@skill(
    name="feedback_submit",
    description="Package a validated feedback submission.",
    category="interaction",
    tags=["feedback", "submit", "questionnaire"],
    idempotent=False,
    side_effects=False,
    display_name="Submit Feedback",
    icon="clipboard-list",
    risk_level=RiskLevel.SAFE,
    group="Feedback",
)
def feedback_submit(
    form: dict,
    responses: Dict[str, Any],
    respondent: str = "",
) -> dict:
    """Package a validated feedback submission.

    Args:
        form: The form definition (output of feedback_create).
        responses: Dict mapping question id to the answer value.
        respondent: Optional respondent identifier.
    """
    errors = _validate_responses(form, responses)
    if errors:
        msgs = "; ".join(f"{e['question_id']}: {e['error']}" for e in errors)
        raise ValueError(f"Validation failed: {msgs}")

    questions = form.get("questions", [])
    q_map = {q["id"]: q for q in questions}

    response_list = []
    for qid, answer in responses.items():
        q = q_map.get(qid)
        if q is not None:
            response_list.append({
                "question_id": qid,
                "question_text": q["text"],
                "question_type": q["type"],
                "answer": answer,
            })

    return {
        "submission_id": uuid.uuid4().hex[:12],
        "form_id": form.get("form_id", ""),
        "form_title": form.get("title", ""),
        "respondent": respondent,
        "responses": response_list,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "response_count": len(response_list),
    }


@skill(
    name="feedback_analyze",
    description="Analyze multiple feedback submissions for a form.",
    category="interaction",
    tags=["feedback", "analyze", "statistics"],
    idempotent=True,
    display_name="Analyze Feedback",
    icon="clipboard-list",
    risk_level=RiskLevel.SAFE,
    group="Feedback",
)
def feedback_analyze(form: dict, submissions: List[dict]) -> dict:
    """Analyze multiple feedback submissions.

    Args:
        form: The form definition (output of feedback_create).
        submissions: List of submission dicts (output of feedback_submit).
    """
    questions = form.get("questions", [])
    analysis: Dict[str, Any] = {}

    for q in questions:
        qid = q["id"]
        qtype = q["type"]

        # Collect answers for this question across all submissions
        answers = []
        for sub in submissions:
            for resp in sub.get("responses", []):
                if resp.get("question_id") == qid:
                    answers.append(resp["answer"])

        stats: Dict[str, Any] = {
            "question_text": q["text"],
            "question_type": qtype,
            "response_count": len(answers),
        }

        if qtype == "text":
            lengths = [len(a) for a in answers if isinstance(a, str)]
            stats["avg_length"] = round(sum(lengths) / len(lengths), 2) if lengths else 0
            stats["responses"] = [a for a in answers if isinstance(a, str)]

        elif qtype in ("rating", "scale"):
            nums = [a for a in answers if isinstance(a, (int, float))]
            if nums:
                stats["average"] = round(sum(nums) / len(nums), 2)
                stats["min"] = min(nums)
                stats["max"] = max(nums)
                distribution: Dict[str, int] = {}
                for n in nums:
                    key = str(n)
                    distribution[key] = distribution.get(key, 0) + 1
                stats["distribution"] = distribution
            else:
                stats["average"] = 0
                stats["min"] = 0
                stats["max"] = 0
                stats["distribution"] = {}

        elif qtype == "choice":
            distribution = {}
            for a in answers:
                if isinstance(a, str):
                    distribution[a] = distribution.get(a, 0) + 1
            stats["distribution"] = distribution
            if distribution:
                stats["most_common"] = max(distribution, key=distribution.get)
            else:
                stats["most_common"] = None

        elif qtype == "multi_choice":
            distribution = {}
            total_selections = 0
            for a in answers:
                if isinstance(a, list):
                    total_selections += len(a)
                    for item in a:
                        if isinstance(item, str):
                            distribution[item] = distribution.get(item, 0) + 1
            stats["distribution"] = distribution
            if distribution:
                stats["most_common"] = max(distribution, key=distribution.get)
            else:
                stats["most_common"] = None
            stats["avg_selections"] = (
                round(total_selections / len(answers), 2) if answers else 0
            )

        elif qtype == "yes_no":
            yes_count = sum(1 for a in answers if a is True)
            no_count = sum(1 for a in answers if a is False)
            stats["yes_count"] = yes_count
            stats["no_count"] = no_count
            total_bool = yes_count + no_count
            stats["yes_percentage"] = (
                round(yes_count / total_bool * 100, 2) if total_bool else 0
            )

        analysis[qid] = stats

    return {
        "form_id": form.get("form_id", ""),
        "form_title": form.get("title", ""),
        "total_submissions": len(submissions),
        "analysis": analysis,
    }


@skill(
    name="feedback_summary",
    description="Generate a human-readable text summary from feedback analysis.",
    category="interaction",
    tags=["feedback", "summary", "report"],
    idempotent=True,
    display_name="Feedback Summary",
    icon="clipboard-list",
    risk_level=RiskLevel.SAFE,
    group="Feedback",
)
def feedback_summary(analysis: dict) -> dict:
    """Generate a human-readable text summary from feedback analysis.

    Args:
        analysis: The analysis dict (output of feedback_analyze).
    """
    form_title = analysis.get("form_title", "Untitled Form")
    total = analysis.get("total_submissions", 0)
    question_analysis = analysis.get("analysis", {})

    lines: List[str] = []
    lines.append(f"Feedback Summary: {form_title}")
    lines.append("=" * (len(lines[0])))
    lines.append(f"Total submissions: {total}")
    lines.append("")

    for qid, stats in question_analysis.items():
        qtext = stats.get("question_text", qid)
        qtype = stats.get("question_type", "unknown")
        count = stats.get("response_count", 0)

        lines.append(f"Q: {qtext}")
        lines.append(f"   Type: {qtype} | Responses: {count}")

        if qtype == "text":
            avg_len = stats.get("avg_length", 0)
            lines.append(f"   Average response length: {avg_len} characters")

        elif qtype in ("rating", "scale"):
            avg = stats.get("average", 0)
            mn = stats.get("min", 0)
            mx = stats.get("max", 0)
            lines.append(f"   Average: {avg} | Min: {mn} | Max: {mx}")
            dist = stats.get("distribution", {})
            if dist:
                dist_str = ", ".join(f"{k}: {v}" for k, v in sorted(dist.items()))
                lines.append(f"   Distribution: {dist_str}")

        elif qtype == "choice":
            most = stats.get("most_common")
            if most:
                lines.append(f"   Most common: {most}")
            dist = stats.get("distribution", {})
            if dist:
                dist_str = ", ".join(f"{k}: {v}" for k, v in sorted(dist.items()))
                lines.append(f"   Distribution: {dist_str}")

        elif qtype == "multi_choice":
            most = stats.get("most_common")
            avg_sel = stats.get("avg_selections", 0)
            if most:
                lines.append(f"   Most common: {most}")
            lines.append(f"   Average selections: {avg_sel}")
            dist = stats.get("distribution", {})
            if dist:
                dist_str = ", ".join(f"{k}: {v}" for k, v in sorted(dist.items()))
                lines.append(f"   Distribution: {dist_str}")

        elif qtype == "yes_no":
            yes_c = stats.get("yes_count", 0)
            no_c = stats.get("no_count", 0)
            yes_pct = stats.get("yes_percentage", 0)
            lines.append(f"   Yes: {yes_c} ({yes_pct}%) | No: {no_c}")

        lines.append("")

    summary_text = "\n".join(lines).rstrip()

    return {
        "summary": summary_text,
        "form_title": form_title,
        "total_submissions": total,
    }


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------


class FeedbackPlugin(TransformerPlugin):
    """Plugin providing feedback/questionnaire skills (no transformers)."""

    def __init__(self):
        super().__init__("feedback")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "feedback_create": feedback_create.__skill__,
            "feedback_validate": feedback_validate.__skill__,
            "feedback_submit": feedback_submit.__skill__,
            "feedback_analyze": feedback_analyze.__skill__,
            "feedback_summary": feedback_summary.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest
        return PluginManifest(
            name="feedback",
            display_name="Feedback",
            description="Create, validate, submit, and analyze feedback forms and questionnaires.",
            icon="clipboard-list",
            color="#8b5cf6",
            group="Interaction",
        )
