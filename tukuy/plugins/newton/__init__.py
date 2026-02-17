"""Newton math API plugin.

Provides async skills for symbolic math operations: simplify, factor,
derive, integrate, find zeroes, and more using the Newton API (free, no key).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://newton.now.sh/api/v2"

_OPERATIONS = [
    "simplify", "factor", "derive", "integrate", "zeroes",
    "tangent", "area", "cos", "sin", "tan", "arccos",
    "arcsin", "arctan", "abs", "log",
]


class FormatMathResultTransformer(ChainableTransformer[dict, str]):
    """Format a math result dict into a human-readable string."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "result" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        op = value.get("operation", "")
        expr = value.get("expression", "")
        result = value.get("result", "")
        return f"{op}({expr}) = {result}"


# -- Skills ------------------------------------------------------------------


@skill(
    name="math_compute",
    display_name="Math Compute",
    description="Perform a symbolic math operation (simplify, factor, derive, integrate, zeroes, etc.) using the Newton API (free, no key).",
    category="math",
    tags=["math", "calculus", "algebra", "symbolic"],
    icon="calculator",
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
async def math_compute(
    operation: str,
    expression: str,
    timeout: int = 15,
) -> dict:
    """Run a symbolic math operation on an expression.

    Args:
        operation: One of simplify, factor, derive, integrate, zeroes,
                   tangent, area, cos, sin, tan, arccos, arcsin, arctan,
                   abs, log.
        expression: The math expression (e.g. ``"x^2+2x"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    operation = operation.strip().lower()
    if operation not in _OPERATIONS:
        return {"error": f"Unknown operation '{operation}'. Must be one of: {', '.join(_OPERATIONS)}", "success": False}

    expression = expression.strip()
    if not expression:
        return {"error": "Expression must not be empty.", "success": False}

    url = f"{_BASE_URL}/{operation}/{expression}"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Newton API returned status {resp.status_code}", "success": False}
        data = resp.json()

    return {
        "operation": data.get("operation", operation),
        "expression": data.get("expression", expression),
        "result": data.get("result", ""),
        "success": True,
    }


@skill(
    name="math_simplify",
    display_name="Simplify Expression",
    description="Simplify a math expression (Newton API, free, no key).",
    category="math",
    tags=["math", "simplify", "algebra"],
    icon="calculator",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def math_simplify(expression: str) -> dict:
    """Simplify a mathematical expression."""
    return await math_compute(operation="simplify", expression=expression)


@skill(
    name="math_derive",
    display_name="Derive Expression",
    description="Compute the derivative of a math expression (Newton API, free, no key).",
    category="math",
    tags=["math", "derivative", "calculus"],
    icon="calculator",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def math_derive(expression: str) -> dict:
    """Compute the derivative of an expression."""
    return await math_compute(operation="derive", expression=expression)


@skill(
    name="math_integrate",
    display_name="Integrate Expression",
    description="Compute the integral of a math expression (Newton API, free, no key).",
    category="math",
    tags=["math", "integral", "calculus"],
    icon="calculator",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def math_integrate(expression: str) -> dict:
    """Compute the integral of an expression."""
    return await math_compute(operation="integrate", expression=expression)


@skill(
    name="math_factor",
    display_name="Factor Expression",
    description="Factor a math expression (Newton API, free, no key).",
    category="math",
    tags=["math", "factor", "algebra"],
    icon="calculator",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def math_factor(expression: str) -> dict:
    """Factor an expression."""
    return await math_compute(operation="factor", expression=expression)


@skill(
    name="math_zeroes",
    display_name="Find Zeroes",
    description="Find the zeroes (roots) of a math expression (Newton API, free, no key).",
    category="math",
    tags=["math", "zeroes", "roots", "algebra"],
    icon="calculator",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def math_zeroes(expression: str) -> dict:
    """Find the zeroes of an expression."""
    return await math_compute(operation="zeroes", expression=expression)


class NewtonPlugin(TransformerPlugin):
    """Plugin providing symbolic math skills via the Newton API."""

    def __init__(self):
        super().__init__("newton")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_math_result": lambda _: FormatMathResultTransformer("format_math_result"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "math_compute": math_compute.__skill__,
            "math_simplify": math_simplify.__skill__,
            "math_derive": math_derive.__skill__,
            "math_integrate": math_integrate.__skill__,
            "math_factor": math_factor.__skill__,
            "math_zeroes": math_zeroes.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="newton",
            display_name="Newton Math",
            description="Symbolic math: simplify, factor, derive, integrate, find zeroes via Newton API.",
            icon="calculator",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
