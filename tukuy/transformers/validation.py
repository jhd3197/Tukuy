"""Validation transformation implementations."""

import re
from typing import Optional, Any, Union
from decimal import Decimal

from ..base import ChainableTransformer
from ..types import TransformContext
from ..exceptions import ValidationError

class BooleanTransformer(ChainableTransformer[str, bool]):
    """Convert string to boolean."""
    
    TRUE_VALUES = {'true', '1', 'yes', 'y', 't'}
    FALSE_VALUES = {'false', '0', 'no', 'n', 'f'}
    
    def validate(self, value: str) -> bool:
        if isinstance(value, bool):
            return True
        return isinstance(value, str)
    
    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> Optional[bool]:
        if isinstance(value, bool):
            return value
            
        val_str = str(value).strip().lower()
        if val_str in self.TRUE_VALUES:
            return True
        if val_str in self.FALSE_VALUES:
            return False
        return None

class EmailValidator(ChainableTransformer[str, str]):
    """Validate email address."""
    
    def __init__(self, name: str, allowed_domains: Optional[list] = None):
        super().__init__(name)
        self.allowed_domains = allowed_domains
        self.pattern = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> Optional[str]:
        value = value.strip()
        if not self.pattern.match(value):
            return None
            
        if self.allowed_domains:
            domain = value.split('@')[1]
            if domain not in self.allowed_domains:
                return None
                
        return value

class PhoneFormatter(ChainableTransformer[str, str]):
    """Format phone number."""
    
    def __init__(self, name: str, format: str = '({area}) {prefix}-{line}'):
        super().__init__(name)
        self.format = format
        self.digit_pattern = re.compile(r'\D')
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        digits = self.digit_pattern.sub('', value)
        
        if len(digits) == 11 and digits[0] == '1':
            digits = digits[1:]
            
        if len(digits) != 10:
            raise ValidationError("Invalid phone number length", value)
            
        return self.format.format(
            area=digits[:3],
            prefix=digits[3:6],
            line=digits[6:]
        )

class CreditCardValidator(ChainableTransformer[str, str]):
    """Validate credit card number using Luhn algorithm."""
    
    def __init__(self, name: str, mask: bool = False):
        super().__init__(name)
        self.mask = mask
        self.digit_pattern = re.compile(r'\D')
    
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> Optional[str]:
        # Keep original format
        original = value
        # Extract digits
        digits = self.digit_pattern.sub('', value)
        
        if len(digits) < 13 or len(digits) > 19:
            return None
            
        # Luhn algorithm
        sum_ = 0
        alt = False
        for d in digits[::-1]:
            d = int(d)
            if alt:
                d *= 2
                if d > 9:
                    d -= 9
            sum_ += d
            alt = not alt
            
        if sum_ % 10 != 0:
            return None
            
        # Return masked or original number
        if self.mask:
            visible = 4
            masked_len = len(digits) - (2 * visible)
            return f"{digits[:visible]}{'*' * masked_len}{digits[-visible:]}"
            
        return original

class TypeEnforcer(ChainableTransformer[Any, Any]):
    """Enforce type conversion."""
    
    def __init__(self, name: str, target_type: str):
        super().__init__(name)
        self.target_type = target_type
    
    def validate(self, value: Any) -> bool:
        return True
    
    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> Any:
        try:
            if self.target_type == 'int':
                if isinstance(value, str):
                    # Handle float strings
                    return int(float(value))
                return int(value)
            elif self.target_type == 'float':
                return float(value)
            elif self.target_type == 'str':
                return str(value)
            elif self.target_type == 'bool':
                if isinstance(value, str):
                    value = value.lower()
                    if value in ('true', '1', 'yes', 'y'):
                        return True
                    if value in ('false', '0', 'no', 'n'):
                        return False
                return bool(value)
            elif self.target_type == 'decimal':
                if isinstance(value, str):
                    return Decimal(value)
                return Decimal(str(value))
            else:
                raise ValidationError(f"Unsupported type: {self.target_type}", value)
        except (ValueError, TypeError, ArithmeticError) as e:
            raise ValidationError(f"Type conversion failed: {str(e)}", value)
