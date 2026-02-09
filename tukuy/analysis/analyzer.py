"""Main code analysis interface.

Provides the primary analyze_python() function for code security assessment.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ast_visitors import CodeFeatures, extract_features
from .risk_scoring import RiskAssessment, RiskLevel, calculate_risk


@dataclass
class CodeAnalysis:
    """Complete analysis result for Python code.

    Attributes:
        source: The original source code analyzed.
        features: Extracted code features from AST analysis.
        risk: Risk assessment with level, score, and reasons.
        is_safe: Whether the code is considered safe for execution.
        syntax_valid: Whether the code has valid Python syntax.
        syntax_error: Syntax error message if parsing failed.
    """

    source: str
    features: CodeFeatures
    risk: RiskAssessment
    is_safe: bool
    syntax_valid: bool = True
    syntax_error: str | None = None

    @property
    def risk_level(self) -> RiskLevel:
        """Convenience property to access risk level directly."""
        return self.risk.level

    @property
    def risk_score(self) -> int:
        """Convenience property to access risk score directly."""
        return self.risk.score

    def to_dict(self) -> dict:
        """Convert analysis to a dictionary for serialization."""
        return {
            "source": self.source,
            "syntax_valid": self.syntax_valid,
            "syntax_error": self.syntax_error,
            "is_safe": self.is_safe,
            "risk": {
                "level": self.risk.level.value,
                "score": self.risk.score,
                "reasons": self.risk.reasons,
                "warnings": self.risk.warnings,
                "blocked_imports": list(self.risk.blocked_imports),
            },
            "features": {
                "imports": list(self.features.imports),
                "file_operations": self.features.file_operations,
                "network_calls": self.features.network_calls,
                "system_calls": self.features.system_calls,
                "exec_eval_usage": self.features.exec_eval_usage,
                "dangerous_builtins": list(self.features.dangerous_builtins),
                "function_calls": list(self.features.function_calls),
                "has_global_statements": self.features.has_global_statements,
                "has_nonlocal_statements": self.features.has_nonlocal_statements,
                "class_definitions": list(self.features.class_definitions),
                "async_operations": self.features.async_operations,
            },
        }


def analyze_python(
    source: str,
    *,
    safe_threshold: RiskLevel = RiskLevel.MEDIUM,
) -> CodeAnalysis:
    """Analyze Python source code for security risks.

    Performs AST-based analysis to detect potentially dangerous operations
    and calculates a risk score.

    Args:
        source: Python source code as a string.
        safe_threshold: Maximum risk level considered safe.
            Defaults to MEDIUM (allowing LOW and MEDIUM risk code).

    Returns:
        CodeAnalysis with features, risk assessment, and safety determination.

    Example::

        from tukuy.analysis import analyze_python, RiskLevel

        analysis = analyze_python("import subprocess; subprocess.run(['ls'])")
        print(f"Risk: {analysis.risk_level}")  # RiskLevel.CRITICAL
        print(f"Safe: {analysis.is_safe}")  # False

        # More permissive threshold
        analysis = analyze_python("import json", safe_threshold=RiskLevel.HIGH)
        print(f"Safe: {analysis.is_safe}")  # True
    """
    # Try to parse the source code
    try:
        features = extract_features(source)
        syntax_valid = True
        syntax_error = None
    except SyntaxError as e:
        # Return analysis with syntax error
        features = CodeFeatures()
        risk = RiskAssessment(
            level=RiskLevel.CRITICAL,
            score=100,
            reasons=[f"Syntax error: {e}"],
        )
        return CodeAnalysis(
            source=source,
            features=features,
            risk=risk,
            is_safe=False,
            syntax_valid=False,
            syntax_error=str(e),
        )

    # Calculate risk
    risk = calculate_risk(features)

    # Determine safety based on threshold
    threshold_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    risk_index = threshold_order.index(risk.level)
    threshold_index = threshold_order.index(safe_threshold)
    is_safe = risk_index <= threshold_index

    return CodeAnalysis(
        source=source,
        features=features,
        risk=risk,
        is_safe=is_safe,
        syntax_valid=syntax_valid,
        syntax_error=syntax_error,
    )
