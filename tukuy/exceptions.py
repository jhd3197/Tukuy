from typing import Any, Optional

class TransformerError(Exception):
    """Base exception class for all transformer-related errors."""
    def __init__(self, message: str, value: Any = None):
        self.message = message
        self.value = value
        super().__init__(self.message)

class ValidationError(TransformerError):
    """Raised when input validation fails."""
    pass

class TransformationError(TransformerError):
    """Raised when a transformation operation fails."""
    def __init__(self, message: str, value: Any = None, transformer_name: Optional[str] = None):
        self.transformer_name = transformer_name
        super().__init__(message, value)

class ConfigurationError(TransformerError):
    """Raised when transformer configuration is invalid."""
    pass

class PatternError(TransformerError):
    """Raised when a pattern is invalid or malformed."""
    pass

class ExtractorError(TransformerError):
    """Raised when data extraction fails."""
    pass

class ParseError(TransformerError):
    """Raised when parsing operations fail."""
    pass
