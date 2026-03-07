"""AST fingerprinting plugin — hash Python function signatures, bodies, and classes.

Provides SHA-256 based fingerprinting of Python AST nodes for change detection.
Used by CacaoDocs (documentation change tracking) and Sondeo (performance
regression attribution).

Standalone usage::

    from tukuy.plugins.ast_fingerprint import (
        hash_signature,
        hash_body,
        hash_body_per_statement,
        hash_class_signature,
        hash_call_graph,
        compute_complexity,
        normalize_ast,
        hash_function,
    )

    import ast
    tree = ast.parse(open("mymodule.py").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            print(hash_signature(node))
            print(hash_body(node))
            print(compute_complexity(node))

Transformer usage (via Tukuy pipeline)::

    tukuy("def foo(x): return x + 1 | ast_signature_hash")
    tukuy("def foo(x): return x + 1 | ast_body_hash")
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import textwrap
from typing import Any, Dict, Optional

from ...base import ChainableTransformer
from ...types import TransformContext
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Core utilities
# ---------------------------------------------------------------------------


def normalize_ast(node: ast.AST) -> str:
    """Produce a normalized AST string that ignores cosmetic differences.

    Uses ``ast.unparse`` (Python 3.9+) for a canonical text form, falling
    back to ``ast.dump`` on older interpreters.
    """
    if hasattr(ast, "unparse"):
        return ast.unparse(node)
    return ast.dump(node)


# ---------------------------------------------------------------------------
# Function hashing
# ---------------------------------------------------------------------------


def hash_signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    length: int | None = None,
) -> str:
    """SHA-256 of function name + args + return type + decorators.

    Args:
        node: A ``FunctionDef`` or ``AsyncFunctionDef`` AST node.
        length: If given, truncate the hex digest to this many characters.
                ``None`` returns the full 64-char digest.
    """
    parts: list[str] = [node.name]
    parts.append(normalize_ast(node.args))
    if node.returns:
        parts.append(normalize_ast(node.returns))
    for d in node.decorator_list:
        parts.append(normalize_ast(d))
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


def hash_body(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    length: int | None = None,
) -> str:
    """SHA-256 of function body AST, excluding the docstring.

    Args:
        node: A ``FunctionDef`` or ``AsyncFunctionDef`` AST node.
        length: If given, truncate the hex digest to this many characters.
    """
    body = list(node.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    parts = [normalize_ast(stmt) for stmt in body]
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


def hash_body_per_statement(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    length: int | None = 16,
) -> list[str]:
    """Hash each statement in the body individually.

    Returns a list of SHA-256 hashes, one per statement (docstring excluded).
    This enables pinpointing *which lines* changed.

    Args:
        node: A ``FunctionDef`` or ``AsyncFunctionDef`` AST node.
        length: Truncation length per hash (default 16).
    """
    body = list(node.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    results = []
    for stmt in body:
        digest = hashlib.sha256(normalize_ast(stmt).encode("utf-8")).hexdigest()
        results.append(digest[:length] if length else digest)
    return results


# ---------------------------------------------------------------------------
# Class hashing
# ---------------------------------------------------------------------------


def hash_class_signature(
    node: ast.ClassDef,
    *,
    length: int | None = None,
) -> str:
    """SHA-256 of class name + bases + decorators.

    Args:
        node: A ``ClassDef`` AST node.
        length: If given, truncate the hex digest to this many characters.
    """
    parts: list[str] = [node.name]
    for base in node.bases:
        parts.append(normalize_ast(base))
    for d in node.decorator_list:
        parts.append(normalize_ast(d))
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


# ---------------------------------------------------------------------------
# Call graph hashing
# ---------------------------------------------------------------------------


def _call_name(node: ast.expr) -> str:
    """Extract the dotted name from a Call node's func attribute."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def hash_call_graph(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    length: int | None = None,
) -> str:
    """SHA-256 of the sorted set of functions this function calls.

    Useful for detecting transitive dependency changes.

    Args:
        node: A ``FunctionDef`` or ``AsyncFunctionDef`` AST node.
        length: If given, truncate the hex digest to this many characters.
    """
    calls: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            name = _call_name(child.func)
            if name and name not in calls:
                calls.append(name)
    calls.sort()
    digest = hashlib.sha256("|".join(calls).encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


# ---------------------------------------------------------------------------
# Complexity metrics
# ---------------------------------------------------------------------------


def compute_complexity(node: ast.AST) -> int:
    """Compute cyclomatic complexity by counting decision points.

    Counts: if, for, while, try/except, BoolOp (and/or), comprehensions,
    assert, with, IfExp (ternary).
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.IfExp)):
            complexity += 1
        elif isinstance(child, (ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.While):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.With):
            complexity += 1
        elif isinstance(child, ast.Assert):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(
            child, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)
        ):
            complexity += sum(1 for _ in child.generators)
    return complexity


# ---------------------------------------------------------------------------
# High-level: hash a live function object
# ---------------------------------------------------------------------------


def hash_function(func: Any) -> dict[str, str | None]:
    """Compute signature and body hashes for a live function object.

    Uses ``inspect.getsource()`` to retrieve the source, then parses it
    with AST to compute hashes.

    Returns:
        Dict with ``signature_hash``, ``body_hash``, and ``complexity``.
        Values are ``None`` if the source cannot be retrieved.
    """
    try:
        source = inspect.getsource(func)
    except (OSError, TypeError):
        return {"signature_hash": None, "body_hash": None, "complexity": None}

    source = textwrap.dedent(source)

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"signature_hash": None, "body_hash": None, "complexity": None}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return {
                "signature_hash": hash_signature(node),
                "body_hash": hash_body(node),
                "complexity": compute_complexity(node),
            }

    return {"signature_hash": None, "body_hash": None, "complexity": None}


# ---------------------------------------------------------------------------
# Tukuy transformer wrappers
# ---------------------------------------------------------------------------


class AstSignatureHashTransformer(ChainableTransformer[str, str]):
    """Hash the signature of the first function found in source code."""

    def __init__(self, name: str, length: int = 0):
        super().__init__(name)
        self.length = length or None

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        tree = ast.parse(value)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return hash_signature(node, length=self.length)
        return ""


class AstBodyHashTransformer(ChainableTransformer[str, str]):
    """Hash the body of the first function found in source code."""

    def __init__(self, name: str, length: int = 0):
        super().__init__(name)
        self.length = length or None

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        tree = ast.parse(value)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return hash_body(node, length=self.length)
        return ""


class AstComplexityTransformer(ChainableTransformer[str, str]):
    """Compute cyclomatic complexity of the first function in source code."""

    def validate(self, value: str) -> bool:
        return isinstance(value, str)

    def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
        tree = ast.parse(value)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return str(compute_complexity(node))
        return "0"


class AstFingerprintPlugin(TransformerPlugin):
    """Plugin providing AST-based code fingerprinting transformers."""

    def __init__(self):
        super().__init__("ast_fingerprint")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {
            "ast_signature_hash": lambda params: AstSignatureHashTransformer(
                "ast_signature_hash",
                length=params.get("length", 0),
            ),
            "ast_body_hash": lambda params: AstBodyHashTransformer(
                "ast_body_hash",
                length=params.get("length", 0),
            ),
            "ast_complexity": lambda _: AstComplexityTransformer("ast_complexity"),
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest

        return PluginManifest(
            name="ast_fingerprint",
            display_name="AST Fingerprint",
            description="SHA-256 fingerprinting of Python function signatures, bodies, and classes.",
            icon="fingerprint",
            group="Code",
        )
