"""Transformer implementations for different types of data transformations."""

from typing import Any, Dict, List, Optional, Union
from logging import getLogger

from ..base import BaseTransformer
from ..types import TransformContext, JsonType
from ..exceptions import ValidationError, TransformationError
from ..plugins import (
    PluginRegistry,
    BUILTIN_PLUGINS
)

logger = getLogger(__name__)

class TukuyTransformer:
    """
    Main transformer class that provides access to all transformation tools.
    
    This class serves as the main entry point for the transformation library,
    providing a unified interface to all available transformers through a plugin system.
    """
    
    def __init__(self):
        """Initialize the transformer registry."""
        self.registry = PluginRegistry()
        self._load_builtin_plugins()
    
    def _load_builtin_plugins(self):
        """Load all built-in plugins."""
        for name, plugin_class in BUILTIN_PLUGINS.items():
            try:
                plugin = plugin_class()
                self.registry.register(plugin)
            except Exception as e:
                logger.error(f"Failed to load plugin {name}: {str(e)}")
    
    def register_plugin(self, plugin):
        """
        Register a custom plugin.
        
        Args:
            plugin: The plugin to register
        """
        self.registry.register(plugin)
    
    def unregister_plugin(self, name: str):
        """
        Unregister a plugin.
        
        Args:
            name: Name of the plugin to unregister
        """
        self.registry.unregister(name)
    
    def transform(self, value: Any, transforms: List[Union[str, Dict[str, Any]]]) -> Any:
        """
        Transform a value using a sequence of transformations.
        
        Args:
            value: The value to transform
            transforms: List of transformations to apply. Each item can be:
                - a string (the transformer name)
                - a dict with 'function' key and additional parameters
                
        Returns:
            The transformed value
            
        Raises:
            TransformationError: If any transformation fails
            ParseError: If JSON parsing fails in strict mode
            ValidationError: If schema validation fails
        """
        from ..exceptions import ParseError, ValidationError
        
        context = {}
        current_value = value
        
        for transform in transforms:
            # Skip null transformations
            if current_value is None:
                break
                
            # Get transformer name and parameters
            if isinstance(transform, dict):
                func_name = transform.get('function')
                params = {k: v for k, v in transform.items() if k != 'function'}
            else:
                func_name = transform
                params = {}
                
            # Get transformer factory
            factory = self.registry.get_transformer(func_name)
            if not factory:
                raise ValidationError(f"Unknown transformer: {func_name}")
                
            # Create transformer
            transformer = factory(params)
                
            # Apply transformation
            try:
                result = transformer.transform(current_value, context)
                if result.failed:
                    error = result.error
                    # Make sure we're re-raising the right exception class
                    if func_name == "json_parse":
                        if error.__class__.__name__ == "ValidationError":
                            raise ValidationError(str(error), current_value)
                        if params.get('strict', True) and error.__class__.__name__ == "ParseError":
                            raise ParseError(str(error), current_value)
                    raise error
                current_value = result.value
                
            except (ValidationError, ParseError) as e:
                # Allow these exceptions to propagate directly
                raise
            except Exception as e:
                if isinstance(e, TransformationError):
                    raise e
                raise TransformationError(
                    f"Transformation '{func_name}' failed: {str(e)}",
                    current_value
                )
        
        return current_value
    
    def extract_html_with_pattern(self, html: str, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from HTML using a pattern."""
        html_plugin = self.registry.get_plugin('html')
        if not html_plugin:
            raise ValidationError("HTML plugin not loaded")
            
        extractor = html_plugin.transformers['html_extract']({"pattern": pattern})
        result = extractor.transform(html)
        if result.failed:
            raise result.error
        return result.value
    
    def extract_property_from_html(self, html: str, prop: Dict[str, Any]) -> Any:
        """Extract a single property from HTML."""
        html_plugin = self.registry.get_plugin('html')
        if not html_plugin:
            raise ValidationError("HTML plugin not loaded")
            
        # Convert single property to proper pattern format
        pattern = {
            "properties": [prop]
        }
        extractor = html_plugin.transformers['html_extract']({"pattern": pattern})
        result = extractor.transform(html)
        if result.failed:
            raise result.error
        return result.value[prop['name']] if prop.get('name') else None
    
    def extract_json_with_pattern(self, json_data: str, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from JSON using a pattern."""
        json_plugin = self.registry.get_plugin('json')
        if not json_plugin:
            raise ValidationError("JSON plugin not loaded")
            
        # Parse the JSON string first
        parser = json_plugin.transformers['json_parse']({"strict": True})
        parsed = parser.transform(json_data)
        if parsed.failed:
            raise parsed.error
            
        # Extract data using the pattern
        extractor = json_plugin.transformers['json_extract']({"pattern": pattern})
        result = extractor.transform(parsed.value)
        if result.failed:
            raise result.error
        
        return result.value

    def extract_property_from_json(self, json_data: Union[str, JsonType], prop: Dict[str, Any]) -> Any:
        """Extract a single property from JSON data.
        
        Args:
            json_data: JSON string or already parsed JSON data
            prop: Property extraction pattern
            
        Returns:
            The extracted property value
            
        Raises:
            ValidationError: If JSON plugin is not loaded
            ParseError: If JSON string is invalid
            TransformationError: If extraction fails
        """
        json_plugin = self.registry.get_plugin('json')
        if not json_plugin:
            raise ValidationError("JSON plugin not loaded")
            
        # Parse the JSON string if needed
        if isinstance(json_data, str):
            parser = json_plugin.transformers['json_parse']({"strict": True})
            parsed = parser.transform(json_data)
            if parsed.failed:
                raise parsed.error
            data = parsed.value
        else:
            data = json_data
            
        # Convert single property to proper pattern format
        pattern = {
            "properties": [prop]
        }
        extractor = json_plugin.transformers['json_extract']({"pattern": pattern})
        result = extractor.transform(data)
        if result.failed:
            raise result.error
        return result.value[prop['name']] if prop.get('name') else None

__all__ = ['TukuyTransformer']
