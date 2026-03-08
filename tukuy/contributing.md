# Contributing

Thank you for your interest in contributing to Tukuy! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. **Fork the Repository**

   Start by forking the main repository to your GitHub account.

   ```bash
   # Clone your fork locally
   git clone https://github.com/YOUR-USERNAME/tukuy.git
   cd tukuy
   ```

2. **Set Up Development Environment**

   ```bash
   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate

   # Install development dependencies
   pip install -e ".[dev]"
   ```

3. **Create a Feature Branch**

   Always create a new branch for your changes:

   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

Tukuy follows these coding standards:

- Use **PEP 8** style guide for Python code
- Use **type hints** for all function parameters and return values
- Document all public functions, classes, and methods with docstrings
- Keep line length to a maximum of 100 characters
- Use meaningful variable and function names
- Write unit tests for all new functionality

Here's an example of proper style:

```python
from typing import Optional, List

def calculate_average(numbers: List[float]) -> Optional[float]:
    """
    Calculate the average of a list of numbers.

    Args:
        numbers: A list of floating-point numbers

    Returns:
        The average as a float, or None if the list is empty
    """
    if not numbers:
        return None
    return sum(numbers) / len(numbers)
```

### Documentation

- All new features should be documented with docstrings
- Include examples in docstrings
- Keep docstrings up-to-date with code changes
- Update the user guide and examples for significant features

### Testing

All new code should be thoroughly tested:

1. **Write Unit Tests** -- Write tests for each new feature or bug fix, aim for high code coverage, and test edge cases and error conditions.

2. **Run Tests Locally**

   ```bash
   # Run all tests
   pytest

   # Run tests with coverage report
   pytest --cov=tukuy tests/
   ```

3. **Ensure All Tests Pass** before submitting a pull request.

## Creating a Pull Request

1. **Commit Your Changes**

   Make sure your commits are focused and include clear messages:

   ```bash
   git add .
   git commit -m "Add feature: brief description of what you did"
   ```

2. **Push to Your Fork**

   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** -- Go to the original repository on GitHub, click "Pull Request", select your branch, and fill in the PR template.

4. **Respond to Feedback** -- Be open to feedback and make requested changes.

## Creating New Transformers

When adding new transformers to Tukuy, follow these guidelines:

1. **Choose the Right Location** -- Place the transformer in the appropriate module based on its functionality, or create a new module if it doesn't fit existing categories.

2. **Extend the Base Class**

   All transformers should extend `ChainableTransformer`:

   ```python
   from tukuy.base import ChainableTransformer

   class MyTransformer(ChainableTransformer[InputType, OutputType]):
       def __init__(self, name: str, **kwargs):
           super().__init__(name)
           # Initialize additional parameters

       def validate(self, value: InputType) -> bool:
           # Validate input
           return isinstance(value, ExpectedType)

       def _transform(self, value: InputType, context=None) -> OutputType:
           # Implement transformation logic
           return transformed_value
   ```

3. **Handle Errors Properly** -- Use appropriate exception types, provide clear error messages, and include the input value in error messages for debugging.

4. **Document Thoroughly** -- Include detailed docstrings with examples, document parameters, return types, and exceptions.

5. **Test Comprehensively** -- Test basic functionality, edge cases, error conditions, and chaining with other transformers.

## Creating New Plugins

To create a new plugin:

```python
from tukuy.plugins import TransformerPlugin

class MyPlugin(TransformerPlugin):
    def __init__(self):
        super().__init__("my_plugin_name")

    @property
    def transformers(self):
        return {
            'transformer_name': lambda _: MyTransformer('transformer_name'),
            'other_transformer': lambda _: OtherTransformer('other_transformer')
        }

    def initialize(self) -> None:
        super().initialize()
        # Perform initialization tasks
```

## Community Guidelines

- **Be Respectful**: Treat all contributors with respect and consideration.
- **Be Constructive**: Provide constructive feedback on pull requests.
- **Be Patient**: Not all contributors have the same level of experience.
- **Be Inclusive**: Welcome contributions from everyone, regardless of background.

Thank you for helping to improve Tukuy!
