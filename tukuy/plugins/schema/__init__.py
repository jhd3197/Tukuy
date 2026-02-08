"""JSON Schema plugin.

Provides JSON Schema validation, schema inference from data, and schema
comparison.
Pure stdlib — no external dependencies (uses a lightweight built-in
validator rather than requiring ``jsonschema``).
"""

import json
import re
from typing import Any, Dict, List, Optional, Union

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


# ── Lightweight JSON Schema validator (subset) ────────────────────────────

def _validate_value(value: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    """Validate a value against a JSON Schema (subset).

    Supports: type, enum, required, properties, items, minLength,
    maxLength, minimum, maximum, pattern, minItems, maxItems, oneOf,
    anyOf, allOf, const, not.
    """
    errors: List[str] = []

    if "const" in schema:
        if value != schema["const"]:
            errors.append(f"{path}: expected const {schema['const']!r}, got {value!r}")
        return errors

    if "enum" in schema:
        if value not in schema["enum"]:
            errors.append(f"{path}: value {value!r} not in enum {schema['enum']}")

    if "not" in schema:
        sub_errors = _validate_value(value, schema["not"], path)
        if not sub_errors:
            errors.append(f"{path}: value must NOT match the 'not' schema")

    if "allOf" in schema:
        for i, sub in enumerate(schema["allOf"]):
            errors.extend(_validate_value(value, sub, f"{path}/allOf[{i}]"))

    if "anyOf" in schema:
        if not any(not _validate_value(value, sub, path) for sub in schema["anyOf"]):
            errors.append(f"{path}: value does not match any of 'anyOf' schemas")

    if "oneOf" in schema:
        match_count = sum(1 for sub in schema["oneOf"] if not _validate_value(value, sub, path))
        if match_count != 1:
            errors.append(f"{path}: value must match exactly one of 'oneOf' schemas (matched {match_count})")

    schema_type = schema.get("type")
    if schema_type:
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        expected = type_map.get(schema_type)
        if expected and not isinstance(value, expected):
            # int should not match boolean
            if schema_type == "integer" and isinstance(value, bool):
                errors.append(f"{path}: expected {schema_type}, got {type(value).__name__}")
            elif not isinstance(value, expected):
                errors.append(f"{path}: expected {schema_type}, got {type(value).__name__}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string length {len(value)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: string length {len(value)} > maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: string does not match pattern '{schema['pattern']}'")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: value {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: value {value} > maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: value {value} <= exclusiveMinimum {schema['exclusiveMinimum']}")
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            errors.append(f"{path}: value {value} >= exclusiveMaximum {schema['exclusiveMaximum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: array length {len(value)} < minItems {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: array length {len(value)} > maxItems {schema['maxItems']}")
        if "items" in schema:
            for i, item in enumerate(value):
                errors.extend(_validate_value(item, schema["items"], f"{path}[{i}]"))

    if isinstance(value, dict):
        if "required" in schema:
            for req in schema["required"]:
                if req not in value:
                    errors.append(f"{path}: missing required property '{req}'")
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if prop_name in value:
                    errors.extend(_validate_value(value[prop_name], prop_schema, f"{path}.{prop_name}"))
        if "additionalProperties" in schema and schema["additionalProperties"] is False:
            allowed = set(schema.get("properties", {}).keys())
            for key in value:
                if key not in allowed:
                    errors.append(f"{path}: additional property '{key}' not allowed")

    return errors


# ── Schema inference ──────────────────────────────────────────────────────

def _infer_type(value: Any) -> Dict[str, Any]:
    """Infer a JSON Schema from a single Python value."""
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {}}
        item_schemas = [_infer_type(item) for item in value]
        # If all items share the same type, merge
        types = {s.get("type") for s in item_schemas}
        if len(types) == 1 and types != {None}:
            merged = item_schemas[0]
            if merged.get("type") == "object":
                merged = _merge_object_schemas(item_schemas)
            return {"type": "array", "items": merged}
        return {"type": "array", "items": {}}
    if isinstance(value, dict):
        properties = {}
        required = []
        for k, v in value.items():
            properties[k] = _infer_type(v)
            required.append(k)
        schema: Dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = sorted(required)
        return schema
    return {}


def _merge_object_schemas(schemas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple object schemas (from array items) into one."""
    all_props: Dict[str, List[Dict[str, Any]]] = {}
    all_keys: set = set()
    for s in schemas:
        props = s.get("properties", {})
        for k, v in props.items():
            all_props.setdefault(k, []).append(v)
            all_keys.add(k)

    properties = {}
    required = []
    for k in sorted(all_keys):
        prop_schemas = all_props[k]
        # Use first schema as representative
        properties[k] = prop_schemas[0]
        # Only required if present in ALL schemas
        if len(prop_schemas) == len(schemas):
            required.append(k)

    result: Dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        result["required"] = sorted(required)
    return result


# ── Transformers ──────────────────────────────────────────────────────────

class JsonSchemaValidateTransformer(ChainableTransformer[Any, dict]):
    """Validate a value (or JSON string) against a JSON Schema.

    Returns ``{"valid": bool, "errors": [...], "error_count": int}``.
    """

    def __init__(self, name: str, schema: Optional[Dict] = None):
        super().__init__(name)
        self.schema = schema or {}

    def validate(self, value: Any) -> bool:
        return True

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> dict:
        # If value is a JSON string, parse it
        data = value
        if isinstance(value, str):
            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                return {"valid": False, "errors": ["Input is not valid JSON"], "error_count": 1}

        errors = _validate_value(data, self.schema)
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "error_count": len(errors),
        }


class InferSchemaTransformer(ChainableTransformer[Any, dict]):
    """Infer a JSON Schema from sample data.

    Accepts a Python value or a JSON string.
    """

    def validate(self, value: Any) -> bool:
        return True

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> dict:
        data = value
        if isinstance(value, str):
            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                return {"type": "string"}

        return _infer_type(data)


class SchemaDiffTransformer(ChainableTransformer[dict, dict]):
    """Compare two JSON Schemas and report differences.

    Expects input as ``{"a": {...}, "b": {...}}`` (both JSON Schema dicts).
    Returns ``{"added": [...], "removed": [...], "changed": [...]}``.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "a" in value and "b" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> dict:
        a = value["a"] if isinstance(value["a"], dict) else {}
        b = value["b"] if isinstance(value["b"], dict) else {}

        changes: Dict[str, list] = {"added": [], "removed": [], "changed": []}
        self._compare(a, b, "$", changes)
        return changes

    def _compare(self, a: Dict, b: Dict, path: str, changes: Dict[str, list]) -> None:
        a_props = a.get("properties", {})
        b_props = b.get("properties", {})

        # Type change at current level
        if a.get("type") != b.get("type"):
            changes["changed"].append({
                "path": path,
                "field": "type",
                "from": a.get("type"),
                "to": b.get("type"),
            })

        # Required changes
        a_req = set(a.get("required", []))
        b_req = set(b.get("required", []))
        for r in b_req - a_req:
            changes["changed"].append({"path": path, "field": "required", "added": r})
        for r in a_req - b_req:
            changes["changed"].append({"path": path, "field": "required", "removed": r})

        # Added / removed properties
        for key in set(b_props) - set(a_props):
            changes["added"].append({"path": f"{path}.{key}", "schema": b_props[key]})
        for key in set(a_props) - set(b_props):
            changes["removed"].append({"path": f"{path}.{key}", "schema": a_props[key]})

        # Recurse into shared properties
        for key in set(a_props) & set(b_props):
            child_path = f"{path}.{key}"
            if a_props[key] != b_props[key]:
                if a_props[key].get("type") == "object" and b_props[key].get("type") == "object":
                    self._compare(a_props[key], b_props[key], child_path, changes)
                else:
                    changes["changed"].append({
                        "path": child_path,
                        "from": a_props[key],
                        "to": b_props[key],
                    })

        # Items schema (for arrays)
        a_items = a.get("items", {})
        b_items = b.get("items", {})
        if a_items != b_items and (a_items or b_items):
            if isinstance(a_items, dict) and isinstance(b_items, dict):
                if a_items.get("type") == "object" and b_items.get("type") == "object":
                    self._compare(a_items, b_items, f"{path}[]", changes)
                elif a_items != b_items:
                    changes["changed"].append({
                        "path": f"{path}[]",
                        "from": a_items,
                        "to": b_items,
                    })


class SchemaPlugin(TransformerPlugin):
    """Plugin providing JSON Schema validation and inference."""

    def __init__(self):
        super().__init__("schema")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "json_schema_validate": lambda params: JsonSchemaValidateTransformer(
                "json_schema_validate",
                schema=params.get("schema"),
            ),
            "infer_schema": lambda _: InferSchemaTransformer("infer_schema"),
            "schema_diff": lambda _: SchemaDiffTransformer("schema_diff"),
        }
