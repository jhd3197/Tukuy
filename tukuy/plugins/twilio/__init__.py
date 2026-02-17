"""Twilio plugin.

Provides async skills to send SMS/WhatsApp messages and make phone calls
via the Twilio REST API, plus status-check skills for sent messages and calls.

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import os
from typing import Any, Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.twilio.com/2010-04-01"

_COST_WARNING = "This message was sent via Twilio and may incur charges."
_DISCLAIMER = "Twilio charges may apply. Messages/calls are sent to real recipients."


# ── Helpers ───────────────────────────────────────────────────────────────


def _get_credentials():
    """Return ``(account_sid, auth_token)`` from env vars, or ``(None, None)``."""
    return (
        os.environ.get("TWILIO_ACCOUNT_SID"),
        os.environ.get("TWILIO_AUTH_TOKEN"),
    )


def _account_url(account_sid: str) -> str:
    """Return the base account URL for the given SID."""
    return f"{_BASE_URL}/Accounts/{account_sid}"


def _parse_message(raw: dict) -> dict:
    """Normalise a Twilio message resource into a flat dict."""
    return {
        "sid": raw.get("sid"),
        "from_number": raw.get("from"),
        "to": raw.get("to"),
        "body": raw.get("body"),
        "status": raw.get("status"),
        "direction": raw.get("direction"),
        "date_created": raw.get("date_created"),
        "date_sent": raw.get("date_sent"),
        "price": raw.get("price"),
        "price_unit": raw.get("price_unit"),
        "num_segments": raw.get("num_segments"),
        "error_code": raw.get("error_code"),
        "error_message": raw.get("error_message"),
    }


def _parse_call(raw: dict) -> dict:
    """Normalise a Twilio call resource into a flat dict."""
    return {
        "sid": raw.get("sid"),
        "from_number": raw.get("from"),
        "to": raw.get("to"),
        "status": raw.get("status"),
        "direction": raw.get("direction"),
        "duration": raw.get("duration"),
        "start_time": raw.get("start_time"),
        "end_time": raw.get("end_time"),
        "price": raw.get("price"),
        "price_unit": raw.get("price_unit"),
        "answered_by": raw.get("answered_by"),
    }


# ── Transformer ───────────────────────────────────────────────────────────


class FormatMessageStatusTransformer(ChainableTransformer[dict, str]):
    """Format a message dict into a human-readable status line.

    Example output: ``SMS to +1234567890 -- delivered -- $0.0075``
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "sid" in value and "status" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        to = value.get("to", "unknown")
        status = value.get("status", "unknown")
        price = value.get("price")
        if price is not None:
            return f"SMS to {to} \u2014 {status} \u2014 ${abs(float(price))}"
        return f"SMS to {to} \u2014 {status}"


# ── Skills ────────────────────────────────────────────────────────────────

_COMMON_CONFIG_PARAMS = [
    ConfigParam(
        name="account_sid",
        display_name="Account SID",
        description="Twilio Account SID. Falls back to TWILIO_ACCOUNT_SID env var.",
        type="secret",
        placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    ),
    ConfigParam(
        name="auth_token",
        display_name="Auth Token",
        description="Twilio Auth Token. Falls back to TWILIO_AUTH_TOKEN env var.",
        type="secret",
        placeholder="your-twilio-auth-token",
    ),
    ConfigParam(
        name="from_number",
        display_name="From Number",
        description="Default sender phone number. Falls back to TWILIO_FROM_NUMBER env var.",
        type="string",
        placeholder="+1234567890",
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
]


@skill(
    name="twilio_send_sms",
    display_name="Send SMS",
    description="Send an SMS message via Twilio (requires TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN env vars). Costs real money.",
    category="messaging",
    tags=["twilio", "sms", "messaging", "text"],
    icon="phone",
    risk_level=RiskLevel.DANGEROUS,
    group="Integrations",
    idempotent=False,
    side_effects=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG_PARAMS,
)
async def twilio_send_sms(to: str, body: str, from_number: str = "") -> dict:
    """Send an SMS message via the Twilio REST API."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    account_sid, auth_token = _get_credentials()
    if not account_sid or not auth_token:
        return {
            "error": "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN env vars are required.",
            "success": False,
        }

    if not to.startswith("+"):
        return {"error": "The 'to' number must be in E.164 format (e.g. +1234567890).", "success": False}
    if not body:
        return {"error": "Message body must not be empty.", "success": False}
    if len(body) > 1600:
        return {"error": "Message body must be 1600 characters or fewer.", "success": False}

    from_number = from_number or os.environ.get("TWILIO_FROM_NUMBER", "")
    if not from_number:
        return {"error": "No sender number. Set from_number or TWILIO_FROM_NUMBER env var.", "success": False}

    url = f"{_account_url(account_sid)}/Messages.json"
    check_host(url)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            data={"To": to, "From": from_number, "Body": body},
            auth=(account_sid, auth_token),
            timeout=15,
        )
        if not resp.is_success:
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            return {
                "error": error_data.get("message", f"API returned status {resp.status_code}"),
                "status_code": resp.status_code,
                "success": False,
            }
        data = resp.json()
        result = _parse_message(data)
        result["success"] = True
        result["_cost_warning"] = _COST_WARNING
        result["_disclaimer"] = _DISCLAIMER
        return result


@skill(
    name="twilio_send_whatsapp",
    display_name="Send WhatsApp Message",
    description="Send a WhatsApp message via Twilio (requires TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN env vars). Costs real money.",
    category="messaging",
    tags=["twilio", "whatsapp", "messaging"],
    icon="phone",
    risk_level=RiskLevel.DANGEROUS,
    group="Integrations",
    idempotent=False,
    side_effects=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG_PARAMS,
)
async def twilio_send_whatsapp(to: str, body: str, from_number: str = "") -> dict:
    """Send a WhatsApp message via the Twilio REST API."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    account_sid, auth_token = _get_credentials()
    if not account_sid or not auth_token:
        return {
            "error": "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN env vars are required.",
            "success": False,
        }

    if not to.startswith("+"):
        return {"error": "The 'to' number must be in E.164 format (e.g. +1234567890).", "success": False}
    if not body:
        return {"error": "Message body must not be empty.", "success": False}
    if len(body) > 1600:
        return {"error": "Message body must be 1600 characters or fewer.", "success": False}

    from_number = from_number or os.environ.get("TWILIO_WHATSAPP_NUMBER", "")
    if not from_number:
        return {"error": "No sender number. Set from_number or TWILIO_WHATSAPP_NUMBER env var.", "success": False}

    url = f"{_account_url(account_sid)}/Messages.json"
    check_host(url)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            data={
                "To": f"whatsapp:{to}",
                "From": f"whatsapp:{from_number}",
                "Body": body,
            },
            auth=(account_sid, auth_token),
            timeout=15,
        )
        if not resp.is_success:
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            return {
                "error": error_data.get("message", f"API returned status {resp.status_code}"),
                "status_code": resp.status_code,
                "success": False,
            }
        data = resp.json()
        result = _parse_message(data)
        result["success"] = True
        result["_cost_warning"] = _COST_WARNING
        result["_disclaimer"] = _DISCLAIMER
        return result


@skill(
    name="twilio_make_call",
    display_name="Make Phone Call",
    description="Initiate a phone call via Twilio with TwiML or a TwiML URL (requires TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN env vars). Costs real money.",
    category="messaging",
    tags=["twilio", "call", "voice", "phone"],
    icon="phone",
    risk_level=RiskLevel.DANGEROUS,
    group="Integrations",
    idempotent=False,
    side_effects=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG_PARAMS,
)
async def twilio_make_call(
    to: str,
    from_number: str = "",
    twiml: str = "<Response><Say>Hello from Tukuy</Say></Response>",
    url: str = "",
) -> dict:
    """Initiate a phone call via the Twilio REST API."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    account_sid, auth_token = _get_credentials()
    if not account_sid or not auth_token:
        return {
            "error": "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN env vars are required.",
            "success": False,
        }

    if not to.startswith("+"):
        return {"error": "The 'to' number must be in E.164 format (e.g. +1234567890).", "success": False}

    from_number = from_number or os.environ.get("TWILIO_FROM_NUMBER", "")
    if not from_number:
        return {"error": "No sender number. Set from_number or TWILIO_FROM_NUMBER env var.", "success": False}

    endpoint = f"{_account_url(account_sid)}/Calls.json"
    check_host(endpoint)

    form_data: Dict[str, str] = {"To": to, "From": from_number}
    if twiml:
        form_data["Twiml"] = twiml
    elif url:
        form_data["Url"] = url
    else:
        form_data["Twiml"] = "<Response><Say>Hello from Tukuy</Say></Response>"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            endpoint,
            data=form_data,
            auth=(account_sid, auth_token),
            timeout=15,
        )
        if not resp.is_success:
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            return {
                "error": error_data.get("message", f"API returned status {resp.status_code}"),
                "status_code": resp.status_code,
                "success": False,
            }
        data = resp.json()
        result = _parse_call(data)
        result["success"] = True
        result["_cost_warning"] = "This call was initiated via Twilio and may incur charges."
        result["_disclaimer"] = _DISCLAIMER
        return result


@skill(
    name="twilio_message_status",
    display_name="Message Status",
    description="Get the delivery status of a sent Twilio message by its SID.",
    category="messaging",
    tags=["twilio", "sms", "status"],
    icon="phone",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG_PARAMS,
)
async def twilio_message_status(message_sid: str) -> dict:
    """Retrieve the status of a previously sent message."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    account_sid, auth_token = _get_credentials()
    if not account_sid or not auth_token:
        return {
            "error": "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN env vars are required.",
            "success": False,
        }

    if not message_sid:
        return {"error": "message_sid is required.", "success": False}

    url = f"{_account_url(account_sid)}/Messages/{message_sid}.json"
    check_host(url)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            auth=(account_sid, auth_token),
            timeout=15,
        )
        if not resp.is_success:
            return {
                "error": f"API returned status {resp.status_code}",
                "status_code": resp.status_code,
                "success": False,
            }
        data = resp.json()
        result = _parse_message(data)
        result["success"] = True
        return result


@skill(
    name="twilio_call_status",
    display_name="Call Status",
    description="Get the status of a Twilio call by its SID.",
    category="messaging",
    tags=["twilio", "call", "status"],
    icon="phone",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG_PARAMS,
)
async def twilio_call_status(call_sid: str) -> dict:
    """Retrieve the status of a previously initiated call."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    account_sid, auth_token = _get_credentials()
    if not account_sid or not auth_token:
        return {
            "error": "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN env vars are required.",
            "success": False,
        }

    if not call_sid:
        return {"error": "call_sid is required.", "success": False}

    url = f"{_account_url(account_sid)}/Calls/{call_sid}.json"
    check_host(url)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            auth=(account_sid, auth_token),
            timeout=15,
        )
        if not resp.is_success:
            return {
                "error": f"API returned status {resp.status_code}",
                "status_code": resp.status_code,
                "success": False,
            }
        data = resp.json()
        result = _parse_call(data)
        result["success"] = True
        return result


# ── Plugin class ──────────────────────────────────────────────────────────


class TwilioPlugin(TransformerPlugin):
    """Plugin providing Twilio SMS, WhatsApp, and voice call skills."""

    def __init__(self):
        super().__init__("twilio")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_message_status": lambda _: FormatMessageStatusTransformer("format_message_status"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "twilio_send_sms": twilio_send_sms.__skill__,
            "twilio_send_whatsapp": twilio_send_whatsapp.__skill__,
            "twilio_make_call": twilio_make_call.__skill__,
            "twilio_message_status": twilio_message_status.__skill__,
            "twilio_call_status": twilio_call_status.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="twilio",
            display_name="Twilio",
            description="Send SMS, WhatsApp messages, and make calls via Twilio API.",
            icon="phone",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
