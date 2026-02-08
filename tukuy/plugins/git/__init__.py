"""Git operations plugin.

Skills-only plugin providing git status, diff, log, commit, and branch
operations via subprocess.

Pure stdlib — no external dependencies.
All skills declare ``requires_filesystem=True`` for SafetyPolicy enforcement.
"""

import subprocess
from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin
from ...skill import skill


def _run_git(args: List[str], cwd: str = ".") -> Dict[str, Any]:
    """Run a git command and return structured output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd or ".",
        )
        return {
            "command": f"git {' '.join(args)}",
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }
    except FileNotFoundError:
        return {
            "command": f"git {' '.join(args)}",
            "stdout": "",
            "stderr": "git is not installed or not on PATH",
            "returncode": -1,
            "success": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "command": f"git {' '.join(args)}",
            "stdout": "",
            "stderr": "Command timed out after 30s",
            "returncode": -1,
            "success": False,
        }


@skill(
    name="git_status",
    description="Get the current git status (modified, staged, untracked files).",
    category="git",
    tags=["git", "vcs"],
    idempotent=True,
    requires_filesystem=True,
)
def git_status(cwd: str = ".") -> dict:
    """Get git repository status."""
    result = _run_git(["status", "--porcelain", "-b"], cwd)
    if not result["success"]:
        return result

    lines = result["stdout"].splitlines()
    branch = ""
    modified = []
    staged = []
    untracked = []

    for line in lines:
        if line.startswith("##"):
            branch = line[3:].split("...")[0]
            continue
        if len(line) < 2:
            continue
        index_status = line[0]
        work_status = line[1]
        filename = line[3:]

        if index_status in ("M", "A", "D", "R"):
            staged.append({"file": filename, "status": index_status})
        if work_status in ("M", "D"):
            modified.append({"file": filename, "status": work_status})
        if index_status == "?" and work_status == "?":
            untracked.append(filename)

    return {
        "branch": branch,
        "staged": staged,
        "modified": modified,
        "untracked": untracked,
        "clean": len(staged) == 0 and len(modified) == 0 and len(untracked) == 0,
        "success": True,
    }


@skill(
    name="git_diff",
    description="Show git diff (staged, unstaged, or between refs).",
    category="git",
    tags=["git", "vcs", "diff"],
    idempotent=True,
    requires_filesystem=True,
)
def git_diff(
    staged: bool = False,
    ref: str = "",
    path: str = "",
    cwd: str = ".",
) -> dict:
    """Get git diff output."""
    args = ["diff"]
    if staged:
        args.append("--cached")
    if ref:
        args.append(ref)
    if path:
        args.extend(["--", path])

    result = _run_git(args, cwd)
    if not result["success"]:
        return result

    # Parse diff stats
    stat_result = _run_git(args + ["--stat"], cwd)
    return {
        "diff": result["stdout"],
        "stats": stat_result["stdout"] if stat_result["success"] else "",
        "has_changes": len(result["stdout"]) > 0,
        "success": True,
    }


@skill(
    name="git_log",
    description="Show recent git commit log.",
    category="git",
    tags=["git", "vcs", "log"],
    idempotent=True,
    requires_filesystem=True,
)
def git_log(
    n: int = 10,
    oneline: bool = False,
    path: str = "",
    cwd: str = ".",
) -> dict:
    """Get git commit log."""
    fmt = "--oneline" if oneline else "--format=%H|%an|%ae|%ai|%s"
    args = ["log", fmt, f"-{n}"]
    if path:
        args.extend(["--", path])

    result = _run_git(args, cwd)
    if not result["success"]:
        return result

    if oneline:
        return {"log": result["stdout"], "count": len(result["stdout"].splitlines()), "success": True}

    commits = []
    for line in result["stdout"].splitlines():
        parts = line.split("|", 4)
        if len(parts) == 5:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "email": parts[2],
                "date": parts[3],
                "message": parts[4],
            })

    return {"commits": commits, "count": len(commits), "success": True}


@skill(
    name="git_commit",
    description="Stage files and create a git commit.",
    category="git",
    tags=["git", "vcs", "commit"],
    side_effects=True,
    requires_filesystem=True,
)
def git_commit(
    message: str,
    files: Optional[list] = None,
    all: bool = False,
    cwd: str = ".",
) -> dict:
    """Create a git commit."""
    # Stage files
    if files:
        for f in files:
            add_result = _run_git(["add", f], cwd)
            if not add_result["success"]:
                return {"error": f"Failed to stage {f}: {add_result['stderr']}", "success": False}
    elif all:
        add_result = _run_git(["add", "-A"], cwd)
        if not add_result["success"]:
            return {"error": f"Failed to stage: {add_result['stderr']}", "success": False}

    # Commit
    result = _run_git(["commit", "-m", message], cwd)
    return {
        "message": message,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "success": result["success"],
    }


@skill(
    name="git_branch",
    description="List, create, or switch git branches.",
    category="git",
    tags=["git", "vcs", "branch"],
    idempotent=False,
    requires_filesystem=True,
)
def git_branch(
    name: str = "",
    action: str = "list",
    cwd: str = ".",
) -> dict:
    """Manage git branches.

    Actions: "list", "create", "switch", "delete".
    """
    if action == "list":
        result = _run_git(["branch", "-a"], cwd)
        if not result["success"]:
            return result
        branches = []
        current = ""
        for line in result["stdout"].splitlines():
            line = line.strip()
            if line.startswith("* "):
                current = line[2:]
                branches.append(current)
            else:
                branches.append(line)
        return {"branches": branches, "current": current, "success": True}

    if not name:
        return {"error": "Branch name is required for this action", "success": False}

    if action == "create":
        result = _run_git(["checkout", "-b", name], cwd)
    elif action == "switch":
        result = _run_git(["checkout", name], cwd)
    elif action == "delete":
        result = _run_git(["branch", "-d", name], cwd)
    else:
        return {"error": f"Unknown action: {action}", "success": False}

    return {
        "action": action,
        "branch": name,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "success": result["success"],
    }


class GitPlugin(TransformerPlugin):
    """Plugin providing git operations as skills (no transformers)."""

    def __init__(self):
        super().__init__("git")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "git_status": git_status.__skill__,
            "git_diff": git_diff.__skill__,
            "git_log": git_log.__skill__,
            "git_commit": git_commit.__skill__,
            "git_branch": git_branch.__skill__,
        }
