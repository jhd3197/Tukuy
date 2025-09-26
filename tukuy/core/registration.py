"""Decorator-based plugin registration system for Tukuy."""

import importlib
import inspect
import sys
from functools import wraps
from typing import Dict, List, Any, Optional, Callable, Type
from logging import getLogger

from ..plugins.base import TransformerPlugin, PluginRegistry
from .introspection import TransformerIntrospector, TransformerMetadata
from ..base import ChainableTransformer

logger = getLogger(__name__)


class PluginState:
    """Tracks the state of registered plugins for hot-reloading."""

    def __init__(self):
        self.registered_plugins: Dict[str, TransformerPlugin] = {}
        self.plugin_modules: Dict[str, str] = {}
        self.plugin_last_modified: Dict[str, float] = {}

    def register_plugin(self, name: str, plugin: TransformerPlugin, module_name: str):
        """Register a plugin with its module name."""
        self.registered_plugins[name] = plugin
        self.plugin_modules[name] = module_name

    def get_plugin(self, name: str) -> Optional[TransformerPlugin]:
        """Get a registered plugin by name."""
        return self.registered_plugins.get(name)

    def get_module_name(self, name: str) -> Optional[str]:
        """Get the module name for a plugin."""
        return self.plugin_modules.get(name)


class TukuyPluginMeta:
    """Metadata for registered Tukuy plugins."""

    def __init__(self, name: str, description: str = "", version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.metadata: Dict[str, TransformerMetadata] = {}
        self.transformers: Dict[str, Callable] = {}


class RegistrationManager:
    """Manages the registration of plugins and transformers."""

    def __init__(self, registry: Optional[PluginRegistry] = None):
        """Initialize the registration manager."""
        self.registry = registry or PluginRegistry()
        self.introspector = TransformerIntrospector(self.registry)
        self.plugin_state = PluginState()
        self.registered_plugin_metas: Dict[str, TukuyPluginMeta] = {}

    def register_plugin_by_decorator(self, plugin_class: Type[TransformerPlugin],
                                     name: str, description: str = "",
                                     version: str = "1.0.0") -> Type[TransformerPlugin]:
        """Register a plugin class with the registration manager."""

        # Extract plugin metadata
        plugin_meta = TukuyPluginMeta(name, description, version)

        # Get the module name for hot-reloading support
        module_name = getattr(plugin_class, '__module__', 'unknown')

        # Register the plugin instance
        plugin_instance = plugin_class()
        self.registry.register(plugin_instance)

        # Store plugin state for hot-reloading
        self.plugin_state.register_plugin(name, plugin_instance, module_name)
        self.registered_plugin_metas[name] = plugin_meta

        logger.info("Registered plugin '%s' via decorator", name)
        return plugin_class

    def register_transformer(self, func_or_method: Callable, plugin_name: str,
                           transformer_name: str) -> Callable:
        """Register a transformer function or method with a plugin."""

        # Get the plugin instance
        plugin = self.plugin_state.get_plugin(plugin_name)
        if not plugin:
            logger.error("Plugin '%s' not found when registering transformer '%s'",
                        plugin_name, transformer_name)
            return func_or_method

        # Create a wrapper that creates the transformer instance
        def factory_wrapper(**kwargs):
            """Wrapper that creates transformer instances."""
            return func_or_method(**kwargs)

        # Add to plugin's transformers
        plugin.transformers[transformer_name] = factory_wrapper

        # Update the registry
        self.registry._transformers[transformer_name] = factory_wrapper

        logger.info("Registered transformer '%s' for plugin '%s'", transformer_name, plugin_name)
        return func_or_method

    def hot_reload_plugin(self, plugin_name: str) -> bool:
        """Hot-reload a specific plugin by name."""
        plugin = self.plugin_state.get_plugin(plugin_name)
        module_name = self.plugin_state.get_module_name(plugin_name)

        if not plugin or not module_name:
            logger.error("Plugin '%s' not found for hot reload", plugin_name)
            return False

        try:
            # Reload the module
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])

            # Re-create and re-register the plugin
            plugin_class = plugin.__class__
            new_plugin = plugin_class()

            # Unregister old plugin
            self.registry.unregister(plugin_name)

            # Register new plugin
            self.registry.register(new_plugin)

            # Update state
            self.plugin_state.register_plugin(plugin_name, new_plugin, module_name)

            logger.info("Successfully hot-reloaded plugin '%s'", plugin_name)
            return True

        except Exception as e:
            logger.error("Failed to hot-reload plugin '%s': %s", plugin_name, str(e))
            return False

    def hot_reload_all(self) -> Dict[str, bool]:
        """Hot-reload all registered plugins."""
        results = {}
        for plugin_name in self.plugin_state.registered_plugins.keys():
            results[plugin_name] = self.hot_reload_plugin(plugin_name)
        return results

    def get_plugin_metadata(self, plugin_name: str) -> Optional[TukuyPluginMeta]:
        """Get metadata for a registered plugin."""
        return self.registered_plugin_metas.get(plugin_name)

    def list_registered_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self.registered_plugin_metas.keys())

    def extract_transformer_metadata(self, plugin_name: str) -> Dict[str, TransformerMetadata]:
        """Extract metadata for all transformers in a plugin."""
        if plugin_name not in self.registered_plugin_metas:
            return {}

        plugin = self.plugin_state.get_plugin(plugin_name)
        if not plugin:
            return {}

        metadata = {}
        for transformer_name, factory_func in plugin.transformers.items():
            try:
                transformer_meta = self.introspector.get_transformer_metadata(
                    transformer_name, plugin, factory_func
                )
                metadata[transformer_name] = transformer_meta
            except Exception as e:
                logger.warning("Could not extract metadata for transformer '%s': %s",
                             transformer_name, str(e))

        return metadata


# Global registration manager instance
_registration_manager = None


def get_registration_manager() -> RegistrationManager:
    """Get the global registration manager instance."""
    global _registration_manager
    if _registration_manager is None:
        _registration_manager = RegistrationManager()
    return _registration_manager


def tukuy_plugin(name: str, description: str = "", version: str = "1.0.0"):
    """
    Decorator to register a plugin class with Tukuy.

    Args:
        name: Unique identifier for the plugin
        description: Optional description of the plugin
        version: Version string for the plugin

    Example:
        ```python
        @tukuy_plugin("my_plugin", "My custom plugin", "1.0.0")
        class MyPlugin(TransformerPlugin):
            @property
            def transformers(self):
                return {
                    'my_transformer': lambda: MyTransformer(),
                }
        ```
    """
    def decorator(cls: Type[TransformerPlugin]) -> Type[TransformerPlugin]:
        manager = get_registration_manager()
        return manager.register_plugin_by_decorator(cls, name, description, version)

    return decorator


def transformer(plugin_name: str, name: str):
    """
    Decorator to register transformer methods or functions.

    Args:
        plugin_name: Name of the plugin this transformer belongs to
        name: Name to register the transformer with

    Example:
        ```python
        class MyPlugin(TransformerPlugin):
            @transformer('my_plugin', 'my_transformer')
            class MyTransformer(ChainableTransformer[str, str]):
                def validate(self, value: str) -> bool:
                    return isinstance(value, str)

                def _transform(self, value: str, context=None) -> str:
                    return value.upper()
        ```
    """
    def decorator(func: Callable) -> Callable:
        manager = get_registration_manager()
        return manager.register_transformer(func, plugin_name, name)

    return decorator


# Convenience function for manual registration
def register_plugin(plugin: TransformerPlugin) -> None:
    """Manually register a plugin with the global registry."""
    manager = get_registration_manager()
    manager.registry.register(plugin)
    # Also track in plugin state if possible
    plugin_name = getattr(plugin, 'name', str(id(plugin)))
    module_name = getattr(type(plugin), '__module__', 'unknown')
    manager.plugin_state.register_plugin(plugin_name, plugin, module_name)


# Convenience function to get metadata
def get_plugin_info(plugin_name: str) -> Optional[TukuyPluginMeta]:
    """Get information about a registered plugin."""
    manager = get_registration_manager()
    return manager.get_plugin_metadata(plugin_name)


# Convenience function for hot reloading
def hot_reload(plugin_name: Optional[str] = None) -> bool:
    """Hot-reload a plugin or all plugins."""
    manager = get_registration_manager()
    if plugin_name:
        return manager.hot_reload_plugin(plugin_name)
    else:
        results = manager.hot_reload_all()
        return all(results.values())


def extract_metadata(plugin_name: str) -> Dict[str, TransformerMetadata]:
    """Extract metadata for all transformers in a plugin."""
    manager = get_registration_manager()
    return manager.extract_transformer_metadata(plugin_name)