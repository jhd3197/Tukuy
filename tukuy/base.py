from abc import ABC, abstractmethod
import re
from typing import Any, Generic, List, Optional
from logging import getLogger

from .types import TransformContext, TransformOptions, TransformResult, T, U
from .exceptions import TransformerError, ValidationError, TransformationError

logger = getLogger(__name__)

class BaseTransformer(Generic[T, U], ABC):
    """
    Description:
        Abstract base class for all transformers. Provides common functionality and defines
        the interface that all transformers must implement.

    Version: v2
    Status: Production

    Type Parameters:
        T: The input type that this transformer accepts
        U: The output type that this transformer produces
    """

    def __init__(self, name: str = "", options: Optional[TransformOptions] = None):
        self.name = name or self.__class__.__name__
        self.options = options or TransformOptions()
        self._input_type = self._resolve_input_type()
        self._validate_options()

    def _resolve_input_type(self):
        """Extract T from ChainableTransformer[str, str] for auto-validation."""
        import typing
        for base in getattr(self.__class__, '__orig_bases__', []):
            args = getattr(base, '__args__', None)
            if args and len(args) >= 1:
                arg = args[0]
                # Skip typing.Any and other non-concrete types
                if arg is typing.Any:
                    return None
                if isinstance(arg, type):
                    return arg
        return None

    def _validate_options(self) -> None:
        """Validate the transformer options."""
        pass

    def validate(self, value: T) -> bool:
        """
        Validate the input value. Default implementation uses auto-isinstance
        from generic type parameters. Override for custom validation.
        """
        if self._input_type is None:
            return True
        return isinstance(value, self._input_type)

    @abstractmethod
    def _transform(self, value: T, context: Optional[TransformContext] = None) -> U:
        """
        Internal transformation method that subclasses must implement.
        """
        raise NotImplementedError

    def transform(self, value: T, context: Optional[TransformContext] = None, **kwargs) -> TransformResult[U]:
        """
        Public method to transform a value with error handling.
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
        A transformer that can be chained with other transformers.
    """

    def __init__(
        self,
        name: str = "",
        next_transformer: Optional[BaseTransformer] = None,
        options: Optional[TransformOptions] = None
    ):
        super().__init__(name, options)
        self.next_transformer = next_transformer

    def chain(self, next_transformer: BaseTransformer) -> 'ChainableTransformer':
        self.next_transformer = next_transformer
        return self

    def transform(self, value: T, context: Optional[TransformContext] = None, **kwargs) -> TransformResult:
        result = super().transform(value, context, **kwargs)

        if result.failed or not self.next_transformer:
            return result

        return self.next_transformer.transform(result.value, context, **kwargs)

class CompositeTransformer(BaseTransformer[T, U]):
    """
    Description:
        A transformer that combines multiple transformers into a single unit.
    """

    def __init__(
        self,
        name: str = "",
        transformers: List[BaseTransformer] = None,
        options: Optional[TransformOptions] = None
    ):
        super().__init__(name, options)
        self.transformers = transformers or []

    def validate(self, value: Any) -> bool:
        return all(t.validate(value) for t in self.transformers)

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> Any:
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
        A transformer that applies a regular expression pattern to text.
    """

    def __init__(self, name: str = "", pattern: str = "", template: Optional[str] = None):
        super().__init__(name)
        self.pattern = pattern
        self.template = template

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
    """

    def __init__(self, name: str = "", old: str = "", new: str = ""):
        super().__init__(name)
        self.old = old
        self.new = new

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        return value.replace(self.old, self.new)
