"""Local/dynamic plugins plugin — plugin creator and lifecycle manager.

Skills-only plugin that lets users and AI tools (like Prompture) create,
discover, validate, load, and unload custom Tukuy plugins from
``~/.tukuy/plugins/``.

Pure stdlib — no external dependencies.
"""

import importlib
import importlib.util
import inspect
import os
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...plugins.base import TransformerPlugin, PluginRegistry
from ...skill import skill

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LOCAL_PLUGINS_DIR = Path.home() / ".tukuy" / "plugins"

# Track which local plugins are currently loaded so we can list/unload them
# independently of the global registry.
_loaded_local_plugins: Dict[str, TransformerPlugin] = {}

# Reference to the active registry — set by the plugin's ``initialize()``.
_registry: Optional[PluginRegistry] = None


def _ensure_dir() -> Path:
    """Ensure ``~/.tukuy/plugins/`` exists and return its path."""
    LOCAL_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    return LOCAL_PLUGINS_DIR


def _plugin_dir(name: str) -> Path:
    return LOCAL_PLUGINS_DIR / name


def _find_plugin_class(module: Any) -> Optional[type]:
    """Find exactly one ``TransformerPlugin`` subclass in *module*."""
    candidates = []
    for attr_name in dir(module):
        obj = getattr(module, attr_name)
        if (
            isinstance(obj, type)
            and issubclass(obj, TransformerPlugin)
            and obj is not TransformerPlugin
        ):
            candidates.append(obj)
    if len(candidates) == 1:
        return candidates[0]
    return None


# ---------------------------------------------------------------------------
# Scaffold templates
# ---------------------------------------------------------------------------

_SCAFFOLD_BOTH = textwrap.dedent('''\
    """$DESCRIPTION"""

    from typing import Any, Dict, Optional

    from tukuy.plugins.base import TransformerPlugin
    from tukuy.base import ChainableTransformer
    from tukuy.types import TransformContext
    from tukuy.skill import skill


    # --- Transformers -------------------------------------------------------

    class ExampleTransformer(ChainableTransformer[str, str]):
        """A sample transformer — replace with your own logic."""

        def validate(self, value: str) -> bool:
            return isinstance(value, str)

        def _transform(
            self, value: str, context: Optional[TransformContext] = None
        ) -> str:
            return value


    # --- Skills -------------------------------------------------------------

    @skill(
        name="${NAME}_hello",
        description="Example skill for the $NAME plugin.",
        category="$NAME",
        tags=["$NAME", "local"],
        idempotent=True,
    )
    def ${NAME}_hello(text: str = "world") -> dict:
        """Say hello."""
        return {"message": f"Hello, {text}!"}


    # --- Plugin class -------------------------------------------------------

    class ${CLASS}(TransformerPlugin):
        """$DESCRIPTION"""

        def __init__(self):
            super().__init__("$NAME")

        @property
        def transformers(self) -> Dict[str, callable]:
            return {
                "${NAME}_example": lambda **kw: ExampleTransformer("${NAME}_example", **kw),
            }

        @property
        def skills(self) -> Dict[str, Any]:
            return {
                "${NAME}_hello": ${NAME}_hello.__skill__,
            }
''')

_SCAFFOLD_SKILLS = textwrap.dedent('''\
    """$DESCRIPTION"""

    from typing import Any, Dict

    from tukuy.plugins.base import TransformerPlugin
    from tukuy.skill import skill


    # --- Skills -------------------------------------------------------------

    @skill(
        name="${NAME}_hello",
        description="Example skill for the $NAME plugin.",
        category="$NAME",
        tags=["$NAME", "local"],
        idempotent=True,
    )
    def ${NAME}_hello(text: str = "world") -> dict:
        """Say hello."""
        return {"message": f"Hello, {text}!"}


    # --- Plugin class -------------------------------------------------------

    class ${CLASS}(TransformerPlugin):
        """$DESCRIPTION"""

        def __init__(self):
            super().__init__("$NAME")

        @property
        def transformers(self) -> Dict[str, callable]:
            return {}

        @property
        def skills(self) -> Dict[str, Any]:
            return {
                "${NAME}_hello": ${NAME}_hello.__skill__,
            }
''')

_SCAFFOLD_TRANSFORMERS = textwrap.dedent('''\
    """$DESCRIPTION"""

    from typing import Any, Dict, Optional

    from tukuy.plugins.base import TransformerPlugin
    from tukuy.base import ChainableTransformer
    from tukuy.types import TransformContext


    # --- Transformers -------------------------------------------------------

    class ExampleTransformer(ChainableTransformer[str, str]):
        """A sample transformer — replace with your own logic."""

        def validate(self, value: str) -> bool:
            return isinstance(value, str)

        def _transform(
            self, value: str, context: Optional[TransformContext] = None
        ) -> str:
            return value


    # --- Plugin class -------------------------------------------------------

    class ${CLASS}(TransformerPlugin):
        """$DESCRIPTION"""

        def __init__(self):
            super().__init__("$NAME")

        @property
        def transformers(self) -> Dict[str, callable]:
            return {
                "${NAME}_example": lambda **kw: ExampleTransformer("${NAME}_example", **kw),
            }

        @property
        def skills(self) -> Dict[str, Any]:
            return {}
''')

_SCAFFOLDS = {
    "both": _SCAFFOLD_BOTH,
    "skills": _SCAFFOLD_SKILLS,
    "transformers": _SCAFFOLD_TRANSFORMERS,
}


def _render_scaffold(name: str, plugin_type: str, description: str) -> str:
    """Render a scaffold template with the given parameters."""
    template = _SCAFFOLDS.get(plugin_type, _SCAFFOLD_BOTH)
    class_name = "".join(part.capitalize() for part in name.split("_")) + "Plugin"
    return (
        template
        .replace("$DESCRIPTION", description)
        .replace("${CLASS}", class_name)
        .replace("${NAME}", name)
        .replace("$NAME", name)
    )


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@skill(
    name="local_spec",
    description=(
        "Return the full Tukuy plugin creation specification. "
        "Contains interfaces, base classes, decorators, file structure, "
        "and examples — everything an AI agent needs to generate a valid plugin."
    ),
    category="local_plugins",
    tags=["local", "plugins", "spec", "creator"],
    idempotent=True,
)
def local_spec() -> dict:
    """Return the complete plugin-creation specification."""
    return {
        "version": "1.0",
        "plugin_dir": str(LOCAL_PLUGINS_DIR),
        "file_structure": {
            "description": "Each plugin is a Python package under ~/.tukuy/plugins/",
            "layout": [
                "~/.tukuy/plugins/<name>/__init__.py  # REQUIRED — exports one TransformerPlugin subclass",
                "~/.tukuy/plugins/<name>/helpers.py    # optional helper modules",
            ],
        },
        "interfaces": {
            "TransformerPlugin": {
                "import": "from tukuy.plugins.base import TransformerPlugin",
                "description": "Abstract base class every plugin must subclass.",
                "constructor": "__init__(self, name: str) — call super().__init__(name)",
                "required_properties": {
                    "transformers": {
                        "signature": "@property def transformers(self) -> Dict[str, callable]",
                        "description": "Return a dict mapping transformer names to factory functions. Return {} for skills-only plugins.",
                    },
                },
                "optional_properties": {
                    "skills": {
                        "signature": "@property def skills(self) -> Dict[str, Skill]",
                        "description": "Return a dict mapping skill names to Skill instances (fn.__skill__). Return {} for transformers-only plugins.",
                    },
                },
                "lifecycle_methods": {
                    "initialize": "Called when the plugin is loaded (sync).",
                    "async_initialize": "Async variant — called by async_register.",
                    "cleanup": "Called when the plugin is unloaded (sync).",
                    "async_cleanup": "Async variant — called by async_unregister.",
                },
            },
            "ChainableTransformer": {
                "import": "from tukuy.base import ChainableTransformer",
                "type_params": "ChainableTransformer[T, U] — T is input type, U is output type",
                "required_methods": {
                    "validate": "def validate(self, value: T) -> bool — return True if value is valid input",
                    "_transform": "def _transform(self, value: T, context: Optional[TransformContext] = None) -> U — core logic",
                },
                "constructor": "__init__(self, name: str, next_transformer=None, options=None)",
                "chaining": "Use .chain(next_transformer) for fluent piping.",
            },
            "skill_decorator": {
                "import": "from tukuy.skill import skill",
                "usage": "@skill(name=..., description=..., category=..., tags=[...], ...)",
                "parameters": {
                    "name": "str — unique skill name (default: function name)",
                    "description": "str — what the skill does (default: docstring)",
                    "version": "str — version string (default: '0.1.0')",
                    "input_schema": "None | dict | type — JSON Schema for input (auto-inferred from annotations)",
                    "output_schema": "None | dict | type — JSON Schema for output (auto-inferred from annotations)",
                    "category": "str — grouping category (default: 'general')",
                    "tags": "List[str] — discovery tags (lowercased automatically)",
                    "examples": "List[SkillExample] — usage examples",
                    "is_async": "bool — auto-detected if None",
                    "idempotent": "bool — safe to retry (default: False)",
                    "side_effects": "bool — modifies external state (default: False)",
                    "requires_network": "bool — needs network access (default: False)",
                    "requires_filesystem": "bool — needs filesystem access (default: False)",
                },
                "access_skill_object": "function_name.__skill__ — the Skill instance attached by the decorator",
            },
        },
        "available_imports": [
            "from tukuy.plugins.base import TransformerPlugin",
            "from tukuy.base import ChainableTransformer",
            "from tukuy.types import TransformContext, TransformOptions, TransformResult, T, U",
            "from tukuy.exceptions import TransformerError, ValidationError, TransformationError",
            "from tukuy.skill import skill, SkillExample, SkillDescriptor",
        ],
        "examples": {
            "skills_only": {
                "description": "A plugin that only provides skills (no transformers).",
                "code": textwrap.dedent("""\
                    from typing import Any, Dict
                    from tukuy.plugins.base import TransformerPlugin
                    from tukuy.skill import skill

                    @skill(
                        name="greet",
                        description="Greet someone by name.",
                        category="demo",
                        tags=["demo"],
                        idempotent=True,
                    )
                    def greet(name: str = "world") -> dict:
                        return {"greeting": f"Hello, {name}!"}

                    class GreetPlugin(TransformerPlugin):
                        def __init__(self):
                            super().__init__("greet")

                        @property
                        def transformers(self) -> Dict[str, callable]:
                            return {}

                        @property
                        def skills(self) -> Dict[str, Any]:
                            return {"greet": greet.__skill__}
                """),
            },
            "transformers_only": {
                "description": "A plugin that only provides transformers (no skills).",
                "code": textwrap.dedent("""\
                    from typing import Any, Dict, Optional
                    from tukuy.plugins.base import TransformerPlugin
                    from tukuy.base import ChainableTransformer
                    from tukuy.types import TransformContext

                    class ReverseTransformer(ChainableTransformer[str, str]):
                        def validate(self, value: str) -> bool:
                            return isinstance(value, str)

                        def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
                            return value[::-1]

                    class ReversePlugin(TransformerPlugin):
                        def __init__(self):
                            super().__init__("reverse")

                        @property
                        def transformers(self) -> Dict[str, callable]:
                            return {"reverse": lambda **kw: ReverseTransformer("reverse", **kw)}

                        @property
                        def skills(self) -> Dict[str, Any]:
                            return {}
                """),
            },
            "mixed": {
                "description": "A plugin with both transformers and skills.",
                "code": textwrap.dedent("""\
                    from typing import Any, Dict, Optional
                    from tukuy.plugins.base import TransformerPlugin
                    from tukuy.base import ChainableTransformer
                    from tukuy.types import TransformContext
                    from tukuy.skill import skill

                    class ShoutTransformer(ChainableTransformer[str, str]):
                        def validate(self, value: str) -> bool:
                            return isinstance(value, str)

                        def _transform(self, value: str, context: Optional[TransformContext] = None) -> str:
                            return value.upper() + "!"

                    @skill(
                        name="shout_info",
                        description="Return info about the shout plugin.",
                        category="shout",
                        tags=["shout"],
                        idempotent=True,
                    )
                    def shout_info() -> dict:
                        return {"name": "shout", "version": "1.0"}

                    class ShoutPlugin(TransformerPlugin):
                        def __init__(self):
                            super().__init__("shout")

                        @property
                        def transformers(self) -> Dict[str, callable]:
                            return {"shout": lambda **kw: ShoutTransformer("shout", **kw)}

                        @property
                        def skills(self) -> Dict[str, Any]:
                            return {"shout_info": shout_info.__skill__}
                """),
            },
        },
    }


@skill(
    name="local_scaffold",
    description="Generate a ready-to-edit plugin directory from a name, type, and description.",
    category="local_plugins",
    tags=["local", "plugins", "scaffold", "creator"],
    side_effects=True,
    requires_filesystem=True,
)
def local_scaffold(
    name: str,
    plugin_type: str = "both",
    description: str = "A custom Tukuy plugin.",
) -> dict:
    """Create a scaffolded plugin at ``~/.tukuy/plugins/<name>/``."""
    if plugin_type not in ("both", "skills", "transformers"):
        return {
            "created": False,
            "error": f"Invalid plugin_type '{plugin_type}'. Must be 'both', 'skills', or 'transformers'.",
        }

    plugin_path = _ensure_dir() / name
    init_path = plugin_path / "__init__.py"

    if plugin_path.exists():
        return {
            "created": False,
            "error": f"Directory already exists: {plugin_path}",
        }

    plugin_path.mkdir(parents=True)
    content = _render_scaffold(name, plugin_type, description)
    init_path.write_text(content, encoding="utf-8")

    return {
        "created": True,
        "path": str(init_path),
        "plugin_type": plugin_type,
        "content": content,
    }


@skill(
    name="local_validate",
    description="Validate a local plugin's structure and code before loading.",
    category="local_plugins",
    tags=["local", "plugins", "validate"],
    idempotent=True,
    requires_filesystem=True,
)
def local_validate(name: str) -> dict:
    """Validate the plugin at ``~/.tukuy/plugins/<name>/``."""
    errors: List[str] = []
    warnings: List[str] = []

    plugin_path = _plugin_dir(name)
    init_path = plugin_path / "__init__.py"

    # Check directory exists
    if not plugin_path.is_dir():
        return {"valid": False, "errors": [f"Directory not found: {plugin_path}"], "warnings": []}

    # Check __init__.py exists
    if not init_path.is_file():
        return {"valid": False, "errors": [f"Missing __init__.py in {plugin_path}"], "warnings": []}

    # Attempt to import the module
    module_name = f"_tukuy_local_validate_{name}"
    spec = importlib.util.spec_from_file_location(module_name, str(init_path))
    if spec is None or spec.loader is None:
        return {"valid": False, "errors": [f"Cannot create import spec for {init_path}"], "warnings": []}

    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:
        return {"valid": False, "errors": [f"Import error: {exc}"], "warnings": []}
    finally:
        # Clean up the temporary module
        sys.modules.pop(module_name, None)

    # Find TransformerPlugin subclass
    plugin_cls = _find_plugin_class(module)
    if plugin_cls is None:
        # Count candidates for a better message
        candidates = [
            attr for attr in dir(module)
            if isinstance(getattr(module, attr), type)
            and issubclass(getattr(module, attr), TransformerPlugin)
            and getattr(module, attr) is not TransformerPlugin
        ]
        if len(candidates) == 0:
            errors.append("No TransformerPlugin subclass found.")
        else:
            errors.append(
                f"Expected exactly 1 TransformerPlugin subclass, found {len(candidates)}: {candidates}"
            )
        return {"valid": False, "errors": errors, "warnings": warnings}

    # Instantiate and check properties
    try:
        instance = plugin_cls()
    except Exception as exc:
        errors.append(f"Instantiation error: {exc}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # Check transformers property
    try:
        transformers = instance.transformers
        if not isinstance(transformers, dict):
            errors.append(f"'transformers' property must return a dict, got {type(transformers).__name__}")
    except Exception as exc:
        errors.append(f"Error accessing 'transformers': {exc}")

    # Check skills property
    try:
        skills = instance.skills
        if not isinstance(skills, dict):
            errors.append(f"'skills' property must return a dict, got {type(skills).__name__}")
    except Exception as exc:
        # skills is optional — just warn
        warnings.append(f"Error accessing 'skills': {exc}")

    # Check that factory functions are callable
    try:
        transformers = instance.transformers
        for tname, factory in transformers.items():
            if not callable(factory):
                errors.append(f"Transformer factory '{tname}' is not callable.")
    except Exception:
        pass  # already reported above

    if not errors:
        warnings_msg = f" ({len(warnings)} warnings)" if warnings else ""
        return {"valid": True, "errors": [], "warnings": warnings, "message": f"Plugin '{name}' is valid{warnings_msg}."}

    return {"valid": False, "errors": errors, "warnings": warnings}


@skill(
    name="local_discover",
    description="Scan ~/.tukuy/plugins/ and return all found plugins with metadata.",
    category="local_plugins",
    tags=["local", "plugins", "discover"],
    idempotent=True,
    requires_filesystem=True,
)
def local_discover() -> dict:
    """Discover local plugins without importing them."""
    _ensure_dir()
    plugins: List[Dict[str, Any]] = []

    for entry in sorted(LOCAL_PLUGINS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        init_file = entry / "__init__.py"
        if not init_file.is_file():
            continue

        name = entry.name
        content = init_file.read_text(encoding="utf-8", errors="replace")

        plugins.append({
            "name": name,
            "path": str(entry),
            "has_transformers": "transformers" in content and "ChainableTransformer" in content,
            "has_skills": "@skill" in content,
            "loaded": name in _loaded_local_plugins,
        })

    return {"plugins_dir": str(LOCAL_PLUGINS_DIR), "plugins": plugins, "count": len(plugins)}


@skill(
    name="local_load",
    description="Load a local plugin into the active plugin registry.",
    category="local_plugins",
    tags=["local", "plugins", "load"],
    side_effects=True,
    requires_filesystem=True,
)
def local_load(name: str) -> dict:
    """Load the plugin at ``~/.tukuy/plugins/<name>/`` into the registry."""
    if name in _loaded_local_plugins:
        return {"loaded": False, "error": f"Plugin '{name}' is already loaded."}

    plugin_path = _plugin_dir(name)
    init_path = plugin_path / "__init__.py"

    if not init_path.is_file():
        return {"loaded": False, "error": f"Plugin not found: {plugin_path}"}

    # Import the module
    module_name = f"tukuy_local_plugin_{name}"
    spec = importlib.util.spec_from_file_location(module_name, str(init_path))
    if spec is None or spec.loader is None:
        return {"loaded": False, "error": f"Cannot create import spec for {init_path}"}

    try:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        return {"loaded": False, "error": f"Import error: {exc}"}

    # Find and instantiate the plugin class
    plugin_cls = _find_plugin_class(module)
    if plugin_cls is None:
        sys.modules.pop(module_name, None)
        return {"loaded": False, "error": "No single TransformerPlugin subclass found."}

    try:
        instance = plugin_cls()
    except Exception as exc:
        sys.modules.pop(module_name, None)
        return {"loaded": False, "error": f"Instantiation error: {exc}"}

    # Register with the global registry if available
    if _registry is not None:
        try:
            _registry.register(instance)
        except ValueError as exc:
            sys.modules.pop(module_name, None)
            return {"loaded": False, "error": str(exc)}

    _loaded_local_plugins[name] = instance

    transformer_names = list(instance.transformers.keys())
    try:
        skill_names = list(instance.skills.keys())
    except Exception:
        skill_names = []

    return {
        "loaded": True,
        "name": name,
        "module": module_name,
        "transformers": transformer_names,
        "skills": skill_names,
    }


@skill(
    name="local_unload",
    description="Unload a local plugin from the registry.",
    category="local_plugins",
    tags=["local", "plugins", "unload"],
    side_effects=True,
)
def local_unload(name: str) -> dict:
    """Unload the local plugin *name* from the registry."""
    if name not in _loaded_local_plugins:
        return {"unloaded": False, "error": f"Plugin '{name}' is not loaded."}

    instance = _loaded_local_plugins.pop(name)

    # Unregister from the global registry
    if _registry is not None:
        _registry.unregister(instance.name)

    # Remove from sys.modules
    module_name = f"tukuy_local_plugin_{name}"
    sys.modules.pop(module_name, None)

    return {"unloaded": True, "name": name}


@skill(
    name="local_list",
    description="List all currently loaded local plugins with their capabilities.",
    category="local_plugins",
    tags=["local", "plugins", "list"],
    idempotent=True,
)
def local_list() -> dict:
    """Return all loaded local plugins with transformer/skill counts."""
    plugins: List[Dict[str, Any]] = []

    for name, instance in _loaded_local_plugins.items():
        transformer_names = list(instance.transformers.keys())
        try:
            skill_names = list(instance.skills.keys())
        except Exception:
            skill_names = []

        plugins.append({
            "name": name,
            "plugin_class": type(instance).__name__,
            "transformer_count": len(transformer_names),
            "transformers": transformer_names,
            "skill_count": len(skill_names),
            "skills": skill_names,
        })

    return {"plugins": plugins, "count": len(plugins)}


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------


class LocalPluginsPlugin(TransformerPlugin):
    """Plugin creator and local plugin lifecycle manager.

    Provides skills for generating, validating, discovering, loading,
    and unloading custom Tukuy plugins from ``~/.tukuy/plugins/``.
    """

    def __init__(self, registry: Optional[PluginRegistry] = None):
        super().__init__("local_plugins")
        self._registry = registry

    def initialize(self) -> None:
        global _registry
        if self._registry is not None:
            _registry = self._registry
        super().initialize()

    def cleanup(self) -> None:
        # Unload all local plugins
        for name in list(_loaded_local_plugins.keys()):
            local_unload(name)
        super().cleanup()

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "local_spec": local_spec.__skill__,
            "local_scaffold": local_scaffold.__skill__,
            "local_validate": local_validate.__skill__,
            "local_discover": local_discover.__skill__,
            "local_load": local_load.__skill__,
            "local_unload": local_unload.__skill__,
            "local_list": local_list.__skill__,
        }
