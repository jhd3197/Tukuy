"""Open Library book search plugin.

Provides async skills for searching books and looking up ISBNs using the
Open Library API (free, no key required, unlimited).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://openlibrary.org"


# -- Skills ------------------------------------------------------------------


@skill(
    name="book_search",
    display_name="Search Books",
    description="Search for books by title, author, or subject (Open Library, free, no key required).",
    category="open_library",
    tags=["book", "search", "library", "isbn", "literature"],
    icon="book",
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
async def book_search(
    query: str,
    limit: int = 10,
    timeout: int = 15,
) -> dict:
    """Search for books matching a query.

    Args:
        query: Search query (title, author, or keywords).
        limit: Maximum results to return (default 10).
        timeout: Request timeout in seconds.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    query = query.strip()
    if not query:
        return {"error": "Query must not be empty.", "success": False}

    url = f"{_BASE_URL}/search.json"
    params = {"q": query, "limit": min(limit, 50)}

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=timeout)
        if not resp.is_success:
            return {"error": f"Open Library returned status {resp.status_code}", "success": False}
        data = resp.json()

    books = []
    for doc in data.get("docs", [])[:limit]:
        isbn_list = doc.get("isbn", [])
        books.append({
            "title": doc.get("title", ""),
            "author": (doc.get("author_name") or ["Unknown"])[0],
            "authors": doc.get("author_name", []),
            "first_publish_year": doc.get("first_publish_year"),
            "isbn": isbn_list[0] if isbn_list else None,
            "number_of_pages": doc.get("number_of_pages_median"),
            "publisher": (doc.get("publisher") or [None])[0],
            "language": (doc.get("language") or [None])[0],
            "subject": (doc.get("subject") or [])[:5],
            "cover_id": doc.get("cover_i"),
        })

    return {
        "query": query,
        "books": books,
        "total_found": data.get("numFound", 0),
        "count": len(books),
        "success": True,
    }


@skill(
    name="book_isbn",
    display_name="ISBN Lookup",
    description="Look up a book by its ISBN (Open Library, free, no key required).",
    category="open_library",
    tags=["book", "isbn", "lookup"],
    icon="book",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def book_isbn(isbn: str) -> dict:
    """Look up detailed book information by ISBN.

    Args:
        isbn: ISBN-10 or ISBN-13.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    isbn = isbn.strip().replace("-", "")
    if not isbn:
        return {"error": "ISBN must not be empty.", "success": False}

    url = f"{_BASE_URL}/isbn/{isbn}.json"

    check_host(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15, follow_redirects=True)
        if not resp.is_success:
            return {"error": f"ISBN not found (status {resp.status_code})", "isbn": isbn, "success": False}
        data = resp.json()

        # Resolve author names
        authors = []
        for a in data.get("authors", []):
            author_key = a.get("key", "")
            if author_key:
                author_url = f"{_BASE_URL}{author_key}.json"
                check_host(author_url)
                aresp = await client.get(author_url, timeout=10)
                if aresp.is_success:
                    adata = aresp.json()
                    authors.append(adata.get("name", ""))

    return {
        "isbn": isbn,
        "title": data.get("title", ""),
        "authors": authors or ["Unknown"],
        "publishers": data.get("publishers", []),
        "publish_date": data.get("publish_date", ""),
        "number_of_pages": data.get("number_of_pages"),
        "subjects": [s.get("name", s) if isinstance(s, dict) else s for s in data.get("subjects", [])[:10]],
        "cover": f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
        "success": True,
    }


class OpenLibraryPlugin(TransformerPlugin):
    """Plugin providing book search and ISBN lookup skills."""

    def __init__(self):
        super().__init__("open_library")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "book_search": book_search.__skill__,
            "book_isbn": book_isbn.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="open_library",
            display_name="Open Library",
            description="Search books and look up ISBNs via the Open Library API.",
            icon="book",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
