"""Tests for the sandbox module."""

import platform
import tempfile
from pathlib import Path

import pytest

from tukuy.sandbox import (
    ALWAYS_BLOCKED_IMPORTS,
    ImportRestrictions,
    ImportViolationError,
    PathRestrictions,
    PathViolationError,
    PythonSandbox,
    ResourceLimits,
    SandboxError,
    SandboxResult,
    SandboxTimeoutError,
)
from tukuy.sandbox.restrictions import get_safe_imports


class TestImportRestrictions:
    """Tests for ImportRestrictions."""

    def test_always_blocked(self):
        """Test that always-blocked imports are rejected."""
        restrictions = ImportRestrictions()
        for module in ["ctypes", "subprocess", "os", "sys"]:
            allowed, reason = restrictions.is_allowed(module)
            assert allowed is False
            assert "always-blocked" in reason.lower()

    def test_whitelist_mode(self):
        """Test whitelist mode allows only specified modules."""
        restrictions = ImportRestrictions(allowed={"json", "math"})

        assert restrictions.is_allowed("json")[0] is True
        assert restrictions.is_allowed("math")[0] is True
        assert restrictions.is_allowed("re")[0] is False

    def test_blacklist_mode(self):
        """Test blacklist mode blocks specified modules."""
        restrictions = ImportRestrictions(blocked={"requests", "httpx"})

        assert restrictions.is_allowed("json")[0] is True
        assert restrictions.is_allowed("requests")[0] is False
        assert restrictions.is_allowed("httpx")[0] is False

    def test_block_all(self):
        """Test block_all mode."""
        restrictions = ImportRestrictions(block_all=True)

        assert restrictions.is_allowed("json")[0] is False
        assert restrictions.is_allowed("math")[0] is False

    def test_submodule_blocking(self):
        """Test that submodules of blocked modules are also blocked."""
        restrictions = ImportRestrictions()

        # os.path should be blocked because os is always blocked
        allowed, _ = restrictions.is_allowed("os.path")
        assert allowed is False


class TestPathRestrictions:
    """Tests for PathRestrictions."""

    def test_no_restrictions(self):
        """Test that with no restrictions, nothing is allowed."""
        restrictions = PathRestrictions()

        assert restrictions.can_read("/tmp/test.txt") is False
        assert restrictions.can_write("/tmp/test.txt") is False

    def test_allowed_read_paths(self):
        """Test allowed read paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            restrictions = PathRestrictions(
                allowed_read={Path(tmpdir)}
            )

            assert restrictions.can_read(f"{tmpdir}/test.txt") is True
            assert restrictions.can_read("/other/path.txt") is False

    def test_allowed_write_paths(self):
        """Test allowed write paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            restrictions = PathRestrictions(
                allowed_write={Path(tmpdir)}
            )

            assert restrictions.can_write(f"{tmpdir}/test.txt") is True
            assert restrictions.can_write("/other/path.txt") is False

    def test_allow_cwd(self):
        """Test allow_cwd flag."""
        restrictions = PathRestrictions(allow_cwd=True)

        cwd = Path.cwd()
        assert restrictions.can_read(cwd / "test.txt") is True
        assert restrictions.can_write(cwd / "test.txt") is True


class TestResourceLimits:
    """Tests for ResourceLimits."""

    def test_default_values(self):
        """Test default resource limit values."""
        limits = ResourceLimits()

        assert limits.timeout_seconds == 30.0
        assert limits.max_memory_bytes is None
        assert limits.max_output_bytes == 1024 * 1024

    def test_custom_values(self):
        """Test custom resource limit values."""
        limits = ResourceLimits(
            timeout_seconds=10.0,
            max_memory_bytes=100 * 1024 * 1024,
            max_output_bytes=1024,
        )

        assert limits.timeout_seconds == 10.0
        assert limits.max_memory_bytes == 100 * 1024 * 1024
        assert limits.max_output_bytes == 1024


class TestPythonSandbox:
    """Tests for PythonSandbox."""

    def test_simple_execution(self):
        """Test simple code execution."""
        sandbox = PythonSandbox(allowed_imports=["json"])
        result = sandbox.execute("x = 1 + 2\nprint(x)")

        assert result.success is True
        assert "3" in result.output
        assert result.error is None

    def test_capture_locals(self):
        """Test that local variables are captured."""
        sandbox = PythonSandbox(allowed_imports=[])
        result = sandbox.execute("x = 42\ny = 'hello'")

        assert result.success is True
        assert result.locals.get("x") == 42
        assert result.locals.get("y") == "hello"

    def test_blocked_import(self):
        """Test that blocked imports fail."""
        sandbox = PythonSandbox(allowed_imports=["json"])
        result = sandbox.execute("import os")

        assert result.success is False
        assert isinstance(result.exception, ImportViolationError)

    def test_allowed_import(self):
        """Test that allowed imports work."""
        sandbox = PythonSandbox(allowed_imports=["json"])
        result = sandbox.execute("""
import json
data = json.dumps({"key": "value"})
print(data)
""")

        assert result.success is True
        assert '"key"' in result.output

    def test_syntax_error(self):
        """Test that syntax errors are caught."""
        sandbox = PythonSandbox()
        result = sandbox.execute("def foo(")

        assert result.success is False
        assert "syntax" in result.error.lower() or "Syntax" in result.error

    def test_runtime_error(self):
        """Test that runtime errors are caught."""
        sandbox = PythonSandbox()
        result = sandbox.execute("x = 1 / 0")

        assert result.success is False
        assert "ZeroDivisionError" in result.error

    def test_use_safe_imports(self):
        """Test use_safe_imports flag."""
        sandbox = PythonSandbox(use_safe_imports=True)
        result = sandbox.execute("""
import json
import math
import re
print(json.dumps({"pi": math.pi}))
""")

        assert result.success is True

    def test_globals_dict(self):
        """Test passing globals to execution."""
        sandbox = PythonSandbox()
        result = sandbox.execute(
            "result = multiply(x, y)",
            globals_dict={
                "x": 3,
                "y": 4,
                "multiply": lambda a, b: a * b,
            }
        )

        assert result.success is True
        assert result.locals.get("result") == 12

    def test_output_truncation(self):
        """Test that long output is truncated."""
        sandbox = PythonSandbox()
        sandbox.resource_limits.max_output_bytes = 100

        result = sandbox.execute("print('x' * 1000)")

        assert result.success is True
        assert len(result.output) <= 150  # Allow some overhead for truncation message
        assert "truncated" in result.output.lower()

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Timeout via signals not available on Windows"
    )
    def test_timeout(self):
        """Test execution timeout."""
        sandbox = PythonSandbox(timeout_seconds=0.5)
        result = sandbox.execute("""
import time
time.sleep(10)
""")

        assert result.success is False
        assert isinstance(result.exception, SandboxTimeoutError)


class TestSandboxResult:
    """Tests for SandboxResult."""

    def test_success_result(self):
        """Test successful result."""
        result = SandboxResult(
            success=True,
            output="hello",
            locals={"x": 1},
        )

        assert result.success is True
        assert result.output == "hello"
        assert result.error is None
        assert result.exception is None

    def test_error_result(self):
        """Test error result."""
        exc = ValueError("test error")
        result = SandboxResult(
            success=False,
            error="ValueError: test error",
            exception=exc,
        )

        assert result.success is False
        assert result.error == "ValueError: test error"
        assert result.exception is exc


class TestSafeImports:
    """Tests for safe imports list."""

    def test_get_safe_imports(self):
        """Test get_safe_imports returns a set."""
        imports = get_safe_imports()

        assert isinstance(imports, set)
        assert "json" in imports
        assert "math" in imports
        assert "re" in imports

    def test_safe_imports_immutable(self):
        """Test that modifying returned set doesn't affect original."""
        imports1 = get_safe_imports()
        imports1.add("dangerous_module")

        imports2 = get_safe_imports()
        assert "dangerous_module" not in imports2


class TestAlwaysBlockedImports:
    """Tests for the always-blocked imports list."""

    def test_critical_modules_blocked(self):
        """Test that critical modules are in the blocked list."""
        assert "ctypes" in ALWAYS_BLOCKED_IMPORTS
        assert "subprocess" in ALWAYS_BLOCKED_IMPORTS
        assert "os" in ALWAYS_BLOCKED_IMPORTS
        assert "sys" in ALWAYS_BLOCKED_IMPORTS
        assert "pickle" in ALWAYS_BLOCKED_IMPORTS
        assert "importlib" in ALWAYS_BLOCKED_IMPORTS

    def test_is_frozenset(self):
        """Test that ALWAYS_BLOCKED_IMPORTS is immutable."""
        assert isinstance(ALWAYS_BLOCKED_IMPORTS, frozenset)


class TestSandboxFileOperations:
    """Tests for sandbox file operations."""

    def test_read_file_allowed(self):
        """Test reading from allowed path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("hello world")

            sandbox = PythonSandbox(
                allowed_read_paths=[tmpdir],
            )

            content = sandbox.read_file(test_file)
            assert content == "hello world"

    def test_read_file_denied(self):
        """Test reading from disallowed path."""
        sandbox = PythonSandbox()

        with pytest.raises(PathViolationError):
            sandbox.read_file("/etc/passwd")

    def test_write_file_allowed(self):
        """Test writing to allowed path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "output.txt"

            sandbox = PythonSandbox(
                allowed_write_paths=[tmpdir],
            )

            sandbox.write_file(test_file, "test content")
            assert test_file.read_text() == "test content"

    def test_write_file_denied(self):
        """Test writing to disallowed path."""
        sandbox = PythonSandbox()

        with pytest.raises(PathViolationError):
            sandbox.write_file("/tmp/dangerous.txt", "content")
