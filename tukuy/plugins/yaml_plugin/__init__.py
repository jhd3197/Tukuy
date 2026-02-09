"""YAML plugin.

Skills-only plugin providing YAML read, write, to-JSON conversion,
and validation operations.

Requires ``pyyaml`` — fails gracefully with a clear error message.
All skills declare ``requires_filesystem=True`` for SafetyPolicy enforcement.
"""

import json
import os
from typing import Any, Dict

from ...plugins.base import TransformerPlugin
from ...safety import check_read_path, check_write_path
from ...skill import skill, RiskLevel

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    _YAML_AVAILABLE = False


def _require_yaml():
    """Raise a clear error when pyyaml is not installed."""
    if not _YAML_AVAILABLE:
        raise RuntimeError(
            "The 'pyyaml' package is required for YAML skills. "
            "Install it with: pip install pyyaml"
        )


@skill(
    name="yaml_read",
    description="Read and parse a YAML file.",
    category="data",
    tags=["yaml", "read", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="Read YAML",
    icon="file-code",
    risk_level=RiskLevel.SAFE,
    group="YAML Operations",
)
def yaml_read(path: str) -> dict:
    """Read a YAML file and return parsed data."""
    _require_yaml()
    path = check_read_path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {"path": path, "data": data}


@skill(
    name="yaml_write",
    description="Write data as a YAML file.",
    category="data",
    tags=["yaml", "write", "data"],
    side_effects=True,
    requires_filesystem=True,
    display_name="Write YAML",
    icon="file-code",
    risk_level=RiskLevel.MODERATE,
    group="YAML Operations",
)
def yaml_write(path: str, data: Any = None) -> dict:
    """Write data to a YAML file."""
    _require_yaml()
    path = check_write_path(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    content = yaml.dump(data, default_flow_style=False, allow_unicode=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"path": path, "bytes_written": len(content.encode("utf-8"))}


@skill(
    name="yaml_to_json",
    description="Convert a YAML file to JSON.",
    category="data",
    tags=["yaml", "json", "convert", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="YAML to JSON",
    icon="file-code",
    risk_level=RiskLevel.SAFE,
    group="YAML Operations",
)
def yaml_to_json(path: str, output_path: str = None) -> dict:
    """Read a YAML file and return JSON representation."""
    _require_yaml()
    path = check_read_path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    json_string = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path is not None:
        output_path = check_write_path(output_path)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_string)
    return {"data": data, "json_string": json_string}


@skill(
    name="yaml_validate",
    description="Check if a file contains valid YAML.",
    category="data",
    tags=["yaml", "validate", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="Validate YAML",
    icon="file-check",
    risk_level=RiskLevel.SAFE,
    group="YAML Operations",
)
def yaml_validate(path: str) -> dict:
    """Validate whether a file is well-formed YAML."""
    _require_yaml()
    path = check_read_path(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            yaml.safe_load(f)
        return {"valid": True, "error": None, "path": path}
    except yaml.YAMLError as exc:
        return {"valid": False, "error": str(exc), "path": path}


class YamlPlugin(TransformerPlugin):
    """Plugin providing YAML file operation skills (no transformers)."""

    def __init__(self):
        super().__init__("yaml")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "yaml_read": yaml_read.__skill__,
            "yaml_write": yaml_write.__skill__,
            "yaml_to_json": yaml_to_json.__skill__,
            "yaml_validate": yaml_validate.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="yaml",
            display_name="YAML",
            description="Read, write, convert, and validate YAML files.",
            icon="file-code",
            color="#cb3837",
            group="Data",
            requires=PluginRequirements(filesystem=True, imports=["yaml"]),
        )
