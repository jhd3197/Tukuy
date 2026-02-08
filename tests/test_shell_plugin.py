"""Tests for the Shell plugin."""

import sys

import pytest

from tukuy.plugins.shell import ShellPlugin, shell_execute, shell_which
from tukuy.skill import SkillResult
from tukuy.safety import SafetyPolicy


# ── shell_execute skill ──────────────────────────────────────────────────


class TestShellExecute:
    def test_echo(self):
        if sys.platform == "win32":
            result = shell_execute.__skill__.invoke("echo hello")
        else:
            result = shell_execute.__skill__.invoke("echo hello")
        assert result.success is True
        assert result.value["success"] is True
        assert "hello" in result.value["stdout"]

    def test_failing_command(self):
        if sys.platform == "win32":
            cmd = "cmd /c exit 1"
        else:
            cmd = "false"
        result = shell_execute.__skill__.invoke(cmd)
        assert result.success is True  # skill itself succeeds
        assert result.value["success"] is False  # command failed
        assert result.value["returncode"] != 0

    def test_timeout(self):
        if sys.platform == "win32":
            cmd = "ping -n 10 127.0.0.1"
        else:
            cmd = "sleep 10"
        result = shell_execute.__skill__.invoke(cmd, timeout=1)
        assert result.success is True
        assert result.value["success"] is False
        assert "timed out" in result.value["stderr"].lower()


# ── shell_which skill ────────────────────────────────────────────────────


class TestShellWhich:
    def test_find_python(self):
        result = shell_which.__skill__.invoke("python")
        # python may or may not be on PATH, but the call should succeed
        assert result.success is True
        assert "found" in result.value

    def test_not_found(self):
        result = shell_which.__skill__.invoke("nonexistent_binary_xyz_123")
        assert result.success is True
        assert result.value["found"] is False
        assert result.value["path"] is None


# ── Safety policy ─────────────────────────────────────────────────────────


class TestShellSafety:
    def test_blocked_by_no_filesystem(self):
        policy = SafetyPolicy(allow_filesystem=False)
        result = shell_execute.__skill__.invoke("echo hi", policy=policy)
        assert result.failed

    def test_blocked_by_no_network(self):
        policy = SafetyPolicy(allow_network=False)
        result = shell_execute.__skill__.invoke("echo hi", policy=policy)
        assert result.failed

    def test_which_needs_filesystem(self):
        policy = SafetyPolicy(allow_filesystem=False)
        result = shell_which.__skill__.invoke("python", policy=policy)
        assert result.failed

    def test_allowed_by_permissive(self):
        policy = SafetyPolicy.permissive()
        result = shell_which.__skill__.invoke("python", policy=policy)
        assert result.success is True


# ── Plugin registration ──────────────────────────────────────────────────


class TestShellPlugin:
    def test_plugin_name(self):
        plugin = ShellPlugin()
        assert plugin.name == "shell"

    def test_no_transformers(self):
        plugin = ShellPlugin()
        assert plugin.transformers == {}

    def test_has_all_skills(self):
        plugin = ShellPlugin()
        names = set(plugin.skills.keys())
        assert names == {"shell_execute", "shell_which"}

    def test_shell_execute_declares_network(self):
        plugin = ShellPlugin()
        sk = plugin.skills["shell_execute"]
        assert sk.descriptor.requires_network is True
        assert sk.descriptor.requires_filesystem is True
