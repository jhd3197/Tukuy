import pytest

def test_basic_text_transforms(transformer):
    # Test strip
    assert transformer.transform(" hello ", ["strip"]) == "hello"
    
    # Test lowercase
    assert transformer.transform("HELLO", ["lowercase"]) == "hello"
    
    # Test uppercase
    assert transformer.transform("hello", ["uppercase"]) == "HELLO"
    
    # Test title case
    assert transformer.transform("hello world", ["title_case"]) == "Hello World"
    
    # Test camel case
    assert transformer.transform("hello world", ["camel_case"]) == "helloWorld"
    
    # Test snake case
    assert transformer.transform("Hello World", ["snake_case"]) == "hello_world"

def test_chained_text_transforms(transformer):
    # Test multiple transformations
    text = " HELLO WORLD! "
    result = transformer.transform(text, [
        "strip",
        "lowercase",
        {"function": "truncate", "length": 5}
    ])
    assert result == "hello..."

def test_slugify(transformer):
    # Test slugify with special characters
    text = "Hello, World! This is a Test"
    assert transformer.transform(text, ["slugify"]) == "hello-world-this-is-a-test"

def test_text_replacements(transformer):
    # Test replace
    text = "hello world"
    result = transformer.transform(text, [{
        "function": "replace",
        "from": "world",
        "to": "there"
    }])
    assert result == "hello there"

def test_regex_transforms(transformer):
    # Test regex with pattern
    text = "The price is $123.45"
    result = transformer.transform(text, [{
        "function": "regex",
        "pattern": r"\$(\d+\.\d+)"
    }])
    assert result == "123.45"

def test_template_transform(transformer):
    # Test template with regex
    text = "Name: John, Age: 30"
    transforms = [
        {
            "function": "regex",
            "pattern": r"Name: (.*), Age: (\d+)",
            "template": "{1} is {2} years old"
        }
    ]
    assert transformer.transform(text, transforms) == "John is 30 years old"
