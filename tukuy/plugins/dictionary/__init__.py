"""Dictionary and word API plugin.

Provides async skills for word definitions (Free Dictionary API) and
word finding/rhymes/synonyms (Datamuse API). Both free, no key required.

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_DICTIONARY_URL = "https://api.dictionaryapi.dev/api/v2/entries"
_DATAMUSE_URL = "https://api.datamuse.com"


class FormatDefinitionTransformer(ChainableTransformer[dict, str]):
    """Format a dictionary result into a readable string."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "word" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        word = value.get("word", "")
        phonetic = value.get("phonetic", "")
        meanings = value.get("meanings", [])
        parts = [f"{word} {phonetic}".strip()]
        for m in meanings[:3]:
            pos = m.get("part_of_speech", "")
            defs = m.get("definitions", [])
            if defs:
                parts.append(f"  ({pos}) {defs[0].get('definition', '')}")
        return "\n".join(parts)


# -- Skills ------------------------------------------------------------------


@skill(
    name="word_define",
    display_name="Define Word",
    description="Get definitions, phonetics, and examples for a word (Free Dictionary API, no key required).",
    category="dictionary",
    tags=["dictionary", "definition", "word", "language"],
    icon="book-open",
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
async def word_define(
    word: str,
    language: str = "en",
    timeout: int = 15,
) -> dict:
    """Look up a word's definitions, phonetics, synonyms, and examples.

    Args:
        word: The word to define.
        language: Language code (e.g. ``"en"``, ``"es"``, ``"fr"``).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    word = word.strip().lower()
    if not word:
        return {"error": "Word must not be empty.", "success": False}

    url = f"{_DICTIONARY_URL}/{language}/{word}"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=timeout)
        if not resp.is_success:
            return {"word": word, "error": f"Word not found (status {resp.status_code})", "success": False}
        data = resp.json()

    if not data or not isinstance(data, list):
        return {"word": word, "error": "No results", "success": False}

    entry = data[0]
    phonetic = entry.get("phonetic", "")
    phonetics = []
    for p in entry.get("phonetics", []):
        ph = {"text": p.get("text", "")}
        if p.get("audio"):
            ph["audio"] = p["audio"]
        phonetics.append(ph)

    meanings = []
    all_synonyms = set()
    all_antonyms = set()
    for m in entry.get("meanings", []):
        pos = m.get("partOfSpeech", "")
        defs = []
        for d in m.get("definitions", []):
            defn = {"definition": d.get("definition", "")}
            if d.get("example"):
                defn["example"] = d["example"]
            syns = d.get("synonyms", [])
            ants = d.get("antonyms", [])
            if syns:
                defn["synonyms"] = syns
                all_synonyms.update(syns)
            if ants:
                defn["antonyms"] = ants
                all_antonyms.update(ants)
            defs.append(defn)
        all_synonyms.update(m.get("synonyms", []))
        all_antonyms.update(m.get("antonyms", []))
        meanings.append({"part_of_speech": pos, "definitions": defs})

    return {
        "word": entry.get("word", word),
        "phonetic": phonetic,
        "phonetics": phonetics,
        "meanings": meanings,
        "synonyms": sorted(all_synonyms)[:20],
        "antonyms": sorted(all_antonyms)[:20],
        "success": True,
    }


@skill(
    name="word_synonyms",
    display_name="Find Synonyms",
    description="Find synonyms for a word using the Datamuse API (free, no key required).",
    category="dictionary",
    tags=["synonyms", "thesaurus", "word", "language"],
    icon="book-open",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def word_synonyms(word: str, max_results: int = 20) -> dict:
    """Find words with similar meaning (synonyms).

    Args:
        word: The word to find synonyms for.
        max_results: Maximum number of results (default 20).
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    word = word.strip()
    url = f"{_DATAMUSE_URL}/words"
    params = {"ml": word, "max": min(max_results, 100)}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Datamuse API returned status {resp.status_code}", "success": False}
        data = resp.json()

    results = [{"word": w["word"], "score": w.get("score", 0)} for w in data]
    return {
        "query": word,
        "synonyms": results,
        "count": len(results),
        "success": True,
    }


@skill(
    name="word_rhymes",
    display_name="Find Rhymes",
    description="Find words that rhyme with a given word (Datamuse API, free, no key required).",
    category="dictionary",
    tags=["rhyme", "poetry", "word", "language"],
    icon="music",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def word_rhymes(word: str, max_results: int = 20) -> dict:
    """Find words that rhyme with the given word.

    Args:
        word: The word to find rhymes for.
        max_results: Maximum number of results (default 20).
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    word = word.strip()
    url = f"{_DATAMUSE_URL}/words"
    params = {"rel_rhy": word, "max": min(max_results, 100)}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Datamuse API returned status {resp.status_code}", "success": False}
        data = resp.json()

    results = [{"word": w["word"], "score": w.get("score", 0), "syllables": w.get("numSyllables")} for w in data]
    return {
        "query": word,
        "rhymes": results,
        "count": len(results),
        "success": True,
    }


@skill(
    name="word_sounds_like",
    display_name="Sounds Like",
    description="Find words that sound similar to a given word (Datamuse API, free, no key required).",
    category="dictionary",
    tags=["sounds-like", "phonetic", "word", "language"],
    icon="volume-2",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def word_sounds_like(word: str, max_results: int = 20) -> dict:
    """Find words that sound similar to the given word.

    Args:
        word: The word to match phonetically.
        max_results: Maximum number of results (default 20).
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    word = word.strip()
    url = f"{_DATAMUSE_URL}/words"
    params = {"sl": word, "max": min(max_results, 100)}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Datamuse API returned status {resp.status_code}", "success": False}
        data = resp.json()

    results = [{"word": w["word"], "score": w.get("score", 0)} for w in data]
    return {
        "query": word,
        "matches": results,
        "count": len(results),
        "success": True,
    }


@skill(
    name="word_related",
    display_name="Related Words",
    description="Find words related to a topic or triggered by a word (Datamuse API, free, no key required).",
    category="dictionary",
    tags=["related", "association", "word", "language"],
    icon="link",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def word_related(word: str, max_results: int = 20) -> dict:
    """Find words triggered by or associated with the given word.

    Args:
        word: The trigger word.
        max_results: Maximum number of results (default 20).
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    word = word.strip()
    url = f"{_DATAMUSE_URL}/words"
    params = {"rel_trg": word, "max": min(max_results, 100)}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15)
        if not resp.is_success:
            return {"error": f"Datamuse API returned status {resp.status_code}", "success": False}
        data = resp.json()

    results = [{"word": w["word"], "score": w.get("score", 0)} for w in data]
    return {
        "query": word,
        "related": results,
        "count": len(results),
        "success": True,
    }


class DictionaryPlugin(TransformerPlugin):
    """Plugin providing dictionary and word-finding skills."""

    def __init__(self):
        super().__init__("dictionary")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_definition": lambda _: FormatDefinitionTransformer("format_definition"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "word_define": word_define.__skill__,
            "word_synonyms": word_synonyms.__skill__,
            "word_rhymes": word_rhymes.__skill__,
            "word_sounds_like": word_sounds_like.__skill__,
            "word_related": word_related.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="dictionary",
            display_name="Dictionary",
            description="Word definitions, synonyms, rhymes, and related words via Free Dictionary and Datamuse APIs.",
            icon="book-open",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
