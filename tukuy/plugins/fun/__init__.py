"""Fun and entertainment plugin.

Provides async skills for jokes, quotes, advice, trivia, and number facts
using various free APIs (no keys required).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel


# -- Skills ------------------------------------------------------------------


@skill(
    name="random_joke",
    display_name="Random Joke",
    description="Get a random joke with optional category filter (JokeAPI, free, no key required).",
    category="fun",
    tags=["joke", "humor", "fun", "entertainment"],
    icon="smile",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=False,
    requires_network=True,
    required_imports=["httpx"],
)
async def random_joke(
    category: str = "Any",
    safe_mode: bool = True,
    language: str = "en",
) -> dict:
    """Get a random joke.

    Args:
        category: Joke category: Any, Programming, Misc, Dark, Pun, Spooky, Christmas.
        safe_mode: If True, exclude NSFW/racist/sexist jokes (default True).
        language: Language code (default ``"en"``).
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = f"https://v2.jokeapi.dev/joke/{category}"
    params = {"lang": language}
    if safe_mode:
        params["safe-mode"] = ""

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"JokeAPI returned status {resp.status_code}", "success": False}
        data = resp.json()

    if data.get("error"):
        return {"error": data.get("message", "Unknown error"), "success": False}

    result = {
        "category": data.get("category", ""),
        "type": data.get("type", ""),
        "language": data.get("lang", language),
        "safe": data.get("safe", True),
        "success": True,
    }

    if data.get("type") == "twopart":
        result["setup"] = data.get("setup", "")
        result["delivery"] = data.get("delivery", "")
        result["joke"] = f"{data.get('setup', '')}\n{data.get('delivery', '')}"
    else:
        result["joke"] = data.get("joke", "")

    return result


@skill(
    name="random_quote",
    display_name="Random Quote",
    description="Get a random inspirational quote (Quotable API, free, no key required).",
    category="fun",
    tags=["quote", "inspiration", "wisdom"],
    icon="quote",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=False,
    requires_network=True,
    required_imports=["httpx"],
)
async def random_quote(tag: str = "") -> dict:
    """Get a random quote, optionally filtered by tag.

    Args:
        tag: Optional tag filter (e.g. ``"technology"``, ``"wisdom"``, ``"humor"``).
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = "https://api.quotable.io/quotes/random"
    params = {}
    if tag.strip():
        params["tags"] = tag.strip()

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Quotable API returned status {resp.status_code}", "success": False}
        data = resp.json()

    if not data or not isinstance(data, list):
        return {"error": "No quote returned.", "success": False}

    q = data[0]
    return {
        "quote": q.get("content", ""),
        "author": q.get("author", ""),
        "tags": q.get("tags", []),
        "success": True,
    }


@skill(
    name="random_advice",
    display_name="Random Advice",
    description="Get a random piece of life advice (Advice Slip API, free, no key required).",
    category="fun",
    tags=["advice", "wisdom", "random"],
    icon="lightbulb",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=False,
    requires_network=True,
    required_imports=["httpx"],
)
async def random_advice() -> dict:
    """Get a random piece of advice."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = "https://api.adviceslip.com/advice"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    slip = data.get("slip", {})
    return {
        "advice": slip.get("advice", ""),
        "id": slip.get("id"),
        "success": True,
    }


@skill(
    name="number_fact",
    display_name="Number Fact",
    description="Get a fun fact about a number (Numbers API, free, no key required).",
    category="fun",
    tags=["number", "trivia", "fact", "math"],
    icon="hash",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def number_fact(
    number: int = 42,
    fact_type: str = "trivia",
) -> dict:
    """Get a fun fact about a number.

    Args:
        number: The number to get a fact about.
        fact_type: Type of fact: trivia, math, date, or year.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    fact_type = fact_type.strip().lower()
    if fact_type not in ("trivia", "math", "date", "year"):
        return {"error": "fact_type must be one of: trivia, math, date, year", "success": False}

    url = f"http://numbersapi.com/{number}/{fact_type}"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"Content-Type": "text/plain"}, timeout=15)
        if not resp.is_success:
            return {"error": f"Numbers API returned status {resp.status_code}", "success": False}

    return {
        "number": number,
        "type": fact_type,
        "fact": resp.text.strip(),
        "success": True,
    }


@skill(
    name="trivia_question",
    display_name="Trivia Question",
    description="Get random trivia questions (Open Trivia DB, free, no key required).",
    category="fun",
    tags=["trivia", "quiz", "question", "game"],
    icon="help-circle",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=False,
    requires_network=True,
    required_imports=["httpx"],
)
async def trivia_question(
    amount: int = 1,
    category: int = 0,
    difficulty: str = "",
) -> dict:
    """Get random trivia questions.

    Args:
        amount: Number of questions (1-50, default 1).
        category: Category ID (0 = any, 9=General, 18=Computers, 21=Sports, etc.).
        difficulty: Difficulty: easy, medium, hard, or empty for any.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = "https://opentdb.com/api.php"
    params = {"amount": min(max(amount, 1), 50)}
    if category > 0:
        params["category"] = category
    if difficulty in ("easy", "medium", "hard"):
        params["difficulty"] = difficulty

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Open Trivia DB returned status {resp.status_code}", "success": False}
        data = resp.json()

    if data.get("response_code") != 0:
        return {"error": "No trivia questions available for these filters.", "success": False}

    import html as html_mod
    questions = []
    for q in data.get("results", []):
        incorrect = [html_mod.unescape(a) for a in q.get("incorrect_answers", [])]
        questions.append({
            "category": html_mod.unescape(q.get("category", "")),
            "difficulty": q.get("difficulty", ""),
            "question": html_mod.unescape(q.get("question", "")),
            "correct_answer": html_mod.unescape(q.get("correct_answer", "")),
            "incorrect_answers": incorrect,
            "type": q.get("type", ""),
        })

    return {
        "questions": questions,
        "count": len(questions),
        "success": True,
    }


@skill(
    name="dad_joke",
    display_name="Dad Joke",
    description="Get a random dad joke (icanhazdadjoke, free, no key required).",
    category="fun",
    tags=["joke", "dad", "humor"],
    icon="smile",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=False,
    requires_network=True,
    required_imports=["httpx"],
)
async def dad_joke() -> dict:
    """Get a random dad joke."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    url = "https://icanhazdadjoke.com/"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"Accept": "application/json"}, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}
        data = resp.json()

    return {
        "joke": data.get("joke", ""),
        "id": data.get("id", ""),
        "success": True,
    }


class FunPlugin(TransformerPlugin):
    """Plugin providing fun and entertainment skills."""

    def __init__(self):
        super().__init__("fun")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "random_joke": random_joke.__skill__,
            "random_quote": random_quote.__skill__,
            "random_advice": random_advice.__skill__,
            "number_fact": number_fact.__skill__,
            "trivia_question": trivia_question.__skill__,
            "dad_joke": dad_joke.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="fun",
            display_name="Fun & Trivia",
            description="Jokes, quotes, advice, trivia, and number facts from various free APIs.",
            icon="smile",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
