"""Tukuy CLI — inspect plugins, run skills, and apply transformers from the terminal.

Usage::

    tukuy info                                    # summary stats
    tukuy list plugins                            # list all plugins
    tukuy list skills                             # list all skills
    tukuy list skills --plugin country            # filter by plugin
    tukuy list transformers                       # list all transformers
    tukuy list groups                             # list plugin groups

    tukuy show plugin country                     # detailed plugin info
    tukuy show skill crypto_price                 # detailed skill info

    tukuy run word_define --word hello            # run a skill
    tukuy run crypto_price --coins bitcoin        # run with params
    tukuy run public_holidays --country_code US   # run with params

    tukuy transform lower "HELLO WORLD"           # apply a transformer
    echo "HELLO" | tukuy transform lower          # pipe input
"""

import argparse
import asyncio
import inspect
import json
import sys
from typing import Any, Dict, List, Optional


def _get_registry():
    """Get the shared plugin registry (lazy import to keep CLI startup fast)."""
    from .registry import get_shared_registry
    return get_shared_registry()


def _iter_plugins():
    """Yield (name, plugin_instance) for every built-in plugin."""
    from .plugins import BUILTIN_PLUGINS
    for name in sorted(BUILTIN_PLUGINS):
        cls = BUILTIN_PLUGINS[name]
        yield name, cls()


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------


def cmd_info(args):
    """Print a high-level summary of plugins, transformers, skills, groups."""
    total_plugins = 0
    total_transformers = 0
    total_skills = 0
    groups = set()
    categories = set()

    for name, inst in _iter_plugins():
        total_plugins += 1
        total_transformers += len(inst.transformers)
        total_skills += len(inst.skills)
        m = inst.manifest
        if m.group:
            groups.add(m.group)
        for s in inst.skills.values():
            categories.add(s.descriptor.category)

    print(f"  Plugins:      {total_plugins}")
    print(f"  Transformers: {total_transformers}")
    print(f"  Skills:       {total_skills}")
    print(f"  Groups:       {len(groups)}")
    print()
    print(f"  Groups: {', '.join(sorted(groups))}")


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def cmd_list(args):
    """List plugins, skills, transformers, or groups."""
    what = args.what

    if what == "plugins":
        _list_plugins(args)
    elif what == "skills":
        _list_skills(args)
    elif what == "transformers":
        _list_transformers(args)
    elif what == "groups":
        _list_groups(args)
    else:
        print(f"Unknown list target: {what}", file=sys.stderr)
        print("Choose from: plugins, skills, transformers, groups", file=sys.stderr)
        sys.exit(1)


def _list_plugins(args):
    group_filter = getattr(args, "group", None)

    rows = []
    for name, inst in _iter_plugins():
        m = inst.manifest
        if group_filter and (m.group or "").lower() != group_filter.lower():
            continue
        t = len(inst.transformers)
        s = len(inst.skills)
        rows.append((name, m.display_name or name, t, s, m.group or "—"))

    if getattr(args, "json", False):
        print(json.dumps([{"name": r[0], "display_name": r[1], "transformers": r[2], "skills": r[3], "group": r[4]} for r in rows], indent=2))
        return

    # Table output
    hdr = f"  {'Name':<22} {'Display Name':<26} {'T':>3} {'S':>3}  {'Group'}"
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))
    for name, display, t, s, grp in rows:
        print(f"  {name:<22} {display:<26} {t:>3} {s:>3}  {grp}")
    print()
    print(f"  {len(rows)} plugins")


def _list_skills(args):
    plugin_filter = getattr(args, "plugin", None)
    tag_filter = getattr(args, "tag", None)
    group_filter = getattr(args, "group", None)

    rows = []
    for pname, inst in _iter_plugins():
        if plugin_filter and pname != plugin_filter:
            continue
        m = inst.manifest
        if group_filter and (m.group or "").lower() != group_filter.lower():
            continue
        for sname, skill_obj in inst.skills.items():
            d = skill_obj.descriptor
            if tag_filter and tag_filter.lower() not in d.tags:
                continue
            risk = d.resolved_risk_level.value
            rows.append((sname, d.resolved_display_name, pname, d.category, risk, d.requires_network))

    if getattr(args, "json", False):
        print(json.dumps([{"name": r[0], "display_name": r[1], "plugin": r[2], "category": r[3], "risk": r[4], "network": r[5]} for r in rows], indent=2))
        return

    hdr = f"  {'Skill':<28} {'Plugin':<18} {'Risk':<10} {'Net':>3}"
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))
    for sname, display, pname, cat, risk, net in rows:
        net_str = "yes" if net else "—"
        print(f"  {sname:<28} {pname:<18} {risk:<10} {net_str:>3}")
    print()
    print(f"  {len(rows)} skills")


def _list_transformers(args):
    plugin_filter = getattr(args, "plugin", None)

    rows = []
    for pname, inst in _iter_plugins():
        if plugin_filter and pname != plugin_filter:
            continue
        for tname in sorted(inst.transformers):
            rows.append((tname, pname, inst.manifest.group or "—"))

    if getattr(args, "json", False):
        print(json.dumps([{"name": r[0], "plugin": r[1], "group": r[2]} for r in rows], indent=2))
        return

    hdr = f"  {'Transformer':<30} {'Plugin':<18} {'Group'}"
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))
    for tname, pname, grp in rows:
        print(f"  {tname:<30} {pname:<18} {grp}")
    print()
    print(f"  {len(rows)} transformers")


def _list_groups(args):
    groups: Dict[str, Dict[str, int]] = {}
    for name, inst in _iter_plugins():
        m = inst.manifest
        grp = m.group or "Ungrouped"
        if grp not in groups:
            groups[grp] = {"plugins": 0, "transformers": 0, "skills": 0}
        groups[grp]["plugins"] += 1
        groups[grp]["transformers"] += len(inst.transformers)
        groups[grp]["skills"] += len(inst.skills)

    if getattr(args, "json", False):
        print(json.dumps({g: v for g, v in sorted(groups.items())}, indent=2))
        return

    hdr = f"  {'Group':<18} {'Plugins':>8} {'Transformers':>13} {'Skills':>7}"
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))
    for grp in sorted(groups):
        v = groups[grp]
        print(f"  {grp:<18} {v['plugins']:>8} {v['transformers']:>13} {v['skills']:>7}")
    print()
    print(f"  {len(groups)} groups")


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


def cmd_show(args):
    """Show detailed info about a plugin or skill."""
    what = args.what
    name = args.name

    if what == "plugin":
        _show_plugin(name)
    elif what == "skill":
        _show_skill(name)
    else:
        print(f"Unknown show target: {what}. Choose: plugin, skill", file=sys.stderr)
        sys.exit(1)


def _show_plugin(name: str):
    from .plugins import BUILTIN_PLUGINS
    if name not in BUILTIN_PLUGINS:
        print(f"Plugin not found: {name}", file=sys.stderr)
        print(f"Available: {', '.join(sorted(BUILTIN_PLUGINS))}", file=sys.stderr)
        sys.exit(1)

    cls = BUILTIN_PLUGINS[name]
    inst = cls()
    m = inst.manifest

    print(f"  Plugin: {m.display_name or name}")
    print(f"  Name:   {name}")
    print(f"  Group:  {m.group or '—'}")
    print(f"  Icon:   {m.icon or '—'}")
    print(f"  Desc:   {m.description or '—'}")
    if hasattr(m, "requires") and m.requires:
        req = m.requires
        parts = []
        if req.network:
            parts.append("network")
        if req.imports:
            parts.append(f"imports: {', '.join(req.imports)}")
        if parts:
            print(f"  Needs:  {'; '.join(parts)}")
    print()

    transformers = sorted(inst.transformers)
    if transformers:
        print(f"  Transformers ({len(transformers)}):")
        for t in transformers:
            print(f"    - {t}")
        print()

    skills = inst.skills
    if skills:
        print(f"  Skills ({len(skills)}):")
        for sname, skill_obj in sorted(skills.items()):
            d = skill_obj.descriptor
            print(f"    - {sname:<28} {d.resolved_display_name}")
            if d.description:
                # Wrap long descriptions
                desc = d.description[:80] + ("..." if len(d.description) > 80 else "")
                print(f"      {desc}")
        print()


def _show_skill(name: str):
    registry = _get_registry()
    skill_obj = registry.get_skill(name)
    if skill_obj is None:
        print(f"Skill not found: {name}", file=sys.stderr)
        # Suggest close matches
        all_skills = list(registry.skills.keys())
        matches = [s for s in all_skills if name.lower() in s.lower()]
        if matches:
            print(f"Did you mean: {', '.join(matches[:5])}", file=sys.stderr)
        sys.exit(1)

    d = skill_obj.descriptor
    print(f"  Skill:       {d.resolved_display_name}")
    print(f"  Name:        {d.name}")
    print(f"  Category:    {d.category}")
    print(f"  Group:       {d.group or '—'}")
    print(f"  Risk:        {d.resolved_risk_level.value}")
    print(f"  Async:       {'yes' if d.is_async else 'no'}")
    print(f"  Idempotent:  {'yes' if d.idempotent else 'no'}")
    print(f"  Network:     {'yes' if d.requires_network else 'no'}")
    print(f"  Tags:        {', '.join(d.tags) if d.tags else '—'}")
    if d.icon:
        print(f"  Icon:        {d.icon}")
    print()
    if d.description:
        print(f"  {d.description}")
        print()

    # Show parameters from input_schema
    schema = d.input_schema
    if schema and schema.get("properties"):
        required = set(schema.get("required", []))
        print("  Parameters:")
        for pname, pschema in schema["properties"].items():
            req_str = " (required)" if pname in required else ""
            ptype = pschema.get("type", "any")
            desc = pschema.get("description", "")
            print(f"    --{pname:<20} {ptype:<10} {desc}{req_str}")
        print()

    # Config params
    if d.config_params:
        print("  Config:")
        for cp in d.config_params:
            default = f" (default: {cp.default})" if cp.default is not None else ""
            print(f"    {cp.name}: {cp.type}{default}")
        print()


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


def cmd_run(args):
    """Run a skill by name with keyword arguments."""
    skill_name = args.skill_name
    registry = _get_registry()
    skill_obj = registry.get_skill(skill_name)

    if skill_obj is None:
        print(f"Skill not found: {skill_name}", file=sys.stderr)
        all_skills = list(registry.skills.keys())
        matches = [s for s in all_skills if skill_name.lower() in s.lower()]
        if matches:
            print(f"Did you mean: {', '.join(matches[:5])}", file=sys.stderr)
        sys.exit(1)

    # Parse extra --key value pairs from remaining args
    kwargs = _parse_extra_args(args.extra)

    # Coerce types based on input_schema
    schema = skill_obj.descriptor.input_schema
    if schema and schema.get("properties"):
        kwargs = _coerce_types(kwargs, schema["properties"])

    # Run the skill
    if skill_obj.descriptor.is_async:
        result = asyncio.run(skill_obj.ainvoke(**kwargs, policy=None))
    else:
        result = skill_obj.invoke(**kwargs, policy=None)

    # Output
    if getattr(args, "raw", False):
        if result.success:
            print(json.dumps(result.value, indent=2, default=str))
        else:
            print(json.dumps({"error": result.error}, indent=2), file=sys.stderr)
            sys.exit(1)
    else:
        if result.success:
            _pretty_print_result(result.value, result.duration_ms)
        else:
            print(f"  Error: {result.error}", file=sys.stderr)
            if result.duration_ms:
                print(f"  ({result.duration_ms:.0f}ms)", file=sys.stderr)
            sys.exit(1)


def _parse_extra_args(extra: List[str]) -> Dict[str, Any]:
    """Parse ['--key', 'value', '--flag', ...] into a dict."""
    kwargs = {}
    i = 0
    while i < len(extra):
        arg = extra[i]
        if arg.startswith("--"):
            key = arg[2:].replace("-", "_")
            # Check if next arg is a value or another flag
            if i + 1 < len(extra) and not extra[i + 1].startswith("--"):
                kwargs[key] = extra[i + 1]
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            i += 1
    return kwargs


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


def _pretty_print_result(value: Any, duration_ms: Optional[float] = None):
    """Pretty-print a skill result."""
    if isinstance(value, dict):
        # Remove internal keys
        display = {k: v for k, v in value.items() if not k.startswith("_")}
        success = display.pop("success", None)

        for key, val in display.items():
            if isinstance(val, (list, dict)):
                print(f"  {key}:")
                formatted = json.dumps(val, indent=4, default=str)
                for line in formatted.split("\n"):
                    print(f"    {line}")
            else:
                print(f"  {key}: {val}")

        if duration_ms is not None:
            print()
            print(f"  ({duration_ms:.0f}ms)")
    elif isinstance(value, list):
        print(json.dumps(value, indent=2, default=str))
    else:
        print(value)


# ---------------------------------------------------------------------------
# transform
# ---------------------------------------------------------------------------


def cmd_transform(args):
    """Apply a transformer to input text."""
    transformer_name = args.transformer_name
    registry = _get_registry()

    factory = registry.get_transformer(transformer_name)
    if factory is None:
        print(f"Transformer not found: {transformer_name}", file=sys.stderr)
        all_t = list(registry.transformers.keys())
        matches = [t for t in all_t if transformer_name.lower() in t.lower()]
        if matches:
            print(f"Did you mean: {', '.join(matches[:5])}", file=sys.stderr)
        sys.exit(1)

    # Get input: positional arg or stdin
    input_text = args.input
    if input_text is None:
        if not sys.stdin.isatty():
            input_text = sys.stdin.read().rstrip("\n")
        else:
            print("No input provided. Pass as argument or pipe via stdin.", file=sys.stderr)
            sys.exit(1)

    # Build the transformer
    params = _parse_extra_args(args.extra) if args.extra else {}
    transformer = factory(params)

    # Validate and transform
    if not transformer.validate(input_text):
        # Try numeric input
        try:
            numeric = float(input_text) if "." in input_text else int(input_text)
            if transformer.validate(numeric):
                input_text = numeric
            else:
                print(f"Input validation failed for transformer '{transformer_name}'.", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print(f"Input validation failed for transformer '{transformer_name}'.", file=sys.stderr)
            sys.exit(1)

    result = transformer.transform(input_text)
    if result.success:
        print(result.value)
    else:
        print(f"Error: {result.error}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tukuy",
        description="Tukuy — data transformation toolkit",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command")

    # --- info ---
    sub.add_parser("info", help="Show summary stats")

    # --- list ---
    p_list = sub.add_parser("list", help="List plugins, skills, transformers, or groups")
    p_list.add_argument("what", choices=["plugins", "skills", "transformers", "groups"])
    p_list.add_argument("--plugin", help="Filter by plugin name")
    p_list.add_argument("--group", help="Filter by group name")
    p_list.add_argument("--tag", help="Filter skills by tag")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")

    # --- show ---
    p_show = sub.add_parser("show", help="Show detailed info about a plugin or skill")
    p_show.add_argument("what", choices=["plugin", "skill"])
    p_show.add_argument("name", help="Name of the plugin or skill")

    # --- run ---
    p_run = sub.add_parser("run", help="Run a skill")
    p_run.add_argument("skill_name", help="Name of the skill to run")
    p_run.add_argument("--raw", action="store_true", help="Output raw JSON")
    p_run.add_argument("extra", nargs=argparse.REMAINDER, help="Skill params as --key value")

    # --- transform ---
    p_transform = sub.add_parser("transform", help="Apply a transformer to input")
    p_transform.add_argument("transformer_name", help="Name of the transformer")
    p_transform.add_argument("input", nargs="?", default=None, help="Input value (or pipe via stdin)")
    p_transform.add_argument("extra", nargs=argparse.REMAINDER, help="Transformer params as --key value")

    return parser


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from . import __version__
        print(f"tukuy {__version__}")
        return

    if args.command is None:
        parser.print_help()
        return

    commands = {
        "info": cmd_info,
        "list": cmd_list,
        "show": cmd_show,
        "run": cmd_run,
        "transform": cmd_transform,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
