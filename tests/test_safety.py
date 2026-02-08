"""Tests for tukuy.safety — SafetyManifest, SafetyPolicy, enforcement, sandbox integration."""

import asyncio
import pytest

from tukuy.safety import (
    SafetyError,
    SafetyManifest,
    SafetyPolicy,
    SafetyViolation,
    get_policy,
    reset_policy,
    set_policy,
)
from tukuy.skill import Skill, SkillDescriptor, SkillResult, skill


# ── helpers ──────────────────────────────────────────────────────────────────


def _echo(x: str) -> str:
    return x


def _make_descriptor(**overrides):
    defaults = dict(
        name="test_skill",
        description="A test skill",
        required_imports=[],
        requires_network=False,
        requires_filesystem=False,
    )
    defaults.update(overrides)
    return SkillDescriptor(**defaults)


def _make_skill(fn=None, **descriptor_overrides):
    fn = fn or _echo
    descriptor = _make_descriptor(**descriptor_overrides)
    return Skill(descriptor=descriptor, fn=fn)


# ── SafetyViolation ─────────────────────────────────────────────────────────


class TestSafetyViolation:
    def test_str_with_skill_name(self):
        v = SafetyViolation(kind="network", message="denied", skill_name="scraper")
        assert str(v) == "[scraper] denied"

    def test_str_without_skill_name(self):
        v = SafetyViolation(kind="network", message="denied")
        assert str(v) == "denied"


# ── SafetyError ──────────────────────────────────────────────────────────────


class TestSafetyError:
    def test_message_contains_violations(self):
        violations = [
            SafetyViolation(kind="network", message="no network", skill_name="s"),
            SafetyViolation(kind="import", message="bad import", skill_name="s"),
        ]
        err = SafetyError(violations)
        assert "no network" in str(err)
        assert "bad import" in str(err)
        assert len(err.violations) == 2


# ── SafetyManifest ───────────────────────────────────────────────────────────


class TestSafetyManifest:
    def test_from_descriptor(self):
        desc = _make_descriptor(
            name="web_scraper",
            requires_network=True,
            required_imports=["aiohttp", "bs4"],
        )
        manifest = SafetyManifest.from_descriptor(desc)
        assert manifest.skill_name == "web_scraper"
        assert manifest.requires_network is True
        assert manifest.requires_filesystem is False
        assert manifest.required_imports == ["aiohttp", "bs4"]

    def test_from_skill(self):
        sk = _make_skill(requires_network=True)
        manifest = SafetyManifest.from_skill(sk)
        assert manifest.requires_network is True
        assert manifest.skill_name == "test_skill"

    def test_to_dict(self):
        manifest = SafetyManifest(
            required_imports=["json"],
            requires_network=True,
            requires_filesystem=False,
            skill_name="parser",
        )
        d = manifest.to_dict()
        assert d["required_imports"] == ["json"]
        assert d["requires_network"] is True
        assert d["skill_name"] == "parser"


# ── SafetyPolicy ─────────────────────────────────────────────────────────────


class TestSafetyPolicy:
    # -- Convenience constructors --

    def test_restrictive(self):
        p = SafetyPolicy.restrictive()
        assert p.allowed_imports == set()
        assert p.allow_network is False
        assert p.allow_filesystem is False

    def test_permissive(self):
        p = SafetyPolicy.permissive()
        assert p.allowed_imports is None
        assert p.allow_network is True
        assert p.allow_filesystem is True

    def test_network_only(self):
        p = SafetyPolicy.network_only()
        assert p.allow_network is True
        assert p.allow_filesystem is False

    def test_filesystem_only(self):
        p = SafetyPolicy.filesystem_only()
        assert p.allow_network is False
        assert p.allow_filesystem is True

    # -- Network validation --

    def test_network_denied(self):
        policy = SafetyPolicy(allow_network=False)
        desc = _make_descriptor(requires_network=True)
        violations = policy.validate(desc)
        assert len(violations) == 1
        assert violations[0].kind == "network"

    def test_network_allowed(self):
        policy = SafetyPolicy(allow_network=True)
        desc = _make_descriptor(requires_network=True)
        assert policy.validate(desc) == []

    def test_network_not_required(self):
        policy = SafetyPolicy(allow_network=False)
        desc = _make_descriptor(requires_network=False)
        assert policy.validate(desc) == []

    # -- Filesystem validation --

    def test_filesystem_denied(self):
        policy = SafetyPolicy(allow_filesystem=False)
        desc = _make_descriptor(requires_filesystem=True)
        violations = policy.validate(desc)
        assert len(violations) == 1
        assert violations[0].kind == "filesystem"

    def test_filesystem_allowed(self):
        policy = SafetyPolicy(allow_filesystem=True)
        desc = _make_descriptor(requires_filesystem=True)
        assert policy.validate(desc) == []

    # -- Import validation: allowed_imports --

    def test_import_allowed(self):
        policy = SafetyPolicy(allowed_imports={"json", "re"})
        desc = _make_descriptor(required_imports=["json"])
        assert policy.validate(desc) == []

    def test_import_not_in_allowed(self):
        policy = SafetyPolicy(allowed_imports={"json", "re"})
        desc = _make_descriptor(required_imports=["os"])
        violations = policy.validate(desc)
        assert len(violations) == 1
        assert violations[0].kind == "import"
        assert "'os'" in violations[0].message

    def test_import_unrestricted_when_none(self):
        policy = SafetyPolicy(allowed_imports=None)
        desc = _make_descriptor(required_imports=["os", "subprocess"])
        assert policy.validate(desc) == []

    # -- Import validation: blocked_imports --

    def test_import_blocked(self):
        policy = SafetyPolicy(blocked_imports={"os", "subprocess"})
        desc = _make_descriptor(required_imports=["os"])
        violations = policy.validate(desc)
        assert len(violations) == 1
        assert violations[0].kind == "import"
        assert "'os'" in violations[0].message

    def test_blocked_takes_precedence_over_allowed(self):
        policy = SafetyPolicy(
            allowed_imports={"os", "json"},
            blocked_imports={"os"},
        )
        desc = _make_descriptor(required_imports=["os"])
        violations = policy.validate(desc)
        assert len(violations) == 1
        assert violations[0].kind == "import"

    # -- Multiple violations --

    def test_multiple_violations(self):
        policy = SafetyPolicy.restrictive()
        desc = _make_descriptor(
            requires_network=True,
            requires_filesystem=True,
            required_imports=["aiohttp"],
        )
        violations = policy.validate(desc)
        assert len(violations) == 3
        kinds = {v.kind for v in violations}
        assert kinds == {"network", "filesystem", "import"}

    # -- No violations --

    def test_compliant_skill(self):
        policy = SafetyPolicy(
            allowed_imports={"json", "re"},
            allow_network=True,
            allow_filesystem=False,
        )
        desc = _make_descriptor(
            requires_network=True,
            requires_filesystem=False,
            required_imports=["json"],
        )
        assert policy.validate(desc) == []

    # -- enforce() --

    def test_enforce_raises_on_violation(self):
        policy = SafetyPolicy(allow_network=False)
        desc = _make_descriptor(requires_network=True)
        with pytest.raises(SafetyError) as exc_info:
            policy.enforce(desc)
        assert len(exc_info.value.violations) == 1

    def test_enforce_passes_when_compliant(self):
        policy = SafetyPolicy.permissive()
        desc = _make_descriptor(requires_network=True)
        policy.enforce(desc)  # should not raise

    # -- Validate with Skill instance --

    def test_validate_skill_instance(self):
        policy = SafetyPolicy(allow_network=False)
        sk = _make_skill(requires_network=True)
        violations = policy.validate(sk)
        assert len(violations) == 1

    # -- Validate with SafetyManifest directly --

    def test_validate_manifest_directly(self):
        policy = SafetyPolicy(allow_filesystem=False)
        manifest = SafetyManifest(
            requires_filesystem=True,
            skill_name="writer",
        )
        violations = policy.validate(manifest)
        assert len(violations) == 1
        assert violations[0].skill_name == "writer"

    # -- to_dict / to_sandbox_config / from_sandbox_config --

    def test_to_dict(self):
        policy = SafetyPolicy(
            allowed_imports={"json", "re"},
            blocked_imports={"os"},
            allow_network=True,
            allow_filesystem=False,
        )
        d = policy.to_dict()
        assert d["allowed_imports"] == ["json", "re"]
        assert d["blocked_imports"] == ["os"]
        assert d["allow_network"] is True
        assert d["allow_filesystem"] is False

    def test_to_sandbox_config(self):
        policy = SafetyPolicy(
            allowed_imports={"json"},
            blocked_imports={"os"},
            allow_network=False,
            allow_filesystem=True,
        )
        config = policy.to_sandbox_config()
        assert config["allowed_imports"] == ["json"]
        assert config["blocked_imports"] == ["os"]
        assert config["network"] is False
        assert config["filesystem"] is True

    def test_to_sandbox_config_unrestricted(self):
        policy = SafetyPolicy.permissive()
        config = policy.to_sandbox_config()
        assert config["allowed_imports"] is None
        assert config["blocked_imports"] == []

    def test_from_sandbox_config(self):
        config = {
            "allowed_imports": ["json", "re"],
            "blocked_imports": ["os"],
            "network": False,
            "filesystem": True,
        }
        policy = SafetyPolicy.from_sandbox_config(config)
        assert policy.allowed_imports == {"json", "re"}
        assert policy.blocked_imports == {"os"}
        assert policy.allow_network is False
        assert policy.allow_filesystem is True

    def test_from_sandbox_config_alternate_keys(self):
        config = {
            "allow_network": False,
            "allow_filesystem": True,
        }
        policy = SafetyPolicy.from_sandbox_config(config)
        assert policy.allow_network is False
        assert policy.allow_filesystem is True

    def test_sandbox_roundtrip(self):
        original = SafetyPolicy(
            allowed_imports={"aiohttp", "json"},
            blocked_imports={"subprocess"},
            allow_network=True,
            allow_filesystem=False,
        )
        config = original.to_sandbox_config()
        restored = SafetyPolicy.from_sandbox_config(config)
        assert restored.allowed_imports == original.allowed_imports
        assert restored.blocked_imports == original.blocked_imports
        assert restored.allow_network == original.allow_network
        assert restored.allow_filesystem == original.allow_filesystem


# ── set_policy / get_policy / reset_policy ───────────────────────────────────


class TestPolicyContextVar:
    def setup_method(self):
        # Ensure clean state
        token = set_policy(None)
        reset_policy(token)

    def test_default_is_none(self):
        assert get_policy() is None

    def test_set_and_get(self):
        policy = SafetyPolicy.restrictive()
        token = set_policy(policy)
        assert get_policy() is policy
        reset_policy(token)

    def test_reset_restores_previous(self):
        p1 = SafetyPolicy.permissive()
        p2 = SafetyPolicy.restrictive()

        t1 = set_policy(p1)
        assert get_policy() is p1

        t2 = set_policy(p2)
        assert get_policy() is p2

        reset_policy(t2)
        assert get_policy() is p1

        reset_policy(t1)

    def test_set_none_clears(self):
        t1 = set_policy(SafetyPolicy.restrictive())
        assert get_policy() is not None

        t2 = set_policy(None)
        assert get_policy() is None

        reset_policy(t2)
        reset_policy(t1)


# ── Integration: Skill.invoke() with safety ──────────────────────────────────


class TestSkillInvokeSafety:
    def test_invoke_blocked_by_policy(self):
        sk = _make_skill(requires_network=True)
        policy = SafetyPolicy(allow_network=False)
        result = sk.invoke("hello", policy=policy)
        assert result.failed
        assert "network" in result.error.lower()
        assert "safety_violations" in result.metadata

    def test_invoke_allowed_by_policy(self):
        sk = _make_skill(requires_network=False)
        policy = SafetyPolicy(allow_network=False)
        result = sk.invoke("hello", policy=policy)
        assert result.success
        assert result.value == "hello"

    def test_invoke_no_policy_unrestricted(self):
        sk = _make_skill(requires_network=True, requires_filesystem=True)
        result = sk.invoke("hello")
        assert result.success

    def test_invoke_uses_active_policy(self):
        sk = _make_skill(requires_network=True)
        token = set_policy(SafetyPolicy(allow_network=False))
        try:
            result = sk.invoke("hello")
            assert result.failed
            assert "network" in result.error.lower()
        finally:
            reset_policy(token)

    def test_invoke_explicit_policy_overrides_active(self):
        sk = _make_skill(requires_network=True)
        # Active policy denies network
        token = set_policy(SafetyPolicy(allow_network=False))
        try:
            # Explicit policy allows it
            result = sk.invoke("hello", policy=SafetyPolicy.permissive())
            assert result.success
        finally:
            reset_policy(token)


# ── Integration: Skill.ainvoke() with safety ─────────────────────────────────


class TestSkillAinvokeSafety:
    def test_ainvoke_blocked_by_policy(self):
        sk = _make_skill(requires_network=True)
        policy = SafetyPolicy(allow_network=False)
        result = asyncio.get_event_loop().run_until_complete(
            sk.ainvoke("hello", policy=policy)
        )
        assert result.failed
        assert "network" in result.error.lower()

    def test_ainvoke_allowed_by_policy(self):
        sk = _make_skill(requires_network=False)
        policy = SafetyPolicy.restrictive()
        result = asyncio.get_event_loop().run_until_complete(
            sk.ainvoke("hello", policy=policy)
        )
        assert result.success

    def test_ainvoke_uses_active_policy(self):
        sk = _make_skill(requires_filesystem=True)
        token = set_policy(SafetyPolicy(allow_filesystem=False))
        try:
            result = asyncio.get_event_loop().run_until_complete(
                sk.ainvoke("hello")
            )
            assert result.failed
            assert "filesystem" in result.error.lower()
        finally:
            reset_policy(token)


# ── Integration: @skill decorator with safety ────────────────────────────────


class TestDecoratorSafety:
    def test_decorated_skill_respects_policy(self):
        @skill(
            name="web_scraper",
            requires_network=True,
            required_imports=["aiohttp"],
        )
        def web_scraper(url: str) -> str:
            return f"scraped: {url}"

        policy = SafetyPolicy(allow_network=False)
        result = web_scraper.__skill__.invoke("https://example.com", policy=policy)
        assert result.failed
        assert "network" in result.error.lower()

    def test_decorated_skill_passes_when_compliant(self):
        @skill(
            name="parser",
            required_imports=["json"],
        )
        def parser(data: str) -> dict:
            return {"parsed": data}

        policy = SafetyPolicy(allowed_imports={"json", "re"})
        result = parser.__skill__.invoke('{"key": "value"}', policy=policy)
        assert result.success

    def test_decorated_skill_blocked_import(self):
        @skill(
            name="sys_reader",
            required_imports=["os", "subprocess"],
        )
        def sys_reader(path: str) -> str:
            return path

        policy = SafetyPolicy(blocked_imports={"subprocess"})
        result = sys_reader.__skill__.invoke("/etc/passwd", policy=policy)
        assert result.failed
        assert "subprocess" in result.error
