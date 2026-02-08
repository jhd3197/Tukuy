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
