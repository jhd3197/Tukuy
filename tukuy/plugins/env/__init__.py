"""Env file manager plugin.

Skills-only plugin for reading, writing, and managing ``.env`` files
with masking support for sensitive values.

Pure stdlib — no external dependencies.
All skills declare ``requires_filesystem=True`` for SafetyPolicy enforcement.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_read_path, check_write_path
from ...skill import skill


def _parse_env_content(content: str) -> Dict[str, str]:
    """Parse .env file content into a key-value dict (skips comments)."""
    result = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Remove surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key] = value
    return result


def _mask_value(value: str, value_type: str = "api_key") -> str:
    """Mask a sensitive value, showing only the last 4 chars.

    For endpoint-type values (URLs), the full value is returned.
    """
    if value_type == "endpoint":
        return value
    if len(value) <= 4:
        return "****"
    return "*" * (len(value) - 4) + value[-4:]


@skill(
    name="env_read",
    description="Read and parse a .env file, returning all key-value pairs.",
    category="env",
    tags=["env", "config"],
    idempotent=True,
    requires_filesystem=True,
)
def env_read(path: str = ".env", mask: bool = False) -> dict:
    """Read a .env file and return its contents."""
    path = check_read_path(path)
    env_path = Path(path)
    if not env_path.exists():
        return {"path": str(env_path), "values": {}, "exists": False}

    content = env_path.read_text(encoding="utf-8")
    values = _parse_env_content(content)

    if mask:
        values = {
            k: _mask_value(v, "endpoint" if "endpoint" in k.lower() or "url" in k.lower() else "api_key")
            for k, v in values.items()
        }

    return {"path": str(env_path), "values": values, "exists": True, "count": len(values)}


@skill(
    name="env_write",
    description="Set a key=value in a .env file, preserving existing format.",
    category="env",
    tags=["env", "config"],
    side_effects=True,
    requires_filesystem=True,
)
def env_write(key: str, value: str, path: str = ".env") -> dict:
    """Set a key=value pair in a .env file."""
    path = check_write_path(path)
    env_path = Path(path)
    content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

    pattern = re.compile(rf"^#?\s*{re.escape(key)}\s*=.*$", re.MULTILINE)
    replacement = f"{key}={value}"

    if pattern.search(content):
        content = pattern.sub(replacement, content, count=1)
    else:
        if content and not content.endswith("\n"):
            content += "\n"
        content += f"{replacement}\n"

    env_path.write_text(content, encoding="utf-8")
    os.environ[key] = value

    return {"key": key, "path": str(env_path), "action": "set"}


@skill(
    name="env_remove",
    description="Comment out a key in a .env file and remove from os.environ.",
    category="env",
    tags=["env", "config"],
    side_effects=True,
    requires_filesystem=True,
)
def env_remove(key: str, path: str = ".env") -> dict:
    """Comment out a key in a .env file and remove from environment."""
    path = check_write_path(path)
    env_path = Path(path)
    if not env_path.exists():
        return {"key": key, "path": str(env_path), "action": "not_found"}

    content = env_path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^{re.escape(key)}\s*=.*$", re.MULTILINE)
    new_content = pattern.sub(f"# {key}=", content)
    env_path.write_text(new_content, encoding="utf-8")
    os.environ.pop(key, None)

    return {"key": key, "path": str(env_path), "action": "removed"}


@skill(
    name="env_list",
    description="List all keys in a .env file (values masked by default).",
    category="env",
    tags=["env", "config"],
    idempotent=True,
    requires_filesystem=True,
)
def env_list(path: str = ".env") -> dict:
    """List all keys defined in a .env file with masked values."""
    path = check_read_path(path)
    env_path = Path(path)
    if not env_path.exists():
        return {"path": str(env_path), "keys": [], "exists": False}

    content = env_path.read_text(encoding="utf-8")
    values = _parse_env_content(content)

    keys = []
    for k, v in values.items():
        value_type = "endpoint" if "endpoint" in k.lower() or "url" in k.lower() else "api_key"
        keys.append({
            "key": k,
            "masked_value": _mask_value(v, value_type),
            "type": value_type,
        })

    return {"path": str(env_path), "keys": keys, "count": len(keys), "exists": True}


class EnvPlugin(TransformerPlugin):
    """Plugin providing .env file management skills (no transformers)."""

    def __init__(self):
        super().__init__("env")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "env_read": env_read.__skill__,
            "env_write": env_write.__skill__,
            "env_remove": env_remove.__skill__,
            "env_list": env_list.__skill__,
        }
