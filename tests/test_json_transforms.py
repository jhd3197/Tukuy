import pytest
import json
from tukuy.exceptions import ValidationError, TransformationError, ParseError

def test_json_parser_basic(transformer):
    # Test basic JSON parsing
    json_str = '{"name": "John", "age": 30, "city": "New York"}'
    result = transformer.transform(json_str, ["json_parse"])
    assert isinstance(result, dict)
    assert result["name"] == "John"
    assert result["age"] == 30
    assert result["city"] == "New York"
    
    # Test parsing JSON array
    json_array = '[1, 2, 3, 4, 5]'
    result = transformer.transform(json_array, ["json_parse"])
    assert isinstance(result, list)
    assert len(result) == 5
    assert result[0] == 1
    assert result[4] == 5

def test_json_parser_invalid(transformer):
    # Test invalid JSON with strict mode (default)
    invalid_json = '{"name": "John", "age": 30, "city": "New York"'  # Missing closing brace
    with pytest.raises(ParseError):
        transformer.transform(invalid_json, ["json_parse"])
    
    # Test invalid JSON with lenient mode
    result = transformer.transform(invalid_json, [{
        "function": "json_parse",
        "strict": False
    }])
    assert result == invalid_json  # Should return original string in lenient mode

def test_json_parser_schema_validation(transformer):
    # Test schema validation - valid
    json_str = '{"name": "John", "age": 30}'
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"}
        }
    }
    
    result = transformer.transform(json_str, [{
        "function": "json_parse",
        "schema": schema
    }])
    assert result["name"] == "John"
    assert result["age"] == 30
    
    # Test schema validation - invalid
    json_str = '{"name": "John", "age": "thirty"}'  # Age should be a number
    with pytest.raises(ValidationError):
        transformer.transform(json_str, [{
            "function": "json_parse",
            "schema": schema
        }])

def test_json_extractor_simple(transformer):
    # Test simple property extraction
    json_str = '{"user": {"name": "John", "email": "john@example.com"}, "status": "active"}'
    parsed = json.loads(json_str)
    
    # Extract user name
    result = transformer.transform(parsed, [{
        "function": "json_extract",
        "pattern": {
            "properties": [
                {
                    "name": "username",
                    "selector": "user.name"
                }
            ]
        }
    }])
    
    assert result["username"] == "John"
    
    # Extract status
    result = transformer.transform(parsed, [{
        "function": "json_extract",
        "pattern": {
            "properties": [
                {
                    "name": "account_status",
                    "selector": "status"
                }
            ]
        }
    }])
    
    assert result["account_status"] == "active"

def test_json_extractor_nested(transformer):
    # Test nested property extraction
    json_str = '''
    {
        "user": {
            "profile": {
                "personal": {
                    "name": "John Doe",
                    "age": 30,
                    "contact": {
                        "email": "john@example.com",
                        "phone": "555-1234"
                    }
                },
                "preferences": {
                    "theme": "dark",
                    "notifications": true
                }
            },
            "account": {
                "id": "user123",
                "type": "premium"
            }
        }
    }
    '''
    parsed = json.loads(json_str)
    
    # Extract deeply nested properties
    result = transformer.transform(parsed, [{
        "function": "json_extract",
        "pattern": {
            "properties": [
                {
                    "name": "email",
                    "selector": "user.profile.personal.contact.email"
                },
                {
                    "name": "theme",
                    "selector": "user.profile.preferences.theme"
                },
                {
                    "name": "account_type",
                    "selector": "user.account.type"
                }
            ]
        }
    }])
    
    assert result["email"] == "john@example.com"
    assert result["theme"] == "dark"
    assert result["account_type"] == "premium"

def test_json_extractor_array(transformer):
    # Test array extraction
    json_str = '''
    {
        "products": [
            {"id": "p1", "name": "Laptop", "price": 999.99},
            {"id": "p2", "name": "Phone", "price": 699.99},
            {"id": "p3", "name": "Tablet", "price": 499.99}
        ],
        "categories": ["Electronics", "Computers", "Mobile"]
    }
    '''
    parsed = json.loads(json_str)
    
    # Extract array of product names
    result = transformer.transform(parsed, [{
        "function": "json_extract",
        "pattern": {
            "properties": [
                {
                    "name": "product_names",
                    "selector": "products[*].name",
                    "type": "array"
                }
            ]
        }
    }])
    
    assert result["product_names"] == ["Laptop", "Phone", "Tablet"]
    
    # Extract categories
    result = transformer.transform(parsed, [{
        "function": "json_extract",
        "pattern": {
            "properties": [
                {
                    "name": "all_categories",
                    "selector": "categories",
                    "type": "array"
                }
            ]
        }
    }])
    
    assert result["all_categories"] == ["Electronics", "Computers", "Mobile"]

def test_json_extractor_fallback(transformer):
    # Test extraction with fallbacks
    json_str = '''
    {
        "data": {
            "main_image": "image1.jpg"
        },
        "backup": {
            "image": "backup.jpg"
        }
    }
    '''
    parsed = json.loads(json_str)
    
    # Test with primary selector that exists
    result = transformer.transform(parsed, [{
        "function": "json_extract",
        "pattern": {
            "properties": [
                {
                    "name": "image",
                    "selector": {
                        "primary": "data.main_image",
                        "fallback": ["backup.image", "default.image"]
                    }
                }
            ]
        }
    }])
    
    assert result["image"] == "image1.jpg"
    
    # Test with missing primary, using fallback
    json_str = '''
    {
        "data": {},
        "backup": {
            "image": "backup.jpg"
        }
    }
    '''
    parsed = json.loads(json_str)
    
    result = transformer.transform(parsed, [{
        "function": "json_extract",
        "pattern": {
            "properties": [
                {
                    "name": "image",
                    "selector": {
                        "primary": "data.main_image",
                        "fallback": ["backup.image", "default.image"]
                    }
                }
            ]
        }
    }])
    
    assert result["image"] == "backup.jpg"

def test_complex_json_pattern(transformer):
    # Test complex JSON pattern extraction
    COMPLEX_JSON = '''
    {
        "product": {
            "id": "prod-123",
            "name": "Smart TV X3000",
            "model": "TV-X3000-2023",
            "specs": {
                "display": "4K OLED",
                "size": "55 inch",
                "connectivity": ["HDMI", "USB", "Bluetooth", "WiFi"],
                "features": ["Smart Assistant", "HDR", "Dolby Vision"]
            },
            "pricing": {
                "msrp": 1299.99,
                "sale": 999.99,
                "discount": "23%"
            },
            "inventory": {
                "status": "in_stock",
                "quantity": 42,
                "warehouses": [
                    {"id": "w1", "stock": 15},
                    {"id": "w2", "stock": 27}
                ]
            },
            "reviews": [
                {"user": "user1", "rating": 5, "comment": "Excellent TV!"},
                {"user": "user2", "rating": 4, "comment": "Good but expensive"},
                {"user": "user3", "rating": 5, "comment": "Amazing picture quality"}
            ]
        }
    }
    '''
    
    COMPLEX_PATTERN = {
        "properties": [
            {
                "name": "product_info",
                "selector": "product",
                "type": "object",
                "properties": [
                    {
                        "name": "id",
                        "selector": "id"
                    },
                    {
                        "name": "name",
                        "selector": "name"
                    },
                    {
                        "name": "model_number",
                        "selector": "model",
                        "transform": [
                            {"function": "regex", "pattern": r"TV-(.+)-\d+", "template": "{1}"}
                        ]
                    }
                ]
            },
            {
                "name": "technical_specs",
                "selector": "product.specs",
                "type": "object"
            },
            {
                "name": "price_info",
                "selector": "product.pricing",
                "type": "object",
                "properties": [
                    {
                        "name": "current_price",
                        "selector": "sale"
                    },
                    {
                        "name": "savings",
                        "selector": {
                            "primary": "discount"
                        },
                        "transform": [
                            {"function": "regex", "pattern": r"(\d+)%", "template": "{1}"}
                        ]
                    }
                ]
            },
            {
                "name": "stock_info",
                "selector": "product.inventory",
                "type": "object",
                "properties": [
                    {
                        "name": "availability",
                        "selector": "status",
                        "transform": [
                            {"function": "replace", "find": "in_stock", "replace": "Available"}
                        ]
                    },
                    {
                        "name": "total_stock",
                        "selector": "quantity"
                    }
                ]
            },
            {
                "name": "warehouse_stock",
                "selector": "product.inventory.warehouses",
                "type": "array"
            },
            {
                "name": "review_ratings",
                "selector": "product.reviews[*].rating",
                "type": "array"
            },
            {
                "name": "average_rating",
                "selector": "product.reviews[*].rating",
                "transform": [
                    {"function": "average"}
                ]
            }
        ]
    }
    
    # Extract data using the pattern
    result = transformer.extract_json_with_pattern(COMPLEX_JSON, COMPLEX_PATTERN)
    
    # Verify extracted data
    assert result["product_info"]["id"] == "prod-123"
    assert result["product_info"]["name"] == "Smart TV X3000"
    assert result["product_info"]["model_number"] == "X3000"
    
    assert result["technical_specs"]["display"] == "4K OLED"
    assert result["technical_specs"]["size"] == "55 inch"
    assert len(result["technical_specs"]["connectivity"]) == 4
    assert len(result["technical_specs"]["features"]) == 3
    
    assert result["price_info"]["current_price"] == 999.99
    assert result["price_info"]["savings"] == "23"
    
    assert result["stock_info"]["availability"] == "Available"
    assert result["stock_info"]["total_stock"] == 42
    
    assert len(result["warehouse_stock"]) == 2
    assert result["warehouse_stock"][0]["id"] == "w1"
    assert result["warehouse_stock"][1]["stock"] == 27
    
    assert result["review_ratings"] == [5, 4, 5]
    assert result["average_rating"] == 4.67  # Average of [5, 4, 5]
