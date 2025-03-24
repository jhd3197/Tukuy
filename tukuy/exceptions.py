from typing import Any, Optional

class TransformerError(Exception):
    """Base exception class for all transformer-related errors."""
    def __init__(self, message: str, value: Any = None):
        self.message = message
        self.value = value
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.value is not None:
            return f"{self.message} (value: {repr(self.value)})"
        return self.message

class ValidationError(TransformerError):
    """Raised when input validation fails."""
    def __str__(self) -> str:
        base_msg = super().__str__()
        return f"Validation Error: {base_msg}"

class TransformationError(TransformerError):
    """Raised when a transformation operation fails."""
    def __init__(self, message: str, value: Any = None, transformer_name: Optional[str] = None):
        self.transformer_name = transformer_name
        super().__init__(message, value)
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.transformer_name:
            return f"Transformation Error in {self.transformer_name}: {base_msg}"
        return f"Transformation Error: {base_msg}"

class ConfigurationError(TransformerError):
    """Raised when transformer configuration is invalid."""
    def __str__(self) -> str:
        base_msg = super().__str__()
        return f"Configuration Error: {base_msg}"

class PatternError(TransformerError):
    """Raised when a pattern is invalid or malformed."""
    def __str__(self) -> str:
        base_msg = super().__str__()
        return f"Pattern Error: {base_msg}"

class ExtractorError(TransformerError):
    """Raised when data extraction fails."""
    def __str__(self) -> str:
        base_msg = super().__str__()
        return f"Extraction Error: {base_msg}"

class ParseError(TransformerError):
    """Raised when parsing operations fail."""
    def __str__(self) -> str:
        base_msg = super().__str__()
        return f"Parse Error: {base_msg}"
