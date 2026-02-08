# Tukuy + Cacao Integration Feedback

## The Idea

Use Tukuy's transformation library to power/expand Cacao's built-in JS handlers for static builds.

---

## Current State

### Cacao Handlers (27 handlers, JS, client-side)
| Category | Handlers |
|----------|----------|
| Encoders | base64, URL, HTML entities, JWT decode |
| Generators | UUID, password, lorem ipsum |
| Converters | JSON-to-YAML, case (8 styles), number base |
| Text | text stats, regex tester |
| Crypto | SHA hash, HMAC-SHA256 |

### Tukuy Transformers (50+, Python, server-side)
| Category | Transformers |
|----------|-------------|
| Text | strip, lowercase, uppercase, title_case, camel_case, snake_case, slugify, truncate, replace, regex, template, map, split, remove_emojis, redact_sensitive |
| Numerical | int, float, round, abs, floor, ceil, pow, sqrt, log, clamp, scale, percentage, currency, unit convert, math ops, format_number, random, stats, extract_numbers, shorthand parsing |
| Validation | bool, email validator, phone formatter, credit card check, type enforcer |
| Date | date parse, timezone convert, duration calc, age calc |
| HTML | strip tags, sanitize, link extraction, CSS selector extraction, URL resolve, domain extract |
| JSON | JSON parse, JSONPath extraction |

---

## Overlap & Gaps

| Area | Cacao Has | Tukuy Adds |
|------|-----------|------------|
| Case conversion | 8 styles | slugify (URL-safe), split |
| Text manipulation | stats, regex | truncate, replace, template, map, emoji removal, redaction |
| Number ops | base conversion only | 25+ math/format/stats operations |
| Validation | nothing | email, phone, credit card, type enforcement |
| Date/time | nothing | parsing, timezone, duration, age calculation |
| HTML processing | entity encode/decode | strip tags, sanitize, link/data extraction |
| JSON processing | JSON-to-YAML | JSONPath extraction, schema validation |
| Encoding | base64, URL, JWT | (no overlap, Cacao covers this) |
| Crypto | hash, HMAC | (no overlap, Cacao covers this) |
| Generators | UUID, password, lorem | random numbers (Tukuy), but mostly Cacao's domain |

**Bottom line**: Very little overlap. Tukuy fills almost every gap Cacao has, especially in numerical, validation, date, and deeper text/HTML processing.

---

## Integration Approaches

### Option A: Port Tukuy Transformers to JS Handlers

Rewrite Tukuy's pure transformations as JS handler functions following Cacao's `handler(signals, data) => void` pattern. This would add ~30-40 new built-in handlers.

**New handler files:**
```
handlers/
├── encoders.js      (existing)
├── generators.js    (existing)
├── converters.js    (existing)
├── text.js          (existing - expand with Tukuy text ops)
├── crypto.js        (existing)
├── numerical.js     (NEW - from Tukuy numerical plugin)
├── validation.js    (NEW - from Tukuy validation plugin)
├── datetime.js      (NEW - from Tukuy date plugin)
└── html.js          (NEW - from Tukuy HTML plugin, needs browser DOM)
```

**Pros**: Works in static builds (no server), fast (client-side), self-contained
**Cons**: Maintaining two implementations (Python + JS), some Tukuy features need Python libs (beautifulsoup, python-slugify)

### Option B: Tukuy as Server-Side Transform Pipeline

In WebSocket mode, expose Tukuy transformations as a server-side processing layer. Components can declare transformation chains that run on the server.

```python
# Python API concept
c.input(label="Email", on_change=c.transform(
    ["strip", "lowercase", "email_validator"],
    output="validated_email"
))
```

**Pros**: Full Tukuy power, no JS rewrite, leverages Python ecosystem
**Cons**: Only works in WebSocket mode (not static builds), adds latency

### Option C: Hybrid - JS for Simple, Server for Complex

Port the simple/pure transformers to JS (text, case, number formatting) and keep complex ones server-side (HTML extraction with CSS selectors, date with timezone, validation with domain checks).

**Pros**: Best of both worlds, practical split
**Cons**: Two systems to understand, need clear boundary

### Option D: Tukuy DSL as Handler Configuration

Use Tukuy's transformation chain syntax as the declarative format for configuring Cacao handlers. Instead of writing JS handlers, users define chains:

```python
c.input(
    label="Text",
    on_change=c.chain(["strip", "lowercase", {"function": "truncate", "length": 50}]),
    output="result"
)
```

The chain definition gets serialized to JSON and interpreted by a generic JS chain executor on the client.

**Pros**: Single syntax for both modes, Tukuy becomes the "language" of transforms
**Cons**: Needs a JS interpreter for the chain format, limited to what JS can do client-side

---

## Recommendation

**Start with Option A (targeted port) + Option D (chain syntax).**

### Phase 1: Port High-Value Pure Transformers to JS
Focus on transformers that are pure functions and don't need Python libraries:

**Priority 1 - Easy wins (pure JS, high utility):**
- `numerical.js`: round, abs, floor, ceil, clamp, scale, format_number, percentage, math_operation, extract_numbers, shorthand_number
- `validation.js`: email_validator (regex-based), phone_formatter (regex-based), type_enforcer
- Expand `text.js`: truncate, replace, slugify (simple JS port), template, remove_emojis, split
- Expand `converters.js`: more case styles (already has 8, add slugify)

**Priority 2 - Medium effort:**
- `datetime.js`: date formatting (use `Intl.DateTimeFormat`), duration calc, age calc, timezone convert (use `Intl` API)
- `html.js`: strip_tags (regex or DOMParser), link_extraction (DOMParser), domain extraction (URL API)

**Priority 3 - Consider leaving server-side:**
- HTML sanitize (security-sensitive, better with trusted lib)
- CSS selector extraction (need DOM context)
- Credit card validation (Luhn algorithm is easy, but masking logic is complex)
- JSONPath extraction (needs a mini JSONPath interpreter)

### Phase 2: Implement Chain Executor
Build a lightweight chain executor in JS that interprets Tukuy-style transformation arrays:

```javascript
// In static-runtime.js or new chain-executor.js
function executeChain(chain, input, signals) {
    let value = input;
    for (const step of chain) {
        const name = typeof step === 'string' ? step : step.function;
        const params = typeof step === 'string' ? {} : step;
        value = transforms[name](value, params);
    }
    return value;
}
```

This would let `cacao build` apps use Tukuy-style chains entirely client-side.

### Phase 3: Tukuy as Optional Python Dependency
Make Tukuy an optional dependency (`pip install cacao[transforms]`) for server-side mode. When running with `cacao run`, transformations go through Tukuy on the server. When using `cacao build`, they use the JS ports.

---

## What This Unlocks

1. **Richer static tool apps**: Number formatters, date converters, validators, text processors - all without a server
2. **Consistent transformation API**: Same chain syntax works in both `cacao run` and `cacao build`
3. **Tukuy gets a visual frontend**: Every Tukuy transformer becomes a drag-and-use tool in Cacao dashboards
4. **Cross-pollination**: Tukuy's plugin system could inform how users add custom Cacao handlers

---

## Concrete Example: What a Tukuy-Powered Cacao App Could Look Like

```python
import cacao as c

c.title("Data Transformer")
input_text = c.signal("", name="input")
c.textarea(label="Input", on_change="set_input")

c.tabs(
    labels=["Text", "Numbers", "Dates", "Validate"],
    on_change="switch_tab"
)

# Text tab - all powered by ported Tukuy transforms
c.button("Lowercase", on_click="text_lowercase")
c.button("Slugify", on_click="text_slugify")
c.button("Truncate (50)", on_click="text_truncate")
c.button("Remove Emojis", on_click="text_remove_emojis")
c.button("Redact Emails", on_click="text_redact_sensitive")

# Numbers tab
c.button("Format Number", on_click="num_format")
c.button("Round to 2dp", on_click="num_round")
c.button("Percentage", on_click="num_percentage")
c.button("Extract Numbers", on_click="num_extract")

# Dates tab
c.button("Parse Date", on_click="date_parse")
c.button("Calculate Age", on_click="date_age")
c.button("Time Until", on_click="date_duration")

# Validation tab
c.button("Validate Email", on_click="validate_email")
c.button("Format Phone", on_click="validate_phone")

c.code(signal="output")
```

All of this would work as a **static build** deployed to GitHub Pages with zero server.
