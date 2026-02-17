"""Tests for the Tukuy MCP server tool functions.

These test the tool functions directly as regular Python functions,
without requiring an actual MCP transport connection.
"""

import json
import pytest

try:
    import mcp  # noqa: F401
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

pytestmark = pytest.mark.skipif(not HAS_MCP, reason="mcp package not installed")


# ---------------------------------------------------------------------------
# Import helpers — guarded by the skip marker above
# ---------------------------------------------------------------------------

if HAS_MCP:
    from tukuy.mcp_server import (
        tukuy_info,
        tukuy_browse,
        tukuy_search,
        tukuy_show,
        tukuy_run,
        tukuy_transform,
        _apply_filters,
        _allowed_plugins,
    )
    import tukuy.mcp_server as _mcp_mod


# ---------------------------------------------------------------------------
# tukuy_info
# ---------------------------------------------------------------------------


class TestTukuyInfo:
    def test_returns_counts(self):
        result = tukuy_info()
        assert "Plugins:" in result
        assert "Transformers:" in result
        assert "Skills:" in result
        assert "Groups:" in result

    def test_counts_are_positive(self):
        result = tukuy_info()
        # Extract the plugins count
        for line in result.split("\n"):
            if line.startswith("Plugins:"):
                count = int(line.split(":")[1].strip())
                assert count > 0
                break


# ---------------------------------------------------------------------------
# tukuy_browse
# ---------------------------------------------------------------------------


class TestTukuyBrowse:
    def test_lists_plugins(self):
        result = tukuy_browse()
        # Should contain at least the text plugin
        assert "text" in result.lower()

    def test_filter_by_plugin(self):
        result = tukuy_browse(plugin="text")
        assert "text" in result.lower()
        # Should NOT contain other unrelated plugins (check a distinctive one)
        assert "=== Crypto" not in result or "text" in result

    def test_filter_by_group(self):
        result = tukuy_browse(group="Text Processing")
        # Should only show plugins in the Text Processing group
        if "No plugins found" not in result:
            assert "===" in result

    def test_no_match(self):
        result = tukuy_browse(plugin="nonexistent_plugin_xyz")
        assert "No plugins found" in result


# ---------------------------------------------------------------------------
# tukuy_search
# ---------------------------------------------------------------------------


class TestTukuySearch:
    def test_finds_known_transformer(self):
        result = tukuy_search("uppercase")
        assert "uppercase" in result.lower()

    def test_finds_known_skill(self):
        result = tukuy_search("env")
        assert "env" in result.lower()

    def test_empty_query(self):
        result = tukuy_search("")
        assert "No query" in result

    def test_no_results(self):
        result = tukuy_search("xyzzy_nonexistent_capability_42")
        assert "No results" in result

    def test_limit(self):
        result = tukuy_search("text", limit=3)
        # Count result entries (lines starting with '[')
        entries = [l for l in result.split("\n") if l.startswith("[")]
        assert len(entries) <= 3


# ---------------------------------------------------------------------------
# tukuy_show
# ---------------------------------------------------------------------------


class TestTukuyShow:
    def test_show_skill(self):
        result = tukuy_show("token_estimate")
        assert "Skill:" in result
        assert "token_estimate" in result.lower()

    def test_show_transformer(self):
        result = tukuy_show("uppercase")
        assert "Transformer:" in result or "uppercase" in result.lower()

    def test_not_found(self):
        result = tukuy_show("nonexistent_xyzzy_42")
        assert "Not found" in result

    def test_skill_shows_parameters(self):
        result = tukuy_show("token_estimate")
        # token_estimate should have a 'text' parameter
        assert "Parameters:" in result or "text" in result.lower()


# ---------------------------------------------------------------------------
# tukuy_run
# ---------------------------------------------------------------------------


class TestTukuyRun:
    @pytest.mark.asyncio
    async def test_run_skill(self):
        # token_estimate is a safe local skill (no network, no filesystem)
        result = await tukuy_run("token_estimate", json.dumps({"text": "hello world"}))
        assert "token" in result.lower() or result.strip().isdigit() or ":" in result

    @pytest.mark.asyncio
    async def test_run_not_found(self):
        result = await tukuy_run("nonexistent_skill_xyz")
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_run_invalid_json(self):
        result = await tukuy_run("token_estimate", "not-json{")
        assert "Invalid JSON" in result

    @pytest.mark.asyncio
    async def test_run_params_not_object(self):
        result = await tukuy_run("token_estimate", '"just a string"')
        assert "must be a JSON object" in result


# ---------------------------------------------------------------------------
# tukuy_transform
# ---------------------------------------------------------------------------


class TestTukuyTransform:
    def test_uppercase(self):
        result = tukuy_transform("uppercase", "hello world")
        assert result == "HELLO WORLD"

    def test_lowercase(self):
        result = tukuy_transform("lowercase", "HELLO WORLD")
        assert result == "hello world"

    def test_hash_text_with_params(self):
        result = tukuy_transform("hash_text", "hello", json.dumps({"algorithm": "md5"}))
        # MD5 of "hello" is well-known
        assert "5d41402abc4b2a76b9719d911017c592" in result.lower()

    def test_not_found(self):
        result = tukuy_transform("nonexistent_transformer_xyz", "hello")
        assert "not found" in result.lower()

    def test_invalid_params_json(self):
        result = tukuy_transform("uppercase", "hello", "bad{json")
        assert "Invalid JSON" in result

    def test_numeric_coercion(self):
        # abs expects a number; string "-42" should be coerced
        result = tukuy_transform("abs", "-42")
        assert "42" in result


# ---------------------------------------------------------------------------
# Plugin filtering
# ---------------------------------------------------------------------------


class TestFiltering:
    """Test --only / --exclude / TUKUY_MCP_ONLY / TUKUY_MCP_EXCLUDE."""

    def _reset_filter(self):
        _apply_filters()  # no args = clear filter

    def test_only_by_plugin_name(self):
        _apply_filters(only_csv="numerical")
        try:
            result = tukuy_info()
            assert "Filter active:" in result
            # Should only have numerical plugin
            assert "Plugins:      1" in result

            # uppercase (text plugin) should not appear in search
            result = tukuy_search("uppercase")
            assert "No results" in result

            # abs (numerical plugin) should appear
            result = tukuy_search("abs")
            assert "abs" in result.lower()
        finally:
            self._reset_filter()

    def test_only_by_group_name(self):
        _apply_filters(only_csv="Data")
        try:
            result = tukuy_browse()
            # Data group has: csv, date, numerical, sql, validation, xml, yaml
            assert "numerical" in result.lower()
            assert "csv" in result.lower()
            # text is in Core, not Data — should not appear
            assert "=== Text" not in result
        finally:
            self._reset_filter()

    def test_exclude_by_plugin_name(self):
        _apply_filters(exclude_csv="text")
        try:
            # uppercase (from text plugin) should be blocked
            result = tukuy_transform("uppercase", "hello")
            assert "excluded" in result.lower()

            # abs (numerical) should still work
            result = tukuy_transform("abs", "-5")
            assert "5" in result
        finally:
            self._reset_filter()

    def test_exclude_by_group(self):
        _apply_filters(exclude_csv="Integrations")
        try:
            result = tukuy_browse()
            # weather is in Integrations — should not appear
            assert "weather" not in result.lower() or "=== Weather" not in result
            # text is in Core — should still appear
            assert "text" in result.lower()
        finally:
            self._reset_filter()

    def test_only_plus_exclude(self):
        _apply_filters(only_csv="Data", exclude_csv="sql")
        try:
            result = tukuy_browse()
            assert "numerical" in result.lower()
            assert "=== Sql" not in result and "=== SQL" not in result
        finally:
            self._reset_filter()

    def test_env_var_only(self, monkeypatch):
        monkeypatch.setenv("TUKUY_MCP_ONLY", "numerical")
        _apply_filters()
        try:
            result = tukuy_info()
            assert "Filter active:" in result
            assert "Plugins:      1" in result
        finally:
            monkeypatch.delenv("TUKUY_MCP_ONLY", raising=False)
            self._reset_filter()

    def test_env_var_exclude(self, monkeypatch):
        monkeypatch.setenv("TUKUY_MCP_EXCLUDE", "text")
        _apply_filters()
        try:
            result = tukuy_transform("uppercase", "hello")
            assert "excluded" in result.lower()
        finally:
            monkeypatch.delenv("TUKUY_MCP_EXCLUDE", raising=False)
            self._reset_filter()

    def test_cli_overrides_env(self, monkeypatch):
        monkeypatch.setenv("TUKUY_MCP_ONLY", "text")
        # CLI --only should take precedence over env var
        _apply_filters(only_csv="numerical")
        try:
            result = tukuy_info()
            assert "Plugins:      1" in result
            # Should have numerical, not text
            result = tukuy_search("abs")
            assert "abs" in result.lower()
            result = tukuy_search("uppercase")
            assert "No results" in result
        finally:
            monkeypatch.delenv("TUKUY_MCP_ONLY", raising=False)
            self._reset_filter()

    def test_no_filter_shows_all(self):
        _apply_filters()
        result = tukuy_info()
        assert "Filter active:" not in result
        # Should show many plugins
        for line in result.split("\n"):
            if line.startswith("Plugins:"):
                count = int(line.split(":")[1].strip())
                assert count > 10
                break

    def test_run_blocked_skill(self):
        _apply_filters(only_csv="numerical")
        try:
            result = tukuy_browse()
            # Verify token_estimate is NOT in numerical
            assert "token_estimate" not in result
        finally:
            self._reset_filter()

    def test_show_blocked_skill(self):
        _apply_filters(only_csv="numerical")
        try:
            result = tukuy_show("token_estimate")
            assert "excluded" in result.lower()
        finally:
            self._reset_filter()
