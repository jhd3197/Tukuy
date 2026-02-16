"""
Tukuy Skills Showcase — powered by Cacao.

An interactive web UI that discovers all Tukuy plugins and skills at runtime
and presents them in a browsable admin-style dashboard.

Run:
    cacao run tukuy_showcase.py
"""

import sys
import cacao as c

# ---------------------------------------------------------------------------
# Cacao app configuration
# ---------------------------------------------------------------------------

c.config(title="Tukuy Skills Showcase", theme="dark")

# ---------------------------------------------------------------------------
# Discover Tukuy plugins at import time
# ---------------------------------------------------------------------------

from tukuy.registry import get_shared_registry

registry = get_shared_registry()

# Build a structured catalog: group -> list of plugin dicts
_catalog: dict[str, list[dict]] = {}

for name, plugin in registry.plugins.items():
    manifest = plugin.manifest
    group = manifest.group or "Other"

    transformers = {}
    try:
        transformers = plugin.transformers or {}
    except Exception:
        pass

    skills = {}
    try:
        skills = plugin.skills or {}
    except Exception:
        pass

    entry = {
        "name": manifest.name,
        "display_name": manifest.display_name,
        "description": manifest.description,
        "icon": manifest.icon,
        "color": manifest.color,
        "group": group,
        "version": manifest.version,
        "experimental": manifest.experimental,
        "deprecated": manifest.deprecated,
        "requires": manifest.requires.to_dict(),
        "transformer_names": sorted(transformers.keys()),
        "skill_names": sorted(skills.keys()),
        "skill_descriptors": {},
    }

    # Collect skill descriptor metadata
    for sname, skill_obj in skills.items():
        desc = skill_obj.descriptor
        entry["skill_descriptors"][sname] = {
            "display_name": desc.resolved_display_name,
            "description": desc.description,
            "category": desc.category,
            "risk_level": desc.resolved_risk_level.value,
            "tags": desc.tags,
            "is_async": desc.is_async,
            "requires_network": desc.requires_network,
            "requires_filesystem": desc.requires_filesystem,
            "input_schema": desc.input_schema,
            "output_schema": desc.output_schema,
        }

    _catalog.setdefault(group, []).append(entry)

# Sort plugins alphabetically within each group
for group in _catalog:
    _catalog[group].sort(key=lambda p: p["display_name"])

# Define a consistent group ordering
GROUP_ORDER = [
    "Core",
    "Data",
    "Web",
    "Code",
    "Integrations",
    "Documents",
    "Media",
    "Prompt Engineering",
    "Other",
]

ordered_groups = [g for g in GROUP_ORDER if g in _catalog]
# Append any groups not in our predefined order
for g in sorted(_catalog.keys()):
    if g not in ordered_groups:
        ordered_groups.append(g)

# Icon mapping for groups
GROUP_ICONS = {
    "Core": "layers",
    "Data": "database",
    "Web": "globe",
    "Code": "code",
    "Integrations": "plug",
    "Documents": "file-text",
    "Media": "image",
    "Prompt Engineering": "message-square",
    "Other": "package",
}

# Risk level badge colors
RISK_COLORS = {
    "safe": "success",
    "moderate": "warning",
    "dangerous": "danger",
    "critical": "danger",
}

# ---------------------------------------------------------------------------
# Summary stats
# ---------------------------------------------------------------------------

total_plugins = sum(len(plugins) for plugins in _catalog.values())
total_transformers = sum(
    len(p["transformer_names"])
    for plugins in _catalog.values()
    for p in plugins
)
total_skills = sum(
    len(p["skill_names"])
    for plugins in _catalog.values()
    for p in plugins
)

# ---------------------------------------------------------------------------
# Build the UI
# ---------------------------------------------------------------------------

with c.app_shell(brand="Tukuy Skills", default="overview"):

    # -- Sidebar navigation --------------------------------------------------
    with c.nav_sidebar():
        c.nav_item("Overview", key="overview", icon="home")

        for group in ordered_groups:
            plugins = _catalog[group]
            icon = GROUP_ICONS.get(group, "package")
            with c.nav_group(group, icon=icon):
                for plugin in plugins:
                    p_icon = plugin["icon"] or "box"
                    badge_text = None
                    n_items = len(plugin["transformer_names"]) + len(plugin["skill_names"])
                    if n_items:
                        badge_text = str(n_items)
                    c.nav_item(
                        plugin["display_name"],
                        key=plugin["name"],
                        icon=p_icon,
                        badge=badge_text,
                    )

    # -- Main content ---------------------------------------------------------
    with c.shell_content():

        # ── Overview panel ──────────────────────────────────────────────────
        with c.nav_panel("overview"):
            c.title("Tukuy Skills Showcase")
            c.text(
                "Browse every plugin, transformer, and skill registered in Tukuy. "
                "This dashboard is auto-generated from the live plugin registry.",
                color="muted",
            )
            c.spacer()

            # KPI row
            with c.row():
                c.metric("Plugins", total_plugins)
                c.metric("Transformers", total_transformers)
                c.metric("Skills", total_skills)
                c.metric("Groups", len(ordered_groups))

            c.spacer()

            # Group summary table
            group_rows = []
            for group in ordered_groups:
                plugins = _catalog[group]
                t_count = sum(len(p["transformer_names"]) for p in plugins)
                s_count = sum(len(p["skill_names"]) for p in plugins)
                group_rows.append({
                    "Group": group,
                    "Plugins": len(plugins),
                    "Transformers": t_count,
                    "Skills": s_count,
                })

            with c.card("Groups"):
                c.table(
                    group_rows,
                    columns=["Group", "Plugins", "Transformers", "Skills"],
                    searchable=True,
                )

            c.spacer()

            # Full plugin catalog table
            all_plugins_table = []
            for group in ordered_groups:
                for p in _catalog[group]:
                    requires_tags = []
                    if p["requires"].get("filesystem"):
                        requires_tags.append("filesystem")
                    if p["requires"].get("network"):
                        requires_tags.append("network")
                    all_plugins_table.append({
                        "Plugin": p["display_name"],
                        "Group": group,
                        "Transformers": len(p["transformer_names"]),
                        "Skills": len(p["skill_names"]),
                        "Requires": ", ".join(requires_tags) if requires_tags else "-",
                        "Version": p["version"],
                    })

            with c.card("All Plugins"):
                c.table(
                    all_plugins_table,
                    columns=["Plugin", "Group", "Transformers", "Skills", "Requires", "Version"],
                    searchable=True,
                    page_size=15,
                )

        # ── Per-plugin panels ───────────────────────────────────────────────
        for group in ordered_groups:
            for plugin in _catalog[group]:
                with c.nav_panel(plugin["name"]):
                    # Header
                    c.title(plugin["display_name"])
                    if plugin["description"]:
                        c.text(plugin["description"], color="muted")

                    c.spacer(size=2)

                    # Badges row
                    with c.row(gap=2, wrap=True):
                        c.badge(group, color="primary")
                        c.badge(f"v{plugin['version']}", color="info")
                        if plugin["experimental"]:
                            c.badge("Experimental", color="warning")
                        if plugin["deprecated"]:
                            c.badge("Deprecated", color="danger")
                        if plugin["requires"].get("filesystem"):
                            c.badge("Filesystem", color="warning")
                        if plugin["requires"].get("network"):
                            c.badge("Network", color="warning")
                        imports = plugin["requires"].get("imports", [])
                        for imp in imports:
                            c.badge(imp, color="info")

                    c.spacer()

                    # Quick stats
                    with c.row():
                        c.metric("Transformers", len(plugin["transformer_names"]))
                        c.metric("Skills", len(plugin["skill_names"]))

                    c.spacer()

                    # Tabs for transformers and skills
                    has_transformers = bool(plugin["transformer_names"])
                    has_skills = bool(plugin["skill_names"])

                    if has_transformers or has_skills:
                        default_tab = "transformers" if has_transformers else "skills"
                        with c.tabs(default=default_tab):

                            # Transformers tab
                            if has_transformers:
                                with c.tab("transformers", "Transformers"):
                                    transformer_rows = [
                                        {"Name": t, "Type": "transformer"}
                                        for t in plugin["transformer_names"]
                                    ]
                                    c.table(
                                        transformer_rows,
                                        columns=["Name", "Type"],
                                        searchable=True,
                                    )

                            # Skills tab
                            if has_skills:
                                with c.tab("skills", "Skills"):
                                    for sname in plugin["skill_names"]:
                                        sd = plugin["skill_descriptors"].get(sname, {})
                                        with c.card(sd.get("display_name", sname)):
                                            if sd.get("description"):
                                                c.text(sd["description"], size="sm")
                                            c.spacer(size=1)

                                            with c.row(gap=2, wrap=True):
                                                risk = sd.get("risk_level", "safe")
                                                risk_color = RISK_COLORS.get(risk, "default")
                                                c.badge(risk, color=risk_color)
                                                if sd.get("is_async"):
                                                    c.badge("async", color="info")
                                                if sd.get("requires_network"):
                                                    c.badge("network", color="warning")
                                                if sd.get("requires_filesystem"):
                                                    c.badge("filesystem", color="warning")
                                                for tag in sd.get("tags", []):
                                                    c.badge(tag, color="default")

                                            # Show input schema if available
                                            if sd.get("input_schema"):
                                                c.spacer(size=1)
                                                c.text("Input Schema", size="sm", color="muted")
                                                c.json(sd["input_schema"], expanded=False)

                    else:
                        c.alert(
                            "This plugin provides no transformers or skills.",
                            type="info",
                        )
