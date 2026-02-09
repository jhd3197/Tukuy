"""Resource limits for sandbox execution.

Provides timeout and memory limit handling.
"""

from __future__ import annotations

import platform
import signal
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from .exceptions import SandboxTimeoutError


@dataclass
class ResourceLimits:
    """Configuration for resource limits in the sandbox.

    Attributes:
        timeout_seconds: Maximum execution time in seconds.
        max_memory_bytes: Maximum memory usage in bytes (Unix only via resource module).
            Note: Memory limits are only enforced on Unix systems.
        max_output_bytes: Maximum output size in bytes.
    """

    timeout_seconds: float = 30.0
    max_memory_bytes: int | None = None
    max_output_bytes: int = 1024 * 1024  # 1 MB default


class TimeoutHandler:
    """Context manager for handling execution timeouts.

    Uses signal.SIGALRM on Unix systems, threading-based approach on Windows.
    """

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        self._old_handler: Any = None
        self._is_unix = platform.system() != "Windows"

    def _timeout_handler(self, signum: int, frame: Any) -> None:
        """Signal handler for timeout."""
        raise SandboxTimeoutError(self.seconds)

    def __enter__(self) -> TimeoutHandler:
        if self._is_unix and self.seconds > 0:
            self._old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._is_unix and self.seconds > 0:
            signal.setitimer(signal.ITIMER_REAL, 0)
            if self._old_handler is not None:
                signal.signal(signal.SIGALRM, self._old_handler)


class ResourceContext:
    """Context manager for resource limits.

    Applies timeout and optionally memory limits during code execution.

    Note:
        Memory limits via the resource module are only available on Unix.
        On Windows, only timeout limits are enforced (and with limitations).
    """

    def __init__(self, limits: ResourceLimits) -> None:
        self.limits = limits
        self._timeout_handler: TimeoutHandler | None = None
        self._old_memory_limit: tuple[int, int] | None = None
        self._is_unix = platform.system() != "Windows"

    def __enter__(self) -> ResourceContext:
        # Set up timeout
        if self.limits.timeout_seconds > 0:
            self._timeout_handler = TimeoutHandler(self.limits.timeout_seconds)
            self._timeout_handler.__enter__()

        # Set up memory limit (Unix only)
        if self._is_unix and self.limits.max_memory_bytes is not None:
            try:
                import resource as res

                self._old_memory_limit = res.getrlimit(res.RLIMIT_AS)
                res.setrlimit(res.RLIMIT_AS, (self.limits.max_memory_bytes, self.limits.max_memory_bytes))
            except (ImportError, ValueError, OSError):
                # resource module not available or limit can't be set
                self._old_memory_limit = None

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Clean up timeout
        if self._timeout_handler is not None:
            self._timeout_handler.__exit__(exc_type, exc_val, exc_tb)

        # Clean up memory limit
        if self._is_unix and self._old_memory_limit is not None:
            try:
                import resource as res

                res.setrlimit(res.RLIMIT_AS, self._old_memory_limit)
            except (ImportError, ValueError, OSError):
                pass


@contextmanager
def enforce_limits(limits: ResourceLimits) -> Generator[None, None, None]:
    """Context manager to enforce resource limits.

    Args:
        limits: ResourceLimits configuration.

    Yields:
        None - use this as a context manager around code execution.

    Raises:
        SandboxTimeoutError: If execution exceeds timeout.
        ResourceLimitError: If memory limit is exceeded (Unix only).
    """
    ctx = ResourceContext(limits)
    with ctx:
        yield
