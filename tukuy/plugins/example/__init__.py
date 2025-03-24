"""Example plugin demonstrating how to create custom plugins."""

import re
from typing import Optional

from ...base import BaseTransformer, ChainableTransformer
from ...plugins.base import TransformerPlugin
from ...types import TransformContext
from ...exceptions import ValidationError

class ReverseTransformer(ChainableTransformer[str, str]):
    """Example transformer that reverses text."""
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return value[::-1]

class CountWordsTransformer(ChainableTransformer[str, int]):
    """Example transformer that counts words in text."""
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> int:
        return len(value.split())

class FindPatternTransformer(ChainableTransformer[str, list]):
    """Example transformer that finds all occurrences of a pattern."""
    
    def __init__(self, name: str, pattern: str):
        super().__init__(name)
        self.pattern = re.compile(pattern)
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> list:
        return self.pattern.findall(value)

class ExamplePlugin(TransformerPlugin):
    """
    Example plugin demonstrating plugin creation.
    
    This plugin provides simple text manipulation transformers as an example
    of how to create custom plugins. Use this as a template for creating
    your own plugins.
    
    Example usage:
        ```python
        from tukuy import ToolsTransformer
        from tukuy.plugins.example import ExamplePlugin
        
        # Create transformer
        TUKUY = ToolsTransformer()
        
        # Register plugin
        TUKUY.register_plugin(ExamplePlugin())
        
        # Use transformers
        text = "Hello World"
        
        # Reverse text
        reversed_text = TUKUY.transform(text, ["reverse"])  # "dlroW olleH"
        
        # Count words
        word_count = TUKUY.transform(text, ["count_words"])  # 2
        
        # Find patterns
        patterns = TUKUY.transform(text, [{
            "function": "find_pattern",
            "pattern": r"\w+"
        }])  # ["Hello", "World"]
        ```
    """
    
    def __init__(self):
        """Initialize the example plugin."""
        super().__init__("example")
        
    @property
    def transformers(self):
        """Get the example transformers."""
        return {
            'reverse': lambda _: ReverseTransformer('reverse'),
            'count_words': lambda _: CountWordsTransformer('count_words'),
            'find_pattern': lambda params: FindPatternTransformer('find_pattern',
                pattern=params.get('pattern', r'\w+')),
        }
        
    def initialize(self) -> None:
        """Initialize the example plugin."""
        super().initialize()
        # Add any setup code here
        
    def cleanup(self) -> None:
        """Clean up the example plugin."""
        super().cleanup()
        # Add any cleanup code here
