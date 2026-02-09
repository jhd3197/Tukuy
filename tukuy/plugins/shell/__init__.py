"""Shell execution plugin.

Skills-only plugin providing shell command execution and which lookup.

Pure stdlib — no external dependencies.
Both skills declare ``requires_filesystem=True`` and ``requires_network=True``
for SafetyPolicy enforcement.
"""

import shutil
import subprocess
from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_command, get_security_context
from ...skill import skill, ConfigParam, ConfigScope, RiskLevel


@skill(
    name="shell_execute",
    description="Execute a shell command with timeout, capturing stdout and stderr.",
    category="shell",
    tags=["shell", "exec"],
    side_effects=True,
    requires_filesystem=True,
    requires_network=True,
    display_name="Execute Command",
    icon="terminal",
    risk_level=RiskLevel.DANGEROUS,
    group="Shell",
    config_params=[
        ConfigParam(
            name="timeout",
            display_name="Timeout",
            description="Default timeout for command execution.",
            type="number",
            default=30,
            min=1,
            max=600,
            unit="seconds",
        ),
        ConfigParam(
            name="default_cwd",
            display_name="Working Directory",
            description="Default working directory for commands.",
            type="path",
            path_type="directory",
            placeholder="/path/to/project",
        ),
        ConfigParam(
            name="allowed_commands",
            display_name="Allowed Commands",
            description="Whitelist of permitted commands. Empty allows all.",
            type="string[]",
            default=[],
            item_placeholder="e.g. ls, git, npm",
        ),
    ],
)
def shell_execute(
    command: str,
    timeout: int = 30,
    cwd: str = "",
    shell: bool = True,
) -> dict:
    """Execute a shell command and return its output."""
    check_command(command)
    ctx = get_security_context()
    if ctx and ctx.working_directory and not cwd:
        cwd = ctx.working_directory
    kwargs: Dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": timeout,
        "shell": shell,
    }
    if cwd:
        kwargs["cwd"] = cwd

    try:
        result = subprocess.run(command, **kwargs)
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "success": False,
        }


@skill(
    name="shell_which",
    description="Find the full path of an executable (like Unix 'which').",
    category="shell",
    tags=["shell", "which"],
    idempotent=True,
    requires_filesystem=True,
    requires_network=False,
    display_name="Which",
    icon="search",
    risk_level=RiskLevel.SAFE,
    group="Shell",
)
def shell_which(name: str) -> dict:
    """Locate an executable on PATH."""
    path = shutil.which(name)
    return {"name": name, "path": path, "found": path is not None}


class ShellPlugin(TransformerPlugin):
    """Plugin providing shell execution skills (no transformers)."""

    def __init__(self):
        super().__init__("shell")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "shell_execute": shell_execute.__skill__,
            "shell_which": shell_which.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="shell",
            display_name="Shell",
            description="Execute shell commands and find executables.",
            icon="terminal",
            color="#ef4444",
            group="Core",
            requires=PluginRequirements(filesystem=True, network=True),
        )
