"""Safety manifest system for Tukuy — policy enforcement and sandbox integration.

Phase 7 of the Tukuy roadmap: each skill declares what resources it needs
(imports, network, filesystem access) and the runtime enforces these
declarations against an active safety policy.

Usage::

    from tukuy import SafetyPolicy, set_policy, skill

    # Define a restrictive policy
    policy = SafetyPolicy(
        allowed_imports={"json", "re"},
        allow_network=False,
        allow_filesystem=False,
    )

    # Activate globally (async-safe via contextvars)
    set_policy(policy)

    # Skills are now validated before execution
    @skill(
        name="web_scraper",
        requires_network=True,
        required_imports=["aiohttp"],
    )
    async def web_scraper(url: str) -> str:
        ...

    # web_scraper.invoke("https://example.com")
    # => SafetyError: requires network access but policy denies it

Integration with Prompture::

    config = policy.to_sandbox_config()
    # => {"allowed_imports": ["json", "re"], "network": False, "filesystem": False}

    policy = SafetyPolicy.from_sandbox_config(config)
"""

import contextvars
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union


# ---------------------------------------------------------------------------
# SafetyViolation
# ---------------------------------------------------------------------------

@dataclass
class SafetyViolation:
    """A single safety policy violation."""

    kind: str  # "import", "network", "filesystem"
    message: str
    skill_name: str = ""

    def __str__(self) -> str:
        prefix = f"[{self.skill_name}] " if self.skill_name else ""
        return f"{prefix}{self.message}"


# ---------------------------------------------------------------------------
# SafetyError
# ---------------------------------------------------------------------------

class SafetyError(Exception):
    """Raised when a skill violates the active safety policy."""

    def __init__(self, violations: List[SafetyViolation]) -> None:
        self.violations = list(violations)
        messages = [str(v) for v in self.violations]
        super().__init__(f"Safety policy violated: {'; '.join(messages)}")


# ---------------------------------------------------------------------------
# SafetyManifest
# ---------------------------------------------------------------------------

@dataclass
class SafetyManifest:
    """Extracted resource requirements from a skill descriptor.

    This is the "what does this skill need?" side of the equation.
    """

    required_imports: List[str] = field(default_factory=list)
    requires_network: bool = False
    requires_filesystem: bool = False
    skill_name: str = ""

    @classmethod
    def from_descriptor(cls, descriptor: Any) -> "SafetyManifest":
        """Create a manifest from a :class:`~tukuy.skill.SkillDescriptor`.

        Typed as ``Any`` to avoid circular imports.
        """
        return cls(
            required_imports=list(getattr(descriptor, "required_imports", [])),
            requires_network=getattr(descriptor, "requires_network", False),
            requires_filesystem=getattr(descriptor, "requires_filesystem", False),
            skill_name=getattr(descriptor, "name", ""),
        )

    @classmethod
    def from_skill(cls, skill: Any) -> "SafetyManifest":
        """Create a manifest from a :class:`~tukuy.skill.Skill` instance."""
        descriptor = getattr(skill, "descriptor", skill)
        return cls.from_descriptor(descriptor)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "required_imports": self.required_imports,
            "requires_network": self.requires_network,
            "requires_filesystem": self.requires_filesystem,
            "skill_name": self.skill_name,
        }


# ---------------------------------------------------------------------------
# SafetyPolicy
# ---------------------------------------------------------------------------

@dataclass
class SafetyPolicy:
    """Defines what resources are permitted in the current runtime.

    This is the "what does the environment allow?" side of the equation.

    Parameters
    ----------
    allowed_imports : set of str, optional
        If set, only these imports are permitted.  ``None`` means
        unrestricted (all imports allowed).
    blocked_imports : set of str
        Imports that are always denied, even if in *allowed_imports*.
    allow_network : bool
        Whether skills may declare network access.
    allow_filesystem : bool
        Whether skills may declare filesystem access.
    """

    allowed_imports: Optional[Set[str]] = None
    blocked_imports: Set[str] = field(default_factory=set)
    allow_network: bool = True
    allow_filesystem: bool = True

    # -- Convenience constructors -------------------------------------------

    @classmethod
    def restrictive(cls) -> "SafetyPolicy":
        """Create a fully restrictive policy: no network, no filesystem, no imports."""
        return cls(
            allowed_imports=set(),
            allow_network=False,
            allow_filesystem=False,
        )

    @classmethod
    def permissive(cls) -> "SafetyPolicy":
        """Create a fully permissive policy: everything allowed."""
        return cls()

    @classmethod
    def network_only(cls) -> "SafetyPolicy":
        """Allow network but deny filesystem access."""
        return cls(allow_network=True, allow_filesystem=False)

    @classmethod
    def filesystem_only(cls) -> "SafetyPolicy":
        """Allow filesystem but deny network access."""
        return cls(allow_network=False, allow_filesystem=True)

    # -- Validation ---------------------------------------------------------

    def validate(
        self,
        target: Any,
    ) -> List[SafetyViolation]:
        """Validate a skill, descriptor, or manifest against this policy.

        Parameters
        ----------
        target
            A :class:`SafetyManifest`, :class:`~tukuy.skill.SkillDescriptor`,
            or :class:`~tukuy.skill.Skill` instance.

        Returns
        -------
        list of SafetyViolation
            Empty list if the target complies with the policy.
        """
        if isinstance(target, SafetyManifest):
            manifest = target
        else:
            manifest = SafetyManifest.from_skill(target)

        violations: List[SafetyViolation] = []

        # Network check
        if manifest.requires_network and not self.allow_network:
            violations.append(SafetyViolation(
                kind="network",
                message="Skill requires network access but policy denies it",
                skill_name=manifest.skill_name,
            ))

        # Filesystem check
        if manifest.requires_filesystem and not self.allow_filesystem:
            violations.append(SafetyViolation(
                kind="filesystem",
                message="Skill requires filesystem access but policy denies it",
                skill_name=manifest.skill_name,
            ))

        # Import checks
        for imp in manifest.required_imports:
            # Blocked imports take precedence
            if imp in self.blocked_imports:
                violations.append(SafetyViolation(
                    kind="import",
                    message=f"Import '{imp}' is blocked by policy",
                    skill_name=manifest.skill_name,
                ))
            elif self.allowed_imports is not None and imp not in self.allowed_imports:
                violations.append(SafetyViolation(
                    kind="import",
                    message=f"Import '{imp}' is not in the allowed imports list",
                    skill_name=manifest.skill_name,
                ))

        return violations

    def enforce(self, target: Any) -> None:
        """Validate and raise :class:`SafetyError` if violations are found.

        Parameters
        ----------
        target
            A manifest, descriptor, or skill to validate.

        Raises
        ------
        SafetyError
            If any violations are detected.
        """
        violations = self.validate(target)
        if violations:
            raise SafetyError(violations)

    # -- Sandbox integration ------------------------------------------------

    def to_sandbox_config(self) -> Dict[str, Any]:
        """Export as a Prompture ``PythonSandbox``-compatible configuration.

        Returns a dict with keys that map to sandbox settings::

            {
                "allowed_imports": ["json", "re"] or None,
                "blocked_imports": ["os", "subprocess"],
                "network": True,
                "filesystem": False,
            }
        """
        return {
            "allowed_imports": sorted(self.allowed_imports) if self.allowed_imports is not None else None,
            "blocked_imports": sorted(self.blocked_imports),
            "network": self.allow_network,
            "filesystem": self.allow_filesystem,
        }

    @classmethod
    def from_sandbox_config(cls, config: Dict[str, Any]) -> "SafetyPolicy":
        """Create a SafetyPolicy from a Prompture sandbox configuration dict.

        Accepts the format produced by :meth:`to_sandbox_config` as well as
        common sandbox config variations.
        """
        allowed = config.get("allowed_imports")
        if allowed is not None:
            allowed = set(allowed)

        blocked = config.get("blocked_imports", [])
        if isinstance(blocked, (list, tuple)):
            blocked = set(blocked)

        return cls(
            allowed_imports=allowed,
            blocked_imports=blocked,
            allow_network=config.get("network", config.get("allow_network", True)),
            allow_filesystem=config.get("filesystem", config.get("allow_filesystem", True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the policy to a plain dict."""
        return {
            "allowed_imports": sorted(self.allowed_imports) if self.allowed_imports is not None else None,
            "blocked_imports": sorted(self.blocked_imports),
            "allow_network": self.allow_network,
            "allow_filesystem": self.allow_filesystem,
        }


# ---------------------------------------------------------------------------
# Active policy management (contextvars — async-safe)
# ---------------------------------------------------------------------------

_active_policy: contextvars.ContextVar[Optional[SafetyPolicy]] = contextvars.ContextVar(
    "tukuy_safety_policy", default=None,
)


def set_policy(policy: Optional[SafetyPolicy]) -> contextvars.Token:
    """Set the active safety policy for the current context.

    Pass ``None`` to clear the policy (unrestricted mode).

    Returns a token that can be used with :func:`reset_policy` to
    restore the previous value.

    This uses ``contextvars`` so it is safe for use with ``asyncio``
    and concurrent tasks — each task inherits the policy from its
    parent context but can override it independently.
    """
    return _active_policy.set(policy)


def get_policy() -> Optional[SafetyPolicy]:
    """Return the active safety policy, or ``None`` if unrestricted."""
    return _active_policy.get()


def reset_policy(token: contextvars.Token) -> None:
    """Restore the previous safety policy using a token from :func:`set_policy`."""
    _active_policy.reset(token)


__all__ = [
    "SafetyViolation",
    "SafetyError",
    "SafetyManifest",
    "SafetyPolicy",
    "set_policy",
    "get_policy",
    "reset_policy",
]
