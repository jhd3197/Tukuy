User Guide
=========

Core Concepts
------------

Tukuy is built around a few key concepts that make it powerful and flexible:

Transformers
~~~~~~~~~~~

Transformers are the basic building blocks in Tukuy. Each transformer takes an input value, performs a specific operation, and returns a result. Transformers can:

- **Validate** input data (like validating email formats)
- **Transform** data from one form to another (like stripping HTML tags)
- **Extract** specific pieces of information (like selecting elements from HTML)
- **Calculate** new values (like calculating age from a date)

Chaining
~~~~~~~~

Transformers can be chained together to create complex transformation pipelines. This allows you to:

- Apply multiple transformations in sequence
- Build reusable transformation sequences
- Combine different types of transformations

Plugins
~~~~~~~

Tukuy's plugin system allows for extensibility. Plugins:

- Provide sets of related transformers
- Can be registered with the main TukuyTransformer
- Allow for modular organization of functionality
- Make it easy to add custom transformations

Using Transformers
-----------------

Text Transformations
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from tukuy import TukuyTransformer
    
    TUKUY = TukuyTransformer()
    
    # Basic transformations
    text = " Hello World! "
    result = TUKUY.transform(text, [
        "strip",              # Remove leading/trailing whitespace
        "lowercase",          # Convert to lowercase
        {"function": "truncate", "length": 5}  # Truncate to 5 chars
    ])
    print(result)  # "hello..."
    
    # Using regex
    text = "Hello 123 World"
    result = TUKUY.transform(text, [
        {"function": "regex_replace", "pattern": r"\d+", "replacement": "#"}
    ])
    print(result)  # "Hello # World"

HTML Transformations
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    html = "<div><h1>Title</h1><p>This is <b>important</b> content.</p></div>"
    
    # Strip tags
    clean_text = TUKUY.transform(html, ["strip_html_tags"])
    print(clean_text)  # "Title This is important content."
    
    # Extract specific content
    title = TUKUY.transform(html, [
        {"function": "select", "selector": "h1"}
    ])
    print(title)  # "Title"
    
    # Extract and transform
    important = TUKUY.transform(html, [
        {"function": "select", "selector": "b"},
        "uppercase"
    ])
    print(important)  # "IMPORTANT"

Date Transformations
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from datetime import date
    
    # Calculate age
    birth_date = "1990-05-15"
    age = TUKUY.transform(birth_date, [
        {"function": "age_calc"}
    ])
    print(f"Age: {age} years")
    
    # Calculate duration
    start_date = "2023-01-01"
    days = TUKUY.transform(start_date, [
        {"function": "duration_calc", "unit": "days", "end": "2023-12-31"}
    ])
    print(f"Days: {days}")

JSON Transformations
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    json_str = '{"user": {"name": "John", "email": "john@example.com", "age": 30}}'
    
    # Extract values
    name = TUKUY.transform(json_str, [
        {"function": "extract", "selector": "user.name"}
    ])
    print(name)  # "John"
    
    # Transform extracted values
    email = TUKUY.transform(json_str, [
        {"function": "extract", "selector": "user.email"},
        {"function": "validate_email"}
    ])
    print(email)  # "john@example.com" or None if invalid

Numerical Transformations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Format number
    number = 1234.56
    formatted = TUKUY.transform(number, [
        {"function": "format_number", "decimals": 1}
    ])
    print(formatted)  # "1,234.6"
    
    # Convert to percentage
    decimal = 0.75
    percentage = TUKUY.transform(decimal, [
        {"function": "percentage", "decimals": 0}
    ])
    print(percentage)  # "75%"

Validation Transformations
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Validate email
    email = "test@example.com"
    valid_email = TUKUY.transform(email, ["email_validator"])
    print(valid_email)  # "test@example.com" or None if invalid
    
    # Validate URL
    url = "https://example.com"
    valid_url = TUKUY.transform(url, ["url_validator"])
    print(valid_url)  # "https://example.com" or None if invalid
    
    # Validate number range
    number = 15
    in_range = TUKUY.transform(number, [
        {"function": "range_validator", "min": 10, "max": 20}
    ])
    print(in_range)  # 15 or None if outside range

Pattern-based Data Extraction
----------------------------

HTML Pattern Extraction
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    html = """
    <div class="article">
        <h1>Main Title</h1>
        <div class="metadata">
            <span class="author">John Doe</span>
            <span class="date">2023-05-15</span>
        </div>
        <div class="content">
            <p>First paragraph</p>
            <p>Second paragraph</p>
        </div>
        <ul class="tags">
            <li>tech</li>
            <li>python</li>
            <li>data</li>
        </ul>
    </div>
    """
    
    pattern = {
        "properties": [
            {
                "name": "title",
                "selector": "h1",
                "transform": ["strip", "uppercase"]
            },
            {
                "name": "author",
                "selector": ".author",
                "transform": ["strip"]
            },
            {
                "name": "paragraphs",
                "selector": "p",
                "type": "array"
            },
            {
                "name": "tags",
                "selector": ".tags li",
                "type": "array"
            }
        ]
    }
    
    result = TUKUY.extract_html_with_pattern(html, pattern)
    print(result)
    # {
    #     "title": "MAIN TITLE",
    #     "author": "John Doe",
    #     "paragraphs": ["First paragraph", "Second paragraph"],
    #     "tags": ["tech", "python", "data"]
    # }

JSON Pattern Extraction
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    json_str = """
    {
        "data": {
            "user": {
                "profile": {
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "settings": {
                    "theme": "dark",
                    "notifications": true
                },
                "posts": [
                    {"id": 1, "title": "First Post", "likes": 10},
                    {"id": 2, "title": "Second Post", "likes": 15},
                    {"id": 3, "title": "Third Post", "likes": 5}
                ]
            }
        }
    }
    """
    
    pattern = {
        "properties": [
            {
                "name": "userName",
                "selector": "data.user.profile.name"
            },
            {
                "name": "email",
                "selector": "data.user.profile.email",
                "transform": ["email_validator"]
            },
            {
                "name": "darkMode",
                "selector": "data.user.settings.theme",
                "transform": [{"function": "equals", "value": "dark"}]
            },
            {
                "name": "postTitles",
                "selector": "data.user.posts[*].title",
                "type": "array"
            },
            {
                "name": "totalLikes",
                "selector": "data.user.posts[*].likes",
                "transform": [{"function": "sum"}]
            }
        ]
    }
    
    result = TUKUY.extract_json_with_pattern(json_str, pattern)
    print(result)
    # {
    #     "userName": "John Doe",
    #     "email": "john@example.com",
    #     "darkMode": true,
    #     "postTitles": ["First Post", "Second Post", "Third Post"],
    #     "totalLikes": 30
    # }

Error Handling
-------------

Tukuy provides comprehensive error handling through specific exception types:

.. code-block:: python

    from tukuy import TukuyTransformer
    from tukuy.exceptions import ValidationError, TransformationError, ParseError
    
    TUKUY = TukuyTransformer()
    
    try:
        # Try to validate an invalid email
        result = TUKUY.transform("not-an-email", ["email_validator"])
    except ValidationError as e:
        print(f"Validation error: {e}")
    
    try:
        # Try to parse invalid JSON
        result = TUKUY.transform("{invalid-json}", [{"function": "parse_json"}])
    except ParseError as e:
        print(f"Parse error: {e}")
    
    try:
        # Try to use a non-existent transformer
        result = TUKUY.transform("hello", ["non_existent_transformer"])
    except TransformationError as e:
        print(f"Transformation error: {e}")

Best Practices
-------------

Chain Transformations
~~~~~~~~~~~~~~~~~~~

Chain transformations to avoid creating intermediate objects and to make your code more readable:

.. code-block:: python

    # Less efficient with intermediate objects:
    text = " Hello World! "
    text = TUKUY.transform(text, ["strip"])
    text = TUKUY.transform(text, ["lowercase"])
    
    # More efficient with chaining:
    text = " Hello World! "
    text = TUKUY.transform(text, ["strip", "lowercase"])

Use Specific Selectors
~~~~~~~~~~~~~~~~~~~~

When extracting data from HTML or JSON, use specific selectors to improve performance:

.. code-block:: python

    # Less efficient:
    title = TUKUY.transform(html, [
        {"function": "select", "selector": "div"}  # Too general
    ])
    
    # More efficient:
    title = TUKUY.transform(html, [
        {"function": "select", "selector": "div.article h1"}  # More specific
    ])

Reuse Transformer Instances
~~~~~~~~~~~~~~~~~~~~~~~~~

Create a single TukuyTransformer instance and reuse it throughout your application:

.. code-block:: python

    # Create once:
    TUKUY = TukuyTransformer()
    
    # Reuse across your application:
    def process_user(user_data):
        name = TUKUY.transform(user_data, [{"function": "extract", "selector": "name"}])
        email = TUKUY.transform(user_data, [{"function": "extract", "selector": "email"}])
        # ...

Create Custom Transformers
~~~~~~~~~~~~~~~~~~~~~~~~

For performance-critical operations or specialized transformations, create custom transformers:

.. code-block:: python

    from tukuy.base import ChainableTransformer
    from tukuy.plugins import TransformerPlugin
    
    class CustomTransformer(ChainableTransformer[str, str]):
        def validate(self, value: str) -> bool:
            return isinstance(value, str)
        
        def _transform(self, value: str, context=None) -> str:
            # Custom implementation here
            return value.replace('specific_pattern', 'replacement')
    
    class CustomPlugin(TransformerPlugin):
        def __init__(self):
            super().__init__("custom_plugin")
        
        @property
        def transformers(self):
            return {
                'custom_transform': lambda _: CustomTransformer('custom_transform')
            }
    
    TUKUY = TukuyTransformer()
    TUKUY.register_plugin(CustomPlugin())