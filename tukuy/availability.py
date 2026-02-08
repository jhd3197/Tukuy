"""Tool availability engine for Tukuy.

Answers the question: "Given the current SecurityContext + SafetyPolicy,
which tools can this user actually use?"

Usage::

    from tukuy.availability import get_available_skills, discover_plugins

    availability = get_available_skills(
        plugins=all_plugins,
        policy=bot_safety_policy,
        security_context=workspace_security_context,
    )

    # Filter to only available tools
    active_tools = [a.skill for a in availability if a.available]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .manifest import PluginManifest
    from .plugins.base import TransformerPlugin
    from .safety import SafetyPolicy, SecurityContext
    from .skill import Skill


class AvailabilityReason(str, Enum):
    """Why a skill or plugin is (un)available."""

    ALLOWED = "allowed"
    POLICY_BLOCKED = "policy_blocked"
    SECURITY_RESTRICTED = "security_restricted"
    MISSING_DEPENDENCY = "missing_dependency"
    PLATFORM_UNSUPPORTED = "platform_unsupported"
    DEPRECATED = "deprecated"


@dataclass
class SkillAvailability:
    """Whether a skill is available and why/why not."""

    skill: Skill
    available: bool
    reason: Optional[str] = None
    reason_code: AvailabilityReason = AvailabilityReason.ALLOWED
    restrictions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "name": self.skill.descriptor.name,
            "available": self.available,
        }
        if self.reason is not None:
            d["reason"] = self.reason
        d["reasonCode"] = self.reason_code.value
        if self.restrictions:
            d["restrictions"] = self.restrictions
        return d


@dataclass
class PluginDiscoveryResult:
    """Result of discovering a plugin's availability."""

    plugin: TransformerPlugin
    manifest: PluginManifest
    available: bool
    reason: Optional[str] = None
    reason_code: AvailabilityReason = AvailabilityReason.ALLOWED
    skill_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = self.manifest.to_dict()
        d["available"] = self.available
        if self.reason is not None:
            d["reason"] = self.reason
        d["reasonCode"] = self.reason_code.value
        d["skillCount"] = self.skill_count
        return d


def get_available_skills(
    plugins: List[TransformerPlugin],
    *,
    policy: Optional[SafetyPolicy] = None,
    security_context: Optional[SecurityContext] = None,
    check_imports: bool = False,
) -> List[SkillAvailability]:
    """Return availability status for all skills across given plugins.

    Checks each skill's requirements against the active policy and security
    context.

    Parameters
    ----------
    plugins
        List of plugins to check skills from.
    policy
        Safety policy to validate against.  ``None`` = unrestricted.
    security_context
        Security context for scoped restrictions.  ``None`` = unrestricted.
    check_imports
        If ``True``, verify that ``required_imports`` are importable.
    """
    results: List[SkillAvailability] = []

    for plugin in plugins:
        for _name, skill_obj in plugin.skills.items():
            desc = skill_obj.descriptor
            available = True
            reason: Optional[str] = None
            reason_code = AvailabilityReason.ALLOWED
            restrictions: List[str] = []

            # Check SafetyPolicy
            if policy and available:
                if desc.requires_network and not policy.allow_network:
                    available = False
                    reason = "Network access is disabled by safety policy"
                    reason_code = AvailabilityReason.POLICY_BLOCKED
                if desc.requires_filesystem and not policy.allow_filesystem:
                    available = False
                    reason = "Filesystem access is disabled by safety policy"
                    reason_code = AvailabilityReason.POLICY_BLOCKED

            # Check SecurityContext restrictions (tool is available but scoped)
            if security_context and available:
                if desc.requires_filesystem:
                    if security_context.allowed_read_paths is not None:
                        restrictions.append(
                            f"Read access limited to: {', '.join(security_context.allowed_read_paths)}"
                        )
                    if security_context.allowed_write_paths is not None:
                        restrictions.append(
                            f"Write access limited to: {', '.join(security_context.allowed_write_paths)}"
                        )
                if desc.requires_network:
                    if security_context.allowed_hosts is not None:
                        restrictions.append(
                            f"Network limited to: {', '.join(security_context.allowed_hosts)}"
                        )

            # Check imports
            if check_imports and available and desc.required_imports:
                for imp in desc.required_imports:
                    try:
                        __import__(imp)
                    except ImportError:
                        available = False
                        reason = f"Missing dependency: {imp}"
                        reason_code = AvailabilityReason.MISSING_DEPENDENCY
                        break

            results.append(SkillAvailability(
                skill=skill_obj,
                available=available,
                reason=reason,
                reason_code=reason_code,
                restrictions=restrictions,
            ))

    return results


def discover_plugins(
    plugins: List[TransformerPlugin],
    *,
    policy: Optional[SafetyPolicy] = None,
    check_requirements: bool = True,
) -> List[PluginDiscoveryResult]:
    """Discover all plugins with availability based on current environment.

    Parameters
    ----------
    plugins
        List of plugins to discover.
    policy
        Safety policy to validate against.  ``None`` = unrestricted.
    check_requirements
        If ``True``, check manifest requirements against policy and imports.
    """
    import sys

    results: List[PluginDiscoveryResult] = []

    for plugin in plugins:
        manifest = plugin.manifest
        available = True
        reason: Optional[str] = None
        reason_code = AvailabilityReason.ALLOWED

        if check_requirements and policy:
            if manifest.requires.filesystem and not policy.allow_filesystem:
                available = False
                reason = "Requires filesystem access"
                reason_code = AvailabilityReason.POLICY_BLOCKED
            if manifest.requires.network and not policy.allow_network:
                available = False
                reason = "Requires network access"
                reason_code = AvailabilityReason.POLICY_BLOCKED

        if check_requirements and available and manifest.requires.imports:
            for imp in manifest.requires.imports:
                try:
                    __import__(imp)
                except ImportError:
                    available = False
                    reason = f"Missing package: {imp}"
                    reason_code = AvailabilityReason.MISSING_DEPENDENCY
                    break

        if check_requirements and available and manifest.requires.platforms is not None:
            if sys.platform not in manifest.requires.platforms:
                available = False
                reason = f"Platform '{sys.platform}' not supported (requires: {', '.join(manifest.requires.platforms)})"
                reason_code = AvailabilityReason.PLATFORM_UNSUPPORTED

        if manifest.deprecated is not None:
            reason_code = AvailabilityReason.DEPRECATED
            if reason is None:
                reason = manifest.deprecated

        results.append(PluginDiscoveryResult(
            plugin=plugin,
            manifest=manifest,
            available=available,
            reason=reason,
            reason_code=reason_code,
            skill_count=len(plugin.skills),
        ))

    return results


__all__ = [
    "AvailabilityReason",
    "SkillAvailability",
    "PluginDiscoveryResult",
    "get_available_skills",
    "discover_plugins",
]
