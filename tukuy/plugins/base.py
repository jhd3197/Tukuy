"""Base classes and utilities for the plugin system."""

from abc import ABC, abstractmethod
from enum import Enum
import inspect
import sys
from typing import TYPE_CHECKING, Dict, List, Optional
from logging import getLogger

if TYPE_CHECKING:
    from ..manifest import PluginManifest
    from ..skill import Skill

logger = getLogger(__name__)


def register_transformer(name: str, **default_params):
    """Decorate a transformer class so ``_auto_transformers`` can discover it.

    Usage::

        @register_transformer("strip")
        class StripTransformer(ChainableTransformer[str, str]):
            ...

        @register_transformer("truncate", length=50, suffix="...")
        class TruncateTransformer(ChainableTransformer[str, str]):
            def __init__(self, name="", length=50, suffix="..."):
                ...

    The decorated class gets two private attributes:

    * ``_tukuy_name``  – the registry name (e.g. ``"strip"``)
    * ``_tukuy_defaults`` – a dict of default param values
    """
    def decorator(cls):
        cls._tukuy_name = name
        cls._tukuy_defaults = default_params
        return cls
    return decorator


class PluginSource(str, Enum):
    """Where a plugin was loaded from."""
    TUKUY = "tukuy"
    LOCAL = "local"
    PIP = "pip"          # future
    CLAUDE = "claude"    # future
    UNKNOWN = "unknown"


DEFAULT_SOURCE_PRIORITY: List[str] = ["tukuy", "local", "pip", "claude", "unknown"]


class TransformerPlugin(ABC):
    """
    Base class for transformer plugins.

    A plugin is a collection of related transformers that can be registered
    with the TukuyTransformer. Plugins provide a way to organize transformers
    into logical groups and manage their lifecycle.
    """

    def __init__(self, name: str, source: PluginSource = PluginSource.UNKNOWN):
        """
        Initialize the plugin.

        Args:
            name: Unique identifier for this plugin
            source: Where this plugin originates from
        """
        self.name = name
        self.source = source

    @property
    @abstractmethod
    def transformers(self) -> Dict[str, callable]:
        """
        Get the transformers provided by this plugin.

        Returns:
            A dictionary mapping transformer names to factory functions
        """
        return {}

    def initialize(self) -> None:
        """
        Called when the plugin is loaded.

        Override this method to perform any setup required by the plugin.
        """
        logger.info(f"Initializing plugin: {self.name}")

    async def async_initialize(self) -> None:
        """Async variant of :meth:`initialize`.

        Called by :meth:`PluginRegistry.async_register`.  The default
        implementation delegates to the synchronous ``initialize()`` so
        existing plugins work without changes.
        """
        self.initialize()

    @property
    def skills(self) -> Dict[str, "Skill"]:
        """Get the skills provided by this plugin.

        Returns:
            A dictionary mapping skill names to Skill instances.
            Defaults to an empty dict for backward compatibility.
        """
        return {}

    @property
    def manifest(self) -> "PluginManifest":
        """Declarative metadata about this plugin for discovery and UI.

        The default implementation auto-generates a minimal manifest from the
        plugin ``name``.  Subclasses can override to provide richer metadata
        (icons, colors, groups, requirements).
        """
        from ..manifest import PluginManifest

        return PluginManifest(name=self.name)

    def _auto_transformers(self) -> Dict[str, callable]:
        """Build a ``{name: factory}`` dict from ``@register_transformer``-decorated classes.

        Scans the module that defines ``self.__class__`` for classes whose
        ``_tukuy_name`` attribute is set by the decorator.  For each such
        class it introspects ``__init__`` to map a *params* dict to keyword
        arguments automatically.

        Returns:
            Dict mapping transformer names to factory callables.
        """
        module = sys.modules.get(self.__class__.__module__)
        if module is None:
            return {}

        factories: Dict[str, callable] = {}
        for _attr_name in dir(module):
            obj = getattr(module, _attr_name, None)
            if not (isinstance(obj, type) and hasattr(obj, '_tukuy_name')):
                continue

            tukuy_name: str = obj._tukuy_name
            defaults: dict = obj._tukuy_defaults

            # Introspect __init__ to find accepted parameter names (skip self, name)
            sig = inspect.signature(obj.__init__)
            init_params = {
                k: v
                for k, v in sig.parameters.items()
                if k not in ('self', 'name')
            }

            def _make_factory(_cls=obj, _defaults=defaults, _init_params=init_params, _name=tukuy_name):
                def factory(params):
                    kwargs = {}
                    for param_name, param_obj in _init_params.items():
                        if param_name in params:
                            kwargs[param_name] = params[param_name]
                        elif param_name in _defaults:
                            kwargs[param_name] = _defaults[param_name]
                        # else: let the class __init__ use its own default
                    return _cls(_name, **kwargs)
                return factory

            factories[tukuy_name] = _make_factory()

        return factories

    def cleanup(self) -> None:
        """
        Called when the plugin is unloaded.

        Override this method to perform any cleanup required by the plugin.
        """
        logger.info(f"Cleaning up plugin: {self.name}")

    async def async_cleanup(self) -> None:
        """Async variant of :meth:`cleanup`.

        Called by :meth:`PluginRegistry.async_unregister`.  The default
        implementation delegates to the synchronous ``cleanup()`` so
        existing plugins work without changes.
        """
        self.cleanup()

class PluginRegistry:
    """
    Registry for managing transformer plugins.

    The registry maintains the collection of loaded plugins and their
    transformers, handling registration, unregistration, and access to
    transformer factories.

    Plugins are stored in source-layered dicts.  A flat resolved view is
    rebuilt after every mutation so that all existing callers keep working.
    When two sources register the same transformer/skill name, the source
    with higher priority (lower index in ``_source_priority``) wins in the
    flat view.  Users can look up a specific source's version using a
    qualified name like ``"tukuy:strip"`` or ``"local:strip"``.
    """

    def __init__(self):
        """Initialize an empty plugin registry."""
        self._source_priority: List[str] = list(DEFAULT_SOURCE_PRIORITY)

        # Layered storage: source -> {name -> value}
        self._plugins_by_source: Dict[str, Dict[str, TransformerPlugin]] = {}
        self._transformers_by_source: Dict[str, Dict[str, callable]] = {}
        self._skills_by_source: Dict[str, Dict[str, "Skill"]] = {}

        # Flat resolved views (rebuilt by _rebuild_resolved_views)
        self._plugins: Dict[str, TransformerPlugin] = {}
        self._transformers: Dict[str, callable] = {}
        self._skills: Dict[str, "Skill"] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rebuild_resolved_views(self) -> None:
        """Iterate sources in priority order to produce flat resolved views."""
        new_plugins: Dict[str, TransformerPlugin] = {}
        new_transformers: Dict[str, callable] = {}
        new_skills: Dict[str, "Skill"] = {}

        for source in self._source_priority:
            # Plugins
            for name, plugin in self._plugins_by_source.get(source, {}).items():
                if name not in new_plugins:
                    new_plugins[name] = plugin
                else:
                    logger.debug(
                        "Plugin '%s' from source '%s' shadowed by higher-priority source",
                        name, source,
                    )

            # Transformers
            for name, factory in self._transformers_by_source.get(source, {}).items():
                if name not in new_transformers:
                    new_transformers[name] = factory
                else:
                    logger.debug(
                        "Transformer '%s' from source '%s' shadowed by higher-priority source",
                        name, source,
                    )

            # Skills
            for name, skill_obj in self._skills_by_source.get(source, {}).items():
                if name not in new_skills:
                    new_skills[name] = skill_obj
                else:
                    logger.debug(
                        "Skill '%s' from source '%s' shadowed by higher-priority source",
                        name, source,
                    )

        # Also pick up any sources not in priority list
        all_sources = set(self._plugins_by_source) | set(self._transformers_by_source) | set(self._skills_by_source)
        extra_sources = all_sources - set(self._source_priority)
        for source in sorted(extra_sources):
            for name, plugin in self._plugins_by_source.get(source, {}).items():
                if name not in new_plugins:
                    new_plugins[name] = plugin
            for name, factory in self._transformers_by_source.get(source, {}).items():
                if name not in new_transformers:
                    new_transformers[name] = factory
            for name, skill_obj in self._skills_by_source.get(source, {}).items():
                if name not in new_skills:
                    new_skills[name] = skill_obj

        self._plugins = new_plugins
        self._transformers = new_transformers
        self._skills = new_skills

    @staticmethod
    def _resolve_source(source) -> str:
        """Normalise a source to its string value."""
        if source is None:
            return PluginSource.UNKNOWN.value
        if isinstance(source, PluginSource):
            return source.value
        return str(source)

    def _store_plugin(self, plugin: TransformerPlugin, source_str: str) -> None:
        """Store a plugin in the layered structures."""
        plugin.source = PluginSource(source_str) if source_str in PluginSource._value2member_map_ else PluginSource.UNKNOWN

        self._plugins_by_source.setdefault(source_str, {})[plugin.name] = plugin

        self._transformers_by_source.setdefault(source_str, {}).update(plugin.transformers)

        try:
            self._skills_by_source.setdefault(source_str, {}).update(plugin.skills)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public registration API
    # ------------------------------------------------------------------

    def register(self, plugin: TransformerPlugin, source=None) -> None:
        """
        Register a plugin with the registry.

        Args:
            plugin: The plugin to register
            source: Where this plugin comes from (PluginSource or str).
                    Defaults to the plugin's own ``source`` attribute, or
                    ``UNKNOWN`` if not set.

        Raises:
            ValueError: If a plugin with the same name is already registered
                        **from the same source**.
        """
        source_str = self._resolve_source(source if source is not None else getattr(plugin, "source", None))

        existing = self._plugins_by_source.get(source_str, {})
        if plugin.name in existing:
            raise ValueError(f"Plugin already registered: {plugin.name}")

        logger.info(f"Registering plugin: {plugin.name} (source={source_str})")
        self._store_plugin(plugin, source_str)
        self._rebuild_resolved_views()
        plugin.initialize()

    async def async_register(self, plugin: TransformerPlugin, source=None) -> None:
        """Async variant of :meth:`register`.

        Indexes transformers and skills synchronously, then awaits the
        plugin's :meth:`~TransformerPlugin.async_initialize`.
        """
        source_str = self._resolve_source(source if source is not None else getattr(plugin, "source", None))

        existing = self._plugins_by_source.get(source_str, {})
        if plugin.name in existing:
            raise ValueError(f"Plugin already registered: {plugin.name}")

        logger.info(f"Async registering plugin: {plugin.name} (source={source_str})")
        self._store_plugin(plugin, source_str)
        self._rebuild_resolved_views()
        await plugin.async_initialize()

    def unregister(self, name: str) -> None:
        """
        Unregister a plugin from the registry.

        Finds the first source that contains a plugin with this name,
        cleans it up, removes it from layered storage, and rebuilds views.

        Args:
            name: Name of the plugin to unregister
        """
        # Find which source(s) hold this plugin
        found_source = None
        for source_str, plugins_dict in self._plugins_by_source.items():
            if name in plugins_dict:
                found_source = source_str
                break

        if found_source is None:
            return

        logger.info(f"Unregistering plugin: {name} (source={found_source})")
        plugin = self._plugins_by_source[found_source][name]
        plugin.cleanup()

        # Remove from layered storage
        del self._plugins_by_source[found_source][name]

        for key in plugin.transformers:
            self._transformers_by_source.get(found_source, {}).pop(key, None)

        try:
            for key in plugin.skills:
                self._skills_by_source.get(found_source, {}).pop(key, None)
        except Exception:
            pass

        self._rebuild_resolved_views()

    async def async_unregister(self, name: str) -> None:
        """Async variant of :meth:`unregister`.

        Awaits the plugin's :meth:`~TransformerPlugin.async_cleanup` before
        removing it from the registry.
        """
        found_source = None
        for source_str, plugins_dict in self._plugins_by_source.items():
            if name in plugins_dict:
                found_source = source_str
                break

        if found_source is None:
            return

        logger.info(f"Async unregistering plugin: {name} (source={found_source})")
        plugin = self._plugins_by_source[found_source][name]
        await plugin.async_cleanup()

        del self._plugins_by_source[found_source][name]

        for key in plugin.transformers:
            self._transformers_by_source.get(found_source, {}).pop(key, None)

        try:
            for key in plugin.skills:
                self._skills_by_source.get(found_source, {}).pop(key, None)
        except Exception:
            pass

        self._rebuild_resolved_views()

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_qualified_name(name: str):
        """Split ``"source:bare_name"`` into ``(source, bare_name)`` or ``(None, name)``."""
        if ":" in name:
            source, _, bare = name.partition(":")
            return source, bare
        return None, name

    def get_transformer(self, name: str) -> Optional[callable]:
        """
        Get a transformer factory by name.

        Supports qualified names like ``"tukuy:strip"`` to bypass priority
        resolution and look up a specific source directly.

        Args:
            name: Name of the transformer (optionally qualified as ``source:name``)

        Returns:
            The transformer factory function, or None if not found
        """
        source, bare = self._parse_qualified_name(name)
        if source is not None:
            return self._transformers_by_source.get(source, {}).get(bare)
        return self._transformers.get(name)

    def get_plugin(self, name: str) -> Optional[TransformerPlugin]:
        """
        Get a plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            The plugin instance, or None if not found
        """
        return self._plugins.get(name)

    @property
    def plugins(self) -> Dict[str, TransformerPlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()

    @property
    def transformers(self) -> Dict[str, callable]:
        """Get all registered transformers."""
        return self._transformers.copy()

    def get_skill(self, name: str) -> Optional["Skill"]:
        """Get a skill by name.

        Supports qualified names like ``"tukuy:my_skill"``.

        Args:
            name: Name of the skill (optionally qualified as ``source:name``)

        Returns:
            The Skill instance, or None if not found
        """
        source, bare = self._parse_qualified_name(name)
        if source is not None:
            return self._skills_by_source.get(source, {}).get(bare)
        return self._skills.get(name)

    @property
    def skills(self) -> Dict[str, "Skill"]:
        """Get all registered skills."""
        return self._skills.copy()

    # ------------------------------------------------------------------
    # Introspection & priority management
    # ------------------------------------------------------------------

    def get_source_for_transformer(self, name: str) -> Optional[str]:
        """Return the winning source string for *name*, or ``None``."""
        for source in self._source_priority:
            if name in self._transformers_by_source.get(source, {}):
                return source
        # Check extra sources
        for source in sorted(set(self._transformers_by_source) - set(self._source_priority)):
            if name in self._transformers_by_source[source]:
                return source
        return None

    def get_all_sources_for_transformer(self, name: str) -> List[str]:
        """Return every source that provides *name*, in priority order."""
        sources: List[str] = []
        for source in self._source_priority:
            if name in self._transformers_by_source.get(source, {}):
                sources.append(source)
        for source in sorted(set(self._transformers_by_source) - set(self._source_priority)):
            if name in self._transformers_by_source[source]:
                sources.append(source)
        return sources

    def get_source_for_skill(self, name: str) -> Optional[str]:
        """Return the winning source string for skill *name*, or ``None``."""
        for source in self._source_priority:
            if name in self._skills_by_source.get(source, {}):
                return source
        for source in sorted(set(self._skills_by_source) - set(self._source_priority)):
            if name in self._skills_by_source[source]:
                return source
        return None

    def get_all_sources_for_skill(self, name: str) -> List[str]:
        """Return every source that provides skill *name*, in priority order."""
        sources: List[str] = []
        for source in self._source_priority:
            if name in self._skills_by_source.get(source, {}):
                sources.append(source)
        for source in sorted(set(self._skills_by_source) - set(self._source_priority)):
            if name in self._skills_by_source[source]:
                sources.append(source)
        return sources

    def set_source_priority(self, priority: List[str]) -> None:
        """Override the default source priority and rebuild resolved views.

        Args:
            priority: Ordered list of source strings (highest priority first).
        """
        self._source_priority = list(priority)
        self._rebuild_resolved_views()
