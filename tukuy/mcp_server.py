"""Tukuy MCP Server — expose plugins, skills, and transformers as MCP tools.

Uses a meta-tools pattern: 6 tools that let an LLM discover and invoke any
of Tukuy's capabilities dynamically, rather than registering hundreds of
individual tools.

Filtering — control which plugins are exposed via env vars or CLI flags::

    # Only expose specific plugins or groups (comma-separated)
    TUKUY_MCP_ONLY=numerical,text          python -m tukuy.mcp_server
    TUKUY_MCP_ONLY=Data,Core               python -m tukuy.mcp_server   # groups
    tukuy-mcp --only numerical,text

    # Exclude specific plugins or groups
    TUKUY_MCP_EXCLUDE=shell,file_ops       python -m tukuy.mcp_server
    TUKUY_MCP_EXCLUDE=Integrations         python -m tukuy.mcp_server   # group
    tukuy-mcp --exclude shell,file_ops

    # Combine: start from a group, then exclude some plugins
    TUKUY_MCP_ONLY=Data  TUKUY_MCP_EXCLUDE=sql  python -m tukuy.mcp_server

Values are matched against both plugin names (exact) and group names
(case-insensitive).  ``--only`` / ``TUKUY_MCP_ONLY`` is applied first,
then ``--exclude`` / ``TUKUY_MCP_EXCLUDE`` removes from that set.

Usage::

    # stdio transport (default for Claude Desktop / Claude Code)
    python -m tukuy.mcp_server

    # or via the installed script
    tukuy-mcp
"""

import json
import logging
import os
import sys
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "The 'mcp' package is required for the Tukuy MCP server.\n"
        "Install it with: pip install 'tukuy[mcp]'"
    )

# ---------------------------------------------------------------------------
# Logging — send to stderr so stdout stays clean for MCP stdio transport
# ---------------------------------------------------------------------------

logging.basicConfig(
    stream=sys.stderr,
    level=logging.WARNING,
    format="%(name)s %(levelname)s: %(message)s",
)
logger = logging.getLogger("tukuy.mcp")

# ---------------------------------------------------------------------------
# FastMCP instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "tukuy",
    instructions=(
        "Tukuy is a data transformation toolkit with plugins, skills, and transformers. "
        "Use tukuy_info for an overview, tukuy_search to find capabilities, "
        "tukuy_show for details, tukuy_run to execute skills, and tukuy_transform "
        "to apply transformers."
    ),
)

# ---------------------------------------------------------------------------
# Plugin filtering
# ---------------------------------------------------------------------------

# Populated at startup by _apply_filters(); empty means "no filtering".
_allowed_plugins: FrozenSet[str] = frozenset()


def _parse_csv_env(key: str) -> Set[str]:
    """Parse a comma-separated env var into a set of stripped tokens."""
    raw = os.environ.get(key, "")
    if not raw:
        return set()
    return {tok.strip() for tok in raw.split(",") if tok.strip()}


def _resolve_filter_tokens(tokens: Set[str]) -> Set[str]:
    """Expand a set of tokens that may be plugin names or group names.

    Returns a set of concrete plugin names.
    """
    from .plugins import BUILTIN_PLUGINS

    # Build group→plugins map once
    group_map: Dict[str, List[str]] = {}
    for pname in BUILTIN_PLUGINS:
        inst = BUILTIN_PLUGINS[pname]()
        grp = inst.manifest.group or "Ungrouped"
        group_map.setdefault(grp, []).append(pname)
        # Also index lowercase for case-insensitive matching
        group_map.setdefault(grp.lower(), []).append(pname)

    resolved: Set[str] = set()
    for tok in tokens:
        if tok in BUILTIN_PLUGINS:
            resolved.add(tok)
        else:
            # Try as group name (case-insensitive)
            matched = group_map.get(tok) or group_map.get(tok.lower())
            if matched:
                resolved.update(matched)
            else:
                logger.warning("Filter token '%s' matches no plugin or group — ignored", tok)
    return resolved


def _apply_filters(only_csv: str = "", exclude_csv: str = "") -> None:
    """Compute _allowed_plugins from env vars and/or CLI args.

    Args:
        only_csv: Comma-separated only list (CLI --only overrides env var).
        exclude_csv: Comma-separated exclude list (CLI --exclude overrides env var).
    """
    global _allowed_plugins
    from .plugins import BUILTIN_PLUGINS

    # Merge CLI args with env vars (CLI takes precedence if non-empty)
    only_tokens = {t.strip() for t in only_csv.split(",") if t.strip()} if only_csv else _parse_csv_env("TUKUY_MCP_ONLY")
    exclude_tokens = {t.strip() for t in exclude_csv.split(",") if t.strip()} if exclude_csv else _parse_csv_env("TUKUY_MCP_EXCLUDE")

    if not only_tokens and not exclude_tokens:
        _allowed_plugins = frozenset()  # empty = everything allowed
        return

    # Start with only-set or everything
    if only_tokens:
        base = _resolve_filter_tokens(only_tokens)
    else:
        base = set(BUILTIN_PLUGINS.keys())

    # Subtract excludes
    if exclude_tokens:
        excluded = _resolve_filter_tokens(exclude_tokens)
        base -= excluded

    _allowed_plugins = frozenset(base)
    logger.info("MCP plugin filter active: %d plugins allowed", len(_allowed_plugins))


def _is_plugin_allowed(plugin_name: str) -> bool:
    """Return True if this plugin passes the current filter."""
    if not _allowed_plugins:
        return True  # no filter = everything allowed
    return plugin_name in _allowed_plugins


# ---------------------------------------------------------------------------
# Lazy helpers (keep startup fast)
# ---------------------------------------------------------------------------


def _get_registry():
    from .registry import get_shared_registry
    return get_shared_registry()


def _get_unified():
    from .core.unified import get_unified_registry
    return get_unified_registry()


def _iter_plugins():
    """Yield (name, plugin_instance) for every allowed built-in plugin."""
    from .plugins import BUILTIN_PLUGINS
    for name in sorted(BUILTIN_PLUGINS):
        if not _is_plugin_allowed(name):
            continue
        cls = BUILTIN_PLUGINS[name]
        yield name, cls()


def _plugin_for_skill(skill_name: str) -> Optional[str]:
    """Return the plugin name that owns a skill, or None."""
    for pname, inst in _iter_plugins():
        if skill_name in inst.skills:
            return pname
    return None


def _plugin_for_transformer(transformer_name: str) -> Optional[str]:
    """Return the plugin name that owns a transformer, or None."""
    for pname, inst in _iter_plugins():
        if transformer_name in inst.transformers:
            return pname
    return None


def _coerce_types(kwargs: Dict[str, Any], properties: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce string values to the types declared in the JSON schema."""
    coerced = {}
    for key, value in kwargs.items():
        if key in properties and isinstance(value, str):
            ptype = properties[key].get("type", "string")
            if ptype == "integer":
                try:
                    value = int(value)
                except ValueError:
                    pass
            elif ptype == "number":
                try:
                    value = float(value)
                except ValueError:
                    pass
            elif ptype == "boolean":
                value = value.lower() in ("true", "1", "yes")
        coerced[key] = value
    return coerced


def _truncate(text: str, max_len: int = 80) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


# ---------------------------------------------------------------------------
# Tool 1: tukuy_info
# ---------------------------------------------------------------------------


@mcp.tool()
def tukuy_info() -> str:
    """Get a summary of all Tukuy capabilities: plugin, skill, transformer, and group counts."""
    total_plugins = 0
    total_transformers = 0
    total_skills = 0
    groups: Dict[str, Dict[str, int]] = {}

    for name, inst in _iter_plugins():
        total_plugins += 1
        total_transformers += len(inst.transformers)
        total_skills += len(inst.skills)
        grp = inst.manifest.group or "Ungrouped"
        if grp not in groups:
            groups[grp] = {"plugins": 0, "transformers": 0, "skills": 0}
        groups[grp]["plugins"] += 1
        groups[grp]["transformers"] += len(inst.transformers)
        groups[grp]["skills"] += len(inst.skills)

    lines = []
    if _allowed_plugins:
        lines.append(f"Filter active: {len(_allowed_plugins)} plugins allowed")
        lines.append("")
    lines += [
        f"Plugins:      {total_plugins}",
        f"Transformers: {total_transformers}",
        f"Skills:       {total_skills}",
        f"Groups:       {len(groups)}",
        "",
    ]
    for grp in sorted(groups):
        v = groups[grp]
        lines.append(f"  {grp}: {v['plugins']} plugins, {v['transformers']} transformers, {v['skills']} skills")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2: tukuy_browse
# ---------------------------------------------------------------------------


@mcp.tool()
def tukuy_browse(plugin: str = "", group: str = "") -> str:
    """Browse available plugins and their skills/transformers.

    Args:
        plugin: Filter by plugin name (optional).
        group: Filter by plugin group (optional).
    """
    lines = []
    for pname, inst in _iter_plugins():
        if plugin and pname != plugin:
            continue
        m = inst.manifest
        if group and (m.group or "").lower() != group.lower():
            continue

        lines.append(f"=== {m.display_name or pname} ({pname}) ===")
        lines.append(f"  Group: {m.group or '—'}")

        # Skills
        skills = inst.skills
        if skills:
            lines.append(f"  Skills ({len(skills)}):")
            for sname, skill_obj in sorted(skills.items()):
                d = skill_obj.descriptor
                risk = d.resolved_risk_level.value
                net = "net" if d.requires_network else ""
                desc = _truncate(d.description, 60)
                lines.append(f"    {sname:<28} [{risk}] {net:>3}  {desc}")

        # Transformers
        transformers = sorted(inst.transformers)
        if transformers:
            lines.append(f"  Transformers ({len(transformers)}):")
            for tname in transformers:
                lines.append(f"    {tname}")

        lines.append("")

    if not lines:
        return "No plugins found matching the filter."

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 3: tukuy_search
# ---------------------------------------------------------------------------


@mcp.tool()
def tukuy_search(query: str, limit: int = 20) -> str:
    """Search for skills and transformers by keyword.

    Searches names, tags, categories, and descriptions across both skills and transformers.

    Args:
        query: Search query (keywords).
        limit: Maximum number of results (default 20).
    """
    query_words = query.lower().split()
    if not query_words:
        return "No query provided."

    scored: List[tuple] = []  # (score, kind, name, plugin, description)

    # Collect allowed skill/transformer names from filtered plugins
    allowed_skills: Dict[str, Any] = {}  # name -> (descriptor, plugin_name)
    allowed_transformers: Set[str] = set()
    for pname, inst in _iter_plugins():
        for sname, skill_obj in inst.skills.items():
            allowed_skills[sname] = (skill_obj.descriptor, pname)
        for tname in inst.transformers:
            allowed_transformers.add(tname)

    # Search skills
    for sname, (d, pname) in allowed_skills.items():
        score = 0
        name_lower = sname.lower()
        tags_lower = {t.lower() for t in d.tags}
        cat_lower = d.category.lower()
        desc_lower = (d.description or "").lower()
        group_lower = (d.group or "").lower()

        for word in query_words:
            if word == name_lower:
                score += 10
            elif word in name_lower:
                score += 5
            if word in tags_lower:
                score += 3
            if word in cat_lower:
                score += 3
            if word in group_lower:
                score += 2
            if word in desc_lower:
                score += 1

        if score > 0:
            scored.append((score, "skill", sname, d.group or "", _truncate(d.description, 80)))

    # Search transformers
    unified = _get_unified()
    for tname in unified.get_all_transformers():
        if tname not in allowed_transformers:
            continue
        metadata = unified.get_transformer_metadata(tname)
        if metadata is None:
            continue

        score = 0
        name_lower = tname.lower()
        tags_lower = {t.lower() for t in (metadata.tags or set())}
        cat_lower = (
            metadata.category.value.lower()
            if hasattr(metadata.category, "value")
            else str(metadata.category).lower()
        )
        plugin_lower = (metadata.plugin or "").lower()
        desc_lower = (metadata.description or "").lower()

        for word in query_words:
            if word == name_lower:
                score += 10
            elif word in name_lower:
                score += 5
            if word in tags_lower:
                score += 3
            if word in cat_lower:
                score += 3
            if word in plugin_lower:
                score += 2
            if word in desc_lower:
                score += 1

        if score > 0:
            scored.append((score, "transformer", tname, metadata.plugin or "", _truncate(metadata.description, 80)))

    scored.sort(key=lambda x: -x[0])
    scored = scored[:limit]

    if not scored:
        return f"No results for '{query}'."

    lines = []
    for score, kind, name, plugin, desc in scored:
        lines.append(f"[{kind}] {name}  (plugin: {plugin}, score: {score})")
        if desc:
            lines.append(f"  {desc}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 4: tukuy_show
# ---------------------------------------------------------------------------


@mcp.tool()
def tukuy_show(name: str) -> str:
    """Show detailed information about a skill or transformer by name.

    Args:
        name: The exact name of the skill or transformer.
    """
    registry = _get_registry()

    # Try skill first
    skill_obj = registry.get_skill(name)
    if skill_obj is not None:
        if _allowed_plugins and _plugin_for_skill(name) is None:
            return f"Skill '{name}' is excluded by the current filter."
        return _format_skill(skill_obj)

    # Try transformer
    factory = registry.get_transformer(name)
    if factory is not None:
        if _allowed_plugins and _plugin_for_transformer(name) is None:
            return f"Transformer '{name}' is excluded by the current filter."
        return _format_transformer(name)

    return f"Not found: '{name}'. Use tukuy_search to find the correct name."


def _format_skill(skill_obj) -> str:
    d = skill_obj.descriptor
    lines = [
        f"Skill: {d.resolved_display_name}",
        f"Name:        {d.name}",
        f"Category:    {d.category}",
        f"Group:       {d.group or '—'}",
        f"Risk:        {d.resolved_risk_level.value}",
        f"Async:       {'yes' if d.is_async else 'no'}",
        f"Idempotent:  {'yes' if d.idempotent else 'no'}",
        f"Network:     {'yes' if d.requires_network else 'no'}",
        f"Tags:        {', '.join(d.tags) if d.tags else '—'}",
    ]
    if d.icon:
        lines.append(f"Icon:        {d.icon}")
    if d.description:
        lines.append("")
        lines.append(d.description)

    # Parameters from input_schema
    schema = d.input_schema
    if schema and schema.get("properties"):
        required = set(schema.get("required", []))
        lines.append("")
        lines.append("Parameters:")
        for pname, pschema in schema["properties"].items():
            req_str = " (required)" if pname in required else ""
            ptype = pschema.get("type", "any")
            desc = pschema.get("description", "")
            default = pschema.get("default")
            default_str = f" [default: {default}]" if default is not None else ""
            lines.append(f"  --{pname}  {ptype}  {desc}{req_str}{default_str}")

    # Examples
    if d.examples:
        lines.append("")
        lines.append("Examples:")
        for ex in d.examples:
            if ex.description:
                lines.append(f"  {ex.description}")
            lines.append(f"    Input:  {ex.input}")
            if ex.output is not None:
                lines.append(f"    Output: {ex.output}")

    # Config params
    if d.config_params:
        lines.append("")
        lines.append("Config:")
        for cp in d.config_params:
            default = f" (default: {cp.default})" if cp.default is not None else ""
            lines.append(f"  {cp.name}: {cp.type}{default}")

    return "\n".join(lines)


def _format_transformer(name: str) -> str:
    unified = _get_unified()
    details = unified.get_details(name)
    if not details:
        return f"Transformer '{name}' registered but no metadata available."

    info = details[0]
    lines = [
        f"Transformer: {info['name']}",
        f"Plugin:      {info.get('plugin', '—')}",
        f"Category:    {info.get('category', '—')}",
        f"Version:     {info.get('version', '—')}",
        f"Input type:  {info.get('input_type', '—')}",
        f"Output type: {info.get('output_type', '—')}",
    ]

    if info.get("description"):
        lines.append("")
        lines.append(info["description"])

    if info.get("tags"):
        lines.append("")
        lines.append(f"Tags: {', '.join(info['tags'])}")

    if info.get("parameters"):
        lines.append("")
        lines.append("Parameters:")
        for p in info["parameters"]:
            req_str = " (required)" if p.get("required") else ""
            default_str = f" [default: {p['default']}]" if p.get("default") is not None else ""
            lines.append(f"  {p['name']}  {p.get('type', 'any')}  {p.get('description', '')}{req_str}{default_str}")

    if info.get("examples"):
        lines.append("")
        lines.append("Examples:")
        for ex in info["examples"]:
            lines.append(f"  {ex}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 5: tukuy_run
# ---------------------------------------------------------------------------


@mcp.tool()
async def tukuy_run(name: str, params: str = "{}") -> str:
    """Run a Tukuy skill by name with the given parameters.

    Args:
        name: The skill name (use tukuy_search or tukuy_browse to find names).
        params: JSON object of keyword arguments for the skill (default "{}").
    """
    registry = _get_registry()
    skill_obj = registry.get_skill(name)
    if skill_obj is None:
        # Suggest close matches (only from allowed plugins)
        allowed = {sn for pn, inst in _iter_plugins() for sn in inst.skills}
        matches = [s for s in allowed if name.lower() in s.lower()]
        msg = f"Skill not found: '{name}'."
        if matches:
            msg += f" Did you mean: {', '.join(sorted(matches)[:5])}?"
        return msg

    # Check filter
    if _allowed_plugins and _plugin_for_skill(name) is None:
        return f"Skill '{name}' is excluded by the current filter."

    # Parse params
    try:
        kwargs = json.loads(params) if isinstance(params, str) else params
    except json.JSONDecodeError as e:
        return f"Invalid JSON in params: {e}"

    if not isinstance(kwargs, dict):
        return "params must be a JSON object."

    # Coerce types based on input_schema
    schema = skill_obj.descriptor.input_schema
    if schema and schema.get("properties"):
        kwargs = _coerce_types(kwargs, schema["properties"])

    # Run via ainvoke (handles both sync and async skills)
    result = await skill_obj.ainvoke(**kwargs, policy=None)

    if result.success:
        return _format_result(result.value, result.duration_ms)
    else:
        msg = f"Error: {result.error}"
        if result.duration_ms:
            msg += f" ({result.duration_ms:.0f}ms)"
        if result.retryable:
            msg += " [retryable]"
        return msg


def _format_result(value: Any, duration_ms: Optional[float] = None) -> str:
    lines = []
    if isinstance(value, dict):
        display = {k: v for k, v in value.items() if not k.startswith("_")}
        display.pop("success", None)
        for key, val in display.items():
            if isinstance(val, (list, dict)):
                lines.append(f"{key}: {json.dumps(val, indent=2, default=str)}")
            else:
                lines.append(f"{key}: {val}")
    elif isinstance(value, (list, tuple)):
        lines.append(json.dumps(value, indent=2, default=str))
    else:
        lines.append(str(value))

    if duration_ms is not None:
        lines.append(f"({duration_ms:.0f}ms)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 6: tukuy_transform
# ---------------------------------------------------------------------------


@mcp.tool()
def tukuy_transform(name: str, input: str, params: str = "{}") -> str:
    """Apply a Tukuy transformer to input text.

    Args:
        name: The transformer name (use tukuy_search or tukuy_browse to find names).
        input: The input value to transform.
        params: JSON object of extra parameters for the transformer (default "{}").
    """
    registry = _get_registry()
    factory = registry.get_transformer(name)
    if factory is None:
        # Suggest close matches (only from allowed plugins)
        allowed = {tn for pn, inst in _iter_plugins() for tn in inst.transformers}
        matches = [t for t in allowed if name.lower() in t.lower()]
        msg = f"Transformer not found: '{name}'."
        if matches:
            msg += f" Did you mean: {', '.join(sorted(matches)[:5])}?"
        return msg

    # Check filter
    if _allowed_plugins and _plugin_for_transformer(name) is None:
        return f"Transformer '{name}' is excluded by the current filter."

    # Parse params
    try:
        extra = json.loads(params) if isinstance(params, str) else params
    except json.JSONDecodeError as e:
        return f"Invalid JSON in params: {e}"

    if not isinstance(extra, dict):
        return "params must be a JSON object."

    transformer = factory(extra)

    # Validate and transform — try numeric coercion if string validation fails
    input_value: Any = input
    if not transformer.validate(input_value):
        try:
            numeric = float(input) if "." in input else int(input)
            if transformer.validate(numeric):
                input_value = numeric
            else:
                return f"Input validation failed for transformer '{name}'."
        except ValueError:
            return f"Input validation failed for transformer '{name}'."

    result = transformer.transform(input_value)
    if result.success:
        val = result.value
        if isinstance(val, (dict, list)):
            return json.dumps(val, indent=2, default=str)
        return str(val)
    else:
        return f"Error: {result.error}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the Tukuy MCP server with stdio transport."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="tukuy-mcp",
        description="Tukuy MCP server — expose plugins as MCP tools",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Comma-separated plugin names or group names to expose (default: all)",
    )
    parser.add_argument(
        "--exclude",
        default="",
        help="Comma-separated plugin names or group names to hide",
    )
    args = parser.parse_args()

    _apply_filters(only_csv=args.only, exclude_csv=args.exclude)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
