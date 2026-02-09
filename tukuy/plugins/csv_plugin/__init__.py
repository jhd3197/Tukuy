"""CSV plugin.

Skills-only plugin providing CSV read, write, query, headers,
and stats operations.

Pure stdlib — no external dependencies.
All skills declare ``requires_filesystem=True`` for SafetyPolicy enforcement.
"""

import csv
import io
import os
import statistics as _stats
from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_read_path, check_write_path
from ...skill import skill, ConfigParam, ConfigScope, RiskLevel


@skill(
    name="csv_read",
    description="Read a CSV file and return its headers and rows as a list of dicts.",
    category="data",
    tags=["csv", "read", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="Read CSV",
    icon="table",
    risk_level=RiskLevel.SAFE,
    group="CSV Operations",
    config_params=[
        ConfigParam(
            name="delimiter",
            display_name="Delimiter",
            description="Column delimiter character.",
            type="string",
            default=",",
        ),
        ConfigParam(
            name="encoding",
            display_name="Encoding",
            description="File encoding to use.",
            type="select",
            default="utf-8",
            options=["utf-8", "ascii", "latin-1", "utf-16"],
        ),
    ],
)
def csv_read(path: str, delimiter: str = ",", encoding: str = "utf-8") -> dict:
    """Read a CSV file and return headers + rows."""
    path = check_read_path(path)
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = reader.fieldnames or []
        rows = list(reader)
    return {"headers": list(headers), "rows": rows, "row_count": len(rows)}


@skill(
    name="csv_write",
    description="Write a list of dicts to a CSV file.",
    category="data",
    tags=["csv", "write", "data"],
    side_effects=True,
    requires_filesystem=True,
    display_name="Write CSV",
    icon="table",
    risk_level=RiskLevel.MODERATE,
    group="CSV Operations",
    config_params=[
        ConfigParam(
            name="delimiter",
            display_name="Delimiter",
            description="Column delimiter character.",
            type="string",
            default=",",
        ),
        ConfigParam(
            name="encoding",
            display_name="Encoding",
            description="File encoding to use.",
            type="select",
            default="utf-8",
            options=["utf-8", "ascii", "latin-1", "utf-16"],
        ),
    ],
)
def csv_write(
    path: str,
    rows: List[Dict[str, Any]],
    headers: Optional[List[str]] = None,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> dict:
    """Write rows (list of dicts) to a CSV file."""
    path = check_write_path(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if headers is None:
        headers = list(rows[0].keys()) if rows else []
    with open(path, "w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)
    return {"path": path, "row_count": len(rows)}


@skill(
    name="csv_query",
    description="Filter CSV rows where a column equals a given value.",
    category="data",
    tags=["csv", "query", "filter", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="Query CSV",
    icon="table",
    risk_level=RiskLevel.SAFE,
    group="CSV Operations",
    config_params=[
        ConfigParam(
            name="delimiter",
            display_name="Delimiter",
            description="Column delimiter character.",
            type="string",
            default=",",
        ),
    ],
)
def csv_query(path: str, column: str, value: str, delimiter: str = ",") -> dict:
    """Return rows where *column* equals *value*."""
    path = check_read_path(path)
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        matches = [row for row in reader if row.get(column) == value]
    return {"matches": matches, "count": len(matches)}


@skill(
    name="csv_headers",
    description="Get the column names of a CSV file.",
    category="data",
    tags=["csv", "headers", "schema", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="CSV Headers",
    icon="table",
    risk_level=RiskLevel.SAFE,
    group="CSV Operations",
)
def csv_headers(path: str, delimiter: str = ",") -> dict:
    """Return the header row of a CSV file."""
    path = check_read_path(path)
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        headers = next(reader, [])
    return {"headers": headers, "path": path}


@skill(
    name="csv_stats",
    description="Compute basic statistics on a numeric column of a CSV file.",
    category="data",
    tags=["csv", "stats", "statistics", "data"],
    idempotent=True,
    requires_filesystem=True,
    display_name="CSV Stats",
    icon="bar-chart",
    risk_level=RiskLevel.SAFE,
    group="CSV Operations",
    config_params=[
        ConfigParam(
            name="delimiter",
            display_name="Delimiter",
            description="Column delimiter character.",
            type="string",
            default=",",
        ),
    ],
)
def csv_stats(path: str, column: str, delimiter: str = ",") -> dict:
    """Return count, min, max, mean, median, and stdev for a numeric column."""
    path = check_read_path(path)
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        values = []
        for row in reader:
            raw = row.get(column)
            if raw is None:
                raise ValueError(f"Column '{column}' not found")
            try:
                values.append(float(raw))
            except ValueError:
                raise ValueError(
                    f"Non-numeric value '{raw}' in column '{column}'"
                )
    if not values:
        raise ValueError(f"No data in column '{column}'")
    result: Dict[str, Any] = {
        "column": column,
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": _stats.mean(values),
        "median": _stats.median(values),
    }
    if len(values) >= 2:
        result["stdev"] = _stats.stdev(values)
    return result


class CsvPlugin(TransformerPlugin):
    """Plugin providing CSV file operation skills (no transformers)."""

    def __init__(self):
        super().__init__("csv")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "csv_read": csv_read.__skill__,
            "csv_write": csv_write.__skill__,
            "csv_query": csv_query.__skill__,
            "csv_headers": csv_headers.__skill__,
            "csv_stats": csv_stats.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="csv",
            display_name="CSV",
            description="Read, write, query, and analyze CSV files.",
            icon="table",
            color="#10b981",
            group="Data",
            requires=PluginRequirements(filesystem=True),
        )
