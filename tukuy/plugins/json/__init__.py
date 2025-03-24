"""JSON transformation plugin."""

from ...base import BaseTransformer
from ...plugins.base import TransformerPlugin
from ...transformers.json import (
    JsonParser,
    JsonExtractor
)

class JsonTransformersPlugin(TransformerPlugin):
    """Plugin providing JSON transformation capabilities."""
    
    def __init__(self):
        """Initialize the JSON transformers plugin."""
        super().__init__("json")
        
    @property
    def transformers(self):
        """Get the JSON transformers."""
        return {
            # JSON parsing
            'json_parse': lambda params: JsonParser('json_parse',
                strict=params.get('strict', True),
                schema=params.get('schema')),
                
            # JSON extraction
            'json_extract': lambda params: JsonExtractor('json_extract',
                pattern=params.get('pattern', {})),
        }
        
    def initialize(self) -> None:
        """Initialize the JSON transformers plugin."""
        super().initialize()
        # Could add loading of JSON schemas or validation rules here
        
    def cleanup(self) -> None:
        """Clean up the JSON transformers plugin."""
        super().cleanup()
        # Could add cleanup of any JSON caches here
