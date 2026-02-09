"""Main PythonSandbox class for safe code execution.

Provides a configurable sandbox environment for executing Python code
with import restrictions, path restrictions, and resource limits.
"""

from __future__ import annotations

import builtins
import io
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tukuy.analysis import analyze_python

from .exceptions import ImportViolationError, PathViolationError, SandboxError, SandboxTimeoutError
from .resource_limits import ResourceContext, ResourceLimits
from .restrictions import ImportRestrictions, PathRestrictions, get_safe_imports


@dataclass
class SandboxResult:
    """Result of sandbox code execution.

    Attributes:
        success: Whether execution completed without errors.
        output: Captured stdout from execution.
        error: Error message if execution failed.
        exception: The exception object if one was raised.
        return_value: The return value of the executed code (if any).
        locals: Dictionary of local variables after execution.
    """

    success: bool
    output: str = ""
    error: str | None = None
    exception: BaseException | None = None
    return_value: Any = None
    locals: dict[str, Any] = field(default_factory=dict)


class RestrictedImporter:
    """Custom import handler that enforces import restrictions."""

    def __init__(self, restrictions: ImportRestrictions, original_import: Any) -> None:
        self.restrictions = restrictions
        self.original_import = original_import

    def __call__(
        self,
        name: str,
        globals: dict | None = None,
        locals: dict | None = None,
        fromlist: tuple = (),
        level: int = 0,
    ) -> Any:
        """Check import restrictions before allowing the import."""
        allowed, reason = self.restrictions.is_allowed(name)
        if not allowed:
            raise ImportViolationError(name, reason)

        # Also check fromlist items
        if fromlist:
            for item in fromlist:
                full_name = f"{name}.{item}"
                allowed, reason = self.restrictions.is_allowed(full_name)
                if not allowed:
                    raise ImportViolationError(full_name, reason)

        return self.original_import(name, globals, locals, fromlist, level)


class RestrictedOpen:
    """Custom open handler that enforces path restrictions."""

    def __init__(self, path_restrictions: PathRestrictions) -> None:
        self.path_restrictions = path_restrictions

    def __call__(
        self,
        file: str | Path,
        mode: str = "r",
        *args: Any,
        **kwargs: Any,
    ) -> io.IOBase:
        """Check path restrictions before opening a file."""
        is_write = any(c in mode for c in "wax+")

        if is_write:
            if not self.path_restrictions.can_write(file):
                raise PathViolationError(str(file), "write")
        else:
            if not self.path_restrictions.can_read(file):
                raise PathViolationError(str(file), "read")

        return builtins.open(file, mode, *args, **kwargs)


class PythonSandbox:
    """Sandbox for safe Python code execution.

    Provides a restricted execution environment with:
    - Import whitelist/blacklist with always-blocked security list
    - Filesystem path restrictions
    - Timeout handling
    - Optional memory limits (Unix only)
    - Captured stdout/stderr

    Example::

        from tukuy.sandbox import PythonSandbox

        sandbox = PythonSandbox(
            allowed_imports=["json", "math"],
            timeout_seconds=5,
        )

        result = sandbox.execute('''
            import json
            data = {"x": 1, "y": 2}
            print(json.dumps(data))
        ''')

        if result.success:
            print(result.output)  # '{"x": 1, "y": 2}'
        else:
            print(f"Error: {result.error}")

    Args:
        allowed_imports: List of module names to allow (whitelist mode).
            If empty, uses blocked_imports as a blacklist.
        blocked_imports: List of module names to block (blacklist mode).
            Only used if allowed_imports is empty.
        timeout_seconds: Maximum execution time in seconds.
        max_memory_bytes: Maximum memory usage (Unix only).
        allowed_read_paths: List of directory paths allowed for reading.
        allowed_write_paths: List of directory paths allowed for writing.
        allow_cwd: Whether to allow file access in the current working directory.
        working_directory: Optional working directory for the sandbox.
        use_safe_imports: If True and allowed_imports is empty, use the
            predefined SAFE_IMPORTS set as the allowed list.
        validate_before_exec: If True, run code analysis before execution.
    """

    def __init__(
        self,
        allowed_imports: list[str] | None = None,
        blocked_imports: list[str] | None = None,
        timeout_seconds: float = 30.0,
        max_memory_bytes: int | None = None,
        allowed_read_paths: list[str | Path] | None = None,
        allowed_write_paths: list[str | Path] | None = None,
        allow_cwd: bool = False,
        working_directory: str | Path | None = None,
        use_safe_imports: bool = True,
        validate_before_exec: bool = True,
    ) -> None:
        # Set up import restrictions
        if allowed_imports is not None:
            allowed_set = set(allowed_imports)
        elif use_safe_imports:
            allowed_set = get_safe_imports()
        else:
            allowed_set = set()

        blocked_set = set(blocked_imports) if blocked_imports else set()

        self.import_restrictions = ImportRestrictions(
            allowed=allowed_set,
            blocked=blocked_set,
        )

        # Set up path restrictions
        read_paths = {Path(p) for p in (allowed_read_paths or [])}
        write_paths = {Path(p) for p in (allowed_write_paths or [])}
        work_dir = Path(working_directory) if working_directory else None

        self.path_restrictions = PathRestrictions(
            allowed_read=read_paths,
            allowed_write=write_paths,
            allow_cwd=allow_cwd,
            working_directory=work_dir,
        )

        # Set up resource limits
        self.resource_limits = ResourceLimits(
            timeout_seconds=timeout_seconds,
            max_memory_bytes=max_memory_bytes,
        )

        self.validate_before_exec = validate_before_exec

    def execute(self, code: str, globals_dict: dict[str, Any] | None = None) -> SandboxResult:
        """Execute Python code in the sandbox.

        Args:
            code: Python source code to execute.
            globals_dict: Optional dictionary of global variables to make
                available during execution. Defaults to a minimal safe set.

        Returns:
            SandboxResult with execution outcome.
        """
        # Validate code first if enabled
        if self.validate_before_exec:
            analysis = analyze_python(code)
            if not analysis.syntax_valid:
                return SandboxResult(
                    success=False,
                    error=f"Syntax error: {analysis.syntax_error}",
                )

        # Set up restricted builtins
        safe_builtins = self._get_safe_builtins()

        # Set up globals
        exec_globals: dict[str, Any] = {"__builtins__": safe_builtins}
        if globals_dict:
            exec_globals.update(globals_dict)

        exec_locals: dict[str, Any] = {}

        # Capture stdout
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()

        try:
            sys.stdout = captured_stdout
            sys.stderr = captured_stderr

            # Execute with resource limits
            with ResourceContext(self.resource_limits):
                exec(compile(code, "<sandbox>", "exec"), exec_globals, exec_locals)

            # Success
            output = captured_stdout.getvalue()
            if len(output) > self.resource_limits.max_output_bytes:
                output = output[: self.resource_limits.max_output_bytes] + "\n... [output truncated]"

            return SandboxResult(
                success=True,
                output=output,
                locals={k: v for k, v in exec_locals.items() if not k.startswith("_")},
            )

        except ImportViolationError as e:
            return SandboxResult(
                success=False,
                output=captured_stdout.getvalue(),
                error=str(e),
                exception=e,
            )

        except PathViolationError as e:
            return SandboxResult(
                success=False,
                output=captured_stdout.getvalue(),
                error=str(e),
                exception=e,
            )

        except SandboxTimeoutError as e:
            return SandboxResult(
                success=False,
                output=captured_stdout.getvalue(),
                error=str(e),
                exception=e,
            )

        except SandboxError as e:
            return SandboxResult(
                success=False,
                output=captured_stdout.getvalue(),
                error=str(e),
                exception=e,
            )

        except Exception as e:
            return SandboxResult(
                success=False,
                output=captured_stdout.getvalue(),
                error=f"{type(e).__name__}: {e}",
                exception=e,
            )

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _get_safe_builtins(self) -> dict[str, Any]:
        """Return a dictionary of safe builtins for the sandbox."""
        # Start with a minimal set of safe builtins
        safe = {
            # Types
            "bool": bool,
            "int": int,
            "float": float,
            "str": str,
            "bytes": bytes,
            "bytearray": bytearray,
            "list": list,
            "tuple": tuple,
            "dict": dict,
            "set": set,
            "frozenset": frozenset,
            "type": type,
            "object": object,
            # Functions
            "abs": abs,
            "all": all,
            "any": any,
            "bin": bin,
            "chr": chr,
            "divmod": divmod,
            "enumerate": enumerate,
            "filter": filter,
            "format": format,
            "hash": hash,
            "hex": hex,
            "id": id,
            "isinstance": isinstance,
            "issubclass": issubclass,
            "iter": iter,
            "len": len,
            "map": map,
            "max": max,
            "min": min,
            "next": next,
            "oct": oct,
            "ord": ord,
            "pow": pow,
            "print": print,
            "range": range,
            "repr": repr,
            "reversed": reversed,
            "round": round,
            "slice": slice,
            "sorted": sorted,
            "sum": sum,
            "zip": zip,
            # Constants
            "True": True,
            "False": False,
            "None": None,
            # Exceptions (subset)
            "Exception": Exception,
            "BaseException": BaseException,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "AttributeError": AttributeError,
            "RuntimeError": RuntimeError,
            "StopIteration": StopIteration,
            "ZeroDivisionError": ZeroDivisionError,
            "AssertionError": AssertionError,
            "NotImplementedError": NotImplementedError,
        }

        # Add restricted import
        safe["__import__"] = RestrictedImporter(self.import_restrictions, builtins.__import__)

        # Add restricted open if path restrictions are configured
        if (
            self.path_restrictions.allowed_read
            or self.path_restrictions.allowed_write
            or self.path_restrictions.allow_cwd
        ):
            safe["open"] = RestrictedOpen(self.path_restrictions)

        return safe

    def read_file(self, path: str | Path) -> str:
        """Convenience method to read a file through the sandbox.

        Args:
            path: Path to the file to read.

        Returns:
            File contents as a string.

        Raises:
            PathViolationError: If the path is not allowed for reading.
            FileNotFoundError: If the file does not exist.
        """
        if not self.path_restrictions.can_read(path):
            raise PathViolationError(str(path), "read")
        return Path(path).read_text()

    def write_file(self, path: str | Path, content: str) -> None:
        """Convenience method to write a file through the sandbox.

        Args:
            path: Path to the file to write.
            content: Content to write to the file.

        Raises:
            PathViolationError: If the path is not allowed for writing.
        """
        if not self.path_restrictions.can_write(path):
            raise PathViolationError(str(path), "write")
        Path(path).write_text(content)

    def to_security_context(self) -> Any:
        """Convert this sandbox's path restrictions to a tukuy ``SecurityContext``.

        Returns:
            A tukuy ``SecurityContext`` with read/write paths and working
            directory derived from :attr:`path_restrictions`.
        """
        from tukuy.safety import SecurityContext

        return SecurityContext(
            allowed_read_paths=[str(p) for p in self.path_restrictions.allowed_read],
            allowed_write_paths=[str(p) for p in self.path_restrictions.allowed_write],
            working_directory=str(self.path_restrictions.working_directory)
            if self.path_restrictions.working_directory
            else None,
        )
