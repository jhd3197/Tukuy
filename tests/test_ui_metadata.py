"""Tests for UI metadata, ConfigParam, RiskLevel, PluginManifest, and availability engine."""

import pytest

from tukuy.skill import (
    ConfigParam,
    ConfigScope,
    RiskLevel,
    Skill,
    SkillDescriptor,
    skill,
)
from tukuy.context import SkillContext
from tukuy.manifest import PluginManifest, PluginRequirements
from tukuy.availability import (
    AvailabilityReason,
    PluginDiscoveryResult,
    SkillAvailability,
    discover_plugins,
    get_available_skills,
)
from tukuy.safety import SafetyPolicy, SecurityContext
from tukuy.plugins.base import TransformerPlugin, PluginSource


# ── helpers ──────────────────────────────────────────────────────────────────


class _DummyPlugin(TransformerPlugin):
    def __init__(self, name="dummy", skills_dict=None, manifest_override=None):
        super().__init__(name, source=PluginSource.TUKUY)
        self._skills_dict = skills_dict or {}
        self._manifest_override = manifest_override

    @property
    def transformers(self):
        return {}

    @property
    def skills(self):
        return self._skills_dict

    @property
    def manifest(self):
        if self._manifest_override:
            return self._manifest_override
        return super().manifest


@skill(name="read_file", requires_filesystem=True, idempotent=True)
def _read_file(path: str) -> str:
    return "content"


@skill(name="write_file", requires_filesystem=True, side_effects=True)
def _write_file(path: str, content: str) -> dict:
    return {"ok": True}


@skill(name="web_fetch", requires_network=True, required_imports=["httpx"])
def _web_fetch(url: str) -> str:
    return "<html>"


@skill(name="simple_calc", idempotent=True)
def _simple_calc(x: int) -> int:
    return x + 1


@skill(
    name="python_execute",
    side_effects=True,
    requires_filesystem=True,
    config_params=[
        ConfigParam(
            name="timeout_seconds",
            display_name="Timeout",
            description="Maximum execution time.",
            type="number",
            default=30,
            min=1,
            max=300,
            unit="seconds",
        ),
        ConfigParam(
            name="max_output_length",
            display_name="Output Limit",
            type="number",
            default=10000,
            min=100,
            max=100000,
            unit="characters",
        ),
    ],
)
def _python_execute(code: str) -> dict:
    return {"result": "ok"}


# ── TestRiskLevel ────────────────────────────────────────────────────────────


class TestRiskLevel:
    def test_enum_values(self):
        assert RiskLevel.AUTO == "auto"
        assert RiskLevel.SAFE == "safe"
        assert RiskLevel.MODERATE == "moderate"
        assert RiskLevel.DANGEROUS == "dangerous"
        assert RiskLevel.CRITICAL == "critical"

    def test_auto_derives_safe(self):
        desc = SkillDescriptor(name="test", description="", idempotent=True, side_effects=False)
        assert desc.resolved_risk_level == RiskLevel.SAFE

    def test_auto_derives_moderate(self):
        desc = SkillDescriptor(name="test", description="", side_effects=True)
        assert desc.resolved_risk_level == RiskLevel.MODERATE

    def test_auto_derives_dangerous_filesystem(self):
        desc = SkillDescriptor(name="test", description="", side_effects=True, requires_filesystem=True)
        assert desc.resolved_risk_level == RiskLevel.DANGEROUS

    def test_auto_derives_dangerous_network(self):
        desc = SkillDescriptor(name="test", description="", side_effects=True, requires_network=True)
        assert desc.resolved_risk_level == RiskLevel.DANGEROUS

    def test_explicit_override(self):
        desc = SkillDescriptor(
            name="git_commit", description="",
            side_effects=True, requires_filesystem=True,
            risk_level=RiskLevel.MODERATE,
        )
        assert desc.resolved_risk_level == RiskLevel.MODERATE


# ── TestConfigParam ──────────────────────────────────────────────────────────


class TestConfigParam:
    def test_basic_creation(self):
        cp = ConfigParam(name="timeout", type="number", default=30)
        assert cp.name == "timeout"
        assert cp.type == "number"
        assert cp.default == 30
        assert cp.scope == ConfigScope.PER_BOT

    def test_to_dict_minimal(self):
        cp = ConfigParam(name="flag", type="boolean")
        d = cp.to_dict()
        assert d["name"] == "flag"
        assert d["type"] == "boolean"
        assert d["scope"] == "per_bot"
        assert "displayName" not in d
        assert "min" not in d

    def test_to_dict_full(self):
        cp = ConfigParam(
            name="timeout_seconds",
            display_name="Timeout",
            description="Max time",
            type="number",
            default=30,
            min=1,
            max=300,
            step=1,
            unit="seconds",
            scope=ConfigScope.PER_INVOCATION,
        )
        d = cp.to_dict()
        assert d["displayName"] == "Timeout"
        assert d["description"] == "Max time"
        assert d["default"] == 30
        assert d["min"] == 1
        assert d["max"] == 300
        assert d["step"] == 1
        assert d["unit"] == "seconds"
        assert d["scope"] == "per_call"

    def test_select_type(self):
        cp = ConfigParam(name="mode", type="select", options=["fast", "slow"])
        d = cp.to_dict()
        assert d["options"] == ["fast", "slow"]

    def test_string_array_type(self):
        cp = ConfigParam(
            name="allowed_commands",
            type="string[]",
            default=["ls", "git"],
            min_items=0,
            max_items=50,
            item_placeholder="e.g. ls, git",
        )
        d = cp.to_dict()
        assert d["type"] == "string[]"
        assert d["default"] == ["ls", "git"]
        assert d["minItems"] == 0
        assert d["maxItems"] == 50
        assert d["itemPlaceholder"] == "e.g. ls, git"

    def test_number_array_type(self):
        cp = ConfigParam(
            name="thresholds",
            type="number[]",
            default=[0.5, 0.8],
            min_items=1,
            item_placeholder="0.0-1.0",
        )
        d = cp.to_dict()
        assert d["type"] == "number[]"
        assert d["default"] == [0.5, 0.8]
        assert d["minItems"] == 1
        assert d["itemPlaceholder"] == "0.0-1.0"

    def test_secret_type(self):
        cp = ConfigParam(
            name="api_key",
            type="secret",
            placeholder="sk-...",
        )
        d = cp.to_dict()
        assert d["type"] == "secret"
        assert d["placeholder"] == "sk-..."

    def test_text_type(self):
        cp = ConfigParam(
            name="system_prompt",
            type="text",
            placeholder="Enter prompt...",
            rows=5,
        )
        d = cp.to_dict()
        assert d["type"] == "text"
        assert d["placeholder"] == "Enter prompt..."
        assert d["rows"] == 5

    def test_path_type(self):
        cp = ConfigParam(
            name="working_dir",
            type="path",
            path_type="directory",
            placeholder="/path/to/project",
        )
        d = cp.to_dict()
        assert d["type"] == "path"
        assert d["pathType"] == "directory"
        assert d["placeholder"] == "/path/to/project"

    def test_map_type(self):
        cp = ConfigParam(
            name="headers",
            type="map",
            default={},
            key_placeholder="Header-Name",
            value_placeholder="value",
            max_items=20,
        )
        d = cp.to_dict()
        assert d["type"] == "map"
        assert d["keyPlaceholder"] == "Header-Name"
        assert d["valuePlaceholder"] == "value"
        assert d["maxItems"] == 20

    def test_multiselect_type(self):
        cp = ConfigParam(
            name="methods",
            type="multiselect",
            options=["GET", "POST", "PUT", "DELETE"],
            default=["GET", "POST"],
        )
        d = cp.to_dict()
        assert d["type"] == "multiselect"
        assert d["options"] == ["GET", "POST", "PUT", "DELETE"]
        assert d["default"] == ["GET", "POST"]

    def test_url_type(self):
        cp = ConfigParam(
            name="base_url",
            type="url",
            placeholder="https://api.example.com",
        )
        d = cp.to_dict()
        assert d["type"] == "url"
        assert d["placeholder"] == "https://api.example.com"

    def test_code_type(self):
        cp = ConfigParam(
            name="template",
            type="code",
            language="json",
            placeholder='{"key": "value"}',
            rows=8,
        )
        d = cp.to_dict()
        assert d["type"] == "code"
        assert d["language"] == "json"
        assert d["placeholder"] == '{"key": "value"}'
        assert d["rows"] == 8

    def test_code_type_sql(self):
        cp = ConfigParam(
            name="query",
            type="code",
            language="sql",
            rows=4,
        )
        d = cp.to_dict()
        assert d["type"] == "code"
        assert d["language"] == "sql"
        assert d["rows"] == 4

    def test_to_dict_omits_none_new_fields(self):
        cp = ConfigParam(name="simple", type="string")
        d = cp.to_dict()
        assert "minItems" not in d
        assert "maxItems" not in d
        assert "placeholder" not in d
        assert "rows" not in d
        assert "pathType" not in d
        assert "keyPlaceholder" not in d
        assert "valuePlaceholder" not in d
        assert "itemPlaceholder" not in d
        assert "language" not in d

    def test_all_new_types_roundtrip(self):
        """Serialize all new types together and verify round-trip."""
        params = [
            ConfigParam(name="cmds", type="string[]", default=["a"], item_placeholder="cmd"),
            ConfigParam(name="nums", type="number[]", default=[1, 2], min_items=1),
            ConfigParam(name="key", type="secret", placeholder="sk-..."),
            ConfigParam(name="prompt", type="text", rows=10, placeholder="..."),
            ConfigParam(name="dir", type="path", path_type="directory"),
            ConfigParam(name="hdrs", type="map", key_placeholder="k", value_placeholder="v"),
            ConfigParam(name="methods", type="multiselect", options=["A", "B"], default=["A"]),
            ConfigParam(name="endpoint", type="url", placeholder="https://..."),
            ConfigParam(name="tpl", type="code", language="json", rows=5),
        ]
        dicts = [p.to_dict() for p in params]
        assert len(dicts) == 9
        types = [d["type"] for d in dicts]
        assert types == [
            "string[]", "number[]", "secret", "text", "path", "map",
            "multiselect", "url", "code",
        ]
        # Verify no None values leaked
        for d in dicts:
            assert None not in d.values()


# ── TestSkillDescriptorUIFields ──────────────────────────────────────────────


class TestSkillDescriptorUIFields:
    def test_defaults(self):
        desc = SkillDescriptor(name="my_skill", description="Does stuff")
        assert desc.display_name is None
        assert desc.icon is None
        assert desc.risk_level == RiskLevel.AUTO
        assert desc.group is None
        assert desc.hidden is False
        assert desc.deprecated is None
        assert desc.config_params == []

    def test_resolved_display_name_auto(self):
        desc = SkillDescriptor(name="file_read", description="")
        assert desc.resolved_display_name == "File Read"

    def test_resolved_display_name_explicit(self):
        desc = SkillDescriptor(name="file_read", description="", display_name="Read a File")
        assert desc.resolved_display_name == "Read a File"

    def test_to_dict_includes_ui_fields(self):
        desc = SkillDescriptor(
            name="file_read",
            description="Read a file",
            icon="file-text",
            group="File Operations",
            risk_level=RiskLevel.SAFE,
        )
        d = desc.to_dict()
        assert d["display_name"] == "File Read"
        assert d["icon"] == "file-text"
        assert d["group"] == "File Operations"
        assert d["risk_level"] == "safe"

    def test_to_dict_omits_none_ui_fields(self):
        desc = SkillDescriptor(name="test", description="")
        d = desc.to_dict()
        assert "icon" not in d
        assert "group" not in d
        assert "hidden" not in d
        assert "deprecated" not in d

    def test_to_dict_includes_config_params(self):
        desc = _python_execute.__skill__.descriptor
        d = desc.to_dict()
        assert "config_params" in d
        assert len(d["config_params"]) == 2
        assert d["config_params"][0]["name"] == "timeout_seconds"

    def test_to_dict_omits_empty_config_params(self):
        desc = SkillDescriptor(name="test", description="")
        d = desc.to_dict()
        assert "config_params" not in d


# ── TestSkillDecoratorNewParams ──────────────────────────────────────────────


class TestSkillDecoratorNewParams:
    def test_ui_metadata_via_decorator(self):
        @skill(
            name="test_skill",
            display_name="Test Skill",
            icon="wrench",
            risk_level=RiskLevel.MODERATE,
            group="Testing",
            hidden=True,
            deprecated="Use test_skill_v2 instead",
        )
        def test_fn(x: int) -> int:
            return x

        desc = test_fn.__skill__.descriptor
        assert desc.display_name == "Test Skill"
        assert desc.icon == "wrench"
        assert desc.risk_level == RiskLevel.MODERATE
        assert desc.group == "Testing"
        assert desc.hidden is True
        assert desc.deprecated == "Use test_skill_v2 instead"

    def test_config_params_via_decorator(self):
        desc = _python_execute.__skill__.descriptor
        assert len(desc.config_params) == 2
        assert desc.config_params[0].name == "timeout_seconds"
        assert desc.config_params[1].name == "max_output_length"

    def test_defaults_preserved(self):
        @skill
        def bare_fn(x: int) -> int:
            return x

        desc = bare_fn.__skill__.descriptor
        assert desc.risk_level == RiskLevel.AUTO
        assert desc.config_params == []
        assert desc.hidden is False


# ── TestSkillContextConfig ───────────────────────────────────────────────────


class TestSkillContextConfig:
    def test_config_empty_by_default(self):
        ctx = SkillContext()
        assert ctx.config == {}

    def test_config_set_and_get(self):
        ctx = SkillContext(config={"timeout_seconds": 60})
        assert ctx.config["timeout_seconds"] == 60

    def test_config_inherited_by_child_scope(self):
        ctx = SkillContext(config={"timeout": 30})
        child = ctx.scope("branch_0")
        assert child.config["timeout"] == 30
        # Mutation in child is visible in parent (shared dict)
        child.config["timeout"] = 60
        assert ctx.config["timeout"] == 60

    def test_config_independent_of_data(self):
        ctx = SkillContext(data={"key": "val"}, config={"timeout": 30})
        assert ctx.get("key") == "val"
        assert ctx.config["timeout"] == 30
        assert ctx.get("timeout") is None  # config is separate from data


# ── TestPluginManifest ───────────────────────────────────────────────────────


class TestPluginManifest:
    def test_auto_display_name(self):
        m = PluginManifest(name="file_ops")
        assert m.display_name == "File Ops"

    def test_explicit_display_name(self):
        m = PluginManifest(name="file_ops", display_name="File Operations")
        assert m.display_name == "File Operations"

    def test_to_dict_minimal(self):
        m = PluginManifest(name="test")
        d = m.to_dict()
        assert d["name"] == "test"
        assert d["displayName"] == "Test"
        assert "icon" not in d
        assert "requires" not in d

    def test_to_dict_full(self):
        m = PluginManifest(
            name="web",
            display_name="Web",
            description="Fetch web pages",
            icon="globe",
            color="#3b82f6",
            group="Integrations",
            requires=PluginRequirements(network=True, imports=["httpx"]),
        )
        d = m.to_dict()
        assert d["icon"] == "globe"
        assert d["color"] == "#3b82f6"
        assert d["group"] == "Integrations"
        assert d["requires"]["network"] is True
        assert d["requires"]["imports"] == ["httpx"]

    def test_deprecated_in_dict(self):
        m = PluginManifest(name="old", deprecated="Use new_plugin instead")
        d = m.to_dict()
        assert d["deprecated"] == "Use new_plugin instead"


class TestPluginRequirements:
    def test_defaults(self):
        r = PluginRequirements()
        assert r.filesystem is False
        assert r.network is False
        assert r.imports == []

    def test_to_dict_empty_when_defaults(self):
        r = PluginRequirements()
        assert r.to_dict() == {}

    def test_to_dict_with_values(self):
        r = PluginRequirements(filesystem=True, imports=["PIL"])
        d = r.to_dict()
        assert d["filesystem"] is True
        assert d["imports"] == ["PIL"]
        assert "network" not in d


# ── TestTransformerPluginManifest ────────────────────────────────────────────


class TestTransformerPluginManifest:
    def test_default_manifest(self):
        plugin = _DummyPlugin(name="my_plugin")
        m = plugin.manifest
        assert m.name == "my_plugin"
        assert m.display_name == "My Plugin"

    def test_overridden_manifest(self):
        custom = PluginManifest(
            name="file_ops",
            display_name="File Operations",
            icon="folder",
            requires=PluginRequirements(filesystem=True),
        )
        plugin = _DummyPlugin(name="file_ops", manifest_override=custom)
        m = plugin.manifest
        assert m.display_name == "File Operations"
        assert m.icon == "folder"
        assert m.requires.filesystem is True


# ── TestGetAvailableSkills ───────────────────────────────────────────────────


class TestGetAvailableSkills:
    def _make_plugin(self, *skill_fns):
        skills_dict = {fn.__skill__.descriptor.name: fn.__skill__ for fn in skill_fns}
        return _DummyPlugin(name="test", skills_dict=skills_dict)

    def test_all_available_permissive(self):
        plugin = self._make_plugin(_read_file, _web_fetch, _simple_calc)
        results = get_available_skills([plugin])
        assert all(r.available for r in results)

    def test_network_blocked(self):
        plugin = self._make_plugin(_read_file, _web_fetch, _simple_calc)
        policy = SafetyPolicy(allow_network=False)
        results = get_available_skills([plugin], policy=policy)

        by_name = {r.skill.descriptor.name: r for r in results}
        assert by_name["read_file"].available is True
        assert by_name["web_fetch"].available is False
        assert by_name["web_fetch"].reason_code == AvailabilityReason.POLICY_BLOCKED
        assert by_name["simple_calc"].available is True

    def test_filesystem_blocked(self):
        plugin = self._make_plugin(_read_file, _write_file, _simple_calc)
        policy = SafetyPolicy(allow_filesystem=False)
        results = get_available_skills([plugin], policy=policy)

        by_name = {r.skill.descriptor.name: r for r in results}
        assert by_name["read_file"].available is False
        assert by_name["write_file"].available is False
        assert by_name["simple_calc"].available is True

    def test_security_context_restrictions(self):
        plugin = self._make_plugin(_read_file, _web_fetch)
        sec_ctx = SecurityContext(
            allowed_read_paths=["/workspace"],
            allowed_write_paths=["/workspace"],
            allowed_hosts=["api.github.com"],
        )
        results = get_available_skills([plugin], security_context=sec_ctx)

        by_name = {r.skill.descriptor.name: r for r in results}
        assert by_name["read_file"].available is True
        assert len(by_name["read_file"].restrictions) >= 1
        assert "Read access limited to: /workspace" in by_name["read_file"].restrictions

        assert by_name["web_fetch"].available is True
        assert "Network limited to: api.github.com" in by_name["web_fetch"].restrictions

    def test_to_dict(self):
        plugin = self._make_plugin(_simple_calc)
        results = get_available_skills([plugin])
        d = results[0].to_dict()
        assert d["name"] == "simple_calc"
        assert d["available"] is True
        assert d["reasonCode"] == "allowed"


# ── TestDiscoverPlugins ──────────────────────────────────────────────────────


class TestDiscoverPlugins:
    def test_basic_discovery(self):
        plugin = _DummyPlugin(name="test_plugin")
        results = discover_plugins([plugin])
        assert len(results) == 1
        assert results[0].available is True
        assert results[0].manifest.name == "test_plugin"

    def test_policy_blocks_filesystem_plugin(self):
        manifest = PluginManifest(
            name="file_ops",
            requires=PluginRequirements(filesystem=True),
        )
        plugin = _DummyPlugin(name="file_ops", manifest_override=manifest)
        policy = SafetyPolicy(allow_filesystem=False)

        results = discover_plugins([plugin], policy=policy)
        assert results[0].available is False
        assert results[0].reason_code == AvailabilityReason.POLICY_BLOCKED

    def test_policy_blocks_network_plugin(self):
        manifest = PluginManifest(
            name="web",
            requires=PluginRequirements(network=True),
        )
        plugin = _DummyPlugin(name="web", manifest_override=manifest)
        policy = SafetyPolicy(allow_network=False)

        results = discover_plugins([plugin], policy=policy)
        assert results[0].available is False

    def test_missing_import(self):
        manifest = PluginManifest(
            name="web",
            requires=PluginRequirements(imports=["nonexistent_package_xyz"]),
        )
        plugin = _DummyPlugin(name="web", manifest_override=manifest)

        results = discover_plugins([plugin])
        assert results[0].available is False
        assert results[0].reason_code == AvailabilityReason.MISSING_DEPENDENCY

    def test_deprecated_plugin(self):
        manifest = PluginManifest(
            name="old_plugin",
            deprecated="Use new_plugin instead",
        )
        plugin = _DummyPlugin(name="old_plugin", manifest_override=manifest)

        results = discover_plugins([plugin])
        assert results[0].available is True
        assert results[0].reason_code == AvailabilityReason.DEPRECATED

    def test_to_dict(self):
        manifest = PluginManifest(
            name="test",
            display_name="Test Plugin",
            icon="wrench",
        )
        plugin = _DummyPlugin(name="test", manifest_override=manifest)
        results = discover_plugins([plugin])
        d = results[0].to_dict()
        assert d["name"] == "test"
        assert d["displayName"] == "Test Plugin"
        assert d["available"] is True
        assert d["skillCount"] == 0

    def test_skill_count(self):
        plugin = _DummyPlugin(
            name="test",
            skills_dict={"a": _read_file.__skill__, "b": _simple_calc.__skill__},
        )
        results = discover_plugins([plugin])
        assert results[0].skill_count == 2

    def test_skip_requirements_check(self):
        manifest = PluginManifest(
            name="web",
            requires=PluginRequirements(imports=["nonexistent_xyz"]),
        )
        plugin = _DummyPlugin(name="web", manifest_override=manifest)

        results = discover_plugins([plugin], check_requirements=False)
        assert results[0].available is True


# ── TestPluginConfigParams ───────────────────────────────────────────────────


class TestPluginConfigParams:
    """Verify that each modified plugin declares the expected config_params."""

    @staticmethod
    def _param_names(skill_fn):
        return [p.name for p in skill_fn.__skill__.descriptor.config_params]

    def test_shell_execute(self):
        from tukuy.plugins.shell import shell_execute
        names = self._param_names(shell_execute)
        assert "timeout" in names
        assert "default_cwd" in names
        assert "allowed_commands" in names

    def test_file_read(self):
        from tukuy.plugins.file_ops import file_read
        names = self._param_names(file_read)
        assert "max_file_size" in names
        assert "encoding" in names

    def test_file_write(self):
        from tukuy.plugins.file_ops import file_write
        names = self._param_names(file_write)
        assert "encoding" in names
        assert "allowed_extensions" in names

    def test_file_edit(self):
        from tukuy.plugins.file_ops import file_edit
        names = self._param_names(file_edit)
        assert "max_file_size" in names
        assert "allowed_extensions" in names

    def test_git_commit(self):
        from tukuy.plugins.git import git_commit
        names = self._param_names(git_commit)
        assert "protected_branches" in names

    def test_env_read(self):
        from tukuy.plugins.env import env_read
        names = self._param_names(env_read)
        assert "env_file_path" in names
        assert "auto_mask_patterns" in names

    def test_env_write(self):
        from tukuy.plugins.env import env_write
        names = self._param_names(env_write)
        assert "env_file_path" in names

    def test_web_fetch(self):
        from tukuy.plugins.web import web_fetch
        names = self._param_names(web_fetch)
        assert "timeout" in names
        assert "user_agent" in names
        assert "proxy_url" in names

    def test_web_search(self):
        from tukuy.plugins.web import web_search
        names = self._param_names(web_search)
        assert "max_results" in names
        assert "timeout" in names
        assert "blocked_domains" in names

    def test_http_request(self):
        from tukuy.plugins.http import http_request
        names = self._param_names(http_request)
        assert "base_url" in names
        assert "timeout" in names
        assert "allowed_methods" in names
        assert "default_headers" in names
        assert "auth_token" in names
        assert "request_body_template" in names
        assert "blocked_hosts" in names

    def test_token_estimate(self):
        from tukuy.plugins.llm import token_estimate
        names = self._param_names(token_estimate)
        assert "chars_per_token" in names

    def test_sqlite_query(self):
        from tukuy.plugins.sql import sqlite_query
        names = self._param_names(sqlite_query)
        assert "max_rows" in names
        assert "timeout" in names
        assert "db_path" in names
        assert "query_template" in names

    def test_sqlite_execute(self):
        from tukuy.plugins.sql import sqlite_execute
        names = self._param_names(sqlite_execute)
        assert "timeout" in names
        assert "db_path" in names
        assert "allowed_operations" in names

    def test_pdf_read(self):
        from tukuy.plugins.pdf import pdf_read
        names = self._param_names(pdf_read)
        assert "max_file_size" in names

    def test_xlsx_read(self):
        from tukuy.plugins.xlsx import xlsx_read
        names = self._param_names(xlsx_read)
        assert "max_rows_per_sheet" in names

    def test_image_resize(self):
        from tukuy.plugins.image import image_resize
        names = self._param_names(image_resize)
        assert "max_file_size" in names
        assert "quality" in names

    def test_docx_write(self):
        from tukuy.plugins.docx import docx_write
        names = self._param_names(docx_write)
        assert "default_author" in names

    def test_zip_create(self):
        from tukuy.plugins.compression import zip_create
        names = self._param_names(zip_create)
        assert "compression_level" in names

    def test_new_types_in_plugins(self):
        """Spot-check that new types (path, string[], map, secret, url, multiselect, code) are used in real plugins."""
        from tukuy.plugins.shell import shell_execute
        from tukuy.plugins.http import http_request
        from tukuy.plugins.sql import sqlite_query, sqlite_execute
        from tukuy.plugins.web import web_fetch

        shell_types = {p.type for p in shell_execute.__skill__.descriptor.config_params}
        assert "path" in shell_types
        assert "string[]" in shell_types

        http_types = {p.type for p in http_request.__skill__.descriptor.config_params}
        assert "map" in http_types
        assert "secret" in http_types
        assert "string[]" in http_types
        assert "url" in http_types
        assert "multiselect" in http_types
        assert "code" in http_types

        sql_query_types = {p.type for p in sqlite_query.__skill__.descriptor.config_params}
        assert "code" in sql_query_types

        sql_exec_types = {p.type for p in sqlite_execute.__skill__.descriptor.config_params}
        assert "multiselect" in sql_exec_types

        web_types = {p.type for p in web_fetch.__skill__.descriptor.config_params}
        assert "url" in web_types

    def test_config_params_serialize_in_descriptor(self):
        """Verify config_params serialize correctly through SkillDescriptor.to_dict()."""
        from tukuy.plugins.http import http_request

        d = http_request.__skill__.descriptor.to_dict()
        assert "config_params" in d
        param_dicts = d["config_params"]
        assert len(param_dicts) == 7

        # Find the map-type param
        headers_param = next(p for p in param_dicts if p["name"] == "default_headers")
        assert headers_param["type"] == "map"
        assert headers_param["keyPlaceholder"] == "Header-Name"
        assert headers_param["valuePlaceholder"] == "value"

        # Find the secret-type param
        auth_param = next(p for p in param_dicts if p["name"] == "auth_token")
        assert auth_param["type"] == "secret"
        assert auth_param["placeholder"] == "sk-..."

        # Find the url-type param
        url_param = next(p for p in param_dicts if p["name"] == "base_url")
        assert url_param["type"] == "url"
        assert "placeholder" in url_param

        # Find the multiselect-type param
        methods_param = next(p for p in param_dicts if p["name"] == "allowed_methods")
        assert methods_param["type"] == "multiselect"
        assert "GET" in methods_param["options"]
        assert "POST" in methods_param["options"]

        # Find the code-type param
        body_param = next(p for p in param_dicts if p["name"] == "request_body_template")
        assert body_param["type"] == "code"
        assert body_param["language"] == "json"
