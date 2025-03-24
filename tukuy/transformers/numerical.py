"""Numerical transformation implementations."""

import re
from decimal import Decimal
from typing import Optional, Union, Any

from ..base import ChainableTransformer
from ..types import TransformContext
from ..exceptions import ValidationError

class IntegerTransformer(ChainableTransformer[str, int]):
    """Convert value to integer."""
    
    def __init__(self, name: str, min_value: Optional[int] = None, max_value: Optional[int] = None):
        super().__init__(name)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> bool:
        return True
    
    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> int:
        try:
            if isinstance(value, str):
                # Remove non-digit characters except minus sign
                value = re.sub(r'[^\d-]', '', value)
                
            result = int(float(value))
            
            if self.min_value is not None and result < self.min_value:
                raise ValidationError(f"Value {result} is less than minimum {self.min_value}", value)
                
            if self.max_value is not None and result > self.max_value:
                raise ValidationError(f"Value {result} is greater than maximum {self.max_value}", value)
                
            return result
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid integer: {str(e)}", value)

class FloatTransformer(ChainableTransformer[str, float]):
    """Convert value to float."""
    
    def __init__(self, name: str, min_value: Optional[float] = None, max_value: Optional[float] = None):
        super().__init__(name)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> bool:
        return True
    
    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> float:
        try:
            if isinstance(value, str):
                # Remove non-digit characters except minus sign and decimal point
                value = re.sub(r'[^\d.-]', '', value)
                
            result = float(value)
            
            if self.min_value is not None and result < self.min_value:
                raise ValidationError(f"Value {result} is less than minimum {self.min_value}", value)
                
            if self.max_value is not None and result > self.max_value:
                raise ValidationError(f"Value {result} is greater than maximum {self.max_value}", value)
                
            return result
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid float: {str(e)}", value)

class RoundTransformer(ChainableTransformer[Union[int, float, Decimal], float]):
    """Round a number to specified number of decimal places."""
    
    def __init__(self, name: str, decimals: int = 0):
        super().__init__(name)
        self.decimals = decimals
    
    def validate(self, value: Any) -> bool:
        return isinstance(value, (int, float, Decimal))
    
    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        try:
            # Convert to float first to ensure we return a float, not a Decimal
            return float(round(float(value), self.decimals))
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid number for rounding: {str(e)}", value)

class CurrencyConverter(ChainableTransformer[Union[int, float, Decimal], float]):
    """Convert currency using exchange rate."""
    
    def __init__(self, name: str, rate: Optional[float] = None):
        super().__init__(name)
        self.rate = rate
    
    def validate(self, value: Any) -> bool:
        return isinstance(value, (int, float, Decimal))
    
    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        if self.rate is None:
            raise ValidationError("Exchange rate not provided", value)
            
        try:
            return float(value) * float(self.rate)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid currency value: {str(e)}", value)

class UnitConverter(ChainableTransformer[Union[int, float, Decimal], float]):
    """Convert units using conversion rate."""
    
    def __init__(self, name: str, rate: Optional[float] = None):
        super().__init__(name)
        self.rate = rate
    
    def validate(self, value: Any) -> bool:
        return isinstance(value, (int, float, Decimal))
    
    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        if self.rate is None:
            raise ValidationError("Conversion rate not provided", value)
            
        try:
            return float(value) * float(self.rate)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid unit value: {str(e)}", value)

class MathOperationTransformer(ChainableTransformer[Union[int, float, Decimal], float]):
    """Perform math operation on a value."""
    
    OPERATIONS = {
        'add': lambda x, y: x + y,
        'subtract': lambda x, y: x - y,
        'multiply': lambda x, y: x * y,
        'divide': lambda x, y: x / y if y != 0 else None,
    }
    
    def __init__(self, name: str, operation: str = 'add', operand: Union[int, float, Decimal] = 0):
        super().__init__(name)
        self.operation = operation.lower()
        self.operand = operand
        
        if self.operation not in self.OPERATIONS:
            raise ValueError(f"Invalid operation: {operation}")
    
    def validate(self, value: Any) -> bool:
        return isinstance(value, (int, float, Decimal))
    
    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        try:
            value = float(value)
            operand = float(self.operand)
            
            result = self.OPERATIONS[self.operation](value, operand)
            if result is None:
                raise ValidationError("Division by zero", value)
                
            return result
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid value for math operation: {str(e)}", value)

class PercentageCalculator(ChainableTransformer[Union[int, float, Decimal], float]):
    """Convert decimal to percentage."""
    
    def validate(self, value: Any) -> bool:
        return isinstance(value, (int, float, Decimal))
    
    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        try:
            return float(value) * 100.0
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid value for percentage calculation: {str(e)}", value)
