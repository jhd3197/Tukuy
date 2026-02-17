"""CoinGecko crypto market data plugin.

Provides async skills for querying cryptocurrency prices, market data,
trending coins, and price history using the CoinGecko free API (no key required).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.coingecko.com/api/v3"

_DISCLAIMER = "Data from CoinGecko. Not financial advice."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_large_number(n: Optional[float]) -> str:
    """Format a large number with abbreviated suffixes.

    Examples:
        1_320_000_000_000 -> "1.32T"
        28_400_000_000    -> "28.4B"
        543_000_000       -> "543M"
        12_300            -> "12.3K"
        42                -> "42"
    """
    if n is None:
        return "N/A"
    if not isinstance(n, (int, float)):
        return str(n)

    abs_n = abs(n)
    sign = "-" if n < 0 else ""

    if abs_n >= 1_000_000_000_000:
        return f"{sign}{abs_n / 1_000_000_000_000:.2f}T"
    if abs_n >= 1_000_000_000:
        return f"{sign}{abs_n / 1_000_000_000:.2f}B"
    if abs_n >= 1_000_000:
        return f"{sign}{abs_n / 1_000_000:.2f}M"
    if abs_n >= 1_000:
        return f"{sign}{abs_n / 1_000:.2f}K"
    return f"{sign}{abs_n}"


def _fmt_price(price: Optional[float]) -> str:
    """Format a price value, preserving precision for very small values (e.g. SHIB)."""
    if price is None:
        return "N/A"
    if not isinstance(price, (int, float)):
        return str(price)

    abs_price = abs(price)
    if abs_price == 0:
        return "0"
    if abs_price >= 1:
        return f"{price:,.2f}"
    # For sub-dollar prices, keep enough decimals to show significant digits
    if abs_price >= 0.01:
        return f"{price:.4f}"
    if abs_price >= 0.0001:
        return f"{price:.6f}"
    return f"{price:.10f}"


def _rate_limit_error() -> dict:
    """Return a standardized rate-limit error response."""
    return {
        "error": "Rate limited by CoinGecko. Please try again in a moment.",
        "success": False,
    }


# ---------------------------------------------------------------------------
# Transformers
# ---------------------------------------------------------------------------


class FormatCryptoPriceTransformer(ChainableTransformer[dict, str]):
    """Format a crypto price dict into a human-readable string.

    Expects a dict with at least ``symbol`` (or ``name``) and ``price`` keys.
    Optionally includes ``change_24h`` for the 24-hour percentage change.

    Example output: ``"BTC $67,432.18 +2.30%"``
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and ("price" in value or "current_price" in value)

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        symbol = value.get("symbol", value.get("name", "???")).upper()
        price = value.get("price", value.get("current_price"))
        change = value.get("change_24h", value.get("price_change_percentage_24h"))

        parts = [symbol, f"${_fmt_price(price)}"]
        if change is not None:
            sign = "+" if change >= 0 else ""
            parts.append(f"{sign}{change:.2f}%")
        return " ".join(parts)


class FormatMarketCapTransformer(ChainableTransformer[float, str]):
    """Format a numeric market-cap value with dollar sign and abbreviation.

    Example: ``1234567890`` -> ``"$1.23B"``
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, (int, float))

    def _transform(self, value: float, context: Optional[TransformContext] = None) -> str:
        return f"${_fmt_large_number(value)}"


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@skill(
    name="crypto_price",
    display_name="Crypto Price",
    description="Get current prices for one or more cryptocurrencies (CoinGecko, no key required).",
    category="crypto",
    tags=["crypto", "price", "bitcoin", "ethereum", "market"],
    icon="bitcoin",
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
async def crypto_price(
    coins: str,
    vs_currencies: str = "usd",
    timeout: int = 15,
) -> dict:
    """Fetch current prices, 24h change, market cap, and volume for the given coins.

    Args:
        coins: Comma-separated CoinGecko coin IDs (e.g. ``"bitcoin,ethereum"``).
        vs_currencies: Comma-separated fiat/crypto currencies (e.g. ``"usd,eur"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    coins = coins.strip().lower()
    vs_currencies = vs_currencies.strip().lower()

    url = f"{_BASE_URL}/simple/price"
    params = {
        "ids": coins,
        "vs_currencies": vs_currencies,
        "include_24hr_change": "true",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
    }

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if resp.status_code == 429:
            return _rate_limit_error()
        if not resp.is_success:
            return {"error": f"CoinGecko API returned status {resp.status_code}", "success": False}
        data = resp.json()

    currencies = [c.strip() for c in vs_currencies.split(",")]
    result: Dict[str, Any] = {}

    for coin_id, coin_data in data.items():
        coin_result: Dict[str, Any] = {}
        for curr in currencies:
            price = coin_data.get(curr)
            change_key = f"{curr}_24h_change"
            mcap_key = f"{curr}_market_cap"
            vol_key = f"{curr}_24h_vol"

            coin_result[curr] = {
                "price": price,
                "price_formatted": _fmt_price(price),
                "change_24h": coin_data.get(change_key),
                "market_cap": coin_data.get(mcap_key),
                "market_cap_formatted": _fmt_large_number(coin_data.get(mcap_key)),
                "volume_24h": coin_data.get(vol_key),
                "volume_24h_formatted": _fmt_large_number(coin_data.get(vol_key)),
            }
        result[coin_id] = coin_result

    return {
        "prices": result,
        "coins_queried": coins,
        "vs_currencies": vs_currencies,
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


@skill(
    name="crypto_details",
    display_name="Crypto Details",
    description="Get detailed information for a specific cryptocurrency (CoinGecko, no key required).",
    category="crypto",
    tags=["crypto", "details", "info", "coin", "market"],
    icon="bitcoin",
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
async def crypto_details(
    coin_id: str,
    timeout: int = 15,
) -> dict:
    """Fetch detailed info for a single coin: description, market data, links.

    Args:
        coin_id: CoinGecko coin ID (e.g. ``"bitcoin"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    coin_id = coin_id.strip().lower()
    url = f"{_BASE_URL}/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
    }

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if resp.status_code == 429:
            return _rate_limit_error()
        if not resp.is_success:
            return {"error": f"CoinGecko API returned status {resp.status_code}", "success": False}
        data = resp.json()

    # Extract nested market data safely
    market = data.get("market_data") or {}
    description_full = (data.get("description") or {}).get("en", "")
    description = (description_full[:500] + "...") if len(description_full) > 500 else description_full

    # Extract links
    links_data = data.get("links") or {}
    homepage_list = links_data.get("homepage") or []
    homepage = [u for u in homepage_list if u] or []
    twitter = links_data.get("twitter_screen_name") or ""
    repos = links_data.get("repos_url") or {}
    github = [u for u in (repos.get("github") or []) if u] or []

    current_price = (market.get("current_price") or {}).get("usd")
    market_cap = (market.get("market_cap") or {}).get("usd")
    total_volume = (market.get("total_volume") or {}).get("usd")
    ath = (market.get("ath") or {}).get("usd")
    atl = (market.get("atl") or {}).get("usd")

    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "symbol": (data.get("symbol") or "").upper(),
        "description": description,
        "market_cap_rank": data.get("market_cap_rank"),
        "current_price": current_price,
        "current_price_formatted": _fmt_price(current_price),
        "market_cap": market_cap,
        "market_cap_formatted": _fmt_large_number(market_cap),
        "total_volume": total_volume,
        "total_volume_formatted": _fmt_large_number(total_volume),
        "ath": ath,
        "ath_formatted": _fmt_price(ath),
        "atl": atl,
        "atl_formatted": _fmt_price(atl),
        "price_change_24h": market.get("price_change_24h"),
        "price_change_percentage_24h": market.get("price_change_percentage_24h"),
        "circulating_supply": market.get("circulating_supply"),
        "circulating_supply_formatted": _fmt_large_number(market.get("circulating_supply")),
        "total_supply": market.get("total_supply"),
        "max_supply": market.get("max_supply"),
        "links": {
            "homepage": homepage,
            "twitter": f"https://twitter.com/{twitter}" if twitter else None,
            "github": github,
        },
        "image": (data.get("image") or {}).get("large"),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


@skill(
    name="crypto_chart",
    display_name="Crypto Price History",
    description="Get price history and summary statistics for a cryptocurrency (CoinGecko, no key required).",
    category="crypto",
    tags=["crypto", "chart", "history", "price", "trend"],
    icon="trending-up",
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
async def crypto_chart(
    coin_id: str,
    days: int = 7,
    vs_currency: str = "usd",
    timeout: int = 15,
) -> dict:
    """Fetch price history and compute summary stats (high, low, trend, etc.).

    CoinGecko returns ``[timestamp_ms, price]`` pairs.  Since we cannot
    render charts in text, this skill computes derived statistics instead.

    Args:
        coin_id: CoinGecko coin ID (e.g. ``"bitcoin"``).
        days: Number of days of history (1, 7, 14, 30, 90, 180, 365, max).
        vs_currency: Target currency (e.g. ``"usd"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    coin_id = coin_id.strip().lower()
    vs_currency = vs_currency.strip().lower()

    url = f"{_BASE_URL}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days,
    }

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if resp.status_code == 429:
            return _rate_limit_error()
        if not resp.is_success:
            return {"error": f"CoinGecko API returned status {resp.status_code}", "success": False}
        data = resp.json()

    prices: List[List[float]] = data.get("prices") or []
    if not prices:
        return {
            "coin_id": coin_id,
            "days": days,
            "vs_currency": vs_currency,
            "error": "No price data returned for this coin/period.",
            "success": False,
        }

    price_values = [p[1] for p in prices]
    start_price = price_values[0]
    end_price = price_values[-1]
    high = max(price_values)
    low = min(price_values)
    avg = sum(price_values) / len(price_values)

    if start_price != 0:
        change_percent = ((end_price - start_price) / start_price) * 100
    else:
        change_percent = 0.0

    # Determine trend
    threshold = 1.0  # 1% threshold for sideways
    if change_percent > threshold:
        trend = "up"
    elif change_percent < -threshold:
        trend = "down"
    else:
        trend = "sideways"

    return {
        "coin_id": coin_id,
        "days": days,
        "vs_currency": vs_currency,
        "high": high,
        "high_formatted": _fmt_price(high),
        "low": low,
        "low_formatted": _fmt_price(low),
        "average": round(avg, 8),
        "average_formatted": _fmt_price(avg),
        "start_price": start_price,
        "start_price_formatted": _fmt_price(start_price),
        "end_price": end_price,
        "end_price_formatted": _fmt_price(end_price),
        "change_percent": round(change_percent, 2),
        "trend": trend,
        "data_points": len(prices),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


@skill(
    name="crypto_trending",
    display_name="Trending Crypto",
    description="Get currently trending cryptocurrencies on CoinGecko (no key required).",
    category="crypto",
    tags=["crypto", "trending", "popular", "hot"],
    icon="trending-up",
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
async def crypto_trending(
    timeout: int = 15,
) -> dict:
    """Fetch the top trending coins on CoinGecko.

    Args:
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"{_BASE_URL}/search/trending"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=timeout)
        if resp.status_code == 429:
            return _rate_limit_error()
        if not resp.is_success:
            return {"error": f"CoinGecko API returned status {resp.status_code}", "success": False}
        data = resp.json()

    coins_raw = data.get("coins") or []
    trending: List[Dict[str, Any]] = []

    for entry in coins_raw:
        item = entry.get("item") or {}
        trending.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "symbol": (item.get("symbol") or "").upper(),
            "market_cap_rank": item.get("market_cap_rank"),
            "price_btc": item.get("price_btc"),
            "price_btc_formatted": _fmt_price(item.get("price_btc")),
            "score": item.get("score"),
            "thumb": item.get("thumb"),
        })

    return {
        "trending": trending,
        "count": len(trending),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


@skill(
    name="crypto_search",
    display_name="Search Crypto",
    description="Search for cryptocurrencies by name or symbol (CoinGecko, no key required).",
    category="crypto",
    tags=["crypto", "search", "find", "lookup"],
    icon="bitcoin",
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
async def crypto_search(
    query: str,
    timeout: int = 15,
) -> dict:
    """Search CoinGecko for coins matching a query string.

    Args:
        query: Search term (coin name or symbol, e.g. ``"sol"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    query = query.strip()
    if not query:
        return {"error": "Query must not be empty.", "success": False}

    url = f"{_BASE_URL}/search"
    params = {"query": query}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if resp.status_code == 429:
            return _rate_limit_error()
        if not resp.is_success:
            return {"error": f"CoinGecko API returned status {resp.status_code}", "success": False}
        data = resp.json()

    coins_raw = data.get("coins") or []
    results: List[Dict[str, Any]] = []

    for coin in coins_raw:
        results.append({
            "id": coin.get("id"),
            "name": coin.get("name"),
            "symbol": (coin.get("symbol") or "").upper(),
            "market_cap_rank": coin.get("market_cap_rank"),
            "thumb": coin.get("thumb"),
        })

    return {
        "query": query,
        "results": results,
        "count": len(results),
        "success": True,
    }


@skill(
    name="crypto_global",
    display_name="Global Crypto Market",
    description="Get global cryptocurrency market data and statistics (CoinGecko, no key required).",
    category="crypto",
    tags=["crypto", "global", "market", "stats", "dominance"],
    icon="trending-up",
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
async def crypto_global(
    timeout: int = 15,
) -> dict:
    """Fetch global crypto market overview: total market cap, volume, BTC dominance.

    Args:
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"{_BASE_URL}/global"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=timeout)
        if resp.status_code == 429:
            return _rate_limit_error()
        if not resp.is_success:
            return {"error": f"CoinGecko API returned status {resp.status_code}", "success": False}
        data = resp.json()

    gdata = data.get("data") or {}

    total_market_cap = (gdata.get("total_market_cap") or {}).get("usd")
    total_volume = (gdata.get("total_volume") or {}).get("usd")
    btc_dominance = gdata.get("market_cap_percentage", {}).get("btc")
    eth_dominance = gdata.get("market_cap_percentage", {}).get("eth")
    market_cap_change_24h = gdata.get("market_cap_change_percentage_24h_usd")

    return {
        "total_market_cap": total_market_cap,
        "total_market_cap_formatted": _fmt_large_number(total_market_cap),
        "total_volume_24h": total_volume,
        "total_volume_24h_formatted": _fmt_large_number(total_volume),
        "btc_dominance": btc_dominance,
        "btc_dominance_formatted": f"{btc_dominance:.1f}%" if btc_dominance is not None else "N/A",
        "eth_dominance": eth_dominance,
        "eth_dominance_formatted": f"{eth_dominance:.1f}%" if eth_dominance is not None else "N/A",
        "market_cap_change_24h_pct": market_cap_change_24h,
        "active_cryptocurrencies": gdata.get("active_cryptocurrencies"),
        "markets": gdata.get("markets"),
        "ongoing_icos": gdata.get("ongoing_icos"),
        "ended_icos": gdata.get("ended_icos"),
        "_disclaimer": _DISCLAIMER,
        "success": True,
    }


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------


class CoinGeckoPlugin(TransformerPlugin):
    """Plugin providing CoinGecko cryptocurrency market data skills and formatters."""

    def __init__(self):
        super().__init__("coingecko")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_crypto_price": lambda _: FormatCryptoPriceTransformer("format_crypto_price"),
            "format_market_cap": lambda _: FormatMarketCapTransformer("format_market_cap"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "crypto_price": crypto_price.__skill__,
            "crypto_details": crypto_details.__skill__,
            "crypto_chart": crypto_chart.__skill__,
            "crypto_trending": crypto_trending.__skill__,
            "crypto_search": crypto_search.__skill__,
            "crypto_global": crypto_global.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="coingecko",
            display_name="CoinGecko",
            description="Cryptocurrency prices, market data, trends, and history via CoinGecko API.",
            icon="bitcoin",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
