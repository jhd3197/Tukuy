"""Tests for the code analysis module."""

import pytest

from tukuy.analysis import (
    CodeAnalysis,
    CodeFeatures,
    FeatureExtractor,
    RiskAssessment,
    RiskLevel,
    analyze_python,
    calculate_risk,
)
from tukuy.analysis.ast_visitors import extract_features


class TestFeatureExtractor:
    """Tests for the FeatureExtractor AST visitor."""

    def test_extract_imports(self):
        """Test extraction of import statements."""
        code = """
import json
import os
from collections import defaultdict
from typing import Any, List
"""
        features = extract_features(code)
        assert "json" in features.imports
        assert "os" in features.imports
        assert "collections" in features.imports
        assert "typing" in features.imports

    def test_extract_function_calls(self):
        """Test extraction of function calls."""
        code = """
x = len([1, 2, 3])
y = print("hello")
z = json.loads('{}')
"""
        features = extract_features(code)
        assert "len" in features.function_calls
        assert "print" in features.function_calls
        assert "json.loads" in features.function_calls

    def test_extract_file_operations(self):
        """Test extraction of file operations."""
        code = """
f = open("test.txt", "r")
content = f.read()
f.close()
"""
        features = extract_features(code)
        assert len(features.file_operations) >= 1
        assert any("open" in op[0] for op in features.file_operations)

    def test_extract_exec_eval(self):
        """Test extraction of exec/eval usage."""
        code = """
exec("print('hello')")
result = eval("1 + 2")
"""
        features = extract_features(code)
        assert len(features.exec_eval_usage) == 2
        assert any("exec" in op[0] for op in features.exec_eval_usage)
        assert any("eval" in op[0] for op in features.exec_eval_usage)

    def test_extract_system_calls(self):
        """Test extraction of system calls."""
        code = """
import subprocess
subprocess.run(["ls", "-la"])
"""
        features = extract_features(code)
        assert "subprocess" in features.imports
        assert len(features.system_calls) >= 1

    def test_extract_dangerous_builtins(self):
        """Test extraction of dangerous builtin usage."""
        code = """
x = eval("1+1")
y = exec("pass")
z = __import__("os")
"""
        features = extract_features(code)
        assert "eval" in features.dangerous_builtins
        assert "exec" in features.dangerous_builtins
        assert "__import__" in features.dangerous_builtins

    def test_extract_global_nonlocal(self):
        """Test extraction of global/nonlocal statements."""
        code = """
x = 1
def foo():
    global x
    x = 2

def outer():
    y = 1
    def inner():
        nonlocal y
        y = 2
"""
        features = extract_features(code)
        assert features.has_global_statements is True
        assert features.has_nonlocal_statements is True

    def test_extract_class_definitions(self):
        """Test extraction of class definitions."""
        code = """
class Foo:
    pass

class Bar(Foo):
    pass
"""
        features = extract_features(code)
        assert "Foo" in features.class_definitions
        assert "Bar" in features.class_definitions

    def test_extract_async_operations(self):
        """Test extraction of async operations."""
        code = """
async def foo():
    await bar()

async for x in items:
    pass
"""
        features = extract_features(code)
        assert features.async_operations is True


class TestRiskScoring:
    """Tests for risk scoring logic."""

    def test_low_risk_code(self):
        """Test that simple code gets low risk."""
        features = extract_features("x = 1 + 2")
        risk = calculate_risk(features)
        assert risk.level == RiskLevel.LOW
        assert risk.score < 15

    def test_medium_risk_imports(self):
        """Test that medium-risk imports increase score."""
        features = extract_features("import urllib")
        risk = calculate_risk(features)
        assert risk.level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_high_risk_imports(self):
        """Test that high-risk imports increase score."""
        features = extract_features("import os")
        risk = calculate_risk(features)
        assert risk.level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
        assert len(risk.reasons) > 0

    def test_critical_imports(self):
        """Test that critical imports get critical level."""
        features = extract_features("import ctypes")
        risk = calculate_risk(features)
        assert risk.level == RiskLevel.CRITICAL
        assert "ctypes" in risk.blocked_imports

    def test_exec_eval_critical(self):
        """Test that exec/eval usage is critical."""
        features = extract_features("exec('print(1)')")
        risk = calculate_risk(features)
        assert risk.level == RiskLevel.CRITICAL
        assert any("exec" in r.lower() for r in risk.reasons)

    def test_system_calls_critical(self):
        """Test that system calls are critical."""
        features = extract_features("""
import subprocess
subprocess.run(['ls'])
""")
        risk = calculate_risk(features)
        assert risk.level == RiskLevel.CRITICAL


class TestAnalyzePython:
    """Tests for the main analyze_python function."""

    def test_basic_analysis(self):
        """Test basic code analysis."""
        analysis = analyze_python("x = 1 + 2")
        assert analysis.syntax_valid is True
        assert analysis.is_safe is True
        assert analysis.risk_level == RiskLevel.LOW

    def test_syntax_error(self):
        """Test that syntax errors are caught."""
        analysis = analyze_python("def foo(")
        assert analysis.syntax_valid is False
        assert analysis.is_safe is False
        assert analysis.syntax_error is not None

    def test_dangerous_code(self):
        """Test that dangerous code is flagged."""
        analysis = analyze_python("import subprocess; subprocess.run(['rm', '-rf', '/'])")
        assert analysis.is_safe is False
        assert analysis.risk_level == RiskLevel.CRITICAL

    def test_safe_threshold(self):
        """Test safe_threshold parameter."""
        # Code that would normally be unsafe
        code = "import os"

        # With default threshold (MEDIUM), it's unsafe
        analysis1 = analyze_python(code)
        # os import gives HIGH risk, which is > MEDIUM threshold

        # With HIGH threshold, it becomes safe
        analysis2 = analyze_python(code, safe_threshold=RiskLevel.HIGH)
        assert analysis2.is_safe is True

    def test_to_dict(self):
        """Test CodeAnalysis.to_dict() method."""
        analysis = analyze_python("import json; print(json.dumps({}))")
        d = analysis.to_dict()
        assert "source" in d
        assert "risk" in d
        assert "features" in d
        assert d["syntax_valid"] is True

    def test_risk_properties(self):
        """Test convenience properties."""
        analysis = analyze_python("x = 1")
        assert analysis.risk_level == analysis.risk.level
        assert analysis.risk_score == analysis.risk.score


class TestCodeFeatures:
    """Tests for the CodeFeatures dataclass."""

    def test_default_values(self):
        """Test default values are empty."""
        features = CodeFeatures()
        assert len(features.imports) == 0
        assert len(features.file_operations) == 0
        assert features.has_global_statements is False


class TestRiskAssessment:
    """Tests for the RiskAssessment dataclass."""

    def test_creation(self):
        """Test RiskAssessment creation."""
        risk = RiskAssessment(
            level=RiskLevel.HIGH,
            score=50,
            reasons=["test reason"],
            warnings=["test warning"],
        )
        assert risk.level == RiskLevel.HIGH
        assert risk.score == 50
        assert len(risk.reasons) == 1
        assert len(risk.warnings) == 1
