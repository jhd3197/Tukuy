"""Plugin registration helper for easy plugin creation and management.

This module provides utilities to simplify the process of creating and registering
new plugins in Tukuy, while maintaining compatibility with the existing folder structure.
"""

import importlib
import inspect
import os
import sys
from typing import Dict, List, Optional, Any, Callable, Type
from logging import getLogger

from .base import TransformerPlugin
from ..base import ChainableTransformer
from ..core.registration import tukuy_plugin, get_registration_manager

logger = getLogger(__name__)


class PluginBuilder:
    """Helper class for building plugins with automatic transformer discovery."""

    def __init__(self, name: str, description: str = "", version: str = "1.0.0"):
        """Initialize the plugin builder.

        Args:
            name: Unique name for the plugin
            description: Description of the plugin
            version: Version string
        """
        self.name = name
        self.description = description
        self.version = version
        self.transformers: Dict[str, Callable] = {}

    def add_transformer(self, name: str, factory_func: Callable,
                       description: str = "") -> 'PluginBuilder':
        """Add a transformer to the plugin.

        Args:
            name: Name of the transformer
            factory_func: Factory function that returns the transformer instance
            description: Optional description

        Returns:
            Self for chaining
        """
        self.transformers[name] = factory_func
        return self

    def add_transformer_from_class(self, name: str, transformer_class: Type[ChainableTransformer],
                                  factory_kwargs: Optional[Dict[str, Any]] = None) -> 'PluginBuilder':
        """Add a transformer from a class with automatic factory function creation.

        Args:
            name: Name of the transformer
            transformer_class: The transformer class
            factory_kwargs: Optional kwargs to pass to the factory function

        Returns:
            Self for chaining
        """
        kwargs = factory_kwargs or {}

        def factory_func(**params):
            # Merge default kwargs with runtime params
            all_kwargs = {**kwargs, **params}
            # Ensure name is always provided (required by ChainableTransformer)
            if 'name' not in all_kwargs:
                all_kwargs['name'] = name
            return transformer_class(**all_kwargs)

        self.transformers[name] = factory_func
        return self

    def discover_transformers_from_module(self, module_name: str,
                                        base_class: Type = ChainableTransformer) -> 'PluginBuilder':
        """Automatically discover and add transformers from a module.

        This method imports a module and finds all classes that inherit from base_class,
        automatically registering them as transformers.

        Args:
            module_name: Name of the module to import (e.g., 'tukuy.transformers.custom')
            base_class: Base class to look for (default: ChainableTransformer)

        Returns:
            Self for chaining
        """
        try:
            module = importlib.import_module(module_name)

            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, base_class) and
                    obj != base_class):

                    # Create a factory function for this transformer
                    def factory_func(transformer_name=name, transformer_class=obj, **kwargs):
                        # Use the transformer name as default name parameter if not provided
                        if 'name' not in kwargs:
                            kwargs['name'] = transformer_name
                        return transformer_class(**kwargs)

                    # Use lowercase class name as transformer name
                    transformer_name = name.lower()
                    self.add_transformer(transformer_name, factory_func)

                    logger.info(f"Discovered transformer: {transformer_name} from {module_name}")

        except ImportError as e:
            logger.warning(f"Could not import module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Error discovering transformers from {module_name}: {e}")

        return self

    def build(self) -> Type[TransformerPlugin]:
        """Build the plugin class.

        Returns:
            A plugin class that can be instantiated and registered
        """
        # Define the plugin class
        class BuiltPlugin(TransformerPlugin):
            def __init__(self):
                super().__init__(self._name)

            def __class_getitem__(cls, key):
                return cls

            @property
            def transformers(self):
                return self._transformers.copy()

        # Set class attributes
        BuiltPlugin._name = self.name
        BuiltPlugin._transformers = self.transformers.copy()

        # Add docstring
        BuiltPlugin.__doc__ = f"{self.description}\n\nVersion: {self.version}"

        # Store metadata for registration
        BuiltPlugin._plugin_metadata = {
            'name': self.name,
            'description': self.description,
            'version': self.version
        }

        logger.info(f"Built plugin: {self.name} with {len(self.transformers)} transformers")
        return BuiltPlugin


def create_simple_plugin(name: str, transformers: Dict[str, Callable],
                        description: str = "", version: str = "1.0.0") -> Type[TransformerPlugin]:
    """Create a simple plugin from a dictionary of transformers.

    Args:
        name: Plugin name
        transformers: Dictionary mapping transformer names to factory functions
        description: Plugin description
        version: Plugin version

    Returns:
        Plugin class ready for registration
    """
    builder = PluginBuilder(name, description, version)

    for transformer_name, factory_func in transformers.items():
        builder.add_transformer(transformer_name, factory_func)

    return builder.build()


def create_plugin_from_directory(dirname: str, plugin_name: str,
                               description: str = "", version: str = "1.0.0") -> Optional[Type[TransformerPlugin]]:
    """Create a plugin by discovering transformers from a directory structure.

    This function looks for Python files in the given directory and attempts to
    discover transformer classes from them.

    Args:
        dirname: Directory path to scan (relative to tukuy/plugins/)
        plugin_name: Name for the plugin
        description: Plugin description
        version: Plugin version

    Returns:
        Plugin class if transformers were found, None otherwise
    """
    builder = PluginBuilder(plugin_name, description, version)

    # Convert dirname to module path
    module_base = f"tukuy.plugins.{dirname}"

    # Look for __init__.py first
    init_module = f"{module_base}"
    try:
        builder.discover_transformers_from_module(init_module)
    except ImportError:
        logger.debug(f"No __init__.py found in {module_base}")

    # Look for individual files in the directory
    try:
        import tukuy.plugins
        plugins_dir = os.path.dirname(tukuy.plugins.__file__)

        if os.path.exists(plugins_dir):
            target_dir = os.path.join(plugins_dir, dirname)
            if os.path.exists(target_dir):
                for file_name in os.listdir(target_dir):
                    if file_name.endswith('.py') and file_name != '__init__.py':
                        module_name = file_name[:-3]  # Remove .py extension
                        full_module = f"{module_base}.{module_name}"

                        try:
                            builder.discover_transformers_from_module(full_module)
                        except ImportError:
                            logger.debug(f"Could not import {full_module}")

    except Exception as e:
        logger.warning(f"Error scanning directory {dirname}: {e}")

    # Only return a plugin if we found transformers
    if builder.transformers:
        return builder.build()

    logger.warning(f"No transformers found in directory: {dirname}")
    return None


def register_plugin(plugin_class: Type[TransformerPlugin]) -> None:
    """Register a plugin with the Tukuy system.

    This function handles the registration process and ensures the plugin
    is properly integrated with the existing system.

    Args:
        plugin_class: The plugin class to register
    """
    try:
        manager = get_registration_manager()

        # Use decorator-based registration if metadata is available
        if hasattr(plugin_class, '_plugin_metadata'):
            metadata = plugin_class._plugin_metadata
            registered_class = tukuy_plugin(
                metadata['name'],
                metadata['description'],
                metadata['version']
            )(plugin_class)
        else:
            # Fallback to manual registration for backward compatibility
            plugin_instance = plugin_class()
            manager.registry.register(plugin_instance)

        # Get unified registry and refresh discovery
        try:
            from ..core.unified import get_unified_registry
            registry = get_unified_registry()
            registry.discover_plugins()
        except ImportError:
            pass  # Unified registry not available, but plugin is still registered

        logger.info(f"Successfully registered plugin: {plugin_class.__name__}")

    except Exception as e:
        logger.error(f"Failed to register plugin {plugin_class.__name__}: {e}")
        raise


def quick_register_from_directory(dirname: str, plugin_name: str,
                                description: str = "", version: str = "1.0.0") -> bool:
    """Quickly create and register a plugin from a directory.

    This is a convenience function that combines create_plugin_from_directory
    and register_plugin for one-step plugin registration.

    Args:
        dirname: Directory to scan for transformers
        plugin_name: Name for the plugin
        description: Plugin description
        version: Plugin version

    Returns:
        True if registration was successful, False otherwise
    """
    try:
        plugin_class = create_plugin_from_directory(dirname, plugin_name, description, version)

        if plugin_class:
            register_plugin(plugin_class)
            return True

        logger.warning(f"Could not create plugin from directory: {dirname}")
        return False

    except Exception as e:
        logger.error(f"Failed to register plugin from directory {dirname}: {e}")
        return False


# Convenience functions for common use cases
def create_text_transformer_plugin(transformers: Dict[str, Callable]) -> Type[TransformerPlugin]:
    """Create a text processing plugin with the given transformers."""
    return create_simple_plugin(
        "text_transformers",
        transformers,
        "Custom text processing transformers",
        "1.0.0"
    )


def create_data_transformer_plugin(transformers: Dict[str, Callable]) -> Type[TransformerPlugin]:
    """Create a data processing plugin with the given transformers."""
    return create_simple_plugin(
        "data_transformers",
        transformers,
        "Custom data processing transformers",
        "1.0.0"
    )