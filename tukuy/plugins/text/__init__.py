"""Text transformation plugin."""

from typing import Dict, Optional

from ...base import BaseTransformer
from ...plugins.base import TransformerPlugin
from ...transformers.text import (
    StripTransformer,
    LowercaseTransformer,
    UppercaseTransformer,
    RegexTransformer,
    TemplateTransformer,
    MapTransformer,
    ReplaceTransformer,
    SplitTransformer,
    TitleCaseTransformer,
    CamelCaseTransformer,
    SnakeCaseTransformer,
    SlugifyTransformer,
    TruncateTransformer,
    RemoveEmojisTransformer,
    RedactSensitiveTransformer
)

class TextTransformersPlugin(TransformerPlugin):
    """Plugin providing text transformation capabilities."""
    
    def __init__(self):
        """Initialize the text transformers plugin."""
        super().__init__("text")
        
    @property
    def transformers(self):
        """Get the text transformers."""
        return {
            # Basic text transformers
            'strip': lambda _: StripTransformer('strip'),
            'lowercase': lambda _: LowercaseTransformer('lowercase'),
            'uppercase': lambda _: UppercaseTransformer('uppercase'),
            
            # Pattern matching
            'regex': lambda params: RegexTransformer('regex',
                pattern=params.get('pattern', ''),
                template=params.get('template')),
            'template': lambda params: TemplateTransformer('template',
                template=params.get('template', '')),
                
            # Value mapping
            'map': lambda params: MapTransformer('map',
                mapping=params.get('values', {}),
                default=params.get('default')),
                
            # String operations
            'replace': lambda params: ReplaceTransformer('replace',
                old=params.get('from', ''),
                new=params.get('to', '')),
            'split': lambda params: SplitTransformer('split',
                delimiter=params.get('delimiter', ':'),
                index=params.get('index', -1)),
                
            # Case transformations
            'title_case': lambda _: TitleCaseTransformer('title_case'),
            'camel_case': lambda _: CamelCaseTransformer('camel_case'),
            'snake_case': lambda _: SnakeCaseTransformer('snake_case'),
            'slugify': lambda _: SlugifyTransformer('slugify'),
            
            # Text manipulation
            'truncate': lambda params: TruncateTransformer('truncate',
                length=params.get('length', 50),
                suffix=params.get('suffix', '...')),
            'remove_emojis': lambda _: RemoveEmojisTransformer('remove_emojis'),
            'redact_sensitive': lambda _: RedactSensitiveTransformer('redact_sensitive'),
        }
        
    def initialize(self) -> None:
        """Initialize the text transformers plugin."""
        super().initialize()
        # Could add loading of text patterns or dictionaries here
        
    def cleanup(self) -> None:
        """Clean up the text transformers plugin."""
        super().cleanup()
        # Could add cleanup of any text caches here
