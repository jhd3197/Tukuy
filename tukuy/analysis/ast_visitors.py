"""AST visitors for extracting code features.

Provides an AST node visitor that extracts security-relevant features
from Python source code.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class CodeFeatures:
    """Features extracted from Python code via AST analysis.

    Attributes:
        imports: Set of module names imported (import x, from x import y).
        file_operations: List of (operation, args) tuples for file access.
        network_calls: List of network-related function calls detected.
        system_calls: List of system/subprocess calls detected.
        exec_eval_usage: List of exec/eval/compile calls detected.
        dangerous_builtins: Set of dangerous builtin names used.
        attribute_accesses: Set of attribute access patterns (e.g., "os.system").
        function_calls: Set of all function call names.
        has_global_statements: Whether the code uses global statements.
        has_nonlocal_statements: Whether the code uses nonlocal statements.
        class_definitions: Set of class names defined.
        async_operations: Whether the code contains async/await.
    """

    imports: set[str] = field(default_factory=set)
    file_operations: list[tuple[str, list[str]]] = field(default_factory=list)
    network_calls: list[tuple[str, list[str]]] = field(default_factory=list)
    system_calls: list[tuple[str, list[str]]] = field(default_factory=list)
    exec_eval_usage: list[tuple[str, list[str]]] = field(default_factory=list)
    dangerous_builtins: set[str] = field(default_factory=set)
    attribute_accesses: set[str] = field(default_factory=set)
    function_calls: set[str] = field(default_factory=set)
    has_global_statements: bool = False
    has_nonlocal_statements: bool = False
    class_definitions: set[str] = field(default_factory=set)
    async_operations: bool = False


# Builtins that can be dangerous when executed dynamically
DANGEROUS_BUILTINS = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",
        "input",
        "breakpoint",
        "memoryview",
        "vars",
        "dir",
        "globals",
        "locals",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
    }
)

# File operation function names
FILE_OPERATIONS = frozenset(
    {
        "open",
        "read",
        "write",
        "close",
        "seek",
        "tell",
        "readline",
        "readlines",
        "writelines",
        "flush",
        "truncate",
    }
)

# Network-related module prefixes and function names
NETWORK_MODULES = frozenset(
    {
        "socket",
        "urllib",
        "http",
        "requests",
        "httpx",
        "aiohttp",
        "ftplib",
        "smtplib",
        "poplib",
        "imaplib",
        "telnetlib",
        "ssl",
        "websocket",
        "websockets",
    }
)

# System call patterns
SYSTEM_CALL_PATTERNS = frozenset(
    {
        "os.system",
        "os.popen",
        "os.spawn",
        "os.spawnl",
        "os.spawnle",
        "os.spawnlp",
        "os.spawnlpe",
        "os.spawnv",
        "os.spawnve",
        "os.spawnvp",
        "os.spawnvpe",
        "os.exec",
        "os.execl",
        "os.execle",
        "os.execlp",
        "os.execlpe",
        "os.execv",
        "os.execve",
        "os.execvp",
        "os.execvpe",
        "os.fork",
        "os.forkpty",
        "os.kill",
        "os.killpg",
        "subprocess.run",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.Popen",
        "subprocess.getoutput",
        "subprocess.getstatusoutput",
        "pty.spawn",
        "pty.fork",
    }
)


class FeatureExtractor(ast.NodeVisitor):
    """AST visitor that extracts security-relevant features from Python code.

    Usage::

        extractor = FeatureExtractor()
        extractor.visit(ast.parse(source_code))
        features = extractor.features
    """

    def __init__(self) -> None:
        self.features = CodeFeatures()
        self._current_module_context: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Handle import statements."""
        for alias in node.names:
            self.features.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Handle from ... import statements."""
        if node.module:
            self.features.imports.add(node.module.split(".")[0])
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Handle function calls."""
        call_name = self._get_call_name(node)
        if call_name:
            self.features.function_calls.add(call_name)
            self._classify_call(call_name, node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Handle attribute access."""
        attr_chain = self._get_attribute_chain(node)
        if attr_chain:
            self.features.attribute_accesses.add(attr_chain)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Handle name references (potential builtin usage)."""
        if node.id in DANGEROUS_BUILTINS:
            self.features.dangerous_builtins.add(node.id)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        """Handle global statements."""
        self.features.has_global_statements = True
        self.generic_visit(node)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        """Handle nonlocal statements."""
        self.features.has_nonlocal_statements = True
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Handle class definitions."""
        self.features.class_definitions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Handle async function definitions."""
        self.features.async_operations = True
        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        """Handle await expressions."""
        self.features.async_operations = True
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        """Handle async for loops."""
        self.features.async_operations = True
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        """Handle async with statements."""
        self.features.async_operations = True
        self.generic_visit(node)

    def _get_call_name(self, node: ast.Call) -> str | None:
        """Extract the full call name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return self._get_attribute_chain(node.func)
        return None

    def _get_attribute_chain(self, node: ast.Attribute) -> str | None:
        """Build the full attribute chain (e.g., 'os.path.join')."""
        parts: list[str] = [node.attr]
        current = node.value
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))
        return None

    def _get_call_args_as_strings(self, node: ast.Call) -> list[str]:
        """Extract string representations of call arguments."""
        args: list[str] = []
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                args.append(arg.value)
            else:
                args.append(ast.dump(arg))
        return args

    def _classify_call(self, call_name: str, node: ast.Call) -> None:
        """Classify a function call into categories."""
        args = self._get_call_args_as_strings(node)

        # Check for exec/eval
        if call_name in ("exec", "eval", "compile"):
            self.features.exec_eval_usage.append((call_name, args))

        # Check for file operations
        if (
            call_name == "open"
            or call_name.endswith(".open")
            or any(call_name.endswith(f".{op}") for op in FILE_OPERATIONS)
        ):
            self.features.file_operations.append((call_name, args))

        # Check for system calls
        if call_name in SYSTEM_CALL_PATTERNS or any(
            call_name.startswith(pattern.rsplit(".", 1)[0])
            for pattern in SYSTEM_CALL_PATTERNS
            if call_name.endswith(pattern.rsplit(".", 1)[-1])
        ):
            self.features.system_calls.append((call_name, args))

        # Check for network calls
        module_prefix = call_name.split(".")[0] if "." in call_name else ""
        if module_prefix in NETWORK_MODULES:
            self.features.network_calls.append((call_name, args))


def extract_features(source: str) -> CodeFeatures:
    """Extract security-relevant features from Python source code.

    Args:
        source: Python source code as a string.

    Returns:
        CodeFeatures dataclass with extracted features.

    Raises:
        SyntaxError: If the source code is not valid Python.
    """
    tree = ast.parse(source)
    extractor = FeatureExtractor()
    extractor.visit(tree)
    return extractor.features
