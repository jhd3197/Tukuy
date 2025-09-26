"""Example plugin demonstrating decorator-based registration (new approach)."""

from typing import Optional
from ..base import ChainableTransformer
from ..types import TransformContext
from ..plugins.base import TransformerPlugin
from ..core.registration import tukuy_plugin, transformer, get_registration_manager


# Example 1: Using @tukuy_plugin decorator
@tukuy_plugin("text_processor", "A comprehensive text processing plugin", "2.0.0")
class TextProcessorPlugin(TransformerPlugin):
    """A plugin that provides various text processing transformers."""

    def __init__(self):
        """Initialize the text processor plugin."""
        super().__init__("text_processor")

    @property
    def transformers(self):
        """Get the transformers provided by this plugin."""
        return {
            'excerpt': lambda: ExcerptTransformer('excerpt'),
            'format_title': lambda: FormatTitleTransformer('format_title'),
            'remove_duplicates': lambda: RemoveDuplicatesTransformer('remove_duplicates'),
        }


class ExcerptTransformer(ChainableTransformer[str, str]):
    """
    Description:
        Creates an excerpt from text with a specified maximum length.

    Version: v1.0
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        max_length (int): Maximum length of the excerpt (default: 150)
        suffix (str): String to append when truncation occurs (default: "...")

    Returns:
        str: The text excerpt, truncated if necessary

    Example:
        ```python
        transformer = ExcerptTransformer("excerpt", max_length=100)
        result = transformer.transform("This is a very long text that needs to be shortened")
        # Result: "This is a very long text that needs..."
        ```
    """

    def __init__(self, name: str, max_length: int = 150, suffix: str = "..."):
        super().__init__(name)
        self.max_length = max_length
        self.suffix = suffix

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        if len(value) <= self.max_length:
            return value
        return value[:self.max_length - len(self.suffix)] + self.suffix


class FormatTitleTransformer(ChainableTransformer[str, str]):
    """
    Description:
        Formats text into a proper title case with intelligent word capitalization.

    Version: v1.0
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer

    Returns:
        str: The text formatted as title case

    Example:
        ```python
        transformer = FormatTitleTransformer("title")
        result = transformer.transform("hello world example")
        # Result: "Hello World Example"
        ```
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        import string
        return string.capwords(value.lower())


class RemoveDuplicatesTransformer(ChainableTransformer[str, str]):
    """
    Description:
        Removes duplicate words from text while preserving order.

    Version: v1.0
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        case_sensitive (bool): Whether to consider case when detecting duplicates

    Returns:
        str: Text with duplicate words removed

    Example:
        ```python
        transformer = RemoveDuplicatesTransformer("dedup")
        result = transformer.transform("hello world hello there there")
        # Result: "hello world there"
        ```
    """

    def __init__(self, name: str, case_sensitive: bool = False):
        super().__init__(name)
        self.case_sensitive = case_sensitive

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        words = value.split()
        seen = set()
        unique_words = []

        for word in words:
            key = word if self.case_sensitive else word.lower()
            if key not in seen:
                seen.add(key)
                unique_words.append(word)

        return ' '.join(unique_words)


# Example 2: Using @transformer decorator directly on functions
# This allows for more flexible registration patterns

def create_sentiment_transformer(sensitivity: float = 0.5):
    """Factory function for creating sentiment analysis transformers."""
    return SentimentAnalyzer('sentiment', sensitivity)


def create_word_count_transformer(ignore_whitespace: bool = True):
    """Factory function for creating word count transformers."""
    return WordCountTransformer('word_count', ignore_whitespace)


class SentimentAnalyzer(ChainableTransformer[str, dict]):
    """
    Description:
        Performs basic sentiment analysis on text.

    Version: v1.0
    Status: Beta
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        sensitivity (float): Sensitivity for positive/negative detection (0.0-1.0)

    Returns:
        dict: Dictionary with sentiment analysis results
    """

    def __init__(self, name: str, sensitivity: float = 0.5):
        super().__init__(name)
        self.sensitivity = sensitivity

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        # Simple sentiment detection based on positive/negative words
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike']

        text_lower = value.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        return {
            'sentiment': sentiment,
            'positive_score': positive_count,
            'negative_score': negative_count,
            'confidence': min(1.0, (positive_count + negative_count) * self.sensitivity)
        }


class WordCountTransformer(ChainableTransformer[str, dict]):
    """
    Description:
        Counts words, characters, and lines in text.

    Version: v1.0
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        ignore_whitespace (bool): Whether to ignore empty lines

    Returns:
        dict: Statistics about the text
    """

    def __init__(self, name: str, ignore_whitespace: bool = True):
        super().__init__(name)
        self.ignore_whitespace = ignore_whitespace

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> dict:
        lines = value.split('\n') if not self.ignore_whitespace else [line for line in value.split('\n') if line.strip()]

        return {
            'word_count': sum(len(line.split()) for line in lines),
            'line_count': len(lines),
            'char_count': len(value),
            'char_count_no_whitespace': len(value.replace(' ', '').replace('\n', '').replace('\t', '')),
        }


# Register the individual transformers using the transformer decorator
@transformer('sentiment_plugin', 'sentiment')
def sentiment_factory(**kwargs):
    """Factory function for sentiment transformers registered via decorator."""
    return SentimentAnalyzer('sentiment', kwargs.get('sensitivity', 0.5))


@transformer('word_analysis_plugin', 'word_stats')
def word_stats_factory(**kwargs):
    """Factory function for word statistics transformers registered via decorator."""
    return WordCountTransformer('word_stats', kwargs.get('ignore_whitespace', True))


# Example custom plugin using manual registration pattern (backward compatibility)
class CustomUtilitiesPlugin:
    """Custom utilities plugin showing backward compatibility."""

    def __init__(self):
        """Initialize the custom utilities plugin."""
        self.name = "custom_utils"

    @property
    def transformers(self):
        """Get the transformers provided by this plugin."""
        return {
            'advanced_excerpt': lambda: AdvancedExcerptTransformer('advanced_excerpt'),
        }


class AdvancedExcerptTransformer(ChainableTransformer[str, str]):
    """
    Description:
        Advanced excerpt transformer with intelligent content truncation.

    Version: v1.0
    Status: Production
    Last Updated: 2024-03-24
    """

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        # Advanced logic to find sentence boundaries
        if len(value) <= 100:
            return value

        # Try to find a sentence boundary near the limit
        text = value[:120]  # Slightly over our limit
        last_period = text.rfind('.')
        last_exclamation = text.rfind('!')
        last_question = text.rfind('?')

        # Find the rightmost sentence ending
        boundaries = [last_period, last_exclamation, last_question]
        cut_point = max(b for b in boundaries if b > 0)

        if cut_point > 50:  # Ensure we're not cutting too short
            return value[:cut_point + 1]

        # Fall back to word boundary
        words = value[:90].split()
        return ' '.join(words[:-1]) + '...'