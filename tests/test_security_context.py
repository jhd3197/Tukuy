"""Tests for SecurityContext, SecurityError, contextvar management, and plugin integration."""

import os
import tempfile

import pytest

from tukuy.safety import (
    SecurityContext,
    SecurityError,
    check_command,
    check_host,
    check_read_path,
    check_write_path,
    get_security_context,
    reset_security_context,
    set_security_context,
    SafetyPolicy,
)


# ── SecurityContext: path resolution ─────────────────────────────────────────


class TestSecurityContextResolvePath:
    def test_absolute_path_unchanged(self, tmp_path):
        ctx = SecurityContext()
        resolved = ctx.resolve_path(str(tmp_path / "file.txt"))
        assert resolved == (tmp_path / "file.txt").resolve()

    def test_relative_path_uses_working_directory(self, tmp_path):
        ctx = SecurityContext(working_directory=str(tmp_path))
        resolved = ctx.resolve_path("subdir/file.txt")
        assert resolved == (tmp_path / "subdir" / "file.txt").resolve()

    def test_relative_path_without_working_directory(self):
        ctx = SecurityContext()
        resolved = ctx.resolve_path("file.txt")
        # Should resolve relative to cwd
        from pathlib import Path
        assert resolved == Path("file.txt").resolve()


# ── SecurityContext: is_read_allowed / is_write_allowed ──────────────────────


class TestSecurityContextPathAllowed:
    def test_read_allowed_when_unrestricted(self, tmp_path):
        ctx = SecurityContext()
        assert ctx.is_read_allowed(str(tmp_path / "any_file.txt")) is True

    def test_read_allowed_when_path_in_allowed(self, tmp_path):
        ctx = SecurityContext(allowed_read_paths=[str(tmp_path)])
        assert ctx.is_read_allowed(str(tmp_path / "file.txt")) is True

    def test_read_denied_when_path_outside_allowed(self, tmp_path):
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        ctx = SecurityContext(allowed_read_paths=[str(allowed_dir)])
        assert ctx.is_read_allowed(str(tmp_path / "other" / "file.txt")) is False

    def test_read_denied_when_empty_allowed_list(self, tmp_path):
        ctx = SecurityContext(allowed_read_paths=[])
        assert ctx.is_read_allowed(str(tmp_path / "file.txt")) is False

    def test_write_allowed_when_unrestricted(self, tmp_path):
        ctx = SecurityContext()
        assert ctx.is_write_allowed(str(tmp_path / "file.txt")) is True

    def test_write_allowed_when_path_in_allowed(self, tmp_path):
        ctx = SecurityContext(allowed_write_paths=[str(tmp_path)])
        assert ctx.is_write_allowed(str(tmp_path / "file.txt")) is True

    def test_write_denied_when_path_outside_allowed(self, tmp_path):
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        ctx = SecurityContext(allowed_write_paths=[str(allowed_dir)])
        assert ctx.is_write_allowed(str(tmp_path / "other" / "file.txt")) is False

    def test_blocked_paths_take_precedence(self, tmp_path):
        blocked_dir = tmp_path / "secrets"
        blocked_dir.mkdir()
        ctx = SecurityContext(
            allowed_read_paths=[str(tmp_path)],
            blocked_paths=[str(blocked_dir)],
        )
        assert ctx.is_read_allowed(str(tmp_path / "file.txt")) is True
        assert ctx.is_read_allowed(str(blocked_dir / "key.pem")) is False

    def test_ignore_patterns_deny(self, tmp_path):
        ctx = SecurityContext(
            allowed_read_paths=[str(tmp_path)],
            ignore_patterns=["*.secret", ".env"],
        )
        assert ctx.is_read_allowed(str(tmp_path / "config.txt")) is True
        assert ctx.is_read_allowed(str(tmp_path / "key.secret")) is False
        assert ctx.is_read_allowed(str(tmp_path / ".env")) is False


# ── SecurityContext: is_host_allowed ─────────────────────────────────────────


class TestSecurityContextHostAllowed:
    def test_host_allowed_when_unrestricted(self):
        ctx = SecurityContext()
        assert ctx.is_host_allowed("example.com") is True

    def test_host_allowed_when_in_allowed_list(self):
        ctx = SecurityContext(allowed_hosts=["api.example.com", "cdn.example.com"])
        assert ctx.is_host_allowed("api.example.com") is True

    def test_host_denied_when_not_in_allowed_list(self):
        ctx = SecurityContext(allowed_hosts=["api.example.com"])
        assert ctx.is_host_allowed("evil.com") is False

    def test_host_denied_when_empty_allowed_list(self):
        ctx = SecurityContext(allowed_hosts=[])
        assert ctx.is_host_allowed("example.com") is False

    def test_blocked_hosts_take_precedence(self):
        ctx = SecurityContext(
            allowed_hosts=None,  # unrestricted
            blocked_hosts=["evil.com"],
        )
        assert ctx.is_host_allowed("good.com") is True
        assert ctx.is_host_allowed("evil.com") is False

    def test_host_comparison_case_insensitive(self):
        ctx = SecurityContext(allowed_hosts=["API.Example.COM"])
        assert ctx.is_host_allowed("api.example.com") is True

    def test_blocked_host_case_insensitive(self):
        ctx = SecurityContext(blocked_hosts=["Evil.COM"])
        assert ctx.is_host_allowed("evil.com") is False


# ── SecurityContext: is_command_allowed ──────────────────────────────────────


class TestSecurityContextCommandAllowed:
    def test_command_allowed_when_unrestricted(self):
        ctx = SecurityContext()
        assert ctx.is_command_allowed("rm -rf /") is True

    def test_command_allowed_when_prefix_matches(self):
        ctx = SecurityContext(allowed_commands=["git", "npm"])
        assert ctx.is_command_allowed("git status") is True
        assert ctx.is_command_allowed("npm install") is True

    def test_command_denied_when_not_in_allowed(self):
        ctx = SecurityContext(allowed_commands=["git", "npm"])
        assert ctx.is_command_allowed("rm -rf /") is False

    def test_exact_command_match(self):
        ctx = SecurityContext(allowed_commands=["git"])
        assert ctx.is_command_allowed("git") is True

    def test_command_denied_when_empty_allowed_list(self):
        ctx = SecurityContext(allowed_commands=[])
        assert ctx.is_command_allowed("ls") is False

    def test_partial_prefix_no_false_match(self):
        ctx = SecurityContext(allowed_commands=["git"])
        # "gitfoo" should not match "git" prefix (no space separator)
        assert ctx.is_command_allowed("gitfoo") is False


# ── check_read_path / check_write_path helpers ──────────────────────────────


class TestCheckPathHelpers:
    def test_check_read_path_noop_without_context(self):
        """No SecurityContext active → passthrough."""
        result = check_read_path("/some/path")
        assert result == "/some/path"

    def test_check_write_path_noop_without_context(self):
        result = check_write_path("/some/path")
        assert result == "/some/path"

    def test_check_read_path_allowed(self, tmp_path):
        ctx = SecurityContext(allowed_read_paths=[str(tmp_path)])
        token = set_security_context(ctx)
        try:
            result = check_read_path(str(tmp_path / "file.txt"))
            from pathlib import Path
            assert Path(result) == (tmp_path / "file.txt").resolve()
        finally:
            reset_security_context(token)

    def test_check_read_path_denied(self, tmp_path):
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        ctx = SecurityContext(allowed_read_paths=[str(allowed_dir)])
        token = set_security_context(ctx)
        try:
            with pytest.raises(SecurityError, match="Read access denied"):
                check_read_path(str(tmp_path / "other" / "file.txt"))
        finally:
            reset_security_context(token)

    def test_check_write_path_allowed(self, tmp_path):
        ctx = SecurityContext(allowed_write_paths=[str(tmp_path)])
        token = set_security_context(ctx)
        try:
            result = check_write_path(str(tmp_path / "file.txt"))
            from pathlib import Path
            assert Path(result) == (tmp_path / "file.txt").resolve()
        finally:
            reset_security_context(token)

    def test_check_write_path_denied(self, tmp_path):
        ctx = SecurityContext(allowed_write_paths=[])
        token = set_security_context(ctx)
        try:
            with pytest.raises(SecurityError, match="Write access denied"):
                check_write_path(str(tmp_path / "file.txt"))
        finally:
            reset_security_context(token)


# ── check_host helper ───────────────────────────────────────────────────────


class TestCheckHostHelper:
    def test_noop_without_context(self):
        check_host("https://example.com")  # should not raise

    def test_allowed_host(self):
        ctx = SecurityContext(allowed_hosts=["example.com"])
        token = set_security_context(ctx)
        try:
            check_host("https://example.com/path")  # should not raise
        finally:
            reset_security_context(token)

    def test_denied_host(self):
        ctx = SecurityContext(allowed_hosts=["example.com"])
        token = set_security_context(ctx)
        try:
            with pytest.raises(SecurityError, match="Host access denied"):
                check_host("https://evil.com/steal")
        finally:
            reset_security_context(token)

    def test_blocked_host(self):
        ctx = SecurityContext(blocked_hosts=["evil.com"])
        token = set_security_context(ctx)
        try:
            with pytest.raises(SecurityError, match="Host access denied"):
                check_host("https://evil.com/steal")
        finally:
            reset_security_context(token)


# ── check_command helper ────────────────────────────────────────────────────


class TestCheckCommandHelper:
    def test_noop_without_context(self):
        check_command("rm -rf /")  # should not raise

    def test_allowed_command(self):
        ctx = SecurityContext(allowed_commands=["git", "npm"])
        token = set_security_context(ctx)
        try:
            check_command("git status")  # should not raise
        finally:
            reset_security_context(token)

    def test_denied_command(self):
        ctx = SecurityContext(allowed_commands=["git"])
        token = set_security_context(ctx)
        try:
            with pytest.raises(SecurityError, match="Command not allowed"):
                check_command("rm -rf /")
        finally:
            reset_security_context(token)


# ── Contextvar lifecycle ────────────────────────────────────────────────────


class TestSecurityContextVar:
    def test_default_is_none(self):
        assert get_security_context() is None

    def test_set_and_get(self):
        ctx = SecurityContext()
        token = set_security_context(ctx)
        assert get_security_context() is ctx
        reset_security_context(token)

    def test_reset_restores_previous(self):
        ctx1 = SecurityContext(allowed_hosts=["a.com"])
        ctx2 = SecurityContext(allowed_hosts=["b.com"])

        t1 = set_security_context(ctx1)
        assert get_security_context() is ctx1

        t2 = set_security_context(ctx2)
        assert get_security_context() is ctx2

        reset_security_context(t2)
        assert get_security_context() is ctx1

        reset_security_context(t1)

    def test_set_none_clears(self):
        ctx = SecurityContext()
        t1 = set_security_context(ctx)
        assert get_security_context() is not None

        t2 = set_security_context(None)
        assert get_security_context() is None

        reset_security_context(t2)
        reset_security_context(t1)


# ── SafetyPolicy.security_context integration ──────────────────────────────


class TestSafetyPolicySecurityContext:
    def test_default_security_context_is_none(self):
        policy = SafetyPolicy()
        assert policy.security_context is None

    def test_policy_with_security_context(self, tmp_path):
        ctx = SecurityContext(allowed_read_paths=[str(tmp_path)])
        policy = SafetyPolicy(security_context=ctx)
        assert policy.security_context is ctx
        assert policy.security_context.is_read_allowed(str(tmp_path / "f.txt"))

    def test_restrictive_policy_no_security_context(self):
        policy = SafetyPolicy.restrictive()
        assert policy.security_context is None


# ── Integration: file_read with SecurityContext ─────────────────────────────


class TestFileReadIntegration:
    def test_file_read_allowed(self, tmp_path):
        """file_read succeeds when SecurityContext allows the path."""
        test_file = tmp_path / "allowed.txt"
        test_file.write_text("hello world", encoding="utf-8")

        ctx = SecurityContext(allowed_read_paths=[str(tmp_path)])
        token = set_security_context(ctx)
        try:
            from tukuy.plugins.file_ops import file_read
            result = file_read.__skill__.invoke(str(test_file))
            assert result.success
            assert result.value["content"] == "hello world"
        finally:
            reset_security_context(token)

    def test_file_read_denied(self, tmp_path):
        """file_read fails with SecurityError when path is outside allowed."""
        test_file = tmp_path / "secret.txt"
        test_file.write_text("secret", encoding="utf-8")

        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        ctx = SecurityContext(allowed_read_paths=[str(allowed_dir)])
        token = set_security_context(ctx)
        try:
            from tukuy.plugins.file_ops import file_read
            result = file_read.__skill__.invoke(str(test_file))
            assert result.failed
            assert "Read access denied" in result.error
        finally:
            reset_security_context(token)


class TestFileWriteIntegration:
    def test_file_write_allowed(self, tmp_path):
        ctx = SecurityContext(allowed_write_paths=[str(tmp_path)])
        token = set_security_context(ctx)
        try:
            from tukuy.plugins.file_ops import file_write
            out = tmp_path / "out.txt"
            result = file_write.__skill__.invoke(str(out), content="test data")
            assert result.success
            assert out.read_text(encoding="utf-8") == "test data"
        finally:
            reset_security_context(token)

    def test_file_write_denied(self, tmp_path):
        ctx = SecurityContext(allowed_write_paths=[])
        token = set_security_context(ctx)
        try:
            from tukuy.plugins.file_ops import file_write
            out = tmp_path / "denied.txt"
            result = file_write.__skill__.invoke(str(out), content="nope")
            assert result.failed
            assert "Write access denied" in result.error
        finally:
            reset_security_context(token)


# ── Backward compatibility: no SecurityContext = unchanged behavior ──────────


class TestBackwardCompatibility:
    def test_file_read_works_without_context(self, tmp_path):
        """With no SecurityContext active, skills work as before."""
        assert get_security_context() is None
        test_file = tmp_path / "normal.txt"
        test_file.write_text("normal content", encoding="utf-8")

        from tukuy.plugins.file_ops import file_read
        result = file_read.__skill__.invoke(str(test_file))
        assert result.success
        assert result.value["content"] == "normal content"

    def test_check_helpers_passthrough_without_context(self):
        assert get_security_context() is None
        assert check_read_path("/any/path") == "/any/path"
        assert check_write_path("/any/path") == "/any/path"
        check_host("https://any.host.com")  # no raise
        check_command("any command")  # no raise
