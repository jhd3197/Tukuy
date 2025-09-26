"""Validation transformation implementations."""

import re
from typing import Optional, Any, Union
from decimal import Decimal


from ..base import ChainableTransformer
from ..types import TransformContext
from ..exceptions import ValidationError

class BooleanTransformer(ChainableTransformer[str, bool]):
    """
    Description:
        A transformer that converts string values to boolean based on common
        true/false representations. Handles various string formats like 'true',
        'yes', '1', etc.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
    
    Returns:
        Optional[bool]: The boolean value (True, False) or None if conversion fails
    
    Raises:
        ValidationError: If the input value is not a string or boolean
    
    Notes:
        - True values: 'true', '1', 'yes', 'y', 't' (case-insensitive)
        - False values: 'false', '0', 'no', 'n', 'f' (case-insensitive)
        - Returns None for values that don't match any of the above
        - Passes through boolean inputs unchanged
    
    Example:
        ```python
        # Basic boolean conversion
        transformer = BooleanTransformer("to_bool")
        
        # Convert string to boolean
        result = transformer.transform("yes")
        assert result.value is True
        
        result = transformer.transform("NO")
        assert result.value is False
        
        # Handle numeric strings
        result = transformer.transform("1")
        assert result.value is True
        
        result = transformer.transform("0")
        assert result.value is False
        
        # Handle actual booleans
        result = transformer.transform(True)
        assert result.value is True
        
        # Handle invalid values
        result = transformer.transform("maybe")
        assert result.value is None
        
        # Chain with other transformers
        default = DefaultValueTransformer("default_false", default_value=False)
        pipeline = transformer.chain(default)
        
        result = pipeline.transform("maybe")  # Invalid value
        assert result.value is False  # Uses default
        ```
    """
    
    TRUE_VALUES = {'true', '1', 'yes', 'y', 't', "on", "si", "sí", "verdadero"}
    FALSE_VALUES = {'false', '0', 'no', 'n', 'f', "off", "falso"}
    
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
    """
    Description:
        A transformer that validates email addresses using a simple regex pattern
        and optional domain restrictions. Returns the email if valid or None if invalid.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        allowed_domains (Optional[list]): List of allowed email domains (e.g., ['example.com'])
    
    Returns:
        Optional[str]: The validated email address or None if validation fails
    
    Raises:
        ValidationError: If the input value is not a string
    
    Notes:
        - Uses a basic regex pattern to validate email format
        - Optionally restricts to specific domains
        - Returns None for invalid emails instead of raising an exception
        - Trims whitespace from input
    
    Example:
        ```python
        # Basic email validation
        transformer = EmailValidator("validate_email")
        
        # Valid email
        result = transformer.transform("user@example.com")
        assert result.value == "user@example.com"
        
        # Invalid email
        result = transformer.transform("not-an-email")
        assert result.value is None
        
        # With domain restrictions
        restricted = EmailValidator(
            "company_email",
            allowed_domains=["company.com", "company.org"]
        )
        
        # Valid domain
        result = restricted.transform("user@company.com")
        assert result.value == "user@company.com"
        
        # Invalid domain
        result = restricted.transform("user@gmail.com")
        assert result.value is None
        
        # Chain with other transformers
        default = DefaultValueTransformer(
            "default_email",
            default_value="unknown@example.com"
        )
        pipeline = transformer.chain(default)
        
        result = pipeline.transform("invalid-email")
        assert result.value == "unknown@example.com"
        ```
    """
    
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
    """
    Description:
        A transformer that formats phone numbers according to a specified pattern.
        Extracts digits from the input and formats them into a standardized format.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        format (str): Format string with placeholders for area code, prefix, and line
            (default: '({area}) {prefix}-{line}')
    
    Returns:
        str: The formatted phone number
    
    Raises:
        ValidationError: If the input value is not a string or doesn't contain
            exactly 10 digits (or 11 digits starting with '1')
    
    Notes:
        - Removes all non-digit characters from input
        - Handles US/Canada numbers (10 digits)
        - Automatically strips leading '1' from 11-digit numbers
        - Format string can use {area}, {prefix}, and {line} placeholders
    
    Example:
        ```python
        # Basic phone formatting
        transformer = PhoneFormatter("format_phone")
        
        # Format with default pattern: (XXX) XXX-XXXX
        result = transformer.transform("1234567890")
        assert result.value == "(123) 456-7890"
        
        # Handle input with non-digit characters
        result = transformer.transform("(123) 456-7890")
        assert result.value == "(123) 456-7890"
        
        # Handle 11-digit number with leading 1
        result = transformer.transform("11234567890")
        assert result.value == "(123) 456-7890"
        
        # Custom format
        custom = PhoneFormatter(
            "custom_format",
            format="{area}-{prefix}-{line}"
        )
        result = custom.transform("1234567890")
        assert result.value == "123-456-7890"
        
        # Chain with other transformers
        uppercase = UppercaseTransformer("uppercase")
        pipeline = custom.chain(uppercase)
        
        result = pipeline.transform("1234567890")
        assert result.value == "123-456-7890"  # No effect on digits
        ```
    """
    
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
    """
    Description:
        A transformer that validates credit card numbers using the Luhn algorithm
        and optionally masks the number for security. Returns the validated number
        (original or masked) or None if invalid.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        mask (bool): Whether to mask the middle digits of the card number (default: False)
    
    Returns:
        Optional[str]: The validated credit card number (original or masked) or None if invalid
    
    Raises:
        ValidationError: If the input value is not a string
    
    Notes:
        - Removes all non-digit characters from input
        - Validates using the Luhn algorithm (checksum)
        - Checks that length is between 13-19 digits (standard card lengths)
        - When masking, shows first and last 4 digits, masks the rest
        - Returns None for invalid card numbers instead of raising an exception
    
    Example:
        ```python
        # Basic credit card validation
        transformer = CreditCardValidator("validate_cc")
        
        # Valid card (test number)
        result = transformer.transform("4111 1111 1111 1111")
        assert result.value == "4111 1111 1111 1111"  # Returns original format
        
        # Invalid card
        result = transformer.transform("1234 5678 9012 3456")
        assert result.value is None
        
        # With masking
        masked = CreditCardValidator("masked_cc", mask=True)
        
        # Valid card with masking
        result = masked.transform("4111-1111-1111-1111")
        assert result.value == "4111********1111"
        
        # Handle input with spaces, dashes, etc.
        result = masked.transform("4111 1111 1111 1111")
        assert result.value == "4111********1111"
        
        # Chain with other transformers
        default = DefaultValueTransformer(
            "default_cc",
            default_value="INVALID"
        )
        pipeline = transformer.chain(default)
        
        result = pipeline.transform("1234 5678 9012 3456")  # Invalid
        assert result.value == "INVALID"
        ```
    """
    
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
    """
    Description:
        A transformer that enforces type conversion of input values to a specified
        target type. Supports conversion to int, float, str, bool, and decimal types.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
            name (str): Unique identifier for this transformer
            ``target_type`` (str): The target type to convert to ('int', 'float', 'str', 'bool', 'decimal')
    
    Returns:
        Any: The converted value in the target type
    
    Raises:
        ValidationError: If the conversion fails or if the target type is not supported
    
    Notes:
        - Supported target types: 'int', 'float', 'str', 'bool', 'decimal'
        - For 'int' conversion of string values, handles float strings (e.g., "10.5" → 10)
        - For 'bool' conversion of string values, uses common true/false representations
        - For 'decimal' conversion, uses Python's Decimal type for precise decimal arithmetic
    
    Example:
        ```python
        # Integer conversion
        transformer = TypeEnforcer("to_int", ``target_type``="int")
        
        # Convert string to int
        result = transformer.transform("123")
        assert result.value == 123
        
        # Convert float to int
        result = transformer.transform(45.67)
        assert result.value == 45
        
        # Float conversion
        float_converter = TypeEnforcer("to_float", ``target_type``="float")
        
        # Convert string to float
        result = float_converter.transform("123.45")
        assert result.value == 123.45
        
        # Boolean conversion
        bool_converter = TypeEnforcer("to_bool", ``target_type``="bool")
        
        # Convert string to bool
        result = bool_converter.transform("yes")
        assert result.value is True
        
        # Decimal conversion
        decimal_converter = TypeEnforcer("to_decimal", ``target_type``="decimal")
        
        # Convert string to Decimal
        result = decimal_converter.transform("123.45")
        assert str(result.value) == "123.45"
        
        # Chain with other transformers
        round_transformer = RoundTransformer("round", decimals=2)
        pipeline = float_converter.chain(round_transformer)
        
        result = pipeline.transform("123.456")
        assert result.value == 123.46
        ```
    """
    
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
