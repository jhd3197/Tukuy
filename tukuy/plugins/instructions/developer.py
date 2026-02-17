"""Developer instruction pack -- AI-powered developer tools.

Provides instructions for code explanation, docstring generation,
code review, SQL generation, regex building, and test case generation.
"""

from typing import Optional

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="explain_code",
    description="Explain what a piece of code does in plain language",
    prompt=(
        "Explain what the following code does in plain language. Be clear "
        "and concise. If a programming language is specified, use that context "
        "for your explanation.\n\n"
        "Language: {language}\n\n"
        "```\n{code}\n```"
    ),
    system_prompt="You are a senior software engineer who excels at explaining code clearly to developers of all levels.",
    output_format="markdown",
    temperature=0.3,
    max_tokens=800,
    category="developer",
    tags=["code", "explanation", "developer"],
    icon="code",
)
def explain_code(code: str, language: str = "auto-detect"):
    pass


@instruction(
    name="generate_docstring",
    description="Generate a comprehensive docstring for a function or class",
    prompt=(
        "Generate a comprehensive docstring for the following code. Use the "
        "{style} docstring style. Include a description, parameters, return "
        "value, raises (if applicable), and a brief example.\n\n"
        "```\n{code}\n```"
    ),
    system_prompt="You are a documentation expert. Write clear, complete docstrings. Output only the docstring text (no code fences).",
    output_format="text",
    temperature=0.3,
    max_tokens=500,
    category="developer",
    tags=["docstring", "documentation", "developer"],
    icon="file-text",
)
def generate_docstring(code: str, style: str = "google"):
    pass


@instruction(
    name="review_code",
    description="Review code for bugs, security issues, performance problems, and style improvements",
    prompt=(
        "Review the following code for bugs, security issues, performance "
        "problems, and style improvements. Be specific and actionable.\n\n"
        "Language: {language}\n"
        "Focus areas: {focus}\n\n"
        "```\n{code}\n```"
    ),
    system_prompt="You are a senior code reviewer. Identify real issues, not nitpicks. Be specific about line numbers and provide concrete fix suggestions. Always respond with valid JSON.",
    output_format="json",
    temperature=0.4,
    max_tokens=1000,
    category="developer",
    tags=["code-review", "bugs", "security", "developer"],
    icon="shield",
    few_shot_examples=[
        {
            "input": "Language: python\nFocus areas: all\n\ndef get_user(id):\n    query = f\"SELECT * FROM users WHERE id = {id}\"\n    return db.execute(query)",
            "output": '{"issues": [{"severity": "critical", "type": "security", "line": 2, "description": "SQL injection vulnerability via f-string interpolation", "suggestion": "Use parameterized queries: db.execute(\'SELECT * FROM users WHERE id = ?\', (id,))"}], "summary": "Critical SQL injection vulnerability found. The user input is directly interpolated into the query string."}',
        },
    ],
)
def review_code(code: str, language: str = "auto-detect", focus: str = "all"):
    pass


@instruction(
    name="sql_from_english",
    description="Convert a natural language description into a SQL query",
    prompt=(
        "Convert the following natural language description into a SQL query. "
        "Target database: {database}.\n\n"
        "Description: {description}\n\n"
        "Schema (if provided): {schema}"
    ),
    system_prompt="You are a SQL expert. Write clean, efficient, correct SQL. Only output the SQL query, no explanation.",
    output_format="text",
    temperature=0.2,
    max_tokens=500,
    category="developer",
    tags=["sql", "query", "database", "developer"],
    icon="database",
)
def sql_from_english(description: str, database: str = "standard SQL", schema: str = "not provided"):
    pass


@instruction(
    name="regex_builder",
    description="Create a regular expression pattern from a natural language description",
    prompt=(
        "Create a regular expression pattern that matches the following "
        "description. Use {flavor} regex flavor.\n\n"
        "Description: {description}"
    ),
    system_prompt="You are a regex expert. Create precise, efficient patterns. Always respond with valid JSON including the pattern, flags, explanation, and example matches/non-matches.",
    output_format="json",
    temperature=0.3,
    max_tokens=400,
    category="developer",
    tags=["regex", "pattern", "developer"],
    icon="terminal",
    few_shot_examples=[
        {
            "input": "Description: Match email addresses. Flavor: python.",
            "output": '{"pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}", "flags": "", "explanation": "Matches standard email addresses: one or more alphanumeric/special chars, @, domain with dots, and a TLD of 2+ letters.", "examples": {"matches": ["user@example.com", "first.last@company.co.uk"], "non_matches": ["@missing.com", "no-at-sign.com"]}}',
        },
    ],
)
def regex_builder(description: str, flavor: str = "python"):
    pass


@instruction(
    name="generate_test_cases",
    description="Generate test cases for a function including edge cases and error cases",
    prompt=(
        "Generate test cases for the following code. Include normal cases, "
        "edge cases, and error cases. Use the {framework} testing framework.\n\n"
        "Language: {language}\n\n"
        "```\n{code}\n```"
    ),
    system_prompt="You are a QA engineer. Write thorough, meaningful tests that catch real bugs. Include descriptive test names and comments explaining what each test verifies.",
    output_format="text",
    temperature=0.5,
    max_tokens=1500,
    category="developer",
    tags=["testing", "test-cases", "qa", "developer"],
    icon="check-square",
)
def generate_test_cases(code: str, framework: str = "pytest", language: str = "python"):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class DeveloperInstructionPack(TransformerPlugin):
    """AI-powered developer tools: code explanation, docstrings, review, SQL, regex, and test generation."""

    def __init__(self):
        super().__init__("instructions_developer")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "explain_code": explain_code.__instruction__,
            "generate_docstring": generate_docstring.__instruction__,
            "review_code": review_code.__instruction__,
            "sql_from_english": sql_from_english.__instruction__,
            "regex_builder": regex_builder.__instruction__,
            "generate_test_cases": generate_test_cases.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_developer",
            display_name="Developer Instructions",
            description="AI-powered developer tools: code explanation, docstring generation, code review, SQL from English, regex builder, and test case generation.",
            icon="terminal",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
