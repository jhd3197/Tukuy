"""Instruction contract system for Tukuy — LLM-powered tools with prompt templates.

An instruction is like a skill but instead of executing Python code, it renders
a prompt template and sends it to an LLM backend.  The decorated function (if
any) serves as a post-processor for the LLM response.

Usage::

    from tukuy import instruction

    @instruction(
        name="summarize",
        prompt="Summarize the following text: {text}",
        output_format="text",
    )
    def summarize(text: str):
        pass  # No post-processing

    @instruction(
        name="analyze_sentiment",
        prompt="Analyze the sentiment of: {text}",
        output_format="json",
    )
    def analyze_sentiment(result: dict) -> dict:
        result["processed"] = True
        return result
"""

import inspect
import json
import re
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
)

from .skill import (
    SkillDescriptor,
    SkillResult,
    _has_context_param,
    _infer_schemas,
    _resolve_schema,
)
from .types import TransformResult


# ---------------------------------------------------------------------------
# LLMBackend Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class LLMBackend(Protocol):
    """Protocol that LLM providers must implement.

    Consumers of Tukuy provide their own implementation of this protocol
    (e.g. wrapping OpenAI, Anthropic, or any other provider).  Tukuy
    itself remains provider-agnostic.
    """

    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_schema: Optional[dict] = None,
    ) -> dict:
        """Send a prompt to the LLM and return the response.

        Returns:
            A dict with the shape::

                {
                    "text": str,
                    "meta": {
                        "prompt_tokens": int,
                        "completion_tokens": int,
                        "cost": float,
                        "model": str,
                    }
                }
        """
        ...


# ---------------------------------------------------------------------------
# Prompt template helpers
# ---------------------------------------------------------------------------

_TEMPLATE_VAR_RE = re.compile(r"\{(\w+)\}")


def _extract_template_variables(template: str) -> List[str]:
    """Extract ``{variable}`` names from a prompt template string."""
    return list(dict.fromkeys(_TEMPLATE_VAR_RE.findall(template)))


# ---------------------------------------------------------------------------
# InstructionDescriptor
# ---------------------------------------------------------------------------

@dataclass
class InstructionDescriptor(SkillDescriptor):
    """Extends :class:`SkillDescriptor` with LLM-specific fields.

    Adds prompt template, output format, model hints, and few-shot
    examples on top of the standard skill identity / I/O / safety
    metadata.
    """

    # Prompt
    prompt: str = ""
    system_prompt: Optional[str] = None
    output_format: str = "text"  # "text", "json", "list", "markdown"

    # Model hints
    model_hint: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    # Few-shot
    few_shot_examples: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.requires_network = True
        self.is_async = True


# ---------------------------------------------------------------------------
# Instruction
# ---------------------------------------------------------------------------

@dataclass
class Instruction:
    """Binds an :class:`InstructionDescriptor` to an optional post-processor.

    Similar to :class:`~tukuy.skill.Skill` but execution goes through an
    LLM backend rather than calling Python code directly.  The optional
    ``fn`` is a post-processor applied to the parsed LLM response.
    """

    descriptor: InstructionDescriptor
    fn: Optional[Callable] = None

    # Cached on first call
    _ctx_param: Optional[str] = field(default=None, init=False, repr=False)
    _ctx_param_checked: bool = field(default=False, init=False, repr=False)

    @property
    def _context_param_name(self) -> Optional[str]:
        """Lazily resolve whether ``fn`` expects a SkillContext parameter."""
        if not self._ctx_param_checked:
            if self.fn is not None:
                self._ctx_param = _has_context_param(self.fn)
            self._ctx_param_checked = True
        return self._ctx_param

    def invoke(self, *args: Any, **kwargs: Any) -> SkillResult:
        """Sync invocation is not supported for instructions.

        Instructions always require an LLM call which is inherently async.
        Use :meth:`ainvoke` instead.
        """
        raise RuntimeError(
            "Instructions require async execution — use ainvoke() instead. "
            "In sync dispatch, use async_dispatch_openai or async_dispatch_anthropic."
        )

    async def ainvoke(self, *args: Any, **kwargs: Any) -> SkillResult:
        """Invoke the instruction asynchronously.

        1. Retrieves the LLM backend from context.
        2. Renders the prompt template with the provided arguments.
        3. Calls the LLM backend.
        4. Parses the response per ``output_format``.
        5. Optionally runs the post-processor function.
        6. Returns a :class:`SkillResult`.

        Pass ``context=<SkillContext>`` to provide the LLM backend and
        other configuration.
        """
        # Safety enforcement
        policy = kwargs.pop("policy", None)
        if policy is None:
            from .safety import get_policy
            policy = get_policy()
        if policy is not None:
            from .safety import SafetyError
            violations = policy.validate(self.descriptor)
            if violations:
                return SkillResult(
                    error=str(SafetyError(violations)),
                    success=False,
                    retryable=False,
                    metadata={"safety_violations": [str(v) for v in violations]},
                )

        # Extract context
        ctx = kwargs.pop("context", None)

        # Get LLM backend from context
        if ctx is None:
            return SkillResult(
                error="Instruction requires a SkillContext with 'llm_backend' in config. "
                      "Pass context=SkillContext(config={'llm_backend': <LLMBackend>}).",
                success=False,
            )

        llm_backend = ctx.config.get("llm_backend")
        if llm_backend is None:
            return SkillResult(
                error="No 'llm_backend' found in context.config. "
                      "Set context.config['llm_backend'] to an LLMBackend implementation.",
                success=False,
            )

        start = time.perf_counter()
        try:
            # Build template variables from kwargs
            template_vars = dict(kwargs)

            # Render prompt
            try:
                rendered_prompt = self.descriptor.prompt.format_map(template_vars)
            except KeyError as exc:
                return SkillResult(
                    error=f"Missing prompt variable: {exc}",
                    success=False,
                    duration_ms=(time.perf_counter() - start) * 1000,
                )

            # Prepend few-shot examples if present
            if self.descriptor.few_shot_examples:
                examples_text = ""
                for ex in self.descriptor.few_shot_examples:
                    examples_text += f"Input: {ex['input']}\nOutput: {ex['output']}\n\n"
                rendered_prompt = examples_text + rendered_prompt

            # Append output format instructions
            if self.descriptor.output_format == "json":
                rendered_prompt += "\nRespond with valid JSON only."
            elif self.descriptor.output_format == "list":
                rendered_prompt += "\nRespond with a bulleted list, one item per line starting with '- '."

            # Build LLM call kwargs
            llm_kwargs: Dict[str, Any] = {}
            if self.descriptor.system_prompt is not None:
                llm_kwargs["system"] = self.descriptor.system_prompt
            if self.descriptor.temperature is not None:
                llm_kwargs["temperature"] = self.descriptor.temperature
            if self.descriptor.max_tokens is not None:
                llm_kwargs["max_tokens"] = self.descriptor.max_tokens
            if self.descriptor.output_format == "json" and self.descriptor.output_schema:
                llm_kwargs["json_schema"] = self.descriptor.output_schema

            # Call LLM
            response = await llm_backend.complete(rendered_prompt, **llm_kwargs)
            response_text = response.get("text", "")
            meta = response.get("meta", {})

            # Parse response per output_format
            parsed = self._parse_response(response_text)
            if isinstance(parsed, SkillResult):
                # Parsing failed — return error result
                parsed.duration_ms = (time.perf_counter() - start) * 1000
                return parsed

            # Run post-processor if present
            if self.fn is not None:
                post_kwargs: Dict[str, Any] = {}
                # Inject context into post-processor if it accepts one
                if self._context_param_name is not None and ctx is not None:
                    post_kwargs[self._context_param_name] = ctx

                raw = self.fn(parsed, **post_kwargs)
                if inspect.isawaitable(raw):
                    raw = await raw
                if isinstance(raw, TransformResult):
                    result = SkillResult.from_transform_result(raw)
                    result.duration_ms = (time.perf_counter() - start) * 1000
                    result.metadata.update(meta)
                    return result
                parsed = raw

            elapsed_ms = (time.perf_counter() - start) * 1000
            return SkillResult(
                value=parsed,
                success=True,
                duration_ms=elapsed_ms,
                metadata=meta,
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return SkillResult(
                error=str(exc),
                success=False,
                duration_ms=elapsed_ms,
                retryable=False,
            )

    def _parse_response(self, text: str) -> Any:
        """Parse the LLM response according to ``output_format``.

        Returns the parsed value, or a ``SkillResult`` with an error
        if parsing fails.
        """
        fmt = self.descriptor.output_format

        if fmt == "text" or fmt == "markdown":
            return text

        if fmt == "json":
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError) as exc:
                return SkillResult(
                    error=f"Failed to parse LLM response as JSON: {exc}. Response: {text!r}",
                    success=False,
                )

        if fmt == "list":
            lines = text.strip().split("\n")
            items = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("- "):
                    stripped = stripped[2:]
                if stripped:
                    items.append(stripped)
            return items

        return text


# ---------------------------------------------------------------------------
# @instruction decorator
# ---------------------------------------------------------------------------


def _is_passthrough_body(fn: Callable) -> bool:
    """Return True if the function body is ``pass`` or ``...`` (Ellipsis).

    These indicate "no post-processing" — the LLM output is returned as-is.
    """
    try:
        source = inspect.getsource(fn)
        lines = source.strip().split("\n")
        # Find lines after the def/decorator that are the body
        body_lines = []
        in_body = False
        for line in lines:
            stripped = line.strip()
            if in_body:
                if stripped and not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    body_lines.append(stripped)
            elif stripped.startswith("def "):
                in_body = True
        if len(body_lines) == 1 and body_lines[0] in ("pass", "..."):
            return True
    except (OSError, TypeError):
        pass
    return False


def _build_input_schema_from_template(
    prompt: str,
    fn: Optional[Callable],
) -> Optional[Dict[str, Any]]:
    """Build an input_schema from prompt template variables.

    If the function has type-annotated parameters matching the template
    variables, those types are used.  Otherwise defaults to string.
    """
    variables = _extract_template_variables(prompt)
    if not variables:
        return None

    # Get type hints from function if available
    type_hints: Dict[str, Any] = {}
    if fn is not None:
        try:
            sig = inspect.signature(fn)
            for name, param in sig.parameters.items():
                if param.annotation is not inspect.Parameter.empty:
                    type_hints[name] = param.annotation
        except (ValueError, TypeError):
            pass

    from .skill import _annotation_to_json_schema

    properties: Dict[str, Any] = {}
    for var in variables:
        if var in type_hints:
            properties[var] = _annotation_to_json_schema(type_hints[var])
        else:
            properties[var] = {"type": "string"}

    return {
        "type": "object",
        "properties": properties,
        "required": variables,
    }


def instruction(
    fn=None,
    *,
    name=None,
    description=None,
    version="0.1.0",
    input_schema=None,
    output_schema=None,
    category="general",
    tags=None,
    examples=None,
    estimated_latency_ms=None,
    idempotent=False,
    side_effects=False,
    required_imports=None,
    requires_filesystem=False,
    # UI metadata
    display_name=None,
    icon=None,
    risk_level=None,
    group=None,
    hidden=False,
    deprecated=None,
    # Config
    config_params=None,
    # Instruction-specific
    prompt="",
    system_prompt=None,
    output_format="text",
    model_hint=None,
    temperature=None,
    max_tokens=None,
    few_shot_examples=None,
):
    """Decorator that turns a function into an LLM-powered instruction.

    Supports three calling conventions::

        @instruction
        def my_fn(text: str): ...

        @instruction()
        def my_fn(text: str): ...

        @instruction(name="custom", prompt="Summarize: {text}")
        def my_fn(text: str): ...

    The decorated function body is the **post-processor** — it receives
    the parsed LLM response and can transform it before returning.  If the
    body is ``pass`` or ``...``, no post-processing is applied.

    An ``Instruction`` instance is attached as ``fn.__instruction__`` and
    also as ``fn.__skill__`` so instructions are usable wherever skills are.
    """
    from .skill import RiskLevel as _RiskLevel

    def _attach(func):
        resolved_name = name if name is not None else func.__name__
        resolved_description = (
            description if description is not None else (func.__doc__ or "").strip()
        )

        # Determine if function is a passthrough (no post-processor)
        is_passthrough = _is_passthrough_body(func)
        post_processor = None if is_passthrough else func

        # Build input schema from prompt template variables
        resolved_input_schema = input_schema
        if resolved_input_schema is None:
            resolved_input_schema = _build_input_schema_from_template(prompt, func)

        resolved_risk_level = risk_level if risk_level is not None else _RiskLevel.AUTO

        descriptor = InstructionDescriptor(
            name=resolved_name,
            description=resolved_description,
            version=version,
            input_schema=resolved_input_schema,
            output_schema=_resolve_schema(output_schema),
            category=category,
            tags=tags if tags is not None else [],
            examples=examples if examples is not None else [],
            is_async=True,
            estimated_latency_ms=estimated_latency_ms,
            idempotent=idempotent,
            side_effects=side_effects,
            required_imports=required_imports if required_imports is not None else [],
            requires_network=True,
            requires_filesystem=requires_filesystem,
            # UI metadata
            display_name=display_name,
            icon=icon,
            risk_level=resolved_risk_level,
            group=group,
            hidden=hidden,
            deprecated=deprecated,
            # Config
            config_params=config_params if config_params is not None else [],
            # Instruction-specific
            prompt=prompt,
            system_prompt=system_prompt,
            output_format=output_format,
            model_hint=model_hint,
            temperature=temperature,
            max_tokens=max_tokens,
            few_shot_examples=few_shot_examples,
        )

        instr = Instruction(descriptor=descriptor, fn=post_processor)
        func.__instruction__ = instr
        func.__skill__ = instr  # Makes instructions usable wherever skills are
        return func

    if fn is not None:
        # Bare @instruction usage
        return _attach(fn)

    # @instruction() or @instruction(name=...) usage
    return _attach


__all__ = [
    "LLMBackend",
    "InstructionDescriptor",
    "Instruction",
    "instruction",
]
