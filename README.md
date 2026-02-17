<p align="center">
  <h1 align="center">🌀 Tukuy</h1>
  <p align="center">Portable agent skills library and data transformation toolkit for Python.</p>
</p>

<p align="center">
  <a href="https://pypi.org/project/tukuy/"><img src="https://badge.fury.io/py/tukuy.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/tukuy/"><img src="https://img.shields.io/pypi/pyversions/tukuy.svg" alt="Python versions"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://pepy.tech/project/tukuy"><img src="https://static.pepy.tech/badge/tukuy" alt="Downloads"></a>
  <a href="https://github.com/jhd3197/Tukuy"><img src="https://img.shields.io/github/stars/jhd3197/Tukuy?style=social" alt="GitHub stars"></a>
</p>

---

**Tukuy** (meaning "to transform" or "to become" in Quechua) is a cross-platform skills layer that any Python agent framework can use. It provides typed skill descriptors, agent-framework bridges (OpenAI, Anthropic), async-first execution, smart composition, and runtime safety enforcement — all built on top of a proven plugin-based transformation engine.

```python
from tukuy import skill

@skill(name="parse_date", description="Parse a date string into ISO format")
def parse_date(text: str) -> str:
    from dateutil import parser
    return parser.parse(text).isoformat()

result = parse_date.__skill__.invoke("January 15, 2025")
print(result.value)  # "2025-01-15T00:00:00"
```

## Installation

```bash
pip install tukuy
```

## Quick Start

### Define a skill

```python
from tukuy import skill

@skill(
    name="parse_date",
    description="Parse a date string into ISO format",
    category="date",
    tags=["parsing", "datetime"],
)
def parse_date(text: str, format: str = "auto") -> str:
    """Parse date from text, return ISO 8601."""
    from dateutil import parser
    return parser.parse(text).isoformat()
```

The `@skill` decorator infers input/output schemas from type hints, detects async functions automatically, and attaches a `Skill` instance as `fn.__skill__`.

### Invoke a skill

```python
result = parse_date.__skill__.invoke("January 15, 2025")
print(result.value)      # "2025-01-15T00:00:00"
print(result.success)    # True
print(result.duration_ms) # 0.42
```

### Use with an agent framework

```python
from tukuy import to_openai_tools, to_anthropic_tools

skills = [parse_date, extract_entities, summarize]

# OpenAI function-calling format
tools = to_openai_tools(skills)

# Anthropic tool_use format
tools = to_anthropic_tools(skills)
```

Dispatch tool calls back to skills:

```python
from tukuy import dispatch_openai, dispatch_anthropic

# OpenAI
result_msg = dispatch_openai(tool_call, skills)

# Anthropic
result_block = dispatch_anthropic(tool_use, skills)
```

---

## Core Concepts

### Skill Descriptors

Every skill has a declared-upfront contract via `SkillDescriptor`:

```python
from tukuy import SkillDescriptor

descriptor = SkillDescriptor(
    name="web_scraper",
    description="Scrape and extract text from a URL",
    input_schema=str,
    output_schema=str,
    category="web",
    tags=["scraping", "extraction"],
    is_async=True,
    requires_network=True,
    required_imports=["aiohttp", "beautifulsoup4"],
    idempotent=True,
    side_effects=False,
)
```

Descriptors carry identity, typed I/O schemas, discovery metadata, operational hints, and safety declarations — everything an agent framework needs to discover and invoke a skill.

### Async Support

Skills work with both sync and async functions:

```python
@skill(name="fetch_page", requires_network=True)
async def fetch_page(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()

# Async invocation
result = await fetch_page.__skill__.ainvoke("https://example.com")
```

Sync skills also work with `ainvoke()` — they're called normally without blocking the event loop.

### Composition

Chain, branch, and fan-out skills with `Chain`, `Branch`, and `Parallel`:

```python
from tukuy import Chain, branch, parallel

# Sequential pipeline
chain = Chain(["strip", "lowercase", parse_date])
result = chain.run("  January 15, 2025  ")

# Conditional branching
chain = Chain([
    "strip",
    branch(
        on_match=lambda v: "@" in v,
        true_path=["email_validator"],
        false_path=["url_validator"],
    ),
])

# Parallel fan-out with merge
chain = Chain([
    parallel(
        steps=["extract_dates", "extract_emails", "extract_phones"],
        merge="dict",  # {"extract_dates": [...], "extract_emails": [...], ...}
    ),
])

# Async execution with asyncio.gather for parallel steps
result = await chain.arun(input_text)
```

Steps can be transformer names (strings), parametrized transforms (dicts), `Skill` instances, `@skill`-decorated functions, plain callables, or nested `Chain` objects.

### Context

Skills share state through a typed, scoped `SkillContext`:

```python
from tukuy import skill, SkillContext

@skill(name="extract_entities")
def extract_entities(text: str, ctx: SkillContext) -> dict:
    entities = do_extraction(text)
    ctx.set("last_entities", entities)
    return entities

@skill(name="format_entities")
def format_entities(ctx: SkillContext) -> str:
    entities = ctx.get("last_entities")
    return format_them(entities)
```

Context supports namespaced scoping (for parallel branches), parent-child delegation, snapshot/merge, and bridging to plain dicts.

### Safety Policy

Each skill declares what resources it needs. The runtime enforces these declarations against an active policy:

```python
from tukuy import SafetyPolicy, set_policy

# Define what the environment allows
policy = SafetyPolicy(
    allowed_imports={"json", "re", "datetime"},
    blocked_imports={"os", "subprocess"},
    allow_network=False,
    allow_filesystem=False,
)

# Activate globally (async-safe via contextvars)
set_policy(policy)

# Skills that violate the policy are blocked before execution
@skill(name="web_scraper", requires_network=True)
async def web_scraper(url: str) -> str: ...

result = web_scraper.__skill__.invoke("https://example.com")
# result.success == False
# result.error == "Safety policy violated: Skill requires network access but policy denies it"
```

Convenience constructors for common scenarios:

```python
SafetyPolicy.restrictive()    # No imports, no network, no filesystem
SafetyPolicy.permissive()     # Everything allowed
SafetyPolicy.network_only()   # Network yes, filesystem no
SafetyPolicy.filesystem_only() # Filesystem yes, network no
```

Policies can be exported/imported as sandbox configurations for integration with external sandbox runtimes:

```python
config = policy.to_sandbox_config()
# {"allowed_imports": ["json", "re"], "network": False, "filesystem": False}

policy = SafetyPolicy.from_sandbox_config(config)
```

---

## Data Transformations

Tukuy includes a full transformation engine with six built-in plugins. This is the foundation that the skills layer is built on.

```python
from tukuy import TukuyTransformer

t = TukuyTransformer()

# Text
t.transform("  Hello World!  ", ["strip", "lowercase"])
# "hello world!"

# HTML
t.transform("<div>Hello <b>World</b>!</div>", ["strip_html_tags", "lowercase"])
# "hello world!"

# Chained with parameters
t.transform("  Hello World!  ", [
    "strip",
    "lowercase",
    {"function": "truncate", "length": 5},
])
# "hello..."
```

### Built-in Plugins

**Text** — `strip`, `lowercase`, `uppercase`, `truncate`, `replace`, `regex_replace`, `split`, `join`, `normalize`

**HTML** — `strip_html_tags`, `extract_text`, `select`, `extract_links`, `extract_tables`, `clean_html`

**JSON** — `parse_json`, `stringify`, `extract`, `flatten`, `merge`, `validate_schema`

**Date** — `parse_date`, `format_date`, `age_calc`, `add_days`, `diff_days`, `is_weekend`

**Numerical** — `round`, `format_number`, `to_currency`, `percentage`, `math_eval`, `scale`, `statistics`

**Validation** — `email_validator`, `url_validator`, `phone_validator`, `length_validator`, `range_validator`, `regex_validator`, `type_validator`

### Custom Plugins

Extend Tukuy with your own transformer plugins:

```python
from tukuy import TransformerPlugin
from tukuy.base import ChainableTransformer

class ReverseTransformer(ChainableTransformer):
    def validate(self, value):
        return isinstance(value, str)

    def _transform(self, value, context=None):
        return value[::-1]

class MyPlugin(TransformerPlugin):
    def __init__(self):
        super().__init__("my_plugin")

    @property
    def transformers(self):
        return {"reverse": lambda _: ReverseTransformer("reverse")}

t = TukuyTransformer()
t.register_plugin(MyPlugin())
t.transform("hello", ["reverse"])  # "olleh"
```

Plugins support lifecycle hooks (`initialize()` / `cleanup()`) and can expose skills alongside transformers via the `skills` property.

### Dynamic Tool Registration

Tukuy makes it easy to add tools at runtime without restarting your application.

**Register a plugin on the fly:**

```python
from tukuy import TukuyTransformer, TransformerPlugin

class MyPlugin(TransformerPlugin):
    def __init__(self):
        super().__init__("my_plugin")

    @property
    def transformers(self):
        return {"reverse": lambda _: ReverseTransformer("reverse")}

t = TukuyTransformer()
t.register_plugin(MyPlugin())       # available immediately
t.transform("hello", ["reverse"])   # "olleh"
t.unregister_plugin("my_plugin")    # remove when no longer needed
```

**Create skills at runtime:**

```python
from tukuy import skill, to_openai_tools

@skill(name="sentiment", description="Classify sentiment", category="nlp")
def sentiment(text: str) -> str:
    return "positive" if "good" in text.lower() else "negative"

# Instantly usable — invoke directly or convert to agent tool format
result = sentiment.__skill__.invoke("This is good!")
tools = to_openai_tools([sentiment])  # ready for OpenAI function-calling
```

**Use the `@tukuy_plugin` decorator for metadata:**

```python
from tukuy import tukuy_plugin

@tukuy_plugin("analytics", "Real-time analytics transforms", "1.0.0")
class AnalyticsPlugin(TransformerPlugin):
    @property
    def transformers(self):
        return {"moving_avg": lambda p: MovingAvgTransformer("moving_avg", **p)}
```

**Hot-reload plugins without restarting:**

```python
from tukuy import hot_reload

hot_reload("my_plugin")  # reload a specific plugin
hot_reload()             # reload all plugins
```

**Discover what's available:**

```python
from tukuy import browse_tools, get_tool_details, search_tools

index = browse_tools()                      # compact index of all tools
details = get_tool_details("reverse")       # full metadata for a specific tool
results = search_tools("date", limit=5)     # keyword search across all tools
```

---

## Pattern-based Extraction

### HTML

```python
pattern = {
    "properties": [
        {"name": "title", "selector": "h1", "transform": ["strip", "lowercase"]},
        {"name": "links", "selector": "a", "attribute": "href", "type": "array"},
    ]
}
data = t.extract_html_with_pattern(html, pattern)
```

### JSON

```python
pattern = {
    "properties": [
        {
            "name": "user",
            "selector": "data.user",
            "properties": [
                {"name": "name", "selector": "fullName", "transform": ["strip"]},
            ],
        }
    ]
}
data = t.extract_json_with_pattern(json_str, pattern)
```

---

## Error Handling

```python
from tukuy.exceptions import ValidationError, TransformationError, ParseError

try:
    result = t.transform(data, transformations)
except ValidationError as e:
    print(f"Validation failed: {e}")
except ParseError as e:
    print(f"Parsing failed: {e}")
except TransformationError as e:
    print(f"Transformation failed: {e}")
```

---

## CLI

Tukuy ships with a command-line interface for inspecting plugins, running skills, and applying transformers directly from the terminal.

```bash
pip install tukuy
```

### Discovery

```bash
# High-level summary (plugin/skill/transformer/group counts)
tukuy info

# List everything
tukuy list plugins
tukuy list skills
tukuy list transformers
tukuy list groups

# Filter lists
tukuy list skills --plugin country
tukuy list skills --group Integrations
tukuy list skills --tag crypto
tukuy list plugins --group Data

# JSON output for scripting
tukuy list skills --json
tukuy list plugins --json
```

### Inspect

```bash
# Detailed plugin info (transformers, skills, requirements)
tukuy show plugin country

# Detailed skill info (parameters, risk level, tags, config)
tukuy show skill crypto_price
```

### Run Skills

```bash
# Run a skill with keyword arguments
tukuy run word_define --word hello
tukuy run crypto_price --coins bitcoin
tukuy run public_holidays --country_code US

# Raw JSON output
tukuy run crypto_price --coins bitcoin --raw
```

### Apply Transformers

```bash
# Transform inline text
tukuy transform lowercase "HELLO WORLD"
tukuy transform hash_text "secret" --algorithm md5

# Pipe input from stdin
echo "HELLO" | tukuy transform lowercase
cat data.json | tukuy transform parse_json
```

---

## MCP Server

Tukuy includes an [MCP](https://modelcontextprotocol.io/) server that exposes all plugins, skills, and transformers as tools for Claude Desktop, Claude Code, and other MCP clients.

```bash
pip install 'tukuy[mcp]'
```

### Configuration

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tukuy": {
      "command": "python",
      "args": ["-m", "tukuy.mcp_server"]
    }
  }
}
```

**Claude Code** (`.claude/settings.json`):

```json
{
  "mcpServers": {
    "tukuy": {
      "command": "python",
      "args": ["-m", "tukuy.mcp_server"]
    }
  }
}
```

The server provides 6 meta-tools rather than registering hundreds of individual tools:

| Tool | Purpose |
|------|---------|
| `tukuy_info` | Summary of all capabilities (counts, groups) |
| `tukuy_browse` | Browse plugins with their skills and transformers |
| `tukuy_search` | Keyword search across skills and transformers |
| `tukuy_show` | Detailed info for a specific skill or transformer |
| `tukuy_run` | Execute a skill with parameters |
| `tukuy_transform` | Apply a transformer to input |

### Filtering Plugins

Control which plugins are exposed with `--only` / `--exclude` flags or environment variables. Values can be plugin names or group names.

```bash
# Only expose math-related plugins
tukuy-mcp --only numerical

# Only expose an entire group
tukuy-mcp --only Data

# Exclude dangerous plugins
tukuy-mcp --exclude shell,file_ops

# Combine: start from a group, then remove some
tukuy-mcp --only Data --exclude sql
```

Environment variables work the same way, useful for JSON-based MCP config:

```json
{
  "mcpServers": {
    "tukuy-math": {
      "command": "python",
      "args": ["-m", "tukuy.mcp_server"],
      "env": { "TUKUY_MCP_ONLY": "numerical,date" }
    },
    "tukuy-safe": {
      "command": "python",
      "args": ["-m", "tukuy.mcp_server"],
      "env": { "TUKUY_MCP_EXCLUDE": "shell,file_ops,git" }
    }
  }
}
```

Available groups: `Code`, `Core`, `Data`, `Documents`, `Extensibility`, `Integrations`, `Interaction`, `Media`, `Web`.

---

## Architecture

```
tukuy/
    skill.py          Skill descriptors, @skill decorator, invoke/ainvoke
    context.py        SkillContext with scoping, snapshot, merge
    safety.py         SafetyPolicy, manifest validation, sandbox integration
    bridges.py        OpenAI and Anthropic tool format bridges
    chain.py          Chain, Branch, Parallel composition
    cli.py            Command-line interface (tukuy info/list/show/run/transform)
    mcp_server.py     MCP server for Claude Desktop / Claude Code
    async_base.py     Async transformer base classes
    base.py           Sync transformer base classes
    plugins/          Built-in plugins (text, html, json, date, numerical, validation, ...)
    core/             Registration, introspection, unified registry
    transformers/     Transformer implementations
```

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests with `pytest`
5. Commit and push
6. Open a Pull Request

## License

See [LICENSE](LICENSE) for details.
