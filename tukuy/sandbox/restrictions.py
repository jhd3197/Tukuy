"""Import and path restriction logic for the sandbox.

Defines configurable restrictions for imports and filesystem access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Always blocked imports - these are never allowed regardless of configuration
# These modules can be used to escape the sandbox or cause serious harm
ALWAYS_BLOCKED_IMPORTS = frozenset(
    {
        # Low-level system access
        "ctypes",
        "ctypes.util",
        "_ctypes",
        # Process/threading that could escape sandbox
        "multiprocessing",
        "_multiprocessing",
        "threading",
        "_thread",
        "concurrent",
        "concurrent.futures",
        # Memory/garbage collection manipulation
        "gc",
        # System internals
        "sys",
        "_sys",
        "builtins",
        "_builtins",
        # Import system manipulation
        "importlib",
        "importlib.util",
        "importlib.abc",
        "importlib.machinery",
        "importlib.resources",
        "pkgutil",
        "runpy",
        # Code introspection/manipulation
        "code",
        "codeop",
        "ast",  # Could be used to construct code
        "dis",
        "inspect",
        "traceback",
        "linecache",
        "tokenize",
        "token",
        "symbol",
        "parser",
        # Debugging
        "pdb",
        "bdb",
        "trace",
        "faulthandler",
        # Serialization that can execute code
        "pickle",
        "cPickle",
        "_pickle",
        "shelve",
        "marshal",
        "pickletools",
        # OS/subprocess access
        "os",
        "posix",
        "nt",
        "posixpath",
        "ntpath",
        "_posixsubprocess",
        "subprocess",
        "shutil",
        "pathlib",  # Can access filesystem
        "glob",
        "fnmatch",
        # Signals and process control
        "signal",
        "pty",
        "tty",
        "termios",
        # Resource control
        "resource",
        # Windows-specific
        "msilib",
        "winreg",
        "_winapi",
        "msvcrt",
        # Platform info leakage
        "platform",
        "sysconfig",
        # Sockets/networking
        "socket",
        "_socket",
        "ssl",
        "_ssl",
        "select",
        "selectors",
        "asyncio",
        # File-related
        "io",
        "_io",
        "tempfile",
        # Weak references (can leak objects)
        "weakref",
        # Exit/termination
        "atexit",
    }
)


@dataclass
class ImportRestrictions:
    """Configuration for import restrictions in the sandbox.

    Attributes:
        allowed: Set of explicitly allowed module names. If non-empty,
            only these modules can be imported (whitelist mode).
        blocked: Set of explicitly blocked module names. Used in
            blacklist mode when allowed is empty.
        block_all: If True, block all imports except builtins.
    """

    allowed: set[str] = field(default_factory=set)
    blocked: set[str] = field(default_factory=set)
    block_all: bool = False

    def is_allowed(self, module_name: str) -> tuple[bool, str | None]:
        """Check if a module import is allowed.

        Args:
            module_name: The module name to check.

        Returns:
            Tuple of (is_allowed, reason_if_blocked).
        """
        # Get the top-level module
        top_level = module_name.split(".")[0]

        # Always blocked takes precedence
        if module_name in ALWAYS_BLOCKED_IMPORTS or top_level in ALWAYS_BLOCKED_IMPORTS:
            return False, "Module is on the always-blocked list for security"

        # Check block_all mode
        if self.block_all:
            return False, "All imports are blocked in this sandbox"

        # Explicit blocked set takes precedence over the allowed whitelist
        if top_level in self.blocked or module_name in self.blocked:
            return False, "Module is explicitly blocked"

        # Whitelist mode (allowed is non-empty)
        if self.allowed:
            if top_level in self.allowed or module_name in self.allowed:
                return True, None
            return False, "Module is not on the allowed list"

        return True, None


# Safe imports that are typically allowed for data processing
SAFE_IMPORTS = frozenset(
    {
        "json",
        "re",
        "math",
        "statistics",
        "decimal",
        "fractions",
        "random",
        "collections",
        "itertools",
        "functools",
        "operator",
        "string",
        "textwrap",
        "unicodedata",
        "difflib",
        "typing",
        "dataclasses",
        "enum",
        "numbers",
        "datetime",
        "calendar",
        "time",
        "copy",
        "pprint",
        "reprlib",
        "types",
        "abc",
        "contextlib",
        "heapq",
        "bisect",
        "array",
        "hashlib",
        "hmac",
        "secrets",
        "base64",
        "binascii",
        "struct",
        "codecs",
        "html",
        "html.parser",
        "html.entities",
        "urllib.parse",
        "zlib",
        "gzip",
        "bz2",
        "lzma",
        "csv",
    }
)


def get_safe_imports() -> set[str]:
    """Return a copy of the safe imports set.

    These are modules that are generally safe to allow in a sandbox
    for data processing tasks.
    """
    return set(SAFE_IMPORTS)


@dataclass
class PathRestrictions:
    """Configuration for filesystem path restrictions in the sandbox.

    Attributes:
        allowed_read: Set of directory paths allowed for reading.
        allowed_write: Set of directory paths allowed for writing.
        allow_cwd: Whether to allow read/write in the current working directory.
        working_directory: Optional working directory override.
    """

    allowed_read: set[Path] = field(default_factory=set)
    allowed_write: set[Path] = field(default_factory=set)
    allow_cwd: bool = False
    working_directory: Path | None = None

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve a path relative to the working directory."""
        p = Path(path)
        if not p.is_absolute():
            base = self.working_directory or Path.cwd()
            p = base / p
        return p.resolve()

    def can_read(self, path: str | Path) -> bool:
        """Check if a path can be read."""
        resolved = self._resolve_path(path)

        # Check if it's under any allowed read directory
        for allowed in self.allowed_read:
            try:
                resolved.relative_to(allowed.resolve())
                return True
            except ValueError:
                continue

        # Check CWD allowance
        if self.allow_cwd:
            cwd = self.working_directory or Path.cwd()
            try:
                resolved.relative_to(cwd.resolve())
                return True
            except ValueError:
                pass

        return False

    def can_write(self, path: str | Path) -> bool:
        """Check if a path can be written."""
        resolved = self._resolve_path(path)

        # Check if it's under any allowed write directory
        for allowed in self.allowed_write:
            try:
                resolved.relative_to(allowed.resolve())
                return True
            except ValueError:
                continue

        # Check CWD allowance
        if self.allow_cwd:
            cwd = self.working_directory or Path.cwd()
            try:
                resolved.relative_to(cwd.resolve())
                return True
            except ValueError:
                pass

        return False
