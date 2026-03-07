# Tukuy + Cacao Integration

## Status: Implemented

The integration is live. Tukuy's JS engine is bundled into Cacao's frontend, making all 62 transformers available in static builds with zero server.

---

## Architecture

```
Tukuy (single source of truth)
├── tukuy/plugins/          # Python transformers (server-side)
└── js/src/transformers/    # JS ports (client-side)
        │
        │  npm file: dependency
        ▼
Cacao (consumer)
├── frontend/src/handlers/tukuy-bridge.js   # Auto-wraps every Tukuy transformer
├── frontend/src/handlers/index.js          # Includes tukuy bridge with other handlers
└── frontend/dist/cacao.js                  # Tukuy bundled in (esbuild)
```

### How it works

1. **Tukuy owns the transformers** — both Python and JS versions live in the Tukuy repo
2. **Cacao depends on Tukuy's JS** via `"tukuy": "file:../../../Tukuy/js"` in package.json
3. **The bridge auto-generates handlers** — every Tukuy transformer becomes `tukuy_<name>`
4. **esbuild bundles everything** — end users get it all in `cacao.js`, no extra setup

### Handler naming

- `tukuy_slugify` — run the slugify transformer
- `tukuy_chain` — run a chain of transformers
- `tukuy_browse` — list all available transformers
- `tukuy_list` — get metadata as JSON

### Usage in Cacao apps

```python
import cacao as c

# Direct transform — uses tukuy_slugify handler in static builds
c.input(label="Text", on_change="tukuy_slugify")
c.code(signal="tukuy_out")

# Chain — runs multiple transforms in sequence
c.static_handler("process_text", """
  async function(signals, data) {
    // Access the Tukuy chain via built-in handler
    const steps = ["strip", "lowercase", "slugify"];
    await signals.dispatch("tukuy_chain", { value: data.value, steps });
  }
""")

# Or use the chain with options
c.static_handler("format_number", """
  async function(signals, data) {
    await signals.dispatch("tukuy_round", {
      value: data.value,
      options: { decimals: 2 },
      output: "formatted_number"
    });
  }
""")
```

---

## What's available (62 transformers, 8 categories)

| Category | Count | Transformers |
|----------|-------|-------------|
| **text** | 11 | strip, lowercase, uppercase, title_case, camel_case, snake_case, slugify, truncate, remove_emojis, redact_sensitive, regex, split |
| **encoding** | 6 | url_encode, url_decode, hex_encode, hex_decode, html_entities_encode, html_entities_decode, rot13, unicode_escape, unicode_unescape |
| **crypto** | 4 | hash_text, base64_encode, base64_decode, uuid_generate, hmac_sign |
| **numerical** | 19 | int, float, round, currency_convert, unit_convert, math_operation, extract_numbers, abs, floor, ceil, clamp, scale, stats, format_number, random, pow, sqrt, log, shorthand_number, shorthand_decimal, percentage_calc |
| **date** | 3 | date, duration_calc, age_calc |
| **validation** | 5 | bool, email_validator, phone_formatter, credit_card_check, type_enforcer |
| **json** | 2 | json_parse, json_extract |
| **html** | 5 | strip_html_tags, html_sanitize, link_extraction, extract_domain, resolve_url |

---

## Server-side vs Static builds

| Mode | How Tukuy works |
|------|----------------|
| `cacao run` (WebSocket) | Full Python Tukuy via `tukuy_skills.py` — all 74 plugins, chains, skills, instructions |
| `cacao build` (static) | JS Tukuy via bridge — 62 pure transformers, chains, no server needed |

Both modes share the same transformer names. A chain like `["strip", "lowercase", "slugify"]` works identically in both modes.

---

## Adding new transformers

To add a new transformer that works in both Cacao modes:

1. Add the Python transformer in `Tukuy/tukuy/plugins/<category>/`
2. Add the JS port in `Tukuy/js/src/transformers/<category>.js`
3. Rebuild Tukuy JS: `cd Tukuy/js && npm run build`
4. Rebuild Cacao frontend: `cd Cacao/cacao/frontend && npm run build`

The bridge picks it up automatically — no changes needed in Cacao.

---

## Previous plans (completed)

- ~~Phase 1: Port transformers to JS~~ — Done in Tukuy's `js/` directory
- ~~Phase 2: Chain executor~~ — Done via `tukuy.chain()` + `tukuy_chain` handler
- ~~Phase 3: Tukuy as optional dependency~~ — Done: server-side via `tukuy_skills.py`, client-side via JS bundle
- ~~SecurityContext for Tukuy~~ — Done: `SecurityContext` in `tukuy/safety.py` (see `feedback.md`)
