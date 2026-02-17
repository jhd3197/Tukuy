"""Google Calendar plugin.

Provides async skills to list, create, update, and delete Google Calendar
events, plus a ``format_event`` transformer for human-readable output.

Supports two authentication modes:
  1. **API Key** (read-only, public calendars) via ``GOOGLE_CALENDAR_API_KEY``.
  2. **OAuth2 Bearer token** (full access) via ``GOOGLE_CALENDAR_TOKEN``.

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://www.googleapis.com/calendar/v3"


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _get_auth() -> Optional[Dict[str, str]]:
    """Return auth info from environment, preferring OAuth token over API key.

    Returns:
        ``{"type": "token", "value": "..."}`` or
        ``{"type": "api_key", "value": "..."}`` or ``None``.
    """
    token = os.environ.get("GOOGLE_CALENDAR_TOKEN")
    if token:
        return {"type": "token", "value": token}
    api_key = os.environ.get("GOOGLE_CALENDAR_API_KEY")
    if api_key:
        return {"type": "api_key", "value": api_key}
    return None


def _add_auth(params: dict, headers: dict, auth: dict) -> None:
    """Mutate *params* / *headers* to include the appropriate auth."""
    if auth["type"] == "token":
        headers["Authorization"] = f"Bearer {auth['value']}"
    else:
        params["key"] = auth["value"]


# ---------------------------------------------------------------------------
# Event parsing helpers
# ---------------------------------------------------------------------------

def _parse_event(raw: dict) -> dict:
    """Normalise a raw Google Calendar event resource into a flat dict."""
    start_raw = raw.get("start", {})
    end_raw = raw.get("end", {})

    start = start_raw.get("dateTime") or start_raw.get("date", "")
    end = end_raw.get("dateTime") or end_raw.get("date", "")
    all_day = "dateTime" not in start_raw and "date" in start_raw

    start_date = start_raw.get("date") or (start[:10] if len(start) >= 10 else "")
    end_date = end_raw.get("date") or (end[:10] if len(end) >= 10 else "")

    # Attendees
    attendees_raw = raw.get("attendees") or []
    attendees = [
        {
            "email": a.get("email", ""),
            "displayName": a.get("displayName", ""),
            "responseStatus": a.get("responseStatus", ""),
        }
        for a in attendees_raw
    ]

    # Hangout / conference link
    hangout_link = raw.get("hangoutLink", "")
    conference_data = raw.get("conferenceData") or {}
    entry_points = conference_data.get("entryPoints") or []
    if entry_points:
        hangout_link = entry_points[0].get("uri", hangout_link)

    creator = raw.get("creator") or {}
    organizer = raw.get("organizer") or {}

    return {
        "id": raw.get("id", ""),
        "summary": raw.get("summary", ""),
        "description": raw.get("description", ""),
        "location": raw.get("location", ""),
        "start": start,
        "end": end,
        "start_date": start_date,
        "end_date": end_date,
        "all_day": all_day,
        "status": raw.get("status", ""),
        "html_link": raw.get("htmlLink", ""),
        "creator": creator.get("email", ""),
        "organizer": {
            "email": organizer.get("email", ""),
            "displayName": organizer.get("displayName", ""),
        },
        "attendees": attendees,
        "recurrence": raw.get("recurrence"),
        "hangout_link": hangout_link,
    }


def _format_event_time(event: dict) -> str:
    """Format start/end into a human-readable string.

    Returns something like ``"Mon Feb 17, 2:00 PM - 3:00 PM"`` or
    ``"Mon Feb 17 (all day)"``.
    """
    if event.get("all_day"):
        try:
            dt = datetime.strptime(event["start_date"], "%Y-%m-%d")
            return dt.strftime("%a %b %d") + " (all day)"
        except (ValueError, KeyError):
            return event.get("start_date", "?") + " (all day)"

    start_str = event.get("start", "")
    end_str = event.get("end", "")

    def _parse_dt(s: str) -> Optional[datetime]:
        # RFC3339: 2026-02-17T14:00:00-05:00 or 2026-02-17T19:00:00Z
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        # Try with fractional seconds
        try:
            return datetime.fromisoformat(s)
        except (ValueError, TypeError):
            return None

    start_dt = _parse_dt(start_str)
    end_dt = _parse_dt(end_str)

    if start_dt and end_dt:
        day_part = start_dt.strftime("%a %b %d")
        start_time = start_dt.strftime("%-I:%M %p")
        end_time = end_dt.strftime("%-I:%M %p")
        return f"{day_part}, {start_time} - {end_time}"

    # Fallback
    return start_str


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------

class FormatEventTransformer(ChainableTransformer[dict, str]):
    """Format a parsed calendar event dict into a human-readable summary line.

    Output: ``"Mon Feb 17, 2:00 PM \u2014 Event Title \u2014 Location"``
    or ``"Mon Feb 17 (all day) \u2014 Event Title"`` when ``all_day`` is true.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "summary" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        time_part = _format_event_time(value)
        title = value.get("summary", "")
        location = value.get("location", "")

        parts = [time_part, title]
        if location:
            parts.append(location)
        return " \u2014 ".join(parts)


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

_COMMON_CONFIG = [
    ConfigParam(
        name="api_key",
        display_name="Google API Key",
        description="Google Calendar API key (env: GOOGLE_CALENDAR_API_KEY). Read-only, public calendars.",
        type="secret",
        placeholder="AIza...",
    ),
    ConfigParam(
        name="oauth_token",
        display_name="OAuth Token",
        description="Google Calendar OAuth2 Bearer token (env: GOOGLE_CALENDAR_TOKEN). Full access.",
        type="secret",
        placeholder="ya29...",
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
    name="calendar_events",
    display_name="List Calendar Events",
    description="List upcoming events from a Google Calendar.",
    category="calendar",
    tags=["calendar", "events", "google"],
    icon="calendar",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def calendar_events(
    calendar_id: str = "primary",
    max_results: int = 10,
    time_min: str = "",
    time_max: str = "",
    query: str = "",
    single_events: bool = True,
    order_by: str = "startTime",
) -> dict:
    """List upcoming events from a Google Calendar."""
    auth = _get_auth()
    if auth is None:
        return {
            "error": "No Google Calendar credentials found. Set GOOGLE_CALENDAR_TOKEN or GOOGLE_CALENDAR_API_KEY.",
            "success": False,
        }

    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    if not time_min:
        time_min = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    params: Dict[str, Any] = {
        "maxResults": max_results,
        "timeMin": time_min,
        "singleEvents": str(single_events).lower(),
        "orderBy": order_by,
    }
    if time_max:
        params["timeMax"] = time_max
    if query:
        params["q"] = query

    headers: Dict[str, str] = {}
    _add_auth(params, headers, auth)

    endpoint = f"{_BASE_URL}/calendars/{calendar_id}/events"
    check_host(endpoint)

    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, headers=headers, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}: {resp.text}", "success": False}
        data = resp.json()

    items = data.get("items", [])
    events = [_parse_event(item) for item in items]
    return {
        "calendar_id": calendar_id,
        "events": events,
        "count": len(events),
        "success": True,
    }


@skill(
    name="calendar_event_details",
    display_name="Event Details",
    description="Get full details of a single Google Calendar event by ID.",
    category="calendar",
    tags=["calendar", "event", "details", "google"],
    icon="calendar",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def calendar_event_details(
    event_id: str,
    calendar_id: str = "primary",
) -> dict:
    """Get a single event by ID from a Google Calendar."""
    auth = _get_auth()
    if auth is None:
        return {
            "error": "No Google Calendar credentials found. Set GOOGLE_CALENDAR_TOKEN or GOOGLE_CALENDAR_API_KEY.",
            "success": False,
        }

    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    params: Dict[str, Any] = {}
    headers: Dict[str, str] = {}
    _add_auth(params, headers, auth)

    endpoint = f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}"
    check_host(endpoint)

    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint, params=params, headers=headers, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}: {resp.text}", "success": False}
        data = resp.json()

    event = _parse_event(data)
    return {
        "event": event,
        "success": True,
    }


@skill(
    name="calendar_create_event",
    display_name="Create Event",
    description="Create a new event on a Google Calendar (requires OAuth token).",
    category="calendar",
    tags=["calendar", "create", "event", "google"],
    icon="calendar",
    risk_level=RiskLevel.MODERATE,
    group="Integrations",
    idempotent=False,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def calendar_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: str = "",
    calendar_id: str = "primary",
    timezone: str = "UTC",
) -> dict:
    """Create a new event on a Google Calendar."""
    auth = _get_auth()
    if auth is None:
        return {
            "error": "No Google Calendar credentials found. Set GOOGLE_CALENDAR_TOKEN or GOOGLE_CALENDAR_API_KEY.",
            "success": False,
        }
    if auth["type"] != "token":
        return {
            "error": "Creating events requires an OAuth token (GOOGLE_CALENDAR_TOKEN). API key is read-only.",
            "success": False,
        }

    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    # Detect all-day events: YYYY-MM-DD pattern (length 10, no 'T')
    all_day = len(start_time) == 10 and "T" not in start_time

    if all_day:
        start_body: Dict[str, str] = {"date": start_time}
        end_body: Dict[str, str] = {"date": end_time}
    else:
        start_body = {"dateTime": start_time, "timeZone": timezone}
        end_body = {"dateTime": end_time, "timeZone": timezone}

    event_resource: Dict[str, Any] = {
        "summary": summary,
        "start": start_body,
        "end": end_body,
    }
    if description:
        event_resource["description"] = description
    if location:
        event_resource["location"] = location
    if attendees:
        event_resource["attendees"] = [
            {"email": email.strip()} for email in attendees.split(",") if email.strip()
        ]

    params: Dict[str, Any] = {}
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    _add_auth(params, headers, auth)

    endpoint = f"{_BASE_URL}/calendars/{calendar_id}/events"
    check_host(endpoint)

    async with httpx.AsyncClient() as client:
        resp = await client.post(endpoint, params=params, headers=headers, json=event_resource, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}: {resp.text}", "success": False}
        data = resp.json()

    event = _parse_event(data)
    return {
        "event": event,
        "success": True,
    }


@skill(
    name="calendar_update_event",
    display_name="Update Event",
    description="Update an existing event on a Google Calendar (requires OAuth token).",
    category="calendar",
    tags=["calendar", "update", "event", "google"],
    icon="calendar",
    risk_level=RiskLevel.MODERATE,
    group="Integrations",
    idempotent=False,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def calendar_update_event(
    event_id: str,
    summary: str = "",
    start_time: str = "",
    end_time: str = "",
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
    timezone: str = "UTC",
) -> dict:
    """Update an existing event on a Google Calendar."""
    auth = _get_auth()
    if auth is None:
        return {
            "error": "No Google Calendar credentials found. Set GOOGLE_CALENDAR_TOKEN or GOOGLE_CALENDAR_API_KEY.",
            "success": False,
        }
    if auth["type"] != "token":
        return {
            "error": "Updating events requires an OAuth token (GOOGLE_CALENDAR_TOKEN). API key is read-only.",
            "success": False,
        }

    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    patch_body: Dict[str, Any] = {}
    if summary:
        patch_body["summary"] = summary
    if description:
        patch_body["description"] = description
    if location:
        patch_body["location"] = location
    if start_time:
        all_day = len(start_time) == 10 and "T" not in start_time
        if all_day:
            patch_body["start"] = {"date": start_time}
        else:
            patch_body["start"] = {"dateTime": start_time, "timeZone": timezone}
    if end_time:
        all_day_end = len(end_time) == 10 and "T" not in end_time
        if all_day_end:
            patch_body["end"] = {"date": end_time}
        else:
            patch_body["end"] = {"dateTime": end_time, "timeZone": timezone}

    if not patch_body:
        return {"error": "No fields provided to update.", "success": False}

    params: Dict[str, Any] = {}
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    _add_auth(params, headers, auth)

    endpoint = f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}"
    check_host(endpoint)

    async with httpx.AsyncClient() as client:
        resp = await client.patch(endpoint, params=params, headers=headers, json=patch_body, timeout=15)
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}: {resp.text}", "success": False}
        data = resp.json()

    event = _parse_event(data)
    return {
        "event": event,
        "success": True,
    }


@skill(
    name="calendar_delete_event",
    display_name="Delete Event",
    description="Delete an event from a Google Calendar (requires OAuth token).",
    category="calendar",
    tags=["calendar", "delete", "event", "google"],
    icon="calendar",
    risk_level=RiskLevel.MODERATE,
    group="Integrations",
    idempotent=False,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_COMMON_CONFIG,
)
async def calendar_delete_event(
    event_id: str,
    calendar_id: str = "primary",
) -> dict:
    """Delete an event from a Google Calendar."""
    auth = _get_auth()
    if auth is None:
        return {
            "error": "No Google Calendar credentials found. Set GOOGLE_CALENDAR_TOKEN or GOOGLE_CALENDAR_API_KEY.",
            "success": False,
        }
    if auth["type"] != "token":
        return {
            "error": "Deleting events requires an OAuth token (GOOGLE_CALENDAR_TOKEN). API key is read-only.",
            "success": False,
        }

    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    params: Dict[str, Any] = {}
    headers: Dict[str, str] = {}
    _add_auth(params, headers, auth)

    endpoint = f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}"
    check_host(endpoint)

    async with httpx.AsyncClient() as client:
        resp = await client.delete(endpoint, params=params, headers=headers, timeout=15)
        # DELETE returns 204 No Content on success
        if resp.status_code == 204 or resp.is_success:
            return {
                "event_id": event_id,
                "calendar_id": calendar_id,
                "deleted": True,
                "success": True,
            }
        return {"error": f"API returned status {resp.status_code}: {resp.text}", "success": False}


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class GoogleCalendarPlugin(TransformerPlugin):
    """Plugin providing Google Calendar skills and event formatting transformer."""

    def __init__(self):
        super().__init__("google_calendar")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_event": lambda _: FormatEventTransformer("format_event"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "calendar_events": calendar_events.__skill__,
            "calendar_event_details": calendar_event_details.__skill__,
            "calendar_create_event": calendar_create_event.__skill__,
            "calendar_update_event": calendar_update_event.__skill__,
            "calendar_delete_event": calendar_delete_event.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="google_calendar",
            display_name="Google Calendar",
            description="List, create, update, and delete Google Calendar events.",
            icon="calendar",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
