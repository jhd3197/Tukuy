"""Tests for the plugin source & priority system."""

import pytest
from typing import Dict

from tukuy.plugins.base import (
    TransformerPlugin,
    PluginRegistry,
    PluginSource,
    DEFAULT_SOURCE_PRIORITY,
)


# ---------------------------------------------------------------------------
# Helpers — minimal concrete plugins for testing
# ---------------------------------------------------------------------------

class _StubPlugin(TransformerPlugin):
    """A minimal plugin that exposes a single transformer and optional skill."""

    def __init__(self, name: str, transformer_value="default", skill_value=None):
        super().__init__(name)
        self._transformer_value = transformer_value
        self._skill_value = skill_value

    @property
    def transformers(self) -> Dict[str, callable]:
        return {self.name: lambda: self._transformer_value}

    @property
    def skills(self) -> Dict[str, object]:
        if self._skill_value is not None:
            return {self.name: self._skill_value}
        return {}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPluginSourceEnum:
    def test_string_values(self):
        assert PluginSource.TUKUY == "tukuy"
        assert PluginSource.LOCAL == "local"
        assert PluginSource.UNKNOWN == "unknown"

    def test_default_priority_order(self):
        assert DEFAULT_SOURCE_PRIORITY[0] == "tukuy"
        assert "local" in DEFAULT_SOURCE_PRIORITY
        assert "unknown" in DEFAULT_SOURCE_PRIORITY


class TestRegistrationWithSource:
    def test_register_with_explicit_source(self):
        reg = PluginRegistry()
        p = _StubPlugin("foo")
        reg.register(p, source=PluginSource.TUKUY)
        assert reg.get_plugin("foo") is p
        assert p.source == PluginSource.TUKUY

    def test_register_without_source_defaults_to_unknown(self):
        reg = PluginRegistry()
        p = _StubPlugin("bar")
        reg.register(p)
        assert p.source == PluginSource.UNKNOWN
        assert reg.get_source_for_transformer("bar") == "unknown"

    def test_register_same_name_same_source_raises(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("x"), source=PluginSource.TUKUY)
        with pytest.raises(ValueError, match="already registered"):
            reg.register(_StubPlugin("x"), source=PluginSource.TUKUY)

    def test_register_same_name_different_source_allowed(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("dup", transformer_value="tukuy_ver"), source=PluginSource.TUKUY)
        reg.register(_StubPlugin("dup", transformer_value="local_ver"), source=PluginSource.LOCAL)
        # Both are registered — tukuy wins in flat view
        assert reg.get_transformer("dup")() == "tukuy_ver"


class TestPriorityResolution:
    def test_tukuy_wins_over_local_by_default(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("t", transformer_value="tukuy_val"), source=PluginSource.TUKUY)
        reg.register(_StubPlugin("t", transformer_value="local_val"), source=PluginSource.LOCAL)
        assert reg.get_transformer("t")() == "tukuy_val"

    def test_local_wins_over_unknown(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("t", transformer_value="local_val"), source=PluginSource.LOCAL)
        reg.register(_StubPlugin("t", transformer_value="unknown_val"), source=PluginSource.UNKNOWN)
        assert reg.get_transformer("t")() == "local_val"

    def test_set_source_priority_inverts_resolution(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("t", transformer_value="tukuy_val"), source=PluginSource.TUKUY)
        reg.register(_StubPlugin("t", transformer_value="local_val"), source=PluginSource.LOCAL)
        # Default: tukuy wins
        assert reg.get_transformer("t")() == "tukuy_val"
        # Invert priority
        reg.set_source_priority(["local", "tukuy", "pip", "claude", "unknown"])
        assert reg.get_transformer("t")() == "local_val"

    def test_priority_applies_to_skills_too(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("s", skill_value="tukuy_skill"), source=PluginSource.TUKUY)
        reg.register(_StubPlugin("s", skill_value="local_skill"), source=PluginSource.LOCAL)
        assert reg.get_skill("s") == "tukuy_skill"
        reg.set_source_priority(["local", "tukuy", "pip", "claude", "unknown"])
        assert reg.get_skill("s") == "local_skill"


class TestQualifiedNameLookup:
    def test_qualified_transformer_lookup(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("t", transformer_value="tukuy_val"), source=PluginSource.TUKUY)
        reg.register(_StubPlugin("t", transformer_value="local_val"), source=PluginSource.LOCAL)
        assert reg.get_transformer("tukuy:t")() == "tukuy_val"
        assert reg.get_transformer("local:t")() == "local_val"

    def test_qualified_skill_lookup(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("s", skill_value="tk"), source=PluginSource.TUKUY)
        reg.register(_StubPlugin("s", skill_value="lc"), source=PluginSource.LOCAL)
        assert reg.get_skill("tukuy:s") == "tk"
        assert reg.get_skill("local:s") == "lc"

    def test_qualified_nonexistent_returns_none(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("t"), source=PluginSource.TUKUY)
        assert reg.get_transformer("local:t") is None
        assert reg.get_skill("local:t") is None

    def test_unqualified_name_uses_flat_view(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("t", transformer_value="v"), source=PluginSource.TUKUY)
        assert reg.get_transformer("t")() == "v"


class TestUnregister:
    def test_unregister_from_one_source_keeps_other(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("t", transformer_value="tukuy_val"), source=PluginSource.TUKUY)
        reg.register(_StubPlugin("t", transformer_value="local_val"), source=PluginSource.LOCAL)
        # Unregister tukuy's version
        reg.unregister("t")
        # Local version should now win
        assert reg.get_transformer("t")() == "local_val"

    def test_unregister_nonexistent_is_noop(self):
        reg = PluginRegistry()
        reg.unregister("does_not_exist")  # Should not raise


class TestIntrospection:
    def test_get_source_for_transformer(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("t", transformer_value="v"), source=PluginSource.TUKUY)
        assert reg.get_source_for_transformer("t") == "tukuy"

    def test_get_source_for_transformer_returns_none(self):
        reg = PluginRegistry()
        assert reg.get_source_for_transformer("nonexistent") is None

    def test_get_all_sources_for_transformer(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("t", transformer_value="tv"), source=PluginSource.TUKUY)
        reg.register(_StubPlugin("t", transformer_value="lv"), source=PluginSource.LOCAL)
        sources = reg.get_all_sources_for_transformer("t")
        assert sources == ["tukuy", "local"]

    def test_get_source_for_skill(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("s", skill_value="sk"), source=PluginSource.LOCAL)
        assert reg.get_source_for_skill("s") == "local"

    def test_get_all_sources_for_skill(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("s", skill_value="sk1"), source=PluginSource.TUKUY)
        reg.register(_StubPlugin("s", skill_value="sk2"), source=PluginSource.LOCAL)
        assert reg.get_all_sources_for_skill("s") == ["tukuy", "local"]


class TestBackwardCompatibility:
    def test_flat_plugins_property(self):
        reg = PluginRegistry()
        p = _StubPlugin("foo")
        reg.register(p)
        plugins = reg.plugins
        assert "foo" in plugins
        assert isinstance(plugins, dict)

    def test_flat_transformers_property(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("bar"))
        transformers = reg.transformers
        assert "bar" in transformers
        assert isinstance(transformers, dict)

    def test_flat_skills_property(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("baz", skill_value="sk"))
        skills = reg.skills
        assert "baz" in skills

    def test_properties_return_copies(self):
        reg = PluginRegistry()
        reg.register(_StubPlugin("x"))
        t1 = reg.transformers
        t1["injected"] = "bad"
        assert "injected" not in reg.transformers


class TestTransformerPluginSource:
    def test_default_source_is_unknown(self):
        p = _StubPlugin("test")
        assert p.source == PluginSource.UNKNOWN

    def test_source_set_by_register(self):
        reg = PluginRegistry()
        p = _StubPlugin("test")
        reg.register(p, source=PluginSource.LOCAL)
        assert p.source == PluginSource.LOCAL


class TestIntegrationWithTukuyTransformer:
    def test_builtins_tagged_as_tukuy(self, transformer):
        """Built-in plugins loaded by TukuyTransformer should be tagged as tukuy."""
        # Every transformer in the registry should have source=tukuy
        for name in transformer.registry.transformers:
            source = transformer.registry.get_source_for_transformer(name)
            assert source == "tukuy", f"Transformer '{name}' has source '{source}', expected 'tukuy'"

    def test_qualified_lookup_for_builtin(self, transformer):
        """Qualified name lookup should work for built-in transformers."""
        # Pick any transformer that exists
        names = list(transformer.registry.transformers.keys())
        if names:
            name = names[0]
            assert transformer.registry.get_transformer(f"tukuy:{name}") is not None
            assert transformer.registry.get_transformer(f"local:{name}") is None
