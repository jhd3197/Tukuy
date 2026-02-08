"""Tests for the Env File Manager plugin."""

import os

import pytest

from tukuy.plugins.env import (
    EnvPlugin,
    env_read,
    env_write,
    env_remove,
    env_list,
    _mask_value,
    _parse_env_content,
)
from tukuy.skill import SkillResult
from tukuy.safety import SafetyPolicy


# ── Helper function tests ────────────────────────────────────────────────


class TestMaskValue:
    def test_api_key_masked(self):
        assert _mask_value("sk-abc123xyz", "api_key") == "********3xyz"

    def test_short_key_fully_masked(self):
        assert _mask_value("abc", "api_key") == "****"

    def test_endpoint_not_masked(self):
        assert _mask_value("http://localhost:8080", "endpoint") == "http://localhost:8080"


class TestParseEnvContent:
    def test_basic(self):
        content = "KEY1=value1\nKEY2=value2"
        result = _parse_env_content(content)
        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_skips_comments(self):
        content = "# comment\nKEY=value"
        result = _parse_env_content(content)
        assert result == {"KEY": "value"}

    def test_skips_empty_lines(self):
        content = "\n\nKEY=value\n\n"
        result = _parse_env_content(content)
        assert result == {"KEY": "value"}

    def test_strips_quotes(self):
        content = 'KEY="quoted value"'
        result = _parse_env_content(content)
        assert result == {"KEY": "quoted value"}

    def test_single_quotes(self):
        content = "KEY='single quoted'"
        result = _parse_env_content(content)
        assert result == {"KEY": "single quoted"}

    def test_value_with_equals(self):
        content = "URL=http://host?a=1&b=2"
        result = _parse_env_content(content)
        assert result == {"URL": "http://host?a=1&b=2"}


# ── Skill tests ──────────────────────────────────────────────────────────


class TestEnvRead:
    def test_read_env(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=abc123\nDEBUG=true", encoding="utf-8")
        result = env_read.__skill__.invoke(str(env_file))
        assert result.success is True
        assert result.value["exists"] is True
        assert result.value["values"]["API_KEY"] == "abc123"
        assert result.value["values"]["DEBUG"] == "true"

    def test_read_nonexistent(self, tmp_path):
        result = env_read.__skill__.invoke(str(tmp_path / ".env"))
        assert result.success is True
        assert result.value["exists"] is False

    def test_read_masked(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=sk-verysecretkey", encoding="utf-8")
        result = env_read.__skill__.invoke(str(env_file), mask=True)
        assert result.success is True
        assert "****" in result.value["values"]["API_KEY"]
        assert result.value["values"]["API_KEY"].endswith("tkey")


class TestEnvWrite:
    def test_write_new_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("", encoding="utf-8")
        result = env_write.__skill__.invoke("NEW_KEY", "new_value", str(env_file))
        assert result.success is True
        content = env_file.read_text(encoding="utf-8")
        assert "NEW_KEY=new_value" in content
        # Clean up env
        os.environ.pop("NEW_KEY", None)

    def test_update_existing_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=old_value\n", encoding="utf-8")
        env_write.__skill__.invoke("KEY", "new_value", str(env_file))
        content = env_file.read_text(encoding="utf-8")
        assert "KEY=new_value" in content
        assert "old_value" not in content
        os.environ.pop("KEY", None)

    def test_uncomments_commented_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# KEY=old\n", encoding="utf-8")
        env_write.__skill__.invoke("KEY", "restored", str(env_file))
        content = env_file.read_text(encoding="utf-8")
        assert "KEY=restored" in content
        assert "# KEY=" not in content
        os.environ.pop("KEY", None)

    def test_creates_file(self, tmp_path):
        env_file = tmp_path / "new.env"
        env_write.__skill__.invoke("KEY", "val", str(env_file))
        assert env_file.exists()
        assert "KEY=val" in env_file.read_text(encoding="utf-8")
        os.environ.pop("KEY", None)


class TestEnvRemove:
    def test_remove_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value\nOTHER=keep\n", encoding="utf-8")
        os.environ["KEY"] = "value"
        result = env_remove.__skill__.invoke("KEY", str(env_file))
        assert result.success is True
        content = env_file.read_text(encoding="utf-8")
        assert "# KEY=" in content
        assert "KEY" not in os.environ
        assert "OTHER=keep" in content

    def test_remove_nonexistent_file(self, tmp_path):
        result = env_remove.__skill__.invoke("KEY", str(tmp_path / ".env"))
        assert result.success is True
        assert result.value["action"] == "not_found"


class TestEnvList:
    def test_list_keys(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=secret\nENDPOINT_URL=http://localhost\n", encoding="utf-8")
        result = env_list.__skill__.invoke(str(env_file))
        assert result.success is True
        assert result.value["count"] == 2
        keys = {k["key"] for k in result.value["keys"]}
        assert keys == {"API_KEY", "ENDPOINT_URL"}
        # API_KEY should be masked (6 chars -> 2 stars + last 4)
        api_entry = next(k for k in result.value["keys"] if k["key"] == "API_KEY")
        assert "**" in api_entry["masked_value"]
        assert api_entry["masked_value"] != "secret"
        # URL should not be masked
        url_entry = next(k for k in result.value["keys"] if k["key"] == "ENDPOINT_URL")
        assert url_entry["masked_value"] == "http://localhost"
        assert url_entry["type"] == "endpoint"


# ── Safety policy tests ──────────────────────────────────────────────────


class TestEnvSafety:
    def test_blocked_by_restrictive_policy(self, tmp_path):
        policy = SafetyPolicy(allow_filesystem=False)
        result = env_read.__skill__.invoke(str(tmp_path / ".env"), policy=policy)
        assert result.failed

    def test_all_skills_declare_filesystem(self):
        plugin = EnvPlugin()
        for name, sk in plugin.skills.items():
            assert sk.descriptor.requires_filesystem is True, f"{name} missing requires_filesystem"


# ── Plugin registration ──────────────────────────────────────────────────


class TestEnvPlugin:
    def test_plugin_name(self):
        plugin = EnvPlugin()
        assert plugin.name == "env"

    def test_no_transformers(self):
        plugin = EnvPlugin()
        assert plugin.transformers == {}

    def test_has_all_skills(self):
        plugin = EnvPlugin()
        names = set(plugin.skills.keys())
        assert names == {"env_read", "env_write", "env_remove", "env_list"}
