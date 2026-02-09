"""Sandbox exceptions.

Custom exceptions for sandbox violations and errors.
"""

from __future__ import annotations


class SandboxError(Exception):
    """Base exception for all sandbox-related errors."""

    pass


class ImportViolationError(SandboxError):
    """Raised when code attempts to import a blocked module."""

    def __init__(self, module_name: str, reason: str | None = None) -> None:
        self.module_name = module_name
        self.reason = reason
        message = f"Import of '{module_name}' is not allowed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class PathViolationError(SandboxError):
    """Raised when code attempts to access a restricted path."""

    def __init__(self, path: str, operation: str = "access") -> None:
        self.path = path
        self.operation = operation
        super().__init__(f"Cannot {operation} path '{path}': outside allowed directories")


class SandboxTimeoutError(SandboxError):
    """Raised when code execution exceeds the timeout limit."""

    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Execution exceeded timeout of {timeout_seconds} seconds")


class ResourceLimitError(SandboxError):
    """Raised when code exceeds resource limits (memory, etc.)."""

    def __init__(self, resource: str, limit: int | float, used: int | float | None = None) -> None:
        self.resource = resource
        self.limit = limit
        self.used = used
        message = f"Resource limit exceeded for {resource}: limit={limit}"
        if used is not None:
            message += f", used={used}"
        super().__init__(message)
