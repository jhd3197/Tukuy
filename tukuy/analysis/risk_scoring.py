"""Risk scoring for Python code analysis.

Calculates risk levels based on detected code features.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from .ast_visitors import CodeFeatures

# Always-blocked imports that represent severe security risks
CRITICAL_IMPORTS = frozenset(
    {
        "ctypes",
        "multiprocessing",
        "threading",
        "_thread",
        "gc",
        "sys",
        "builtins",
        "importlib",
        "pkgutil",
        "code",
        "codeop",
        "rlcompleter",
        "pdb",
        "bdb",
        "trace",
        "traceback",
        "linecache",
        "inspect",
        "dis",
        "pickletools",
        "formatter",
        "msilib",
        "winreg",
        "_winapi",
        "posix",
        "posixpath",
        "nt",
        "ntpath",
        "_posixsubprocess",
    }
)

# High-risk imports
HIGH_RISK_IMPORTS = frozenset(
    {
        "os",
        "subprocess",
        "shutil",
        "pathlib",
        "pickle",
        "shelve",
        "marshal",
        "socket",
        "ssl",
        "asyncio",
        "signal",
        "pty",
        "tty",
        "termios",
        "resource",
        "syslog",
        "tempfile",
        "glob",
        "fnmatch",
    }
)

# Medium-risk imports
MEDIUM_RISK_IMPORTS = frozenset(
    {
        "urllib",
        "http",
        "email",
        "mailbox",
        "mimetypes",
        "base64",
        "binascii",
        "quopri",
        "uu",
        "html",
        "xml",
        "configparser",
        "logging",
        "warnings",
        "contextlib",
        "abc",
        "atexit",
        "weakref",
        "copy",
        "pprint",
        "reprlib",
    }
)


class RiskLevel(str, enum.Enum):
    """Risk level classification for code analysis."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    """Detailed risk assessment for analyzed code.

    Attributes:
        level: Overall risk level.
        score: Numeric risk score (0-100).
        reasons: List of reasons contributing to the risk.
        blocked_imports: Imports that would be blocked.
        warnings: Non-blocking warnings about the code.
    """

    level: RiskLevel
    score: int
    reasons: list[str] = field(default_factory=list)
    blocked_imports: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)


def calculate_risk(features: CodeFeatures) -> RiskAssessment:
    """Calculate risk score and level from extracted code features.

    Args:
        features: CodeFeatures from AST analysis.

    Returns:
        RiskAssessment with level, score, reasons, and warnings.
    """
    score = 0
    reasons: list[str] = []
    warnings: list[str] = []
    blocked_imports: set[str] = set()

    # Check critical imports (instant critical)
    critical_found = features.imports & CRITICAL_IMPORTS
    if critical_found:
        score += 100
        blocked_imports.update(critical_found)
        reasons.append(f"Critical imports detected: {', '.join(sorted(critical_found))}")

    # Check high-risk imports
    high_risk_found = features.imports & HIGH_RISK_IMPORTS
    if high_risk_found:
        score += 40
        reasons.append(f"High-risk imports: {', '.join(sorted(high_risk_found))}")

    # Check medium-risk imports
    medium_risk_found = features.imports & MEDIUM_RISK_IMPORTS
    if medium_risk_found:
        score += 15
        warnings.append(f"Medium-risk imports: {', '.join(sorted(medium_risk_found))}")

    # Check exec/eval usage (critical)
    if features.exec_eval_usage:
        score += 80
        calls = [call[0] for call in features.exec_eval_usage]
        reasons.append(f"Dynamic code execution: {', '.join(calls)}")

    # Check system calls (critical)
    if features.system_calls:
        score += 80
        calls = [call[0] for call in features.system_calls]
        reasons.append(f"System calls detected: {', '.join(calls)}")

    # Check network calls (high)
    if features.network_calls:
        score += 35
        calls = [call[0] for call in features.network_calls]
        reasons.append(f"Network operations: {', '.join(calls)}")

    # Check file operations (medium-high depending on context)
    if features.file_operations:
        score += 25
        calls = [call[0] for call in features.file_operations]
        warnings.append(f"File operations: {', '.join(calls)}")

    # Check dangerous builtins
    if features.dangerous_builtins:
        score += 20
        warnings.append(f"Dangerous builtins: {', '.join(sorted(features.dangerous_builtins))}")

    # Check for global/nonlocal (can be used to escape sandbox)
    if features.has_global_statements:
        score += 10
        warnings.append("Uses global statements")

    if features.has_nonlocal_statements:
        score += 5
        warnings.append("Uses nonlocal statements")

    # Cap score at 100
    score = min(score, 100)

    # Determine level
    if score >= 70:
        level = RiskLevel.CRITICAL
    elif score >= 40:
        level = RiskLevel.HIGH
    elif score >= 15:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    return RiskAssessment(
        level=level,
        score=score,
        reasons=reasons,
        blocked_imports=blocked_imports,
        warnings=warnings,
    )
