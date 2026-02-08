# numerical.py
# =========================================
# Tukuy Numerical transformation plugin
# =========================================
"""Numerical transformation implementations."""
from __future__ import annotations

import re
import math
import random
from decimal import Decimal, InvalidOperation
from statistics import mean, median, stdev
from typing import Optional, Union, Any, List, Mapping

from ...base import ChainableTransformer
from ...plugins.base import TransformerPlugin, register_transformer
from ...types import TransformContext
from ...exceptions import ValidationError

# Shorthand number constants and utilities
_SUFFIX_MAP: Mapping[str, int] = {
    "k": 1_000,
    "m": 1_000_000,
    "b": 1_000_000_000,
    "t": 1_000_000_000_000,
    "bn": 1_000_000_000,
    "mm": 1_000_000,           # common in ES: "2.5mm" = 2.5 million
    "tr": 1_000_000_000_000,
}

_NUM_STRIP_RE = re.compile(r"[,\s_]")
_CURRENCY_PREFIX = tuple("$\u20ac\u00a3\u00a5\u20bf\u20bd\u20b9\u20a9\u20ab\u20aa\u20b4\u20a6\u20b2\u20b5\u20a1\u20b1\u20ba\u20b8")
_NUMBER_RE = re.compile(
    r"""
    ^\s*
    (?P<sign>[-+]?)\s*
    (?P<body>
        (?:\d+(?:[,_]\d+)*|\d*\.\d+|\d+)
        (?:e[-+]?\d+)?     # scientific notation
    )
    \s*(?P<suffix>[a-z]{1,2})?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

def _strip_currency_prefix(s: str) -> str:
    """Remove currency symbol prefix from string if present."""
    return s[1:].lstrip() if s and s[0] in _CURRENCY_PREFIX else s

def parse_shorthand_number(
    value: Any,
    *,
    allow_currency: bool = True,
    allow_percent: bool = True,
    percent_base: float = 1.0,
    as_decimal: bool | None = None,
) -> int | float | Decimal:
    """
    Parse numbers with shorthand notations.

    Description:
        Parses numeric values with various formats including currency symbols,
        separators, scientific notation, suffixes, and percentages.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        value: Input value (str/num)
        allow_currency: Accept currency prefix
        allow_percent: Accept '%' suffix
        percent_base: Base for percentage (1.0 => fraction, 100 => 12% -> 12)
        as_decimal: True => Decimal, False => float/int, None => infer

    Returns:
        int | float | Decimal (collapses to int if exact integer)

    Raises:
        ValueError: If the input is invalid or cannot be parsed

    Notes:
        - Handles currency symbols: $1,200
        - Handles separators: 1_200 / 1,200
        - Handles scientific notation: 1e3
        - Handles suffixes: k, m, b, t, bn, mm, tr (2.5m -> 2_500_000)
        - Handles percentages: '12%' (multiplies by percent_base, default 1.0 => 0.12)

    Example:
        ```python
        # Basic number parsing
        result = parse_shorthand_number("1.23k")
        assert result == 1230

        # Currency handling
        result = parse_shorthand_number("$1,234.56")
        assert result == 1234.56

        # Percentage handling
        result = parse_shorthand_number("12%", percent_base=1.0)
        assert result == 0.12

        # Scientific notation
        result = parse_shorthand_number("1.23e3")
        assert result == 1230.0

        # Decimal output
        from decimal import Decimal
        result = parse_shorthand_number("1.23", as_decimal=True)
        assert isinstance(result, Decimal)
        assert result == Decimal("1.23")
        ```
    """
    if value is None:
        raise ValueError("None value invalid")

    if isinstance(value, (int, float, Decimal)):
        return value

    s = str(value).strip()
    if not s:
        raise ValueError("Empty string")

    if allow_currency:
        s = _strip_currency_prefix(s)

    # Handle percentage
    is_percent = False
    if allow_percent and s.endswith("%"):
        is_percent = True
        s = s[:-1].strip()

    core = _NUM_STRIP_RE.sub("", s)
    m = _NUMBER_RE.match(core)
    if not m:
        raise ValueError(f"Invalid number format: {value!r}")

    body = m.group("body")
    suffix = (m.group("suffix") or "").lower()

    multiplier = 1
    if suffix:
        multiplier = _SUFFIX_MAP.get(suffix)
        if multiplier is None:
            raise ValueError(f"Unknown numeric suffix '{suffix}' in {value!r}")

    want_decimal = as_decimal is True or (as_decimal is None and ("." in body or "e" in body.lower()))
    ctor = Decimal if want_decimal else float

    try:
        num = ctor(body)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid number '{body}': {e}") from e

    num = num * (ctor(multiplier) if multiplier != 1 else 1)

    if is_percent:
        num = num * ctor(percent_base) / ctor(100)

    if ctor is float:
        if abs(num - round(num)) < 1e-12:
            return int(round(num))
        return num
    else:
        if num == num.to_integral_value():
            return int(num)
        return num

@register_transformer("int")
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

@register_transformer("float")
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

@register_transformer("round", decimals=0)
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

    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        try:
            # Convert to float first to ensure we return a float, not a Decimal
            return float(round(float(value), self.decimals))
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid number for rounding: {str(e)}", value)

@register_transformer("currency_convert")
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
        - For example, to convert USD to EUR with rate 0.85, $100 USD becomes 85 EUR
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

    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        if self.rate is None:
            raise ValidationError("Exchange rate not provided", value)

        try:
            return float(value) * float(self.rate)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid currency value: {str(e)}", value)

@register_transformer("unit_convert")
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

        result = pipeline.transform(20)  # 20C
        assert result.value == 68.0  # 68F

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

    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        if self.rate is None:
            raise ValidationError("Conversion rate not provided", value)

        try:
            return float(value) * float(self.rate)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid unit value: {str(e)}", value)

@register_transformer("math_operation")
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
        'divide': lambda x, y: x / y if y != 0 else float('inf'),
    }

    def __init__(self, name: str, operation: str = 'add', operand: Union[int, float, Decimal] = 0):
        super().__init__(name)
        if operation not in self.OPERATIONS:
            raise ValueError(f"Invalid operation '{operation}'. Must be one of: {', '.join(self.OPERATIONS.keys())}")
        self.operation = operation
        self.operand = operand

    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        try:
            result = self.OPERATIONS[self.operation](float(value), float(self.operand))
            if math.isinf(result):
                raise ValidationError("Division by zero", value)
            return result
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid numeric value: {str(e)}", value)

@register_transformer("extract_numbers")
class ExtractNumbersTransformer(ChainableTransformer[str, list]):
    """
    Description:
        A transformer that extracts all numbers from text input. Handles both
        integer and decimal numbers.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer

    Returns:
        list[str]: List of extracted number strings

    Raises:
        ValidationError: If the input is not a string

    Notes:
        - Extracts both integer and decimal numbers
        - Returns numbers as strings to preserve original format
        - Does not handle scientific notation or special number formats

    Example:
        ```python
        transformer = ExtractNumbersTransformer("extract_nums")

        # Basic extraction
        result = transformer.transform("A=12.3, B=9")
        assert result.value == ['12.3', '9']

        # Multiple numbers
        result = transformer.transform("Price: $123.45, Qty: 5")
        assert result.value == ['123.45', '5']

        # No numbers
        result = transformer.transform("No numbers here")
        assert result.value == []
        ```
    """
    def __init__(self, name: str):
        super().__init__(name)
        self.pattern = re.compile(r"\d+(?:\.\d+)?")

    def _transform(self, value: str, context: TransformContext = None) -> list:
        return self.pattern.findall(value)

@register_transformer("abs")
class AbsTransformer(ChainableTransformer[float, float]):
    """
    Description:
        A transformer that computes the absolute value of a number.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer

    Returns:
        float: The absolute value of the input

    Raises:
        ValidationError: If the input is not a numeric type

    Notes:
        - Supports integers, floats, and Decimal inputs
        - Always returns a float value

    Example:
        ```python
        transformer = AbsTransformer("abs")

        # Positive number
        result = transformer.transform(5.5)
        assert result.value == 5.5

        # Negative number
        result = transformer.transform(-10.2)
        assert result.value == 10.2

        # Zero
        result = transformer.transform(0)
        assert result.value == 0.0
        ```
    """
    def validate(self, value) -> bool:
        return isinstance(value, (int, float, Decimal))

    def _transform(self, value, context=None):
        return abs(float(value))

@register_transformer("floor")
class FloorTransformer(ChainableTransformer[float, int]):
    """
    Description:
        A transformer that rounds a number down to the nearest integer.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer

    Returns:
        int: The floor value of the input

    Raises:
        ValidationError: If the input is not a numeric type

    Notes:
        - Supports integers, floats, and Decimal inputs
        - Always returns an integer value
        - Uses math.floor() for consistent behavior

    Example:
        ```python
        transformer = FloorTransformer("floor")

        # Basic floor
        result = transformer.transform(3.7)
        assert result.value == 3

        # Negative number
        result = transformer.transform(-2.3)
        assert result.value == -3

        # Integer input
        result = transformer.transform(5)
        assert result.value == 5
        ```
    """
    def validate(self, value) -> bool:
        return isinstance(value, (int, float, Decimal))

    def _transform(self, value, context=None):
        return math.floor(float(value))

@register_transformer("ceil")
class CeilTransformer(ChainableTransformer[float, int]):
    """
    Description:
        A transformer that rounds a number up to the nearest integer.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer

    Returns:
        int: The ceiling value of the input

    Raises:
        ValidationError: If the input is not a numeric type

    Notes:
        - Supports integers, floats, and Decimal inputs
        - Always returns an integer value
        - Uses math.ceil() for consistent behavior

    Example:
        ```python
        transformer = CeilTransformer("ceil")

        # Basic ceiling
        result = transformer.transform(3.2)
        assert result.value == 4

        # Negative number
        result = transformer.transform(-2.8)
        assert result.value == -2

        # Integer input
        result = transformer.transform(5)
        assert result.value == 5
        ```
    """
    def validate(self, value) -> bool:
        return isinstance(value, (int, float, Decimal))

    def _transform(self, value, context=None):
        return math.ceil(float(value))

@register_transformer("clamp")
class ClampTransformer(ChainableTransformer[float, float]):
    """
    Description:
        A transformer that clamps a number between minimum and maximum values.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        min_value (Optional[float]): Minimum allowed value (inclusive)
        max_value (Optional[float]): Maximum allowed value (inclusive)

    Returns:
        float: The clamped value

    Raises:
        ValidationError: If the input is not a numeric type

    Notes:
        - Supports integers, floats, and Decimal inputs
        - Always returns a float value
        - If min_value is None, no lower bound is applied
        - If max_value is None, no upper bound is applied

    Example:
        ```python
        transformer = ClampTransformer("clamp", min_value=0, max_value=100)

        # Within range
        result = transformer.transform(50)
        assert result.value == 50.0

        # Below minimum
        result = transformer.transform(-10)
        assert result.value == 0.0

        # Above maximum
        result = transformer.transform(150)
        assert result.value == 100.0
        ```
    """
    def __init__(self, name: str, min_value=None, max_value=None):
        super().__init__(name)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value) -> bool:
        return isinstance(value, (int, float, Decimal))

    def _transform(self, value, context=None):
        v = float(value)
        if self.min_value is not None:
            v = max(v, self.min_value)
        if self.max_value is not None:
            v = min(v, self.max_value)
        return v

@register_transformer("scale", src_min=0, src_max=1, dst_min=0, dst_max=1)
class ScaleTransformer(ChainableTransformer[float, float]):
    """
    Description:
        A transformer that scales a value from one range to another.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        src_min (float): Source range minimum value
        src_max (float): Source range maximum value
        dst_min (float): Destination range minimum value
        dst_max (float): Destination range maximum value

    Returns:
        float: The scaled value

    Raises:
        ValidationError: If the input is not a numeric type

    Notes:
        - Supports integers, floats, and Decimal inputs
        - Always returns a float value
        - If src_max equals src_min, returns dst_min to avoid division by zero
        - Linear scaling using the formula: dst_min + (v - src_min) * (dst_max - dst_min) / (src_max - src_min)

    Example:
        ```python
        # Scale 0-100 to 0-1
        transformer = ScaleTransformer(
            "percentage_to_ratio",
            src_min=0,
            src_max=100,
            dst_min=0,
            dst_max=1
        )
        result = transformer.transform(50)
        assert result.value == 0.5

        # Scale temperature Celsius to Fahrenheit
        c_to_f = ScaleTransformer(
            "celsius_to_fahrenheit",
            src_min=0,
            src_max=100,
            dst_min=32,
            dst_max=212
        )
        result = c_to_f.transform(20)
        assert result.value == 68.0
        ```
    """
    def __init__(self, name: str, src_min=0, src_max=1, dst_min=0, dst_max=1):
        super().__init__(name)
        self.src_min, self.src_max = src_min, src_max
        self.dst_min, self.dst_max = dst_min, dst_max

    def validate(self, value) -> bool:
        return isinstance(value, (int, float, Decimal))

    def _transform(self, value, context=None):
        v = float(value)
        if self.src_max == self.src_min:
            return self.dst_min
        return self.dst_min + (v - self.src_min) * (self.dst_max - self.dst_min) / (self.src_max - self.src_min)

@register_transformer("stats")
class StatsTransformer(ChainableTransformer[list, dict]):
    """
    Description:
        A transformer that computes basic statistical measures over a list of numbers.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer

    Returns:
        dict: Dictionary containing statistical measures

    Raises:
        ValidationError: If the input is not a list or tuple

    Notes:
        - Supports lists/tuples containing integers, floats, and Decimals
        - Non-numeric values in the input are ignored
        - Returns empty dict if no valid numbers found
        - Standard deviation (stdev) only included if 2+ numbers
        - All results are converted to float

    Example:
        ```python
        transformer = StatsTransformer("stats")

        # Basic stats
        result = transformer.transform([1, 2, 3, 4, 5])
        assert result.value == {
            "count": 5,
            "sum": 15.0,
            "mean": 3.0,
            "median": 3.0,
            "min": 1.0,
            "max": 5.0,
            "stdev": 1.5811388300841898
        }

        # Mixed numeric types
        result = transformer.transform([1, 2.5, Decimal('3.5')])
        assert result.value["mean"] == 2.3333333333333335

        # Ignore non-numeric values
        result = transformer.transform([1, "two", 3.0])
        assert result.value["count"] == 2
        ```
    """
    def validate(self, value) -> bool:
        return isinstance(value, (list, tuple))

    def _transform(self, value, context=None):
        nums = [float(v) for v in value if isinstance(v, (int, float, Decimal))]
        if not nums:
            return {}
        out = {
            "count": len(nums),
            "sum": sum(nums),
            "mean": mean(nums),
            "median": median(nums),
            "min": min(nums),
            "max": max(nums),
        }
        if len(nums) > 1:
            out["stdev"] = stdev(nums)
        return out

@register_transformer("format_number", decimals=2)
class FormatNumberTransformer(ChainableTransformer[float, str]):
    """
    Description:
        A transformer that formats numbers with thousand separators and fixed
        decimal places.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        decimals (int): Number of decimal places (default: 2)

    Returns:
        str: The formatted number string

    Raises:
        ValidationError: If the input is not a numeric type

    Notes:
        - Supports integers, floats, and Decimal inputs
        - Uses comma as thousand separator
        - Rounds to specified decimal places
        - Always shows specified decimals even if zero

    Example:
        ```python
        transformer = FormatNumberTransformer("format", decimals=2)

        # Basic formatting
        result = transformer.transform(1234.5678)
        assert result.value == "1,234.57"

        # Integer with decimals
        result = transformer.transform(1000)
        assert result.value == "1,000.00"

        # Different decimal places
        precise = FormatNumberTransformer("precise", decimals=3)
        result = precise.transform(1234.5678)
        assert result.value == "1,234.568"
        ```
    """
    def __init__(self, name: str, decimals: int = 2):
        super().__init__(name)
        self.decimals = decimals

    def validate(self, value) -> bool:
        return isinstance(value, (int, float, Decimal))

    def _transform(self, value, context=None):
        return f"{float(value):,.{self.decimals}f}"

@register_transformer("random", min_value=0, max_value=1)
class RandomNumberTransformer(ChainableTransformer[None, float]):
    """
    Description:
        A transformer that generates random numbers within a specified range.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        min_value (float): Minimum value (inclusive)
        max_value (float): Maximum value (inclusive)
        seed (Optional[int]): Random seed for reproducibility

    Returns:
        float: A random number in [min_value, max_value]

    Notes:
        - Uses Python's random.uniform() for float generation
        - Setting seed enables reproducible results
        - Input value is ignored (can be None)

    Example:
        ```python
        # Basic random number
        transformer = RandomNumberTransformer(
            "random",
            min_value=0,
            max_value=1
        )
        result = transformer.transform(None)
        assert 0 <= result.value <= 1

        # With seed for reproducibility
        seeded = RandomNumberTransformer(
            "seeded_random",
            min_value=1,
            max_value=10,
            seed=42
        )
        result1 = seeded.transform(None)
        result2 = seeded.transform(None)
        assert result1.value != result2.value  # Different calls

        # Custom range
        dice = RandomNumberTransformer(
            "d6",
            min_value=1,
            max_value=6
        )
        result = dice.transform(None)
        assert 1 <= result.value <= 6
        ```
    """
    def __init__(self, name: str, min_value=0, max_value=1, seed=None):
        super().__init__(name)
        self.min_value, self.max_value = min_value, max_value
        if seed is not None:
            random.seed(seed)

    def validate(self, value) -> bool:
        return True

    def _transform(self, value, context=None):
        return random.uniform(self.min_value, self.max_value)

@register_transformer("pow", exponent=2.0)
class PowerTransformer(ChainableTransformer[float, float]):
    """
    Description:
        A transformer that raises a number to a specified power.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        exponent (float): Power to raise the input to (default: 2.0)

    Returns:
        float: The input raised to the specified power

    Raises:
        ValidationError: If the input is not a numeric type

    Notes:
        - Supports integers, floats, and Decimal inputs
        - Always returns a float value
        - Uses Python's built-in power operator (**)

    Example:
        ```python
        # Square (default)
        transformer = PowerTransformer("square")
        result = transformer.transform(3)
        assert result.value == 9.0

        # Cube
        cube = PowerTransformer("cube", exponent=3)
        result = cube.transform(2)
        assert result.value == 8.0

        # Square root (power of 0.5)
        sqrt = PowerTransformer("sqrt", exponent=0.5)
        result = sqrt.transform(16)
        assert result.value == 4.0
        ```
    """
    def __init__(self, name: str, exponent: float = 2.0):
        super().__init__(name)
        self.exponent = exponent

    def validate(self, value) -> bool:
        return isinstance(value, (int, float, Decimal))

    def _transform(self, value, context=None):
        return float(value) ** float(self.exponent)

@register_transformer("sqrt")
class SqrtTransformer(ChainableTransformer[float, float]):
    """
    Description:
        A transformer that computes the square root of a number.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer

    Returns:
        float: The square root of the input

    Raises:
        ValidationError: If the input is not a numeric type
        ValueError: If the input is negative

    Notes:
        - Supports integers, floats, and Decimal inputs
        - Always returns a float value
        - Only works with non-negative numbers
        - Uses math.sqrt() for computation

    Example:
        ```python
        transformer = SqrtTransformer("sqrt")

        # Basic square root
        result = transformer.transform(16)
        assert result.value == 4.0

        # Decimal number
        result = transformer.transform(2)
        assert result.value == 1.4142135623730951

        # Zero
        result = transformer.transform(0)
        assert result.value == 0.0

        # Negative number raises error
        try:
            transformer.transform(-1)
            assert False, "Should raise ValueError"
        except ValueError:
            pass
        ```
    """
    def validate(self, value) -> bool:
        return isinstance(value, (int, float, Decimal))

    def _transform(self, value, context=None):
        v = float(value)
        if v < 0:
            raise ValueError("sqrt not defined for negative values")
        return math.sqrt(v)

@register_transformer("log")
class LogTransformer(ChainableTransformer[float, float]):
    """
    Description:
        A transformer that computes the logarithm of a number with optional base.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        base (Optional[float]): Logarithm base (None for natural log)

    Returns:
        float: The logarithm of the input

    Raises:
        ValidationError: If the input is not a numeric type
        ValueError: If the input is not positive

    Notes:
        - Supports integers, floats, and Decimal inputs
        - Always returns a float value
        - Only works with positive numbers
        - Uses math.log() with optional base
        - Natural logarithm (base e) used when base is None

    Example:
        ```python
        # Natural logarithm
        transformer = LogTransformer("ln")
        result = transformer.transform(2.718281828459045)
        assert abs(result.value - 1.0) < 1e-10

        # Base 10 logarithm
        log10 = LogTransformer("log10", base=10)
        result = log10.transform(100)
        assert result.value == 2.0

        # Base 2 logarithm
        log2 = LogTransformer("log2", base=2)
        result = log2.transform(8)
        assert result.value == 3.0

        # Non-positive input raises error
        try:
            transformer.transform(0)
            assert False, "Should raise ValueError"
        except ValueError:
            pass
        ```
    """
    def __init__(self, name: str, base: float | None = None):
        super().__init__(name)
        self.base = base

    def validate(self, value) -> bool:
        return isinstance(value, (int, float, Decimal))

    def _transform(self, value, context=None):
        v = float(value)
        if v <= 0:
            raise ValueError("log requires v > 0")
        if self.base is None:
            return math.log(v)
        return math.log(v, self.base)

@register_transformer("shorthand_number", allow_currency=True, allow_percent=True, percent_base=1.0)
class ShorthandNumberTransformer(ChainableTransformer[Any, int | float]):
    """
    Description:
        A transformer that parses shorthand number notations into numeric values.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        allow_currency (bool): Accept currency symbols (default: True)
        allow_percent (bool): Accept percentage notation (default: True)
        percent_base (float): Base for percentage conversion (default: 1.0)

    Returns:
        Union[int, float]: The parsed numeric value

    Raises:
        ValidationError: If the input cannot be parsed

    Notes:
        - Handles currency symbols, separators, suffixes (k/m/b/t)
        - Returns int for exact integers, float otherwise
        - Percentage handling depends on percent_base
        - Already numeric inputs returned as-is

    Example:
        ```python
        transformer = ShorthandNumberTransformer("parse")

        # Basic parsing
        result = transformer.transform("1.23k")
        assert result.value == 1230

        # Currency
        result = transformer.transform("$1,234.56")
        assert result.value == 1234.56

        # Percentage
        result = transformer.transform("50%")
        assert result.value == 0.5  # with default percent_base=1.0

        # Different percent base
        percent = ShorthandNumberTransformer(
            "percent",
            percent_base=100
        )
        result = percent.transform("50%")
        assert result.value == 50.0
        ```
    """
    def __init__(self, name: str, allow_currency=True, allow_percent=True, percent_base=1.0):
        super().__init__(name)
        self.allow_currency = allow_currency
        self.allow_percent = allow_percent
        self.percent_base = percent_base

    def validate(self, value) -> bool:
        return True

    def _transform(self, value, context=None):
        if isinstance(value, (int, float)):
            return value
        out = parse_shorthand_number(
            value,
            allow_currency=self.allow_currency,
            allow_percent=self.allow_percent,
            percent_base=float(self.percent_base),
            as_decimal=False,
        )
        return float(out) if isinstance(out, Decimal) else out

@register_transformer("shorthand_decimal", allow_currency=True, allow_percent=True, percent_base=1.0)
class ShorthandDecimalTransformer(ChainableTransformer[Any, Decimal | int]):
    """
    Description:
        A transformer that parses shorthand number notations into Decimal values.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer
        allow_currency (bool): Accept currency symbols (default: True)
        allow_percent (bool): Accept percentage notation (default: True)
        percent_base (float): Base for percentage conversion (default: 1.0)

    Returns:
        Union[Decimal, int]: The parsed numeric value

    Raises:
        ValidationError: If the input cannot be parsed

    Notes:
        - Similar to ShorthandNumberTransformer but preserves decimal precision
        - Returns int for exact integers, Decimal otherwise
        - Handles currency symbols, separators, suffixes (k/m/b/t)
        - Already Decimal/int inputs returned as-is

    Example:
        ```python
        transformer = ShorthandDecimalTransformer("parse_decimal")

        # Basic parsing
        result = transformer.transform("1.23")
        assert isinstance(result.value, Decimal)
        assert result.value == Decimal("1.23")

        # Currency
        result = transformer.transform("$1,234.56")
        assert result.value == Decimal("1234.56")

        # Percentage
        result = transformer.transform("50%")
        assert result.value == Decimal("0.5")  # with default percent_base=1.0

        # Integer collapse
        result = transformer.transform("1000")
        assert isinstance(result.value, int)
        assert result.value == 1000
        ```
    """
    def __init__(self, name: str, allow_currency=True, allow_percent=True, percent_base=1.0):
        super().__init__(name)
        self.allow_currency = allow_currency
        self.allow_percent = allow_percent
        self.percent_base = percent_base

    def validate(self, value) -> bool:
        return True

    def _transform(self, value, context=None):
        if isinstance(value, (Decimal, int)):
            return value
        return parse_shorthand_number(
            value,
            allow_currency=self.allow_currency,
            allow_percent=self.allow_percent,
            percent_base=float(self.percent_base),
            as_decimal=True,
        )

@register_transformer("percentage_calc")
class PercentageCalculator(ChainableTransformer[Union[int, float, Decimal], float]):
    """
    Description:
        A transformer that converts numeric values to percentages. Can handle
        integers, floats, and Decimal objects as input.

    Version: v1
    Status: Production
    Last Updated: 2024-03-24

    Args:
        name (str): Unique identifier for this transformer

    Returns:
        float: The calculated percentage value

    Raises:
        ValidationError: If the input value is not a numeric type or cannot be converted

    Notes:
        - Converts decimal fractions to percentages (e.g., 0.5 -> 50.0)
        - Preserves existing percentage values (e.g., 50 -> 50.0)
        - Handles integers, floats, and Decimal inputs
        - Always returns a float value

    Example:
        ```python
        # Convert decimal to percentage
        transformer = PercentageCalculator("to_percent")
        result = transformer.transform(0.75)
        assert result.value == 75.0

        # Handle integer input
        result = transformer.transform(50)
        assert result.value == 50.0

        # Handle Decimal input
        from decimal import Decimal
        result = transformer.transform(Decimal('0.25'))
        assert result.value == 25.0

        # Chain with other transformers
        round_transformer = RoundTransformer("round", decimals=1)
        pipeline = transformer.chain(round_transformer)

        result = pipeline.transform(0.333)
        assert result.value == 33.3
        ```
    """

    def _transform(self, value: Union[int, float, Decimal], context: Optional[TransformContext] = None) -> float:
        try:
            float_value = float(value)
            # If value is less than or equal to 1, assume it's a decimal fraction
            if abs(float_value) <= 1:
                return float_value * 100
            return float_value
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid value for percentage calculation: {str(e)}", value)


class NumericalTransformersPlugin(TransformerPlugin):
    """Plugin providing comprehensive numerical transformation capabilities."""
    def __init__(self):
        super().__init__("numerical")

    @property
    def transformers(self):
        return self._auto_transformers()
