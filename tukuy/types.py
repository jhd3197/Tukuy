from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union, Generic
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

# Type variables for generic transformers
T = TypeVar('T')  # Input type
U = TypeVar('U')  # Output type

# Common types
JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
TransformContext = Dict[str, Any]

class TransformResult(Generic[T]):
    """
    Description:
        Container for transformation results with error handling.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Type Parameters:
        T: The type of the transformed value

    Methods:
        __init__(value: Optional[T] = None, error: Optional[Exception] = None):
            Initialize a new TransformResult with an optional value or error.
            
        failed: bool
            Property indicating if the transformation failed.
            
        __str__() -> str:
            String representation of the result.
    """
    
    def __init__(self, value: Optional[T] = None, error: Optional[Exception] = None):
        self.value = value
        self.error = error
        self.success = error is None

    @property
    def failed(self) -> bool:
        """:no-index:"""
        return not self.success

    def __str__(self) -> str:
        if self.success:
            return f"TransformResult(value={self.value})"
        return f"TransformResult(error={self.error})"

@dataclass
class TransformOptions:
    """
    Description:
        Base class for transformer options.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    """
    pass

@dataclass
class TextTransformOptions(TransformOptions):
    """Options for text transformations."""
    strip: bool = True
    case_sensitive: bool = True

@dataclass
class DateTransformOptions(TransformOptions):
    """Options for date transformations."""
    format: str = '%Y-%m-%d'
    timezone: Optional[str] = None

@dataclass
class NumberTransformOptions(TransformOptions):
    """Options for number transformations."""
    decimals: int = 2
    strip_non_numeric: bool = True

@dataclass
class PatternOptions(TransformOptions):
    """Options for pattern-based transformations."""
    pattern: str
    template: Optional[str] = None
    flags: int = 0

@dataclass
class ExtractorOptions(TransformOptions):
    """Options for data extraction."""
    selector: Union[str, Dict[str, Any]]
    attribute: str = "text"
    fallback: Optional[Union[str, List[str]]] = None

class TransformerProtocol(Protocol[T, U]):
    """
    Description:
        Protocol defining the interface for transformers.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Type Parameters:
        T: The input type that this transformer accepts
        U: The output type that this transformer produces

    Methods:
        name() -> str:
            Get the transformer name.
            
        transform(value: T, context: Optional[TransformContext] = None) -> TransformResult[U]:
            Transform the input value according to the transformer's rules.
            
        validate(value: T) -> bool:
            Validate if the input value is acceptable for this transformer.
            
        get_validation_errors(value: T) -> List[str]:
            Get list of validation errors for the input value.
    """
    
    @property
    def name(self) -> str:
        """:no-index:"""
        return "base_transformer"
    
    def transform(self, value: T, context: Optional[TransformContext] = None) -> TransformResult[U]:
        """
        Transform the input value according to the transformer's rules.
        
        Args:
            value: The input value to transform
            context: Optional context for the transformation
            
        Returns:
            TransformResult containing either the transformed value or an error
        """
        return TransformResult(value=None, error=NotImplementedError("Transform method not implemented"))

    def validate(self, value: T) -> bool:
        """
        Validate the input value.
        
        Args:
            value: The input value to validate
            
        Returns:
            True if the value is valid for this transformer, False otherwise
        """
        return True
        
    def get_validation_errors(self, value: T) -> List[str]:
        """
        Get list of validation errors for the input value.
        
        Args:
            value: The input value to validate
            
        Returns:
            List of validation error messages, empty if valid
        """
        return []

class ExtractorProtocol(Protocol):
    """Protocol defining the interface for data extractors."""
    
    def extract_data(self, data: Any, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data according to the given pattern.
        
        Args:
            data: The data to extract from (HTML, JSON, etc.)
            pattern: The pattern describing what to extract
            
        Returns:
            Dictionary of extracted data
        """
        return {}
        
    def extract_property(self, data: Any, property_def: Dict[str, Any]) -> Any:
        """
        Extract a single property from data.
        
        Args:
            data: The data to extract from
            property_def: The property definition
            
        Returns:
            The extracted property value
        """
        return None

class ValidatorProtocol(Protocol[T]):
    """Protocol defining the interface for validators."""
    
    def validate(self, value: T) -> bool:
        """
        Validate the input value.
        
        Args:
            value: The input value to validate
            
        Returns:
            True if the value is valid, False otherwise
        """
        return True

    def get_validation_errors(self, value: T) -> List[str]:
        """
        Get list of validation errors for the input value.
        
        Args:
            value: The input value to validate
            
        Returns:
            List of validation error messages, empty if valid
        """
        return []
        
    def validate_with_context(self, value: T, context: Dict[str, Any]) -> bool:
        """
        Validate the input value with additional context.
        
        Args:
            value: The input value to validate
            context: Additional context for validation
            
        Returns:
            True if the value is valid, False otherwise
        """
        return self.validate(value)

class PluginProtocol(Protocol):
    """Protocol defining the interface for plugins."""
    
    @property
    def name(self) -> str:
        """Get the plugin name."""
        return "base_plugin"
        
    @property
    def transformers(self) -> Dict[str, Any]:
        """Get the transformers provided by this plugin."""
        return {}
        
    def initialize(self) -> None:
        """Initialize the plugin."""
        pass
        
    def cleanup(self) -> None:
        """Clean up the plugin."""
        pass
        
    def get_transformer(self, name: str, params: Dict[str, Any]) -> Optional[TransformerProtocol]:
        """
        Get a transformer by name with the given parameters.
        
        Args:
            name: The transformer name
            params: Parameters for the transformer
            
        Returns:
            The transformer instance or None if not found
        """
        return None

# Pattern types
Pattern = Dict[str, Any]
Selector = Union[str, Dict[str, Union[str, List[str]]]]
