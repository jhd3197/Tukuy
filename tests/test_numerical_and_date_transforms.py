import pytest
from datetime import datetime, date

def test_numerical_transforms(transformer):
    # Test rounding
    assert transformer.transform(123.456, [{"function": "round", "decimals": 2}]) == 123.46
    
    # Test currency conversion
    assert transformer.transform(100, [{"function": "currency_convert", "rate": 0.85}]) == 85.0
    
    # Test unit conversion
    assert transformer.transform(10, [{"function": "unit_convert", "rate": 2.54}]) == 25.4
    
    # Test percentage calculation
    assert transformer.transform(0.75, ["percentage_calc"]) == 75.0

def test_math_operations(transformer):
    # Test basic math operations
    value = 10
    
    # Addition
    assert transformer.transform(value, [{"function": "math_operation", "operation": "add", "operand": 5}]) == 15
    
    # Subtraction
    assert transformer.transform(value, [{"function": "math_operation", "operation": "subtract", "operand": 3}]) == 7
    
    # Multiplication
    assert transformer.transform(value, [{"function": "math_operation", "operation": "multiply", "operand": 2}]) == 20
    
    # Division
    assert transformer.transform(value, [{"function": "math_operation", "operation": "divide", "operand": 2}]) == 5

def test_date_transforms(transformer):
    # Test date parsing
    date_str = "2023-03-24"
    result = transformer.transform(date_str, [{"function": "date", "format": "%Y-%m-%d"}])
    assert isinstance(result, datetime)
    assert result.year == 2023
    assert result.month == 3
    assert result.day == 24

def test_age_calculation(transformer):
    # Test age calculation (note: this test might need adjustment based on current date)
    birth_date = "1990-01-01"
    age = transformer.transform(birth_date, [{"function": "age_calc", "format": "%Y-%m-%d"}])
    assert isinstance(age, int)
    assert age > 0

def test_duration_calculation(transformer):
    # Test duration between dates
    start_date = "2023-01-01"
    transforms = [{
        "function": "duration_calc",
        "format": "%Y-%m-%d",
        "end": "2023-02-01"
    }]
    duration = transformer.transform(start_date, transforms)
    assert duration == 31  # Days between Jan 1 and Feb 1

def test_number_extraction(transformer):
    # Test extracting numbers from text
    text = "The price is $123.45 and quantity is 42 units"
    numbers = transformer.transform(text, ["extract_numbers"])
    assert "123.45" in numbers
    assert "42" in numbers