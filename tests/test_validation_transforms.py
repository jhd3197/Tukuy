import pytest

def test_email_validation(transformer):
    # Test valid email
    assert transformer.transform("test@example.com", ["email_validator"]) == "test@example.com"
    
    # Test invalid email
    assert transformer.transform("invalid-email", ["email_validator"]) is None
    
    # Test email with spaces
    assert transformer.transform(" test@example.com ", ["email_validator"]) == "test@example.com"

def test_phone_formatting(transformer):
    # Test standard 10-digit number
    assert transformer.transform("1234567890", ["phone_formatter"]) == "(123) 456-7890"
    
    # Test number with formatting
    assert transformer.transform("(123) 456-7890", ["phone_formatter"]) == "(123) 456-7890"
    
    # Test number with other characters
    assert transformer.transform("123-456-7890", ["phone_formatter"]) == "(123) 456-7890"

def test_credit_card_validation(transformer):
    # Test valid card (using test numbers)
    assert transformer.transform("4532015112830366", ["credit_card_check"]) == "4532015112830366"
    
    # Test invalid number
    assert transformer.transform("1234567890123456", ["credit_card_check"]) is None
    
    # Test with formatting
    assert transformer.transform("4532-0151-1283-0366", ["credit_card_check"]) == "4532-0151-1283-0366"

def test_boolean_conversion(transformer):
    # Test true values
    assert transformer.transform("yes", ["bool"]) is True
    assert transformer.transform("1", ["bool"]) is True
    assert transformer.transform("true", ["bool"]) is True
    
    # Test false values
    assert transformer.transform("no", ["bool"]) is False
    assert transformer.transform("0", ["bool"]) is False
    assert transformer.transform("false", ["bool"]) is False
    
    # Test invalid values
    assert transformer.transform("maybe", ["bool"]) is None

def test_type_enforcement(transformer):
    # Test int enforcement
    assert transformer.transform("123.45", [{"function": "type_enforcer", "type": "int"}]) == 123
    
    # Test float enforcement
    assert transformer.transform("123.45", [{"function": "type_enforcer", "type": "float"}]) == 123.45
    
    # Test str enforcement
    assert transformer.transform(123, [{"function": "type_enforcer", "type": "str"}]) == "123"
    
    # Test bool enforcement
    assert transformer.transform(1, [{"function": "type_enforcer", "type": "bool"}]) is True