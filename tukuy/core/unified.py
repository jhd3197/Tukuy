"""Unified plugin and transformer discovery system for Tukuy.

This module provides a centralized registry that can discover transformers
from both the plugins/ and transformers/ directories, bridging the gap
between the different organizational approaches.
"""

import importlib
import inspect
import os
import sys
from typing import Dict, List, Optional, Any, Callable, Set, Union
from logging import getLogger

from .registration import get_registration_manager, tukuy_plugin
from .introspection import TransformerMetadata, TransformerIntrospector
from .usage import get_usage_tracker
from ..plugins.base import TransformerPlugin, PluginRegistry
from ..base import ChainableTransformer

logger = getLogger(__name__)


class UnifiedRegistry:
    """Unified registry that bridges plugins and transformers from different sources."""

    def __init__(self):
        self.registry = PluginRegistry()
        self.introspector = TransformerIntrospector(self.registry)
        self.registration_manager = get_registration_manager()
        self.discovered_plugins: Dict[str, TransformerPlugin] = {}
        self.transformer_to_plugin_map: Dict[str, str] = {}
        self.metadata_cache: Dict[str, TransformerMetadata] = {}

    def discover_plugins(self) -> None:
        """Discover plugins from both the plugins/ and transformers/ directories."""
        self._load_builtin_plugins()
        self._register_all_discovered_plugins()

    def _load_builtin_plugins(self) -> None:
        """Load built-in plugins from the plugins/ directory structure."""
        try:
            from ..plugins import BUILTIN_PLUGINS

            for plugin_name, plugin_class in BUILTIN_PLUGINS.items():
                try:
                    plugin_instance = plugin_class()
                    self.discovered_plugins[plugin_name] = plugin_instance
                    logger.info(f"Discovered built-in plugin: {plugin_name}")

                    # Map each transformer to its plugin
                    for transformer_name in plugin_instance.transformers.keys():
                        self.transformer_to_plugin_map[transformer_name] = plugin_name

                except Exception as e:
                    logger.warning(f"Failed to load built-in plugin {plugin_name}: {e}")

        except ImportError as e:
            logger.warning(f"Could not import BUILTIN_PLUGINS: {e}")

    def _register_all_discovered_plugins(self) -> None:
        """Register all discovered plugins with the main registry."""
        for plugin_name, plugin in self.discovered_plugins.items():
            try:
                self.registry.register(plugin)
                logger.info(f"Registered plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Failed to register plugin {plugin_name}: {e}")

    def get_transformer_plugin(self, transformer_name: str) -> Optional[str]:
        """Get the plugin name that provides a specific transformer."""
        return self.transformer_to_plugin_map.get(transformer_name)

    def get_all_transformers(self) -> List[str]:
        """Get a list of all available transformer names."""
        return list(self.registry.transformers.keys())

    def get_transformers_by_plugin(self, plugin_name: Optional[str] = None) -> Dict[str, List[str]]:
        """Get transformers organized by plugin.

        Args:
            plugin_name: If provided, return only transformers from this plugin.
                        If None, return all transformers organized by plugin.

        Returns:
            Dictionary mapping plugin names to lists of transformer names
        """
        if plugin_name:
            plugin = self.discovered_plugins.get(plugin_name)
            if plugin:
                return {plugin_name: list(plugin.transformers.keys())}
            return {}

        result = {}
        for name, plugin in self.discovered_plugins.items():
            result[name] = list(plugin.transformers.keys())

        return result

    def get_transformer_metadata(self, transformer_name: str) -> Optional[TransformerMetadata]:
        """Get metadata for a specific transformer."""
        if transformer_name in self.metadata_cache:
            return self.metadata_cache[transformer_name]

        # Find which plugin provides this transformer
        plugin_name = self.get_transformer_plugin(transformer_name)
        if not plugin_name:
            return None

        plugin = self.discovered_plugins.get(plugin_name)
        if not plugin:
            return None

        # Try to extract metadata using introspection
        try:
            factory_func = plugin.transformers.get(transformer_name)
            if factory_func:
                metadata = self.introspector.get_transformer_metadata(
                    transformer_name, plugin, factory_func
                )
                self.metadata_cache[transformer_name] = metadata
                return metadata
        except Exception as e:
            logger.warning(f"Could not extract metadata for {transformer_name}: {e}")

        return None

    def get_all_metadata(self) -> List[TransformerMetadata]:
        """Get metadata for all available transformers."""
        all_metadata = []

        for transformer_name in self.get_all_transformers():
            metadata = self.get_transformer_metadata(transformer_name)
            if metadata:
                all_metadata.append(metadata)

        return all_metadata

    # ------------------------------------------------------------------
    # Two-phase discovery helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _truncate_description(text: str, max_len: int = 80) -> str:
        """Return first sentence or first *max_len* chars of *text*."""
        if not text:
            return ""
        # First sentence heuristic: split on ". " or standalone "."
        dot_pos = text.find(". ")
        if dot_pos == -1:
            dot_pos = text.find(".\n")
        if 0 < dot_pos < max_len:
            return text[: dot_pos + 1]
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def browse(self) -> Dict[str, Any]:
        """Phase 1: compact index grouped by plugin, with popular tools."""
        tracker = get_usage_tracker()
        plugins_index: Dict[str, Any] = {}
        total = 0

        for plugin_name, plugin in self.discovered_plugins.items():
            tools_map: Dict[str, str] = {}
            for t_name in plugin.transformers:
                metadata = self.get_transformer_metadata(t_name)
                desc = metadata.description if metadata else "No description available"
                tools_map[t_name] = self._truncate_description(desc)
                total += 1
            plugins_index[plugin_name] = {
                "tool_count": len(tools_map),
                "tools": tools_map,
            }

        return {
            "total_count": total,
            "popular": tracker.get_popular(5),
            "plugins": plugins_index,
        }

    def get_details(self, *names: str) -> List[Dict[str, Any]]:
        """Phase 2: full metadata for specific tools by name.

        Also records a usage tick for each requested tool.
        """
        tracker = get_usage_tracker()
        results: List[Dict[str, Any]] = []

        for name in names:
            plugin_name = self.get_transformer_plugin(name)
            metadata = self.get_transformer_metadata(name)
            if metadata is None:
                continue

            tracker.record(name)

            tool_info: Dict[str, Any] = {
                "name": name,
                "plugin": plugin_name or "unknown",
                "description": metadata.description,
                "category": (
                    metadata.category.value
                    if hasattr(metadata.category, "value")
                    else str(metadata.category)
                ),
                "version": metadata.version,
                "status": metadata.status,
                "input_type": metadata.input_type,
                "output_type": metadata.output_type,
                "examples": metadata.examples,
                "tags": sorted(metadata.tags) if metadata.tags else [],
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.param_type,
                        "required": p.required,
                        "description": p.description,
                        "default": p.default_value,
                    }
                    for p in metadata.parameters
                ],
            }
            results.append(tool_info)

        return results

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Keyword search across names, tags, descriptions, categories.

        Scoring:
            - Exact name match: 10
            - Name contains query word: 5
            - Tag match: 3
            - Category match: 3
            - Plugin name match: 2
            - Description contains query word: 1

        Usage count is the tiebreaker (higher = first).
        """
        tracker = get_usage_tracker()
        query_words = query.lower().split()
        if not query_words:
            return []

        scored: List[tuple] = []  # (score, usage, name, plugin, description)

        for t_name in self.get_all_transformers():
            metadata = self.get_transformer_metadata(t_name)
            if metadata is None:
                continue

            score = 0
            name_lower = t_name.lower()
            tags_lower = {t.lower() for t in (metadata.tags or set())}
            category_lower = (
                metadata.category.value.lower()
                if hasattr(metadata.category, "value")
                else str(metadata.category).lower()
            )
            plugin_lower = (metadata.plugin or "").lower()
            desc_lower = (metadata.description or "").lower()

            for word in query_words:
                if word == name_lower:
                    score += 10
                elif word in name_lower:
                    score += 5
                if word in tags_lower:
                    score += 3
                if word in category_lower:
                    score += 3
                if word in plugin_lower:
                    score += 2
                if word in desc_lower:
                    score += 1

            if score > 0:
                usage = tracker.get_count(t_name)
                scored.append((score, usage, t_name, metadata.plugin, metadata.description))

        # Sort by score desc, then usage desc
        scored.sort(key=lambda x: (-x[0], -x[1]))

        results: List[Dict[str, Any]] = []
        for score, _usage, name, plugin, desc in scored[:limit]:
            results.append({
                "name": name,
                "plugin": plugin,
                "description": self._truncate_description(desc),
                "score": score,
            })
        return results


# Global singleton instance
_unified_registry: Optional[UnifiedRegistry] = None


def get_unified_registry() -> UnifiedRegistry:
    """Get the global unified registry instance."""
    global _unified_registry
    if _unified_registry is None:
        _unified_registry = UnifiedRegistry()
        _unified_registry.discover_plugins()
    return _unified_registry


def list_all_tools() -> List[Dict[str, Any]]:
    """Get a complete list of all available transformers with their metadata.

    This function provides a unified view of all transformers available in the system,
    including which plugin provides each transformer and usage examples.

    Returns:
        List of dictionaries with transformer information:
        [
            {
                "name": "transformer_name",
                "plugin": "plugin_name",
                "description": "description text",
                "category": "category_enum_value",
                "examples": ["example1", "example2"],
                ...
            },
            ...
        ]
    """
    registry = get_unified_registry()
    all_tools = []

    for transformer_name in registry.get_all_transformers():
        plugin_name = registry.get_transformer_plugin(transformer_name)
        metadata = registry.get_transformer_metadata(transformer_name)

        tool_info = {
            "name": transformer_name,
            "plugin": plugin_name or "unknown",
            "description": "No description available",
            "category": "unknown",
            "examples": [],
            "parameters": []
        }

        if metadata:
            tool_info.update({
                "description": metadata.description,
                "category": metadata.category.value if hasattr(metadata.category, 'value') else str(metadata.category),
                "version": metadata.version,
                "status": metadata.status,
                "input_type": metadata.input_type,
                "output_type": metadata.output_type,
                "examples": metadata.examples,
                "tags": list(metadata.tags) if metadata.tags else [],
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.param_type,
                        "required": param.required,
                        "description": param.description,
                        "default": param.default_value
                    } for param in metadata.parameters
                ]
            })

        all_tools.append(tool_info)

    # Sort by plugin name, then transformer name
    all_tools.sort(key=lambda x: (x["plugin"], x["name"]))

    return all_tools


def browse_tools() -> Dict[str, Any]:
    """Phase 1 discovery – compact index grouped by plugin with popular tools."""
    return get_unified_registry().browse()


def get_tool_details(*names: str) -> List[Dict[str, Any]]:
    """Phase 2 discovery – full metadata for the requested tool names."""
    return get_unified_registry().get_details(*names)


def search_tools(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Keyword search across tool names, tags, descriptions, and categories."""
    return get_unified_registry().search(query, limit)