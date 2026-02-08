"""SQL plugin.

Provides SQLite query/execute skills and a CSV-to-SQLite transformer.

Pure stdlib — no external dependencies (uses built-in ``sqlite3``).
"""

import csv
import io
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ...plugins.base import TransformerPlugin
from ...safety import check_read_path, check_write_path
from ...skill import skill


# ── Transformers ──────────────────────────────────────────────────────────

class CsvToSqliteTransformer(ChainableTransformer[dict, dict]):
    """Import CSV data into an in-memory SQLite table and return results.

    Expects input as ``{"csv": "...", "table": "data", "query": "SELECT ..."}``.
    Loads the CSV into a table, runs the query, and returns rows.
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "csv" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> dict:
        csv_data = value["csv"]
        table_name = value.get("table", "data")
        query = value.get("query", f"SELECT * FROM {table_name}")

        reader = csv.DictReader(io.StringIO(csv_data))
        fieldnames = reader.fieldnames or []
        rows = list(reader)

        if not fieldnames:
            return {"error": "No columns found in CSV", "rows": [], "columns": []}

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        try:
            # Create table
            cols_def = ", ".join(f'"{col}" TEXT' for col in fieldnames)
            conn.execute(f'CREATE TABLE "{table_name}" ({cols_def})')

            # Insert rows
            placeholders = ", ".join("?" for _ in fieldnames)
            col_names = ", ".join(f'"{col}"' for col in fieldnames)
            for row in rows:
                values = [row.get(col, "") for col in fieldnames]
                conn.execute(f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})', values)
            conn.commit()

            # Execute query
            cursor = conn.execute(query)
            result_rows = [dict(r) for r in cursor.fetchall()]
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            return {
                "rows": result_rows,
                "columns": columns,
                "row_count": len(result_rows),
                "table": table_name,
                "query": query,
            }
        finally:
            conn.close()


class QueryBuilderTransformer(ChainableTransformer[dict, str]):
    """Build a SQL query from a structured specification.

    Expects input as::

        {
            "table": "users",
            "select": ["name", "email"],    # optional, defaults to *
            "where": {"age": 30},           # optional
            "order_by": "name",             # optional
            "limit": 10,                    # optional
        }
    """

    def validate(self, value: Any) -> bool:
        return isinstance(value, dict) and "table" in value

    def _transform(self, value: Any, context: Optional[TransformContext] = None) -> str:
        table = value["table"]
        select = value.get("select", ["*"])
        where = value.get("where", {})
        order_by = value.get("order_by", "")
        limit = value.get("limit")
        group_by = value.get("group_by", "")

        cols = ", ".join(select) if isinstance(select, list) else select
        query = f"SELECT {cols} FROM {table}"

        if where:
            conditions = []
            for k, v in where.items():
                if isinstance(v, str):
                    conditions.append(f"{k} = '{v}'")
                elif v is None:
                    conditions.append(f"{k} IS NULL")
                else:
                    conditions.append(f"{k} = {v}")
            query += " WHERE " + " AND ".join(conditions)

        if group_by:
            query += f" GROUP BY {group_by}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit is not None:
            query += f" LIMIT {limit}"

        return query


# ── Skills ────────────────────────────────────────────────────────────────

@skill(
    name="sqlite_query",
    description="Execute a read-only SQL query against a SQLite database file.",
    category="sql",
    tags=["sql", "sqlite", "database"],
    idempotent=True,
    requires_filesystem=True,
)
def sqlite_query(db_path: str, query: str, params: Optional[list] = None) -> dict:
    """Execute a read-only query on a SQLite database."""
    db_path = check_read_path(db_path)
    p = Path(db_path)
    if not p.exists():
        return {"error": f"Database not found: {db_path}", "rows": [], "success": False}

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(query, params or [])
        rows = [dict(r) for r in cursor.fetchall()]
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return {
            "rows": rows,
            "columns": columns,
            "row_count": len(rows),
            "query": query,
            "success": True,
        }
    except sqlite3.Error as e:
        return {"error": str(e), "query": query, "rows": [], "success": False}
    finally:
        conn.close()


@skill(
    name="sqlite_execute",
    description="Execute a write SQL statement (INSERT/UPDATE/DELETE/CREATE) on a SQLite database.",
    category="sql",
    tags=["sql", "sqlite", "database"],
    side_effects=True,
    requires_filesystem=True,
)
def sqlite_execute(db_path: str, sql: str, params: Optional[list] = None) -> dict:
    """Execute a write SQL statement on a SQLite database."""
    db_path = check_write_path(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(sql, params or [])
        conn.commit()
        return {
            "sql": sql,
            "rows_affected": cursor.rowcount,
            "last_row_id": cursor.lastrowid,
            "success": True,
        }
    except sqlite3.Error as e:
        return {"error": str(e), "sql": sql, "success": False}
    finally:
        conn.close()


@skill(
    name="sqlite_tables",
    description="List all tables and their schemas in a SQLite database.",
    category="sql",
    tags=["sql", "sqlite", "database"],
    idempotent=True,
    requires_filesystem=True,
)
def sqlite_tables(db_path: str) -> dict:
    """List tables in a SQLite database."""
    db_path = check_read_path(db_path)
    p = Path(db_path)
    if not p.exists():
        return {"error": f"Database not found: {db_path}", "tables": [], "success": False}

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = []
        for row in cursor:
            tables.append({"name": row["name"], "sql": row["sql"]})
        return {"tables": tables, "count": len(tables), "success": True}
    except sqlite3.Error as e:
        return {"error": str(e), "tables": [], "success": False}
    finally:
        conn.close()


class SqlPlugin(TransformerPlugin):
    """Plugin providing SQLite operations and SQL query building."""

    def __init__(self):
        super().__init__("sql")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "csv_to_sqlite": lambda _: CsvToSqliteTransformer("csv_to_sqlite"),
            "query_builder": lambda _: QueryBuilderTransformer("query_builder"),
        }

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "sqlite_query": sqlite_query.__skill__,
            "sqlite_execute": sqlite_execute.__skill__,
            "sqlite_tables": sqlite_tables.__skill__,
        }
