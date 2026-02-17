"""Spotify plugin.

Provides async skills for searching music, getting track/artist/album
details, recommendations, and new releases via the Spotify Web API
(Client Credentials flow).

Requires ``httpx`` (optional dependency, imported lazily at call time).
"""

import base64
import os
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_host
from ...skill import skill, ConfigParam, RiskLevel

_BASE_URL = "https://api.spotify.com/v1"
_TOKEN_URL = "https://accounts.spotify.com/api/token"


# ── Helpers ───────────────────────────────────────────────────────────────


def _get_credentials() -> tuple:
    """Read Spotify client credentials from the environment.

    Returns:
        Tuple of (client_id, client_secret) from env vars.
    """
    return (
        os.environ.get("SPOTIFY_CLIENT_ID", ""),
        os.environ.get("SPOTIFY_CLIENT_SECRET", ""),
    )


async def _get_token(client) -> str:
    """Fetch a Bearer access token using Client Credentials flow.

    Args:
        client: An ``httpx.AsyncClient`` instance.

    Returns:
        The access token string.

    Raises:
        RuntimeError: If the token request fails.
    """
    client_id, client_secret = _get_credentials()
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    check_host(_TOKEN_URL)
    resp = await client.post(
        _TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    if not resp.is_success:
        raise RuntimeError(f"Spotify token request failed with status {resp.status_code}")
    return resp.json()["access_token"]


def _fmt_duration(ms: int) -> str:
    """Format milliseconds as ``"M:SS"``."""
    if not isinstance(ms, (int, float)) or ms < 0:
        return "0:00"
    total_seconds = int(ms) // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def _parse_track(raw: dict) -> dict:
    """Normalise a Spotify track object."""
    artists = [a.get("name", "") for a in (raw.get("artists") or [])]
    album = raw.get("album") or {}
    images = album.get("images") or []
    return {
        "name": raw.get("name", ""),
        "artists": artists,
        "album": album.get("name", ""),
        "album_image": images[0]["url"] if images else "",
        "duration_ms": raw.get("duration_ms", 0),
        "duration_formatted": _fmt_duration(raw.get("duration_ms", 0)),
        "explicit": raw.get("explicit", False),
        "popularity": raw.get("popularity", 0),
        "preview_url": raw.get("preview_url") or "",
        "spotify_url": (raw.get("external_urls") or {}).get("spotify", ""),
        "uri": raw.get("uri", ""),
        "release_date": album.get("release_date", ""),
    }


def _parse_artist(raw: dict) -> dict:
    """Normalise a Spotify artist object."""
    images = raw.get("images") or []
    followers = raw.get("followers") or {}
    return {
        "name": raw.get("name", ""),
        "genres": raw.get("genres") or [],
        "popularity": raw.get("popularity", 0),
        "followers": followers.get("total", 0),
        "image": images[0]["url"] if images else "",
        "spotify_url": (raw.get("external_urls") or {}).get("spotify", ""),
        "uri": raw.get("uri", ""),
    }


def _parse_album(raw: dict) -> dict:
    """Normalise a Spotify album object."""
    artists = [a.get("name", "") for a in (raw.get("artists") or [])]
    images = raw.get("images") or []
    return {
        "name": raw.get("name", ""),
        "artists": artists,
        "release_date": raw.get("release_date", ""),
        "total_tracks": raw.get("total_tracks", 0),
        "album_type": raw.get("album_type", ""),
        "image": images[0]["url"] if images else "",
        "spotify_url": (raw.get("external_urls") or {}).get("spotify", ""),
        "uri": raw.get("uri", ""),
    }


# ── Transformer ───────────────────────────────────────────────────────────


class FormatTrackTransformer(ChainableTransformer[dict, str]):
    """Format a parsed track dict into a human-readable string.

    Output format: ``"Artist1, Artist2 — Track Name (Album) [3:45]"``
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "name" in value

    def _transform(self, value: dict, context: Optional[TransformContext] = None) -> str:
        artists = ", ".join(value.get("artists") or [])
        name = value.get("name", "")
        album = value.get("album", "")
        duration = value.get("duration_formatted", "")
        parts = []
        if artists:
            parts.append(f"{artists} \u2014 {name}")
        else:
            parts.append(name)
        if album:
            parts.append(f"({album})")
        if duration:
            parts.append(f"[{duration}]")
        return " ".join(parts)


# ── Shared skill config params ────────────────────────────────────────────

_SPOTIFY_CONFIG_PARAMS = [
    ConfigParam(
        name="client_id",
        display_name="Spotify Client ID",
        description="Spotify application client ID. Falls back to SPOTIFY_CLIENT_ID env var.",
        type="secret",
        placeholder="your-spotify-client-id",
    ),
    ConfigParam(
        name="client_secret",
        display_name="Spotify Client Secret",
        description="Spotify application client secret. Falls back to SPOTIFY_CLIENT_SECRET env var.",
        type="secret",
        placeholder="your-spotify-client-secret",
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


# ── Skills ────────────────────────────────────────────────────────────────


@skill(
    name="spotify_search",
    display_name="Spotify Search",
    description="Search for tracks, artists, albums, or playlists on Spotify.",
    category="music",
    tags=["spotify", "music", "search", "tracks", "artists", "albums"],
    icon="music",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_SPOTIFY_CONFIG_PARAMS,
)
async def spotify_search(
    query: str,
    search_type: str = "track",
    limit: int = 10,
) -> dict:
    """Search Spotify for tracks, artists, albums, or playlists."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    client_id, client_secret = _get_credentials()
    if not client_id or not client_secret:
        return {
            "error": "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars are required.",
            "success": False,
        }

    check_host(_BASE_URL)
    async with httpx.AsyncClient() as client:
        try:
            token = await _get_token(client)
        except RuntimeError as exc:
            return {"error": str(exc), "success": False}

        endpoint = f"{_BASE_URL}/search"
        resp = await client.get(
            endpoint,
            params={"q": query, "type": search_type, "limit": limit},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}

        data = resp.json()
        key = f"{search_type}s"
        items = (data.get(key) or {}).get("items") or []

        parsers = {
            "track": _parse_track,
            "artist": _parse_artist,
            "album": _parse_album,
        }
        parser = parsers.get(search_type)
        if parser:
            results = [parser(item) for item in items]
        else:
            # playlists and other types returned as-is
            results = items

        return {
            "query": query,
            "type": search_type,
            "results": results,
            "count": len(results),
            "success": True,
        }


@skill(
    name="spotify_track",
    display_name="Spotify Track Details",
    description="Get detailed information about a Spotify track by its ID.",
    category="music",
    tags=["spotify", "music", "track", "details"],
    icon="music",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_SPOTIFY_CONFIG_PARAMS,
)
async def spotify_track(track_id: str) -> dict:
    """Get track details by Spotify track ID."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    client_id, client_secret = _get_credentials()
    if not client_id or not client_secret:
        return {
            "error": "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars are required.",
            "success": False,
        }

    check_host(_BASE_URL)
    async with httpx.AsyncClient() as client:
        try:
            token = await _get_token(client)
        except RuntimeError as exc:
            return {"error": str(exc), "success": False}

        endpoint = f"{_BASE_URL}/tracks/{track_id}"
        resp = await client.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}

        data = resp.json()
        track = _parse_track(data)
        track["success"] = True
        return track


@skill(
    name="spotify_artist",
    display_name="Spotify Artist Details",
    description="Get detailed information about a Spotify artist by their ID.",
    category="music",
    tags=["spotify", "music", "artist", "details"],
    icon="music",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_SPOTIFY_CONFIG_PARAMS,
)
async def spotify_artist(artist_id: str) -> dict:
    """Get artist details by Spotify artist ID."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    client_id, client_secret = _get_credentials()
    if not client_id or not client_secret:
        return {
            "error": "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars are required.",
            "success": False,
        }

    check_host(_BASE_URL)
    async with httpx.AsyncClient() as client:
        try:
            token = await _get_token(client)
        except RuntimeError as exc:
            return {"error": str(exc), "success": False}

        endpoint = f"{_BASE_URL}/artists/{artist_id}"
        resp = await client.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}

        data = resp.json()
        artist = _parse_artist(data)
        artist["success"] = True
        return artist


@skill(
    name="spotify_artist_top_tracks",
    display_name="Spotify Artist Top Tracks",
    description="Get an artist's top tracks on Spotify.",
    category="music",
    tags=["spotify", "music", "artist", "top", "tracks"],
    icon="music",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_SPOTIFY_CONFIG_PARAMS,
)
async def spotify_artist_top_tracks(artist_id: str, market: str = "US") -> dict:
    """Get an artist's top tracks."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    client_id, client_secret = _get_credentials()
    if not client_id or not client_secret:
        return {
            "error": "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars are required.",
            "success": False,
        }

    check_host(_BASE_URL)
    async with httpx.AsyncClient() as client:
        try:
            token = await _get_token(client)
        except RuntimeError as exc:
            return {"error": str(exc), "success": False}

        endpoint = f"{_BASE_URL}/artists/{artist_id}/top-tracks"
        resp = await client.get(
            endpoint,
            params={"market": market},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}

        data = resp.json()
        tracks = [_parse_track(t) for t in (data.get("tracks") or [])]
        return {
            "artist_id": artist_id,
            "market": market,
            "tracks": tracks,
            "count": len(tracks),
            "success": True,
        }


@skill(
    name="spotify_recommendations",
    display_name="Spotify Recommendations",
    description="Get track recommendations based on seed tracks, artists, or genres.",
    category="music",
    tags=["spotify", "music", "recommendations", "discover"],
    icon="music",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_SPOTIFY_CONFIG_PARAMS,
)
async def spotify_recommendations(
    seed_tracks: str = "",
    seed_artists: str = "",
    seed_genres: str = "",
    limit: int = 20,
) -> dict:
    """Get track recommendations based on seed tracks, artists, or genres."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    if not seed_tracks and not seed_artists and not seed_genres:
        return {
            "error": "At least one seed is required (seed_tracks, seed_artists, or seed_genres).",
            "success": False,
        }

    client_id, client_secret = _get_credentials()
    if not client_id or not client_secret:
        return {
            "error": "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars are required.",
            "success": False,
        }

    check_host(_BASE_URL)
    async with httpx.AsyncClient() as client:
        try:
            token = await _get_token(client)
        except RuntimeError as exc:
            return {"error": str(exc), "success": False}

        params: Dict[str, Any] = {"limit": limit}
        if seed_tracks:
            params["seed_tracks"] = seed_tracks
        if seed_artists:
            params["seed_artists"] = seed_artists
        if seed_genres:
            params["seed_genres"] = seed_genres

        endpoint = f"{_BASE_URL}/recommendations"
        resp = await client.get(
            endpoint,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}

        data = resp.json()
        tracks = [_parse_track(t) for t in (data.get("tracks") or [])]
        return {
            "tracks": tracks,
            "count": len(tracks),
            "seeds": {
                "tracks": seed_tracks,
                "artists": seed_artists,
                "genres": seed_genres,
            },
            "success": True,
        }


@skill(
    name="spotify_new_releases",
    display_name="Spotify New Releases",
    description="Get new album releases on Spotify.",
    category="music",
    tags=["spotify", "music", "new", "releases", "albums"],
    icon="music",
    risk_level=RiskLevel.SAFE,
    group="Integrations",
    idempotent=True,
    requires_network=True,
    required_imports=["httpx"],
    config_params=_SPOTIFY_CONFIG_PARAMS,
)
async def spotify_new_releases(country: str = "US", limit: int = 20) -> dict:
    """Get new album releases."""
    try:
        import httpx
    except ImportError:
        return {"error": "httpx is required. Install with: pip install httpx", "success": False}

    client_id, client_secret = _get_credentials()
    if not client_id or not client_secret:
        return {
            "error": "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars are required.",
            "success": False,
        }

    check_host(_BASE_URL)
    async with httpx.AsyncClient() as client:
        try:
            token = await _get_token(client)
        except RuntimeError as exc:
            return {"error": str(exc), "success": False}

        endpoint = f"{_BASE_URL}/browse/new-releases"
        resp = await client.get(
            endpoint,
            params={"country": country, "limit": limit},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if not resp.is_success:
            return {"error": f"API returned status {resp.status_code}", "success": False}

        data = resp.json()
        items = (data.get("albums") or {}).get("items") or []
        albums = [_parse_album(a) for a in items]
        return {
            "country": country,
            "albums": albums,
            "count": len(albums),
            "success": True,
        }


# ── Plugin class ──────────────────────────────────────────────────────────


class SpotifyPlugin(TransformerPlugin):
    """Plugin providing Spotify music skills and track formatting transformer."""

    def __init__(self):
        super().__init__("spotify")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "format_track": lambda _: FormatTrackTransformer("format_track"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "spotify_search": spotify_search.__skill__,
            "spotify_track": spotify_track.__skill__,
            "spotify_artist": spotify_artist.__skill__,
            "spotify_artist_top_tracks": spotify_artist_top_tracks.__skill__,
            "spotify_recommendations": spotify_recommendations.__skill__,
            "spotify_new_releases": spotify_new_releases.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="spotify",
            display_name="Spotify",
            description="Search music, get recommendations, and browse new releases via Spotify API.",
            icon="music",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
