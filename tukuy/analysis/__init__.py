"""Code analysis module for Python code security assessment.

Provides AST-based analysis to detect potentially dangerous operations
and calculate risk scores for code execution in sandboxed environments.
"""

from .analyzer import CodeAnalysis, analyze_python
from .ast_visitors import CodeFeatures, FeatureExtractor
from .risk_scoring import RiskAssessment, RiskLevel, calculate_risk

__all__ = [
    "CodeAnalysis",
    "CodeFeatures",
    "FeatureExtractor",
    "RiskAssessment",
    "RiskLevel",
    "analyze_python",
    "calculate_risk",
]
