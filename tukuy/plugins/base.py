"""Base classes and utilities for the plugin system."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Optional
from logging import getLogger

if TYPE_CHECKING:
    from ..skill import Skill

logger = getLogger(__name__)

class TransformerPlugin(ABC):
    """
    Base class for transformer plugins.
    
    A plugin is a collection of related transformers that can be registered
    with the TukuyTransformer. Plugins provide a way to organize transformers
    into logical groups and manage their lifecycle.
    """
    
    def __init__(self, name: str):
        """
        Initialize the plugin.
        
        Args:
            name: Unique identifier for this plugin
        """
        self.name = name
        
    @property
    @abstractmethod
    def transformers(self) -> Dict[str, callable]:
        """
        Get the transformers provided by this plugin.
        
        Returns:
            A dictionary mapping transformer names to factory functions
        """
        return {}
        
    def initialize(self) -> None:
        """
        Called when the plugin is loaded.

        Override this method to perform any setup required by the plugin.
        """
        logger.info(f"Initializing plugin: {self.name}")

    async def async_initialize(self) -> None:
        """Async variant of :meth:`initialize`.

        Called by :meth:`PluginRegistry.async_register`.  The default
        implementation delegates to the synchronous ``initialize()`` so
        existing plugins work without changes.
        """
        self.initialize()

    @property
    def skills(self) -> Dict[str, "Skill"]:
        """Get the skills provided by this plugin.

        Returns:
            A dictionary mapping skill names to Skill instances.
            Defaults to an empty dict for backward compatibility.
        """
        return {}

    def cleanup(self) -> None:
        """
        Called when the plugin is unloaded.

        Override this method to perform any cleanup required by the plugin.
        """
        logger.info(f"Cleaning up plugin: {self.name}")

    async def async_cleanup(self) -> None:
        """Async variant of :meth:`cleanup`.

        Called by :meth:`PluginRegistry.async_unregister`.  The default
        implementation delegates to the synchronous ``cleanup()`` so
        existing plugins work without changes.
        """
        self.cleanup()

class PluginRegistry:
    """
    Registry for managing transformer plugins.
    
    The registry maintains the collection of loaded plugins and their
    transformers, handling registration, unregistration, and access to
    transformer factories.
    """
    
    def __init__(self):
        """Initialize an empty plugin registry."""
        self._plugins: Dict[str, TransformerPlugin] = {}
        self._transformers: Dict[str, callable] = {}
        self._skills: Dict[str, "Skill"] = {}
        
    def register(self, plugin: TransformerPlugin) -> None:
        """
        Register a plugin with the registry.

        Args:
            plugin: The plugin to register

        Raises:
            ValueError: If a plugin with the same name is already registered
        """
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin.name}")

        logger.info(f"Registering plugin: {plugin.name}")
        self._plugins[plugin.name] = plugin
        self._transformers.update(plugin.transformers)

        # Merge skills (backward-compatible: old plugins won't have skills)
        try:
            self._skills.update(plugin.skills)
        except Exception:
            pass

        plugin.initialize()

    async def async_register(self, plugin: TransformerPlugin) -> None:
        """Async variant of :meth:`register`.

        Indexes transformers and skills synchronously, then awaits the
        plugin's :meth:`~TransformerPlugin.async_initialize`.
        """
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin.name}")

        logger.info(f"Async registering plugin: {plugin.name}")
        self._plugins[plugin.name] = plugin
        self._transformers.update(plugin.transformers)

        try:
            self._skills.update(plugin.skills)
        except Exception:
            pass

        await plugin.async_initialize()

    def unregister(self, name: str) -> None:
        """
        Unregister a plugin from the registry.

        Args:
            name: Name of the plugin to unregister
        """
        if name not in self._plugins:
            return

        logger.info(f"Unregistering plugin: {name}")
        plugin = self._plugins[name]
        plugin.cleanup()

        # Remove transformers
        for key in plugin.transformers:
            self._transformers.pop(key, None)

        # Remove skills (backward-compatible)
        try:
            for key in plugin.skills:
                self._skills.pop(key, None)
        except Exception:
            pass

        del self._plugins[name]

    async def async_unregister(self, name: str) -> None:
        """Async variant of :meth:`unregister`.

        Awaits the plugin's :meth:`~TransformerPlugin.async_cleanup` before
        removing it from the registry.
        """
        if name not in self._plugins:
            return

        logger.info(f"Async unregistering plugin: {name}")
        plugin = self._plugins[name]
        await plugin.async_cleanup()

        for key in plugin.transformers:
            self._transformers.pop(key, None)

        try:
            for key in plugin.skills:
                self._skills.pop(key, None)
        except Exception:
            pass

        del self._plugins[name]
        
    def get_transformer(self, name: str) -> Optional[callable]:
        """
        Get a transformer factory by name.
        
        Args:
            name: Name of the transformer
            
        Returns:
            The transformer factory function, or None if not found
        """
        return self._transformers.get(name)
        
    def get_plugin(self, name: str) -> Optional[TransformerPlugin]:
        """
        Get a plugin by name.
        
        Args:
            name: Name of the plugin
            
        Returns:
            The plugin instance, or None if not found
        """
        return self._plugins.get(name)
        
    @property
    def plugins(self) -> Dict[str, TransformerPlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()
        
    @property
    def transformers(self) -> Dict[str, callable]:
        """Get all registered transformers."""
        return self._transformers.copy()

    def get_skill(self, name: str) -> Optional["Skill"]:
        """Get a skill by name.

        Args:
            name: Name of the skill

        Returns:
            The Skill instance, or None if not found
        """
        return self._skills.get(name)

    @property
    def skills(self) -> Dict[str, "Skill"]:
        """Get all registered skills."""
        return self._skills.copy()
