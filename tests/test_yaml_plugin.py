"""Tests for the YAML plugin."""

import json

import pytest

from tukuy.plugins.yaml_plugin import (
    YamlPlugin,
    yaml_read,
    yaml_write,
    yaml_to_json,
    yaml_validate,
)
from tukuy.safety import SafetyPolicy


# ── Skill tests ───────────────────────────────────────────────────────────


class TestYamlRead:
    def test_read_yaml(self, tmp_path):
        p = tmp_path / "data.yaml"
        p.write_text("name: Alice\nage: 30\n", encoding="utf-8")
        result = yaml_read.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["data"] == {"name": "Alice", "age": 30}
        assert result.value["path"] == str(p)

    def test_read_list(self, tmp_path):
        p = tmp_path / "data.yaml"
        p.write_text("- one\n- two\n- three\n", encoding="utf-8")
        result = yaml_read.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["data"] == ["one", "two", "three"]

    def test_read_nonexistent(self, tmp_path):
        result = yaml_read.__skill__.invoke(str(tmp_path / "nope.yaml"))
        assert result.success is False


class TestYamlWrite:
    def test_write_yaml(self, tmp_path):
        p = tmp_path / "out.yaml"
        data = {"name": "Alice", "age": 30}
        result = yaml_write.__skill__.invoke(str(p), data=data)
        assert result.success is True
        assert result.value["bytes_written"] > 0
        content = p.read_text(encoding="utf-8")
        assert "Alice" in content

    def test_write_creates_dirs(self, tmp_path):
        p = tmp_path / "sub" / "dir" / "out.yaml"
        yaml_write.__skill__.invoke(str(p), data={"x": 1})
        assert p.exists()


class TestYamlToJson:
    def test_to_json(self, tmp_path):
        p = tmp_path / "data.yaml"
        p.write_text("name: Alice\nage: 30\n", encoding="utf-8")
        result = yaml_to_json.__skill__.invoke(str(p))
        assert result.success is True
        parsed = json.loads(result.value["json_string"])
        assert parsed == {"name": "Alice", "age": 30}

    def test_to_json_with_output_path(self, tmp_path):
        src = tmp_path / "data.yaml"
        src.write_text("key: value\n", encoding="utf-8")
        out = tmp_path / "data.json"
        result = yaml_to_json.__skill__.invoke(str(src), output_path=str(out))
        assert result.success is True
        assert out.exists()
        parsed = json.loads(out.read_text(encoding="utf-8"))
        assert parsed == {"key": "value"}


class TestYamlValidate:
    def test_valid_yaml(self, tmp_path):
        p = tmp_path / "data.yaml"
        p.write_text("name: Alice\n", encoding="utf-8")
        result = yaml_validate.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["valid"] is True
        assert result.value["error"] is None

    def test_invalid_yaml(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(":\n  - :\n    : :\n  unbalanced: [\n", encoding="utf-8")
        result = yaml_validate.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["valid"] is False
        assert result.value["error"] is not None


# ── Safety policy tests ──────────────────────────────────────────────────


class TestYamlSafety:
    def test_blocked_by_restrictive_policy(self, tmp_path):
        p = tmp_path / "data.yaml"
        p.write_text("a: 1\n", encoding="utf-8")
        policy = SafetyPolicy(allow_filesystem=False)
        result = yaml_read.__skill__.invoke(str(p), policy=policy)
        assert result.failed
        assert "filesystem" in result.error.lower()

    def test_allowed_by_permissive_policy(self, tmp_path):
        p = tmp_path / "data.yaml"
        p.write_text("a: 1\n", encoding="utf-8")
        policy = SafetyPolicy.permissive()
        result = yaml_read.__skill__.invoke(str(p), policy=policy)
        assert result.success is True

    def test_all_skills_declare_filesystem(self):
        plugin = YamlPlugin()
        for name, sk in plugin.skills.items():
            assert sk.descriptor.requires_filesystem is True, f"{name} missing requires_filesystem"


# ── Plugin registration ──────────────────────────────────────────────────


class TestYamlPlugin:
    def test_plugin_name(self):
        plugin = YamlPlugin()
        assert plugin.name == "yaml"

    def test_no_transformers(self):
        plugin = YamlPlugin()
        assert plugin.transformers == {}

    def test_has_all_skills(self):
        plugin = YamlPlugin()
        names = set(plugin.skills.keys())
        assert names == {"yaml_read", "yaml_write", "yaml_to_json", "yaml_validate"}
