"""JSON transformation implementations."""

import json
from typing import Any, Dict, List, Optional, Union
import re

from ..base import BaseTransformer, ChainableTransformer, CoreToolsTransformer
from ..types import JsonType, Pattern, TransformContext
from ..exceptions import ValidationError, TransformationError, ParseError

class JsonParser(ChainableTransformer[str, JsonType]):
    """
    Description:
        A transformer that parses JSON strings into Python objects with support for
        strict/lenient parsing modes and optional schema validation.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        strict (bool): Whether to raise errors for invalid JSON (default: True)
        schema (Optional[Dict[str, Any]]): JSON schema for validation
    
    Returns:
        JsonType: The parsed JSON data as Python objects (dict, list, str, int, float, bool, None)
    
    Raises:
        ValidationError: If the input value is not a string or if schema validation fails
        ParseError: If strict=True and the JSON string is invalid
    
    Notes:
        Schema validation supports:
        - Basic types: object, array, string, number, boolean, null
        - Required properties
        - Nested objects and arrays
        - Property type checking
    
    Example:
        ```python
        # Basic JSON parsing
        parser = JsonParser("parser")
        result = parser.transform('{"name": "John", "age": 30}')
        assert result.value == {"name": "John", "age": 30}
        
        # With schema validation
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"}
            },
            "required": ["name"]
        }
        
        validator = JsonParser(
            "validator",
            strict=True,
            schema=schema
        )
        
        # Valid JSON with schema
        result = validator.transform('{"name": "John", "age": 30}')
        assert result.value == {"name": "John", "age": 30}
        
        # Invalid JSON (will raise ParseError)
        try:
            validator.transform('{"name": "John", age: 30}')
        except ParseError:
            print("Invalid JSON syntax")
            
        # Schema validation failure (will raise ValidationError)
        try:
            validator.transform('{"age": 30}')  # Missing required "name"
        except ValidationError:
            print("Schema validation failed")
        ```
    """
    
    def __init__(
        self,
        name: str,
        strict: bool = True,
        schema: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name)
        self.strict = strict
        self.schema = schema
    
    def validate(self, value: str) -> bool:
        """
        Validate that the input is a JSON string.
        
        In the validate method, we just check if the input is a string.
        Actual JSON validity and schema validation is performed in _transform.
        """
        return isinstance(value, str)
    
    def _transform(self, value: str, context: Optional[TransformContext] = None) -> JsonType:
        """
        Transform a JSON string into a Python object.
        
        Args:
            value: A JSON string
            context: Optional transformation context
            
        Returns:
            Parsed JSON data
            
        Raises:
            ParseError: If the JSON string is invalid and strict=True
            ValidationError: If the JSON data does not match the schema
        """
        try:
            data = json.loads(value)
        except json.JSONDecodeError as e:
            if self.strict:
                raise ParseError(f"Invalid JSON: {str(e)}", value)
            return value
            
        if self.schema:
            if not self._validate_schema(data, self.schema):
                raise ValidationError("JSON data does not match schema", value)
        return data
    
    def _validate_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Simple schema validation."""
        if not isinstance(schema, dict):
            return True
            
        if 'type' in schema:
            expected_type = schema['type']
            if expected_type == 'object' and not isinstance(data, dict):
                return False
            elif expected_type == 'array' and not isinstance(data, list):
                return False
            elif expected_type == 'string' and not isinstance(data, str):
                return False
            elif expected_type == 'number' and not isinstance(data, (int, float)):
                return False
            elif expected_type == 'boolean' and not isinstance(data, bool):
                return False
            elif expected_type == 'null' and data is not None:
                return False
                
        if 'properties' in schema and isinstance(data, dict):
            for key, prop_schema in schema['properties'].items():
                if key not in data:
                    if schema.get('required', [key]):  # Consider property required by default or if in required list
                        return False
                    continue
                if not self._validate_schema(data[key], prop_schema):
                    return False
                    
        if 'items' in schema and isinstance(data, list):
            item_schema = schema['items']
            return all(self._validate_schema(item, item_schema) for item in data)
            
        return True

class JsonExtractor(BaseTransformer[JsonType, Any]):
    """
    Description:
        A transformer that extracts data from JSON structures using a pattern-based
        approach. Supports complex path expressions, nested property access, array
        operations, and fallback values.
    
    Version: v1
    Status: Production
    Last Updated: 2024-03-24
    
    Args:
        name (str): Unique identifier for this transformer
        pattern (Pattern): Pattern describing what data to extract
        default (Any): Default value to use when a property is not found
    
    Returns:
        Any: The extracted data according to the pattern
    
    Raises:
        TransformationError: If extraction fails or transformations fail
    
    Notes:
        Path Expression Syntax:
        - Simple key: "user.name"
        - Array index: "users[0].name"
        - Array wildcard: "users[*].name"
        - Nested arrays: "data.users[*].posts[*].title"
        
        Pattern Structure:
        ```python
        {
            "properties": [
                {
                    "name": "output_field_name",
                    "selector": {
                        "primary": "path.to.data",
                        "fallback": ["alternate.path", "another.path"]
                    },
                    "type": "string|number|boolean|array|object",
                    "transform": [
                        {"function": "transform_name", "params": {...}}
                    ]
                }
            ]
        }
        ```
    
    Example:
        ```python
        # Create an extractor for user data
        pattern = {
            "properties": [
                {
                    "name": "username",
                    "selector": "user.profile.username",
                    "fallback": "user.name"
                },
                {
                    "name": "posts",
                    "selector": "user.posts[*].title",
                    "type": "array"
                },
                {
                    "name": "info",
                    "type": "object",
                    "properties": [
                        {
                            "name": "email",
                            "selector": "user.email"
                        },
                        {
                            "name": "age",
                            "selector": "user.age",
                            "type": "number"
                        }
                    ]
                }
            ]
        }
        
        extractor = JsonExtractor(
            "user_extractor",
            pattern=pattern,
            default=None
        )
        
        # Sample data
        data = {
            "user": {
                "name": "john_doe",
                "email": "john@example.com",
                "age": 30,
                "posts": [
                    {"title": "First Post"},
                    {"title": "Second Post"}
                ]
            }
        }
        
        # Extract data
        result = extractor.transform(data)
        assert result.value == {
            "username": "john_doe",
            "posts": ["First Post", "Second Post"],
            "info": {
                "email": "john@example.com",
                "age": 30
            }
        }
        ```
    """
    
    def __init__(
        self,
        name: str,
        pattern: Pattern,
        default: Any = None
    ):
        super().__init__(name)
        self.pattern = pattern
        self.default = default
    
    def validate(self, value: JsonType) -> bool:
        return True  # Accept any JSON-compatible value
    
    def _transform(self, value: JsonType, context: Optional[TransformContext] = None) -> Any:
        try:
            return self._extract_data(value, self.pattern)
        except Exception as e:
            raise TransformationError(f"JSON extraction failed: {str(e)}", value)
    
    def _extract_data(self, data: JsonType, pattern: Pattern) -> Any:
        """Extract data according to the pattern."""
        if not isinstance(pattern, dict):
            return data
            
        result = {}
        for prop in pattern.get('properties', []):
            name = prop.get('name')
            if not name:
                continue
                
            selector = prop.get('selector', {})
            if isinstance(selector, str):
                selector = {'primary': selector}
                
            primary = selector.get('primary')
            fallback = selector.get('fallback', [])
            prop_type = prop.get('type', 'string')
            transforms = prop.get('transform', [])
            
            # Handle nested properties
            if prop_type == 'object' and 'properties' in prop:
                value = self._get_value(data, primary)
                if value is None and fallback:
                    for fb in ([fallback] if isinstance(fallback, str) else fallback):
                        value = self._get_value(data, fb)
                        if value is not None:
                            break
                            
                if value is not None:
                    result[name] = self._extract_data(value, {'properties': prop['properties']})
                continue
            
            # Handle arrays
            if prop_type == 'array':
                values = self._get_array_values(data, primary)
                if not values and fallback:
                    for fb in ([fallback] if isinstance(fallback, str) else fallback):
                        values = self._get_array_values(data, fb)
                        if values:
                            break
                            
                result[name] = values
                continue
            
            # Handle single values
            value = self._get_value(data, primary)
            if value is None and fallback:
                for fb in ([fallback] if isinstance(fallback, str) else fallback):
                    value = self._get_value(data, fb)
                    if value is not None:
                        break
            
            # Apply transformations if any
            if value is not None and transforms:
                tools = CoreToolsTransformer()
                try:
                    value = tools.transform(value, transforms)
                    # Extract the actual value from TransformResult if needed
                    if hasattr(value, 'value') and hasattr(value, 'failed'):
                        value = value.value
                except Exception as e:
                    raise TransformationError(f"Failed to apply transformation: {str(e)}", value)
                        
            result[name] = value if value is not None else self.default
        
        return result
    
    def _get_value(self, data: JsonType, path: Optional[str]) -> Optional[Any]:
        """Get a value using a path expression."""
        if not path or data is None:
            return None
            
        try:
            current = data
            
            # Handle array wildcard at top level
            if path == '[*]':
                return data if isinstance(data, list) else None
            
            # Handle array wildcards in the middle of the path
            if '[*]' in path:
                before, after = path.split('[*]', 1)
                if before:
                    current = self._get_value(current, before)
                if not isinstance(current, list):
                    return None
                if not after:
                    return current
                return [self._get_value(item, after.lstrip('.')) for item in current]
            
            # Handle simple key access
            if '.' not in path and '[' not in path:
                return current.get(path) if isinstance(current, dict) else None
            
            # Handle complex paths
            parts = re.split(r'\.(?![^\[]*\])', path)
            for part in parts:
                if not part:
                    continue
                
                # Handle array indexing
                match = re.match(r'(.+?)\[(.+?)\]', part)
                if match:
                    key, index = match.groups()
                    current = current.get(key, {})
                    try:
                        idx = int(index)
                        current = current[idx] if isinstance(current, list) and 0 <= idx < len(current) else None
                    except (ValueError, TypeError):
                        current = None
                else:
                    current = current.get(part) if isinstance(current, dict) else None
                
                if current is None:
                    break
            
            return current
            
        except Exception as e:
            raise TransformationError(f"Failed to get value at path {path}: {str(e)}", data)
    
    def _get_array_values(self, data: JsonType, path: Optional[str]) -> List[Any]:
        """Get array values using a path expression."""
        value = self._get_value(data, path)
        if isinstance(value, list):
            return value
        return [value] if value is not None else None