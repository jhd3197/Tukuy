from abc import ABC, abstractmethod
import re
from typing import Any, Dict, Generic, List, Optional, TypeVar
from logging import getLogger

from .types import TransformContext, TransformOptions, TransformResult, T, U
from .exceptions import TransformerError, ValidationError, TransformationError

logger = getLogger(__name__)

class BaseTransformer(Generic[T, U], ABC):
    """
    Abstract base class for all transformers.
    
    Provides common functionality and defines the interface that all transformers
    must implement.
    
    Type Parameters:
        T: The input type that this transformer accepts
        U: The output type that this transformer produces
    """
    
    def __init__(self, name: str, options: Optional[TransformOptions] = None):
        """
        Initialize the transformer.
        
        Args:
            name: Unique identifier for this transformer
            options: Configuration options for this transformer
        """
        self.name = name
        self.options = options or TransformOptions()
        self._validate_options()
    
    def _validate_options(self) -> None:
        """Validate the transformer options."""
        # Subclasses should override this if they need specific option validation
        pass
    
    @abstractmethod
    def validate(self, value: T) -> bool:
        """
        Validate the input value.
        
        Args:
            value: The value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def _transform(self, value: T, context: Optional[TransformContext] = None) -> U:
        """
        Internal transformation method that subclasses must implement.
        
        Args:
            value: The value to transform
            context: Optional context data for the transformation
            
        Returns:
            The transformed value
            
        Raises:
            TransformationError: If the transformation fails
        """
        raise NotImplementedError
    
    def transform(self, value: T, context: Optional[TransformContext] = None, **kwargs) -> TransformResult[U]:
        """
        Public method to transform a value with error handling.
        
        Args:
            value: The value to transform
            context: Optional context data for the transformation
            **kwargs: Additional keyword arguments for the transformation
            
        Returns:
            TransformResult containing either the transformed value or an error
        """
        try:
            if not self.validate(value):
                raise ValidationError(f"Invalid input for transformer {self.name}", value)
            
            logger.debug(f"Transforming value with {self.name}: {value}")
            result = self._transform(value, context)
            logger.debug(f"Transformation result: {result}")
            
            return TransformResult(value=result)
            
        except TransformerError as e:
            logger.error(f"Transformation error in {self.name}: {str(e)}")
            return TransformResult(error=e)
        except Exception as e:
            logger.exception(f"Unexpected error in transformer {self.name}")
            error = TransformationError(
                f"Unexpected error in transformer {self.name}: {str(e)}",
                value,
                self.name
            )
            return TransformResult(error=error)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()

class ChainableTransformer(BaseTransformer[T, U]):
    """
    A transformer that can be chained with other transformers.
    
    Allows for creating pipelines of transformations where the output of one
    transformer becomes the input to the next.
    """
    
    def __init__(
        self,
        name: str,
        next_transformer: Optional[BaseTransformer] = None,
        options: Optional[TransformOptions] = None
    ):
        super().__init__(name, options)
        self.next_transformer = next_transformer
    
    def chain(self, next_transformer: BaseTransformer) -> 'ChainableTransformer':
        """
        Chain this transformer with another transformer.
        
        Args:
            next_transformer: The next transformer in the chain
            
        Returns:
            self for method chaining
        """
        self.next_transformer = next_transformer
        return self
    
    def transform(self, value: T, context: Optional[TransformContext] = None, **kwargs) -> TransformResult:
        """
        Transform the value and pass it through the chain.
        
        Args:
            value: The value to transform
            context: Optional context data for the transformation
            **kwargs: Additional keyword arguments for the transformation
            
        Returns:
            TransformResult containing either the final transformed value or an error
        """
        result = super().transform(value, context, **kwargs)
        
        if result.failed or not self.next_transformer:
            return result
            
        return self.next_transformer.transform(result.value, context, **kwargs)

class CompositeTransformer(BaseTransformer[T, U]):
    """
    A transformer that combines multiple transformers into a single unit.
    
    Useful for creating complex transformations from simpler ones.
    """
    
    def __init__(
        self,
        name: str,
        transformers: List[BaseTransformer],
        options: Optional[TransformOptions] = None
    ):
        super().__init__(name, options)
        self.transformers = transformers
    
    def validate(self, value: Any) -> bool:
        """Validate input through all contained transformers."""
        return all(t.validate(value) for t in self.transformers)
    
    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> Any:
        """Apply all transformations in sequence."""
        current_value = value
        current_context = context or {}
        
        for transformer in self.transformers:
            result = transformer.transform(current_value, current_context)
            if result.failed:
                raise result.error
            current_value = result.value
            
        return current_value

class RegexTransformer(ChainableTransformer[str, str]):
    """Apply regex pattern to text."""
    
    def __init__(self, name: str, pattern: str, template: Optional[str] = None):
        super().__init__(name)
        self.pattern = pattern
        self.template = template
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        match = re.search(self.pattern, value)
        if not match:
            return value
            
        if context is not None:
            context['last_regex_match'] = match
            
        if self.template:
            result = self.template
            for i, group in enumerate(match.groups(), 1):
                result = result.replace(f'{{{i}}}', str(group or ''))
            return result
            
        return match.group(1) if match.groups() else match.group(0)

class ReplaceTransformer(ChainableTransformer[str, str]):
    """Replace text."""
    
    def __init__(self, name: str, old: str, new: str):
        super().__init__(name)
        self.old = old
        self.new = new
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return value.replace(self.old, self.new)

class CoreToolsTransformer(BaseTransformer[Any, Any]):
    """
    Coordinates the application of multiple transformations using existing transformers.
    
    This transformer takes a value and a list of transform operations, creates the
    appropriate transformers, and chains them together to produce the final result.
    """
    
    def __init__(self):
        super().__init__("tools")
        
    def validate(self, value: Any) -> bool:
        return True  # Accept any value type
        
    def _transform(self, value: Any, transforms: List[Dict[str, Any]]) -> Any:
        current_value = value
        
        for transform in transforms:
            func = transform.get('function')
            
            if func == 'regex':
                transformer = RegexTransformer(
                    'regex',
                    pattern=transform['pattern'],
                    template=transform.get('template')
                )
            elif func == 'replace':
                transformer = ReplaceTransformer(
                    'replace',
                    old=transform['find'],
                    new=transform['replace']
                )
            elif func == 'average':
                if not isinstance(current_value, list):
                    raise ValidationError("Average requires a list of numbers", value)
                total = sum(float(x) for x in current_value)
                return round(total / len(current_value), 2)
            else:
                raise ValidationError(f"Unknown transform function: {func}", value)
                
            result = transformer.transform(current_value)
            if result.failed:
                raise result.error
            current_value = result.value
            
        return current_value
