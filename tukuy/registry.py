"""Shared singleton PluginRegistry for Tukuy.

Every component (TukuyTransformer, Chain, UnifiedRegistry) that needs a
registry should call :func:`get_shared_registry` instead of creating its
own :class:`PluginRegistry`.  The shared registry is populated lazily on
first access with all built-in plugins.
"""

from typing import Optional
from logging import getLogger

from .plugins.base import PluginRegistry, PluginSource

logger = getLogger(__name__)

_shared_registry: Optional[PluginRegistry] = None


def get_shared_registry() -> PluginRegistry:
    """Return the process-wide shared :class:`PluginRegistry`.

    On first call the registry is created and all built-in plugins are
    loaded.  Subsequent calls return the same instance.
    """
    global _shared_registry
    if _shared_registry is None:
        _shared_registry = PluginRegistry()
        _load_builtin_plugins(_shared_registry)
    return _shared_registry


def _load_builtin_plugins(registry: PluginRegistry) -> None:
    """Load every built-in plugin into *registry*."""
    from .plugins import BUILTIN_PLUGINS

    for name in BUILTIN_PLUGINS.keys():
        try:
            plugin_class = BUILTIN_PLUGINS[name]
            plugin = plugin_class()
            registry.register(plugin, source=PluginSource.TUKUY)
        except Exception as e:
            logger.debug("Skipped built-in plugin %s: %s", name, e)


def reset_shared_registry() -> None:
    """Discard the current shared registry (mainly useful for tests)."""
    global _shared_registry
    _shared_registry = None
