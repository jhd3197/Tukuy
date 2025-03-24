"""JSON transformation implementations."""

import json
from typing import Any, Dict, List, Optional, Union
import re

from ..base import BaseTransformer, ChainableTransformer, CoreToolsTransformer
from ..types import JsonType, Pattern, TransformContext
from ..exceptions import ValidationError, TransformationError, ParseError

class JsonParser(ChainableTransformer[str, JsonType]):
    """
    Parses JSON strings into Python objects.
    
    Features:
    - Strict/lenient parsing modes
    - Schema validation
    - Error handling with detailed messages
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
    Extracts data from JSON structures using patterns.
    
    Features:
    - JSONPath-like syntax for data extraction
    - Nested property access
    - Array operations
    - Default values
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
