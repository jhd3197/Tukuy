"""Mermaid diagram generation plugin.

Provides transformers that convert structured data (dicts/lists) into
Mermaid diagram syntax for flowcharts, sequence diagrams, ERDs, class
diagrams, Gantt charts, and pie charts.

Pure stdlib — no external dependencies.
"""

from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin


def _escape(text: str) -> str:
    """Escape special Mermaid characters in labels."""
    return text.replace('"', '#quot;').replace("(", "#40;").replace(")", "#41;")


class MermaidFlowchartTransformer(ChainableTransformer[dict, str]):
    """Generate a Mermaid flowchart from structured data.

    Expects input as::

        {
            "direction": "TD",   # TD, LR, BT, RL
            "nodes": [
                {"id": "A", "text": "Start", "shape": "round"},
                {"id": "B", "text": "Process"},
                {"id": "C", "text": "Decision", "shape": "diamond"},
                {"id": "D", "text": "End", "shape": "round"},
            ],
            "edges": [
                {"from": "A", "to": "B"},
                {"from": "B", "to": "C"},
                {"from": "C", "to": "D", "label": "Yes"},
                {"from": "C", "to": "B", "label": "No"},
            ]
        }

    Shapes: "default" (rectangle), "round", "stadium", "diamond",
    "hexagon", "parallelogram", "circle", "double_circle".
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "nodes" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        direction = value.get("direction", "TD")
        nodes = value.get("nodes", [])
        edges = value.get("edges", [])

        lines = [f"flowchart {direction}"]

        shape_map = {
            "default": ("[", "]"),
            "round": ("(", ")"),
            "stadium": ("([", "])"),
            "diamond": ("{", "}"),
            "hexagon": ("{{", "}}"),
            "parallelogram": ("[/", "/]"),
            "circle": ("((", "))"),
            "double_circle": ("(((", ")))"),
        }

        for node in nodes:
            nid = node["id"]
            text = _escape(node.get("text", nid))
            shape = node.get("shape", "default")
            left, right = shape_map.get(shape, ("[", "]"))
            lines.append(f"    {nid}{left}\"{text}\"{right}")

        for edge in edges:
            src = edge["from"]
            dst = edge["to"]
            label = edge.get("label", "")
            style = edge.get("style", "solid")

            if style == "dotted":
                arrow = "-.->"
            elif style == "thick":
                arrow = "==>"
            else:
                arrow = "-->"

            if label:
                lines.append(f"    {src} {arrow}|{_escape(label)}| {dst}")
            else:
                lines.append(f"    {src} {arrow} {dst}")

        return "\n".join(lines)


class MermaidSequenceTransformer(ChainableTransformer[dict, str]):
    """Generate a Mermaid sequence diagram from structured data.

    Expects input as::

        {
            "participants": ["Alice", "Bob", "Server"],
            "messages": [
                {"from": "Alice", "to": "Bob", "text": "Hello", "type": "solid"},
                {"from": "Bob", "to": "Server", "text": "Request", "type": "solid"},
                {"from": "Server", "to": "Bob", "text": "Response", "type": "dashed"},
                {"from": "Bob", "to": "Alice", "text": "Done", "type": "solid"},
            ]
        }

    Types: "solid", "dashed", "solid_arrow", "dashed_arrow",
    "solid_cross", "dashed_cross".
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "messages" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        participants = value.get("participants", [])
        messages = value.get("messages", [])
        title = value.get("title", "")

        lines = ["sequenceDiagram"]

        if title:
            lines.append(f"    title {title}")

        for p in participants:
            if isinstance(p, dict):
                lines.append(f"    participant {p['id']} as {p.get('label', p['id'])}")
            else:
                lines.append(f"    participant {p}")

        arrow_map = {
            "solid": "->>",
            "dashed": "-->>",
            "solid_arrow": "->>",
            "dashed_arrow": "-->>",
            "solid_cross": "-x",
            "dashed_cross": "--x",
            "solid_open": "->",
            "dashed_open": "-->",
        }

        for msg in messages:
            src = msg["from"]
            dst = msg["to"]
            text = msg.get("text", "")
            msg_type = msg.get("type", "solid")
            arrow = arrow_map.get(msg_type, "->>")

            if msg.get("activate"):
                lines.append(f"    activate {dst}")

            lines.append(f"    {src}{arrow}{dst}: {text}")

            if msg.get("deactivate"):
                lines.append(f"    deactivate {dst}")

            # Notes
            if "note" in msg:
                note_pos = msg.get("note_position", "right of")
                note_target = msg.get("note_target", dst)
                lines.append(f"    Note {note_pos} {note_target}: {msg['note']}")

        # Loops, alts, opts
        return "\n".join(lines)


class MermaidErdTransformer(ChainableTransformer[dict, str]):
    """Generate a Mermaid entity-relationship diagram from structured data.

    Expects input as::

        {
            "entities": [
                {
                    "name": "CUSTOMER",
                    "attributes": [
                        {"name": "id", "type": "int", "key": "PK"},
                        {"name": "name", "type": "string"},
                    ]
                },
                {
                    "name": "ORDER",
                    "attributes": [
                        {"name": "id", "type": "int", "key": "PK"},
                        {"name": "customer_id", "type": "int", "key": "FK"},
                    ]
                }
            ],
            "relationships": [
                {"from": "CUSTOMER", "to": "ORDER", "label": "places",
                 "from_cardinality": "||", "to_cardinality": "o{"}
            ]
        }

    Cardinalities: "||" (exactly one), "o|" (zero or one),
    "}|" (one or more), "o{" (zero or more).
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "entities" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        entities = value.get("entities", [])
        relationships = value.get("relationships", [])

        lines = ["erDiagram"]

        for entity in entities:
            name = entity["name"]
            attrs = entity.get("attributes", [])
            if attrs:
                lines.append(f"    {name} {{")
                for attr in attrs:
                    atype = attr.get("type", "string")
                    aname = attr.get("name", "")
                    key = attr.get("key", "")
                    comment = f' "{attr["comment"]}"' if "comment" in attr else ""
                    key_str = f" {key}" if key else ""
                    lines.append(f"        {atype} {aname}{key_str}{comment}")
                lines.append("    }")
            else:
                lines.append(f"    {name}")

        for rel in relationships:
            src = rel["from"]
            dst = rel["to"]
            label = rel.get("label", "relates")
            fc = rel.get("from_cardinality", "||")
            tc = rel.get("to_cardinality", "o{")
            lines.append(f"    {src} {fc}--{tc} {dst} : \"{label}\"")

        return "\n".join(lines)


class MermaidClassTransformer(ChainableTransformer[dict, str]):
    """Generate a Mermaid class diagram from structured data.

    Expects input as::

        {
            "classes": [
                {
                    "name": "Animal",
                    "attributes": ["+String name", "#int age"],
                    "methods": ["+speak() String", "+move() void"],
                },
                {
                    "name": "Dog",
                    "attributes": ["+String breed"],
                    "methods": ["+speak() String"],
                }
            ],
            "relationships": [
                {"from": "Dog", "to": "Animal", "type": "inheritance"},
            ]
        }

    Relationship types: "inheritance", "composition", "aggregation",
    "association", "dependency", "realization".
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "classes" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        classes = value.get("classes", [])
        relationships = value.get("relationships", [])

        lines = ["classDiagram"]

        for cls in classes:
            name = cls["name"]
            lines.append(f"    class {name} {{")
            for attr in cls.get("attributes", []):
                lines.append(f"        {attr}")
            for method in cls.get("methods", []):
                lines.append(f"        {method}")
            lines.append("    }")

        rel_map = {
            "inheritance": "<|--",
            "composition": "*--",
            "aggregation": "o--",
            "association": "-->",
            "dependency": "..>",
            "realization": "..|>",
        }

        for rel in relationships:
            src = rel["from"]
            dst = rel["to"]
            rel_type = rel.get("type", "association")
            arrow = rel_map.get(rel_type, "-->")
            label = rel.get("label", "")
            if label:
                lines.append(f"    {dst} {arrow} {src} : {label}")
            else:
                lines.append(f"    {dst} {arrow} {src}")

        return "\n".join(lines)


class MermaidGanttTransformer(ChainableTransformer[dict, str]):
    """Generate a Mermaid Gantt chart from structured data.

    Expects input as::

        {
            "title": "Project Plan",
            "date_format": "YYYY-MM-DD",
            "sections": [
                {
                    "name": "Design",
                    "tasks": [
                        {"name": "Mockups", "start": "2024-01-01", "duration": "7d"},
                        {"name": "Review", "after": "Mockups", "duration": "3d"},
                    ]
                }
            ]
        }
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "sections" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        title = value.get("title", "")
        date_format = value.get("date_format", "YYYY-MM-DD")
        sections = value.get("sections", [])

        lines = ["gantt"]
        if title:
            lines.append(f"    title {title}")
        lines.append(f"    dateFormat {date_format}")

        for section in sections:
            lines.append(f"    section {section['name']}")
            for task in section.get("tasks", []):
                name = task["name"]
                status = task.get("status", "")
                task_id = task.get("id", "")

                parts = [name]
                if status:
                    parts.append(status)
                if task_id:
                    parts.append(task_id)
                if "after" in task:
                    parts.append(f"after {task['after']}")
                elif "start" in task:
                    parts.append(task["start"])
                if "duration" in task:
                    parts.append(task["duration"])
                elif "end" in task:
                    parts.append(task["end"])

                lines.append(f"    {' , '.join(parts)}")

        return "\n".join(lines)


class MermaidPieTransformer(ChainableTransformer[dict, str]):
    """Generate a Mermaid pie chart from structured data.

    Expects input as::

        {
            "title": "Market Share",
            "data": {"Chrome": 65, "Firefox": 15, "Safari": 12, "Other": 8}
        }

    Or with a list format:

        {
            "title": "Sales",
            "data": [{"label": "Q1", "value": 25}, {"label": "Q2", "value": 30}]
        }
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "data" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        title = value.get("title", "")
        data = value["data"]

        lines = ["pie"]
        if title:
            lines.append(f"    title {title}")

        if isinstance(data, dict):
            for label, val in data.items():
                lines.append(f'    "{label}" : {val}')
        elif isinstance(data, list):
            for item in data:
                label = item.get("label", "")
                val = item.get("value", 0)
                lines.append(f'    "{label}" : {val}')

        return "\n".join(lines)


class MermaidStateDiagramTransformer(ChainableTransformer[dict, str]):
    """Generate a Mermaid state diagram from structured data.

    Expects input as::

        {
            "states": [
                {"id": "Idle", "description": "Waiting for input"},
                {"id": "Processing"},
                {"id": "Done"},
            ],
            "transitions": [
                {"from": "[*]", "to": "Idle"},
                {"from": "Idle", "to": "Processing", "label": "start"},
                {"from": "Processing", "to": "Done", "label": "complete"},
                {"from": "Done", "to": "[*]"},
            ]
        }
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "transitions" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        states = value.get("states", [])
        transitions = value.get("transitions", [])
        direction = value.get("direction", "")

        lines = ["stateDiagram-v2"]
        if direction:
            lines.append(f"    direction {direction}")

        for state in states:
            sid = state["id"]
            desc = state.get("description", "")
            if desc:
                lines.append(f"    {sid} : {desc}")

        for t in transitions:
            src = t["from"]
            dst = t["to"]
            label = t.get("label", "")
            if label:
                lines.append(f"    {src} --> {dst} : {label}")
            else:
                lines.append(f"    {src} --> {dst}")

        return "\n".join(lines)


class MermaidPlugin(TransformerPlugin):
    """Plugin providing Mermaid diagram generation from structured data."""

    def __init__(self):
        super().__init__("mermaid")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "mermaid_flowchart": lambda _: MermaidFlowchartTransformer("mermaid_flowchart"),
            "mermaid_sequence": lambda _: MermaidSequenceTransformer("mermaid_sequence"),
            "mermaid_erd": lambda _: MermaidErdTransformer("mermaid_erd"),
            "mermaid_class_diagram": lambda _: MermaidClassTransformer("mermaid_class_diagram"),
            "mermaid_gantt": lambda _: MermaidGanttTransformer("mermaid_gantt"),
            "mermaid_pie": lambda _: MermaidPieTransformer("mermaid_pie"),
            "mermaid_state_diagram": lambda _: MermaidStateDiagramTransformer("mermaid_state_diagram"),
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest
        return PluginManifest(
            name="mermaid",
            display_name="Mermaid Diagrams",
            description="Generate Mermaid flowcharts, sequence diagrams, ERDs, and more.",
            icon="workflow",
            group="Web",
        )
