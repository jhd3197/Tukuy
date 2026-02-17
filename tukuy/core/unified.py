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

from .introspection import TransformerMetadata, TransformerIntrospector
from .usage import get_usage_tracker
from ..plugins.base import TransformerPlugin, PluginRegistry, PluginSource
from ..registry import get_shared_registry

logger = getLogger(__name__)


class UnifiedRegistry:
    """Unified registry that bridges plugins and transformers from different sources."""

    def __init__(self):
        self.registry = get_shared_registry()
        self.introspector = TransformerIntrospector(self.registry)
        self.discovered_plugins: Dict[str, TransformerPlugin] = {}
        self.transformer_to_plugin_map: Dict[str, str] = {}
        self.metadata_cache: Dict[str, TransformerMetadata] = {}

    def discover_plugins(self) -> None:
        """Index plugins already loaded in the shared registry."""
        self._index_registered_plugins()

    def _index_registered_plugins(self) -> None:
        """Build the discovered_plugins and transformer_to_plugin_map from the shared registry."""
        for plugin_name, plugin in self.registry.plugins.items():
            self.discovered_plugins[plugin_name] = plugin
            for transformer_name in plugin.transformers.keys():
                self.transformer_to_plugin_map[transformer_name] = plugin_name

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
        """Phase 1: compact index grouped by plugin, with popular tools.

        Includes transformers, skills, and instructions from all plugins.
        """
        tracker = get_usage_tracker()
        plugins_index: Dict[str, Any] = {}
        total = 0

        for plugin_name, plugin in self.discovered_plugins.items():
            tools_map: Dict[str, str] = {}

            # Transformers
            for t_name in plugin.transformers:
                metadata = self.get_transformer_metadata(t_name)
                desc = metadata.description if metadata else "No description available"
                tools_map[t_name] = self._truncate_description(desc)

            # Skills (excluding instructions which are added below)
            instruction_names = set()
            try:
                instruction_names = set(plugin.instructions.keys())
            except Exception:
                pass
            try:
                for s_name, skill_obj in plugin.skills.items():
                    if s_name not in tools_map and s_name not in instruction_names:
                        desc = skill_obj.descriptor.description if skill_obj.descriptor else ""
                        tools_map[s_name] = self._truncate_description(desc)
            except Exception:
                pass

            # Instructions
            try:
                for i_name, instr_obj in plugin.instructions.items():
                    if i_name not in tools_map:
                        desc = instr_obj.descriptor.description if instr_obj.descriptor else ""
                        tools_map[i_name] = self._truncate_description(desc)
            except Exception:
                pass

            total += len(tools_map)

            # Determine plugin source
            plugin_obj = self.registry.get_plugin(plugin_name)
            source = plugin_obj.source.value if plugin_obj and hasattr(plugin_obj, "source") else "unknown"
            plugins_index[plugin_name] = {
                "tool_count": len(tools_map),
                "tools": tools_map,
                "source": source,
            }

        return {
            "total_count": total,
            "popular": tracker.get_popular(5),
            "plugins": plugins_index,
        }

    def _find_skill_or_instruction(self, name: str):
        """Find a skill or instruction by name and return (descriptor, plugin_name, kind)."""
        # Check skills first (instructions are dual-registered here too)
        skill_obj = self.registry.skills.get(name)
        if skill_obj and hasattr(skill_obj, "descriptor"):
            # Determine plugin name
            for pname, plugin in self.discovered_plugins.items():
                try:
                    if name in plugin.instructions:
                        return skill_obj.descriptor, pname, "instruction"
                except Exception:
                    pass
                try:
                    if name in plugin.skills:
                        return skill_obj.descriptor, pname, "skill"
                except Exception:
                    pass
            return skill_obj.descriptor, "unknown", "skill"
        return None, None, None

    def get_details(self, *names: str) -> List[Dict[str, Any]]:
        """Phase 2: full metadata for specific tools by name.

        Searches transformers, skills, and instructions. Also records a
        usage tick for each requested tool.
        """
        tracker = get_usage_tracker()
        results: List[Dict[str, Any]] = []

        for name in names:
            # Try transformer first
            plugin_name = self.get_transformer_plugin(name)
            metadata = self.get_transformer_metadata(name)
            if metadata is not None:
                tracker.record(name)
                plugin_obj = self.registry.get_plugin(plugin_name) if plugin_name else None
                source = plugin_obj.source.value if plugin_obj and hasattr(plugin_obj, "source") else "unknown"
                tool_info: Dict[str, Any] = {
                    "name": name,
                    "kind": "transformer",
                    "plugin": plugin_name or "unknown",
                    "source": source,
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
                continue

            # Try skill / instruction
            descriptor, pname, kind = self._find_skill_or_instruction(name)
            if descriptor is not None:
                tracker.record(name)
                plugin_obj = self.registry.get_plugin(pname) if pname else None
                source = plugin_obj.source.value if plugin_obj and hasattr(plugin_obj, "source") else "unknown"
                tool_info = {
                    "name": name,
                    "kind": kind,
                    "plugin": pname or "unknown",
                    "source": source,
                    "description": descriptor.description,
                    "category": descriptor.category,
                    "version": descriptor.version,
                    "tags": sorted(descriptor.tags) if descriptor.tags else [],
                    "group": descriptor.group,
                    "icon": descriptor.icon,
                }
                results.append(tool_info)

        return results

    @staticmethod
    def _score_against_query(
        query_words: List[str],
        name: str,
        tags: set,
        category: str,
        plugin: str,
        description: str,
    ) -> int:
        """Compute relevance score for a single item against query words."""
        score = 0
        name_lower = name.lower()
        tags_lower = {t.lower() for t in tags}
        category_lower = category.lower()
        plugin_lower = plugin.lower()
        desc_lower = description.lower()

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

        return score

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Keyword search across transformers, skills, and instructions.

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

        # (score, usage, kind, name, plugin, description)
        scored: List[tuple] = []
        seen_names: Set[str] = set()

        # --- Transformers ---
        for t_name in self.get_all_transformers():
            metadata = self.get_transformer_metadata(t_name)
            if metadata is None:
                continue

            score = self._score_against_query(
                query_words,
                t_name,
                metadata.tags or set(),
                (
                    metadata.category.value
                    if hasattr(metadata.category, "value")
                    else str(metadata.category)
                ),
                metadata.plugin or "",
                metadata.description or "",
            )
            if score > 0:
                usage = tracker.get_count(t_name)
                scored.append((score, usage, "transformer", t_name, metadata.plugin, metadata.description))
                seen_names.add(t_name)

        # --- Skills and Instructions ---
        # Walk plugins to get proper plugin names and distinguish
        # instructions from regular skills.
        for plugin_name, plugin in self.discovered_plugins.items():
            # Collect instruction names for this plugin so we can label them
            instruction_names: Set[str] = set()
            try:
                for i_name, instr_obj in plugin.instructions.items():
                    instruction_names.add(i_name)
                    if i_name in seen_names:
                        continue
                    desc = instr_obj.descriptor
                    score = self._score_against_query(
                        query_words,
                        i_name,
                        set(desc.tags) if desc.tags else set(),
                        desc.category or "",
                        plugin_name,
                        desc.description or "",
                    )
                    if score > 0:
                        usage = tracker.get_count(i_name)
                        scored.append((score, usage, "instruction", i_name, plugin_name, desc.description))
                        seen_names.add(i_name)
            except Exception:
                pass

            try:
                for s_name, skill_obj in plugin.skills.items():
                    if s_name in seen_names:
                        continue
                    # Skip instructions already collected above
                    if s_name in instruction_names:
                        continue
                    desc = skill_obj.descriptor
                    score = self._score_against_query(
                        query_words,
                        s_name,
                        set(desc.tags) if desc.tags else set(),
                        desc.category or "",
                        plugin_name,
                        desc.description or "",
                    )
                    if score > 0:
                        usage = tracker.get_count(s_name)
                        scored.append((score, usage, "skill", s_name, plugin_name, desc.description))
                        seen_names.add(s_name)
            except Exception:
                pass

        # Sort by score desc, then usage desc
        scored.sort(key=lambda x: (-x[0], -x[1]))

        results: List[Dict[str, Any]] = []
        for score, _usage, kind, name, plugin, desc in scored[:limit]:
            plugin_obj = self.registry.get_plugin(plugin) if plugin else None
            source = plugin_obj.source.value if plugin_obj and hasattr(plugin_obj, "source") else "unknown"
            results.append({
                "name": name,
                "kind": kind,
                "plugin": plugin,
                "source": source,
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


def reset_unified_registry() -> None:
    """Discard the cached unified registry (useful for tests)."""
    global _unified_registry
    _unified_registry = None


def list_all_tools() -> List[Dict[str, Any]]:
    """Get a complete list of all available tools (transformers, skills, instructions).

    This function provides a unified view of every capability in the system,
    including which plugin provides each tool and its metadata.

    Returns:
        List of dictionaries with tool information including a ``kind`` field
        (``"transformer"``, ``"skill"``, or ``"instruction"``).
    """
    registry = get_unified_registry()
    all_tools = []
    seen_names: set = set()

    # Transformers
    for transformer_name in registry.get_all_transformers():
        plugin_name = registry.get_transformer_plugin(transformer_name)
        metadata = registry.get_transformer_metadata(transformer_name)

        tool_info = {
            "name": transformer_name,
            "kind": "transformer",
            "plugin": plugin_name or "unknown",
            "description": "No description available",
            "category": "unknown",
            "examples": [],
            "parameters": [],
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
                        "default": param.default_value,
                    } for param in metadata.parameters
                ],
            })

        all_tools.append(tool_info)
        seen_names.add(transformer_name)

    # Skills and Instructions (from discovered plugins)
    for plugin_name, plugin in registry.discovered_plugins.items():
        instruction_names: set = set()
        try:
            for i_name, instr_obj in plugin.instructions.items():
                instruction_names.add(i_name)
                if i_name in seen_names:
                    continue
                desc = instr_obj.descriptor
                all_tools.append({
                    "name": i_name,
                    "kind": "instruction",
                    "plugin": plugin_name,
                    "description": desc.description or "",
                    "category": desc.category or "general",
                    "version": desc.version,
                    "tags": list(desc.tags) if desc.tags else [],
                })
                seen_names.add(i_name)
        except Exception:
            pass

        try:
            for s_name, skill_obj in plugin.skills.items():
                if s_name in seen_names or s_name in instruction_names:
                    continue
                desc = skill_obj.descriptor
                all_tools.append({
                    "name": s_name,
                    "kind": "skill",
                    "plugin": plugin_name,
                    "description": desc.description or "",
                    "category": desc.category or "general",
                    "version": desc.version,
                    "tags": list(desc.tags) if desc.tags else [],
                })
                seen_names.add(s_name)
        except Exception:
            pass

    # Sort by plugin name, then tool name
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