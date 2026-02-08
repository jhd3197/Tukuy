"""File operations plugin.

Skills-only plugin providing file read, write, edit (search-replace),
list (glob), and info (metadata) operations.

Pure stdlib — no external dependencies.
All skills declare ``requires_filesystem=True`` for SafetyPolicy enforcement.
"""

import glob as _glob
import os
import stat
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...skill import skill


@skill(
    name="file_read",
    description="Read the contents of a file.",
    category="file",
    tags=["file", "read"],
    idempotent=True,
    requires_filesystem=True,
)
def file_read(path: str) -> dict:
    """Read a file and return its contents."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"path": path, "content": content, "size": len(content)}


@skill(
    name="file_write",
    description="Write content to a file, creating directories as needed.",
    category="file",
    tags=["file", "write"],
    side_effects=True,
    requires_filesystem=True,
)
def file_write(path: str, content: str = "", append: bool = False) -> dict:
    """Write content to a file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        f.write(content)
    return {"path": path, "bytes_written": len(content.encode("utf-8")), "append": append}


@skill(
    name="file_edit",
    description="Search-and-replace within a file.",
    category="file",
    tags=["file", "edit"],
    side_effects=True,
    requires_filesystem=True,
)
def file_edit(path: str, search: str = "", replace: str = "", count: int = -1) -> dict:
    """Replace occurrences of *search* with *replace* in a file.

    *count* limits the number of replacements (-1 = all).
    """
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()

    if count < 0:
        new_content = original.replace(search, replace)
    else:
        new_content = original.replace(search, replace, count)

    replacements = original.count(search) if count < 0 else min(original.count(search), count)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return {"path": path, "replacements": replacements}


@skill(
    name="file_list",
    description="List files matching a glob pattern.",
    category="file",
    tags=["file", "list", "glob"],
    idempotent=True,
    requires_filesystem=True,
)
def file_list(pattern: str) -> dict:
    """List files matching a glob pattern."""
    matches = sorted(_glob.glob(pattern, recursive=True))
    return {"pattern": pattern, "matches": matches, "count": len(matches)}


@skill(
    name="file_info",
    description="Get file metadata (size, modified time, permissions).",
    category="file",
    tags=["file", "info", "metadata"],
    idempotent=True,
    requires_filesystem=True,
)
def file_info(path: str) -> dict:
    """Return metadata about a file."""
    st = os.stat(path)
    return {
        "path": path,
        "exists": True,
        "size": st.st_size,
        "is_file": stat.S_ISREG(st.st_mode),
        "is_dir": stat.S_ISDIR(st.st_mode),
        "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
        "created": datetime.fromtimestamp(st.st_ctime).isoformat(),
    }


class FileOpsPlugin(TransformerPlugin):
    """Plugin providing file operation skills (no transformers)."""

    def __init__(self):
        super().__init__("file_ops")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "file_read": file_read.__skill__,
            "file_write": file_write.__skill__,
            "file_edit": file_edit.__skill__,
            "file_list": file_list.__skill__,
            "file_info": file_info.__skill__,
        }
