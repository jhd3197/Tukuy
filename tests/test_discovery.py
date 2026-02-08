"""Tests for two-phase discovery and usage tracking."""

import json
import os
import tempfile

import pytest

from tukuy.core.usage import UsageTracker, get_usage_tracker
from tukuy.core.unified import (
    browse_tools,
    get_tool_details,
    search_tools,
    get_unified_registry,
)


# ---------------------------------------------------------------------------
# UsageTracker unit tests
# ---------------------------------------------------------------------------

class TestUsageTracker:
    def test_record_and_get_count(self):
        tracker = UsageTracker()
        assert tracker.get_count("strip") == 0
        tracker.record("strip")
        tracker.record("strip")
        assert tracker.get_count("strip") == 2

    def test_get_popular(self):
        tracker = UsageTracker()
        tracker.record("a")
        tracker.record("b")
        tracker.record("b")
        tracker.record("c")
        tracker.record("c")
        tracker.record("c")
        popular = tracker.get_popular(2)
        assert popular == ["c", "b"]

    def test_get_popular_empty(self):
        tracker = UsageTracker()
        assert tracker.get_popular() == []

    def test_reset(self):
        tracker = UsageTracker()
        tracker.record("x")
        tracker.reset()
        assert tracker.get_count("x") == 0
        assert tracker.get_popular() == []

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "usage.json")
        t1 = UsageTracker()
        t1.record("strip")
        t1.record("strip")
        t1.record("lowercase")
        t1.save(path)

        t2 = UsageTracker()
        t2.load(path)
        assert t2.get_count("strip") == 2
        assert t2.get_count("lowercase") == 1

    def test_load_merges(self, tmp_path):
        path = str(tmp_path / "usage.json")
        t1 = UsageTracker()
        t1.record("a")
        t1.save(path)

        t2 = UsageTracker()
        t2.record("a")
        t2.load(path)
        assert t2.get_count("a") == 2

    def test_singleton(self):
        tracker = get_usage_tracker()
        assert tracker is get_usage_tracker()


# ---------------------------------------------------------------------------
# browse_tools tests
# ---------------------------------------------------------------------------

class TestBrowseTools:
    def test_structure(self):
        result = browse_tools()
        assert "total_count" in result
        assert "popular" in result
        assert "plugins" in result
        assert isinstance(result["total_count"], int)
        assert result["total_count"] > 0
        assert isinstance(result["popular"], list)
        assert isinstance(result["plugins"], dict)

    def test_plugin_entries(self):
        result = browse_tools()
        for plugin_name, plugin_info in result["plugins"].items():
            assert "tool_count" in plugin_info
            assert "tools" in plugin_info
            assert isinstance(plugin_info["tools"], dict)
            assert plugin_info["tool_count"] == len(plugin_info["tools"])
            for tool_name, desc in plugin_info["tools"].items():
                assert isinstance(tool_name, str)
                assert isinstance(desc, str)
                assert len(desc) <= 83  # 80 + "..."

    def test_total_matches_sum(self):
        result = browse_tools()
        total_from_plugins = sum(
            p["tool_count"] for p in result["plugins"].values()
        )
        assert result["total_count"] == total_from_plugins


# ---------------------------------------------------------------------------
# get_tool_details tests
# ---------------------------------------------------------------------------

class TestGetToolDetails:
    def test_returns_metadata(self):
        # Pick a tool name that we know exists
        index = browse_tools()
        some_tool = None
        for plugin_info in index["plugins"].values():
            if plugin_info["tools"]:
                some_tool = next(iter(plugin_info["tools"]))
                break
        assert some_tool is not None

        details = get_tool_details(some_tool)
        assert len(details) == 1
        d = details[0]
        assert d["name"] == some_tool
        assert "description" in d
        assert "plugin" in d
        assert "parameters" in d

    def test_multiple_names(self):
        index = browse_tools()
        names = []
        for plugin_info in index["plugins"].values():
            for t in plugin_info["tools"]:
                names.append(t)
                if len(names) == 2:
                    break
            if len(names) == 2:
                break

        details = get_tool_details(*names)
        assert len(details) == len(names)

    def test_unknown_name_skipped(self):
        details = get_tool_details("nonexistent_tool_xyz_999")
        assert details == []

    def test_records_usage(self):
        tracker = get_usage_tracker()
        tracker.reset()

        index = browse_tools()
        some_tool = None
        for plugin_info in index["plugins"].values():
            if plugin_info["tools"]:
                some_tool = next(iter(plugin_info["tools"]))
                break

        before = tracker.get_count(some_tool)
        get_tool_details(some_tool)
        assert tracker.get_count(some_tool) == before + 1


# ---------------------------------------------------------------------------
# search_tools tests
# ---------------------------------------------------------------------------

class TestSearchTools:
    def test_returns_results(self):
        results = search_tools("text")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_result_shape(self):
        results = search_tools("text")
        for r in results:
            assert "name" in r
            assert "plugin" in r
            assert "description" in r
            assert "score" in r
            assert r["score"] > 0

    def test_limit(self):
        results = search_tools("text", limit=2)
        assert len(results) <= 2

    def test_empty_query(self):
        results = search_tools("")
        assert results == []

    def test_no_match(self):
        results = search_tools("zzzznonexistenttermzzzz")
        assert results == []

    def test_exact_name_scores_highest(self):
        # Pick a real tool name
        index = browse_tools()
        some_tool = None
        for plugin_info in index["plugins"].values():
            if plugin_info["tools"]:
                some_tool = next(iter(plugin_info["tools"]))
                break

        results = search_tools(some_tool)
        assert len(results) > 0
        assert results[0]["name"] == some_tool

    def test_usage_tiebreaker(self):
        """Tools with higher usage rank first when scores are equal."""
        tracker = get_usage_tracker()
        tracker.reset()

        # Find two tools from the same plugin to get equal category/plugin scores
        index = browse_tools()
        tools = []
        for plugin_name, plugin_info in index["plugins"].items():
            tool_names = list(plugin_info["tools"].keys())
            if len(tool_names) >= 2:
                tools = tool_names[:2]
                query_plugin = plugin_name
                break

        if len(tools) < 2:
            pytest.skip("Need a plugin with at least 2 tools for tiebreaker test")

        # Give second tool more usage
        for _ in range(10):
            tracker.record(tools[1])

        # Search by plugin name — both tools get equal plugin-match score
        results = search_tools(query_plugin)
        result_names = [r["name"] for r in results]

        # Among the two tools (same score from plugin match), the one with
        # higher usage should come first
        if tools[0] in result_names and tools[1] in result_names:
            assert result_names.index(tools[1]) < result_names.index(tools[0])


# ---------------------------------------------------------------------------
# Integration / smoke tests
# ---------------------------------------------------------------------------

class TestIntegrationSmoke:
    def test_browse_search_details_roundtrip(self):
        """Smoke test: browse -> search -> get details."""
        index = browse_tools()
        assert index["total_count"] > 0
        assert "popular" in index

        results = search_tools("html")
        assert len(results) > 0

        first_name = results[0]["name"]
        details = get_tool_details(first_name)
        assert len(details) == 1
        assert details[0]["name"] == first_name

    def test_popular_reflects_usage(self):
        tracker = get_usage_tracker()
        tracker.reset()

        tracker.record("strip")
        tracker.record("strip")
        tracker.record("strip")

        index = browse_tools()
        assert "strip" in index["popular"]
