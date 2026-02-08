"""Plugin manifest system for Tukuy — declarative plugin metadata for discovery and UI.

Plugins declare a :class:`PluginManifest` that tells consumers what the plugin
is, what it needs, and how to display it.  This replaces manual
capability→plugin mappings in consumers like CachiBot.

Usage::

    from tukuy.manifest import PluginManifest, PluginRequirements

    manifest = PluginManifest(
        name="file_ops",
        display_name="File Operations",
        description="Read, write, edit, and list files in the workspace.",
        icon="folder",
        color="#3b82f6",
        group="Core",
        requires=PluginRequirements(filesystem=True),
    )
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PluginRequirements:
    """What a plugin needs from the environment to function."""

    filesystem: bool = False
    network: bool = False
    imports: List[str] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)  # Other plugins this depends on
    min_python: Optional[str] = None  # e.g. "3.10"
    platforms: Optional[List[str]] = None  # ["linux", "darwin", "win32"], None = all

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.filesystem:
            d["filesystem"] = True
        if self.network:
            d["network"] = True
        if self.imports:
            d["imports"] = self.imports
        if self.plugins:
            d["plugins"] = self.plugins
        if self.min_python is not None:
            d["minPython"] = self.min_python
        if self.platforms is not None:
            d["platforms"] = self.platforms
        return d


@dataclass
class PluginManifest:
    """Declarative metadata about a plugin for discovery and UI.

    Every :class:`~tukuy.plugins.base.TransformerPlugin` exposes a ``manifest``
    property.  The base class auto-generates one from the plugin ``name``;
    subclasses can override to provide richer metadata.
    """

    # Identity
    name: str
    display_name: str = ""
    description: str = ""
    version: str = "0.1.0"
    author: Optional[str] = None

    # UI hints
    icon: Optional[str] = None  # Lucide icon name
    color: Optional[str] = None  # Hex color string
    group: Optional[str] = None  # "Core" | "Integrations" | "Data"

    # Requirements
    requires: PluginRequirements = field(default_factory=PluginRequirements)

    # Feature flags
    experimental: bool = False
    deprecated: Optional[str] = None  # Deprecation message

    def __post_init__(self) -> None:
        if not self.display_name:
            self.display_name = self.name.replace("_", " ").title()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict suitable for JSON APIs."""
        d: Dict[str, Any] = {
            "name": self.name,
            "displayName": self.display_name,
            "description": self.description,
            "version": self.version,
        }
        if self.author is not None:
            d["author"] = self.author
        if self.icon is not None:
            d["icon"] = self.icon
        if self.color is not None:
            d["color"] = self.color
        if self.group is not None:
            d["group"] = self.group
        requires_dict = self.requires.to_dict()
        if requires_dict:
            d["requires"] = requires_dict
        if self.experimental:
            d["experimental"] = True
        if self.deprecated is not None:
            d["deprecated"] = self.deprecated
        return d


__all__ = [
    "PluginRequirements",
    "PluginManifest",
]
