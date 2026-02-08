"""Async base classes for transformers — mirrors sync base.py with async transform()."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional
from logging import getLogger

from .types import TransformContext, TransformOptions, TransformResult, T, U
from .exceptions import TransformerError, ValidationError, TransformationError

logger = getLogger(__name__)


class AsyncBaseTransformer(Generic[T, U], ABC):
    """Async counterpart of :class:`BaseTransformer`."""

    def __init__(self, name: str = "", options: Optional[TransformOptions] = None):
        self.name = name or self.__class__.__name__
        self.options = options or TransformOptions()
        self._input_type = self._resolve_input_type()
        self._validate_options()

    def _resolve_input_type(self):
        """Extract T from generic type parameters for auto-validation."""
        import typing
        for base in getattr(self.__class__, '__orig_bases__', []):
            args = getattr(base, '__args__', None)
            if args and len(args) >= 1:
                arg = args[0]
                if arg is typing.Any:
                    return None
                if isinstance(arg, type):
                    return arg
        return None

    def _validate_options(self) -> None:
        pass

    def validate(self, value: T) -> bool:
        if self._input_type is None:
            return True
        return isinstance(value, self._input_type)

    @abstractmethod
    async def _transform(self, value: T, context: Optional[TransformContext] = None) -> U:
        raise NotImplementedError

    async def transform(self, value: T, context: Optional[TransformContext] = None, **kwargs) -> TransformResult[U]:
        try:
            if not self.validate(value):
                raise ValidationError(f"Invalid input for transformer {self.name}", value)

            logger.debug(f"Async transforming value with {self.name}: {value}")
            result = await self._transform(value, context)
            logger.debug(f"Async transformation result: {result}")

            return TransformResult(value=result)

        except TransformerError as e:
            logger.error(f"Transformation error in {self.name}: {str(e)}")
            return TransformResult(error=e)
        except Exception as e:
            logger.exception(f"Unexpected error in async transformer {self.name}")
            error = TransformationError(
                f"Unexpected error in transformer {self.name}: {str(e)}",
                value,
                self.name,
            )
            return TransformResult(error=error)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()


class AsyncChainableTransformer(AsyncBaseTransformer[T, U]):
    """Async counterpart of :class:`ChainableTransformer`."""

    def __init__(
        self,
        name: str = "",
        next_transformer=None,
        options: Optional[TransformOptions] = None,
    ):
        super().__init__(name, options)
        self.next_transformer = next_transformer

    def chain(self, next_transformer) -> "AsyncChainableTransformer":
        self.next_transformer = next_transformer
        return self

    async def transform(self, value: T, context: Optional[TransformContext] = None, **kwargs) -> TransformResult:
        result = await super().transform(value, context, **kwargs)

        if result.failed or not self.next_transformer:
            return result

        next_result = self.next_transformer.transform(result.value, context, **kwargs)
        if asyncio.iscoroutine(next_result):
            return await next_result
        return next_result


class AsyncCompositeTransformer(AsyncBaseTransformer[T, U]):
    """Async counterpart of :class:`CompositeTransformer`."""

    def __init__(
        self,
        name: str = "",
        transformers: List = None,
        options: Optional[TransformOptions] = None,
    ):
        super().__init__(name, options)
        self.transformers = transformers or []

    def validate(self, value: Any) -> bool:
        return all(t.validate(value) for t in self.transformers)

    async def _transform(self, value: Any, context: Optional[TransformContext] = None) -> Any:
        current_value = value
        current_context = context or {}

        for t in self.transformers:
            result = t.transform(current_value, current_context)
            if asyncio.iscoroutine(result):
                result = await result
            if result.failed:
                raise result.error
            current_value = result.value

        return current_value


__all__ = [
    "AsyncBaseTransformer",
    "AsyncChainableTransformer",
    "AsyncCompositeTransformer",
]
