Contributing
===========

Thank you for your interest in contributing to Tukuy! This document provides guidelines and instructions for contributing to the project.

Getting Started
--------------

1. **Fork the Repository**

   Start by forking the main repository to your GitHub account.

   .. code-block:: bash

      # Clone your fork locally
      git clone https://github.com/YOUR-USERNAME/tukuy.git
      cd tukuy

2. **Set Up Development Environment**

   .. code-block:: bash

      # Create a virtual environment
      python -m venv venv
      
      # Activate the virtual environment
      # On Windows:
      venv\Scripts\activate
      # On Unix or MacOS:
      source venv/bin/activate
      
      # Install development dependencies
      pip install -e ".[dev]"

3. **Create a Feature Branch**

   Always create a new branch for your changes:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

Development Guidelines
---------------------

Code Style
~~~~~~~~~

Tukuy follows these coding standards:

- Use **PEP 8** style guide for Python code
- Use **type hints** for all function parameters and return values
- Document all public functions, classes, and methods with docstrings
- Keep line length to a maximum of 100 characters
- Use meaningful variable and function names
- Write unit tests for all new functionality

Here's an example of proper style:

.. code-block:: python

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

Documentation
~~~~~~~~~~~~

- All new features should be documented with docstrings
- Include examples in docstrings
- Keep docstrings up-to-date with code changes
- Update the user guide and examples for significant features

Docstring Format
^^^^^^^^^^^^^^^

Use the following format for docstrings:

.. code-block:: python

   """
   Description:
       A short description of what this function/class does.
   
   Version: v1
   Status: Production/Beta/Under Development
   Last Updated: YYYY-MM-DD
   
   Args:
       param1 (type): Description of parameter 1
       param2 (type): Description of parameter 2
   
   Returns:
       type: Description of return value
   
   Raises:
       ExceptionType: When and why this exception is raised
   
   Notes:
       Additional information, limitations, or special considerations
   
   Example::
   
       # Basic example
       result = function(arg1, arg2)
       assert result == expected_value
   """

Testing
~~~~~~~

All new code should be thoroughly tested:

1. **Write Unit Tests**

   - Write tests for each new feature or bug fix
   - Aim for high code coverage
   - Test edge cases and error conditions

2. **Run Tests Locally**

   .. code-block:: bash

      # Run all tests
      pytest
      
      # Run tests with coverage report
      pytest --cov=tukuy tests/

3. **Ensure All Tests Pass**

   Make sure all tests pass before submitting a pull request.

Creating a Pull Request
----------------------

1. **Commit Your Changes**

   Make sure your commits are focused and include clear messages:

   .. code-block:: bash

      git add .
      git commit -m "Add feature: brief description of what you did"

2. **Push to Your Fork**

   .. code-block:: bash

      git push origin feature/your-feature-name

3. **Create a Pull Request**

   - Go to the original repository on GitHub
   - Click "Pull Request"
   - Select your branch
   - Fill in the PR template with details about your changes

4. **Respond to Feedback**

   Be open to feedback and make requested changes. This is a collaborative process to ensure high-quality code.

Creating New Transformers
------------------------

When adding new transformers to Tukuy, follow these guidelines:

1. **Choose the Right Location**

   - Place the transformer in the appropriate module based on its functionality
   - Create a new module if it doesn't fit existing categories

2. **Extend the Base Class**

   All transformers should extend `ChainableTransformer`:

   .. code-block:: python

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

3. **Handle Errors Properly**

   - Use appropriate exception types
   - Provide clear error messages
   - Include the input value in error messages for debugging

4. **Document Thoroughly**

   - Include detailed docstrings with examples
   - Document parameters, return types, and exceptions
   - Explain edge cases and limitations

5. **Test Comprehensively**

   - Test basic functionality
   - Test edge cases
   - Test error conditions
   - Test chaining with other transformers

Creating New Plugins
------------------

To create a new plugin:

1. **Create a Plugin Class**

   .. code-block:: python

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
          
          def cleanup(self) -> None:
              super().cleanup()
              # Perform cleanup tasks

2. **Register Your Transformers**

   Make sure each transformer is properly registered in the `transformers` property.

3. **Document Your Plugin**

   - Explain the purpose of the plugin
   - Document each transformer provided by the plugin
   - Include examples of how to use the plugin

4. **Test the Plugin**

   - Test registration and initialization
   - Test each transformer
   - Test cleanup

Release Process
-------------

If you're a maintainer, follow these steps for releases:

1. **Version Bump**

   Update the version number in:
   - VERSION file
   - setup.py
   - Any other relevant files

2. **Update Changelog**

   Add detailed notes about changes, improvements, and bug fixes.

3. **Tag the Release**

   .. code-block:: bash

      git tag -a vX.Y.Z -m "Release vX.Y.Z"
      git push origin vX.Y.Z

4. **Publish to PyPI**

   .. code-block:: bash

      python setup.py sdist bdist_wheel
      twine upload dist/*

5. **Update Documentation**

   Ensure the documentation is updated for the new release.

Community Guidelines
------------------

- **Be Respectful**: Treat all contributors with respect and consideration.
- **Be Constructive**: Provide constructive feedback on pull requests.
- **Be Patient**: Not all contributors have the same level of experience.
- **Be Inclusive**: Welcome contributions from everyone, regardless of background.

Thank you for helping to improve Tukuy!