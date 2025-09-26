from abc import ABC, abstractmethod
import re
from typing import Any, Dict, Generic, List, Optional, TypeVar
from logging import getLogger

from .types import TransformContext, TransformOptions, TransformResult, T, U
from .exceptions import TransformerError, ValidationError, TransformationError

logger = getLogger(__name__)

class BaseTransformer(Generic[T, U], ABC):
    """
    Description:
        Abstract base class for all transformers. Provides common functionality and defines 
        the interface that all transformers must implement.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Type Parameters:
        T: The input type that this transformer accepts
        U: The output type that this transformer produces
    
    Methods:
        __init__(name: str, options: Optional[TransformOptions] = None):
            Initialize the transformer with a ``name`` and optional configuration.
            
        validate(value: T) -> bool:
            Validate if the input value is acceptable for this transformer.
            
        transform(value: T, context: Optional[TransformContext] = None) -> TransformResult[U]:
            Transform the input value according to the transformer's rules.
            
        _transform(value: T, context: Optional[TransformContext] = None) -> U:
            Internal transformation method that subclasses must implement.
    
    Example::

        class NumberSquareTransformer(BaseTransformer[int, int]):
            def validate(self, value: int) -> bool:
                return isinstance(value, int)
            
            def _transform(self, value: int, context: Optional[TransformContext] = None) -> int:
                return value * value
        
        transformer = NumberSquareTransformer("square")
        result = transformer.transform(5)
        assert result.value == 25

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
    Description:
        A transformer that can be chained with other transformers. Allows for creating pipelines 
        of transformations where the output of one transformer becomes the input to the next.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Type Parameters:
        T: The input type that this transformer accepts
        U: The output type that this transformer produces
    
    Methods:
        __init__(name: str, next_transformer: Optional[BaseTransformer] = None, options: Optional[TransformOptions] = None):
            Initialize the transformer with a ``name``, optional next transformer, and configuration.
            
        chain(next_transformer: BaseTransformer) -> ChainableTransformer:
            Chain this transformer with another transformer.
            
        transform(value: T, context: Optional[TransformContext] = None) -> TransformResult:
            Transform the value and pass it through the chain.
    
    Example::

        # Create a pipeline that converts text to lowercase then strips whitespace
        lowercase = LowercaseTransformer("lowercase")
        strip = StripTransformer("strip")
        
        # Chain the transformers
        pipeline = lowercase.chain(strip)
        
        # Transform text through the pipeline
        result = pipeline.transform("  Hello World  ")
        assert result.value == "hello world"

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
    Description:
        A transformer that combines multiple transformers into a single unit. Useful for creating 
        complex transformations from simpler ones by composing multiple transformers together.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Type Parameters:
        T: The input type that this transformer accepts
        U: The output type that this transformer produces
    
    Methods:
        __init__(name: str, transformers: List[BaseTransformer], options: Optional[TransformOptions] = None):
            Initialize the transformer with a ``name``, list of transformers, and optional configuration.
            
        validate(value: Any) -> bool:
            Validate input through all contained transformers.
            
        _transform(value: Any, context: Optional[TransformContext] = None) -> Any:
            Apply all transformations in sequence.
    
    Example::

        # Create individual transformers
        lowercase = LowercaseTransformer("lowercase")
        strip = StripTransformer("strip")
        slugify = SlugifyTransformer("slugify")
        
        # Combine them into a composite transformer
        text_processor = CompositeTransformer(
            "text_processor",
            transformers=[lowercase, strip, slugify]
        )
        
        # Process text through all transformers
        result = text_processor.transform("  Hello World!  ")
        assert result.value == "hello-world"

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
    """
    Description:
        A transformer that applies a regular expression pattern to text and optionally 
        formats the result using a template.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        pattern (str): Regular expression pattern to match against the input text
        template (Optional[str]): Optional template for formatting the matched groups.
            Use {1}, {2}, etc. to reference captured groups.
    
    Returns:
        str: The transformed text after applying the regex pattern and template
    
    Raises:
        ValidationError: If the input value is not a string
        TransformationError: If the regex pattern is invalid
    
    Example::

        # Extract and format a date
        transformer = RegexTransformer(
            "date_format",
            pattern=r"(\d{4})-(\d{2})-(\d{2})",
            template="{2}/{3}/{1}"  # MM/DD/YYYY
        )
        
        result = transformer.transform("Date: 2024-03-24")
        assert result.value == "03/24/2024"
        
        # Simple pattern matching without template
        finder = RegexTransformer(
            "find_email",
            pattern=r"\b[\w\.-]+@[\w\.-]+\.\w+\b"
        )
        
        result = finder.transform("Contact: user@example.com")
        assert result.value == "user@example.com"

    """
    
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
    """
    Description:
        A transformer that replaces all occurrences of a specified text with new text.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        old (str): The text to find and replace
        new (str): The text to replace with
    
    Returns:
        str: The text with all occurrences of ``old`` replaced with ``new``
    
    Raises:
        ValidationError: If the input value is not a string
    
    Example::

        # Replace specific text
        transformer = ReplaceTransformer(
            "fix_typo",
            old="teh",
            new="the"
        )
        
        result = transformer.transform("teh quick brown fox")
        assert result.value == "the quick brown fox"
        
        # Chain with other transformers
        capitalize = UppercaseTransformer("uppercase")
        pipeline = transformer.chain(capitalize)
        
        result = pipeline.transform("teh quick brown fox")
        assert result.value == "THE QUICK BROWN FOX"

    """
    
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
    Description:
        Coordinates the application of multiple transformations using existing transformers.
        This transformer takes a value and a list of transform operations, creates the
        appropriate transformers, and chains them together to produce the final result.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Supported Operations:
        regex:
            pattern (str): Regular expression pattern to match
            template (Optional[str]): Optional template for formatting matches
            
        replace:
            find (str): Text to find
            replace (str): Text to replace with
            
        average:
            Calculates the average of a list of numbers
    
    Returns:
        Any: The transformed value after applying all operations
    
    Raises:
        ValidationError: If an unknown transform function is specified or if input validation fails
        TransformationError: If any transformation operation fails
    
    Example::

        transformer = CoreToolsTransformer()
        
        # Apply multiple transformations
        transforms = [
            {
                'function': 'regex',
                'pattern': r'(\d+)',
                'template': 'Number: {1}'
            },
            {
                'function': 'replace',
                'find': 'Number',
                'replace': 'Value'
            }
        ]
        
        result = transformer.transform("Age: 25", transforms)
        assert result.value == "Value: 25"
        
        # Calculate average
        numbers = [1, 2, 3, 4, 5]
        transforms = [{'function': 'average'}]
        result = transformer.transform(numbers, transforms)
        assert result.value == 3.0

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
                result = transformer.transform(current_value)
                if result.failed:
                    raise result.error
                current_value = result.value
            elif func == 'replace':
                transformer = ReplaceTransformer(
                    'replace',
                    old=transform['find'],
                    new=transform['replace']
                )
                result = transformer.transform(current_value)
                if result.failed:
                    raise result.error
                current_value = result.value
            elif func == 'average':
                if not isinstance(current_value, list):
                    raise ValidationError("Average requires a list of numbers", value)
                total = sum(float(x) for x in current_value)
                return round(total / len(current_value), 2)
            else:
                raise ValidationError(f"Unknown transform function: {func}", value)

        return current_value
