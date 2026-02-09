"""HTTP plugin.

Provides an async ``http_request`` skill and a ``parse_response`` transformer.

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

from typing import Any, Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, ConfigScope, RiskLevel


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
    display_name="HTTP Request",
    description="Make an async HTTP request (GET/POST/PUT/DELETE) with headers, body, and auth.",
    category="http",
    tags=["http", "request", "api"],
    icon="send",
    risk_level=RiskLevel.MODERATE,
    group="HTTP",
    side_effects=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=[
        ConfigParam(
            name="base_url",
            display_name="Base URL",
            description="Base URL prepended to relative request paths.",
            type="url",
            placeholder="https://api.example.com/v1",
        ),
        ConfigParam(
            name="timeout",
            display_name="Timeout",
            description="Request timeout.",
            type="number",
            default=30,
            min=1,
            max=300,
            unit="seconds",
        ),
        ConfigParam(
            name="allowed_methods",
            display_name="Allowed Methods",
            description="HTTP methods permitted for requests. Empty allows all.",
            type="multiselect",
            default=[],
            options=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        ),
        ConfigParam(
            name="default_headers",
            display_name="Default Headers",
            description="Headers sent with every request.",
            type="map",
            default={},
            key_placeholder="Header-Name",
            value_placeholder="value",
        ),
        ConfigParam(
            name="auth_token",
            display_name="Auth Token",
            description="Bearer token for authenticated requests.",
            type="secret",
            placeholder="sk-...",
        ),
        ConfigParam(
            name="request_body_template",
            display_name="Body Template",
            description="Default JSON body template for requests.",
            type="code",
            language="json",
            placeholder='{"key": "value"}',
            rows=6,
        ),
        ConfigParam(
            name="blocked_hosts",
            display_name="Blocked Hosts",
            description="Hosts that requests are not allowed to reach.",
            type="string[]",
            default=[],
            item_placeholder="e.g. internal.corp",
        ),
    ],
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

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="http",
            display_name="HTTP",
            description="Make HTTP requests with headers, body, and authentication.",
            icon="send",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
