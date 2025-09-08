Examples
========

This section provides practical examples showcasing how to use Tukuy for various common tasks and scenarios. These examples demonstrate the power and flexibility of Tukuy's transformer system.

Text Transformations
-------------------

Basic Text Processing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from tukuy import TukuyTransformer
    
    TUKUY = TukuyTransformer()
    
    # Clean and normalize user input
    user_input = "  Héllò   Wórld!  "
    clean_text = TUKUY.transform(user_input, [
        "strip",          # Remove leading/trailing whitespace
        "normalize",      # Remove diacritics
        "lowercase"       # Convert to lowercase
    ])
    print(clean_text)  # "hello world!"
    
    # Truncate long text for display
    long_text = "This is a very long text that needs to be truncated for display purposes."
    truncated = TUKUY.transform(long_text, [
        {"function": "truncate", "length": 20, "suffix": "..."}
    ])
    print(truncated)  # "This is a very long..."

Text Search and Replace
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Replace specific words
    text = "The quick brown fox jumps over the lazy dog."
    replaced = TUKUY.transform(text, [
        {"function": "replace", "search": "fox", "replacement": "cat"}
    ])
    print(replaced)  # "The quick brown cat jumps over the lazy dog."
    
    # Replace using regex for more complex patterns
    text = "Contact us at info@example.com or support@example.com"
    anonymized = TUKUY.transform(text, [
        {"function": "regex_replace", 
         "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", 
         "replacement": "[EMAIL REDACTED]"}
    ])
    print(anonymized)  # "Contact us at [EMAIL REDACTED] or [EMAIL REDACTED]"

Text Splitting and Joining
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Split a comma-separated list
    tags = "python,data,transformation,library"
    tag_list = TUKUY.transform(tags, [
        {"function": "split", "separator": ","}
    ])
    print(tag_list)  # ["python", "data", "transformation", "library"]
    
    # Join array into string
    words = ["Tukuy", "is", "awesome"]
    sentence = TUKUY.transform(words, [
        {"function": "join", "separator": " "}
    ])
    print(sentence)  # "Tukuy is awesome"

HTML Transformations
------------------

Extracting Text from HTML
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    html = """
    <article>
        <h1>Understanding Tukuy</h1>
        <div class="content">
            <p>Tukuy is a <strong>powerful</strong> transformation library.</p>
            <p>It makes data processing <em>easy</em> and intuitive.</p>
        </div>
        <div class="author">
            <span>Written by: John Doe</span>
        </div>
    </article>
    """
    
    # Extract plain text from HTML
    text = TUKUY.transform(html, ["strip_html_tags"])
    print(text)  # "Understanding Tukuy Tukuy is a powerful transformation library. It makes data processing easy and intuitive. Written by: John Doe"
    
    # Extract specific elements
    title = TUKUY.transform(html, [
        {"function": "select", "selector": "h1"}
    ])
    print(title)  # "Understanding Tukuy"
    
    paragraphs = TUKUY.transform(html, [
        {"function": "select", "selector": "p", "extract": "text_array"}
    ])
    print(paragraphs)  # ["Tukuy is a powerful transformation library.", "It makes data processing easy and intuitive."]

Scraping Product Information
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    product_html = """
    <div class="product">
        <h2 class="title">Wireless Headphones</h2>
        <div class="price">$99.99</div>
        <div class="description">High-quality wireless headphones with noise cancellation.</div>
        <ul class="features">
            <li>Bluetooth 5.0</li>
            <li>40h Battery Life</li>
            <li>Active Noise Cancellation</li>
        </ul>
        <div class="rating">4.5/5 (230 reviews)</div>
    </div>
    """
    
    # Extract structured product data
    pattern = {
        "properties": [
            {
                "name": "title",
                "selector": ".title",
                "transform": ["strip"]
            },
            {
                "name": "price",
                "selector": ".price",
                "transform": [
                    "strip",
                    {"function": "regex_replace", "pattern": r"^\$", "replacement": ""}
                ]
            },
            {
                "name": "description",
                "selector": ".description",
                "transform": ["strip"]
            },
            {
                "name": "features",
                "selector": ".features li",
                "type": "array"
            },
            {
                "name": "rating",
                "selector": ".rating",
                "transform": [
                    {"function": "regex_extract", "pattern": r"(\d+\.\d+)\/5"}
                ]
            }
        ]
    }
    
    product = TUKUY.extract_html_with_pattern(product_html, pattern)
    print(product)
    # {
    #     "title": "Wireless Headphones",
    #     "price": "99.99",
    #     "description": "High-quality wireless headphones with noise cancellation.",
    #     "features": ["Bluetooth 5.0", "40h Battery Life", "Active Noise Cancellation"],
    #     "rating": "4.5"
    # }

Extracting Tables from HTML
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    table_html = """
    <table>
        <thead>
            <tr>
                <th>Product</th>
                <th>Price</th>
                <th>Stock</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Laptop</td>
                <td>$1,299.99</td>
                <td>10</td>
            </tr>
            <tr>
                <td>Smartphone</td>
                <td>$799.99</td>
                <td>25</td>
            </tr>
            <tr>
                <td>Headphones</td>
                <td>$99.99</td>
                <td>50</td>
            </tr>
        </tbody>
    </table>
    """
    
    # Extract table as structured data
    table_data = TUKUY.transform(table_html, [
        {"function": "extract_tables"}
    ])
    
    print(table_data)
    # [
    #     {
    #         "headers": ["Product", "Price", "Stock"],
    #         "rows": [
    #             ["Laptop", "$1,299.99", "10"],
    #             ["Smartphone", "$799.99", "25"],
    #             ["Headphones", "$99.99", "50"]
    #         ]
    #     }
    # ]
    
    # Process table data
    total_stock = 0
    for row in table_data[0]["rows"]:
        total_stock += int(row[2])
    
    print(f"Total stock: {total_stock}")  # "Total stock: 85"

JSON Transformations
-----------------

Extracting Data from JSON
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    json_data = """
    {
        "user": {
            "profile": {
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30
            },
            "preferences": {
                "theme": "dark",
                "notifications": true
            },
            "stats": {
                "posts": 45,
                "followers": 1024,
                "following": 256
            }
        }
    }
    """
    
    # Extract specific values
    name = TUKUY.transform(json_data, [
        {"function": "extract", "selector": "user.profile.name"}
    ])
    print(name)  # "John Doe"
    
    # Extract and validate
    email = TUKUY.transform(json_data, [
        {"function": "extract", "selector": "user.profile.email"},
        "email_validator"
    ])
    print(email)  # "john@example.com" (or None if invalid)
    
    # Extract multiple values
    stats = TUKUY.transform(json_data, [
        {"function": "extract", "selector": "user.stats"}
    ])
    print(stats)  # {"posts": 45, "followers": 1024, "following": 256}

Processing API Responses
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    api_response = """
    {
        "data": {
            "results": [
                {"id": 1, "name": "Product A", "price": 19.99, "inStock": true},
                {"id": 2, "name": "Product B", "price": 29.99, "inStock": false},
                {"id": 3, "name": "Product C", "price": 39.99, "inStock": true},
                {"id": 4, "name": "Product D", "price": 49.99, "inStock": true}
            ],
            "pagination": {
                "total": 15,
                "page": 1,
                "perPage": 4
            }
        },
        "meta": {
            "requestId": "abc-123",
            "timestamp": "2024-01-15T14:30:00Z"
        }
    }
    """
    
    # Extract all in-stock products
    pattern = {
        "properties": [
            {
                "name": "inStockProducts",
                "selector": "data.results[*]",
                "filter": {"field": "inStock", "value": true},
                "properties": [
                    {"name": "id", "selector": "id"},
                    {"name": "name", "selector": "name"},
                    {"name": "price", "selector": "price"}
                ]
            },
            {
                "name": "totalProducts",
                "selector": "data.pagination.total"
            },
            {
                "name": "requestInfo",
                "properties": [
                    {"name": "id", "selector": "meta.requestId"},
                    {"name": "time", "selector": "meta.timestamp"}
                ]
            }
        ]
    }
    
    result = TUKUY.extract_json_with_pattern(api_response, pattern)
    print(result)
    # {
    #     "inStockProducts": [
    #         {"id": 1, "name": "Product A", "price": 19.99},
    #         {"id": 3, "name": "Product C", "price": 39.99},
    #         {"id": 4, "name": "Product D", "price": 49.99}
    #     ],
    #     "totalProducts": 15,
    #     "requestInfo": {
    #         "id": "abc-123",
    #         "time": "2024-01-15T14:30:00Z"
    #     }
    # }

Date Transformations
-----------------

Working with Dates
~~~~~~~~~~~~~~~~

.. code-block:: python

    from tukuy import TukuyTransformer
    
    TUKUY = TukuyTransformer()
    
    # Parse date string
    date_str = "2023-05-15"
    date_obj = TUKUY.transform(date_str, [
        {"function": "parse_date", "format": "%Y-%m-%d"}
    ])
    
    # Calculate age from birthdate
    birthdate = "1990-08-25"
    age = TUKUY.transform(birthdate, [
        {"function": "age_calc"}
    ])
    print(f"Age: {age} years")
    
    # Calculate days between dates
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    days = TUKUY.transform(start_date, [
        {"function": "duration_calc", "unit": "days", "end": end_date}
    ])
    print(f"Days between: {days}")
    
    # Format date
    date_obj = TUKUY.transform("2023-05-15", [
        {"function": "parse_date"},
        {"function": "format_date", "format": "%B %d, %Y"}
    ])
    print(date_obj)  # "May 15, 2023"

Handling Date Ranges
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Check if date falls within a range
    target_date = "2023-07-15"
    start_range = "2023-06-01"
    end_range = "2023-08-31"
    
    is_in_range = TUKUY.transform(target_date, [
        {"function": "parse_date"},
        {"function": "in_date_range", "start": start_range, "end": end_range}
    ])
    print(f"Date is in range: {is_in_range}")  # True
    
    # Calculate business days in a period
    business_days = TUKUY.transform("2023-01-01", [
        {"function": "business_days", "end": "2023-01-31"}
    ])
    print(f"Business days: {business_days}")  # ~22 (depending on holidays)
    
    # Check if date is a weekend
    is_weekend = TUKUY.transform("2023-07-15", [  # July 15, 2023 is a Saturday
        {"function": "is_weekend"}
    ])
    print(f"Is weekend: {is_weekend}")  # True

Numerical Transformations
----------------------

Basic Numerical Operations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from tukuy import TukuyTransformer
    
    TUKUY = TukuyTransformer()
    
    # Round numbers
    value = 123.456789
    rounded = TUKUY.transform(value, [
        {"function": "round", "decimals": 2}
    ])
    print(rounded)  # 123.46
    
    # Format with thousand separators
    large_number = 1234567.89
    formatted = TUKUY.transform(large_number, [
        {"function": "format_number"}
    ])
    print(formatted)  # "1,234,567.89"
    
    # Format as currency
    price = 49.99
    currency = TUKUY.transform(price, [
        {"function": "to_currency", "currency": "USD"}
    ])
    print(currency)  # "$49.99"
    
    # Calculate percentage
    ratio = 0.7523
    percentage = TUKUY.transform(ratio, [
        {"function": "percentage", "decimals": 1}
    ])
    print(percentage)  # "75.2%"

Statistical Calculations
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Calculate statistics from a list of numbers
    data = [12, 15, 23, 45, 67, 32, 18, 24]
    
    # Mean
    mean = TUKUY.transform(data, [
        {"function": "mean"}
    ])
    print(f"Mean: {mean}")  # Mean: 29.5
    
    # Median
    median = TUKUY.transform(data, [
        {"function": "median"}
    ])
    print(f"Median: {median}")  # Median: 23.5
    
    # Min and Max
    min_max = TUKUY.transform(data, [
        {"function": "range"}
    ])
    print(f"Range: {min_max}")  # Range: [12, 67]
    
    # Sum
    total = TUKUY.transform(data, [
        {"function": "sum"}
    ])
    print(f"Total: {total}")  # Total: 236

Financial Calculations
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Calculate compound interest
    principal = 1000
    interest_rate = 0.05  # 5%
    years = 5
    
    future_value = TUKUY.transform(principal, [
        {"function": "compound_interest", "rate": interest_rate, "years": years}
    ])
    print(f"Future value: {future_value}")  # ~1276.28
    
    # Calculate mortgage payment
    loan_amount = 300000
    interest_rate = 0.04  # 4%
    loan_term_years = 30
    
    monthly_payment = TUKUY.transform(loan_amount, [
        {"function": "mortgage_payment", 
         "rate": interest_rate, 
         "term_years": loan_term_years}
    ])
    print(f"Monthly payment: {monthly_payment}")  # ~$1,432.25
    
    # Calculate discount
    original_price = 100
    discount_percent = 25
    
    sale_price = TUKUY.transform(original_price, [
        {"function": "apply_discount", "discount": discount_percent}
    ])
    print(f"Sale price: {sale_price}")  # 75.0

Validation Transformations
-----------------------

Input Validation
~~~~~~~~~~~~~~

.. code-block:: python

    from tukuy import TukuyTransformer
    
    TUKUY = TukuyTransformer()
    
    # Email validation
    valid_email = "user@example.com"
    invalid_email = "not-an-email"
    
    result1 = TUKUY.transform(valid_email, ["email_validator"])
    result2 = TUKUY.transform(invalid_email, ["email_validator"])
    
    print(f"Valid email: {result1}")  # "user@example.com"
    print(f"Invalid email: {result2}")  # None
    
    # URL validation
    valid_url = "https://tukuy.example.com/docs"
    invalid_url = "not a url"
    
    result1 = TUKUY.transform(valid_url, ["url_validator"])
    result2 = TUKUY.transform(invalid_url, ["url_validator"])
    
    print(f"Valid URL: {result1}")  # "https://tukuy.example.com/docs"
    print(f"Invalid URL: {result2}")  # None
    
    # Phone number validation
    valid_phone = "+1-555-123-4567"
    invalid_phone = "123"
    
    result1 = TUKUY.transform(valid_phone, ["phone_validator"])
    result2 = TUKUY.transform(invalid_phone, ["phone_validator"])
    
    print(f"Valid phone: {result1}")  # "+1-555-123-4567"
    print(f"Invalid phone: {result2}")  # None

Range and Length Validation
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # String length validation
    username = "user123"
    
    is_valid = TUKUY.transform(username, [
        {"function": "length_validator", "min": 3, "max": 20}
    ])
    print(f"Username valid: {is_valid is not None}")  # True
    
    # Number range validation
    age = 25
    
    is_valid = TUKUY.transform(age, [
        {"function": "range_validator", "min": 18, "max": 65}
    ])
    print(f"Age valid: {is_valid is not None}")  # True
    
    # Date range validation
    event_date = "2023-06-15"
    
    is_valid = TUKUY.transform(event_date, [
        {"function": "date_range_validator", 
         "min": "2023-01-01", 
         "max": "2023-12-31"}
    ])
    print(f"Date valid: {is_valid is not None}")  # True

Custom Pattern Validation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Regex pattern validation
    password = "P@ssw0rd123"
    
    # Check if password meets complexity requirements
    is_valid = TUKUY.transform(password, [
        {"function": "regex_validator", 
         "pattern": r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"}
    ])
    print(f"Password valid: {is_valid is not None}")  # True
    
    # Custom validation function
    def validate_isbn(isbn):
        # Remove hyphens
        isbn = isbn.replace('-', '')
        # Check if all remaining characters are digits
        if not isbn.isdigit():
            return False
        # Check length
        if len(isbn) not in (10, 13):
            return False
        return True
    
    # Register custom validator
    class ISBNValidator(ChainableTransformer[str, str]):
        def validate(self, value: str) -> bool:
            return isinstance(value, str)
        
        def _transform(self, value: str, context=None) -> str:
            if validate_isbn(value):
                return value
            return None
    
    # Usage
    isbn = "978-3-16-148410-0"
    
    is_valid = TUKUY.transform(isbn, [
        {"function": "isbn_validator"}  # Assuming registered
    ])
    print(f"ISBN valid: {is_valid is not None}")  # True

Creating Custom Transformers
--------------------------

Custom Text Transformer
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from tukuy.base import ChainableTransformer
    from tukuy.plugins import TransformerPlugin
    from tukuy import TukuyTransformer
    
    # Create a custom transformer for title case conversion
    class TitleCaseTransformer(ChainableTransformer[str, str]):
        def validate(self, value: str) -> bool:
            return isinstance(value, str)
        
        def _transform(self, value: str, context=None) -> str:
            # Custom implementation of title case
            # (Different from str.title() because it preserves UPPERCASE acronyms)
            words = value.split()
            for i, word in enumerate(words):
                # Skip uppercase acronyms
                if word.isupper():
                    continue
                # Capitalize first letter of other words
                if len(word) > 0:
                    words[i] = word[0].upper() + word[1:]
            return ' '.join(words)
    
    # Create a plugin to register the transformer
    class TextExtensionsPlugin(TransformerPlugin):
        def __init__(self):
            super().__init__("text_extensions")
        
        @property
        def transformers(self):
            return {
                'title_case': lambda _: TitleCaseTransformer('title_case')
            }
    
    # Usage
    TUKUY = TukuyTransformer()
    TUKUY.register_plugin(TextExtensionsPlugin())
    
    text = "the QUICK brown fox jumps over the lazy dog"
    result = TUKUY.transform(text, ["title_case"])
    print(result)  # "The QUICK Brown Fox Jumps Over The Lazy Dog"

Custom Data Processor
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create a transformer for processing CSV data
    class CSVParserTransformer(ChainableTransformer[str, list]):
        def __init__(self, name: str, delimiter: str = ',', has_header: bool = True):
            super().__init__(name)
            self.delimiter = delimiter
            self.has_header = has_header
        
        def validate(self, value: str) -> bool:
            return isinstance(value, str)
        
        def _transform(self, value: str, context=None) -> list:
            lines = value.strip().split('\n')
            if not lines:
                return []
                
            results = []
            headers = None
            
            for i, line in enumerate(lines):
                row = line.split(self.delimiter)
                row = [cell.strip() for cell in row]
                
                if i == 0 and self.has_header:
                    headers = row
                    continue
                    
                if self.has_header:
                    row_dict = {headers[j]: cell for j, cell in enumerate(row) if j < len(headers)}
                    results.append(row_dict)
                else:
                    results.append(row)
                    
            return results
    
    # Create a plugin
    class DataProcessingPlugin(TransformerPlugin):
        def __init__(self):
            super().__init__("data_processing")
        
        @property
        def transformers(self):
            return {
                'parse_csv': lambda _: CSVParserTransformer('parse_csv')
            }
    
    # Usage
    TUKUY = TukuyTransformer()
    TUKUY.register_plugin(DataProcessingPlugin())
    
    csv_data = """Name,Age,Email
    John Doe,30,john@example.com
    Jane Smith,25,jane@example.com
    Bob Johnson,45,bob@example.com"""
    
    result = TUKUY.transform(csv_data, [
        {"function": "parse_csv"}
    ])
    
    print(result)
    # [
    #     {'Name': 'John Doe', 'Age': '30', 'Email': 'john@example.com'},
    #     {'Name': 'Jane Smith', 'Age': '25', 'Email': 'jane@example.com'},
    #     {'Name': 'Bob Johnson', 'Age': '45', 'Email': 'bob@example.com'}
    # ]

Using Plugins
-----------

Registering Custom Plugins
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from tukuy.base import ChainableTransformer
    from tukuy.plugins import TransformerPlugin
    from tukuy import TukuyTransformer
    
    # Create a geo transformation plugin
    class GeoTransformer(ChainableTransformer[dict, dict]):
        def __init__(self, name: str):
            super().__init__(name)
            
        def validate(self, value: dict) -> bool:
            return (isinstance(value, dict) and 
                   'lat' in value and 'lon' in value)
            
        def _transform(self, value: dict, context=None) -> dict:
            # Convert decimal coordinates to DMS format
            # (Degrees, Minutes, Seconds)
            lat = value['lat']
            lon = value['lon']
            
            def decimal_to_dms(coord):
                deg = int(coord)
                min_float = (coord - deg) * 60
                min = int(min_float)
                sec = (min_float - min) * 60
                return f"{deg}° {min}' {sec:.1f}\""
                
            return {
                'lat': lat,
                'lon': lon,
                'lat_dms': decimal_to_dms(abs(lat)) + ('N' if lat >= 0 else 'S'),
                'lon_dms': decimal_to_dms(abs(lon)) + ('E' if lon >= 0 else 'W')
            }
    
    class GeoPlugin(TransformerPlugin):
        def __init__(self):
            super().__init__("geo")
            
        @property
        def transformers(self):
            return {
                'to_dms': lambda _: GeoTransformer('to_dms')
            }
            
        def initialize(self):
            super().initialize()
            print("Geo plugin initialized")
            
        def cleanup(self):
            super().cleanup()
            print("Geo plugin cleaned up")
    
    # Usage
    TUKUY = TukuyTransformer()
    TUKUY.register_plugin(GeoPlugin())
    
    coords = {'lat': 40.7128, 'lon': -74.0060}  # New York
    result = TUKUY.transform(coords, [
        {"function": "to_dms"}
    ])
    
    print(result)
    # {
    #     'lat': 40.7128, 
    #     'lon': -74.0060,
    #     'lat_dms': "40° 42' 46.1\"N",
    #     'lon_dms': "74° 0' 21.6\"W"
    # }

Creating Plugin Collections
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create a collection of related transformers
    class AnalyticsTransformerA(ChainableTransformer[list, float]):
        def validate(self, value: list) -> bool:
            return isinstance(value, list) and all(isinstance(x, (int, float)) for x in value)
            
        def _transform(self, value: list, context=None) -> float:
            # Calculate average
            return sum(value) / len(value) if value else 0
            
    class AnalyticsTransformerB(ChainableTransformer[list, dict]):
        def validate(self, value: list) -> bool:
            return isinstance(value, list) and all(isinstance(x, (int, float)) for x in value)
            
        def _transform(self, value: list, context=None) -> dict:
            # Calculate basic statistics
            if not value:
                return {"count": 0, "sum": 0, "mean": 0, "min": None, "max": None}
                
            return {
                "count": len(value),
                "sum": sum(value),
                "mean": sum(value) / len(value),
                "min": min(value),
                "max": max(value)
            }
    
    # Group them in a plugin
    class AnalyticsPlugin(TransformerPlugin):
        def __init__(self):
            super().__init__("analytics")
            
        @property
        def transformers(self):
            return {
                'average': lambda _: AnalyticsTransformerA('average'),
                'stats': lambda _: AnalyticsTransformerB('stats')
            }
    
    # Usage
    TUKUY = TukuyTransformer()
    TUKUY.register_plugin(AnalyticsPlugin())
    
    data = [12, 15, 23, 45, 67, 32, 18, 24]
    
    avg = TUKUY.transform(data, ["average"])
    print(f"Average: {avg}")  # Average: 29.5
    
    stats = TUKUY.transform(data, ["stats"])
    print(f"Statistics: {stats}")
    # Statistics: {
    #   'count': 8, 
    #   'sum': 236, 
    #   'mean': 29.5, 
    #   'min': 12, 
    #   'max': 67
    # }

Real-world Use Cases
------------------

Web Scraping and Data Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import requests
    from tukuy import TukuyTransformer
    
    TUKUY = TukuyTransformer()
    
    # Fetch a web page
    url = "https://example.com/products"
    response = requests.get(url)
    html = response.text
    
    # Define extraction pattern for products
    pattern = {
        "properties": [
            {
                "name": "products",
                "selector": ".product-item",
                "type": "array",
                "properties": [
                    {
                        "name": "title",
                        "selector": ".product-title",
                        "transform": ["strip"]
                    },
                    {
                        "name": "price",
                        "selector": ".product-price",
                        "transform": [
                            "strip",
                            {"function": "regex_extract", "pattern": r"\$(\d+\.\d+)"}
                        ]
                    },
                    {
                        "name": "rating",
                        "selector": ".product-rating",
                        "transform": [
                            {"function": "regex_extract", "pattern": r"(\d\.\d)\/5"}
                        ]
                    },
                    {
                        "name": "inStock",
                        "selector": ".stock-status",
                        "transform": [
                            {"function": "equals", "value": "In Stock"}
                        ]
                    }
                ]
            },
            {
                "name": "pagination",
                "properties": [
                    {
                        "name": "currentPage",
                        "selector": ".pagination .current",
                        "transform": ["strip"]
                    },
                    {
                        "name": "totalPages",
                        "selector": ".pagination .total",
                        "transform": ["strip"]
                    }
                ]
            }
        ]
    }
    
    # Extract structured data
    result = TUKUY.extract_html_with_pattern(html, pattern)
    
    # Process the extracted data
    in_stock_products = [p for p in result["products"] if p["inStock"]]
    print(f"Found {len(in_stock_products)} in-stock products")
    
    # Sort by price
    sorted_products = sorted(result["products"], 
                            key=lambda p: float(p["price"]) if p["price"] else 0)
    
    # Display top 5 cheapest in-stock products
    for product in [p for p in sorted_products if p["inStock"]][:5]:
        print(f"{product['title']} - ${product['price']} - Rating: {product['rating']}/5")

Data Cleaning and Normalization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    from tukuy import TukuyTransformer
    
    TUKUY = TukuyTransformer()
    
    # Load raw data
    df = pd.read_csv("customer_data.csv")
    
    # Clean and normalize data
    cleaned_data = []
    
    for _, row in df.iterrows():
        # Clean and validate email
        email = TUKUY.transform(row["email"], [
            "strip",
            "lowercase",
            "email_validator"
        ])
        
        # Format phone number
        phone = TUKUY.transform(row["phone"], [
            "strip",
            {"function": "regex_replace", "pattern": r"[^\d+]", "replacement": ""},
            "phone_validator"
        ])
        
        # Normalize name
        name = TUKUY.transform(row["name"], [
            "strip",
            {"function": "title_case"}  # Custom transformer from earlier
        ])
        
        # Parse and validate date
        birth_date = TUKUY.transform(row["birth_date"], [
            {"function": "parse_date", "format": "%m/%d/%Y"},
            {"function": "format_date", "format": "%Y-%m-%d"}
        ])
        
        # Calculate age
        age = TUKUY.transform(birth_date, [
            {"function": "age_calc"}
        ]) if birth_date else None
        
        # Add to cleaned data if critical fields are valid
        if email and name:
            cleaned_data.append({
                "name": name,
                "email": email,
                "phone": phone,
                "birth_date": birth_date,
                "age": age
            })
    
    # Create cleaned DataFrame
    cleaned_df = pd.DataFrame(cleaned_data)
    
    # Save cleaned data
    cleaned_df.to_csv("cleaned_customer_data.csv", index=False)
    
    print(f"Processed {len(df)} records, kept {len(cleaned_data)} valid records")
    print(f"Removed {len(df) - len(cleaned_data)} invalid records")

API Data Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

    import requests
    import json
    from tukuy import TukuyTransformer
    
    TUKUY = TukuyTransformer()
    
    # Fetch data from an API
    response = requests.get("https://api.example.com/data")
    api_data = response.json()
    
    # Extract and transform specific data
    pattern = {
        "properties": [
            {
                "name": "items",
                "selector": "data.items[*]",
                "type": "array",
                "properties": [
                    {"name": "id", "selector": "id"},
                    {"name": "title", "selector": "title", "transform": ["strip"]},
                    {"name": "category", "selector": "category.name"},
                    {"name": "price", "selector": "price.amount"},
                    {"name": "currency", "selector": "price.currency"}
                ]
            },
            {
                "name": "metadata",
                "properties": [
                    {"name": "totalCount", "selector": "meta.total"},
                    {"name": "page", "selector": "meta.page"},
                    {"name": "timestamp", "selector": "meta.timestamp"}
                ]
            }
        ]
    }
    
    # Extract structured data
    result = TUKUY.extract_json_with_pattern(json.dumps(api_data), pattern)
    
    # Process items
    for item in result["items"]:
        # Format price with currency symbol
        formatted_price = TUKUY.transform(float(item["price"]), [
            {"function": "to_currency", "currency": item["currency"]}
        ])
        
        item["formatted_price"] = formatted_price
        
        # Categorize by price range
        price = float(item["price"])
        if price < 10:
            item["price_category"] = "budget"
        elif price < 50:
            item["price_category"] = "standard"
        else:
            item["price_category"] = "premium"
    
    # Group items by category
    categories = {}
    for item in result["items"]:
        category = item["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    # Calculate statistics for each category
    for category, items in categories.items():
        prices = [float(item["price"]) for item in items]
        stats = TUKUY.transform(prices, ["stats"])  # From the analytics plugin
        
        print(f"Category: {category}")
        print(f"  Items: {len(items)}")
        print(f"  Average price: {stats['mean']:.2f}")
        print(f"  Price range: {stats['min']} - {stats['max']}")