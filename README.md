# 🌀 Tukuy

A flexible data transformation library with a plugin system for Python.

## 🚀 Overview

Tukuy (meaning "to transform" or "to become" in Quechua) is a powerful and extensible data transformation library that makes it easy to manipulate, validate, and extract data from various formats. With its plugin architecture, Tukuy provides a unified interface for working with text, HTML, JSON, dates, numbers, and more.

## ✨ Features

- 🧩 **Plugin System**: Easily extend functionality with custom plugins
- 🔄 **Chainable Transformers**: Compose multiple transformations in sequence
- 🧪 **Type-safe Transformations**: With built-in validation
- 🔍 **Pattern-based Data Extraction**: Extract structured data from HTML and JSON
- 🛡️ **Error Handling**: Comprehensive error handling with detailed messages

## 📦 Installation

```bash
pip install tukuy
```

## 🛠️ Basic Usage

```python
from tukuy import TukuyTransformer

# Create transformer
TUKUY = TukuyTransformer()

# Basic text transformation
text = " Hello World! "
result = TUKUY.transform(text, [
    "strip",
    "lowercase",
    {"function": "truncate", "length": 5}
])
print(result)  # "hello..."

# HTML transformation
html = "<div>Hello <b>World</b>!</div>"
result = TUKUY.transform(html, [
    "strip_html_tags",
    "lowercase"
])
print(result)  # "hello world!"

# Date transformation
date_str = "2023-01-01"
age = TUKUY.transform(date_str, [
    {"function": "age_calc"}
])
print(age)  # 1

# Validation
email = "test@example.com"
valid = TUKUY.transform(email, ["email_validator"])
print(valid)  # "test@example.com" or None if invalid
```

## 🔍 Pattern-based Extraction

Tukuy provides powerful pattern-based extraction capabilities for both HTML and JSON data.

### 🌐 HTML Extraction

```python
pattern = {
    "properties": [
        {
            "name": "title",
            "selector": "h1",
            "transform": ["strip", "lowercase"]
        },
        {
            "name": "links",
            "selector": "a",
            "attribute": "href",
            "type": "array"
        }
    ]
}

data = TUKUY.extract_html_with_pattern(html, pattern)
```

### 📋 JSON Extraction

```python
pattern = {
    "properties": [
        {
            "name": "user",
            "selector": "data.user",
            "properties": [
                {
                    "name": "name",
                    "selector": "fullName",
                    "transform": ["strip"]
                }
            ]
        }
    ]
}

data = TUKUY.extract_json_with_pattern(json_str, pattern)
```

## 🚀 Use Cases

Tukuy is designed to handle a wide range of data transformation scenarios:

- 🌐 **Web Scraping**: Extract structured data from HTML pages
- 📊 **Data Cleaning**: Normalize and validate data from various sources
- 🔄 **Format Conversion**: Transform data between different formats
- 📝 **Text Processing**: Apply complex text transformations
- 🔍 **Data Extraction**: Extract specific information from complex structures
- ✅ **Validation**: Ensure data meets specific criteria

## ⚡ Performance Tips

- 🔗 **Chain Transformations**: Use chained transformations to avoid intermediate objects
- 🧩 **Use Built-in Transformers**: Built-in transformers are optimized for performance
- 🔍 **Be Specific with Selectors**: More specific selectors are faster to process
- 🛠️ **Custom Transformers**: For performance-critical operations, create custom transformers
- 📦 **Batch Processing**: Process data in batches for better performance

## 🛡️ Error Handling

Tukuy provides comprehensive error handling with detailed error messages:

```python
from tukuy.exceptions import ValidationError, TransformationError, ParseError

try:
    result = TUKUY.transform(data, transformations)
except ValidationError as e:
    print(f"Validation failed: {e}")
except ParseError as e:
    print(f"Parsing failed: {e}")
except TransformationError as e:
    print(f"Transformation failed: {e}")
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. 💻 Make your changes
4. ✅ Run tests with `pytest`
5. 📝 Update documentation if needed
6. 🔄 Commit your changes (`git commit -m 'Add amazing feature'`)
7. 🚀 Push to the branch (`git push origin feature/amazing-feature`)
8. 🔍 Open a Pull Request

## 🧩 Plugin System Documentation

Tukuy's plugin system is the core of its extensibility. Below is a comprehensive list of all available plugins and their features.

### 📚 Built-in Plugins

#### 📝 Text Plugin (`text`)
- **Description**: Handles text manipulation and string operations
- **Key Transformers**:
  - `strip`: Remove leading/trailing whitespace
  - `lowercase`: Convert text to lowercase
  - `uppercase`: Convert text to uppercase
  - `truncate`: Truncate text to specified length
  - `replace`: Replace text patterns
  - `regex_replace`: Replace using regular expressions
  - `split`: Split text into array
  - `join`: Join array into text
  - `normalize`: Normalize text (remove diacritics)

#### 🌐 HTML Plugin (`html`)
- **Description**: Process and extract data from HTML content
- **Key Transformers**:
  - `strip_html_tags`: Remove HTML tags
  - `extract_text`: Extract text content
  - `select`: Extract content using CSS selectors
  - `extract_links`: Get all links from HTML
  - `extract_tables`: Extract tables to structured data
  - `clean_html`: Sanitize HTML content

#### 📅 Date Plugin (`date`)
- **Description**: Handle date parsing, formatting, and calculations
- **Key Transformers**:
  - `parse_date`: Convert string to date object
  - `format_date`: Format date to string
  - `age_calc`: Calculate age from date
  - `add_days`: Add days to date
  - `diff_days`: Calculate days between dates
  - `is_weekend`: Check if date is weekend
  - `to_timezone`: Convert between timezones

#### 🔢 Numerical Plugin (`numerical`)
- **Description**: Mathematical operations and number formatting
- **Key Transformers**:
  - `round`: Round number to decimals
  - `format_number`: Format with thousand separators
  - `to_currency`: Format as currency
  - `percentage`: Convert to percentage
  - `math_eval`: Evaluate mathematical expressions
  - `scale`: Scale number to range
  - `statistics`: Calculate basic statistics

#### ✅ Validation Plugin (`validation`)
- **Description**: Data validation and verification
- **Key Transformers**:
  - `email_validator`: Validate email addresses
  - `url_validator`: Validate URLs
  - `phone_validator`: Validate phone numbers
  - `length_validator`: Validate string length
  - `range_validator`: Validate number ranges
  - `regex_validator`: Validate against regex pattern
  - `type_validator`: Validate data types

#### 📋 JSON Plugin (`json`)
- **Description**: JSON manipulation and extraction
- **Key Transformers**:
  - `parse_json`: Parse JSON string
  - `stringify`: Convert to JSON string
  - `extract`: Extract values using JSON path
  - `flatten`: Flatten nested JSON
  - `merge`: Merge multiple JSON objects
  - `validate_schema`: Validate against JSON schema

### 🔌 Creating Custom Plugins

You can create custom plugins by extending the `TransformerPlugin` class:

```python
from tukuy.plugins import TransformerPlugin
from tukuy.base import ChainableTransformer

class ReverseTransformer(ChainableTransformer[str, str]):
    def validate(self, value: str) -> bool:
        return isinstance(value, str)
    
    def _transform(self, value: str, context=None) -> str:
        return value[::-1]

class MyPlugin(TransformerPlugin):
    def __init__(self):
        super().__init__("my_plugin")
    
    @property
    def transformers(self):
        return {
            'reverse': lambda _: ReverseTransformer('reverse')
        }

# Usage
TUKUY = TukuyTransformer()
TUKUY.register_plugin(MyPlugin())

result = TUKUY.transform("hello", ["reverse"])  # "olleh"
```

### 🔄 Plugin Lifecycle

Plugins can implement `initialize()` and `cleanup()` methods for setup and teardown:

```python
class MyPlugin(TransformerPlugin):
    def initialize(self) -> None:
        super().initialize()
        # Load resources, connect to databases, etc.
    
    def cleanup(self) -> None:
        super().cleanup()
        # Close connections, free resources, etc.
```