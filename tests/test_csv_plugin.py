"""Tests for the CSV plugin."""

import pytest

from tukuy.plugins.csv_plugin import (
    CsvPlugin,
    csv_read,
    csv_write,
    csv_query,
    csv_headers,
    csv_stats,
)
from tukuy.safety import SafetyPolicy


# ── Skill tests ───────────────────────────────────────────────────────────


class TestCsvRead:
    def test_read_csv(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
        result = csv_read.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["headers"] == ["name", "age"]
        assert result.value["row_count"] == 2
        assert result.value["rows"][0]["name"] == "Alice"

    def test_read_with_delimiter(self, tmp_path):
        p = tmp_path / "data.tsv"
        p.write_text("name\tage\nAlice\t30\n", encoding="utf-8")
        result = csv_read.__skill__.invoke(str(p), delimiter="\t")
        assert result.success is True
        assert result.value["headers"] == ["name", "age"]

    def test_read_nonexistent(self, tmp_path):
        result = csv_read.__skill__.invoke(str(tmp_path / "nope.csv"))
        assert result.success is False

    def test_read_empty_csv(self, tmp_path):
        p = tmp_path / "empty.csv"
        p.write_text("name,age\n", encoding="utf-8")
        result = csv_read.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["row_count"] == 0
        assert result.value["headers"] == ["name", "age"]


class TestCsvWrite:
    def test_write_csv(self, tmp_path):
        p = tmp_path / "out.csv"
        rows = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
        result = csv_write.__skill__.invoke(str(p), rows=rows)
        assert result.success is True
        assert result.value["row_count"] == 2
        content = p.read_text(encoding="utf-8")
        assert "Alice" in content
        assert "Bob" in content

    def test_write_with_explicit_headers(self, tmp_path):
        p = tmp_path / "out.csv"
        rows = [{"name": "Alice", "age": "30"}]
        csv_write.__skill__.invoke(str(p), rows=rows, headers=["age", "name"])
        content = p.read_text(encoding="utf-8")
        # Headers should appear in the specified order
        first_line = content.strip().split("\n")[0]
        assert first_line == "age,name"

    def test_write_creates_dirs(self, tmp_path):
        p = tmp_path / "sub" / "dir" / "out.csv"
        rows = [{"x": "1"}]
        result = csv_write.__skill__.invoke(str(p), rows=rows)
        assert result.success is True
        assert p.exists()


class TestCsvQuery:
    def test_query_match(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("name,city\nAlice,Lima\nBob,Lima\nCarl,Cusco\n", encoding="utf-8")
        result = csv_query.__skill__.invoke(str(p), column="city", value="Lima")
        assert result.success is True
        assert result.value["count"] == 2

    def test_query_no_match(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("name,city\nAlice,Lima\n", encoding="utf-8")
        result = csv_query.__skill__.invoke(str(p), column="city", value="Bogota")
        assert result.success is True
        assert result.value["count"] == 0


class TestCsvHeaders:
    def test_headers(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("name,age,city\nAlice,30,Lima\n", encoding="utf-8")
        result = csv_headers.__skill__.invoke(str(p))
        assert result.success is True
        assert result.value["headers"] == ["name", "age", "city"]

    def test_headers_nonexistent(self, tmp_path):
        result = csv_headers.__skill__.invoke(str(tmp_path / "nope.csv"))
        assert result.success is False


class TestCsvStats:
    def test_stats(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("name,score\nA,10\nB,20\nC,30\n", encoding="utf-8")
        result = csv_stats.__skill__.invoke(str(p), column="score")
        assert result.success is True
        v = result.value
        assert v["count"] == 3
        assert v["min"] == 10.0
        assert v["max"] == 30.0
        assert v["mean"] == 20.0
        assert v["median"] == 20.0
        assert "stdev" in v

    def test_stats_non_numeric(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("name,val\nA,abc\n", encoding="utf-8")
        result = csv_stats.__skill__.invoke(str(p), column="val")
        assert result.success is False


# ── Safety policy tests ──────────────────────────────────────────────────


class TestCsvSafety:
    def test_blocked_by_restrictive_policy(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("a,b\n1,2\n", encoding="utf-8")
        policy = SafetyPolicy(allow_filesystem=False)
        result = csv_read.__skill__.invoke(str(p), policy=policy)
        assert result.failed
        assert "filesystem" in result.error.lower()

    def test_allowed_by_permissive_policy(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("a,b\n1,2\n", encoding="utf-8")
        policy = SafetyPolicy.permissive()
        result = csv_read.__skill__.invoke(str(p), policy=policy)
        assert result.success is True

    def test_all_skills_declare_filesystem(self):
        plugin = CsvPlugin()
        for name, sk in plugin.skills.items():
            assert sk.descriptor.requires_filesystem is True, f"{name} missing requires_filesystem"


# ── Plugin registration ──────────────────────────────────────────────────


class TestCsvPlugin:
    def test_plugin_name(self):
        plugin = CsvPlugin()
        assert plugin.name == "csv"

    def test_no_transformers(self):
        plugin = CsvPlugin()
        assert plugin.transformers == {}

    def test_has_all_skills(self):
        plugin = CsvPlugin()
        names = set(plugin.skills.keys())
        assert names == {"csv_read", "csv_write", "csv_query", "csv_headers", "csv_stats"}
