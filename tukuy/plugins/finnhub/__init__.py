"""Finnhub Finance plugin.

Provides async stock quotes, company profiles, market news, financial
metrics, and earnings calendar via the Finnhub API (free tier: 60 calls/min).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import datetime
import os
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://finnhub.io/api/v1"

_DISCLAIMER = "Market data from Finnhub. Not financial advice. Data may be delayed."


def _get_api_key() -> Optional[str]:
    return os.environ.get("FINNHUB_API_KEY")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_large_number(n: Optional[float]) -> str:
    """Format a large number with abbreviated suffixes.

    Examples:
        2_910_000_000_000 -> "$2.91T"
        28_400_000_000    -> "$28.40B"
        543_000_000       -> "$543.00M"
        12_300            -> "$12.30K"
        42                -> "$42"
    """
    if n is None:
        return "N/A"
    if not isinstance(n, (int, float)):
        return str(n)

    abs_n = abs(n)
    sign = "-" if n < 0 else ""

    if abs_n >= 1_000_000_000_000:
        return f"${sign}{abs_n / 1_000_000_000_000:.2f}T"
    if abs_n >= 1_000_000_000:
        return f"${sign}{abs_n / 1_000_000_000:.2f}B"
    if abs_n >= 1_000_000:
        return f"${sign}{abs_n / 1_000_000:.2f}M"
    if abs_n >= 1_000:
        return f"${sign}{abs_n / 1_000:.2f}K"
    return f"${sign}{abs_n}"


def _fmt_timestamp(ts: Optional[int]) -> str:
    """Convert a Unix timestamp to a human-readable datetime string."""
    if ts is None:
        return "N/A"
    if not isinstance(ts, (int, float)):
        return str(ts)
    try:
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (OSError, ValueError, OverflowError):
        return str(ts)


def _default_date_range() -> tuple:
    """Return (7_days_ago, today) as YYYY-MM-DD strings."""
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)
    return week_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def _missing_key_error() -> dict:
    """Return a standardized missing-API-key error response."""
    return {
        "error": "FINNHUB_API_KEY env var is required. Get a free key at https://finnhub.io",
        "success": False,
    }


# ---------------------------------------------------------------------------
# Transformers
# ---------------------------------------------------------------------------


class FormatStockQuoteTransformer(ChainableTransformer[dict, str]):
    """Format a stock quote dict into a human-readable string.

    Expects a dict with ``price`` (or ``c``) key.

    Example output: ``"AAPL $187.44 +1.20% | H: $189.10 L: $185.30"``
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and ("price" in value or "c" in value)

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        symbol = value.get("symbol", "???").upper()
        price = value.get("price", value.get("c"))
        change_pct = value.get("percent_change", value.get("dp"))
        high = value.get("high", value.get("h"))
        low = value.get("low", value.get("l"))

        parts = [symbol]
        if price is not None:
            parts.append(f"${price:,.2f}")
        else:
            parts.append("$N/A")

        if change_pct is not None:
            sign = "+" if change_pct >= 0 else ""
            parts.append(f"{sign}{change_pct:.2f}%")

        extras = []
        if high is not None:
            extras.append(f"H: ${high:,.2f}")
        if low is not None:
            extras.append(f"L: ${low:,.2f}")

        result = " ".join(parts)
        if extras:
            result += " | " + " ".join(extras)
        return result


class FormatLargeNumberTransformer(ChainableTransformer[float, str]):
    """Format a numeric value with dollar sign and abbreviation.

    Example: ``2910000000000`` -> ``"$2.91T"``
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, (int, float))

    def _transform(self, value: float, context: Optional[TransformContext] = None) -> str:
        return _fmt_large_number(value)


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@skill(
    name="stock_quote",
    display_name="Stock Quote",
    description="Get a real-time stock quote from Finnhub (requires FINNHUB_API_KEY).",
    category="finance",
    tags=["stock", "quote", "price", "market", "finance"],
    icon="trending-up",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Finnhub API key.",
            type="secret",
            default="",
            placeholder="your-finnhub-api-key",
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
async def stock_quote(
    symbol: str,
    timeout: int = 15,
) -> dict:
    """Fetch a real-time stock quote for the given symbol.

    Args:
        symbol: Stock ticker symbol (e.g. ``"AAPL"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    key = _get_api_key()
    if not key:
        return _missing_key_error()

    symbol = symbol.strip().upper()
    url = f"{_BASE_URL}/quote"
    params = {"symbol": symbol, "token": key}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Finnhub API returned status {resp.status_code}", "success": False}
        data = resp.json()

    # Finnhub returns all zeros when symbol is invalid
    if data.get("c") == 0 and data.get("h") == 0 and data.get("l") == 0:
        return {"error": f"No quote data found for symbol '{symbol}'.", "success": False}

    return {
        "symbol": symbol,
        "price": data.get("c"),
        "change": data.get("d"),
        "percent_change": data.get("dp"),
        "high": data.get("h"),
        "low": data.get("l"),
        "open": data.get("o"),
        "previous_close": data.get("pc"),
        "timestamp": data.get("t"),
        "timestamp_formatted": _fmt_timestamp(data.get("t")),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


@skill(
    name="stock_profile",
    display_name="Company Profile",
    description="Get company profile information from Finnhub (requires FINNHUB_API_KEY).",
    category="finance",
    tags=["stock", "company", "profile", "info", "finance"],
    icon="bar-chart-2",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Finnhub API key.",
            type="secret",
            default="",
            placeholder="your-finnhub-api-key",
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
async def stock_profile(
    symbol: str,
    timeout: int = 15,
) -> dict:
    """Fetch company profile for the given stock symbol.

    Args:
        symbol: Stock ticker symbol (e.g. ``"AAPL"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    key = _get_api_key()
    if not key:
        return _missing_key_error()

    symbol = symbol.strip().upper()
    url = f"{_BASE_URL}/stock/profile2"
    params = {"symbol": symbol, "token": key}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Finnhub API returned status {resp.status_code}", "success": False}
        data = resp.json()

    if not data or not data.get("name"):
        return {"error": f"No profile data found for symbol '{symbol}'.", "success": False}

    market_cap = data.get("marketCapitalization")
    # Finnhub returns market cap in millions, convert to actual value
    if market_cap is not None:
        market_cap = market_cap * 1_000_000

    return {
        "symbol": symbol,
        "name": data.get("name"),
        "ticker": data.get("ticker"),
        "exchange": data.get("exchange"),
        "industry": data.get("finnhubIndustry"),
        "market_cap": market_cap,
        "market_cap_formatted": _fmt_large_number(market_cap),
        "logo": data.get("logo"),
        "weburl": data.get("weburl"),
        "ipo_date": data.get("ipo"),
        "country": data.get("country"),
        "currency": data.get("currency"),
        "share_outstanding": data.get("shareOutstanding"),
        "phone": data.get("phone"),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


@skill(
    name="stock_news",
    display_name="Company News",
    description="Get recent company news from Finnhub (requires FINNHUB_API_KEY).",
    category="finance",
    tags=["stock", "news", "company", "headlines", "finance"],
    icon="bar-chart-2",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Finnhub API key.",
            type="secret",
            default="",
            placeholder="your-finnhub-api-key",
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
async def stock_news(
    symbol: str,
    from_date: str = "",
    to_date: str = "",
    timeout: int = 15,
) -> dict:
    """Fetch recent company news for the given stock symbol.

    Args:
        symbol: Stock ticker symbol (e.g. ``"AAPL"``).
        from_date: Start date in YYYY-MM-DD format (defaults to 7 days ago).
        to_date: End date in YYYY-MM-DD format (defaults to today).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    key = _get_api_key()
    if not key:
        return _missing_key_error()

    symbol = symbol.strip().upper()

    if not from_date or not to_date:
        default_from, default_to = _default_date_range()
        from_date = from_date or default_from
        to_date = to_date or default_to

    url = f"{_BASE_URL}/company-news"
    params = {
        "symbol": symbol,
        "from": from_date,
        "to": to_date,
        "token": key,
    }

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Finnhub API returned status {resp.status_code}", "success": False}
        data = resp.json()

    if not isinstance(data, list):
        return {"error": "Unexpected response format from Finnhub.", "success": False}

    articles: List[Dict[str, Any]] = []
    for item in data[:10]:
        articles.append({
            "headline": item.get("headline"),
            "source": item.get("source"),
            "url": item.get("url"),
            "summary": item.get("summary"),
            "datetime": item.get("datetime"),
            "datetime_formatted": _fmt_timestamp(item.get("datetime")),
            "image": item.get("image"),
        })

    return {
        "symbol": symbol,
        "from_date": from_date,
        "to_date": to_date,
        "articles": articles,
        "count": len(articles),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


@skill(
    name="stock_metrics",
    display_name="Financial Metrics",
    description="Get financial metrics and fundamentals from Finnhub (requires FINNHUB_API_KEY).",
    category="finance",
    tags=["stock", "metrics", "fundamentals", "pe", "eps", "finance"],
    icon="bar-chart-2",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Finnhub API key.",
            type="secret",
            default="",
            placeholder="your-finnhub-api-key",
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
async def stock_metrics(
    symbol: str,
    timeout: int = 15,
) -> dict:
    """Fetch financial metrics and fundamentals for the given stock symbol.

    Args:
        symbol: Stock ticker symbol (e.g. ``"AAPL"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    key = _get_api_key()
    if not key:
        return _missing_key_error()

    symbol = symbol.strip().upper()
    url = f"{_BASE_URL}/stock/metric"
    params = {"symbol": symbol, "metric": "all", "token": key}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Finnhub API returned status {resp.status_code}", "success": False}
        data = resp.json()

    metric = data.get("metric") or {}

    if not metric:
        return {"error": f"No metric data found for symbol '{symbol}'.", "success": False}

    market_cap = metric.get("marketCapitalization")
    if market_cap is not None:
        market_cap = market_cap * 1_000_000

    revenue = metric.get("revenuePerShareTTM")

    return {
        "symbol": symbol,
        "pe_ratio": metric.get("peBasicExclExtraTTM"),
        "eps": metric.get("epsBasicExclExtraItemsTTM"),
        "52_week_high": metric.get("52WeekHigh"),
        "52_week_low": metric.get("52WeekLow"),
        "beta": metric.get("beta"),
        "dividend_yield": metric.get("dividendYieldIndicatedAnnual"),
        "revenue_per_share": revenue,
        "profit_margin": metric.get("netProfitMarginTTM"),
        "market_cap": market_cap,
        "market_cap_formatted": _fmt_large_number(market_cap),
        "10_day_avg_volume": metric.get("10DayAverageTradingVolume"),
        "3_month_avg_volume": metric.get("3MonthAverageTradingVolume"),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


@skill(
    name="stock_search",
    display_name="Search Stocks",
    description="Search for stock symbols by name or ticker on Finnhub (requires FINNHUB_API_KEY).",
    category="finance",
    tags=["stock", "search", "symbol", "lookup", "finance"],
    icon="trending-up",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Finnhub API key.",
            type="secret",
            default="",
            placeholder="your-finnhub-api-key",
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
async def stock_search(
    query: str,
    timeout: int = 15,
) -> dict:
    """Search for stock symbols matching a query string.

    Args:
        query: Search term (company name or ticker, e.g. ``"apple"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    key = _get_api_key()
    if not key:
        return _missing_key_error()

    query = query.strip()
    if not query:
        return {"error": "Query must not be empty.", "success": False}

    url = f"{_BASE_URL}/search"
    params = {"q": query, "token": key}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Finnhub API returned status {resp.status_code}", "success": False}
        data = resp.json()

    raw_results = data.get("result") or []
    results: List[Dict[str, Any]] = []

    for item in raw_results[:10]:
        results.append({
            "description": item.get("description"),
            "display_symbol": item.get("displaySymbol"),
            "symbol": item.get("symbol"),
            "type": item.get("type"),
        })

    return {
        "query": query,
        "results": results,
        "count": len(results),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


@skill(
    name="earnings_calendar",
    display_name="Earnings Calendar",
    description="Get upcoming and recent earnings dates from Finnhub (requires FINNHUB_API_KEY).",
    category="finance",
    tags=["stock", "earnings", "calendar", "eps", "revenue", "finance"],
    icon="bar-chart-2",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="api_key",
            display_name="API Key",
            description="Finnhub API key.",
            type="secret",
            default="",
            placeholder="your-finnhub-api-key",
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
async def earnings_calendar(
    from_date: str,
    to_date: str,
    timeout: int = 15,
) -> dict:
    """Fetch upcoming and recent earnings for a date range.

    Args:
        from_date: Start date in YYYY-MM-DD format.
        to_date: End date in YYYY-MM-DD format.
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    key = _get_api_key()
    if not key:
        return _missing_key_error()

    url = f"{_BASE_URL}/calendar/earnings"
    params = {"from": from_date, "to": to_date, "token": key}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Finnhub API returned status {resp.status_code}", "success": False}
        data = resp.json()

    raw_earnings = data.get("earningsCalendar") or []
    earnings: List[Dict[str, Any]] = []

    for item in raw_earnings:
        eps_actual = item.get("epsActual")
        eps_estimate = item.get("epsEstimate")
        revenue_actual = item.get("revenueActual")
        revenue_estimate = item.get("revenueEstimate")

        earnings.append({
            "symbol": item.get("symbol"),
            "date": item.get("date"),
            "eps_actual": eps_actual,
            "eps_estimate": eps_estimate,
            "eps_surprise": round(eps_actual - eps_estimate, 4) if eps_actual is not None and eps_estimate is not None else None,
            "revenue_actual": revenue_actual,
            "revenue_actual_formatted": _fmt_large_number(revenue_actual),
            "revenue_estimate": revenue_estimate,
            "revenue_estimate_formatted": _fmt_large_number(revenue_estimate),
            "hour": item.get("hour"),
            "quarter": item.get("quarter"),
            "year": item.get("year"),
        })

    return {
        "from_date": from_date,
        "to_date": to_date,
        "earnings": earnings,
        "count": len(earnings),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------


class FinnhubPlugin(TransformerPlugin):
    """Plugin providing Finnhub stock market data skills and formatters."""

    def __init__(self):
        super().__init__("finnhub")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_stock_quote": lambda _: FormatStockQuoteTransformer("format_stock_quote"),
            "format_large_number": lambda _: FormatLargeNumberTransformer("format_large_number"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "stock_quote": stock_quote.__skill__,
            "stock_profile": stock_profile.__skill__,
            "stock_news": stock_news.__skill__,
            "stock_metrics": stock_metrics.__skill__,
            "stock_search": stock_search.__skill__,
            "earnings_calendar": earnings_calendar.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="finnhub",
            display_name="Finnhub Finance",
            description="Stock quotes, company profiles, news, metrics, and earnings via Finnhub API.",
            icon="trending-up",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
