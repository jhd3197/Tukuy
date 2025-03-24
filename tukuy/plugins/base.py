"""Base classes and utilities for the plugin system."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from logging import getLogger

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
        
    def cleanup(self) -> None:
        """
        Called when the plugin is unloaded.
        
        Override this method to perform any cleanup required by the plugin.
        """
        logger.info(f"Cleaning up plugin: {self.name}")

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
        plugin.initialize()
        
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
