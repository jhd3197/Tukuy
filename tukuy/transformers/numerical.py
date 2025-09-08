"""Numerical transformation implementations."""

import re
from decimal import Decimal
from typing import Optional, Union, Any


from ..base import ChainableTransformer
from ..types import TransformContext
from ..exceptions import ValidationError

class IntegerTransformer(ChainableTransformer[str, int]):
    """
    Description:
        A transformer that converts various input types to integers with optional
        minimum and maximum value validation. Handles string inputs by removing
        non-digit characters before conversion.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        min_value (Optional[int]): Minimum allowed value (inclusive)
        max_value (Optional[int]): Maximum allowed value (inclusive)
    
    Returns:
        int: The converted integer value
    
    Raises:
        ValidationError: If the input cannot be converted to an integer or
            if the result is outside the min/max range
    
    Notes:
        - For string inputs, removes all non-digit characters except minus sign
        - For float inputs, truncates decimal portion
        - Validates against min_value and max_value after conversion
    
    Example:
        ```python
        # Basic integer conversion
        transformer = IntegerTransformer("to_int")
        result = transformer.transform("123")
        assert result.value == 123
        
        # Handle string with non-digit characters
        result = transformer.transform("$1,234")
        assert result.value == 1234
        
        # Convert float to integer
        result = transformer.transform(45.67)
        assert result.value == 45
        
        # With range validation
        bounded = IntegerTransformer(
            "bounded",
            min_value=0,
            max_value=100
        )
        result = bounded.transform("50")
        assert result.value == 50
        
        # Chain with other transformers
        multiply = MathOperationTransformer(
            "multiply_by_2",
            operation="multiply",
            operand=2
        )
        pipeline = transformer.chain(multiply)
        
        result = pipeline.transform("10")
        assert result.value == 20.0  # Note: MathOperation returns float
        ```
    """
    
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
    """
    Description:
        A transformer that converts various input types to floating-point numbers with
        optional minimum and maximum value validation. Handles string inputs by removing
        non-numeric characters before conversion.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        min_value (Optional[float]): Minimum allowed value (inclusive)
        max_value (Optional[float]): Maximum allowed value (inclusive)
    
    Returns:
        float: The converted floating-point value
    
    Raises:
        ValidationError: If the input cannot be converted to a float or
            if the result is outside the min/max range
    
    Notes:
        - For string inputs, removes all non-numeric characters except minus sign and decimal point
        - Validates against min_value and max_value after conversion
        - Handles various numeric formats including currency and percentage strings
    
    Example:
        ```python
        # Basic float conversion
        transformer = FloatTransformer("to_float")
        result = transformer.transform("123.45")
        assert result.value == 123.45
        
        # Handle string with non-numeric characters
        result = transformer.transform("$1,234.56")
        assert result.value == 1234.56
        
        # Convert integer to float
        result = transformer.transform(42)
        assert result.value == 42.0
        
        # With range validation
        bounded = FloatTransformer(
            "bounded",
            min_value=0.0,
            max_value=100.0
        )
        result = bounded.transform("50.5")
        assert result.value == 50.5
        
        # Chain with other transformers
        round_transformer = RoundTransformer("round", decimals=1)
        pipeline = transformer.chain(round_transformer)
        
        result = pipeline.transform("123.456")
        assert result.value == 123.5
        ```
    """
    
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
    """
    Description:
        A transformer that rounds numeric values to a specified number of decimal places.
        Supports integers, floats, and Decimal objects as input.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        decimals (int): Number of decimal places to round to (default: 0)
    
    Returns:
        float: The rounded value as a float
    
    Raises:
        ValidationError: If the input value is not a numeric type or cannot be rounded
    
    Notes:
        - Uses Python's built-in round() function
        - Always returns a float, even when rounding to 0 decimal places
        - Follows standard rounding rules (round to even for tie-breaking)
    
    Example:
        ```python
        # Round to nearest integer
        transformer = RoundTransformer("round_int")
        result = transformer.transform(123.456)
        assert result.value == 123.0
        
        # Round to 2 decimal places
        precise = RoundTransformer("round_2dp", decimals=2)
        result = precise.transform(123.456)
        assert result.value == 123.46
        
        # Handle Decimal input
        from decimal import Decimal
        result = precise.transform(Decimal('123.456'))
        assert result.value == 123.46
        
        # Round negative numbers
        result = precise.transform(-123.456)
        assert result.value == -123.46
        
        # Chain with other transformers
        multiply = MathOperationTransformer(
            "multiply_by_100",
            operation="multiply",
            operand=100
        )
        pipeline = precise.chain(multiply)
        
        result = pipeline.transform(1.2345)
        assert result.value == 123.4  # 1.23 * 100 = 123.0
        ```
    """
    
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
    """
    Description:
        A transformer that converts currency values from one currency to another
        using a specified exchange rate. Supports integers, floats, and Decimal
        objects as input.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        rate (Optional[float]): Exchange rate to apply to the input value
    
    Returns:
        float: The converted currency value
    
    Raises:
        ValidationError: If the input value is not a numeric type, if the exchange
            rate is not provided, or if the conversion fails
    
    Notes:
        - Exchange rate should be the value of target currency per unit of source currency
        - For example, to convert USD to EUR with rate 0.85, $100 USD becomes €85 EUR
        - Always returns a float value
    
    Example:
        ```python
        # Convert USD to EUR (rate: 1 USD = 0.85 EUR)
        transformer = CurrencyConverter(
            "usd_to_eur",
            rate=0.85
        )
        result = transformer.transform(100)
        assert result.value == 85.0
        
        # Convert EUR to USD (rate: 1 EUR = 1.18 USD)
        eur_to_usd = CurrencyConverter(
            "eur_to_usd",
            rate=1.18
        )
        result = eur_to_usd.transform(50)
        assert result.value == 59.0
        
        # Handle Decimal input
        from decimal import Decimal
        result = transformer.transform(Decimal('123.45'))
        assert result.value == 104.9325  # 123.45 * 0.85
        
        # Chain with other transformers
        round_transformer = RoundTransformer("round", decimals=2)
        pipeline = transformer.chain(round_transformer)
        
        result = pipeline.transform(100)
        assert result.value == 85.0
        ```
    """
    
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
    """
    Description:
        A transformer that converts values between different units of measurement
        using a specified conversion rate. Supports integers, floats, and Decimal
        objects as input.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        rate (Optional[float]): Conversion rate to apply to the input value
    
    Returns:
        float: The converted value
    
    Raises:
        ValidationError: If the input value is not a numeric type, if the conversion
            rate is not provided, or if the conversion fails
    
    Notes:
        - Conversion rate should be the value of target unit per unit of source unit
        - For example, to convert miles to kilometers with rate 1.60934, 10 miles becomes 16.0934 km
        - Always returns a float value
    
    Example:
        ```python
        # Convert miles to kilometers (1 mile = 1.60934 km)
        transformer = UnitConverter(
            "miles_to_km",
            rate=1.60934
        )
        result = transformer.transform(10)
        assert result.value == 16.0934
        
        # Convert Celsius to Fahrenheit (special formula: C * 1.8 + 32)
        # For this case, use MathOperationTransformer after UnitConverter
        celsius_to_fahrenheit = UnitConverter(
            "celsius_to_fahrenheit_step1",
            rate=1.8
        )
        add_32 = MathOperationTransformer(
            "add_32",
            operation="add",
            operand=32
        )
        pipeline = celsius_to_fahrenheit.chain(add_32)
        
        result = pipeline.transform(20)  # 20°C
        assert result.value == 68.0  # 68°F
        
        # Convert kilograms to pounds (1 kg = 2.20462 lbs)
        kg_to_lbs = UnitConverter(
            "kg_to_lbs",
            rate=2.20462
        )
        result = kg_to_lbs.transform(5)
        assert result.value == 11.0231  # 5 kg = 11.0231 lbs
        
        # Chain with other transformers
        round_transformer = RoundTransformer("round", decimals=1)
        pipeline = kg_to_lbs.chain(round_transformer)
        
        result = pipeline.transform(5)
        assert result.value == 11.0
        ```
    """
    
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
    """
    Description:
        A transformer that performs basic mathematical operations (add, subtract,
        multiply, divide) on numeric values. Supports integers, floats, and Decimal
        objects as input.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        operation (str): The operation to perform ('add', 'subtract', 'multiply', 'divide')
        operand (Union[int, float, Decimal]): The value to use in the operation
    
    Returns:
        float: The result of the mathematical operation
    
    Raises:
        ValidationError: If the input value is not a numeric type, if the operation
            is invalid, or if division by zero is attempted
        ValueError: If an invalid operation is specified during initialization
    
    Notes:
        - Supported operations: 'add', 'subtract', 'multiply', 'divide'
        - Division by zero will raise a ValidationError
        - Always returns a float value
    
    Example:
        ```python
        # Addition
        transformer = MathOperationTransformer(
            "add_10",
            operation="add",
            operand=10
        )
        result = transformer.transform(5)
        assert result.value == 15.0
        
        # Subtraction
        subtract = MathOperationTransformer(
            "subtract_5",
            operation="subtract",
            operand=5
        )
        result = subtract.transform(10)
        assert result.value == 5.0
        
        # Multiplication
        multiply = MathOperationTransformer(
            "multiply_by_2",
            operation="multiply",
            operand=2
        )
        result = multiply.transform(5)
        assert result.value == 10.0
        
        # Division
        divide = MathOperationTransformer(
            "divide_by_2",
            operation="divide",
            operand=2
        )
        result = divide.transform(10)
        assert result.value == 5.0
        
        # Chain with other transformers
        round_transformer = RoundTransformer("round", decimals=1)
        pipeline = divide.chain(round_transformer)
        
        result = pipeline.transform(10.5)
        assert result.value == 5.2  # (10.5 / 2) = 5.25, rounded to 5.2
        ```
    """
    
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
    """
    Description:
        A transformer that converts decimal values to percentages by multiplying by 100.
        Supports integers, floats, and Decimal objects as input.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
    
    Returns:
        float: The percentage value (input * 100)
    
    Raises:
        ValidationError: If the input value is not a numeric type or cannot be converted
    
    Notes:
        - Multiplies the input value by 100
        - For example, 0.25 becomes 25.0
        - Always returns a float value
    
    Example:
        ```python
        # Basic percentage conversion
        transformer = PercentageCalculator("to_percent")
        
        # Convert decimal to percentage
        result = transformer.transform(0.75)
        assert result.value == 75.0
        
        # Handle integer input
        result = transformer.transform(1)
        assert result.value == 100.0
        
        # Handle Decimal input
        from decimal import Decimal
        result = transformer.transform(Decimal('0.5'))
        assert result.value == 50.0
        
        # Chain with other transformers
        round_transformer = RoundTransformer("round", decimals=1)
        pipeline = transformer.chain(round_transformer)
        
        result = pipeline.transform(0.333)
        assert result.value == 33.3  # 0.333 * 100 = 33.3
        ```
    """
    
    def validate(self, value: Any) -> bool:
        return isinstance(value, (int, float, Decimal))
    
    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        try:
            return float(value) * 100.0
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid value for percentage calculation: {str(e)}", value)
