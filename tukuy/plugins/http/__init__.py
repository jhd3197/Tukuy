"""HTTP plugin.

Provides an async ``http_request`` skill and a ``parse_response`` transformer.

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill


class ParseResponseTransformer(ChainableTransformer[dict, dict]):
    """Extract body, headers, and status from an HTTP response dict."""

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict)

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> dict:
        return {
            "status_code": value.get("status_code"),
            "headers": value.get("headers", {}),
            "body": value.get("body", value.get("content", "")),
            "ok": 200 <= (value.get("status_code") or 0) < 400,
        }


@skill(
    name="http_request",
    description="Make an async HTTP request (GET/POST/PUT/DELETE) with headers, body, and auth.",
    category="http",
    tags=["http", "request", "api"],
    side_effects=True,
    requires_network=True,
    required_imports=["httpx"],
)
async def http_request(
    url: str,
    method: str = "GET",
    headers: dict = None,
    body: Any = None,
    auth: tuple = None,
    timeout: int = 30,
) -> dict:
    """Perform an HTTP request using httpx."""
    check_host(url)
    try:
        import httpx
    except ImportError:
        return {
            "url": url,
            "error": "httpx is required. Install with: pip install httpx",
            "status_code": None,
            "success": False,
        }

    kwargs: Dict[str, Any] = {
        "method": method.upper(),
        "url": url,
        "timeout": timeout,
    }
    if headers:
        kwargs["headers"] = headers
    if body is not None:
        if isinstance(body, (dict, list)):
            kwargs["json"] = body
        else:
            kwargs["content"] = str(body)
    if auth:
        kwargs["auth"] = tuple(auth)

    async with httpx.AsyncClient() as client:
        response = await client.request(**kwargs)
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response_body,
            "success": response.is_success,
        }


class HttpPlugin(TransformerPlugin):
    """Plugin providing HTTP request skill and response parsing transformer."""

    def __init__(self):
        super().__init__("http")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "parse_response": lambda _: ParseResponseTransformer("parse_response"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "http_request": http_request.__skill__,
        }
