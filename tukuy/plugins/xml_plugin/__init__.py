"""XML plugin.

Skills-only plugin providing XML read, write, XPath query,
validation, and to-JSON conversion operations.

Pure stdlib — no external dependencies (uses ``xml.etree.ElementTree``).
All skills declare ``requires_filesystem=True`` for SafetyPolicy enforcement.
"""

import json
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Union

from ...plugins.base import TransformerPlugin
from ...safety import check_read_path, check_write_path
from ...skill import skill, ConfigParam, RiskLevel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _element_to_dict(element: ET.Element) -> Dict[str, Any]:
    """Recursively convert an XML Element into a Python dict.

    - Element tag → dict key
    - Text content → ``"#text"`` key
    - Attributes → ``"@attr"`` keys
    - Repeated child tags → list
    """
    result: Dict[str, Any] = {}

    # Attributes
    for attr_name, attr_value in element.attrib.items():
        result[f"@{attr_name}"] = attr_value

    # Children
    children: Dict[str, List[Any]] = {}
    for child in element:
        child_dict = _element_to_dict(child)
        children.setdefault(child.tag, []).append(child_dict)

    for tag, items in children.items():
        result[tag] = items if len(items) > 1 else items[0]

    # Text content
    text = (element.text or "").strip()
    if text:
        if result:
            result["#text"] = text
        else:
            result = text  # type: ignore[assignment]

    return result


def _dict_to_element(tag: str, data: Any) -> ET.Element:
    """Recursively convert a Python dict/value into an XML Element."""
    element = ET.Element(tag)

    if isinstance(data, dict):
        for key, value in data.items():
            if key.startswith("@"):
                element.set(key[1:], str(value))
            elif key == "#text":
                element.text = str(value)
            elif isinstance(value, list):
                for item in value:
                    element.append(_dict_to_element(key, item))
            else:
                element.append(_dict_to_element(key, value))
    elif isinstance(data, list):
        for item in data:
            element.append(_dict_to_element("item", item))
    else:
        element.text = str(data)

    return element


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

@skill(
    name="xml_read",
    description="Read an XML file and convert it to a nested dict.",
    category="data",
    tags=["xml", "read", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="Read XML",
    icon="file-code-2",
    risk_level=RiskLevel.SAFE,
    group="XML Operations",
)
def xml_read(path: str) -> dict:
    """Read an XML file and return a nested dict."""
    path = check_read_path(path)
    tree = ET.parse(path)
    root = tree.getroot()
    data = {root.tag: _element_to_dict(root)}
    return {"path": path, "data": data}


@skill(
    name="xml_write",
    description="Write a dict as an XML file.",
    category="data",
    tags=["xml", "write", "data"],
    side_effects=True,
    requires_filesystem=True,
    display_name="Write XML",
    icon="file-code-2",
    risk_level=RiskLevel.MODERATE,
    group="XML Operations",
    config_params=[
        ConfigParam(
            name="root_tag",
            display_name="Root Tag",
            description="Name of the root XML element.",
            type="string",
            default="root",
        ),
    ],
)
def xml_write(path: str, data: Any = None, root_tag: str = "root") -> dict:
    """Write a dict as XML to a file."""
    path = check_write_path(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    root = _dict_to_element(root_tag, data)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="unicode", xml_declaration=True)
    size = os.path.getsize(path)
    return {"path": path, "bytes_written": size}


@skill(
    name="xml_xpath",
    description="Query an XML file using an XPath expression.",
    category="data",
    tags=["xml", "xpath", "query", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="XPath Query",
    icon="search",
    risk_level=RiskLevel.SAFE,
    group="XML Operations",
)
def xml_xpath(path: str, expression: str) -> dict:
    """Query an XML file with an XPath expression and return matching elements."""
    path = check_read_path(path)
    tree = ET.parse(path)
    root = tree.getroot()
    elements = root.findall(expression)
    matches = [_element_to_dict(el) for el in elements]
    return {"matches": matches, "count": len(matches)}


@skill(
    name="xml_validate",
    description="Check if a file contains well-formed XML.",
    category="data",
    tags=["xml", "validate", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="Validate XML",
    icon="file-check",
    risk_level=RiskLevel.SAFE,
    group="XML Operations",
)
def xml_validate(path: str) -> dict:
    """Validate whether a file is well-formed XML."""
    path = check_read_path(path)
    try:
        ET.parse(path)
        return {"valid": True, "error": None, "path": path}
    except ET.ParseError as exc:
        return {"valid": False, "error": str(exc), "path": path}


@skill(
    name="xml_to_json",
    description="Convert an XML file to a JSON dict.",
    category="data",
    tags=["xml", "json", "convert", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="XML to JSON",
    icon="file-code-2",
    risk_level=RiskLevel.SAFE,
    group="XML Operations",
)
def xml_to_json(path: str) -> dict:
    """Convert an XML file to a JSON representation."""
    path = check_read_path(path)
    tree = ET.parse(path)
    root = tree.getroot()
    data = {root.tag: _element_to_dict(root)}
    json_string = json.dumps(data, indent=2, ensure_ascii=False)
    return {"data": data, "json_string": json_string}


class XmlPlugin(TransformerPlugin):
    """Plugin providing XML file operation skills (no transformers)."""

    def __init__(self):
        super().__init__("xml")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "xml_read": xml_read.__skill__,
            "xml_write": xml_write.__skill__,
            "xml_xpath": xml_xpath.__skill__,
            "xml_validate": xml_validate.__skill__,
            "xml_to_json": xml_to_json.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="xml",
            display_name="XML",
            description="Read, write, query, validate, and convert XML files.",
            icon="file-code-2",
            color="#f97316",
            group="Data",
            requires=PluginRequirements(filesystem=True),
        )
