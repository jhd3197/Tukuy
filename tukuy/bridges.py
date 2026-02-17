"""Agent bridge — converts Tukuy skills to OpenAI and Anthropic tool formats."""

import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Union

from .context import SkillContext
from .instruction import Instruction
from .skill import Skill, SkillDescriptor, SkillResult


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_first_param_name(fn: Callable) -> str:
    """Return the first real parameter name of *fn*, skipping ``self``/``cls``.

    Falls back to ``"input"`` when no suitable parameter exists.
    """
    sig = inspect.signature(fn)
    for name in sig.parameters:
        if name in ("self", "cls"):
            continue
        return name
    return "input"


def _normalize(skill_or_fn: Any) -> Union[Skill, Instruction]:
    """Accept a ``Skill``, ``Instruction``, or a decorated function and
    return the underlying ``Skill`` or ``Instruction``.

    Checks for ``__instruction__`` first so that instruction-decorated
    functions are recognised even though they also carry ``__skill__``.
    Raises ``TypeError`` otherwise.
    """
    if isinstance(skill_or_fn, Instruction):
        return skill_or_fn
    if isinstance(skill_or_fn, Skill):
        return skill_or_fn
    if callable(skill_or_fn):
        if hasattr(skill_or_fn, "__instruction__"):
            return skill_or_fn.__instruction__
        if hasattr(skill_or_fn, "__skill__"):
            return skill_or_fn.__skill__
    raise TypeError(
        f"Expected a Skill/Instruction instance or decorated function, got {type(skill_or_fn).__name__}"
    )


def _wrap_as_parameters(skill_obj: Union[Skill, Instruction]) -> dict:
    """Ensure the skill's ``input_schema`` is a JSON Schema *object* suitable
    for the ``parameters`` / ``input_schema`` field of a tool definition.

    Three cases:
    * ``None``            → ``{"type": "object", "properties": {}}``
    * Already an object with ``"properties"`` → passthrough
    * Simple type schema  → wrapped with the function's actual param name
    """
    schema = skill_obj.descriptor.input_schema

    if schema is None:
        return {"type": "object", "properties": {}}

    if isinstance(schema, dict) and "properties" in schema:
        return schema

    # Simple type (e.g. {"type": "string"}) — wrap with param name.
    # Instructions may have fn=None so fall back to "input".
    if skill_obj.fn is not None:
        param_name = _get_first_param_name(skill_obj.fn)
    else:
        param_name = "input"
    return {
        "type": "object",
        "properties": {param_name: schema},
        "required": [param_name],
    }


def _serialize_result_value(result: SkillResult) -> str:
    """Convert a ``SkillResult`` to a string for an API ``content`` field."""
    if not result.success:
        return result.error or "Unknown error"
    if result.value is None:
        return ""
    try:
        return json.dumps(result.value)
    except (TypeError, ValueError):
        return str(result.value)


def _unwrap_single_param(skill_obj: Union[Skill, Instruction], args: dict) -> Union[dict, Any]:
    """Handle parameter-name mismatch between a wrapped schema and the actual
    function signature.

    If *args* has exactly one key and the function has exactly one non-self/cls
    parameter whose name differs from that key, remap to the correct name.
    Otherwise return *args* unchanged.

    For Instructions with ``fn=None``, returns *args* unchanged since there
    is no function signature to compare against.
    """
    if not isinstance(args, dict) or len(args) != 1:
        return args

    if skill_obj.fn is None:
        return args

    sig = inspect.signature(skill_obj.fn)
    real_params = [n for n in sig.parameters if n not in ("self", "cls")]

    if len(real_params) != 1:
        return args

    arg_key = next(iter(args))
    real_name = real_params[0]

    if arg_key != real_name:
        return {real_name: args[arg_key]}
    return args


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


def to_openai_tool(skill_or_fn: Any) -> dict:
    """Convert a skill to an OpenAI function-calling tool definition."""
    skill_obj = _normalize(skill_or_fn)
    desc = skill_obj.descriptor
    return {
        "type": "function",
        "function": {
            "name": desc.name,
            "description": desc.description,
            "parameters": _wrap_as_parameters(skill_obj),
        },
    }


def to_anthropic_tool(skill_or_fn: Any) -> dict:
    """Convert a skill to an Anthropic tool definition."""
    skill_obj = _normalize(skill_or_fn)
    desc = skill_obj.descriptor
    return {
        "name": desc.name,
        "description": desc.description,
        "input_schema": _wrap_as_parameters(skill_obj),
    }


def to_openai_tools(skills: List[Any]) -> List[dict]:
    """Batch-convert skills to OpenAI tool definitions."""
    return [to_openai_tool(s) for s in skills]


def to_anthropic_tools(skills: List[Any]) -> List[dict]:
    """Batch-convert skills to Anthropic tool definitions."""
    return [to_anthropic_tool(s) for s in skills]


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------


def format_result_openai(tool_call_id: str, result: SkillResult) -> dict:
    """Format a ``SkillResult`` as an OpenAI tool-result message."""
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": _serialize_result_value(result),
    }


def format_result_anthropic(tool_use_id: str, result: SkillResult) -> dict:
    """Format a ``SkillResult`` as an Anthropic tool-result content block."""
    msg: Dict[str, Any] = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": _serialize_result_value(result),
    }
    if not result.success:
        msg["is_error"] = True
    return msg


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def dispatch_openai(
    tool_call: dict,
    skills: Dict[str, Any],
    *,
    context: Optional[SkillContext] = None,
) -> dict:
    """Look up a skill by name, invoke it, and return a formatted OpenAI
    tool-result message.

    *skills* maps tool names to ``Skill`` instances or ``@skill``-decorated
    functions.

    *context*, if provided, is forwarded to :meth:`Skill.invoke` so that
    skills can read per-bot configuration via ``ctx.config``.
    """
    call_id = tool_call.get("id", "")
    func = tool_call.get("function", {})
    name = func.get("name", "")
    raw_args = func.get("arguments", "{}")

    # Unknown tool
    if name not in skills:
        error_result = SkillResult(error=f"Unknown tool: {name}", success=False)
        return format_result_openai(call_id, error_result)

    # Parse JSON arguments
    try:
        args = json.loads(raw_args)
    except (json.JSONDecodeError, TypeError):
        error_result = SkillResult(error=f"Invalid JSON arguments: {raw_args}", success=False)
        return format_result_openai(call_id, error_result)

    skill_obj = _normalize(skills[name])

    # Instructions are async-only
    if isinstance(skill_obj, Instruction):
        error_result = SkillResult(
            error=f"Instruction '{name}' requires async dispatch — "
                  "use async_dispatch_openai or async_dispatch_anthropic.",
            success=False,
        )
        return format_result_openai(call_id, error_result)

    args = _unwrap_single_param(skill_obj, args)

    ctx_kwargs: Dict[str, Any] = {}
    if context is not None:
        ctx_kwargs["context"] = context

    if isinstance(args, dict):
        result = skill_obj.invoke(**args, **ctx_kwargs)
    else:
        result = skill_obj.invoke(args, **ctx_kwargs)

    return format_result_openai(call_id, result)


def dispatch_anthropic(
    tool_use: dict,
    skills: Dict[str, Any],
    *,
    context: Optional[SkillContext] = None,
) -> dict:
    """Look up a skill by name, invoke it, and return a formatted Anthropic
    tool-result content block.

    *skills* maps tool names to ``Skill`` instances or ``@skill``-decorated
    functions.

    *context*, if provided, is forwarded to :meth:`Skill.invoke` so that
    skills can read per-bot configuration via ``ctx.config``.
    """
    use_id = tool_use.get("id", "")
    name = tool_use.get("name", "")
    args = tool_use.get("input", {})

    # Unknown tool
    if name not in skills:
        error_result = SkillResult(error=f"Unknown tool: {name}", success=False)
        return format_result_anthropic(use_id, error_result)

    skill_obj = _normalize(skills[name])

    # Instructions are async-only
    if isinstance(skill_obj, Instruction):
        error_result = SkillResult(
            error=f"Instruction '{name}' requires async dispatch — "
                  "use async_dispatch_openai or async_dispatch_anthropic.",
            success=False,
        )
        return format_result_anthropic(use_id, error_result)

    args = _unwrap_single_param(skill_obj, args)

    ctx_kwargs: Dict[str, Any] = {}
    if context is not None:
        ctx_kwargs["context"] = context

    if isinstance(args, dict):
        result = skill_obj.invoke(**args, **ctx_kwargs)
    else:
        result = skill_obj.invoke(args, **ctx_kwargs)

    return format_result_anthropic(use_id, result)


async def async_dispatch_openai(
    tool_call: dict,
    skills: Dict[str, Any],
    *,
    context: Optional[SkillContext] = None,
) -> dict:
    """Async variant of :func:`dispatch_openai`.

    Uses :meth:`Skill.ainvoke` so async skills are properly awaited while
    sync skills still work transparently.

    *context*, if provided, is forwarded to :meth:`Skill.ainvoke` so that
    skills can read per-bot configuration via ``ctx.config``.
    """
    call_id = tool_call.get("id", "")
    func = tool_call.get("function", {})
    name = func.get("name", "")
    raw_args = func.get("arguments", "{}")

    if name not in skills:
        error_result = SkillResult(error=f"Unknown tool: {name}", success=False)
        return format_result_openai(call_id, error_result)

    try:
        args = json.loads(raw_args)
    except (json.JSONDecodeError, TypeError):
        error_result = SkillResult(error=f"Invalid JSON arguments: {raw_args}", success=False)
        return format_result_openai(call_id, error_result)

    skill_obj = _normalize(skills[name])
    args = _unwrap_single_param(skill_obj, args)

    ctx_kwargs: Dict[str, Any] = {}
    if context is not None:
        ctx_kwargs["context"] = context

    if isinstance(args, dict):
        result = await skill_obj.ainvoke(**args, **ctx_kwargs)
    else:
        result = await skill_obj.ainvoke(args, **ctx_kwargs)

    return format_result_openai(call_id, result)


async def async_dispatch_anthropic(
    tool_use: dict,
    skills: Dict[str, Any],
    *,
    context: Optional[SkillContext] = None,
) -> dict:
    """Async variant of :func:`dispatch_anthropic`.

    Uses :meth:`Skill.ainvoke` so async skills are properly awaited while
    sync skills still work transparently.

    *context*, if provided, is forwarded to :meth:`Skill.ainvoke` so that
    skills can read per-bot configuration via ``ctx.config``.
    """
    use_id = tool_use.get("id", "")
    name = tool_use.get("name", "")
    args = tool_use.get("input", {})

    if name not in skills:
        error_result = SkillResult(error=f"Unknown tool: {name}", success=False)
        return format_result_anthropic(use_id, error_result)

    skill_obj = _normalize(skills[name])
    args = _unwrap_single_param(skill_obj, args)

    ctx_kwargs: Dict[str, Any] = {}
    if context is not None:
        ctx_kwargs["context"] = context

    if isinstance(args, dict):
        result = await skill_obj.ainvoke(**args, **ctx_kwargs)
    else:
        result = await skill_obj.ainvoke(args, **ctx_kwargs)

    return format_result_anthropic(use_id, result)


__all__ = [
    "to_openai_tool",
    "to_anthropic_tool",
    "to_openai_tools",
    "to_anthropic_tools",
    "format_result_openai",
    "format_result_anthropic",
    "dispatch_openai",
    "dispatch_anthropic",
    "async_dispatch_openai",
    "async_dispatch_anthropic",
]
