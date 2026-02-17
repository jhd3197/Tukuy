"""Currency conversion plugin.

Provides async ``currency_convert``, ``currency_rates``, and
``currency_history`` skills using the Frankfurter API (free, no key).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.frankfurter.dev"


class FormatCurrencyTransformer(ChainableTransformer[dict, str]):
    """Format a currency amount dict into a human-readable string."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "amount" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        amount = value.get("amount", 0)
        currency = value.get("currency", "")
        return f"{amount:,.2f} {currency}".strip()


# ── Skills ─────────────────────────────────────────────────────────────────


@skill(
    name="currency_convert",
    display_name="Convert Currency",
    description="Convert an amount between currencies using the Frankfurter API (ECB rates, no key required).",
    category="currency",
    tags=["currency", "finance", "convert", "exchange"],
    icon="banknote",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="base_url",
            display_name="Base URL",
            description="Frankfurter API base URL (for self-hosted instances).",
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
async def currency_convert(
    amount: float,
    from_currency: str,
    to_currency: str,
    date: str = "latest",
) -> dict:
    """Convert *amount* from one currency to another."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    endpoint = f"{_BASE_URL}/{date}"
    params = {"amount": amount, "from": from_currency, "to": to_currency}

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        converted = data.get("rates", {}).get(to_currency)
        return {
            "amount": amount,
            "from": from_currency,
            "to": to_currency,
            "result": converted,
            "rate": round(converted / amount, 6) if converted and amount else None,
            "date": data.get("date"),
            "success": True,
        }


@skill(
    name="currency_rates",
    display_name="Exchange Rates",
    description="Get all exchange rates for a base currency (Frankfurter API, no key required).",
    category="currency",
    tags=["currency", "rates", "exchange"],
    icon="trending-up",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def currency_rates(base: str = "USD", date: str = "latest") -> dict:
    """Fetch exchange rates for a base currency."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    base = base.upper()
    endpoint = f"{_BASE_URL}/{date}"
    params = {"base": base}

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        return {
            "base": base,
            "date": data.get("date"),
            "rates": data.get("rates", {}),
            "count": len(data.get("rates", {})),
            "success": True,
        }


@skill(
    name="currency_history",
    display_name="Currency History",
    description="Get historical exchange rates between two dates (Frankfurter API, no key required).",
    category="currency",
    tags=["currency", "history", "exchange"],
    icon="calendar",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def currency_history(
    base: str,
    target: str,
    start_date: str,
    end_date: str,
) -> dict:
    """Fetch historical exchange rates for a currency pair over a date range."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    base = base.upper()
    target = target.upper()
    endpoint = f"{_BASE_URL}/{start_date}..{end_date}"
    params = {"base": base, "to": target}

    check_host(endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()
        rates = data.get("rates", {})
        return {
            "base": base,
            "target": target,
            "start_date": data.get("start_date", start_date),
            "end_date": data.get("end_date", end_date),
            "rates": rates,
            "data_points": len(rates),
            "success": True,
        }


class CurrencyPlugin(TransformerPlugin):
    """Plugin providing currency conversion skills and formatting transformer."""

    def __init__(self):
        super().__init__("currency")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_currency": lambda _: FormatCurrencyTransformer("format_currency"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "currency_convert": currency_convert.__skill__,
            "currency_rates": currency_rates.__skill__,
            "currency_history": currency_history.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="currency",
            display_name="Currency",
            description="Convert currencies, fetch exchange rates, and view rate history via Frankfurter API.",
            icon="banknote",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
