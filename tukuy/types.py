from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from dataclasses import dataclass

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

# Pattern types
Pattern = Dict[str, Any]
