"""Tests for the File Operations plugin."""

import os
import tempfile

import pytest

from tukuy.plugins.file_ops import (
    FileOpsPlugin,
    file_read,
    file_write,
    file_edit,
    file_list,
    file_info,
)
from tukuy.skill import SkillResult
from tukuy.safety import SafetyPolicy


# ── Skill tests ───────────────────────────────────────────────────────────


class TestFileRead:
    def test_read_file(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("hello world", encoding="utf-8")
        result = file_read.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["content"] == "hello world"
        assert result.value["size"] == 11

    def test_read_nonexistent(self, tmp_path):
        result = file_read.__skill__.invoke(str(tmp_path / "nope.txt"))
        assert result.success is False


class TestFileWrite:
    def test_write_file(self, tmp_path):
        p = tmp_path / "out.txt"
        result = file_write.__skill__.invoke(str(p), content="data")
        assert result.success is True
        assert p.read_text(encoding="utf-8") == "data"

    def test_write_append(self, tmp_path):
        p = tmp_path / "out.txt"
        p.write_text("A", encoding="utf-8")
        file_write.__skill__.invoke(str(p), content="B", append=True)
        assert p.read_text(encoding="utf-8") == "AB"

    def test_write_creates_dirs(self, tmp_path):
        p = tmp_path / "sub" / "dir" / "file.txt"
        file_write.__skill__.invoke(str(p), content="nested")
        assert p.read_text(encoding="utf-8") == "nested"


class TestFileEdit:
    def test_search_replace(self, tmp_path):
        p = tmp_path / "edit.txt"
        p.write_text("hello world hello", encoding="utf-8")
        result = file_edit.__skill__.invoke(str(p), search="hello", replace="hi")
        assert result.success is True
        assert result.value["replacements"] == 2
        assert p.read_text(encoding="utf-8") == "hi world hi"

    def test_limited_count(self, tmp_path):
        p = tmp_path / "edit.txt"
        p.write_text("aaa", encoding="utf-8")
        file_edit.__skill__.invoke(str(p), search="a", replace="b", count=2)
        assert p.read_text(encoding="utf-8") == "bba"


class TestFileList:
    def test_glob(self, tmp_path):
        (tmp_path / "a.txt").write_text("a", encoding="utf-8")
        (tmp_path / "b.txt").write_text("b", encoding="utf-8")
        (tmp_path / "c.py").write_text("c", encoding="utf-8")
        result = file_list.__skill__.invoke(str(tmp_path / "*.txt"))
        assert result.success is True
        assert result.value["count"] == 2


class TestFileInfo:
    def test_info(self, tmp_path):
        p = tmp_path / "info.txt"
        p.write_text("data", encoding="utf-8")
        result = file_info.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["exists"] is True
        assert result.value["is_file"] is True
        assert result.value["size"] == 4

    def test_info_nonexistent(self, tmp_path):
        result = file_info.__skill__.invoke(str(tmp_path / "nope.txt"))
        assert result.success is False


# ── Safety policy tests ──────────────────────────────────────────────────


class TestFileOpsSafety:
    def test_blocked_by_restrictive_policy(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("data", encoding="utf-8")
        policy = SafetyPolicy(allow_filesystem=False)
        result = file_read.__skill__.invoke(str(p), policy=policy)
        assert result.failed
        assert "filesystem" in result.error.lower()

    def test_allowed_by_permissive_policy(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("data", encoding="utf-8")
        policy = SafetyPolicy.permissive()
        result = file_read.__skill__.invoke(str(p), policy=policy)
        assert result.success is True

    def test_all_skills_declare_filesystem(self):
        plugin = FileOpsPlugin()
        for name, sk in plugin.skills.items():
            assert sk.descriptor.requires_filesystem is True, f"{name} missing requires_filesystem"


# ── Plugin registration ──────────────────────────────────────────────────


class TestFileOpsPlugin:
    def test_plugin_name(self):
        plugin = FileOpsPlugin()
        assert plugin.name == "file_ops"

    def test_no_transformers(self):
        plugin = FileOpsPlugin()
        assert plugin.transformers == {}

    def test_has_all_skills(self):
        plugin = FileOpsPlugin()
        names = set(plugin.skills.keys())
        assert names == {"file_read", "file_write", "file_edit", "file_list", "file_info"}
