"""Async base classes for transformers — mirrors sync base.py with async transform()."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional
from logging import getLogger

from .types import TransformContext, TransformOptions, TransformResult, T, U
from .exceptions import TransformerError, ValidationError, TransformationError

logger = getLogger(__name__)


class AsyncBaseTransformer(Generic[T, U], ABC):
    """Async counterpart of :class:`BaseTransformer`.

    Subclasses implement :meth:`_transform` as an ``async def``.  The public
    :meth:`transform` method is also async — it validates, awaits
    ``_transform``, and wraps the result in a :class:`TransformResult`.
    """

    def __init__(self, name: str, options: Optional[TransformOptions] = None):
        self.name = name
        self.options = options or TransformOptions()
        self._validate_options()

    def _validate_options(self) -> None:
        pass

    @abstractmethod
    def validate(self, value: T) -> bool:
        raise NotImplementedError

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
    """Async counterpart of :class:`ChainableTransformer`.

    Chains are followed by awaiting the next transformer's ``transform``.
    The next transformer can be either sync or async — if sync, it is called
    normally.
    """

    def __init__(
        self,
        name: str,
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

        # Support chaining with both async and sync transformers
        next_result = self.next_transformer.transform(result.value, context, **kwargs)
        if asyncio.iscoroutine(next_result):
            return await next_result
        return next_result


class AsyncCompositeTransformer(AsyncBaseTransformer[T, U]):
    """Async counterpart of :class:`CompositeTransformer`.

    Runs a list of transformers in sequence, awaiting async ones and calling
    sync ones normally.
    """

    def __init__(
        self,
        name: str,
        transformers: List,
        options: Optional[TransformOptions] = None,
    ):
        super().__init__(name, options)
        self.transformers = transformers

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
