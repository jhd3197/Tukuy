# 🌀 Tukuy

A flexible data transformation library with a plugin system for Python.

## 🚀 Overview

Tukuy (meaning "to transform" or "to become" in Quechua) is a powerful and extensible data transformation library that makes it easy to manipulate, validate, and extract data from various formats. With its plugin architecture, Tukuy provides a unified interface for working with text, HTML, JSON, dates, numbers, and more.

## ✨ Features

- 🧩 **Plugin System**: Easily extend functionality with custom plugins
- 🔄 **Chainable Transformers**: Compose multiple transformations in sequence
- 🧪 **Type-safe Transformations**: With built-in validation
- 📊 **Rich Set of Built-in Transformers**:
  - 📝 Text manipulation (case conversion, trimming, regex, etc.)
  - 🌐 HTML processing and extraction
  - 📅 Date parsing and calculations
  - 🔢 Numerical operations
  - ✅ Data validation
  - 📋 JSON parsing and extraction
- 🔍 **Pattern-based Data Extraction**: Extract structured data from HTML and JSON
- 🛡️ **Error Handling**: Comprehensive error handling with detailed messages

## 📦 Installation

```bash
pip install tukuy
```

## 🛠️ Basic Usage

```python
from tukuy import ToolsTransformer

# Create transformer
TUKUY = ToolsTransformer()

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

## 🧩 Plugin System

Tukuy uses a plugin system to organize transformers into logical groups and make it easy to extend functionality.

### 📚 Built-in Plugins

- 📝 **text**: Basic text transformations (strip, lowercase, regex, etc.)
- 🌐 **html**: HTML manipulation and extraction
- 📅 **date**: Date parsing and calculations
- ✅ **validation**: Data validation and formatting
- 🔢 **numerical**: Number manipulation and calculations
- 📋 **json**: JSON parsing and extraction

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
TUKUY = ToolsTransformer()
TUKUY.register_plugin(MyPlugin())

result = TUKUY.transform("hello", ["reverse"])  # "olleh"
```

See the [example plugin](tukuy/plugins/example/__init__.py) for a more detailed example.

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