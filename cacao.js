(() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __esm = (fn, res) => function __init() {
    return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
  };
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };

  // src/handlers/encoders.js
  var encoders;
  var init_encoders = __esm({
    "src/handlers/encoders.js"() {
      encoders = {
        // Base64
        base64_encode: (signals) => {
          signals.set("base64_mode", "encode");
        },
        base64_decode: (signals) => {
          signals.set("base64_mode", "decode");
        },
        base64_process: (signals, data) => {
          const text2 = data.value || "";
          const mode = signals.get("base64_mode") || "encode";
          if (!text2) {
            signals.set("base64_out", "");
            return;
          }
          try {
            if (mode === "encode") {
              signals.set("base64_out", btoa(unescape(encodeURIComponent(text2))));
            } else {
              signals.set("base64_out", decodeURIComponent(escape(atob(text2))));
            }
          } catch (e) {
            signals.set("base64_out", "Error: " + e.message);
          }
        },
        // URL encoding
        url_encode: (signals) => {
          signals.set("url_mode", "encode");
        },
        url_decode: (signals) => {
          signals.set("url_mode", "decode");
        },
        url_process: (signals, data) => {
          const text2 = data.value || "";
          const mode = signals.get("url_mode") || "encode";
          if (!text2) {
            signals.set("url_out", "");
            return;
          }
          try {
            if (mode === "encode") {
              signals.set("url_out", encodeURIComponent(text2));
            } else {
              signals.set("url_out", decodeURIComponent(text2));
            }
          } catch (e) {
            signals.set("url_out", "Error: " + e.message);
          }
        },
        // HTML entities
        html_encode: (signals) => {
          signals.set("html_mode", "encode");
        },
        html_decode: (signals) => {
          signals.set("html_mode", "decode");
        },
        html_process: (signals, data) => {
          const text2 = data.value || "";
          const mode = signals.get("html_mode") || "encode";
          if (!text2) {
            signals.set("html_out", "");
            return;
          }
          try {
            if (mode === "encode") {
              const div = document.createElement("div");
              div.textContent = text2;
              signals.set("html_out", div.innerHTML);
            } else {
              const div = document.createElement("div");
              div.innerHTML = text2;
              signals.set("html_out", div.textContent);
            }
          } catch (e) {
            signals.set("html_out", "Error: " + e.message);
          }
        },
        // JWT decoder
        jwt_decode: (signals, data) => {
          const token = (data.value || "").trim();
          if (!token) {
            signals.set("jwt_header", "{}");
            signals.set("jwt_payload", "{}");
            return;
          }
          try {
            const parts = token.split(".");
            if (parts.length !== 3) {
              throw new Error("Invalid JWT format - expected 3 parts");
            }
            const header = JSON.parse(atob(parts[0].replace(/-/g, "+").replace(/_/g, "/")));
            signals.set("jwt_header", JSON.stringify(header, null, 2));
            const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));
            signals.set("jwt_payload", JSON.stringify(payload, null, 2));
          } catch (e) {
            signals.set("jwt_header", "Error: " + e.message);
            signals.set("jwt_payload", "");
          }
        }
      };
    }
  });

  // src/handlers/generators.js
  var generators;
  var init_generators = __esm({
    "src/handlers/generators.js"() {
      generators = {
        // UUID
        gen_uuid: (signals) => {
          const uuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
            const r = Math.random() * 16 | 0;
            const v2 = c === "x" ? r : r & 3 | 8;
            return v2.toString(16);
          });
          signals.set("uuid_result", uuid);
        },
        // Password
        gen_password: (signals) => {
          const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
          const length = signals.get("pwd_length") || 16;
          let password = "";
          const array = new Uint32Array(length);
          crypto.getRandomValues(array);
          for (let i = 0; i < length; i++) {
            password += chars[array[i] % chars.length];
          }
          signals.set("password", password);
        },
        set_pwd_length: (signals, data) => {
          signals.set("pwd_length", parseInt(data.value) || 16);
        },
        // Lorem Ipsum
        gen_lorem: (signals) => {
          const LOREM_WORDS = [
            "lorem",
            "ipsum",
            "dolor",
            "sit",
            "amet",
            "consectetur",
            "adipiscing",
            "elit",
            "sed",
            "do",
            "eiusmod",
            "tempor",
            "incididunt",
            "ut",
            "labore",
            "et",
            "dolore",
            "magna",
            "aliqua",
            "enim",
            "ad",
            "minim",
            "veniam"
          ];
          const genSentence = () => {
            const length = 8 + Math.floor(Math.random() * 9);
            const words = [];
            for (let i = 0; i < length; i++) {
              words.push(LOREM_WORDS[Math.floor(Math.random() * LOREM_WORDS.length)]);
            }
            words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
            return words.join(" ") + ".";
          };
          const genParagraph = () => {
            const count = 4 + Math.floor(Math.random() * 5);
            const sentences = [];
            for (let i = 0; i < count; i++) {
              sentences.push(genSentence());
            }
            return sentences.join(" ");
          };
          const paraCount = signals.get("lorem_para") || 3;
          const paragraphs = [];
          for (let i = 0; i < paraCount; i++) {
            paragraphs.push(genParagraph());
          }
          signals.set("lorem_out", paragraphs.join("\n\n"));
        },
        set_lorem_para: (signals, data) => {
          signals.set("lorem_para", parseInt(data.value) || 3);
        }
      };
    }
  });

  // src/handlers/converters.js
  var converters;
  var init_converters = __esm({
    "src/handlers/converters.js"() {
      converters = {
        // JSON to YAML
        convert_yaml: (signals, data) => {
          const text2 = (data.value || "").trim();
          if (!text2) {
            signals.set("yaml_out", "");
            return;
          }
          const toYaml = (obj, indent = 0) => {
            const prefix = "  ".repeat(indent);
            const lines = [];
            if (Array.isArray(obj)) {
              obj.forEach((item) => {
                if (typeof item === "object" && item !== null) {
                  lines.push(prefix + "-");
                  lines.push(toYaml(item, indent + 1));
                } else {
                  lines.push(prefix + "- " + item);
                }
              });
            } else if (typeof obj === "object" && obj !== null) {
              Object.entries(obj).forEach(([key, value]) => {
                if (typeof value === "object" && value !== null) {
                  lines.push(prefix + key + ":");
                  lines.push(toYaml(value, indent + 1));
                } else {
                  lines.push(prefix + key + ": " + value);
                }
              });
            }
            return lines.join("\n");
          };
          try {
            const parsed = JSON.parse(text2);
            signals.set("yaml_out", toYaml(parsed));
          } catch (e) {
            signals.set("yaml_out", "Error: " + e.message);
          }
        },
        // Case converter
        convert_case: (signals, data) => {
          const text2 = data.value || "";
          if (!text2) {
            signals.set("case_out", "");
            return;
          }
          const words = text2.replace(/-/g, " ").replace(/_/g, " ").split(/\s+/).filter((w2) => w2);
          const results = [
            "lowercase:     " + text2.toLowerCase(),
            "UPPERCASE:     " + text2.toUpperCase(),
            "Title Case:    " + text2.split(" ").map((w2) => w2.charAt(0).toUpperCase() + w2.slice(1).toLowerCase()).join(" "),
            "camelCase:     " + (words.length ? words[0].toLowerCase() + words.slice(1).map((w2) => w2.charAt(0).toUpperCase() + w2.slice(1).toLowerCase()).join("") : ""),
            "PascalCase:    " + words.map((w2) => w2.charAt(0).toUpperCase() + w2.slice(1).toLowerCase()).join(""),
            "snake_case:    " + words.map((w2) => w2.toLowerCase()).join("_"),
            "kebab-case:    " + words.map((w2) => w2.toLowerCase()).join("-"),
            "CONSTANT_CASE: " + words.map((w2) => w2.toUpperCase()).join("_")
          ];
          signals.set("case_out", results.join("\n"));
        },
        // Number base converter
        convert_base: (signals, data) => {
          const value = (data.value || "").trim();
          if (!value) {
            signals.set("base_out", "");
            return;
          }
          try {
            const num = parseInt(value, 10);
            if (isNaN(num)) {
              throw new Error("Invalid decimal number");
            }
            const results = [
              "Binary:      " + num.toString(2),
              "Octal:       " + num.toString(8),
              "Decimal:     " + num.toString(10),
              "Hexadecimal: " + num.toString(16).toUpperCase()
            ];
            signals.set("base_out", results.join("\n"));
          } catch (e) {
            signals.set("base_out", "Error: " + e.message);
          }
        }
      };
    }
  });

  // src/handlers/text.js
  function testRegex(signals) {
    const pattern = signals.get("regex_pattern") || "";
    const text2 = signals.get("regex_text") || "";
    if (!pattern || !text2) {
      signals.set("regex_out", "Enter a pattern and test text");
      return;
    }
    try {
      const regex = new RegExp(pattern, "g");
      const matches = [...text2.matchAll(regex)];
      if (matches.length === 0) {
        signals.set("regex_out", "No matches found");
        return;
      }
      const lines = [`Found ${matches.length} match(es):`, ""];
      matches.forEach((m2, i) => {
        lines.push(`Match ${i + 1}: "${m2[0]}"`);
        lines.push(`  Position: ${m2.index}-${m2.index + m2[0].length}`);
        if (m2.length > 1) {
          for (let j2 = 1; j2 < m2.length; j2++) {
            lines.push(`  Group ${j2}: "${m2[j2]}"`);
          }
        }
        lines.push("");
      });
      signals.set("regex_out", lines.join("\n"));
    } catch (e) {
      signals.set("regex_out", "Invalid regex: " + e.message);
    }
  }
  var text;
  var init_text = __esm({
    "src/handlers/text.js"() {
      text = {
        // Text statistics
        analyze_text: (signals, data) => {
          const text2 = data.value || "";
          if (!text2) {
            signals.set("stats_out", "");
            return;
          }
          const chars = text2.length;
          const charsNoSpaces = text2.replace(/\s/g, "").length;
          const words = text2.split(/\s+/).filter((w2) => w2.length > 0).length;
          const lines = text2.split("\n").length;
          const sentences = Math.max(0, text2.split(/[.!?]+/).filter((s) => s.trim().length > 0).length);
          const avgWord = words > 0 ? (charsNoSpaces / words).toFixed(2) : 0;
          const readingTime = Math.max(1, Math.floor(words / 200));
          const output = `Characters:           ${chars.toLocaleString()}
Characters (no space): ${charsNoSpaces.toLocaleString()}
Words:                ${words.toLocaleString()}
Lines:                ${lines.toLocaleString()}
Sentences:            ${sentences.toLocaleString()}
Avg word length:      ${avgWord}
Reading time:         ~${readingTime} min`;
          signals.set("stats_out", output);
        },
        // Regex tester
        set_regex_pattern: (signals, data) => {
          signals.set("regex_pattern", data.value || "");
          testRegex(signals);
        },
        set_regex_text: (signals, data) => {
          signals.set("regex_text", data.value || "");
          testRegex(signals);
        }
      };
    }
  });

  // src/handlers/crypto.js
  async function computeHmac(signals) {
    const msg = signals.get("hmac_msg") || "";
    const key = signals.get("hmac_key") || "";
    if (!msg || !key) {
      signals.set("hmac_out", "Enter message and key");
      return;
    }
    try {
      const encoder = new TextEncoder();
      const keyData = encoder.encode(key);
      const msgData = encoder.encode(msg);
      const cryptoKey = await window.crypto.subtle.importKey(
        "raw",
        keyData,
        { name: "HMAC", hash: "SHA-256" },
        false,
        ["sign"]
      );
      const signature = await window.crypto.subtle.sign("HMAC", cryptoKey, msgData);
      const hmac = Array.from(new Uint8Array(signature)).map((b2) => b2.toString(16).padStart(2, "0")).join("");
      signals.set("hmac_out", "HMAC-SHA256:\n" + hmac);
    } catch (e) {
      signals.set("hmac_out", "Error: " + e.message);
    }
  }
  var crypto2;
  var init_crypto = __esm({
    "src/handlers/crypto.js"() {
      crypto2 = {
        // Hash generator
        compute_hash: async (signals, data) => {
          const text2 = data.value || "";
          if (!text2) {
            signals.set("hash_out", "");
            return;
          }
          const encoder = new TextEncoder();
          const dataBuffer = encoder.encode(text2);
          try {
            const sha256Buffer = await window.crypto.subtle.digest("SHA-256", dataBuffer);
            const sha256 = Array.from(new Uint8Array(sha256Buffer)).map((b2) => b2.toString(16).padStart(2, "0")).join("");
            const sha1Buffer = await window.crypto.subtle.digest("SHA-1", dataBuffer);
            const sha1 = Array.from(new Uint8Array(sha1Buffer)).map((b2) => b2.toString(16).padStart(2, "0")).join("");
            const sha512Buffer = await window.crypto.subtle.digest("SHA-512", dataBuffer);
            const sha512 = Array.from(new Uint8Array(sha512Buffer)).map((b2) => b2.toString(16).padStart(2, "0")).join("");
            const results = [
              "MD5:     (not available in browser)",
              "SHA-1:   " + sha1,
              "SHA-256: " + sha256,
              "SHA-512: " + sha512
            ];
            signals.set("hash_out", results.join("\n"));
          } catch (e) {
            signals.set("hash_out", "Error: " + e.message);
          }
        },
        // HMAC
        set_hmac_msg: (signals, data) => {
          signals.set("hmac_msg", data.value || "");
          computeHmac(signals);
        },
        set_hmac_key: (signals, data) => {
          signals.set("hmac_key", data.value || "");
          computeHmac(signals);
        }
      };
    }
  });

  // src/handlers/_tukuy-shim.js
  var tukuy;
  var init_tukuy_shim = __esm({
    "src/handlers/_tukuy-shim.js"() {
      tukuy = null;
    }
  });

  // src/handlers/tukuy-bridge.js
  function buildTransformHandlers() {
    if (!tukuy)
      return {};
    const handlers = {};
    for (const meta of tukuy.getMetadata()) {
      handlers[`tukuy_${meta.name}`] = async (signals, data) => {
        const input = data.value !== void 0 ? data.value : "";
        const outputSignal = data.output || "tukuy_out";
        try {
          const result = await tukuy.transform(meta.name, input, data.options || {});
          const formatted = typeof result === "object" && result !== null ? JSON.stringify(result, null, 2) : String(result);
          signals.set(outputSignal, formatted);
        } catch (e) {
          signals.set(outputSignal, "Error: " + e.message);
        }
      };
    }
    return handlers;
  }
  function buildChainHandler() {
    if (!tukuy)
      return {};
    return {
      tukuy_chain: async (signals, data) => {
        const input = data.value !== void 0 ? data.value : "";
        const outputSignal = data.output || "tukuy_out";
        let steps;
        if (data.steps) {
          steps = data.steps;
        } else {
          const raw = signals.get("tukuy_chain_steps");
          if (!raw) {
            signals.set(outputSignal, "Error: No chain steps provided");
            return;
          }
          try {
            steps = JSON.parse(raw);
          } catch {
            signals.set(outputSignal, "Error: Invalid chain steps JSON");
            return;
          }
        }
        if (!Array.isArray(steps) || steps.length === 0) {
          signals.set(outputSignal, "Error: Chain steps must be a non-empty array");
          return;
        }
        try {
          const { output } = await tukuy.chain(steps, input);
          const formatted = typeof output === "object" && output !== null ? JSON.stringify(output, null, 2) : String(output);
          signals.set(outputSignal, formatted);
        } catch (e) {
          signals.set(outputSignal, "Error: " + e.message);
        }
      }
    };
  }
  function buildBrowseHandlers() {
    if (!tukuy)
      return {};
    return {
      tukuy_browse: (signals) => {
        const byCategory = tukuy.getMetadataByCategory();
        const lines = [];
        for (const [cat, items] of Object.entries(byCategory)) {
          lines.push(`\u2500\u2500 ${cat} (${items.length}) \u2500\u2500`);
          for (const item of items) {
            const paramStr = item.params.length > 0 ? ` (${item.params.map((p) => p.name).join(", ")})` : "";
            lines.push(`  ${item.name}${paramStr} \u2014 ${item.description}`);
          }
          lines.push("");
        }
        signals.set("tukuy_out", lines.join("\n"));
      },
      tukuy_list: (signals) => {
        signals.set("tukuy_out", JSON.stringify(tukuy.getMetadataByCategory(), null, 2));
      }
    };
  }
  var tukuyHandlers;
  var init_tukuy_bridge = __esm({
    "src/handlers/tukuy-bridge.js"() {
      init_tukuy_shim();
      tukuyHandlers = {
        ...buildTransformHandlers(),
        ...buildChainHandler(),
        ...buildBrowseHandlers()
      };
    }
  });

  // src/handlers/index.js
  var builtinHandlers;
  var init_handlers = __esm({
    "src/handlers/index.js"() {
      init_encoders();
      init_generators();
      init_converters();
      init_text();
      init_crypto();
      init_tukuy_bridge();
      builtinHandlers = {
        ...encoders,
        ...generators,
        ...converters,
        ...text,
        ...crypto2,
        ...tukuyHandlers
      };
    }
  });

  // src/components/core/static-runtime.js
  var static_runtime_exports = {};
  __export(static_runtime_exports, {
    builtinHandlers: () => builtinHandlers,
    cacaoStatic: () => cacaoStatic,
    initStaticMode: () => initStaticMode,
    isStaticMode: () => isStaticMode,
    staticDispatcher: () => staticDispatcher,
    staticSignals: () => staticSignals
  });
  function isStaticMode() {
    return window.__CACAO_STATIC__ === true;
  }
  function initStaticMode(config) {
    window.__CACAO_STATIC__ = true;
    if (config.signals) {
      staticSignals.init(config.signals);
    }
    if (config.handlers) {
      staticDispatcher.registerAll(config.handlers);
    }
    if (config.pages) {
      window.__CACAO_PAGES__ = config.pages;
    }
    const builtinCount = Object.keys(builtinHandlers).length;
    const customCount = Object.keys(config.handlers || {}).length;
    console.log(`[Cacao Static] Initialized with ${Object.keys(config.signals || {}).length} signals, ${builtinCount} built-in handlers, ${customCount} custom handlers`);
  }
  var StaticSignals, StaticEventDispatcher, staticSignals, staticDispatcher, cacaoStatic;
  var init_static_runtime = __esm({
    "src/components/core/static-runtime.js"() {
      init_handlers();
      StaticSignals = class {
        constructor() {
          this.signals = {};
          this.listeners = /* @__PURE__ */ new Set();
        }
        init(initialState) {
          this.signals = { ...initialState };
          window.__cacao_signals__ = this.signals;
          this.notifyListeners();
        }
        get(name) {
          return this.signals[name];
        }
        set(name, value) {
          this.signals[name] = value;
          window.__cacao_signals__ = this.signals;
          this.notifyListeners();
        }
        getAll() {
          return { ...this.signals };
        }
        subscribe(listener) {
          this.listeners.add(listener);
          return () => this.listeners.delete(listener);
        }
        notifyListeners() {
          this.listeners.forEach((listener) => listener(this.signals));
        }
      };
      StaticEventDispatcher = class {
        constructor(signalStore) {
          this.handlers = { ...builtinHandlers };
          this.signals = signalStore;
        }
        register(eventName, handler) {
          this.handlers[eventName] = handler;
        }
        registerAll(handlers) {
          Object.entries(handlers).forEach(([name, handler]) => {
            this.handlers[name] = handler;
          });
        }
        dispatch(eventName, eventData = {}) {
          const handler = this.handlers[eventName];
          if (handler) {
            try {
              const result = handler(this.signals, eventData);
              if (result && typeof result.catch === "function") {
                result.catch((e) => console.error(`[Cacao Static] Error in async handler "${eventName}":`, e));
              }
            } catch (e) {
              console.error(`[Cacao Static] Error in handler "${eventName}":`, e);
            }
          } else {
            console.warn(`[Cacao Static] No handler for event: ${eventName}`);
          }
        }
      };
      staticSignals = new StaticSignals();
      staticDispatcher = new StaticEventDispatcher(staticSignals);
      cacaoStatic = {
        connected: true,
        signals: staticSignals.signals,
        getSignal(name) {
          return staticSignals.get(name);
        },
        sendEvent(eventName, eventData = {}) {
          staticDispatcher.dispatch(eventName, eventData);
        },
        subscribe(listener) {
          return staticSignals.subscribe(listener);
        }
      };
    }
  });

  // src/components/core/constants.js
  var COLORS = [
    "#d4a574",
    "#8b5a3c",
    "#7cb342",
    "#64b5f6",
    "#ffb74d",
    "#e57373",
    "#a1887f",
    "#90a4ae",
    "#ce93d8",
    "#80cbc4"
  ];

  // src/components/core/utils.js
  function formatValue(v2) {
    if (v2 === null || v2 === void 0)
      return "-";
    if (typeof v2 === "number")
      return v2.toLocaleString();
    return String(v2);
  }

  // src/components/core/ChartWrapper.js
  var { createElement: h, useEffect, useRef } = React;
  function ChartWrapper({ type, data, options, height }) {
    const canvasRef = useRef(null);
    const chartRef = useRef(null);
    useEffect(() => {
      if (!canvasRef.current || !data)
        return;
      if (chartRef.current)
        chartRef.current.destroy();
      const ctx = canvasRef.current.getContext("2d");
      Chart.defaults.color = "#c4a98a";
      Chart.defaults.borderColor = "rgba(139, 115, 85, 0.2)";
      chartRef.current = new Chart(ctx, {
        type,
        data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: data.datasets?.length > 1 } },
          ...options
        }
      });
      return () => {
        if (chartRef.current)
          chartRef.current.destroy();
      };
    }, [type, JSON.stringify(data)]);
    return h(
      "div",
      { style: { height: height || 300, width: "100%" } },
      h("canvas", { ref: canvasRef })
    );
  }

  // src/components/index.js
  init_static_runtime();

  // src/components/core/shortcuts.js
  var shortcuts = {};
  function registerShortcut(combo, handler, description) {
    shortcuts[combo] = { handler, description };
  }
  function initShortcuts() {
    document.addEventListener("keydown", (e) => {
      const tag = e.target.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
        const combo2 = buildCombo(e);
        if (combo2 !== "mod+k")
          return;
      }
      const combo = buildCombo(e);
      if (shortcuts[combo]) {
        e.preventDefault();
        shortcuts[combo].handler();
      }
    });
  }
  function buildCombo(e) {
    const parts = [];
    if (e.metaKey || e.ctrlKey)
      parts.push("mod");
    if (e.shiftKey)
      parts.push("shift");
    if (e.altKey)
      parts.push("alt");
    parts.push(e.key.toLowerCase());
    return parts.join("+");
  }
  function getShortcuts() {
    return Object.entries(shortcuts).map(([combo, { description }]) => ({
      combo,
      description
    }));
  }

  // src/components/core/ThemeToggle.js
  var STORAGE_KEY = "cacao-theme";
  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }
  function getTheme() {
    return document.documentElement.getAttribute("data-theme") || "dark";
  }
  function initTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved)
      return;
    const serverTheme = document.documentElement.getAttribute("data-theme") || "dark";
    const serverFamily = serverTheme.replace("-light", "");
    const savedFamily = saved.replace("-light", "");
    if (serverFamily === savedFamily) {
      setTheme(saved);
    }
  }
  function toggleTheme() {
    const current = getTheme();
    const next = current === "dark" ? "light" : "dark";
    setTheme(next);
    return next;
  }

  // src/components/core/Toast.js
  var { createElement: h2, useState, useEffect: useEffect2, useCallback, useRef: useRef2 } = React;
  var _addToast = null;
  var _toastId = 0;
  function showToast(message, options = {}) {
    const { type = "info", duration = 4e3 } = options;
    if (_addToast) {
      _addToast({ id: ++_toastId, message, type, duration });
    }
  }
  window.CacaoToast = { show: showToast };
  function ToastContainer() {
    const [toasts, setToasts] = useState([]);
    const timersRef = useRef2({});
    useEffect2(() => {
      _addToast = (toast) => {
        setToasts((prev) => [...prev, toast]);
        if (toast.duration > 0) {
          timersRef.current[toast.id] = setTimeout(() => {
            dismissToast(toast.id);
          }, toast.duration);
        }
      };
      return () => {
        _addToast = null;
      };
    }, []);
    const dismissToast = useCallback((id) => {
      setToasts((prev) => prev.map(
        (t) => t.id === id ? { ...t, exiting: true } : t
      ));
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 150);
      if (timersRef.current[id]) {
        clearTimeout(timersRef.current[id]);
        delete timersRef.current[id];
      }
    }, []);
    useEffect2(() => {
      return () => {
        Object.values(timersRef.current).forEach(clearTimeout);
      };
    }, []);
    if (toasts.length === 0)
      return null;
    return h2(
      "div",
      { className: "toast-container", "aria-live": "polite", "aria-label": "Notifications" },
      toasts.map(
        (toast) => h2("div", {
          key: toast.id,
          className: "toast toast-" + toast.type + (toast.exiting ? " exiting" : ""),
          role: "status"
        }, [
          h2("span", { key: "msg", className: "toast-message" }, toast.message),
          h2("button", {
            key: "close",
            className: "toast-close",
            onClick: () => dismissToast(toast.id),
            "aria-label": "Dismiss"
          }, "\xD7")
        ])
      )
    );
  }

  // src/components/core/CommandPalette.js
  var { createElement: h3, useState: useState2, useEffect: useEffect3, useRef: useRef3, useCallback: useCallback2 } = React;
  var _setOpen = null;
  var _commands = [];
  function openCommandPalette() {
    if (_setOpen)
      _setOpen(true);
  }
  function registerCommand(id, label, handler, options = {}) {
    _commands = _commands.filter((c) => c.id !== id);
    _commands.push({ id, label, handler, shortcut: options.shortcut || null, icon: options.icon || null });
  }
  registerCommand("theme-toggle", "Toggle Theme (Dark/Light)", () => {
    toggleTheme();
  }, { shortcut: "mod+shift+t" });
  registerShortcut("mod+k", () => openCommandPalette(), "Open command palette");
  registerShortcut("mod+shift+t", () => toggleTheme(), "Toggle theme");
  function fuzzyMatch(query, text2) {
    if (!query)
      return true;
    const q2 = query.toLowerCase();
    const t = text2.toLowerCase();
    return t.includes(q2);
  }
  function CommandPalette({ setActiveTab, pages }) {
    const [open, setOpen] = useState2(false);
    const [query, setQuery] = useState2("");
    const [activeIndex, setActiveIndex] = useState2(0);
    const inputRef = useRef3(null);
    const resultsRef = useRef3(null);
    useEffect3(() => {
      _setOpen = setOpen;
      return () => {
        _setOpen = null;
      };
    }, []);
    useEffect3(() => {
      if (open) {
        setQuery("");
        setActiveIndex(0);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
    }, [open]);
    useEffect3(() => {
      if (!open)
        return;
      const handleKey = (e) => {
        if (e.key === "Escape") {
          e.preventDefault();
          setOpen(false);
          return;
        }
        if (e.key === "Tab") {
          e.preventDefault();
        }
      };
      document.addEventListener("keydown", handleKey);
      return () => document.removeEventListener("keydown", handleKey);
    }, [open]);
    const allItems = useCallback2(() => {
      const items = [];
      if (pages) {
        const pageKeys = Object.keys(pages);
        pageKeys.forEach((key) => {
          if (key === "/")
            return;
          items.push({
            id: "page:" + key,
            label: "Go to " + key,
            handler: () => {
              if (setActiveTab)
                setActiveTab(key);
            },
            icon: null,
            shortcut: null
          });
        });
      }
      items.push(..._commands);
      const registeredShortcuts = getShortcuts();
      registeredShortcuts.forEach(({ combo, description }) => {
        if (!items.find((i) => i.shortcut === combo)) {
          items.push({
            id: "shortcut:" + combo,
            label: description,
            handler: null,
            icon: null,
            shortcut: combo
          });
        }
      });
      return items;
    }, [pages, setActiveTab]);
    const filtered = allItems().filter((item) => fuzzyMatch(query, item.label));
    useEffect3(() => {
      if (activeIndex >= filtered.length) {
        setActiveIndex(Math.max(0, filtered.length - 1));
      }
    }, [filtered.length, activeIndex]);
    useEffect3(() => {
      if (!resultsRef.current)
        return;
      const active = resultsRef.current.children[activeIndex];
      if (active)
        active.scrollIntoView({ block: "nearest" });
    }, [activeIndex]);
    const handleKeyDown = useCallback2((e) => {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setActiveIndex((i) => Math.max(i - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          if (filtered[activeIndex]?.handler) {
            filtered[activeIndex].handler();
            setOpen(false);
          }
          break;
      }
    }, [filtered, activeIndex]);
    const handleSelect = useCallback2((item) => {
      if (item.handler) {
        item.handler();
        setOpen(false);
      }
    }, []);
    if (!open)
      return null;
    return h3(
      "div",
      {
        className: "cmd-palette-overlay",
        role: "dialog",
        "aria-modal": "true",
        "aria-label": "Command palette",
        onClick: (e) => {
          if (e.target === e.currentTarget)
            setOpen(false);
        }
      },
      h3("div", { className: "cmd-palette" }, [
        h3("input", {
          key: "input",
          ref: inputRef,
          className: "cmd-palette-input",
          placeholder: "Search commands...",
          value: query,
          onChange: (e) => {
            setQuery(e.target.value);
            setActiveIndex(0);
          },
          onKeyDown: handleKeyDown,
          role: "combobox",
          "aria-expanded": "true",
          "aria-controls": "cmd-palette-listbox",
          "aria-activedescendant": filtered[activeIndex] ? "cmd-item-" + activeIndex : void 0,
          "aria-autocomplete": "list"
        }),
        h3(
          "div",
          {
            key: "results",
            className: "cmd-palette-results",
            ref: resultsRef,
            id: "cmd-palette-listbox",
            role: "listbox"
          },
          filtered.length > 0 ? filtered.map(
            (item, i) => h3("div", {
              key: item.id,
              id: "cmd-item-" + i,
              className: "cmd-palette-item" + (i === activeIndex ? " active" : ""),
              role: "option",
              "aria-selected": i === activeIndex,
              onClick: () => handleSelect(item),
              onMouseEnter: () => setActiveIndex(i)
            }, [
              h3("span", { key: "label" }, item.label),
              item.shortcut && h3(
                "span",
                { key: "shortcut", className: "cmd-palette-shortcut" },
                formatShortcut(item.shortcut)
              )
            ])
          ) : h3("div", { className: "cmd-palette-item", role: "option" }, "No results found")
        )
      ])
    );
  }
  function formatShortcut(combo) {
    const isMac = navigator.platform.indexOf("Mac") !== -1;
    return combo.replace("mod", isMac ? "\u2318" : "Ctrl").replace("shift", isMac ? "\u21E7" : "Shift").replace("alt", isMac ? "\u2325" : "Alt").replace(/\+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  // src/components/core/PanelManager.js
  var _zCounter = 900;
  var PanelManager = {
    bringToFront(panelElement) {
      if (!panelElement)
        return;
      _zCounter++;
      panelElement.style.setProperty("--panel-z", _zCounter);
      panelElement.style.zIndex = _zCounter;
    },
    reset() {
      _zCounter = 900;
    }
  };
  window.CacaoPanelManager = PanelManager;

  // src/components/layout/index.js
  var layout_exports = {};
  __export(layout_exports, {
    AppShell: () => AppShell,
    Col: () => Col,
    Container: () => Container,
    Grid: () => Grid,
    Hero: () => Hero,
    NavGroup: () => NavGroup,
    NavItem: () => NavItem,
    NavPanel: () => NavPanel,
    NavSidebar: () => NavSidebar,
    Panel: () => Panel,
    Row: () => Row,
    ShellContent: () => ShellContent,
    Sidebar: () => Sidebar,
    Split: () => Split,
    Stack: () => Stack
  });

  // src/components/core/icons.js
  var { createElement: h4 } = React;
  var S = {
    xmlns: "http://www.w3.org/2000/svg",
    width: 16,
    height: 16,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round"
  };
  function svg(...children) {
    return h4("svg", S, children);
  }
  function pa(d) {
    return h4("path", { d });
  }
  function ci(cx, cy, r) {
    return h4("circle", { cx, cy, r });
  }
  function ln(x1, y1, x2, y2) {
    return h4("line", { x1, y1, x2, y2 });
  }
  function re(x2, y2, w2, ht, rx) {
    return h4("rect", { x: x2, y: y2, width: w2, height: ht, rx });
  }
  function pl(pts) {
    return h4("polyline", { points: pts });
  }
  function pg(pts) {
    return h4("polygon", { points: pts });
  }
  function el(cx, cy, rx, ry) {
    return h4("ellipse", { cx, cy, rx, ry });
  }
  var ICONS = {
    // --- Navigation ---
    home: () => svg(
      pa("M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"),
      pl("9 22 9 12 15 12 15 22")
    ),
    settings: () => svg(
      ci(12, 12, 3),
      pa("M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z")
    ),
    menu: () => svg(ln(3, 12, 21, 12), ln(3, 6, 21, 6), ln(3, 18, 21, 18)),
    "chevron-down": () => svg(pl("6 9 12 15 18 9")),
    "chevron-right": () => svg(pl("9 18 15 12 9 6")),
    // --- Core plugins ---
    type: () => svg(
      pl("4 7 4 4 20 4 20 7"),
      ln(12, 4, 12, 20),
      ln(8, 20, 16, 20)
    ),
    code: () => svg(pl("16 18 22 12 16 6"), pl("8 6 2 12 8 18")),
    braces: () => svg(
      pa("M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5a2 2 0 0 0 2 2h1"),
      pa("M16 3h1a2 2 0 0 1 2 2v5a2 2 0 0 1 2 2 2 2 0 0 1-2 2v5a2 2 0 0 0-2 2h-1")
    ),
    lock: () => svg(
      re(3, 11, 18, 11, 2),
      pa("M7 11V7a5 5 0 0 1 10 0v4")
    ),
    calendar: () => svg(
      re(3, 4, 18, 18, 2),
      ln(16, 2, 16, 6),
      ln(8, 2, 8, 6),
      ln(3, 10, 21, 10)
    ),
    "check-circle": () => svg(
      pa("M22 11.08V12a10 10 0 1 1-5.93-9.14"),
      pl("22 4 12 14.01 9 11.01")
    ),
    calculator: () => svg(
      re(4, 2, 16, 20, 2),
      ln(8, 6, 16, 6),
      ln(16, 10, 16, 10.01),
      ln(12, 10, 12, 10.01),
      ln(8, 10, 8, 10.01),
      ln(16, 14, 16, 14.01),
      ln(12, 14, 12, 14.01),
      ln(8, 14, 8, 14.01),
      ln(16, 18, 16, 18.01),
      ln(12, 18, 12, 18.01),
      ln(8, 18, 8, 18.01)
    ),
    shuffle: () => svg(
      pl("16 3 21 3 21 8"),
      ln(4, 20, 21, 3),
      pl("21 16 21 21 16 21"),
      ln(15, 15, 21, 21),
      ln(4, 4, 9, 9)
    ),
    "file-code": () => svg(
      pa("M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"),
      pl("14 2 14 8 20 8"),
      ln(10, 13, 8, 15),
      ln(8, 15, 10, 17),
      ln(14, 13, 16, 15),
      ln(16, 15, 14, 17)
    ),
    archive: () => svg(
      pl("21 8 21 21 3 21 3 8"),
      re(1, 3, 22, 5, 0),
      ln(10, 12, 14, 12)
    ),
    palette: () => svg(
      ci(13.5, 6.5, 1.5),
      ci(17, 11, 1.5),
      ci(15.5, 16, 1.5),
      ci(8.5, 16, 1.5),
      ci(6.5, 11, 1.5),
      pa("M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.04-.24-.3-.39-.65-.39-1.04 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-5.17-4.49-9-10-9z")
    ),
    minimize: () => svg(
      pa("M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3")
    ),
    // --- Integration plugins ---
    bitcoin: () => svg(
      pa("M11.767 19.089c4.924.868 6.14-6.025 1.216-6.894m-1.216 6.894L5.86 18.047m5.908 1.042-.347 1.97m1.563-8.864c4.924.869 6.14-6.025 1.215-6.893m-1.215 6.893-6.083-1.043m6.083 1.043-.346 1.97M14.116 2.96l-.346 1.97m-6.2 8.19L1.665 12.08m5.905 1.042.347-1.97")
    ),
    cloud: () => svg(
      pa("M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z")
    ),
    newspaper: () => svg(
      pa("M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"),
      ln(10, 6, 18, 6),
      ln(10, 10, 18, 10),
      ln(10, 14, 14, 14)
    ),
    "map-pin": () => svg(
      pa("M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"),
      ci(12, 10, 3)
    ),
    star: () => svg(
      pg("12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2")
    ),
    "trending-up": () => svg(pl("23 6 13.5 15.5 8.5 10.5 1 18"), pl("17 6 23 6 23 12")),
    ticket: () => svg(
      pa("M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2z"),
      ln(13, 5, 13, 9),
      ln(13, 15, 13, 19)
    ),
    "dollar-sign": () => svg(ln(12, 1, 12, 23), pa("M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6")),
    globe: () => svg(ci(12, 12, 10), ln(2, 12, 22, 12), pa("M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z")),
    music: () => svg(
      pa("M9 18V5l12-2v13"),
      ci(6, 18, 3),
      ci(18, 16, 3)
    ),
    plane: () => svg(
      pa("M17.8 19.2L16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z")
    ),
    phone: () => svg(
      pa("M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z")
    ),
    "calendar-clock": () => svg(
      re(3, 4, 18, 18, 2),
      ln(16, 2, 16, 6),
      ln(8, 2, 8, 6),
      ln(3, 10, 21, 10),
      ci(12, 15, 3),
      ln(12, 14, 12, 15.5),
      ln(12, 15.5, 13.5, 15.5)
    ),
    // --- Data plugins ---
    "file-text": () => svg(
      pa("M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"),
      pl("14 2 14 8 20 8"),
      ln(16, 13, 8, 13),
      ln(16, 17, 8, 17),
      ln(10, 9, 8, 9)
    ),
    database: () => svg(
      el(12, 5, 9, 3),
      pa("M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"),
      pa("M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5")
    ),
    image: () => svg(
      re(3, 3, 18, 18, 2),
      ci(8.5, 8.5, 1.5),
      pl("21 15 16 10 5 21")
    ),
    "file-spreadsheet": () => svg(
      pa("M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"),
      pl("14 2 14 8 20 8"),
      ln(8, 13, 16, 13),
      ln(8, 17, 16, 17),
      ln(12, 9, 12, 21)
    ),
    "file-type": () => svg(
      pa("M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"),
      pl("14 2 14 8 20 8"),
      ln(9, 13, 15, 13),
      ln(12, 13, 12, 20)
    ),
    "git-branch": () => svg(
      ln(6, 3, 6, 15),
      ci(18, 6, 3),
      ci(6, 18, 3),
      pa("M18 9a9 9 0 0 1-9 9")
    ),
    "qr-code": () => svg(
      re(3, 3, 7, 7, 0),
      re(14, 3, 7, 7, 0),
      re(3, 14, 7, 7, 0),
      re(14, 14, 3, 3, 0),
      ln(21, 14, 21, 14.01),
      ln(21, 21, 21, 21.01)
    ),
    "message-square": () => svg(
      pa("M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z")
    ),
    // --- Generic utility ---
    wrench: () => svg(
      pa("M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z")
    ),
    search: () => svg(ci(11, 11, 8), ln(21, 21, 16.65, 16.65)),
    shield: () => svg(pa("M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z")),
    hash: () => svg(ln(4, 9, 20, 9), ln(4, 15, 20, 15), ln(10, 3, 8, 21), ln(16, 3, 14, 21)),
    terminal: () => svg(pl("4 17 10 11 4 5"), ln(12, 19, 20, 19)),
    folder: () => svg(
      pa("M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z")
    ),
    link: () => svg(
      pa("M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"),
      pa("M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71")
    ),
    zap: () => svg(pg("13 2 3 14 12 14 11 22 21 10 12 10 13 2")),
    layers: () => svg(
      pg("12 2 2 7 12 12 22 7 12 2"),
      pl("2 17 12 22 22 17"),
      pl("2 12 12 17 22 12")
    ),
    box: () => svg(
      pa("M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"),
      pl("3.27 6.96 12 12.01 20.73 6.96"),
      ln(12, 22.08, 12, 12)
    ),
    grid: () => svg(
      re(3, 3, 7, 7, 0),
      re(14, 3, 7, 7, 0),
      re(14, 14, 7, 7, 0),
      re(3, 14, 7, 7, 0)
    ),
    cpu: () => svg(
      re(4, 4, 16, 16, 2),
      re(9, 9, 6, 6, 0),
      ln(9, 1, 9, 4),
      ln(15, 1, 15, 4),
      ln(9, 20, 9, 23),
      ln(15, 20, 15, 23),
      ln(20, 9, 23, 9),
      ln(20, 14, 23, 14),
      ln(1, 9, 4, 9),
      ln(1, 14, 4, 14)
    ),
    brain: () => svg(
      pa("M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"),
      pa("M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"),
      ln(12, 5, 12, 18)
    ),
    // --- Theme ---
    sun: () => svg(
      ci(12, 12, 5),
      ln(12, 1, 12, 3),
      ln(12, 21, 12, 23),
      ln(4.22, 4.22, 5.64, 5.64),
      ln(18.36, 18.36, 19.78, 19.78),
      ln(1, 12, 3, 12),
      ln(21, 12, 23, 12),
      ln(4.22, 19.78, 5.64, 18.36),
      ln(18.36, 5.64, 19.78, 4.22)
    ),
    moon: () => svg(
      pa("M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z")
    ),
    // --- Notification ---
    bell: () => svg(
      pa("M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"),
      pa("M13.73 21a2 2 0 0 1-3.46 0")
    ),
    // --- Extra aliases ---
    cog: () => ICONS.settings(),
    file: () => ICONS["file-text"]()
  };
  function getIcon(name) {
    const factory = ICONS[name];
    if (factory)
      return factory();
    return name?.charAt(0)?.toUpperCase() || "";
  }

  // src/components/core/ErrorBoundary.js
  var { createElement: h5, Component } = React;
  var ErrorBoundary = class extends Component {
    constructor(props) {
      super(props);
      this.state = { error: null, errorInfo: null };
    }
    static getDerivedStateFromError(error) {
      return { error };
    }
    componentDidCatch(error, errorInfo) {
      this.setState({ errorInfo });
      console.error(`[Cacao] Component error in <${this.props.componentType || "Unknown"}>:`, error, errorInfo);
    }
    render() {
      if (this.state.error) {
        const { componentType } = this.props;
        const isDebug = window.__CACAO_DEBUG__;
        const errorMessage = this.state.error.message || String(this.state.error);
        return h5(
          "div",
          { className: "cacao-error-boundary" },
          h5(
            "div",
            { className: "cacao-error-boundary__header" },
            h5("span", { className: "cacao-error-boundary__icon" }, "\u26A0"),
            h5(
              "span",
              { className: "cacao-error-boundary__title" },
              `Error in <${componentType || "Component"}>`
            )
          ),
          isDebug && h5(
            "div",
            { className: "cacao-error-boundary__details" },
            h5("code", null, errorMessage),
            this.state.errorInfo && h5(
              "pre",
              { className: "cacao-error-boundary__stack" },
              this.state.errorInfo.componentStack
            )
          ),
          h5("button", {
            className: "cacao-error-boundary__retry",
            onClick: () => this.setState({ error: null, errorInfo: null })
          }, "Retry")
        );
      }
      return this.props.children;
    }
  };

  // src/components/renderer.js
  var { createElement: h6 } = React;
  function didYouMean(name, candidates, maxResults = 3) {
    const lower = name.toLowerCase();
    const scored = candidates.map((c) => ({ name: c, dist: levenshtein(lower, c.toLowerCase()) })).filter((c) => c.dist <= Math.max(2, Math.floor(name.length * 0.4))).sort((a, b2) => a.dist - b2.dist);
    return scored.slice(0, maxResults).map((s) => s.name);
  }
  function levenshtein(a, b2) {
    const m2 = a.length, n = b2.length;
    const dp = Array.from({ length: m2 + 1 }, (_2, i) => {
      const row = new Array(n + 1);
      row[0] = i;
      return row;
    });
    for (let j2 = 1; j2 <= n; j2++)
      dp[0][j2] = j2;
    for (let i = 1; i <= m2; i++) {
      for (let j2 = 1; j2 <= n; j2++) {
        dp[i][j2] = a[i - 1] === b2[j2 - 1] ? dp[i - 1][j2 - 1] : 1 + Math.min(dp[i - 1][j2], dp[i][j2 - 1], dp[i - 1][j2 - 1]);
      }
    }
    return dp[m2][n];
  }
  function renderComponent(comp, key, setActiveTab, activeTab, renderers2) {
    if (!comp || !comp.type)
      return null;
    const Renderer = renderers2[comp.type];
    if (!Renderer) {
      const candidates = Object.keys(renderers2);
      const suggestions = didYouMean(comp.type, candidates);
      const hint = suggestions.length ? ` Did you mean: ${suggestions.join(", ")}?` : "";
      console.warn(`Unknown component type: "${comp.type}".${hint}`);
      return h6(
        "div",
        {
          key,
          className: "cacao-unknown-component"
        },
        h6("span", { className: "cacao-unknown-component__icon" }, "\u26A0"),
        h6("span", null, `Unknown: "${comp.type}"`),
        hint && h6("span", { className: "cacao-unknown-component__hint" }, hint)
      );
    }
    if (window.__CACAO_DEVTOOLS__?.onRender) {
      window.__CACAO_DEVTOOLS__.onRender(comp.type);
    }
    const children = (comp.children || []).map((c, i) => renderComponent(c, i, setActiveTab, activeTab, renderers2));
    const element = h6(
      ErrorBoundary,
      { key, componentType: comp.type, type: comp.type, props: comp.props || {} },
      h6(Renderer, { props: comp.props || {}, children, setActiveTab, activeTab, type: comp.type })
    );
    const id = comp.props?.id;
    if (id) {
      return React.cloneElement(element, { id });
    }
    return element;
  }

  // src/components/layout/AppShell.js
  var { createElement: h7, useEffect: useEffect4, useState: useState3, useCallback: useCallback3 } = React;
  function AppShell({ props, children, setActiveTab, activeTab }) {
    const { brand, logo, themeDark, themeLight } = props;
    const [sidebarOpen, setSidebarOpen] = useState3(false);
    const [isDark, setIsDark] = useState3(() => {
      const current = document.documentElement.getAttribute("data-theme") || "";
      if (themeLight)
        return current !== themeLight;
      return current === "dark" || current.indexOf("light") === -1;
    });
    useEffect4(() => {
      if (activeTab === null && props.default) {
        setActiveTab(props.default);
      }
    }, []);
    useEffect4(() => {
      setSidebarOpen(false);
    }, [activeTab]);
    const toggleTheme2 = useCallback3(() => {
      if (!themeDark || !themeLight)
        return;
      const next = isDark ? themeLight : themeDark;
      if (window.Cacao?.setTheme) {
        window.Cacao.setTheme(next);
      }
      setIsDark(!isDark);
    }, [isDark, themeDark, themeLight]);
    const slots = window.__CACAO_SLOTS__ || {};
    const slotRenderers = window.Cacao?.renderers || {};
    const renderSlot = (slotComps) => slotComps.map((c, i) => renderComponent(c, "slot-" + i, setActiveTab, activeTab, slotRenderers));
    const navSidebar = children.find((c) => c?.props?.type === "NavSidebar");
    const shellContent = children.find((c) => c?.props?.type === "ShellContent");
    const otherChildren = children.filter(
      (c) => c?.props?.type !== "NavSidebar" && c?.props?.type !== "ShellContent"
    );
    const hasThemeToggle = themeDark && themeLight;
    return h7("div", { className: "app-shell" }, [
      // Hamburger button (visible on mobile only via CSS)
      h7("button", {
        key: "hamburger",
        className: "app-shell-hamburger",
        onClick: () => setSidebarOpen(!sidebarOpen),
        "aria-label": sidebarOpen ? "Close menu" : "Open menu"
      }, sidebarOpen ? "\u2715" : "\u2630"),
      // Backdrop overlay (mobile only)
      h7("div", {
        key: "backdrop",
        className: "app-shell-backdrop" + (sidebarOpen ? " open" : ""),
        onClick: () => setSidebarOpen(false)
      }),
      // Left sidebar navigation
      h7("aside", { className: "app-shell-nav" + (sidebarOpen ? " open" : ""), key: "nav" }, [
        // Brand header
        (brand || logo || hasThemeToggle) && h7("div", { className: "app-shell-brand", key: "brand" }, [
          logo && h7("img", { src: logo, alt: brand || "Logo", className: "app-shell-logo", key: "logo" }),
          brand && h7("span", { className: "app-shell-brand-text", key: "brand-text" }, brand),
          // Theme toggle button in the brand bar
          hasThemeToggle && h7("button", {
            key: "theme-toggle",
            className: "app-shell-theme-toggle",
            onClick: toggleTheme2,
            "aria-label": isDark ? "Switch to light mode" : "Switch to dark mode",
            title: isDark ? "Light mode" : "Dark mode"
          }, getIcon(isDark ? "sun" : "moon"))
        ]),
        // Navigation content
        navSidebar,
        // Plugin sidebar slot
        slots.sidebar && h7("div", { className: "app-shell-slot-sidebar", key: "slot-sidebar" }, renderSlot(slots.sidebar))
      ]),
      // Main content area
      h7("main", { className: "app-shell-content", key: "content" }, [
        // Plugin header slot
        slots.header && h7("div", { className: "app-shell-slot-header", key: "slot-header" }, renderSlot(slots.header)),
        shellContent,
        ...otherChildren,
        // Plugin footer slot
        slots.footer && h7("div", { className: "app-shell-slot-footer", key: "slot-footer" }, renderSlot(slots.footer))
      ])
    ]);
  }

  // src/components/layout/Col.js
  var { createElement: h8 } = React;
  function Col({ props, children }) {
    const style = { gap: (props.gap || 4) * 4 + "px" };
    if (props.width) {
      style.flex = "0 0 " + props.width;
      style.width = props.width;
      style.minWidth = 0;
    }
    if (props.flex) {
      style.flex = props.flex;
    }
    if (props.max_width) {
      style.maxWidth = props.max_width;
    }
    if (props.height) {
      style.height = props.height;
    }
    if (props.align && props.align !== "stretch") {
      style.alignItems = props.align === "start" ? "flex-start" : props.align === "end" ? "flex-end" : props.align;
    }
    return h8("div", {
      className: "c-col" + (props.span ? " col-span-" + props.span : ""),
      style
    }, children);
  }

  // src/components/layout/Container.js
  var { createElement: h9 } = React;
  function Container({ props, children }) {
    const { size = "lg", padding = true, center = true } = props;
    const sizes = {
      sm: "640px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
      full: "100%"
    };
    const style = {
      maxWidth: sizes[size] || sizes.lg,
      width: "100%"
    };
    if (center) {
      style.marginLeft = "auto";
      style.marginRight = "auto";
    }
    return h9("div", {
      className: "c-container" + (padding ? " c-container--padded" : ""),
      style
    }, children);
  }

  // src/components/layout/Grid.js
  var { createElement: h10 } = React;
  function Grid({ props, children }) {
    return h10("div", {
      className: "c-grid",
      style: {
        gap: (props.gap || 4) * 4 + "px",
        gridTemplateColumns: "repeat(" + (props.cols || 12) + ", 1fr)"
      }
    }, children);
  }

  // src/components/layout/Hero.js
  var { createElement: h11 } = React;
  function Hero({ props, children }) {
    const { title, subtitle, background, image, height = "400px", align = "center", gradient } = props;
    const style = { minHeight: height };
    if (image) {
      style.backgroundImage = "url(" + image + ")";
      style.backgroundSize = "cover";
      style.backgroundPosition = "center";
    }
    if (gradient) {
      const existing = style.backgroundImage || "";
      const grad = "linear-gradient(" + gradient + ")";
      style.backgroundImage = existing ? grad + ", " + existing : grad;
    } else if (image) {
      style.backgroundImage = "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.6)), " + style.backgroundImage;
    }
    if (background && !image && !gradient) {
      style.background = background;
    }
    return h11("div", {
      className: "c-hero c-hero--" + align,
      style
    }, [
      h11("div", { key: "content", className: "c-hero-content" }, [
        title && h11("h1", { key: "title", className: "c-hero-title" }, title),
        subtitle && h11("p", { key: "subtitle", className: "c-hero-subtitle" }, subtitle),
        children && children.length > 0 && h11("div", { key: "actions", className: "c-hero-actions" }, children)
      ])
    ]);
  }

  // src/components/layout/NavGroup.js
  var { createElement: h12, useState: useState4 } = React;
  function NavGroup({ props, children }) {
    const { label, icon, defaultOpen = true } = props;
    const [isOpen, setIsOpen] = useState4(defaultOpen);
    const groupId = "nav-group-" + label.toLowerCase().replace(/\s+/g, "-");
    return h12("div", { className: "nav-group" + (isOpen ? " open" : ""), role: "group", "aria-label": label }, [
      h12("button", {
        className: "nav-group-header",
        key: "header",
        onClick: () => setIsOpen(!isOpen),
        type: "button",
        "aria-expanded": isOpen,
        "aria-controls": groupId
      }, [
        icon && h12("span", { className: "nav-icon", key: "icon", "aria-hidden": "true" }, getIcon(icon)),
        h12("span", { className: "nav-group-label", key: "label" }, label),
        h12(
          "span",
          { className: "nav-group-chevron", key: "chevron", "aria-hidden": "true" },
          getIcon(isOpen ? "chevron-down" : "chevron-right")
        )
      ]),
      h12("div", {
        className: "nav-group-items",
        key: "items",
        id: groupId,
        role: "menu"
      }, children)
    ]);
  }

  // src/components/layout/NavItem.js
  var { createElement: h13 } = React;
  function NavItem({ props, setActiveTab, activeTab }) {
    const { label, itemKey, icon, badge } = props;
    const isActive = activeTab === itemKey;
    return h13("button", {
      className: "nav-item" + (isActive ? " active" : ""),
      onClick: () => setActiveTab(itemKey),
      type: "button",
      "aria-current": isActive ? "page" : void 0
    }, [
      icon && h13("span", { className: "nav-icon", key: "icon", "aria-hidden": "true" }, getIcon(icon)),
      h13("span", { className: "nav-item-label", key: "label" }, label),
      badge && h13("span", { className: "nav-item-badge", key: "badge" }, badge)
    ]);
  }

  // src/components/layout/NavPanel.js
  var { createElement: h14 } = React;
  function NavPanel({ props, children, activeTab }) {
    const { panelKey } = props;
    if (panelKey !== activeTab) {
      return null;
    }
    return h14("div", { className: "nav-panel" }, children);
  }

  // src/components/layout/NavSidebar.js
  var { createElement: h15 } = React;
  function NavSidebar({ props, children }) {
    return h15("nav", { className: "nav-sidebar", "aria-label": "Main navigation" }, children);
  }

  // src/components/layout/Panel.js
  var { createElement: h16, useState: useState5, useRef: useRef4, useCallback: useCallback4, useEffect: useEffect5 } = React;
  function Panel({ props, children, setActiveTab, activeTab }) {
    const {
      title = "Panel",
      width = "400px",
      height = "300px",
      draggable = true,
      resizable = true,
      closable = true,
      minimizable = true,
      maximizable = true,
      signal,
      x: x2,
      y: y2
    } = props;
    const panelRef = useRef4(null);
    const [pos, setPos] = useState5({ x: x2 ?? 100, y: y2 ?? 100 });
    const [size, setSize] = useState5({ w: parseInt(width), h: parseInt(height) });
    const [minimized, setMinimized] = useState5(false);
    const [maximized, setMaximized] = useState5(false);
    const [visible, setVisible] = useState5(true);
    const dragRef = useRef4(null);
    const resizeRef = useRef4(null);
    const bringToFront = useCallback4(() => {
      if (window.CacaoPanelManager) {
        window.CacaoPanelManager.bringToFront(panelRef.current);
      }
    }, []);
    const onDragStart = useCallback4((e) => {
      if (!draggable || maximized)
        return;
      e.preventDefault();
      bringToFront();
      const startX = e.clientX - pos.x;
      const startY = e.clientY - pos.y;
      const onMove = (e2) => {
        setPos({ x: e2.clientX - startX, y: Math.max(0, e2.clientY - startY) });
      };
      const onUp = () => {
        document.removeEventListener("pointermove", onMove);
        document.removeEventListener("pointerup", onUp);
      };
      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onUp);
    }, [draggable, maximized, pos, bringToFront]);
    const onResizeStart = useCallback4((e, direction) => {
      if (!resizable || maximized)
        return;
      e.preventDefault();
      e.stopPropagation();
      bringToFront();
      const startX = e.clientX;
      const startY = e.clientY;
      const startW = size.w;
      const startH = size.h;
      const startPosX = pos.x;
      const startPosY = pos.y;
      const onMove = (e2) => {
        const dx = e2.clientX - startX;
        const dy = e2.clientY - startY;
        const newSize = { ...size };
        const newPos = { ...pos };
        if (direction.includes("e"))
          newSize.w = Math.max(200, startW + dx);
        if (direction.includes("s"))
          newSize.h = Math.max(150, startH + dy);
        if (direction.includes("w")) {
          newSize.w = Math.max(200, startW - dx);
          newPos.x = startPosX + dx;
        }
        if (direction.includes("n")) {
          newSize.h = Math.max(150, startH - dy);
          newPos.y = startPosY + dy;
        }
        setSize(newSize);
        setPos(newPos);
      };
      const onUp = () => {
        document.removeEventListener("pointermove", onMove);
        document.removeEventListener("pointerup", onUp);
      };
      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onUp);
    }, [resizable, maximized, size, pos, bringToFront]);
    const toggleMaximize = useCallback4(() => {
      setMaximized((prev) => !prev);
    }, []);
    if (!visible)
      return null;
    const style = maximized ? { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, width: "100vw", height: "100vh", zIndex: "var(--panel-z, 900)" } : { position: "absolute", left: pos.x, top: pos.y, width: size.w, height: minimized ? "auto" : size.h, zIndex: "var(--panel-z, 900)" };
    const resizeHandles = resizable && !maximized && !minimized ? [
      h16("div", { key: "r-e", className: "panel-resize panel-resize-e", onPointerDown: (e) => onResizeStart(e, "e") }),
      h16("div", { key: "r-s", className: "panel-resize panel-resize-s", onPointerDown: (e) => onResizeStart(e, "s") }),
      h16("div", { key: "r-se", className: "panel-resize panel-resize-se", onPointerDown: (e) => onResizeStart(e, "se") }),
      h16("div", { key: "r-w", className: "panel-resize panel-resize-w", onPointerDown: (e) => onResizeStart(e, "w") }),
      h16("div", { key: "r-n", className: "panel-resize panel-resize-n", onPointerDown: (e) => onResizeStart(e, "n") })
    ] : [];
    return h16("div", {
      ref: panelRef,
      className: "panel" + (minimized ? " minimized" : "") + (maximized ? " maximized" : ""),
      style,
      onPointerDown: bringToFront
    }, [
      // Title bar
      h16("div", {
        key: "titlebar",
        className: "panel-titlebar",
        onPointerDown: onDragStart
      }, [
        h16("span", { key: "title", className: "panel-title" }, title),
        h16("div", { key: "controls", className: "panel-controls" }, [
          minimizable && h16("button", {
            key: "min",
            className: "panel-btn",
            onClick: (e) => {
              e.stopPropagation();
              setMinimized(!minimized);
            },
            "aria-label": "Minimize"
          }, "\u2013"),
          maximizable && h16("button", {
            key: "max",
            className: "panel-btn",
            onClick: (e) => {
              e.stopPropagation();
              toggleMaximize();
            },
            "aria-label": maximized ? "Restore" : "Maximize"
          }, maximized ? "\u2752" : "\u25A1"),
          closable && h16("button", {
            key: "close",
            className: "panel-btn panel-btn-close",
            onClick: (e) => {
              e.stopPropagation();
              setVisible(false);
            },
            "aria-label": "Close"
          }, "\xD7")
        ])
      ]),
      // Content
      !minimized && h16("div", { key: "content", className: "panel-content" }, children),
      // Resize handles
      ...resizeHandles
    ]);
  }

  // src/components/layout/Row.js
  var { createElement: h17 } = React;
  function Row({ props, children }) {
    const style = { gap: (props.gap || 4) * 4 + "px" };
    if (props.wrap === false) {
      style.flexWrap = "nowrap";
    }
    if (props.height) {
      style.height = props.height;
    }
    if (props.justify && props.justify !== "start") {
      const justifyMap = {
        center: "center",
        end: "flex-end",
        between: "space-between",
        around: "space-around"
      };
      style.justifyContent = justifyMap[props.justify] || props.justify;
    }
    const classNames = ["c-row"];
    if (props.justify === "between")
      classNames.push("justify-between");
    return h17("div", {
      className: classNames.join(" "),
      style
    }, children);
  }

  // src/components/layout/ShellContent.js
  var { createElement: h18 } = React;
  function ShellContent({ props, children }) {
    return h18("div", { className: "shell-content" }, children);
  }

  // src/components/layout/Sidebar.js
  var { createElement: h19 } = React;
  function Sidebar({ props, children }) {
    return h19("div", { className: "sidebar" }, children);
  }

  // src/components/layout/Split.js
  var { createElement: h20, useState: useState6, useRef: useRef5, useCallback: useCallback5, useEffect: useEffect6 } = React;
  function Split({ props, children }) {
    const { direction = "horizontal", defaultSize = 50, minSize = 20, maxSize = 80 } = props;
    const isHorizontal = direction === "horizontal";
    const [size, setSize] = useState6(defaultSize);
    const dragging = useRef5(false);
    const containerRef = useRef5(null);
    const onMouseDown = useCallback5((e) => {
      e.preventDefault();
      dragging.current = true;
      document.body.style.cursor = isHorizontal ? "col-resize" : "row-resize";
      document.body.style.userSelect = "none";
    }, [isHorizontal]);
    useEffect6(() => {
      const onMouseMove = (e) => {
        if (!dragging.current || !containerRef.current)
          return;
        const rect = containerRef.current.getBoundingClientRect();
        let pct;
        if (isHorizontal) {
          pct = (e.clientX - rect.left) / rect.width * 100;
        } else {
          pct = (e.clientY - rect.top) / rect.height * 100;
        }
        setSize(Math.min(maxSize, Math.max(minSize, pct)));
      };
      const onMouseUp = () => {
        if (dragging.current) {
          dragging.current = false;
          document.body.style.cursor = "";
          document.body.style.userSelect = "";
        }
      };
      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
      return () => {
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
      };
    }, [isHorizontal, minSize, maxSize]);
    const firstChild = children[0] || null;
    const secondChild = children[1] || null;
    const firstStyle = isHorizontal ? { width: size + "%", height: "100%" } : { height: size + "%", width: "100%" };
    const secondStyle = isHorizontal ? { width: 100 - size + "%", height: "100%" } : { height: 100 - size + "%", width: "100%" };
    return h20("div", {
      ref: containerRef,
      className: "c-split c-split--" + direction
    }, [
      h20("div", { key: "first", className: "c-split-pane", style: firstStyle }, firstChild),
      h20(
        "div",
        {
          key: "handle",
          className: "c-split-handle c-split-handle--" + direction,
          onMouseDown
        },
        h20("div", { className: "c-split-handle-bar" })
      ),
      h20("div", { key: "second", className: "c-split-pane", style: secondStyle }, secondChild)
    ]);
  }

  // src/components/layout/Stack.js
  var { createElement: h21 } = React;
  function Stack({ props, children }) {
    const { direction = "vertical", gap = 4, divider = false, align, justify } = props;
    const isHorizontal = direction === "horizontal";
    const style = {
      gap: divider ? "0px" : gap * 4 + "px"
    };
    if (align) {
      const alignMap = { start: "flex-start", end: "flex-end", center: "center", stretch: "stretch" };
      style.alignItems = alignMap[align] || align;
    }
    if (justify) {
      const justifyMap = { start: "flex-start", end: "flex-end", center: "center", between: "space-between", around: "space-around" };
      style.justifyContent = justifyMap[justify] || justify;
    }
    const className = "c-stack c-stack--" + direction + (divider ? " c-stack--divider" : "");
    if (!divider) {
      return h21("div", { className, style }, children);
    }
    const items = [];
    children.forEach((child, i) => {
      if (i > 0) {
        items.push(h21("div", {
          key: "d" + i,
          className: "c-stack-divider",
          style: isHorizontal ? { margin: "0 " + gap * 4 + "px" } : { margin: gap * 4 + "px 0" }
        }));
      }
      items.push(child);
    });
    return h21("div", { className, style }, items);
  }

  // src/components/typography/index.js
  var typography_exports = {};
  __export(typography_exports, {
    Code: () => Code,
    Divider: () => Divider,
    Html: () => Html,
    Markdown: () => Markdown,
    RawHtml: () => RawHtml,
    Spacer: () => Spacer,
    Text: () => Text,
    Title: () => Title
  });

  // src/components/core/websocket.js
  init_static_runtime();
  var DEFAULT_RECONNECT = {
    maxAttempts: 10,
    // Max reconnection attempts (0 = infinite)
    baseDelay: 1e3,
    // Initial delay in ms
    maxDelay: 3e4,
    // Maximum delay in ms
    backoffMultiplier: 1.5,
    // Exponential backoff multiplier
    jitter: true
    // Add random jitter to prevent thundering herd
  };
  var CacaoWebSocket = class {
    constructor() {
      this.ws = null;
      this.connected = false;
      this.signals = {};
      this.listeners = /* @__PURE__ */ new Set();
      this.chatListeners = /* @__PURE__ */ new Set();
      this.reconnectAttempts = 0;
      this._reconnectTimer = null;
      const userConfig = window.__CACAO_RECONNECT__ || {};
      this.reconnectConfig = { ...DEFAULT_RECONNECT, ...userConfig };
    }
    connect() {
      if (isStaticMode()) {
        console.log("[Cacao] Running in static mode - no WebSocket");
        this.connected = true;
        return;
      }
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      let url = `${protocol}//${window.location.host}/ws`;
      if (this.sessionId) {
        url += `?session_id=${encodeURIComponent(this.sessionId)}`;
      }
      console.log("[Cacao] Connecting to WebSocket:", url);
      this.ws = new WebSocket(url);
      this.ws.onopen = () => {
        const wasReconnect = this.reconnectAttempts > 0;
        console.log("[Cacao] WebSocket connected");
        this.connected = true;
        this.reconnectAttempts = 0;
        if (this._reconnectTimer) {
          clearTimeout(this._reconnectTimer);
          this._reconnectTimer = null;
        }
        if (wasReconnect) {
          this.notifyMessageListeners({ type: "ws:reconnected" });
        }
      };
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (e) {
          console.error("[Cacao] Failed to parse message:", e);
        }
      };
      this.ws.onclose = (event) => {
        console.log("[Cacao] WebSocket disconnected (code:", event.code, ")");
        this.connected = false;
        this.notifyMessageListeners({ type: "ws:disconnected", code: event.code });
        this.attemptReconnect();
      };
      this.ws.onerror = (error) => {
        console.error("[Cacao] WebSocket error:", error);
      };
    }
    attemptReconnect() {
      const cfg = this.reconnectConfig;
      if (cfg.maxAttempts > 0 && this.reconnectAttempts >= cfg.maxAttempts) {
        console.warn(`[Cacao] Max reconnection attempts (${cfg.maxAttempts}) reached`);
        return;
      }
      this.reconnectAttempts++;
      let delay = cfg.baseDelay * Math.pow(cfg.backoffMultiplier, this.reconnectAttempts - 1);
      delay = Math.min(delay, cfg.maxDelay);
      if (cfg.jitter) {
        const jitterRange = delay * 0.25;
        delay += Math.random() * jitterRange * 2 - jitterRange;
      }
      delay = Math.round(delay);
      console.log(`[Cacao] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
      this._reconnectTimer = setTimeout(() => this.connect(), delay);
    }
    handleMessage(message) {
      const { type } = message;
      switch (type) {
        case "init":
          this.signals = message.state || {};
          this.sessionId = message.sessionId;
          window.__cacao_signals__ = this.signals;
          this.notifyListeners();
          console.log("[Cacao] Received initial state:", this.signals);
          break;
        case "update":
          if (message.changes) {
            Object.entries(message.changes).forEach(([name, value]) => {
              this.signals[name] = value;
            });
            window.__cacao_signals__ = this.signals;
            this.notifyListeners();
            console.log("[Cacao] State updated:", message.changes);
          }
          break;
        case "batch":
          if (message.changes) {
            message.changes.forEach(({ key, value }) => {
              this.signals[key] = value;
            });
            window.__cacao_signals__ = this.signals;
            this.notifyListeners();
            console.log("[Cacao] Batch updated:", message.changes.length, "signals");
          }
          break;
        case "toast":
          if (window.CacaoToast) {
            window.CacaoToast.show(message.message, {
              type: message.variant || "info",
              duration: message.duration || 4e3
            });
          }
          break;
        case "chat_delta":
        case "chat_done":
          this.chatListeners.forEach((listener) => listener(message));
          break;
        case "register_shortcuts":
          if (message.shortcuts && window.Cacao?.registerShortcut) {
            message.shortcuts.forEach((s) => {
              window.Cacao.registerShortcut(s.combo, () => {
                this.sendEvent(s.event_name, {});
              }, s.description || "");
            });
          }
          break;
        case "notification":
          if (window.CacaoNotifications) {
            window.CacaoNotifications.add({
              title: message.title || "",
              message: message.message || "",
              variant: message.variant || "info"
            });
          }
          break;
        case "auth_required":
          window.__CACAO_AUTH_REQUIRED__ = true;
          this.notifyListeners();
          break;
        case "chat:tool_call":
          this.chatListeners.forEach((listener) => listener(message));
          break;
        case "interface:result":
        case "interface:error":
        case "interface:progress":
        case "interface:stream":
        case "interface:stream_done":
        case "interface:flagged":
          break;
        case "agent:started":
        case "agent:step":
        case "agent:delta":
        case "agent:done":
        case "agent:error":
        case "agent:budget_update":
        case "multi_agent:started":
        case "multi_agent:turn":
        case "multi_agent:delta":
        case "multi_agent:routing":
        case "multi_agent:done":
        case "multi_agent:error":
        case "budget:summary":
          break;
        case "skill:result":
        case "skill:error":
        case "skill:browse_result":
        case "skill:browse_error":
        case "skill:search_result":
        case "skill:search_error":
        case "skill:details_result":
        case "skill:details_error":
        case "chain:started":
        case "chain:step_result":
        case "chain:result":
        case "chain:error":
        case "transform:result":
        case "transform:error":
        case "transform:list_result":
        case "transform:list_error":
        case "safety:set_result":
        case "safety:set_error":
        case "safety:get_result":
        case "safety:get_error":
          break;
        case "sql:result":
        case "sql:error":
          break;
        case "server:shutdown":
          console.log("[Cacao] Server shutting down, will reconnect...");
          this._serverShutdown = true;
          break;
        case "server:error":
          console.error("[Cacao] Server error:", message.title, message.message);
          if (window.__CACAO_DEBUG__ && window.__CACAO_ERROR_OVERLAY__) {
            window.__CACAO_ERROR_OVERLAY__.addError(message);
          }
          break;
        default:
          console.log("[Cacao] Unknown message type:", type, message);
      }
      this.notifyMessageListeners(message);
    }
    sendEvent(eventName, eventData = {}) {
      if (isStaticMode()) {
        staticDispatcher.dispatch(eventName, eventData);
        return;
      }
      if (!this.connected || !this.ws) {
        console.warn("[Cacao] Cannot send event - not connected");
        return;
      }
      const message = {
        type: "event",
        name: eventName,
        data: eventData
      };
      console.log("[Cacao] Sending event:", message);
      this.ws.send(JSON.stringify(message));
    }
    getSignal(name) {
      if (isStaticMode()) {
        return staticSignals.get(name);
      }
      return this.signals[name];
    }
    subscribe(listener) {
      if (isStaticMode()) {
        return staticSignals.subscribe(listener);
      }
      this.listeners.add(listener);
      return () => this.listeners.delete(listener);
    }
    subscribeChatStream(listener) {
      this.chatListeners.add(listener);
      return () => this.chatListeners.delete(listener);
    }
    sendChatMessage(signalName, text2) {
      if (isStaticMode())
        return;
      if (!this.connected || !this.ws) {
        console.warn("[Cacao] Cannot send chat message - not connected");
        return;
      }
      this.ws.send(JSON.stringify({
        type: "chat:send",
        signal: signalName,
        text: text2
      }));
    }
    dispatchChat(msg) {
      this.chatListeners.forEach((listener) => listener(msg));
    }
    addListener(handler) {
      if (!this._msgListeners)
        this._msgListeners = /* @__PURE__ */ new Set();
      this._msgListeners.add(handler);
    }
    removeListener(handler) {
      if (this._msgListeners)
        this._msgListeners.delete(handler);
    }
    send(message) {
      if (isStaticMode())
        return;
      if (!this.connected || !this.ws) {
        console.warn("[Cacao] Cannot send message - not connected");
        return;
      }
      this.ws.send(JSON.stringify(message));
    }
    notifyListeners() {
      this.listeners.forEach((listener) => listener(this.signals));
    }
    notifyMessageListeners(message) {
      if (this._msgListeners) {
        this._msgListeners.forEach((handler) => handler(message));
      }
    }
  };
  var cacaoWs = new CacaoWebSocket();
  if (typeof window !== "undefined" && !isStaticMode()) {
    cacaoWs.connect();
  }

  // src/components/typography/Code.js
  var { createElement: h22, useState: useState7, useEffect: useEffect7, useCallback: useCallback6, useMemo } = React;
  var TOKEN_PATTERNS = {
    comment: /(?:\/\/.*$|\/\*[\s\S]*?\*\/|#.*$)/gm,
    string: /(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)/g,
    keyword: /\b(?:def|class|import|from|return|if|else|elif|for|while|try|except|finally|with|as|yield|async|await|raise|pass|break|continue|and|or|not|in|is|lambda|None|True|False|function|const|let|var|export|default|switch|case|new|this|typeof|instanceof|void|delete|throw|catch|extends|implements|interface|type|enum|public|private|static|abstract|super)\b/g,
    number: /\b(?:0[xXbBoO][\da-fA-F_]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b/g,
    builtin: /\b(?:print|len|range|str|int|float|list|dict|set|tuple|bool|map|filter|type|isinstance|hasattr|getattr|setattr|open|self|cls|console|document|window|Math|JSON|Array|Object|String|Number|Promise|Error)\b/g,
    decorator: /(?:^|\s)@[\w.]+/gm,
    operator: /(?:=>|===|!==|==|!=|<=|>=|&&|\|\||[+\-*/%&|^~<>]=?)/g
  };
  function tokenize(code, language) {
    if (language === "text" || language === "plain")
      return [{ type: "plain", text: code }];
    const matches = [];
    for (const [type, pattern] of Object.entries(TOKEN_PATTERNS)) {
      const re3 = new RegExp(pattern.source, pattern.flags);
      let m2;
      while ((m2 = re3.exec(code)) !== null) {
        matches.push({ type, start: m2.index, end: m2.index + m2[0].length, text: m2[0] });
      }
    }
    matches.sort((a, b2) => a.start - b2.start || b2.end - a.end);
    const tokens = [];
    let pos = 0;
    for (const m2 of matches) {
      if (m2.start < pos)
        continue;
      if (m2.start > pos) {
        tokens.push({ type: "plain", text: code.slice(pos, m2.start) });
      }
      tokens.push(m2);
      pos = m2.end;
    }
    if (pos < code.length) {
      tokens.push({ type: "plain", text: code.slice(pos) });
    }
    return tokens;
  }
  function renderTokens(tokens) {
    return tokens.map((t, i) => {
      if (t.type === "plain")
        return t.text;
      return h22("span", { key: i, className: "c-code-token--" + t.type }, t.text);
    });
  }
  function Code({ props }) {
    const {
      content,
      language = "text",
      line_numbers = false,
      highlight_lines
    } = props;
    const [copyText, setCopyText] = useState7("Copy");
    const signalName = content?.__signal__;
    const [displayContent, setDisplayContent] = useState7(
      signalName ? "" : content || ""
    );
    useEffect7(() => {
      if (signalName) {
        const unsubscribe = cacaoWs.subscribe((signals) => {
          if (signals[signalName] !== void 0) {
            setDisplayContent(signals[signalName]);
          }
        });
        const initial = cacaoWs.getSignal(signalName);
        if (initial !== void 0) {
          setDisplayContent(initial);
        }
        return unsubscribe;
      }
    }, [signalName]);
    const handleCopy = useCallback6(() => {
      navigator.clipboard.writeText(displayContent).then(() => {
        setCopyText("Copied!");
        setTimeout(() => setCopyText("Copy"), 1500);
      }).catch(() => {
        setCopyText("Failed");
        setTimeout(() => setCopyText("Copy"), 1500);
      });
    }, [displayContent]);
    const highlightSet = useMemo(() => {
      if (!highlight_lines)
        return null;
      const set = /* @__PURE__ */ new Set();
      if (Array.isArray(highlight_lines)) {
        highlight_lines.forEach((n) => set.add(n));
      } else if (typeof highlight_lines === "string") {
        for (const part of highlight_lines.split(",")) {
          const range = part.trim().split("-");
          if (range.length === 2) {
            const start = parseInt(range[0]), end = parseInt(range[1]);
            for (let i = start; i <= end; i++)
              set.add(i);
          } else {
            set.add(parseInt(range[0]));
          }
        }
      }
      return set;
    }, [highlight_lines]);
    const lines = displayContent.split("\n");
    const showLineNumbers = line_numbers || lines.length > 10;
    const tokens = useMemo(() => tokenize(displayContent, language), [displayContent, language]);
    const langLabel = language && language !== "text" ? language : null;
    const codeContent = showLineNumbers ? h22(
      "table",
      { className: "c-code-table" },
      h22(
        "tbody",
        null,
        lines.map((line, i) => {
          const lineNum = i + 1;
          const isHighlighted = highlightSet && highlightSet.has(lineNum);
          return h22("tr", {
            key: i,
            className: isHighlighted ? "c-code-line c-code-line--highlight" : "c-code-line"
          }, [
            h22("td", { key: "num", className: "c-code-line-number" }, lineNum),
            h22(
              "td",
              { key: "code", className: "c-code-line-content" },
              renderTokens(tokenize(line, language))
            )
          ]);
        })
      )
    ) : h22("code", { key: "code" }, renderTokens(tokens));
    return h22("pre", { className: `c-code language-${language}` }, [
      langLabel && h22("span", { key: "lang", className: "c-code-lang" }, langLabel),
      h22("button", {
        key: "copy",
        className: "c-code-copy",
        onClick: handleCopy,
        "aria-label": "Copy code"
      }, copyText),
      codeContent
    ]);
  }

  // src/components/typography/Divider.js
  var { createElement: h23 } = React;
  function Divider() {
    return h23("hr", { className: "divider" });
  }

  // src/components/typography/Html.js
  var { createElement: h24, useRef: useRef6, useEffect: useEffect8 } = React;
  function attachCopyHandlers(container) {
    const buttons = container.querySelectorAll(".c-code-copy");
    for (const btn of buttons) {
      if (btn.dataset.bound)
        return;
      btn.dataset.bound = "true";
      btn.addEventListener("click", () => {
        const code = btn.closest("pre").querySelector("code");
        if (!code)
          return;
        navigator.clipboard.writeText(code.textContent).then(() => {
          btn.textContent = "Copied!";
          setTimeout(() => {
            btn.textContent = "Copy";
          }, 1500);
        }).catch(() => {
          btn.textContent = "Failed";
          setTimeout(() => {
            btn.textContent = "Copy";
          }, 1500);
        });
      });
    }
  }
  function Html({ props }) {
    const { content } = props;
    const containerRef = useRef6(null);
    useEffect8(() => {
      if (containerRef.current) {
        attachCopyHandlers(containerRef.current);
      }
    }, [content]);
    return h24("div", {
      ref: containerRef,
      className: "prose",
      dangerouslySetInnerHTML: { __html: content || "" }
    });
  }

  // node_modules/marked/lib/marked.esm.js
  function M() {
    return { async: false, breaks: false, extensions: null, gfm: true, hooks: null, pedantic: false, renderer: null, silent: false, tokenizer: null, walkTokens: null };
  }
  var T = M();
  function G(u3) {
    T = u3;
  }
  var _ = { exec: () => null };
  function k(u3, e = "") {
    let t = typeof u3 == "string" ? u3 : u3.source, n = { replace: (r, i) => {
      let s = typeof i == "string" ? i : i.source;
      return s = s.replace(m.caret, "$1"), t = t.replace(r, s), n;
    }, getRegex: () => new RegExp(t, e) };
    return n;
  }
  var Re = (() => {
    try {
      return !!new RegExp("(?<=1)(?<!1)");
    } catch {
      return false;
    }
  })();
  var m = { codeRemoveIndent: /^(?: {1,4}| {0,3}\t)/gm, outputLinkReplace: /\\([\[\]])/g, indentCodeCompensation: /^(\s+)(?:```)/, beginningSpace: /^\s+/, endingHash: /#$/, startingSpaceChar: /^ /, endingSpaceChar: / $/, nonSpaceChar: /[^ ]/, newLineCharGlobal: /\n/g, tabCharGlobal: /\t/g, multipleSpaceGlobal: /\s+/g, blankLine: /^[ \t]*$/, doubleBlankLine: /\n[ \t]*\n[ \t]*$/, blockquoteStart: /^ {0,3}>/, blockquoteSetextReplace: /\n {0,3}((?:=+|-+) *)(?=\n|$)/g, blockquoteSetextReplace2: /^ {0,3}>[ \t]?/gm, listReplaceNesting: /^ {1,4}(?=( {4})*[^ ])/g, listIsTask: /^\[[ xX]\] +\S/, listReplaceTask: /^\[[ xX]\] +/, listTaskCheckbox: /\[[ xX]\]/, anyLine: /\n.*\n/, hrefBrackets: /^<(.*)>$/, tableDelimiter: /[:|]/, tableAlignChars: /^\||\| *$/g, tableRowBlankLine: /\n[ \t]*$/, tableAlignRight: /^ *-+: *$/, tableAlignCenter: /^ *:-+: *$/, tableAlignLeft: /^ *:-+ *$/, startATag: /^<a /i, endATag: /^<\/a>/i, startPreScriptTag: /^<(pre|code|kbd|script)(\s|>)/i, endPreScriptTag: /^<\/(pre|code|kbd|script)(\s|>)/i, startAngleBracket: /^</, endAngleBracket: />$/, pedanticHrefTitle: /^([^'"]*[^\s])\s+(['"])(.*)\2/, unicodeAlphaNumeric: /[\p{L}\p{N}]/u, escapeTest: /[&<>"']/, escapeReplace: /[&<>"']/g, escapeTestNoEncode: /[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/, escapeReplaceNoEncode: /[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/g, caret: /(^|[^\[])\^/g, percentDecode: /%25/g, findPipe: /\|/g, splitPipe: / \|/, slashPipe: /\\\|/g, carriageReturn: /\r\n|\r/g, spaceLine: /^ +$/gm, notSpaceStart: /^\S*/, endingNewline: /\n$/, listItemRegex: (u3) => new RegExp(`^( {0,3}${u3})((?:[	 ][^\\n]*)?(?:\\n|$))`), nextBulletRegex: (u3) => new RegExp(`^ {0,${Math.min(3, u3 - 1)}}(?:[*+-]|\\d{1,9}[.)])((?:[ 	][^\\n]*)?(?:\\n|$))`), hrRegex: (u3) => new RegExp(`^ {0,${Math.min(3, u3 - 1)}}((?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$)`), fencesBeginRegex: (u3) => new RegExp(`^ {0,${Math.min(3, u3 - 1)}}(?:\`\`\`|~~~)`), headingBeginRegex: (u3) => new RegExp(`^ {0,${Math.min(3, u3 - 1)}}#`), htmlBeginRegex: (u3) => new RegExp(`^ {0,${Math.min(3, u3 - 1)}}<(?:[a-z].*>|!--)`, "i"), blockquoteBeginRegex: (u3) => new RegExp(`^ {0,${Math.min(3, u3 - 1)}}>`) };
  var Te = /^(?:[ \t]*(?:\n|$))+/;
  var Oe = /^((?: {4}| {0,3}\t)[^\n]+(?:\n(?:[ \t]*(?:\n|$))*)?)+/;
  var we = /^ {0,3}(`{3,}(?=[^`\n]*(?:\n|$))|~{3,})([^\n]*)(?:\n|$)(?:|([\s\S]*?)(?:\n|$))(?: {0,3}\1[~`]* *(?=\n|$)|$)/;
  var A = /^ {0,3}((?:-[\t ]*){3,}|(?:_[ \t]*){3,}|(?:\*[ \t]*){3,})(?:\n+|$)/;
  var ye = /^ {0,3}(#{1,6})(?=\s|$)(.*)(?:\n+|$)/;
  var N = / {0,3}(?:[*+-]|\d{1,9}[.)])/;
  var re2 = /^(?!bull |blockCode|fences|blockquote|heading|html|table)((?:.|\n(?!\s*?\n|bull |blockCode|fences|blockquote|heading|html|table))+?)\n {0,3}(=+|-+) *(?:\n+|$)/;
  var se = k(re2).replace(/bull/g, N).replace(/blockCode/g, /(?: {4}| {0,3}\t)/).replace(/fences/g, / {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g, / {0,3}>/).replace(/heading/g, / {0,3}#{1,6}/).replace(/html/g, / {0,3}<[^\n>]+>\n/).replace(/\|table/g, "").getRegex();
  var Pe = k(re2).replace(/bull/g, N).replace(/blockCode/g, /(?: {4}| {0,3}\t)/).replace(/fences/g, / {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g, / {0,3}>/).replace(/heading/g, / {0,3}#{1,6}/).replace(/html/g, / {0,3}<[^\n>]+>\n/).replace(/table/g, / {0,3}\|?(?:[:\- ]*\|)+[\:\- ]*\n/).getRegex();
  var Q = /^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table| +\n)[^\n]+)*)/;
  var Se = /^[^\n]+/;
  var j = /(?!\s*\])(?:\\[\s\S]|[^\[\]\\])+/;
  var $e = k(/^ {0,3}\[(label)\]: *(?:\n[ \t]*)?([^<\s][^\s]*|<.*?>)(?:(?: +(?:\n[ \t]*)?| *\n[ \t]*)(title))? *(?:\n+|$)/).replace("label", j).replace("title", /(?:"(?:\\"?|[^"\\])*"|'[^'\n]*(?:\n[^'\n]+)*\n?'|\([^()]*\))/).getRegex();
  var _e = k(/^(bull)([ \t][^\n]+?)?(?:\n|$)/).replace(/bull/g, N).getRegex();
  var q = "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|meta|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul";
  var F = /<!--(?:-?>|[\s\S]*?(?:-->|$))/;
  var Le = k("^ {0,3}(?:<(script|pre|style|textarea)[\\s>][\\s\\S]*?(?:</\\1>[^\\n]*\\n+|$)|comment[^\\n]*(\\n+|$)|<\\?[\\s\\S]*?(?:\\?>\\n*|$)|<![A-Z][\\s\\S]*?(?:>\\n*|$)|<!\\[CDATA\\[[\\s\\S]*?(?:\\]\\]>\\n*|$)|</?(tag)(?: +|\\n|/?>)[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|<(?!script|pre|style|textarea)([a-z][\\w-]*)(?:attribute)*? */?>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|</(?!script|pre|style|textarea)[a-z][\\w-]*\\s*>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$))", "i").replace("comment", F).replace("tag", q).replace("attribute", / +[a-zA-Z:_][\w.:-]*(?: *= *"[^"\n]*"| *= *'[^'\n]*'| *= *[^\s"'=<>`]+)?/).getRegex();
  var ie = k(Q).replace("hr", A).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("|lheading", "").replace("|table", "").replace("blockquote", " {0,3}>").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", q).getRegex();
  var Me = k(/^( {0,3}> ?(paragraph|[^\n]*)(?:\n|$))+/).replace("paragraph", ie).getRegex();
  var U = { blockquote: Me, code: Oe, def: $e, fences: we, heading: ye, hr: A, html: Le, lheading: se, list: _e, newline: Te, paragraph: ie, table: _, text: Se };
  var te = k("^ *([^\\n ].*)\\n {0,3}((?:\\| *)?:?-+:? *(?:\\| *:?-+:? *)*(?:\\| *)?)(?:\\n((?:(?! *\\n|hr|heading|blockquote|code|fences|list|html).*(?:\\n|$))*)\\n*|$)").replace("hr", A).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("blockquote", " {0,3}>").replace("code", "(?: {4}| {0,3}	)[^\\n]").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", q).getRegex();
  var ze = { ...U, lheading: Pe, table: te, paragraph: k(Q).replace("hr", A).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("|lheading", "").replace("table", te).replace("blockquote", " {0,3}>").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", q).getRegex() };
  var Ee = { ...U, html: k(`^ *(?:comment *(?:\\n|\\s*$)|<(tag)[\\s\\S]+?</\\1> *(?:\\n{2,}|\\s*$)|<tag(?:"[^"]*"|'[^']*'|\\s[^'"/>\\s]*)*?/?> *(?:\\n{2,}|\\s*$))`).replace("comment", F).replace(/tag/g, "(?!(?:a|em|strong|small|s|cite|q|dfn|abbr|data|time|code|var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo|span|br|wbr|ins|del|img)\\b)\\w+(?!:|[^\\w\\s@]*@)\\b").getRegex(), def: /^ *\[([^\]]+)\]: *<?([^\s>]+)>?(?: +(["(][^\n]+[")]))? *(?:\n+|$)/, heading: /^(#{1,6})(.*)(?:\n+|$)/, fences: _, lheading: /^(.+?)\n {0,3}(=+|-+) *(?:\n+|$)/, paragraph: k(Q).replace("hr", A).replace("heading", ` *#{1,6} *[^
]`).replace("lheading", se).replace("|table", "").replace("blockquote", " {0,3}>").replace("|fences", "").replace("|list", "").replace("|html", "").replace("|tag", "").getRegex() };
  var Ie = /^\\([!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])/;
  var Ae = /^(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)/;
  var oe = /^( {2,}|\\)\n(?!\s*$)/;
  var Ce = /^(`+|[^`])(?:(?= {2,}\n)|[\s\S]*?(?:(?=[\\<!\[`*_]|\b_|$)|[^ ](?= {2,}\n)))/;
  var v = /[\p{P}\p{S}]/u;
  var K = /[\s\p{P}\p{S}]/u;
  var ae = /[^\s\p{P}\p{S}]/u;
  var Be = k(/^((?![*_])punctSpace)/, "u").replace(/punctSpace/g, K).getRegex();
  var le = /(?!~)[\p{P}\p{S}]/u;
  var De = /(?!~)[\s\p{P}\p{S}]/u;
  var qe = /(?:[^\s\p{P}\p{S}]|~)/u;
  var ue = /(?![*_])[\p{P}\p{S}]/u;
  var ve = /(?![*_])[\s\p{P}\p{S}]/u;
  var He = /(?:[^\s\p{P}\p{S}]|[*_])/u;
  var Ge = k(/link|precode-code|html/, "g").replace("link", /\[(?:[^\[\]`]|(?<a>`+)[^`]+\k<a>(?!`))*?\]\((?:\\[\s\S]|[^\\\(\)]|\((?:\\[\s\S]|[^\\\(\)])*\))*\)/).replace("precode-", Re ? "(?<!`)()" : "(^^|[^`])").replace("code", /(?<b>`+)[^`]+\k<b>(?!`)/).replace("html", /<(?! )[^<>]*?>/).getRegex();
  var pe = /^(?:\*+(?:((?!\*)punct)|[^\s*]))|^_+(?:((?!_)punct)|([^\s_]))/;
  var Ze = k(pe, "u").replace(/punct/g, v).getRegex();
  var Ne = k(pe, "u").replace(/punct/g, le).getRegex();
  var ce = "^[^_*]*?__[^_*]*?\\*[^_*]*?(?=__)|[^*]+(?=[^*])|(?!\\*)punct(\\*+)(?=[\\s]|$)|notPunctSpace(\\*+)(?!\\*)(?=punctSpace|$)|(?!\\*)punctSpace(\\*+)(?=notPunctSpace)|[\\s](\\*+)(?!\\*)(?=punct)|(?!\\*)punct(\\*+)(?!\\*)(?=punct)|notPunctSpace(\\*+)(?=notPunctSpace)";
  var Qe = k(ce, "gu").replace(/notPunctSpace/g, ae).replace(/punctSpace/g, K).replace(/punct/g, v).getRegex();
  var je = k(ce, "gu").replace(/notPunctSpace/g, qe).replace(/punctSpace/g, De).replace(/punct/g, le).getRegex();
  var Fe = k("^[^_*]*?\\*\\*[^_*]*?_[^_*]*?(?=\\*\\*)|[^_]+(?=[^_])|(?!_)punct(_+)(?=[\\s]|$)|notPunctSpace(_+)(?!_)(?=punctSpace|$)|(?!_)punctSpace(_+)(?=notPunctSpace)|[\\s](_+)(?!_)(?=punct)|(?!_)punct(_+)(?!_)(?=punct)", "gu").replace(/notPunctSpace/g, ae).replace(/punctSpace/g, K).replace(/punct/g, v).getRegex();
  var Ue = k(/^~~?(?:((?!~)punct)|[^\s~])/, "u").replace(/punct/g, ue).getRegex();
  var Ke = "^[^~]+(?=[^~])|(?!~)punct(~~?)(?=[\\s]|$)|notPunctSpace(~~?)(?!~)(?=punctSpace|$)|(?!~)punctSpace(~~?)(?=notPunctSpace)|[\\s](~~?)(?!~)(?=punct)|(?!~)punct(~~?)(?!~)(?=punct)|notPunctSpace(~~?)(?=notPunctSpace)";
  var We = k(Ke, "gu").replace(/notPunctSpace/g, He).replace(/punctSpace/g, ve).replace(/punct/g, ue).getRegex();
  var Xe = k(/\\(punct)/, "gu").replace(/punct/g, v).getRegex();
  var Je = k(/^<(scheme:[^\s\x00-\x1f<>]*|email)>/).replace("scheme", /[a-zA-Z][a-zA-Z0-9+.-]{1,31}/).replace("email", /[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+(@)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+(?![-_])/).getRegex();
  var Ve = k(F).replace("(?:-->|$)", "-->").getRegex();
  var Ye = k("^comment|^</[a-zA-Z][\\w:-]*\\s*>|^<[a-zA-Z][\\w-]*(?:attribute)*?\\s*/?>|^<\\?[\\s\\S]*?\\?>|^<![a-zA-Z]+\\s[\\s\\S]*?>|^<!\\[CDATA\\[[\\s\\S]*?\\]\\]>").replace("comment", Ve).replace("attribute", /\s+[a-zA-Z:_][\w.:-]*(?:\s*=\s*"[^"]*"|\s*=\s*'[^']*'|\s*=\s*[^\s"'=<>`]+)?/).getRegex();
  var D = /(?:\[(?:\\[\s\S]|[^\[\]\\])*\]|\\[\s\S]|`+[^`]*?`+(?!`)|[^\[\]\\`])*?/;
  var et = k(/^!?\[(label)\]\(\s*(href)(?:(?:[ \t]+(?:\n[ \t]*)?|\n[ \t]*)(title))?\s*\)/).replace("label", D).replace("href", /<(?:\\.|[^\n<>\\])+>|[^ \t\n\x00-\x1f]*/).replace("title", /"(?:\\"?|[^"\\])*"|'(?:\\'?|[^'\\])*'|\((?:\\\)?|[^)\\])*\)/).getRegex();
  var he = k(/^!?\[(label)\]\[(ref)\]/).replace("label", D).replace("ref", j).getRegex();
  var ke = k(/^!?\[(ref)\](?:\[\])?/).replace("ref", j).getRegex();
  var tt = k("reflink|nolink(?!\\()", "g").replace("reflink", he).replace("nolink", ke).getRegex();
  var ne = /[hH][tT][tT][pP][sS]?|[fF][tT][pP]/;
  var W = { _backpedal: _, anyPunctuation: Xe, autolink: Je, blockSkip: Ge, br: oe, code: Ae, del: _, delLDelim: _, delRDelim: _, emStrongLDelim: Ze, emStrongRDelimAst: Qe, emStrongRDelimUnd: Fe, escape: Ie, link: et, nolink: ke, punctuation: Be, reflink: he, reflinkSearch: tt, tag: Ye, text: Ce, url: _ };
  var nt = { ...W, link: k(/^!?\[(label)\]\((.*?)\)/).replace("label", D).getRegex(), reflink: k(/^!?\[(label)\]\s*\[([^\]]*)\]/).replace("label", D).getRegex() };
  var Z = { ...W, emStrongRDelimAst: je, emStrongLDelim: Ne, delLDelim: Ue, delRDelim: We, url: k(/^((?:protocol):\/\/|www\.)(?:[a-zA-Z0-9\-]+\.?)+[^\s<]*|^email/).replace("protocol", ne).replace("email", /[A-Za-z0-9._+-]+(@)[a-zA-Z0-9-_]+(?:\.[a-zA-Z0-9-_]*[a-zA-Z0-9])+(?![-_])/).getRegex(), _backpedal: /(?:[^?!.,:;*_'"~()&]+|\([^)]*\)|&(?![a-zA-Z0-9]+;$)|[?!.,:;*_'"~)]+(?!$))+/, del: /^(~~?)(?=[^\s~])((?:\\[\s\S]|[^\\])*?(?:\\[\s\S]|[^\s~\\]))\1(?=[^~]|$)/, text: k(/^([`~]+|[^`~])(?:(?= {2,}\n)|(?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)|[\s\S]*?(?:(?=[\\<!\[`*~_]|\b_|protocol:\/\/|www\.|$)|[^ ](?= {2,}\n)|[^a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-](?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)))/).replace("protocol", ne).getRegex() };
  var rt = { ...Z, br: k(oe).replace("{2,}", "*").getRegex(), text: k(Z.text).replace("\\b_", "\\b_| {2,}\\n").replace(/\{2,\}/g, "*").getRegex() };
  var C = { normal: U, gfm: ze, pedantic: Ee };
  var z = { normal: W, gfm: Z, breaks: rt, pedantic: nt };
  var st = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  var de = (u3) => st[u3];
  function O(u3, e) {
    if (e) {
      if (m.escapeTest.test(u3))
        return u3.replace(m.escapeReplace, de);
    } else if (m.escapeTestNoEncode.test(u3))
      return u3.replace(m.escapeReplaceNoEncode, de);
    return u3;
  }
  function X(u3) {
    try {
      u3 = encodeURI(u3).replace(m.percentDecode, "%");
    } catch {
      return null;
    }
    return u3;
  }
  function J(u3, e) {
    let t = u3.replace(m.findPipe, (i, s, a) => {
      let o = false, l = s;
      for (; --l >= 0 && a[l] === "\\"; )
        o = !o;
      return o ? "|" : " |";
    }), n = t.split(m.splitPipe), r = 0;
    if (n[0].trim() || n.shift(), n.length > 0 && !n.at(-1)?.trim() && n.pop(), e)
      if (n.length > e)
        n.splice(e);
      else
        for (; n.length < e; )
          n.push("");
    for (; r < n.length; r++)
      n[r] = n[r].trim().replace(m.slashPipe, "|");
    return n;
  }
  function E(u3, e, t) {
    let n = u3.length;
    if (n === 0)
      return "";
    let r = 0;
    for (; r < n; ) {
      let i = u3.charAt(n - r - 1);
      if (i === e && !t)
        r++;
      else if (i !== e && t)
        r++;
      else
        break;
    }
    return u3.slice(0, n - r);
  }
  function ge(u3, e) {
    if (u3.indexOf(e[1]) === -1)
      return -1;
    let t = 0;
    for (let n = 0; n < u3.length; n++)
      if (u3[n] === "\\")
        n++;
      else if (u3[n] === e[0])
        t++;
      else if (u3[n] === e[1] && (t--, t < 0))
        return n;
    return t > 0 ? -2 : -1;
  }
  function fe(u3, e = 0) {
    let t = e, n = "";
    for (let r of u3)
      if (r === "	") {
        let i = 4 - t % 4;
        n += " ".repeat(i), t += i;
      } else
        n += r, t++;
    return n;
  }
  function me(u3, e, t, n, r) {
    let i = e.href, s = e.title || null, a = u3[1].replace(r.other.outputLinkReplace, "$1");
    n.state.inLink = true;
    let o = { type: u3[0].charAt(0) === "!" ? "image" : "link", raw: t, href: i, title: s, text: a, tokens: n.inlineTokens(a) };
    return n.state.inLink = false, o;
  }
  function it(u3, e, t) {
    let n = u3.match(t.other.indentCodeCompensation);
    if (n === null)
      return e;
    let r = n[1];
    return e.split(`
`).map((i) => {
      let s = i.match(t.other.beginningSpace);
      if (s === null)
        return i;
      let [a] = s;
      return a.length >= r.length ? i.slice(r.length) : i;
    }).join(`
`);
  }
  var w = class {
    options;
    rules;
    lexer;
    constructor(e) {
      this.options = e || T;
    }
    space(e) {
      let t = this.rules.block.newline.exec(e);
      if (t && t[0].length > 0)
        return { type: "space", raw: t[0] };
    }
    code(e) {
      let t = this.rules.block.code.exec(e);
      if (t) {
        let n = t[0].replace(this.rules.other.codeRemoveIndent, "");
        return { type: "code", raw: t[0], codeBlockStyle: "indented", text: this.options.pedantic ? n : E(n, `
`) };
      }
    }
    fences(e) {
      let t = this.rules.block.fences.exec(e);
      if (t) {
        let n = t[0], r = it(n, t[3] || "", this.rules);
        return { type: "code", raw: n, lang: t[2] ? t[2].trim().replace(this.rules.inline.anyPunctuation, "$1") : t[2], text: r };
      }
    }
    heading(e) {
      let t = this.rules.block.heading.exec(e);
      if (t) {
        let n = t[2].trim();
        if (this.rules.other.endingHash.test(n)) {
          let r = E(n, "#");
          (this.options.pedantic || !r || this.rules.other.endingSpaceChar.test(r)) && (n = r.trim());
        }
        return { type: "heading", raw: t[0], depth: t[1].length, text: n, tokens: this.lexer.inline(n) };
      }
    }
    hr(e) {
      let t = this.rules.block.hr.exec(e);
      if (t)
        return { type: "hr", raw: E(t[0], `
`) };
    }
    blockquote(e) {
      let t = this.rules.block.blockquote.exec(e);
      if (t) {
        let n = E(t[0], `
`).split(`
`), r = "", i = "", s = [];
        for (; n.length > 0; ) {
          let a = false, o = [], l;
          for (l = 0; l < n.length; l++)
            if (this.rules.other.blockquoteStart.test(n[l]))
              o.push(n[l]), a = true;
            else if (!a)
              o.push(n[l]);
            else
              break;
          n = n.slice(l);
          let p = o.join(`
`), c = p.replace(this.rules.other.blockquoteSetextReplace, `
    $1`).replace(this.rules.other.blockquoteSetextReplace2, "");
          r = r ? `${r}
${p}` : p, i = i ? `${i}
${c}` : c;
          let d = this.lexer.state.top;
          if (this.lexer.state.top = true, this.lexer.blockTokens(c, s, true), this.lexer.state.top = d, n.length === 0)
            break;
          let h98 = s.at(-1);
          if (h98?.type === "code")
            break;
          if (h98?.type === "blockquote") {
            let R = h98, f = R.raw + `
` + n.join(`
`), S2 = this.blockquote(f);
            s[s.length - 1] = S2, r = r.substring(0, r.length - R.raw.length) + S2.raw, i = i.substring(0, i.length - R.text.length) + S2.text;
            break;
          } else if (h98?.type === "list") {
            let R = h98, f = R.raw + `
` + n.join(`
`), S2 = this.list(f);
            s[s.length - 1] = S2, r = r.substring(0, r.length - h98.raw.length) + S2.raw, i = i.substring(0, i.length - R.raw.length) + S2.raw, n = f.substring(s.at(-1).raw.length).split(`
`);
            continue;
          }
        }
        return { type: "blockquote", raw: r, tokens: s, text: i };
      }
    }
    list(e) {
      let t = this.rules.block.list.exec(e);
      if (t) {
        let n = t[1].trim(), r = n.length > 1, i = { type: "list", raw: "", ordered: r, start: r ? +n.slice(0, -1) : "", loose: false, items: [] };
        n = r ? `\\d{1,9}\\${n.slice(-1)}` : `\\${n}`, this.options.pedantic && (n = r ? n : "[*+-]");
        let s = this.rules.other.listItemRegex(n), a = false;
        for (; e; ) {
          let l = false, p = "", c = "";
          if (!(t = s.exec(e)) || this.rules.block.hr.test(e))
            break;
          p = t[0], e = e.substring(p.length);
          let d = fe(t[2].split(`
`, 1)[0], t[1].length), h98 = e.split(`
`, 1)[0], R = !d.trim(), f = 0;
          if (this.options.pedantic ? (f = 2, c = d.trimStart()) : R ? f = t[1].length + 1 : (f = d.search(this.rules.other.nonSpaceChar), f = f > 4 ? 1 : f, c = d.slice(f), f += t[1].length), R && this.rules.other.blankLine.test(h98) && (p += h98 + `
`, e = e.substring(h98.length + 1), l = true), !l) {
            let S2 = this.rules.other.nextBulletRegex(f), V = this.rules.other.hrRegex(f), Y = this.rules.other.fencesBeginRegex(f), ee = this.rules.other.headingBeginRegex(f), xe = this.rules.other.htmlBeginRegex(f), be = this.rules.other.blockquoteBeginRegex(f);
            for (; e; ) {
              let H = e.split(`
`, 1)[0], I;
              if (h98 = H, this.options.pedantic ? (h98 = h98.replace(this.rules.other.listReplaceNesting, "  "), I = h98) : I = h98.replace(this.rules.other.tabCharGlobal, "    "), Y.test(h98) || ee.test(h98) || xe.test(h98) || be.test(h98) || S2.test(h98) || V.test(h98))
                break;
              if (I.search(this.rules.other.nonSpaceChar) >= f || !h98.trim())
                c += `
` + I.slice(f);
              else {
                if (R || d.replace(this.rules.other.tabCharGlobal, "    ").search(this.rules.other.nonSpaceChar) >= 4 || Y.test(d) || ee.test(d) || V.test(d))
                  break;
                c += `
` + h98;
              }
              R = !h98.trim(), p += H + `
`, e = e.substring(H.length + 1), d = I.slice(f);
            }
          }
          i.loose || (a ? i.loose = true : this.rules.other.doubleBlankLine.test(p) && (a = true)), i.items.push({ type: "list_item", raw: p, task: !!this.options.gfm && this.rules.other.listIsTask.test(c), loose: false, text: c, tokens: [] }), i.raw += p;
        }
        let o = i.items.at(-1);
        if (o)
          o.raw = o.raw.trimEnd(), o.text = o.text.trimEnd();
        else
          return;
        i.raw = i.raw.trimEnd();
        for (let l of i.items) {
          if (this.lexer.state.top = false, l.tokens = this.lexer.blockTokens(l.text, []), l.task) {
            if (l.text = l.text.replace(this.rules.other.listReplaceTask, ""), l.tokens[0]?.type === "text" || l.tokens[0]?.type === "paragraph") {
              l.tokens[0].raw = l.tokens[0].raw.replace(this.rules.other.listReplaceTask, ""), l.tokens[0].text = l.tokens[0].text.replace(this.rules.other.listReplaceTask, "");
              for (let c = this.lexer.inlineQueue.length - 1; c >= 0; c--)
                if (this.rules.other.listIsTask.test(this.lexer.inlineQueue[c].src)) {
                  this.lexer.inlineQueue[c].src = this.lexer.inlineQueue[c].src.replace(this.rules.other.listReplaceTask, "");
                  break;
                }
            }
            let p = this.rules.other.listTaskCheckbox.exec(l.raw);
            if (p) {
              let c = { type: "checkbox", raw: p[0] + " ", checked: p[0] !== "[ ]" };
              l.checked = c.checked, i.loose ? l.tokens[0] && ["paragraph", "text"].includes(l.tokens[0].type) && "tokens" in l.tokens[0] && l.tokens[0].tokens ? (l.tokens[0].raw = c.raw + l.tokens[0].raw, l.tokens[0].text = c.raw + l.tokens[0].text, l.tokens[0].tokens.unshift(c)) : l.tokens.unshift({ type: "paragraph", raw: c.raw, text: c.raw, tokens: [c] }) : l.tokens.unshift(c);
            }
          }
          if (!i.loose) {
            let p = l.tokens.filter((d) => d.type === "space"), c = p.length > 0 && p.some((d) => this.rules.other.anyLine.test(d.raw));
            i.loose = c;
          }
        }
        if (i.loose)
          for (let l of i.items) {
            l.loose = true;
            for (let p of l.tokens)
              p.type === "text" && (p.type = "paragraph");
          }
        return i;
      }
    }
    html(e) {
      let t = this.rules.block.html.exec(e);
      if (t)
        return { type: "html", block: true, raw: t[0], pre: t[1] === "pre" || t[1] === "script" || t[1] === "style", text: t[0] };
    }
    def(e) {
      let t = this.rules.block.def.exec(e);
      if (t) {
        let n = t[1].toLowerCase().replace(this.rules.other.multipleSpaceGlobal, " "), r = t[2] ? t[2].replace(this.rules.other.hrefBrackets, "$1").replace(this.rules.inline.anyPunctuation, "$1") : "", i = t[3] ? t[3].substring(1, t[3].length - 1).replace(this.rules.inline.anyPunctuation, "$1") : t[3];
        return { type: "def", tag: n, raw: t[0], href: r, title: i };
      }
    }
    table(e) {
      let t = this.rules.block.table.exec(e);
      if (!t || !this.rules.other.tableDelimiter.test(t[2]))
        return;
      let n = J(t[1]), r = t[2].replace(this.rules.other.tableAlignChars, "").split("|"), i = t[3]?.trim() ? t[3].replace(this.rules.other.tableRowBlankLine, "").split(`
`) : [], s = { type: "table", raw: t[0], header: [], align: [], rows: [] };
      if (n.length === r.length) {
        for (let a of r)
          this.rules.other.tableAlignRight.test(a) ? s.align.push("right") : this.rules.other.tableAlignCenter.test(a) ? s.align.push("center") : this.rules.other.tableAlignLeft.test(a) ? s.align.push("left") : s.align.push(null);
        for (let a = 0; a < n.length; a++)
          s.header.push({ text: n[a], tokens: this.lexer.inline(n[a]), header: true, align: s.align[a] });
        for (let a of i)
          s.rows.push(J(a, s.header.length).map((o, l) => ({ text: o, tokens: this.lexer.inline(o), header: false, align: s.align[l] })));
        return s;
      }
    }
    lheading(e) {
      let t = this.rules.block.lheading.exec(e);
      if (t)
        return { type: "heading", raw: t[0], depth: t[2].charAt(0) === "=" ? 1 : 2, text: t[1], tokens: this.lexer.inline(t[1]) };
    }
    paragraph(e) {
      let t = this.rules.block.paragraph.exec(e);
      if (t) {
        let n = t[1].charAt(t[1].length - 1) === `
` ? t[1].slice(0, -1) : t[1];
        return { type: "paragraph", raw: t[0], text: n, tokens: this.lexer.inline(n) };
      }
    }
    text(e) {
      let t = this.rules.block.text.exec(e);
      if (t)
        return { type: "text", raw: t[0], text: t[0], tokens: this.lexer.inline(t[0]) };
    }
    escape(e) {
      let t = this.rules.inline.escape.exec(e);
      if (t)
        return { type: "escape", raw: t[0], text: t[1] };
    }
    tag(e) {
      let t = this.rules.inline.tag.exec(e);
      if (t)
        return !this.lexer.state.inLink && this.rules.other.startATag.test(t[0]) ? this.lexer.state.inLink = true : this.lexer.state.inLink && this.rules.other.endATag.test(t[0]) && (this.lexer.state.inLink = false), !this.lexer.state.inRawBlock && this.rules.other.startPreScriptTag.test(t[0]) ? this.lexer.state.inRawBlock = true : this.lexer.state.inRawBlock && this.rules.other.endPreScriptTag.test(t[0]) && (this.lexer.state.inRawBlock = false), { type: "html", raw: t[0], inLink: this.lexer.state.inLink, inRawBlock: this.lexer.state.inRawBlock, block: false, text: t[0] };
    }
    link(e) {
      let t = this.rules.inline.link.exec(e);
      if (t) {
        let n = t[2].trim();
        if (!this.options.pedantic && this.rules.other.startAngleBracket.test(n)) {
          if (!this.rules.other.endAngleBracket.test(n))
            return;
          let s = E(n.slice(0, -1), "\\");
          if ((n.length - s.length) % 2 === 0)
            return;
        } else {
          let s = ge(t[2], "()");
          if (s === -2)
            return;
          if (s > -1) {
            let o = (t[0].indexOf("!") === 0 ? 5 : 4) + t[1].length + s;
            t[2] = t[2].substring(0, s), t[0] = t[0].substring(0, o).trim(), t[3] = "";
          }
        }
        let r = t[2], i = "";
        if (this.options.pedantic) {
          let s = this.rules.other.pedanticHrefTitle.exec(r);
          s && (r = s[1], i = s[3]);
        } else
          i = t[3] ? t[3].slice(1, -1) : "";
        return r = r.trim(), this.rules.other.startAngleBracket.test(r) && (this.options.pedantic && !this.rules.other.endAngleBracket.test(n) ? r = r.slice(1) : r = r.slice(1, -1)), me(t, { href: r && r.replace(this.rules.inline.anyPunctuation, "$1"), title: i && i.replace(this.rules.inline.anyPunctuation, "$1") }, t[0], this.lexer, this.rules);
      }
    }
    reflink(e, t) {
      let n;
      if ((n = this.rules.inline.reflink.exec(e)) || (n = this.rules.inline.nolink.exec(e))) {
        let r = (n[2] || n[1]).replace(this.rules.other.multipleSpaceGlobal, " "), i = t[r.toLowerCase()];
        if (!i) {
          let s = n[0].charAt(0);
          return { type: "text", raw: s, text: s };
        }
        return me(n, i, n[0], this.lexer, this.rules);
      }
    }
    emStrong(e, t, n = "") {
      let r = this.rules.inline.emStrongLDelim.exec(e);
      if (!r || r[3] && n.match(this.rules.other.unicodeAlphaNumeric))
        return;
      if (!(r[1] || r[2] || "") || !n || this.rules.inline.punctuation.exec(n)) {
        let s = [...r[0]].length - 1, a, o, l = s, p = 0, c = r[0][0] === "*" ? this.rules.inline.emStrongRDelimAst : this.rules.inline.emStrongRDelimUnd;
        for (c.lastIndex = 0, t = t.slice(-1 * e.length + s); (r = c.exec(t)) != null; ) {
          if (a = r[1] || r[2] || r[3] || r[4] || r[5] || r[6], !a)
            continue;
          if (o = [...a].length, r[3] || r[4]) {
            l += o;
            continue;
          } else if ((r[5] || r[6]) && s % 3 && !((s + o) % 3)) {
            p += o;
            continue;
          }
          if (l -= o, l > 0)
            continue;
          o = Math.min(o, o + l + p);
          let d = [...r[0]][0].length, h98 = e.slice(0, s + r.index + d + o);
          if (Math.min(s, o) % 2) {
            let f = h98.slice(1, -1);
            return { type: "em", raw: h98, text: f, tokens: this.lexer.inlineTokens(f) };
          }
          let R = h98.slice(2, -2);
          return { type: "strong", raw: h98, text: R, tokens: this.lexer.inlineTokens(R) };
        }
      }
    }
    codespan(e) {
      let t = this.rules.inline.code.exec(e);
      if (t) {
        let n = t[2].replace(this.rules.other.newLineCharGlobal, " "), r = this.rules.other.nonSpaceChar.test(n), i = this.rules.other.startingSpaceChar.test(n) && this.rules.other.endingSpaceChar.test(n);
        return r && i && (n = n.substring(1, n.length - 1)), { type: "codespan", raw: t[0], text: n };
      }
    }
    br(e) {
      let t = this.rules.inline.br.exec(e);
      if (t)
        return { type: "br", raw: t[0] };
    }
    del(e, t, n = "") {
      let r = this.rules.inline.delLDelim.exec(e);
      if (!r)
        return;
      if (!(r[1] || "") || !n || this.rules.inline.punctuation.exec(n)) {
        let s = [...r[0]].length - 1, a, o, l = s, p = this.rules.inline.delRDelim;
        for (p.lastIndex = 0, t = t.slice(-1 * e.length + s); (r = p.exec(t)) != null; ) {
          if (a = r[1] || r[2] || r[3] || r[4] || r[5] || r[6], !a || (o = [...a].length, o !== s))
            continue;
          if (r[3] || r[4]) {
            l += o;
            continue;
          }
          if (l -= o, l > 0)
            continue;
          o = Math.min(o, o + l);
          let c = [...r[0]][0].length, d = e.slice(0, s + r.index + c + o), h98 = d.slice(s, -s);
          return { type: "del", raw: d, text: h98, tokens: this.lexer.inlineTokens(h98) };
        }
      }
    }
    autolink(e) {
      let t = this.rules.inline.autolink.exec(e);
      if (t) {
        let n, r;
        return t[2] === "@" ? (n = t[1], r = "mailto:" + n) : (n = t[1], r = n), { type: "link", raw: t[0], text: n, href: r, tokens: [{ type: "text", raw: n, text: n }] };
      }
    }
    url(e) {
      let t;
      if (t = this.rules.inline.url.exec(e)) {
        let n, r;
        if (t[2] === "@")
          n = t[0], r = "mailto:" + n;
        else {
          let i;
          do
            i = t[0], t[0] = this.rules.inline._backpedal.exec(t[0])?.[0] ?? "";
          while (i !== t[0]);
          n = t[0], t[1] === "www." ? r = "http://" + t[0] : r = t[0];
        }
        return { type: "link", raw: t[0], text: n, href: r, tokens: [{ type: "text", raw: n, text: n }] };
      }
    }
    inlineText(e) {
      let t = this.rules.inline.text.exec(e);
      if (t) {
        let n = this.lexer.state.inRawBlock;
        return { type: "text", raw: t[0], text: t[0], escaped: n };
      }
    }
  };
  var x = class u {
    tokens;
    options;
    state;
    inlineQueue;
    tokenizer;
    constructor(e) {
      this.tokens = [], this.tokens.links = /* @__PURE__ */ Object.create(null), this.options = e || T, this.options.tokenizer = this.options.tokenizer || new w(), this.tokenizer = this.options.tokenizer, this.tokenizer.options = this.options, this.tokenizer.lexer = this, this.inlineQueue = [], this.state = { inLink: false, inRawBlock: false, top: true };
      let t = { other: m, block: C.normal, inline: z.normal };
      this.options.pedantic ? (t.block = C.pedantic, t.inline = z.pedantic) : this.options.gfm && (t.block = C.gfm, this.options.breaks ? t.inline = z.breaks : t.inline = z.gfm), this.tokenizer.rules = t;
    }
    static get rules() {
      return { block: C, inline: z };
    }
    static lex(e, t) {
      return new u(t).lex(e);
    }
    static lexInline(e, t) {
      return new u(t).inlineTokens(e);
    }
    lex(e) {
      e = e.replace(m.carriageReturn, `
`), this.blockTokens(e, this.tokens);
      for (let t = 0; t < this.inlineQueue.length; t++) {
        let n = this.inlineQueue[t];
        this.inlineTokens(n.src, n.tokens);
      }
      return this.inlineQueue = [], this.tokens;
    }
    blockTokens(e, t = [], n = false) {
      for (this.options.pedantic && (e = e.replace(m.tabCharGlobal, "    ").replace(m.spaceLine, "")); e; ) {
        let r;
        if (this.options.extensions?.block?.some((s) => (r = s.call({ lexer: this }, e, t)) ? (e = e.substring(r.raw.length), t.push(r), true) : false))
          continue;
        if (r = this.tokenizer.space(e)) {
          e = e.substring(r.raw.length);
          let s = t.at(-1);
          r.raw.length === 1 && s !== void 0 ? s.raw += `
` : t.push(r);
          continue;
        }
        if (r = this.tokenizer.code(e)) {
          e = e.substring(r.raw.length);
          let s = t.at(-1);
          s?.type === "paragraph" || s?.type === "text" ? (s.raw += (s.raw.endsWith(`
`) ? "" : `
`) + r.raw, s.text += `
` + r.text, this.inlineQueue.at(-1).src = s.text) : t.push(r);
          continue;
        }
        if (r = this.tokenizer.fences(e)) {
          e = e.substring(r.raw.length), t.push(r);
          continue;
        }
        if (r = this.tokenizer.heading(e)) {
          e = e.substring(r.raw.length), t.push(r);
          continue;
        }
        if (r = this.tokenizer.hr(e)) {
          e = e.substring(r.raw.length), t.push(r);
          continue;
        }
        if (r = this.tokenizer.blockquote(e)) {
          e = e.substring(r.raw.length), t.push(r);
          continue;
        }
        if (r = this.tokenizer.list(e)) {
          e = e.substring(r.raw.length), t.push(r);
          continue;
        }
        if (r = this.tokenizer.html(e)) {
          e = e.substring(r.raw.length), t.push(r);
          continue;
        }
        if (r = this.tokenizer.def(e)) {
          e = e.substring(r.raw.length);
          let s = t.at(-1);
          s?.type === "paragraph" || s?.type === "text" ? (s.raw += (s.raw.endsWith(`
`) ? "" : `
`) + r.raw, s.text += `
` + r.raw, this.inlineQueue.at(-1).src = s.text) : this.tokens.links[r.tag] || (this.tokens.links[r.tag] = { href: r.href, title: r.title }, t.push(r));
          continue;
        }
        if (r = this.tokenizer.table(e)) {
          e = e.substring(r.raw.length), t.push(r);
          continue;
        }
        if (r = this.tokenizer.lheading(e)) {
          e = e.substring(r.raw.length), t.push(r);
          continue;
        }
        let i = e;
        if (this.options.extensions?.startBlock) {
          let s = 1 / 0, a = e.slice(1), o;
          this.options.extensions.startBlock.forEach((l) => {
            o = l.call({ lexer: this }, a), typeof o == "number" && o >= 0 && (s = Math.min(s, o));
          }), s < 1 / 0 && s >= 0 && (i = e.substring(0, s + 1));
        }
        if (this.state.top && (r = this.tokenizer.paragraph(i))) {
          let s = t.at(-1);
          n && s?.type === "paragraph" ? (s.raw += (s.raw.endsWith(`
`) ? "" : `
`) + r.raw, s.text += `
` + r.text, this.inlineQueue.pop(), this.inlineQueue.at(-1).src = s.text) : t.push(r), n = i.length !== e.length, e = e.substring(r.raw.length);
          continue;
        }
        if (r = this.tokenizer.text(e)) {
          e = e.substring(r.raw.length);
          let s = t.at(-1);
          s?.type === "text" ? (s.raw += (s.raw.endsWith(`
`) ? "" : `
`) + r.raw, s.text += `
` + r.text, this.inlineQueue.pop(), this.inlineQueue.at(-1).src = s.text) : t.push(r);
          continue;
        }
        if (e) {
          let s = "Infinite loop on byte: " + e.charCodeAt(0);
          if (this.options.silent) {
            console.error(s);
            break;
          } else
            throw new Error(s);
        }
      }
      return this.state.top = true, t;
    }
    inline(e, t = []) {
      return this.inlineQueue.push({ src: e, tokens: t }), t;
    }
    inlineTokens(e, t = []) {
      let n = e, r = null;
      if (this.tokens.links) {
        let o = Object.keys(this.tokens.links);
        if (o.length > 0)
          for (; (r = this.tokenizer.rules.inline.reflinkSearch.exec(n)) != null; )
            o.includes(r[0].slice(r[0].lastIndexOf("[") + 1, -1)) && (n = n.slice(0, r.index) + "[" + "a".repeat(r[0].length - 2) + "]" + n.slice(this.tokenizer.rules.inline.reflinkSearch.lastIndex));
      }
      for (; (r = this.tokenizer.rules.inline.anyPunctuation.exec(n)) != null; )
        n = n.slice(0, r.index) + "++" + n.slice(this.tokenizer.rules.inline.anyPunctuation.lastIndex);
      let i;
      for (; (r = this.tokenizer.rules.inline.blockSkip.exec(n)) != null; )
        i = r[2] ? r[2].length : 0, n = n.slice(0, r.index + i) + "[" + "a".repeat(r[0].length - i - 2) + "]" + n.slice(this.tokenizer.rules.inline.blockSkip.lastIndex);
      n = this.options.hooks?.emStrongMask?.call({ lexer: this }, n) ?? n;
      let s = false, a = "";
      for (; e; ) {
        s || (a = ""), s = false;
        let o;
        if (this.options.extensions?.inline?.some((p) => (o = p.call({ lexer: this }, e, t)) ? (e = e.substring(o.raw.length), t.push(o), true) : false))
          continue;
        if (o = this.tokenizer.escape(e)) {
          e = e.substring(o.raw.length), t.push(o);
          continue;
        }
        if (o = this.tokenizer.tag(e)) {
          e = e.substring(o.raw.length), t.push(o);
          continue;
        }
        if (o = this.tokenizer.link(e)) {
          e = e.substring(o.raw.length), t.push(o);
          continue;
        }
        if (o = this.tokenizer.reflink(e, this.tokens.links)) {
          e = e.substring(o.raw.length);
          let p = t.at(-1);
          o.type === "text" && p?.type === "text" ? (p.raw += o.raw, p.text += o.text) : t.push(o);
          continue;
        }
        if (o = this.tokenizer.emStrong(e, n, a)) {
          e = e.substring(o.raw.length), t.push(o);
          continue;
        }
        if (o = this.tokenizer.codespan(e)) {
          e = e.substring(o.raw.length), t.push(o);
          continue;
        }
        if (o = this.tokenizer.br(e)) {
          e = e.substring(o.raw.length), t.push(o);
          continue;
        }
        if (o = this.tokenizer.del(e, n, a)) {
          e = e.substring(o.raw.length), t.push(o);
          continue;
        }
        if (o = this.tokenizer.autolink(e)) {
          e = e.substring(o.raw.length), t.push(o);
          continue;
        }
        if (!this.state.inLink && (o = this.tokenizer.url(e))) {
          e = e.substring(o.raw.length), t.push(o);
          continue;
        }
        let l = e;
        if (this.options.extensions?.startInline) {
          let p = 1 / 0, c = e.slice(1), d;
          this.options.extensions.startInline.forEach((h98) => {
            d = h98.call({ lexer: this }, c), typeof d == "number" && d >= 0 && (p = Math.min(p, d));
          }), p < 1 / 0 && p >= 0 && (l = e.substring(0, p + 1));
        }
        if (o = this.tokenizer.inlineText(l)) {
          e = e.substring(o.raw.length), o.raw.slice(-1) !== "_" && (a = o.raw.slice(-1)), s = true;
          let p = t.at(-1);
          p?.type === "text" ? (p.raw += o.raw, p.text += o.text) : t.push(o);
          continue;
        }
        if (e) {
          let p = "Infinite loop on byte: " + e.charCodeAt(0);
          if (this.options.silent) {
            console.error(p);
            break;
          } else
            throw new Error(p);
        }
      }
      return t;
    }
  };
  var y = class {
    options;
    parser;
    constructor(e) {
      this.options = e || T;
    }
    space(e) {
      return "";
    }
    code({ text: e, lang: t, escaped: n }) {
      let r = (t || "").match(m.notSpaceStart)?.[0], i = e.replace(m.endingNewline, "") + `
`;
      return r ? '<pre><code class="language-' + O(r) + '">' + (n ? i : O(i, true)) + `</code></pre>
` : "<pre><code>" + (n ? i : O(i, true)) + `</code></pre>
`;
    }
    blockquote({ tokens: e }) {
      return `<blockquote>
${this.parser.parse(e)}</blockquote>
`;
    }
    html({ text: e }) {
      return e;
    }
    def(e) {
      return "";
    }
    heading({ tokens: e, depth: t }) {
      return `<h${t}>${this.parser.parseInline(e)}</h${t}>
`;
    }
    hr(e) {
      return `<hr>
`;
    }
    list(e) {
      let t = e.ordered, n = e.start, r = "";
      for (let a = 0; a < e.items.length; a++) {
        let o = e.items[a];
        r += this.listitem(o);
      }
      let i = t ? "ol" : "ul", s = t && n !== 1 ? ' start="' + n + '"' : "";
      return "<" + i + s + `>
` + r + "</" + i + `>
`;
    }
    listitem(e) {
      return `<li>${this.parser.parse(e.tokens)}</li>
`;
    }
    checkbox({ checked: e }) {
      return "<input " + (e ? 'checked="" ' : "") + 'disabled="" type="checkbox"> ';
    }
    paragraph({ tokens: e }) {
      return `<p>${this.parser.parseInline(e)}</p>
`;
    }
    table(e) {
      let t = "", n = "";
      for (let i = 0; i < e.header.length; i++)
        n += this.tablecell(e.header[i]);
      t += this.tablerow({ text: n });
      let r = "";
      for (let i = 0; i < e.rows.length; i++) {
        let s = e.rows[i];
        n = "";
        for (let a = 0; a < s.length; a++)
          n += this.tablecell(s[a]);
        r += this.tablerow({ text: n });
      }
      return r && (r = `<tbody>${r}</tbody>`), `<table>
<thead>
` + t + `</thead>
` + r + `</table>
`;
    }
    tablerow({ text: e }) {
      return `<tr>
${e}</tr>
`;
    }
    tablecell(e) {
      let t = this.parser.parseInline(e.tokens), n = e.header ? "th" : "td";
      return (e.align ? `<${n} align="${e.align}">` : `<${n}>`) + t + `</${n}>
`;
    }
    strong({ tokens: e }) {
      return `<strong>${this.parser.parseInline(e)}</strong>`;
    }
    em({ tokens: e }) {
      return `<em>${this.parser.parseInline(e)}</em>`;
    }
    codespan({ text: e }) {
      return `<code>${O(e, true)}</code>`;
    }
    br(e) {
      return "<br>";
    }
    del({ tokens: e }) {
      return `<del>${this.parser.parseInline(e)}</del>`;
    }
    link({ href: e, title: t, tokens: n }) {
      let r = this.parser.parseInline(n), i = X(e);
      if (i === null)
        return r;
      e = i;
      let s = '<a href="' + e + '"';
      return t && (s += ' title="' + O(t) + '"'), s += ">" + r + "</a>", s;
    }
    image({ href: e, title: t, text: n, tokens: r }) {
      r && (n = this.parser.parseInline(r, this.parser.textRenderer));
      let i = X(e);
      if (i === null)
        return O(n);
      e = i;
      let s = `<img src="${e}" alt="${O(n)}"`;
      return t && (s += ` title="${O(t)}"`), s += ">", s;
    }
    text(e) {
      return "tokens" in e && e.tokens ? this.parser.parseInline(e.tokens) : "escaped" in e && e.escaped ? e.text : O(e.text);
    }
  };
  var $ = class {
    strong({ text: e }) {
      return e;
    }
    em({ text: e }) {
      return e;
    }
    codespan({ text: e }) {
      return e;
    }
    del({ text: e }) {
      return e;
    }
    html({ text: e }) {
      return e;
    }
    text({ text: e }) {
      return e;
    }
    link({ text: e }) {
      return "" + e;
    }
    image({ text: e }) {
      return "" + e;
    }
    br() {
      return "";
    }
    checkbox({ raw: e }) {
      return e;
    }
  };
  var b = class u2 {
    options;
    renderer;
    textRenderer;
    constructor(e) {
      this.options = e || T, this.options.renderer = this.options.renderer || new y(), this.renderer = this.options.renderer, this.renderer.options = this.options, this.renderer.parser = this, this.textRenderer = new $();
    }
    static parse(e, t) {
      return new u2(t).parse(e);
    }
    static parseInline(e, t) {
      return new u2(t).parseInline(e);
    }
    parse(e) {
      let t = "";
      for (let n = 0; n < e.length; n++) {
        let r = e[n];
        if (this.options.extensions?.renderers?.[r.type]) {
          let s = r, a = this.options.extensions.renderers[s.type].call({ parser: this }, s);
          if (a !== false || !["space", "hr", "heading", "code", "table", "blockquote", "list", "html", "def", "paragraph", "text"].includes(s.type)) {
            t += a || "";
            continue;
          }
        }
        let i = r;
        switch (i.type) {
          case "space": {
            t += this.renderer.space(i);
            break;
          }
          case "hr": {
            t += this.renderer.hr(i);
            break;
          }
          case "heading": {
            t += this.renderer.heading(i);
            break;
          }
          case "code": {
            t += this.renderer.code(i);
            break;
          }
          case "table": {
            t += this.renderer.table(i);
            break;
          }
          case "blockquote": {
            t += this.renderer.blockquote(i);
            break;
          }
          case "list": {
            t += this.renderer.list(i);
            break;
          }
          case "checkbox": {
            t += this.renderer.checkbox(i);
            break;
          }
          case "html": {
            t += this.renderer.html(i);
            break;
          }
          case "def": {
            t += this.renderer.def(i);
            break;
          }
          case "paragraph": {
            t += this.renderer.paragraph(i);
            break;
          }
          case "text": {
            t += this.renderer.text(i);
            break;
          }
          default: {
            let s = 'Token with "' + i.type + '" type was not found.';
            if (this.options.silent)
              return console.error(s), "";
            throw new Error(s);
          }
        }
      }
      return t;
    }
    parseInline(e, t = this.renderer) {
      let n = "";
      for (let r = 0; r < e.length; r++) {
        let i = e[r];
        if (this.options.extensions?.renderers?.[i.type]) {
          let a = this.options.extensions.renderers[i.type].call({ parser: this }, i);
          if (a !== false || !["escape", "html", "link", "image", "strong", "em", "codespan", "br", "del", "text"].includes(i.type)) {
            n += a || "";
            continue;
          }
        }
        let s = i;
        switch (s.type) {
          case "escape": {
            n += t.text(s);
            break;
          }
          case "html": {
            n += t.html(s);
            break;
          }
          case "link": {
            n += t.link(s);
            break;
          }
          case "image": {
            n += t.image(s);
            break;
          }
          case "checkbox": {
            n += t.checkbox(s);
            break;
          }
          case "strong": {
            n += t.strong(s);
            break;
          }
          case "em": {
            n += t.em(s);
            break;
          }
          case "codespan": {
            n += t.codespan(s);
            break;
          }
          case "br": {
            n += t.br(s);
            break;
          }
          case "del": {
            n += t.del(s);
            break;
          }
          case "text": {
            n += t.text(s);
            break;
          }
          default: {
            let a = 'Token with "' + s.type + '" type was not found.';
            if (this.options.silent)
              return console.error(a), "";
            throw new Error(a);
          }
        }
      }
      return n;
    }
  };
  var P = class {
    options;
    block;
    constructor(e) {
      this.options = e || T;
    }
    static passThroughHooks = /* @__PURE__ */ new Set(["preprocess", "postprocess", "processAllTokens", "emStrongMask"]);
    static passThroughHooksRespectAsync = /* @__PURE__ */ new Set(["preprocess", "postprocess", "processAllTokens"]);
    preprocess(e) {
      return e;
    }
    postprocess(e) {
      return e;
    }
    processAllTokens(e) {
      return e;
    }
    emStrongMask(e) {
      return e;
    }
    provideLexer() {
      return this.block ? x.lex : x.lexInline;
    }
    provideParser() {
      return this.block ? b.parse : b.parseInline;
    }
  };
  var B = class {
    defaults = M();
    options = this.setOptions;
    parse = this.parseMarkdown(true);
    parseInline = this.parseMarkdown(false);
    Parser = b;
    Renderer = y;
    TextRenderer = $;
    Lexer = x;
    Tokenizer = w;
    Hooks = P;
    constructor(...e) {
      this.use(...e);
    }
    walkTokens(e, t) {
      let n = [];
      for (let r of e)
        switch (n = n.concat(t.call(this, r)), r.type) {
          case "table": {
            let i = r;
            for (let s of i.header)
              n = n.concat(this.walkTokens(s.tokens, t));
            for (let s of i.rows)
              for (let a of s)
                n = n.concat(this.walkTokens(a.tokens, t));
            break;
          }
          case "list": {
            let i = r;
            n = n.concat(this.walkTokens(i.items, t));
            break;
          }
          default: {
            let i = r;
            this.defaults.extensions?.childTokens?.[i.type] ? this.defaults.extensions.childTokens[i.type].forEach((s) => {
              let a = i[s].flat(1 / 0);
              n = n.concat(this.walkTokens(a, t));
            }) : i.tokens && (n = n.concat(this.walkTokens(i.tokens, t)));
          }
        }
      return n;
    }
    use(...e) {
      let t = this.defaults.extensions || { renderers: {}, childTokens: {} };
      return e.forEach((n) => {
        let r = { ...n };
        if (r.async = this.defaults.async || r.async || false, n.extensions && (n.extensions.forEach((i) => {
          if (!i.name)
            throw new Error("extension name required");
          if ("renderer" in i) {
            let s = t.renderers[i.name];
            s ? t.renderers[i.name] = function(...a) {
              let o = i.renderer.apply(this, a);
              return o === false && (o = s.apply(this, a)), o;
            } : t.renderers[i.name] = i.renderer;
          }
          if ("tokenizer" in i) {
            if (!i.level || i.level !== "block" && i.level !== "inline")
              throw new Error("extension level must be 'block' or 'inline'");
            let s = t[i.level];
            s ? s.unshift(i.tokenizer) : t[i.level] = [i.tokenizer], i.start && (i.level === "block" ? t.startBlock ? t.startBlock.push(i.start) : t.startBlock = [i.start] : i.level === "inline" && (t.startInline ? t.startInline.push(i.start) : t.startInline = [i.start]));
          }
          "childTokens" in i && i.childTokens && (t.childTokens[i.name] = i.childTokens);
        }), r.extensions = t), n.renderer) {
          let i = this.defaults.renderer || new y(this.defaults);
          for (let s in n.renderer) {
            if (!(s in i))
              throw new Error(`renderer '${s}' does not exist`);
            if (["options", "parser"].includes(s))
              continue;
            let a = s, o = n.renderer[a], l = i[a];
            i[a] = (...p) => {
              let c = o.apply(i, p);
              return c === false && (c = l.apply(i, p)), c || "";
            };
          }
          r.renderer = i;
        }
        if (n.tokenizer) {
          let i = this.defaults.tokenizer || new w(this.defaults);
          for (let s in n.tokenizer) {
            if (!(s in i))
              throw new Error(`tokenizer '${s}' does not exist`);
            if (["options", "rules", "lexer"].includes(s))
              continue;
            let a = s, o = n.tokenizer[a], l = i[a];
            i[a] = (...p) => {
              let c = o.apply(i, p);
              return c === false && (c = l.apply(i, p)), c;
            };
          }
          r.tokenizer = i;
        }
        if (n.hooks) {
          let i = this.defaults.hooks || new P();
          for (let s in n.hooks) {
            if (!(s in i))
              throw new Error(`hook '${s}' does not exist`);
            if (["options", "block"].includes(s))
              continue;
            let a = s, o = n.hooks[a], l = i[a];
            P.passThroughHooks.has(s) ? i[a] = (p) => {
              if (this.defaults.async && P.passThroughHooksRespectAsync.has(s))
                return (async () => {
                  let d = await o.call(i, p);
                  return l.call(i, d);
                })();
              let c = o.call(i, p);
              return l.call(i, c);
            } : i[a] = (...p) => {
              if (this.defaults.async)
                return (async () => {
                  let d = await o.apply(i, p);
                  return d === false && (d = await l.apply(i, p)), d;
                })();
              let c = o.apply(i, p);
              return c === false && (c = l.apply(i, p)), c;
            };
          }
          r.hooks = i;
        }
        if (n.walkTokens) {
          let i = this.defaults.walkTokens, s = n.walkTokens;
          r.walkTokens = function(a) {
            let o = [];
            return o.push(s.call(this, a)), i && (o = o.concat(i.call(this, a))), o;
          };
        }
        this.defaults = { ...this.defaults, ...r };
      }), this;
    }
    setOptions(e) {
      return this.defaults = { ...this.defaults, ...e }, this;
    }
    lexer(e, t) {
      return x.lex(e, t ?? this.defaults);
    }
    parser(e, t) {
      return b.parse(e, t ?? this.defaults);
    }
    parseMarkdown(e) {
      return (n, r) => {
        let i = { ...r }, s = { ...this.defaults, ...i }, a = this.onError(!!s.silent, !!s.async);
        if (this.defaults.async === true && i.async === false)
          return a(new Error("marked(): The async option was set to true by an extension. Remove async: false from the parse options object to return a Promise."));
        if (typeof n > "u" || n === null)
          return a(new Error("marked(): input parameter is undefined or null"));
        if (typeof n != "string")
          return a(new Error("marked(): input parameter is of type " + Object.prototype.toString.call(n) + ", string expected"));
        if (s.hooks && (s.hooks.options = s, s.hooks.block = e), s.async)
          return (async () => {
            let o = s.hooks ? await s.hooks.preprocess(n) : n, p = await (s.hooks ? await s.hooks.provideLexer() : e ? x.lex : x.lexInline)(o, s), c = s.hooks ? await s.hooks.processAllTokens(p) : p;
            s.walkTokens && await Promise.all(this.walkTokens(c, s.walkTokens));
            let h98 = await (s.hooks ? await s.hooks.provideParser() : e ? b.parse : b.parseInline)(c, s);
            return s.hooks ? await s.hooks.postprocess(h98) : h98;
          })().catch(a);
        try {
          s.hooks && (n = s.hooks.preprocess(n));
          let l = (s.hooks ? s.hooks.provideLexer() : e ? x.lex : x.lexInline)(n, s);
          s.hooks && (l = s.hooks.processAllTokens(l)), s.walkTokens && this.walkTokens(l, s.walkTokens);
          let c = (s.hooks ? s.hooks.provideParser() : e ? b.parse : b.parseInline)(l, s);
          return s.hooks && (c = s.hooks.postprocess(c)), c;
        } catch (o) {
          return a(o);
        }
      };
    }
    onError(e, t) {
      return (n) => {
        if (n.message += `
Please report this to https://github.com/markedjs/marked.`, e) {
          let r = "<p>An error occurred:</p><pre>" + O(n.message + "", true) + "</pre>";
          return t ? Promise.resolve(r) : r;
        }
        if (t)
          return Promise.reject(n);
        throw n;
      };
    }
  };
  var L = new B();
  function g(u3, e) {
    return L.parse(u3, e);
  }
  g.options = g.setOptions = function(u3) {
    return L.setOptions(u3), g.defaults = L.defaults, G(g.defaults), g;
  };
  g.getDefaults = M;
  g.defaults = T;
  g.use = function(...u3) {
    return L.use(...u3), g.defaults = L.defaults, G(g.defaults), g;
  };
  g.walkTokens = function(u3, e) {
    return L.walkTokens(u3, e);
  };
  g.parseInline = L.parseInline;
  g.Parser = b;
  g.parser = b.parse;
  g.Renderer = y;
  g.TextRenderer = $;
  g.Lexer = x;
  g.lexer = x.lex;
  g.Tokenizer = w;
  g.Hooks = P;
  g.parse = g;
  var Ut = g.options;
  var Kt = g.setOptions;
  var Wt = g.use;
  var Xt = g.walkTokens;
  var Jt = g.parseInline;
  var Yt = b.parse;
  var en = x.lex;

  // src/components/typography/Markdown.js
  var { createElement: h25, useState: useState8, useEffect: useEffect9, useRef: useRef7, useCallback: useCallback7, useMemo: useMemo2 } = React;
  var CALLOUT_TYPES = {
    NOTE: { icon: "\u2139\uFE0F", className: "callout-note" },
    TIP: { icon: "\u{1F4A1}", className: "callout-tip" },
    IMPORTANT: { icon: "\u2757", className: "callout-important" },
    WARNING: { icon: "\u26A0\uFE0F", className: "callout-warning" },
    CAUTION: { icon: "\u{1F6D1}", className: "callout-caution" }
  };
  function calloutExtension() {
    return {
      renderer: {
        blockquote(token) {
          const body = this.parser.parse(token.tokens);
          const match = body.match(/^\s*<p>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*<br\s*\/?>\s*/i);
          if (!match) {
            const matchNewline = body.match(/^\s*<p>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n/i);
            if (!matchNewline)
              return `<blockquote>${body}</blockquote>
`;
            const type2 = matchNewline[1].toUpperCase();
            const callout2 = CALLOUT_TYPES[type2];
            const content2 = body.replace(matchNewline[0], "<p>");
            return `<div class="callout ${callout2.className}"><div class="callout-title">${callout2.icon} ${type2.charAt(0) + type2.slice(1).toLowerCase()}</div><div class="callout-body">${content2}</div></div>
`;
          }
          const type = match[1].toUpperCase();
          const callout = CALLOUT_TYPES[type];
          const content = body.replace(match[0], "<p>");
          return `<div class="callout ${callout.className}"><div class="callout-title">${callout.icon} ${type.charAt(0) + type.slice(1).toLowerCase()}</div><div class="callout-body">${content}</div></div>
`;
        }
      }
    };
  }
  function codeBlockExtension() {
    return {
      renderer: {
        code(token) {
          const text2 = token.text;
          const lang = (token.lang || "").trim();
          if (lang === "mermaid") {
            return `<div class="mermaid-block" data-mermaid="${encodeURIComponent(text2)}"><pre class="mermaid-loading"><code>${text2}</code></pre></div>`;
          }
          const escaped = text2.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
          return `<div class="prose-code-wrapper"><pre class="c-code language-${lang}"><button class="c-code-copy" aria-label="Copy code">Copy</button><code>${escaped}</code></pre></div>`;
        }
      }
    };
  }
  function imageSizeExtension() {
    return {
      renderer: {
        image(token) {
          let alt = token.text || "";
          const src = token.href || "";
          const title = token.title ? ` title="${token.title}"` : "";
          const sizeMatch = alt.match(/^(.*?)\|(\d+)(?:x(\d+))?$/);
          let style = "";
          if (sizeMatch) {
            alt = sizeMatch[1];
            const width = sizeMatch[2];
            const height = sizeMatch[3];
            style = ` style="width:${width}px${height ? `;height:${height}px` : ""}"`;
          }
          return `<img src="${src}" alt="${alt}"${title}${style} />`;
        }
      }
    };
  }
  function preprocessMath(text2) {
    text2 = text2.replace(/\$\$([\s\S]+?)\$\$/g, (_2, math) => {
      return `<div class="math-block" data-math="${encodeURIComponent(math.trim())}">$$${math}$$</div>`;
    });
    text2 = text2.replace(/(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)/g, (_2, math) => {
      return `<span class="math-inline" data-math="${encodeURIComponent(math.trim())}">$${math}$</span>`;
    });
    return text2;
  }
  function extractHeadings(markdown) {
    const headings = [];
    const lines = markdown.split("\n");
    let inCodeBlock = false;
    for (const line of lines) {
      if (line.trim().startsWith("```")) {
        inCodeBlock = !inCodeBlock;
        continue;
      }
      if (inCodeBlock)
        continue;
      const match = line.match(/^(#{1,6})\s+(.+)/);
      if (match) {
        const level = match[1].length;
        const text2 = match[2].replace(/[*_`~\[\]]/g, "");
        const id = text2.toLowerCase().replace(/[^\w\s-]/g, "").replace(/\s+/g, "-");
        headings.push({ level, text: text2, id });
      }
    }
    return headings;
  }
  function headingIdExtension() {
    return {
      renderer: {
        heading(token) {
          const text2 = token.text;
          const depth = token.depth;
          const raw = token.raw || text2;
          const id = raw.replace(/^#+\s*/, "").replace(/[*_`~\[\]]/g, "").toLowerCase().replace(/[^\w\s-]/g, "").replace(/\s+/g, "-");
          return `<h${depth} id="${id}">${this.parser.parseInline(token.tokens)}</h${depth}>
`;
        }
      }
    };
  }
  function createMarkedInstance() {
    const marked = new B();
    marked.use({ gfm: true, breaks: true });
    marked.use(headingIdExtension());
    marked.use(calloutExtension());
    marked.use(codeBlockExtension());
    marked.use(imageSizeExtension());
    return marked;
  }
  var markedInstance = null;
  function getMarked() {
    if (!markedInstance) {
      markedInstance = createMarkedInstance();
    }
    return markedInstance;
  }
  async function initMermaid(container) {
    const blocks = container.querySelectorAll(".mermaid-block");
    if (blocks.length === 0)
      return;
    if (!window.mermaid) {
      try {
        await new Promise((resolve, reject) => {
          if (document.querySelector("script[data-mermaid]")) {
            const check = setInterval(() => {
              if (window.mermaid) {
                clearInterval(check);
                resolve();
              }
            }, 100);
            setTimeout(() => {
              clearInterval(check);
              reject(new Error("Mermaid load timeout"));
            }, 1e4);
            return;
          }
          const script = document.createElement("script");
          script.src = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js";
          script.setAttribute("data-mermaid", "true");
          script.onload = () => {
            window.mermaid.initialize({
              startOnLoad: false,
              theme: document.documentElement.getAttribute("data-theme") === "light" ? "default" : "dark",
              securityLevel: "loose"
            });
            resolve();
          };
          script.onerror = reject;
          document.head.appendChild(script);
        });
      } catch (e) {
        console.warn("Failed to load mermaid:", e);
        return;
      }
    }
    for (const block of blocks) {
      const code = decodeURIComponent(block.dataset.mermaid);
      try {
        const id = "mermaid-" + Math.random().toString(36).slice(2, 9);
        const { svg: svg2 } = await window.mermaid.render(id, code);
        block.innerHTML = svg2;
        block.classList.add("mermaid-rendered");
      } catch (e) {
        console.warn("Mermaid render error:", e);
      }
    }
  }
  async function initKaTeX(container) {
    const mathBlocks = container.querySelectorAll(".math-block, .math-inline");
    if (mathBlocks.length === 0)
      return;
    if (!window.katex) {
      try {
        await new Promise((resolve, reject) => {
          if (document.querySelector("link[data-katex]")) {
            const check = setInterval(() => {
              if (window.katex) {
                clearInterval(check);
                resolve();
              }
            }, 100);
            setTimeout(() => {
              clearInterval(check);
              reject(new Error("KaTeX load timeout"));
            }, 1e4);
            return;
          }
          const link = document.createElement("link");
          link.rel = "stylesheet";
          link.href = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css";
          link.setAttribute("data-katex", "true");
          document.head.appendChild(link);
          const script = document.createElement("script");
          script.src = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js";
          script.onload = resolve;
          script.onerror = reject;
          document.head.appendChild(script);
        });
      } catch (e) {
        console.warn("Failed to load KaTeX:", e);
        return;
      }
    }
    for (const el2 of mathBlocks) {
      const math = decodeURIComponent(el2.dataset.math);
      const isBlock = el2.classList.contains("math-block");
      try {
        el2.innerHTML = window.katex.renderToString(math, {
          displayMode: isBlock,
          throwOnError: false
        });
        el2.classList.add("math-rendered");
      } catch (e) {
        console.warn("KaTeX render error:", e);
      }
    }
  }
  function attachCopyHandlers2(container) {
    const buttons = container.querySelectorAll(".c-code-copy");
    for (const btn of buttons) {
      btn.addEventListener("click", () => {
        const code = btn.closest("pre").querySelector("code");
        if (!code)
          return;
        navigator.clipboard.writeText(code.textContent).then(() => {
          btn.textContent = "Copied!";
          setTimeout(() => {
            btn.textContent = "Copy";
          }, 1500);
        }).catch(() => {
          btn.textContent = "Failed";
          setTimeout(() => {
            btn.textContent = "Copy";
          }, 1500);
        });
      });
    }
  }
  function Markdown({ props }) {
    const { content, toc = false } = props;
    const containerRef = useRef7(null);
    const { html, headings } = useMemo2(() => {
      if (!content)
        return { html: "", headings: [] };
      const md = getMarked();
      const processed = preprocessMath(content);
      const rendered = md.parse(processed);
      const heads = toc ? extractHeadings(content) : [];
      return { html: rendered, headings: heads };
    }, [content, toc]);
    useEffect9(() => {
      if (!containerRef.current)
        return;
      attachCopyHandlers2(containerRef.current);
      initMermaid(containerRef.current);
      initKaTeX(containerRef.current);
    }, [html]);
    const handleTocClick = useCallback7((e) => {
      const id = e.target.dataset.tocId;
      if (!id)
        return;
      e.preventDefault();
      const el2 = containerRef.current?.querySelector(`#${CSS.escape(id)}`);
      if (el2)
        el2.scrollIntoView({ behavior: "smooth" });
    }, []);
    if (toc && headings.length > 0) {
      return h25("div", { className: "prose-with-toc" }, [
        h25("nav", {
          key: "toc",
          className: "prose-toc",
          onClick: handleTocClick
        }, [
          h25("div", { key: "toc-title", className: "prose-toc-title" }, "Contents"),
          ...headings.map(
            (heading, i) => h25("a", {
              key: i,
              href: `#${heading.id}`,
              className: `prose-toc-item prose-toc-level-${heading.level}`,
              "data-toc-id": heading.id
            }, heading.text)
          )
        ]),
        h25("div", {
          key: "content",
          ref: containerRef,
          className: "prose",
          dangerouslySetInnerHTML: { __html: html }
        })
      ]);
    }
    return h25("div", {
      ref: containerRef,
      className: "prose",
      dangerouslySetInnerHTML: { __html: html }
    });
  }

  // src/components/typography/RawHtml.js
  var { createElement: h26 } = React;
  function RawHtml({ props }) {
    const { content } = props;
    return h26("div", {
      className: "raw-html",
      dangerouslySetInnerHTML: { __html: content || "" }
    });
  }

  // src/components/typography/Spacer.js
  var { createElement: h27 } = React;
  function Spacer({ props }) {
    return h27("div", { style: { height: (props.size || 4) * 4 } });
  }

  // src/components/typography/Text.js
  var { createElement: h28, useState: useState9, useEffect: useEffect10 } = React;
  function Text({ props }) {
    const { content, color, size, weight } = props;
    const signalName = content?.__signal__;
    const [displayContent, setDisplayContent] = useState9(
      signalName ? "" : content || ""
    );
    useEffect10(() => {
      if (signalName) {
        const unsubscribe = cacaoWs.subscribe((signals) => {
          if (signals[signalName] !== void 0) {
            setDisplayContent(signals[signalName]);
          }
        });
        const initial = cacaoWs.getSignal(signalName);
        if (initial !== void 0) {
          setDisplayContent(initial);
        }
        return unsubscribe;
      }
    }, [signalName]);
    const classNames = [
      "text",
      color === "muted" && "text-muted",
      size === "sm" && "text-sm",
      size === "lg" && "text-lg"
    ].filter(Boolean).join(" ");
    const style = weight ? { fontWeight: weight } : void 0;
    return h28("p", { className: classNames, style }, displayContent);
  }

  // src/components/typography/Title.js
  var { createElement: h29 } = React;
  function Title({ props }) {
    return h29("h" + (props.level || 1), { className: "title title-" + (props.level || 1) }, props.text);
  }

  // src/components/display/index.js
  var display_exports = {};
  __export(display_exports, {
    Accordion: () => Accordion,
    AccordionItem: () => AccordionItem,
    Alert: () => Alert,
    Anchor: () => Anchor,
    Badge: () => Badge,
    Breadcrumb: () => Breadcrumb,
    Card: () => Card,
    DataFrameView: () => DataFrameView,
    Diff: () => Diff,
    FileTree: () => FileTree,
    Gauge: () => Gauge,
    Image: () => Image,
    JsonView: () => JsonView,
    LinkCard: () => LinkCard,
    Metric: () => Metric,
    Modal: () => Modal,
    MplChart: () => MplChart,
    Progress: () => Progress,
    Step: () => Step,
    Steps: () => Steps,
    SubNav: () => SubNav,
    SubNavGroup: () => SubNavGroup,
    SubNavItem: () => SubNavItem,
    Table: () => Table,
    Timeline: () => Timeline,
    TimelineItem: () => TimelineItem,
    Tooltip: () => Tooltip,
    Video: () => Video,
    VirtualList: () => VirtualList
  });

  // src/components/display/Accordion.js
  var { createElement: h30, useState: useState10 } = React;
  function AccordionItemInner({ title, defaultOpen, icon, children, mode, openIndex, index, setOpenIndex }) {
    const isControlled = mode === "single";
    const [localOpen, setLocalOpen] = useState10(defaultOpen || false);
    const isOpen = isControlled ? openIndex === index : localOpen;
    const toggle = () => {
      if (isControlled) {
        setOpenIndex(isOpen ? -1 : index);
      } else {
        setLocalOpen(!localOpen);
      }
    };
    return h30("div", { className: "c-accordion-item" + (isOpen ? " c-accordion-item--open" : "") }, [
      h30("button", {
        key: "header",
        className: "c-accordion-header",
        onClick: toggle,
        "aria-expanded": isOpen
      }, [
        icon && h30("span", { key: "icon", className: "c-accordion-icon" }, getIcon(icon)),
        h30("span", { key: "title", className: "c-accordion-title" }, title),
        h30("span", { key: "chevron", className: "c-accordion-chevron" + (isOpen ? " c-accordion-chevron--open" : "") }, "\u25B6")
      ]),
      isOpen && h30("div", { key: "content", className: "c-accordion-content" }, children)
    ]);
  }
  function Accordion({ props, children, setActiveTab, activeTab }) {
    const { items, mode = "multiple" } = props;
    const [openIndex, setOpenIndex] = useState10(-1);
    const renderers2 = window.Cacao?.renderers || {};
    if (items && items.length) {
      return h30(
        "div",
        { className: "c-accordion" },
        items.map(
          (item, i) => h30(AccordionItemInner, {
            key: i,
            title: item.title,
            defaultOpen: item.defaultOpen || false,
            icon: item.icon,
            children: [h30("p", null, item.content)],
            mode,
            openIndex,
            index: i,
            setOpenIndex
          })
        )
      );
    }
    return h30(
      "div",
      { className: "c-accordion" },
      children.map((child, i) => {
        if (!child)
          return null;
        return React.cloneElement(child, { key: i, accordionMode: mode, accordionIndex: i, accordionOpenIndex: openIndex, setAccordionOpenIndex: setOpenIndex });
      })
    );
  }
  function AccordionItem({ props, children, accordionMode, accordionIndex, accordionOpenIndex, setAccordionOpenIndex }) {
    const { title, defaultOpen, icon } = props;
    return h30(AccordionItemInner, {
      title,
      defaultOpen,
      icon,
      children,
      mode: accordionMode || "multiple",
      openIndex: accordionOpenIndex,
      index: accordionIndex || 0,
      setOpenIndex: setAccordionOpenIndex || (() => {
      })
    });
  }

  // src/components/display/Alert.js
  var { createElement: h31, useState: useState11 } = React;
  function Alert({ props }) {
    const [dismissed, setDismissed] = useState11(false);
    if (dismissed)
      return null;
    return h31("div", { className: "alert alert-" + (props.type || "info"), role: "alert" }, [
      props.title && h31("strong", { key: "title" }, props.title + ": "),
      h31("span", { key: "msg" }, props.message),
      props.closable && h31("button", {
        key: "close",
        className: "alert-close",
        onClick: () => setDismissed(true),
        "aria-label": "Dismiss alert"
      }, "\xD7")
    ]);
  }

  // src/components/display/Anchor.js
  var { createElement: h32, useEffect: useEffect11, useRef: useRef8 } = React;
  function Anchor({ props }) {
    const { id, offset = 0 } = props;
    const ref = useRef8(null);
    useEffect11(() => {
      if (!id)
        return;
      const hash = window.location.hash;
      const target = hash.includes("#") ? hash.split("#").pop() : "";
      if (target === id) {
        setTimeout(() => {
          if (ref.current) {
            const top = ref.current.getBoundingClientRect().top + window.scrollY - offset;
            window.scrollTo({ top, behavior: "smooth" });
          }
        }, 100);
      }
    }, [id, offset]);
    return h32("div", {
      ref,
      id,
      className: "c-anchor",
      "aria-hidden": "true"
    });
  }

  // src/components/display/Badge.js
  var { createElement: h33 } = React;
  function Badge({ props }) {
    const { text: text2, color = "default" } = props;
    return h33("span", { className: `c-badge c-badge-${color}` }, text2);
  }

  // src/components/display/Breadcrumb.js
  var { createElement: h34 } = React;
  function Breadcrumb({ props }) {
    const { items = [], separator = "/" } = props;
    return h34(
      "nav",
      { className: "c-breadcrumb", "aria-label": "Breadcrumb" },
      h34(
        "ol",
        { className: "c-breadcrumb-list" },
        items.map((item, i) => {
          const isLast = i === items.length - 1;
          return h34("li", { key: i, className: "c-breadcrumb-item" + (isLast ? " c-breadcrumb-item--active" : "") }, [
            i > 0 && h34("span", { key: "sep", className: "c-breadcrumb-separator", "aria-hidden": true }, separator),
            item.icon && h34("span", { key: "icon", className: "c-breadcrumb-icon" }, getIcon(item.icon)),
            isLast ? h34("span", { key: "label", "aria-current": "page" }, item.label) : item.href ? h34("a", { key: "label", href: item.href, className: "c-breadcrumb-link" }, item.label) : h34("span", { key: "label" }, item.label)
          ]);
        })
      )
    );
  }

  // src/components/display/Card.js
  var { createElement: h35 } = React;
  function Card({ props, children }) {
    return h35("div", { className: "card" }, [
      props.title && h35("div", { className: "card-title", key: "title" }, props.title),
      ...children
    ]);
  }

  // src/components/display/DataFrameView.js
  var { createElement: h36, useState: useState12, useMemo: useMemo3 } = React;
  function DataFrameView({ props }) {
    const data = props.data || [];
    const columns = props.columns || (data[0] ? Object.keys(data[0]).map((k2) => ({ key: k2, title: k2 })) : []);
    const colDefs = columns.map((c) => typeof c === "string" ? { key: c, title: c } : c);
    const pageSize = props.pageSize || 25;
    const searchable = props.searchable !== false;
    const sortable = props.sortable !== false;
    const paginate = props.paginate !== false;
    const showDtypes = props.showDtypes !== false;
    const showShape = props.showShape !== false;
    const striped = props.striped !== false;
    const shape = props.shape;
    const framework = props.framework || "unknown";
    const title = props.title;
    const [search, setSearch] = useState12("");
    const [sortCol, setSortCol] = useState12(null);
    const [sortDir, setSortDir] = useState12("asc");
    const [page, setPage] = useState12(0);
    const filtered = useMemo3(() => {
      if (!search)
        return data;
      const q2 = search.toLowerCase();
      return data.filter(
        (row) => colDefs.some((c) => String(row[c.key] ?? "").toLowerCase().includes(q2))
      );
    }, [data, search, colDefs]);
    const sorted = useMemo3(() => {
      if (!sortCol)
        return filtered;
      return [...filtered].sort((a, b2) => {
        const va = a[sortCol], vb = b2[sortCol];
        if (va == null && vb == null)
          return 0;
        if (va == null)
          return 1;
        if (vb == null)
          return -1;
        if (typeof va === "number" && typeof vb === "number") {
          return sortDir === "asc" ? va - vb : vb - va;
        }
        const sa = String(va), sb = String(vb);
        return sortDir === "asc" ? sa.localeCompare(sb) : sb.localeCompare(sa);
      });
    }, [filtered, sortCol, sortDir]);
    const totalPages = paginate ? Math.ceil(sorted.length / pageSize) : 1;
    const pageData = paginate ? sorted.slice(page * pageSize, (page + 1) * pageSize) : sorted;
    const handleSort = (key) => {
      if (!sortable)
        return;
      if (sortCol === key) {
        setSortDir((d) => d === "asc" ? "desc" : "asc");
      } else {
        setSortCol(key);
        setSortDir("asc");
      }
      setPage(0);
    };
    const dtypeBadgeClass = (dtype) => {
      if (!dtype)
        return "df-dtype";
      const d = dtype.toLowerCase();
      if (d.includes("int") || d.includes("float") || d.includes("f64") || d.includes("i64") || d.includes("u"))
        return "df-dtype df-dtype--num";
      if (d.includes("bool"))
        return "df-dtype df-dtype--bool";
      if (d.includes("date") || d.includes("time"))
        return "df-dtype df-dtype--date";
      if (d.includes("str") || d.includes("object") || d.includes("utf8"))
        return "df-dtype df-dtype--str";
      return "df-dtype";
    };
    const frameworkLabel = framework === "pandas" ? "pandas" : framework === "polars" ? "polars" : null;
    return h36("div", { className: "df-view" }, [
      // Header
      (title || showShape || searchable) && h36("div", { className: "df-header", key: "header" }, [
        h36("div", { className: "df-header__left", key: "left" }, [
          title && h36("span", { className: "df-title", key: "title" }, title),
          frameworkLabel && h36("span", { className: "df-framework", key: "fw" }, frameworkLabel),
          showShape && shape && h36(
            "span",
            { className: "df-shape", key: "shape" },
            `${shape[0].toLocaleString()} rows \xD7 ${shape[1]} cols`
          )
        ]),
        searchable && h36("input", {
          key: "search",
          className: "df-search",
          type: "text",
          placeholder: "Search...",
          value: search,
          onInput: (e) => {
            setSearch(e.target.value);
            setPage(0);
          }
        })
      ]),
      // Table
      h36(
        "div",
        { className: "df-table-wrap", key: "table" },
        h36("table", { className: striped ? "df-table df-table--striped" : "df-table" }, [
          h36(
            "thead",
            { key: "head" },
            h36("tr", null, colDefs.map(
              (c) => h36("th", {
                key: c.key,
                className: sortable ? "df-th df-th--sortable" : "df-th",
                onClick: () => handleSort(c.key)
              }, [
                h36("span", { className: "df-th__label", key: "label" }, c.title || c.key),
                sortCol === c.key && h36(
                  "span",
                  { className: "df-th__sort", key: "sort" },
                  sortDir === "asc" ? " \u25B2" : " \u25BC"
                ),
                showDtypes && c.dtype && h36("span", {
                  className: dtypeBadgeClass(c.dtype),
                  key: "dtype"
                }, c.dtype)
              ])
            ))
          ),
          h36("tbody", { key: "body" }, pageData.map(
            (row, i) => h36("tr", { key: i }, colDefs.map(
              (c) => h36("td", { key: c.key, "data-label": c.title || c.key }, formatValue(row[c.key]))
            ))
          ))
        ])
      ),
      // Footer / Pagination
      paginate && totalPages > 1 && h36("div", { className: "df-footer", key: "footer" }, [
        h36(
          "span",
          { className: "df-footer__info", key: "info" },
          `Showing ${page * pageSize + 1}\u2013${Math.min((page + 1) * pageSize, sorted.length)} of ${sorted.length}`
        ),
        h36("div", { className: "df-pagination", key: "pages" }, [
          h36("button", {
            key: "prev",
            className: "df-page-btn",
            disabled: page === 0,
            onClick: () => setPage((p) => p - 1)
          }, "\u2190"),
          h36("span", { key: "current", className: "df-page-info" }, `${page + 1} / ${totalPages}`),
          h36("button", {
            key: "next",
            className: "df-page-btn",
            disabled: page >= totalPages - 1,
            onClick: () => setPage((p) => p + 1)
          }, "\u2192")
        ])
      ])
    ]);
  }

  // src/components/display/Diff.js
  var { createElement: h37, useMemo: useMemo4 } = React;
  function diffLines(oldLines, newLines) {
    const m2 = oldLines.length;
    const n = newLines.length;
    const dp = Array.from({ length: m2 + 1 }, () => Array(n + 1).fill(0));
    for (let i2 = 1; i2 <= m2; i2++) {
      for (let j3 = 1; j3 <= n; j3++) {
        if (oldLines[i2 - 1] === newLines[j3 - 1]) {
          dp[i2][j3] = dp[i2 - 1][j3 - 1] + 1;
        } else {
          dp[i2][j3] = Math.max(dp[i2 - 1][j3], dp[i2][j3 - 1]);
        }
      }
    }
    const result = [];
    let i = m2, j2 = n;
    while (i > 0 || j2 > 0) {
      if (i > 0 && j2 > 0 && oldLines[i - 1] === newLines[j2 - 1]) {
        result.unshift({ type: "equal", oldLine: i, newLine: j2, text: oldLines[i - 1] });
        i--;
        j2--;
      } else if (j2 > 0 && (i === 0 || dp[i][j2 - 1] >= dp[i - 1][j2])) {
        result.unshift({ type: "add", newLine: j2, text: newLines[j2 - 1] });
        j2--;
      } else {
        result.unshift({ type: "remove", oldLine: i, text: oldLines[i - 1] });
        i--;
      }
    }
    return result;
  }
  function UnifiedView({ diff, language }) {
    return h37(
      "table",
      { className: "c-diff-table" },
      h37(
        "tbody",
        null,
        diff.map((line, i) => {
          const cls = line.type === "add" ? "c-diff-line--add" : line.type === "remove" ? "c-diff-line--remove" : "";
          const prefix = line.type === "add" ? "+" : line.type === "remove" ? "-" : " ";
          return h37("tr", { key: i, className: "c-diff-line " + cls }, [
            h37("td", { key: "old", className: "c-diff-gutter" }, line.oldLine || ""),
            h37("td", { key: "new", className: "c-diff-gutter" }, line.newLine || ""),
            h37("td", { key: "prefix", className: "c-diff-prefix" }, prefix),
            h37("td", { key: "code", className: "c-diff-code" }, line.text)
          ]);
        })
      )
    );
  }
  function SideBySideView({ diff }) {
    const left = [];
    const right = [];
    diff.forEach((line, i) => {
      if (line.type === "equal") {
        left.push({ num: line.oldLine, text: line.text, type: "equal" });
        right.push({ num: line.newLine, text: line.text, type: "equal" });
      } else if (line.type === "remove") {
        left.push({ num: line.oldLine, text: line.text, type: "remove" });
        right.push({ num: "", text: "", type: "empty" });
      } else {
        left.push({ num: "", text: "", type: "empty" });
        right.push({ num: line.newLine, text: line.text, type: "add" });
      }
    });
    return h37("div", { className: "c-diff-side-by-side" }, [
      h37(
        "table",
        { key: "left", className: "c-diff-table c-diff-table--left" },
        h37(
          "tbody",
          null,
          left.map(
            (line, i) => h37("tr", { key: i, className: "c-diff-line c-diff-line--" + line.type }, [
              h37("td", { key: "num", className: "c-diff-gutter" }, line.num),
              h37("td", { key: "code", className: "c-diff-code" }, line.text)
            ])
          )
        )
      ),
      h37(
        "table",
        { key: "right", className: "c-diff-table c-diff-table--right" },
        h37(
          "tbody",
          null,
          right.map(
            (line, i) => h37("tr", { key: i, className: "c-diff-line c-diff-line--" + line.type }, [
              h37("td", { key: "num", className: "c-diff-gutter" }, line.num),
              h37("td", { key: "code", className: "c-diff-code" }, line.text)
            ])
          )
        )
      )
    ]);
  }
  function Diff({ props }) {
    const { old_code = "", new_code = "", language = "", mode = "unified" } = props;
    const diff = useMemo4(() => {
      const oldLines = old_code.split("\n");
      const newLines = new_code.split("\n");
      return diffLines(oldLines, newLines);
    }, [old_code, new_code]);
    const stats = useMemo4(() => {
      let added = 0, removed = 0;
      diff.forEach((l) => {
        if (l.type === "add")
          added++;
        if (l.type === "remove")
          removed++;
      });
      return { added, removed };
    }, [diff]);
    return h37("div", { className: "c-diff" }, [
      h37("div", { key: "header", className: "c-diff-header" }, [
        language && h37("span", { key: "lang", className: "c-diff-lang" }, language),
        h37("span", { key: "stats", className: "c-diff-stats" }, [
          stats.added > 0 && h37("span", { key: "add", className: "c-diff-stat--add" }, "+" + stats.added),
          stats.removed > 0 && h37("span", { key: "rm", className: "c-diff-stat--remove" }, "-" + stats.removed)
        ])
      ]),
      h37(
        "div",
        { key: "body", className: "c-diff-body" },
        mode === "side-by-side" ? h37(SideBySideView, { diff }) : h37(UnifiedView, { diff, language })
      )
    ]);
  }

  // src/components/display/FileTree.js
  var { createElement: h38, useState: useState13 } = React;
  function getFileIcon(name, isDir) {
    if (isDir)
      return "\u{1F4C1}";
    const ext = name.split(".").pop()?.toLowerCase();
    const icons = {
      py: "\u{1F40D}",
      js: "\u{1F7E8}",
      ts: "\u{1F535}",
      jsx: "\u269B\uFE0F",
      tsx: "\u269B\uFE0F",
      md: "\u{1F4DD}",
      json: "\u{1F4C4}",
      css: "\u{1F3A8}",
      less: "\u{1F3A8}",
      html: "\u{1F310}",
      yml: "\u2699\uFE0F",
      yaml: "\u2699\uFE0F",
      toml: "\u2699\uFE0F",
      png: "\u{1F5BC}\uFE0F",
      jpg: "\u{1F5BC}\uFE0F",
      svg: "\u{1F5BC}\uFE0F",
      gif: "\u{1F5BC}\uFE0F"
    };
    return icons[ext] || "\u{1F4C4}";
  }
  function TreeNode({ name, value, depth, highlight }) {
    const isDir = value !== null && typeof value === "object";
    const [open, setOpen] = useState13(true);
    const isHighlighted = highlight && name === highlight;
    return h38("div", { className: "c-file-tree-node" }, [
      h38("div", {
        key: "label",
        className: "c-file-tree-label" + (isHighlighted ? " c-file-tree-label--highlight" : ""),
        style: { paddingLeft: depth * 16 + 4 + "px" },
        onClick: isDir ? () => setOpen(!open) : void 0
      }, [
        isDir && h38("span", { key: "arrow", className: "c-file-tree-arrow" + (open ? " c-file-tree-arrow--open" : "") }, "\u25B6"),
        h38("span", { key: "icon", className: "c-file-tree-icon" }, getFileIcon(name, isDir)),
        h38("span", { key: "name", className: "c-file-tree-name" }, name)
      ]),
      isDir && open && h38(
        "div",
        { key: "children", className: "c-file-tree-children" },
        Object.entries(value).map(
          ([k2, v2]) => h38(TreeNode, { key: k2, name: k2, value: v2, depth: depth + 1, highlight })
        )
      )
    ]);
  }
  function parseTreeString(str) {
    const lines = str.trim().split("\n");
    const root = {};
    const stack = [{ obj: root, indent: -1 }];
    for (const line of lines) {
      const cleaned = line.replace(/[│├└──\s]/g, "").replace(/\u2502|\u251C|\u2514|\u2500/g, "");
      if (!cleaned)
        continue;
      const indent = line.search(/[^\s│├└──\u2502\u251C\u2514\u2500]/);
      const name = cleaned.trim();
      const isDir = name.endsWith("/");
      const cleanName = isDir ? name.slice(0, -1) : name;
      while (stack.length > 1 && stack[stack.length - 1].indent >= indent) {
        stack.pop();
      }
      const parent = stack[stack.length - 1].obj;
      if (isDir) {
        parent[cleanName] = {};
        stack.push({ obj: parent[cleanName], indent });
      } else {
        parent[cleanName] = null;
      }
    }
    return root;
  }
  function FileTree({ props }) {
    let { data, highlight } = props;
    if (typeof data === "string") {
      data = parseTreeString(data);
    }
    return h38(
      "div",
      { className: "c-file-tree" },
      Object.entries(data).map(
        ([k2, v2]) => h38(TreeNode, { key: k2, name: k2, value: v2, depth: 0, highlight })
      )
    );
  }

  // src/components/display/Gauge.js
  var { createElement: h39 } = React;
  function Gauge({ props }) {
    const pct = props.value / (props.max_value || 100) * 100;
    const angle = pct / 100 * 180;
    return h39("div", { className: "gauge-container" }, [
      h39("svg", { className: "gauge-svg", viewBox: "0 0 120 80", key: "svg" }, [
        h39("defs", { key: "defs" }, h39("linearGradient", { id: "gaugeGradient", x1: "0%", y1: "0%", x2: "100%", y2: "0%" }, [
          h39("stop", { offset: "0%", stopColor: "var(--gradient-start)", key: "s1" }),
          h39("stop", { offset: "100%", stopColor: "var(--gradient-end)", key: "s2" })
        ])),
        h39("path", { d: "M10 70 A50 50 0 0 1 110 70", fill: "none", stroke: "var(--bg-tertiary)", strokeWidth: 12, strokeLinecap: "round", key: "bg" }),
        h39("path", { d: "M10 70 A50 50 0 0 1 110 70", fill: "none", stroke: "url(#gaugeGradient)", strokeWidth: 12, strokeLinecap: "round", strokeDasharray: angle / 180 * 157 + " 157", key: "fill" })
      ]),
      h39("div", { className: "gauge-value", key: "value" }, props.format ? props.format.replace("{value}", props.value) : props.value + "%"),
      props.title && h39("div", { className: "gauge-title", key: "title" }, props.title)
    ]);
  }

  // src/components/display/Image.js
  var { createElement: h40, useState: useState14, useRef: useRef9, useEffect: useEffect12 } = React;
  function Image({ props }) {
    const { src, alt = "", caption, width, height, lightbox = false, lazy = true } = props;
    const [showLightbox, setShowLightbox] = useState14(false);
    const [loaded, setLoaded] = useState14(!lazy);
    const imgRef = useRef9(null);
    useEffect12(() => {
      if (!lazy || loaded)
        return;
      const observer = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting) {
          setLoaded(true);
          observer.disconnect();
        }
      }, { rootMargin: "200px" });
      if (imgRef.current)
        observer.observe(imgRef.current);
      return () => observer.disconnect();
    }, [lazy, loaded]);
    useEffect12(() => {
      if (!showLightbox)
        return;
      const handler = (e) => {
        if (e.key === "Escape")
          setShowLightbox(false);
      };
      window.addEventListener("keydown", handler);
      return () => window.removeEventListener("keydown", handler);
    }, [showLightbox]);
    const imgStyle = {};
    if (width)
      imgStyle.width = typeof width === "number" ? width + "px" : width;
    if (height)
      imgStyle.height = typeof height === "number" ? height + "px" : height;
    return h40("figure", { className: "c-image", ref: imgRef }, [
      loaded ? h40("img", {
        key: "img",
        src,
        alt,
        style: imgStyle,
        className: "c-image-img" + (lightbox ? " c-image-img--clickable" : ""),
        onClick: lightbox ? () => setShowLightbox(true) : void 0,
        loading: lazy ? "lazy" : void 0
      }) : h40("div", { key: "placeholder", className: "c-image-placeholder", style: imgStyle }),
      caption && h40("figcaption", { key: "caption", className: "c-image-caption" }, caption),
      showLightbox && h40("div", {
        key: "lightbox",
        className: "c-image-lightbox",
        onClick: () => setShowLightbox(false)
      }, [
        h40("img", { key: "lbimg", src, alt, className: "c-image-lightbox-img" }),
        h40("button", {
          key: "close",
          className: "c-image-lightbox-close",
          onClick: () => setShowLightbox(false),
          "aria-label": "Close"
        }, "\xD7")
      ])
    ]);
  }

  // src/components/display/JsonView.js
  var { createElement: h41, useState: useState15 } = React;
  function formatValue2(value) {
    if (value === null)
      return "null";
    if (value === void 0)
      return "undefined";
    if (typeof value === "string")
      return `"${value}"`;
    if (typeof value === "boolean")
      return value ? "true" : "false";
    return String(value);
  }
  function JsonNode({ name, value, depth = 0, expanded: defaultExpanded }) {
    const [isExpanded, setIsExpanded] = useState15(defaultExpanded);
    const type = Array.isArray(value) ? "array" : typeof value;
    const isExpandable = type === "object" || type === "array";
    const isEmpty = isExpandable && Object.keys(value || {}).length === 0;
    const indent = { paddingLeft: `${depth * 16}px` };
    if (!isExpandable || value === null) {
      return h41(
        "div",
        { className: "json-node json-leaf", style: indent },
        name !== null && h41("span", { className: "json-key" }, `"${name}": `),
        h41(
          "span",
          { className: `json-value json-${type === "object" ? "null" : type}` },
          formatValue2(value)
        )
      );
    }
    const entries = Object.entries(value);
    const bracket = type === "array" ? ["[", "]"] : ["{", "}"];
    return h41("div", { className: "json-node" }, [
      h41("div", {
        className: "json-expandable",
        style: indent,
        onClick: () => setIsExpanded(!isExpanded),
        key: "header"
      }, [
        h41("span", { className: "json-toggle", key: "toggle" }, isExpanded ? "\u25BC" : "\u25B6"),
        name !== null && h41("span", { className: "json-key", key: "key" }, `"${name}": `),
        h41("span", { className: "json-bracket", key: "open" }, bracket[0]),
        !isExpanded && h41(
          "span",
          { className: "json-collapsed", key: "dots" },
          isEmpty ? "" : `... ${entries.length} ${type === "array" ? "items" : "keys"}`
        ),
        !isExpanded && h41("span", { className: "json-bracket", key: "close" }, bracket[1])
      ]),
      isExpanded && entries.map(
        ([k2, v2], i) => h41(JsonNode, {
          key: k2,
          name: type === "array" ? null : k2,
          value: v2,
          depth: depth + 1,
          expanded: defaultExpanded
        })
      ),
      isExpanded && h41(
        "div",
        { style: indent, key: "closing" },
        h41("span", { className: "json-bracket" }, bracket[1])
      )
    ]);
  }
  function JsonView({ props }) {
    const { data, expanded = true } = props;
    return h41(
      "div",
      { className: "json-view" },
      h41(JsonNode, { name: null, value: data, depth: 0, expanded })
    );
  }

  // src/components/display/LinkCard.js
  var { createElement: h42 } = React;
  function LinkCard({ props }) {
    const { title, description, href, icon } = props;
    const content = [
      h42("div", { key: "body", className: "c-link-card-body" }, [
        icon && h42("span", { key: "icon", className: "c-link-card-icon" }, getIcon(icon)),
        h42("div", { key: "text", className: "c-link-card-text" }, [
          h42("div", { key: "title", className: "c-link-card-title" }, title),
          description && h42("div", { key: "desc", className: "c-link-card-description" }, description)
        ])
      ]),
      h42("span", { key: "arrow", className: "c-link-card-arrow" }, "\u2192")
    ];
    if (href) {
      return h42("a", { className: "c-link-card", href }, content);
    }
    return h42("div", { className: "c-link-card" }, content);
  }

  // src/components/display/Metric.js
  var { createElement: h43 } = React;
  function Metric({ props }) {
    return h43("div", { className: "metric" }, [
      h43("div", { className: "metric-label", key: "label" }, props.label),
      h43("div", { className: "metric-value", key: "value" }, (props.prefix || "") + props.value + (props.suffix || "")),
      props.trend && h43("div", {
        className: "metric-trend " + (props.trendDirection || (props.trend.startsWith("+") ? "up" : "down")),
        key: "trend"
      }, (props.trendDirection === "up" || props.trend.startsWith("+") ? "\u2191 " : "\u2193 ") + props.trend)
    ]);
  }

  // src/components/display/Modal.js
  var { createElement: h44, useState: useState16, useEffect: useEffect13, useCallback: useCallback8 } = React;
  function Modal({ props, children }) {
    const { title, signal, size = "md", closeOnBackdrop = true, closeOnEscape = true } = props;
    const signalName = signal?.__signal__;
    const [visible, setVisible] = useState16(!signalName);
    useEffect13(() => {
      if (!signalName)
        return;
      const handleSignal = (e) => {
        if (e.detail?.name === signalName) {
          setVisible(!!e.detail.value);
        }
      };
      window.addEventListener("cacao:signal", handleSignal);
      return () => window.removeEventListener("cacao:signal", handleSignal);
    }, [signalName]);
    const close = useCallback8(() => {
      if (signalName) {
        window.dispatchEvent(new CustomEvent("cacao:set-signal", {
          detail: { name: signalName, value: false }
        }));
      }
      setVisible(false);
    }, [signalName]);
    useEffect13(() => {
      if (!visible || !closeOnEscape)
        return;
      const handler = (e) => {
        if (e.key === "Escape")
          close();
      };
      window.addEventListener("keydown", handler);
      return () => window.removeEventListener("keydown", handler);
    }, [visible, closeOnEscape, close]);
    if (!visible)
      return null;
    return h44(
      "div",
      {
        className: "c-modal-overlay",
        onClick: closeOnBackdrop ? (e) => {
          if (e.target === e.currentTarget)
            close();
        } : void 0
      },
      h44("div", { className: "c-modal c-modal--" + size, role: "dialog", "aria-modal": true }, [
        (title || true) && h44("div", { key: "header", className: "c-modal-header" }, [
          title && h44("div", { key: "title", className: "c-modal-title" }, title),
          h44("button", {
            key: "close",
            className: "c-modal-close",
            onClick: close,
            "aria-label": "Close"
          }, "\xD7")
        ]),
        h44("div", { key: "body", className: "c-modal-body" }, children)
      ])
    );
  }

  // src/components/display/MplChart.js
  var { createElement: h45 } = React;
  function MplChart({ props }) {
    const title = props.title;
    const format = props.format || "svg";
    return h45("div", { className: "mpl-chart" }, [
      title && h45("div", { className: "mpl-chart__title", key: "title" }, title),
      format === "svg" ? h45("div", {
        key: "svg",
        className: "mpl-chart__content",
        dangerouslySetInnerHTML: { __html: props.svg || "" }
      }) : h45("img", {
        key: "img",
        className: "mpl-chart__content",
        src: props.src,
        alt: title || "Matplotlib figure"
      })
    ]);
  }

  // src/components/display/Progress.js
  var { createElement: h46 } = React;
  function Progress({ props }) {
    return h46("div", { className: "progress-container" }, [
      props.label && h46("div", { className: "progress-label", key: "label" }, props.label),
      h46(
        "div",
        { className: "progress-bar", key: "bar" },
        h46("div", { className: "progress-fill", style: { width: props.value / (props.max || 100) * 100 + "%" } })
      )
    ]);
  }

  // src/components/display/Steps.js
  var { createElement: h47 } = React;
  function Steps({ props, children }) {
    const { direction = "horizontal" } = props;
    return h47("div", {
      className: "c-steps c-steps--" + direction
    }, children);
  }
  function Step({ props }) {
    const { title, description, status = "pending", icon } = props;
    const statusIcon = {
      complete: "\u2713",
      active: "\u25CF",
      error: "\u2717",
      pending: ""
    };
    return h47("div", { className: "c-step c-step--" + status }, [
      h47(
        "div",
        { key: "indicator", className: "c-step-indicator" },
        icon ? getIcon(icon) : h47("span", null, statusIcon[status] || "")
      ),
      h47("div", { key: "content", className: "c-step-content" }, [
        h47("div", { key: "title", className: "c-step-title" }, title),
        description && h47("div", { key: "desc", className: "c-step-description" }, description)
      ])
    ]);
  }

  // src/components/display/SubNav.js
  var { createElement: h48, useState: useState17, useCallback: useCallback9, useMemo: useMemo5, useRef: useRef10, useEffect: useEffect14 } = React;
  function SubNavItem({ props }) {
    const { label, badge, tag, tag_color, target, href } = props;
    const handleClick = useCallback9((e) => {
      if (target) {
        e.preventDefault();
        const el2 = document.getElementById(target);
        if (el2) {
          el2.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    }, [target]);
    const tagColorClass = tag_color ? " c-subnav-tag--" + tag_color : "";
    return h48("a", {
      className: "c-subnav-item",
      href: href || "#",
      onClick: handleClick
    }, [
      tag && h48("span", {
        key: "tag",
        className: "c-subnav-tag" + tagColorClass
      }, tag),
      h48("span", { key: "label", className: "c-subnav-label" }, label),
      badge != null && h48("span", { key: "badge", className: "c-subnav-badge" }, badge)
    ]);
  }
  function SubNavGroup({ props }) {
    const { label } = props;
    return h48("div", { className: "c-subnav-group" }, label);
  }
  function SubNav({ props, children }) {
    const { searchable = false, placeholder = "Search..." } = props;
    const [query, setQuery] = useState17("");
    const inputRef = useRef10(null);
    const filteredChildren = useMemo5(() => {
      if (!query || !children)
        return children;
      const q2 = query.toLowerCase();
      const result = [];
      let lastGroup = null;
      let groupHasMatch = false;
      for (const child of children) {
        if (!child || !child.props)
          continue;
        const childType = child.props.type || "";
        const innerProps = child.props.props || {};
        if (childType === "SubNavGroup") {
          if (lastGroup && groupHasMatch) {
            result.push(lastGroup);
          }
          lastGroup = child;
          groupHasMatch = false;
        } else if (childType === "SubNavItem") {
          const label = (innerProps.label || "").toLowerCase();
          const tag = (innerProps.tag || "").toLowerCase();
          if (label.includes(q2) || tag.includes(q2)) {
            if (lastGroup && !groupHasMatch) {
              result.push(lastGroup);
              groupHasMatch = true;
            }
            result.push(child);
          }
        } else {
          result.push(child);
        }
      }
      if (lastGroup && groupHasMatch) {
      }
      return result;
    }, [query, children]);
    const itemCount = useMemo5(() => {
      if (!children)
        return 0;
      return children.filter((c) => c && c.props && c.props.type === "SubNavItem").length;
    }, [children]);
    const matchCount = useMemo5(() => {
      if (!query || !filteredChildren)
        return itemCount;
      return filteredChildren.filter((c) => c && c.props && c.props.type === "SubNavItem").length;
    }, [query, filteredChildren, itemCount]);
    return h48("div", { className: "c-subnav" }, [
      searchable && h48(
        "div",
        { key: "search", className: "c-subnav-search" },
        h48("div", { className: "c-subnav-search-wrap" }, [
          h48("svg", {
            key: "icon",
            className: "c-subnav-search-icon",
            viewBox: "0 0 16 16",
            fill: "none",
            stroke: "currentColor",
            strokeWidth: "1.5",
            width: 14,
            height: 14
          }, h48("path", { d: "M11.5 11.5L14 14M6.5 12A5.5 5.5 0 106.5 1a5.5 5.5 0 000 11z" })),
          h48("input", {
            key: "input",
            ref: inputRef,
            type: "text",
            className: "c-subnav-search-input",
            placeholder,
            value: query,
            onInput: (e) => setQuery(e.target.value)
          }),
          query && h48("span", {
            key: "count",
            className: "c-subnav-search-count"
          }, matchCount + "/" + itemCount)
        ])
      ),
      h48("div", { key: "items", className: "c-subnav-items" }, filteredChildren),
      query && matchCount === 0 && h48("div", {
        key: "empty",
        className: "c-subnav-empty"
      }, "No matches")
    ]);
  }

  // src/components/display/Table.js
  var { createElement: h49 } = React;
  function Table({ props }) {
    const data = props.data || [];
    const columns = props.columns || (data[0] ? Object.keys(data[0]) : []);
    const colDefs = columns.map((c) => typeof c === "string" ? { key: c, title: c } : c);
    return h49(
      "div",
      { className: "table-container" },
      h49("table", null, [
        h49("thead", { key: "head" }, h49("tr", null, colDefs.map((c) => h49("th", { key: c.key }, c.title || c.key)))),
        h49("tbody", { key: "body" }, data.slice(0, props.pageSize || 10).map(
          (row, i) => h49("tr", { key: i }, colDefs.map((c) => h49("td", { key: c.key, "data-label": c.title || c.key }, formatValue(row[c.key]))))
        ))
      ])
    );
  }

  // src/components/display/Timeline.js
  var { createElement: h50 } = React;
  function Timeline({ props, children }) {
    const { items, alternate = false } = props;
    if (items && items.length) {
      return h50(
        "div",
        { className: "c-timeline" + (alternate ? " c-timeline--alternate" : "") },
        items.map(
          (item, i) => h50("div", { key: i, className: "c-timeline-item" }, [
            h50(
              "div",
              { key: "line", className: "c-timeline-line" },
              h50(
                "div",
                { className: "c-timeline-dot" + (item.color ? " c-timeline-dot--" + item.color : "") },
                item.icon ? getIcon(item.icon) : null
              )
            ),
            h50("div", { key: "content", className: "c-timeline-content" }, [
              h50("div", { key: "header", className: "c-timeline-header" }, [
                h50("div", { key: "title", className: "c-timeline-title" }, item.title),
                item.date && h50("div", { key: "date", className: "c-timeline-date" }, item.date)
              ]),
              item.description && h50("div", { key: "desc", className: "c-timeline-description" }, item.description)
            ])
          ])
        )
      );
    }
    return h50("div", { className: "c-timeline" + (alternate ? " c-timeline--alternate" : "") }, children);
  }
  function TimelineItem({ props, children }) {
    const { title, description, date, icon, color } = props;
    return h50("div", { className: "c-timeline-item" }, [
      h50(
        "div",
        { key: "line", className: "c-timeline-line" },
        h50(
          "div",
          { className: "c-timeline-dot" + (color ? " c-timeline-dot--" + color : "") },
          icon ? getIcon(icon) : null
        )
      ),
      h50("div", { key: "content", className: "c-timeline-content" }, [
        h50("div", { key: "header", className: "c-timeline-header" }, [
          title && h50("div", { key: "title", className: "c-timeline-title" }, title),
          date && h50("div", { key: "date", className: "c-timeline-date" }, date)
        ]),
        description && h50("div", { key: "desc", className: "c-timeline-description" }, description),
        children && children.length > 0 && h50("div", { key: "body", className: "c-timeline-body" }, children)
      ])
    ]);
  }

  // src/components/display/Tooltip.js
  var { createElement: h51, useState: useState18, useRef: useRef11 } = React;
  function Tooltip({ props, children }) {
    const { text: text2, position = "top", delay = 200 } = props;
    const [show, setShow] = useState18(false);
    const timeoutRef = useRef11(null);
    const handleEnter = () => {
      timeoutRef.current = setTimeout(() => setShow(true), delay);
    };
    const handleLeave = () => {
      clearTimeout(timeoutRef.current);
      setShow(false);
    };
    return h51("div", {
      className: "c-tooltip-wrapper",
      onMouseEnter: handleEnter,
      onMouseLeave: handleLeave,
      onFocus: handleEnter,
      onBlur: handleLeave
    }, [
      ...children,
      show && h51("div", {
        key: "tip",
        className: "c-tooltip c-tooltip--" + position,
        role: "tooltip"
      }, text2)
    ]);
  }

  // src/components/display/Video.js
  var { createElement: h52 } = React;
  function parseProvider(src) {
    if (!src)
      return { type: "direct", id: null };
    const ytMatch = src.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]+)/);
    if (ytMatch)
      return { type: "youtube", id: ytMatch[1] };
    const vimeoMatch = src.match(/vimeo\.com\/(?:video\/)?([\d]+)/);
    if (vimeoMatch)
      return { type: "vimeo", id: vimeoMatch[1] };
    return { type: "direct", id: null };
  }
  function Video({ props }) {
    const { src, title = "", width, height, aspect = "16/9", poster, autoplay = false, controls = true, loop = false, muted = false } = props;
    const { type, id } = parseProvider(src);
    const containerStyle = { aspectRatio: aspect };
    if (width)
      containerStyle.width = typeof width === "number" ? width + "px" : width;
    if (height) {
      containerStyle.height = typeof height === "number" ? height + "px" : height;
      containerStyle.aspectRatio = void 0;
    }
    if (type === "youtube") {
      const params = new URLSearchParams();
      if (autoplay)
        params.set("autoplay", "1");
      if (loop)
        params.set("loop", "1");
      if (muted)
        params.set("mute", "1");
      const paramStr = params.toString();
      return h52(
        "div",
        { className: "c-video", style: containerStyle },
        h52("iframe", {
          src: "https://www.youtube.com/embed/" + id + (paramStr ? "?" + paramStr : ""),
          title,
          frameBorder: "0",
          allow: "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
          allowFullScreen: true,
          className: "c-video-iframe"
        })
      );
    }
    if (type === "vimeo") {
      const params = new URLSearchParams();
      if (autoplay)
        params.set("autoplay", "1");
      if (loop)
        params.set("loop", "1");
      if (muted)
        params.set("muted", "1");
      const paramStr = params.toString();
      return h52(
        "div",
        { className: "c-video", style: containerStyle },
        h52("iframe", {
          src: "https://player.vimeo.com/video/" + id + (paramStr ? "?" + paramStr : ""),
          title,
          frameBorder: "0",
          allow: "autoplay; fullscreen; picture-in-picture",
          allowFullScreen: true,
          className: "c-video-iframe"
        })
      );
    }
    return h52(
      "div",
      { className: "c-video", style: containerStyle },
      h52("video", {
        src,
        title,
        poster,
        controls,
        autoPlay: autoplay,
        loop,
        muted,
        className: "c-video-player"
      })
    );
  }

  // src/components/display/VirtualList.js
  var { createElement: h53, useState: useState19, useEffect: useEffect15, useRef: useRef12, useCallback: useCallback10, useMemo: useMemo6 } = React;
  function getItemKey(item, index) {
    if (item && typeof item === "object") {
      if (item.id !== void 0)
        return String(item.id);
      if (item.key !== void 0)
        return String(item.key);
      if (item._id !== void 0)
        return String(item._id);
    }
    return String(index);
  }
  function VirtualList({ props, setActiveTab, activeTab }) {
    const {
      signal,
      row_height = 40,
      height = "400px",
      render_as = "Card",
      buffer = 5,
      gap = 0,
      jump_to = null,
      end_reached_threshold = 200
    } = props;
    const containerRef = useRef12(null);
    const [scrollTop, setScrollTop] = useState19(0);
    const [items, setItems] = useState19([]);
    const scrollRAF = useRef12(null);
    useEffect15(() => {
      const update = (signals) => {
        if (signal && signals[signal]) {
          setItems(signals[signal]);
        }
      };
      const initial = cacaoWs.getSignal(signal);
      if (initial)
        setItems(initial);
      return cacaoWs.subscribe(update);
    }, [signal]);
    useEffect15(() => {
      if (jump_to != null && containerRef.current) {
        const effectiveRowHeight2 = row_height + gap;
        containerRef.current.scrollTop = jump_to * effectiveRowHeight2;
      }
    }, [jump_to, row_height, gap]);
    const handleScroll = useCallback10((e) => {
      if (scrollRAF.current)
        return;
      scrollRAF.current = requestAnimationFrame(() => {
        scrollRAF.current = null;
        const target = e.target;
        setScrollTop(target.scrollTop);
        if (end_reached_threshold > 0) {
          const distFromBottom = target.scrollHeight - target.scrollTop - target.clientHeight;
          if (distFromBottom < end_reached_threshold) {
            cacaoWs.sendEvent(`${signal}:end_reached`, {
              scrollTop: target.scrollTop,
              itemCount: items.length
            });
          }
        }
      });
    }, [signal, items.length, end_reached_threshold]);
    useEffect15(() => {
      return () => {
        if (scrollRAF.current)
          cancelAnimationFrame(scrollRAF.current);
      };
    }, []);
    const effectiveRowHeight = row_height + gap;
    const containerHeight = containerRef.current?.clientHeight || parseInt(height) || 400;
    const totalHeight = items.length * effectiveRowHeight;
    const overscan = Math.max(buffer, 3);
    const startIndex = Math.max(0, Math.floor(scrollTop / effectiveRowHeight) - overscan);
    const visibleCount = Math.ceil(containerHeight / effectiveRowHeight) + overscan * 2;
    const endIndex = Math.min(items.length, startIndex + visibleCount);
    const renderers2 = window.Cacao?.renderers || {};
    const visibleItems = useMemo6(() => {
      const result = [];
      for (let i = startIndex; i < endIndex; i++) {
        const item = items[i];
        if (!item)
          continue;
        const compDef = {
          type: render_as,
          props: typeof item === "object" ? item : { value: item },
          children: []
        };
        const key = getItemKey(item, i);
        result.push(
          h53("div", {
            key,
            style: {
              position: "absolute",
              top: i * effectiveRowHeight,
              left: 0,
              right: 0,
              height: row_height
            }
          }, renderComponent(compDef, key, setActiveTab, activeTab, renderers2))
        );
      }
      return result;
    }, [startIndex, endIndex, items, render_as, effectiveRowHeight, row_height]);
    return h53(
      "div",
      {
        ref: containerRef,
        className: "virtual-list",
        style: { height, overflow: "auto", position: "relative" },
        onScroll: handleScroll
      },
      h53("div", {
        style: { height: totalHeight, position: "relative" }
      }, visibleItems)
    );
  }

  // src/components/form/index.js
  var form_exports = {};
  __export(form_exports, {
    Agent: () => Agent,
    BudgetGauge: () => BudgetGauge,
    Button: () => Button,
    ChainBuilder: () => ChainBuilder,
    Chat: () => Chat,
    Checkbox: () => Checkbox,
    Compare: () => Compare,
    CostDashboard: () => CostDashboard,
    DatePicker: () => DatePicker,
    DocumentUpload: () => DocumentUpload,
    Extract: () => Extract,
    FileUpload: () => FileUpload,
    Input: () => Input,
    Interface: () => Interface,
    ModelPicker: () => ModelPicker,
    MultiAgent: () => MultiAgent,
    SafetyPolicy: () => SafetyPolicy,
    SearchInput: () => SearchInput,
    Select: () => Select,
    Series: () => Series,
    SkillBrowser: () => SkillBrowser,
    SkillRunner: () => SkillRunner,
    Slider: () => Slider,
    SqlQuery: () => SqlQuery,
    Switch: () => Switch,
    Tab: () => Tab,
    Tabs: () => Tabs,
    Textarea: () => Textarea,
    ToolTimeline: () => ToolTimeline
  });

  // src/components/form/Agent.js
  var { createElement: h54, useState: useState20, useEffect: useEffect16, useRef: useRef13, useCallback: useCallback11 } = React;
  function Agent({ props }) {
    const {
      agent_id,
      title,
      placeholder = "Ask the agent...",
      height = "600px",
      show_steps = true,
      show_cost = true,
      has_tools = false,
      model = "",
      provider = ""
    } = props;
    const [inputText, setInputText] = useState20("");
    const [isRunning, setIsRunning] = useState20(false);
    const [steps, setSteps] = useState20([]);
    const [streamingText, setStreamingText] = useState20("");
    const [finalResponse, setFinalResponse] = useState20("");
    const [error, setError] = useState20(null);
    const [totalCost, setTotalCost] = useState20(0);
    const [totalTokens, setTotalTokens] = useState20(0);
    const [iterations, setIterations] = useState20(0);
    const stepsEndRef = useRef13(null);
    const inputRef = useRef13(null);
    useEffect16(() => {
      const handler = (msg) => {
        if (msg.agent_id !== agent_id)
          return;
        switch (msg.type) {
          case "agent:started":
            setIsRunning(true);
            setSteps([]);
            setStreamingText("");
            setFinalResponse("");
            setError(null);
            break;
          case "agent:step":
            if (msg.status === "done") {
              setSteps((prev) => {
                const existing = prev.findIndex((s) => s.id === msg.step.id);
                if (existing >= 0) {
                  const updated = [...prev];
                  updated[existing] = { ...msg.step, status: "done" };
                  return updated;
                }
                return [...prev, { ...msg.step, status: "done" }];
              });
              setStreamingText("");
            } else {
              setSteps((prev) => {
                const existing = prev.findIndex((s) => s.id === msg.step.id);
                if (existing >= 0)
                  return prev;
                return [...prev, { ...msg.step, status: "running" }];
              });
            }
            break;
          case "agent:delta":
            setStreamingText((prev) => prev + msg.delta);
            break;
          case "agent:done":
            setIsRunning(false);
            setTotalCost(msg.total_cost || 0);
            setTotalTokens(msg.total_tokens || 0);
            setIterations(msg.iterations || 0);
            if (msg.steps && msg.steps.length > 0) {
              const lastResponse = [...msg.steps].reverse().find((s) => s.type === "response");
              if (lastResponse)
                setFinalResponse(lastResponse.content);
            }
            break;
          case "agent:error":
            setIsRunning(false);
            setError(msg.error);
            break;
          case "agent:budget_update":
            if (msg.summary) {
              setTotalCost(msg.summary.total_cost || 0);
              setTotalTokens(msg.summary.total_tokens || 0);
            }
            break;
        }
      };
      cacaoWs.addListener(handler);
      return () => cacaoWs.removeListener(handler);
    }, [agent_id]);
    useEffect16(() => {
      if (stepsEndRef.current) {
        stepsEndRef.current.scrollIntoView({ behavior: "smooth" });
      }
    }, [steps, streamingText]);
    const handleSend = useCallback11(() => {
      const text2 = inputText.trim();
      if (!text2 || isRunning)
        return;
      cacaoWs.send({
        type: "agent:run",
        agent_id,
        text: text2
      });
      setInputText("");
      if (inputRef.current)
        inputRef.current.focus();
    }, [inputText, isRunning, agent_id]);
    const handleKeyDown = useCallback11(
      (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleSend();
        }
      },
      [handleSend]
    );
    const renderStepIcon = (step) => {
      switch (step.type) {
        case "think":
          return "\u{1F9E0}";
        case "tool_call":
          return "\u2699\uFE0F";
        case "response":
          return "\u2705";
        case "error":
          return "\u274C";
        default:
          return "\u25CF";
      }
    };
    const renderStep = (step, index) => {
      const isActive = step.status === "running";
      return h54(
        "div",
        {
          className: `c-agent-step c-agent-step--${step.type} ${isActive ? "c-agent-step--active" : ""}`,
          key: step.id || index
        },
        [
          h54("div", { className: "c-agent-step__header", key: "hdr" }, [
            h54("span", { className: "c-agent-step__icon", key: "icon" }, renderStepIcon(step)),
            h54(
              "span",
              { className: "c-agent-step__type", key: "type" },
              step.type === "tool_call" ? `Tool: ${step.tool_name || "unknown"}` : step.type
            ),
            step.duration > 0 && h54("span", { className: "c-agent-step__duration", key: "dur" }, `${step.duration.toFixed(1)}s`),
            show_cost && step.cost > 0 && h54("span", { className: "c-agent-step__cost", key: "cost" }, `$${step.cost.toFixed(4)}`),
            isActive && h54("span", { className: "c-agent-step__spinner", key: "spin" })
          ]),
          // Tool args
          step.tool_args && h54(
            "div",
            { className: "c-agent-step__args", key: "args" },
            h54("pre", null, JSON.stringify(step.tool_args, null, 2))
          ),
          // Tool result
          step.tool_result && h54("div", { className: "c-agent-step__result", key: "result" }, [
            h54("span", { className: "c-agent-step__result-label", key: "lbl" }, "Result:"),
            h54("pre", { key: "pre" }, step.tool_result)
          ]),
          // Think/response content
          step.type !== "tool_call" && step.content && step.status === "done" && h54(
            "div",
            { className: "c-agent-step__content", key: "content" },
            step.content
          )
        ]
      );
    };
    return h54("div", { className: "c-agent", style: { height } }, [
      // Header
      h54("div", { className: "c-agent__header", key: "header" }, [
        h54(
          "span",
          { className: "c-agent__title", key: "title" },
          title || "Agent"
        ),
        h54("div", { className: "c-agent__meta", key: "meta" }, [
          h54("span", { className: "c-agent__badge", key: "model" }, `${provider}/${model}`),
          has_tools && h54("span", { className: "c-agent__badge c-agent__badge--tools", key: "tools" }, "Tools")
        ])
      ]),
      // Main content area
      h54("div", { className: "c-agent__body", key: "body" }, [
        // Steps panel
        show_steps && (steps.length > 0 || isRunning) && h54("div", { className: "c-agent__steps", key: "steps" }, [
          h54("div", { className: "c-agent__steps-header", key: "shdr" }, "ReAct Trace"),
          h54("div", { className: "c-agent__steps-list", key: "slist" }, [
            ...steps.map(renderStep),
            // Streaming text for current think step
            isRunning && streamingText && h54(
              "div",
              { className: "c-agent-step c-agent-step--think c-agent-step--active", key: "streaming" },
              [
                h54("div", { className: "c-agent-step__content", key: "content" }, streamingText)
              ]
            ),
            h54("div", { ref: stepsEndRef, key: "anchor" })
          ])
        ]),
        // Final response
        finalResponse && !isRunning && h54("div", { className: "c-agent__response", key: "response" }, [
          h54("div", { className: "c-agent__response-label", key: "lbl" }, "Response"),
          h54("div", { className: "c-agent__response-content", key: "content" }, finalResponse)
        ]),
        // Error
        error && h54("div", { className: "c-agent__error", key: "error" }, error),
        // Cost summary
        show_cost && (totalCost > 0 || totalTokens > 0) && !isRunning && h54("div", { className: "c-agent__cost-summary", key: "cost" }, [
          totalCost > 0 && h54("span", { key: "cost" }, `Cost: $${totalCost.toFixed(4)}`),
          totalTokens > 0 && h54("span", { key: "tokens" }, `Tokens: ${totalTokens.toLocaleString()}`),
          iterations > 0 && h54("span", { key: "iter" }, `Iterations: ${iterations}`)
        ]),
        // Empty state
        !isRunning && steps.length === 0 && !finalResponse && !error && h54("div", { className: "c-agent__empty", key: "empty" }, "Send a message to start the agent.")
      ]),
      // Input area
      h54("div", { className: "c-agent__input-area", key: "input" }, [
        h54("textarea", {
          ref: inputRef,
          className: "c-agent__input",
          placeholder,
          value: inputText,
          rows: 1,
          disabled: isRunning,
          onChange: (e) => setInputText(e.target.value),
          onKeyDown: handleKeyDown,
          key: "textarea"
        }),
        h54(
          "button",
          {
            className: "c-agent__send",
            onClick: handleSend,
            disabled: !inputText.trim() || isRunning,
            title: "Run agent",
            key: "send"
          },
          isRunning ? h54("span", { className: "c-agent__send-spinner" }) : h54(
            "svg",
            {
              width: 18,
              height: 18,
              viewBox: "0 0 24 24",
              fill: "none",
              stroke: "currentColor",
              strokeWidth: 2,
              strokeLinecap: "round",
              strokeLinejoin: "round"
            },
            [
              h54("line", { x1: 22, y1: 2, x2: 11, y2: 13, key: "l1" }),
              h54("polygon", { points: "22 2 15 22 11 13 2 9 22 2", key: "p1" })
            ]
          )
        )
      ])
    ]);
  }

  // src/components/form/BudgetGauge.js
  var { createElement: h55, useState: useState21, useEffect: useEffect17, useCallback: useCallback12 } = React;
  function BudgetGauge({ props }) {
    const {
      max_cost = null,
      max_tokens = null,
      warn_threshold = 0.8,
      title = "Budget",
      show_breakdown = true,
      compact = false
    } = props;
    const [summary, setSummary] = useState21(null);
    const [pollInterval, setPollInterval] = useState21(null);
    const fetchBudget = useCallback12(() => {
      cacaoWs.send({ type: "budget:get" });
    }, []);
    useEffect17(() => {
      const handler = (msg) => {
        if (msg.type === "budget:summary") {
          setSummary(msg.summary);
        }
        if (msg.type === "agent:budget_update" && msg.summary) {
          setSummary(msg.summary);
        }
        if (msg.type === "cost:summary" && msg.summary) {
          setSummary(msg.summary);
        }
      };
      cacaoWs.addListener(handler);
      fetchBudget();
      const interval = setInterval(fetchBudget, 5e3);
      setPollInterval(interval);
      return () => {
        cacaoWs.removeListener(handler);
        clearInterval(interval);
      };
    }, [fetchBudget]);
    const totalCost = summary?.total_cost || 0;
    const totalTokens = summary?.total_tokens || 0;
    const callCount = summary?.call_count || 0;
    const costPercent = max_cost ? Math.min(totalCost / max_cost * 100, 100) : 0;
    const tokenPercent = max_tokens ? Math.min(totalTokens / max_tokens * 100, 100) : 0;
    const getGaugeColor = (percent) => {
      if (percent >= 100)
        return "var(--danger)";
      if (percent >= warn_threshold * 100)
        return "#ffb74d";
      return "var(--success, #81c784)";
    };
    const renderGauge = (label, current, max, unit, percent) => {
      const color = getGaugeColor(percent);
      const displayCurrent = unit === "$" ? `$${current.toFixed(4)}` : current.toLocaleString();
      const displayMax = unit === "$" ? `$${max.toFixed(2)}` : max.toLocaleString();
      if (compact) {
        return h55("div", { className: "c-budget-gauge__compact-row", key: label }, [
          h55("span", { className: "c-budget-gauge__compact-label", key: "lbl" }, label),
          h55("div", { className: "c-budget-gauge__compact-bar-wrap", key: "bar" }, [
            h55("div", {
              className: "c-budget-gauge__compact-bar",
              style: { width: `${percent}%`, background: color },
              key: "fill"
            })
          ]),
          h55(
            "span",
            { className: "c-budget-gauge__compact-value", style: { color }, key: "val" },
            `${displayCurrent} / ${displayMax}`
          )
        ]);
      }
      return h55("div", { className: "c-budget-gauge__gauge", key: label }, [
        h55("div", { className: "c-budget-gauge__gauge-header", key: "hdr" }, [
          h55("span", { className: "c-budget-gauge__gauge-label", key: "lbl" }, label),
          h55(
            "span",
            { className: "c-budget-gauge__gauge-value", style: { color }, key: "val" },
            `${displayCurrent} / ${displayMax}`
          )
        ]),
        h55("div", { className: "c-budget-gauge__bar-track", key: "track" }, [
          h55("div", {
            className: "c-budget-gauge__bar-fill",
            style: { width: `${percent}%`, background: color },
            key: "fill"
          }),
          // Warn threshold marker
          h55("div", {
            className: "c-budget-gauge__threshold-mark",
            style: { left: `${warn_threshold * 100}%` },
            key: "mark"
          })
        ]),
        h55(
          "div",
          { className: "c-budget-gauge__gauge-percent", style: { color }, key: "pct" },
          `${percent.toFixed(1)}%`
        )
      ]);
    };
    const costOverBudget = max_cost && totalCost >= max_cost;
    const tokenOverBudget = max_tokens && totalTokens >= max_tokens;
    const costWarning = max_cost && totalCost >= max_cost * warn_threshold && !costOverBudget;
    const tokenWarning = max_tokens && totalTokens >= max_tokens * warn_threshold && !tokenOverBudget;
    if (compact) {
      return h55("div", { className: "c-budget-gauge c-budget-gauge--compact" }, [
        title && h55("span", { className: "c-budget-gauge__compact-title", key: "title" }, title),
        max_cost !== null && renderGauge("Cost", totalCost, max_cost, "$", costPercent),
        max_tokens !== null && renderGauge("Tokens", totalTokens, max_tokens, "tok", tokenPercent),
        max_cost === null && max_tokens === null && h55(
          "span",
          { className: "c-budget-gauge__compact-usage", key: "usage" },
          `$${totalCost.toFixed(4)} \xB7 ${totalTokens.toLocaleString()} tokens \xB7 ${callCount} calls`
        )
      ]);
    }
    return h55("div", { className: "c-budget-gauge" }, [
      // Header
      h55("div", { className: "c-budget-gauge__header", key: "header" }, [
        h55("span", { className: "c-budget-gauge__title", key: "title" }, title),
        h55("span", { className: "c-budget-gauge__calls", key: "calls" }, `${callCount} calls`)
      ]),
      // Alerts
      (costOverBudget || tokenOverBudget) && h55(
        "div",
        { className: "c-budget-gauge__alert c-budget-gauge__alert--danger", key: "over" },
        "Budget exceeded! Requests may be blocked."
      ),
      (costWarning || tokenWarning) && h55(
        "div",
        { className: "c-budget-gauge__alert c-budget-gauge__alert--warn", key: "warn" },
        `Approaching budget limit (${(warn_threshold * 100).toFixed(0)}% threshold).`
      ),
      // Gauges
      h55("div", { className: "c-budget-gauge__gauges", key: "gauges" }, [
        max_cost !== null && renderGauge("Cost", totalCost, max_cost, "$", costPercent),
        max_tokens !== null && renderGauge("Tokens", totalTokens, max_tokens, "tok", tokenPercent)
      ]),
      // Usage summary when no limits set
      max_cost === null && max_tokens === null && h55("div", { className: "c-budget-gauge__usage", key: "usage" }, [
        h55("div", { className: "c-budget-gauge__usage-item", key: "cost" }, [
          h55("span", { className: "c-budget-gauge__usage-label", key: "lbl" }, "Total Cost"),
          h55("span", { className: "c-budget-gauge__usage-value", key: "val" }, `$${totalCost.toFixed(4)}`)
        ]),
        h55("div", { className: "c-budget-gauge__usage-item", key: "tokens" }, [
          h55("span", { className: "c-budget-gauge__usage-label", key: "lbl" }, "Total Tokens"),
          h55("span", { className: "c-budget-gauge__usage-value", key: "val" }, totalTokens.toLocaleString())
        ])
      ]),
      // Breakdown table
      show_breakdown && summary?.by_model && summary.by_model.length > 0 && h55("div", { className: "c-budget-gauge__breakdown", key: "breakdown" }, [
        h55("div", { className: "c-budget-gauge__breakdown-title", key: "title" }, "Per-Model Breakdown"),
        h55("table", { className: "c-budget-gauge__table", key: "table" }, [
          h55(
            "thead",
            { key: "thead" },
            h55("tr", null, [
              h55("th", { key: "model" }, "Model"),
              h55("th", { key: "calls" }, "Calls"),
              h55("th", { key: "tokens" }, "Tokens"),
              h55("th", { key: "cost" }, "Cost")
            ])
          ),
          h55(
            "tbody",
            { key: "tbody" },
            summary.by_model.map(
              (entry, i) => h55("tr", { key: i }, [
                h55("td", { key: "model" }, `${entry.provider}/${entry.model}`),
                h55("td", { key: "calls" }, entry.calls),
                h55("td", { key: "tokens" }, entry.total_tokens.toLocaleString()),
                h55("td", { key: "cost" }, `$${entry.cost.toFixed(4)}`)
              ])
            )
          )
        ])
      ])
    ]);
  }

  // src/components/form/Button.js
  var { createElement: h56 } = React;
  function Button({ props, setActiveTab }) {
    const {
      label,
      variant = "primary",
      size = "md",
      disabled = false,
      loading = false,
      icon,
      on_click
    } = props;
    const handleClick = () => {
      if (disabled || loading)
        return;
      const eventName = on_click?.__event__ || on_click;
      if (eventName) {
        if (typeof eventName === "string" && eventName.startsWith("nav:")) {
          const tabKey = eventName.slice(4);
          if (setActiveTab) {
            setActiveTab(tabKey);
          }
          return;
        }
        if (typeof eventName === "string" && eventName.startsWith("link:")) {
          const url = eventName.slice(5);
          window.open(url, "_blank", "noopener,noreferrer");
          return;
        }
        if (typeof eventName === "string" && eventName.startsWith("theme:")) {
          const theme = eventName.slice(6);
          if (window.Cacao?.setTheme) {
            window.Cacao.setTheme(theme);
          }
          return;
        }
        cacaoWs.sendEvent(eventName, {});
      }
    };
    const className = `btn btn-${variant} btn-${size}${disabled ? " disabled" : ""}${loading ? " loading" : ""}`;
    return h56("button", {
      className,
      onClick: handleClick,
      disabled: disabled || loading,
      type: "button"
    }, [
      icon && h56("span", { className: "btn-icon", key: "icon" }, icon),
      h56("span", { key: "label" }, label)
    ]);
  }

  // src/components/form/ChainBuilder.js
  var { createElement: h57, useState: useState22, useEffect: useEffect18, useCallback: useCallback13, useRef: useRef14 } = React;
  var STEP_TYPES = [
    { value: "transformer", label: "Transformer", icon: "\u2699" },
    { value: "skill", label: "Skill", icon: "\u{1F527}" },
    { value: "branch", label: "Branch", icon: "\u2442" },
    { value: "parallel", label: "Parallel", icon: "\u2AFD" }
  ];
  function StepCard({ step, index, onRemove, onUpdate, onMoveUp, onMoveDown, isFirst, isLast }) {
    const [expanded, setExpanded] = useState22(false);
    const typeInfo = STEP_TYPES.find((t) => t.value === step.type) || STEP_TYPES[0];
    return h57(
      "div",
      {
        className: `cacao-chain-step cacao-chain-step-${step.type}`,
        draggable: true,
        onDragStart: (e) => {
          e.dataTransfer.setData("text/plain", String(index));
          e.dataTransfer.effectAllowed = "move";
        }
      },
      // Step header
      h57(
        "div",
        { className: "cacao-chain-step-header" },
        h57("span", { className: "cacao-chain-step-icon" }, typeInfo.icon),
        h57("span", { className: "cacao-chain-step-type" }, typeInfo.label),
        h57("span", { className: "cacao-chain-step-name" }, step.name || "(unnamed)"),
        h57(
          "div",
          { className: "cacao-chain-step-actions" },
          !isFirst && h57("button", {
            className: "cacao-chain-step-btn",
            onClick: () => onMoveUp(index),
            title: "Move up"
          }, "\u2191"),
          !isLast && h57("button", {
            className: "cacao-chain-step-btn",
            onClick: () => onMoveDown(index),
            title: "Move down"
          }, "\u2193"),
          h57("button", {
            className: "cacao-chain-step-btn",
            onClick: () => setExpanded(!expanded),
            title: expanded ? "Collapse" : "Expand"
          }, expanded ? "\u2212" : "+"),
          h57("button", {
            className: "cacao-chain-step-btn cacao-chain-step-btn-remove",
            onClick: () => onRemove(index),
            title: "Remove"
          }, "\xD7")
        )
      ),
      // Step details (expanded)
      expanded && h57(
        "div",
        { className: "cacao-chain-step-body" },
        h57(
          "div",
          { className: "cacao-chain-step-field" },
          h57("label", null, "Name"),
          h57("input", {
            className: "cacao-input",
            value: step.name || "",
            placeholder: step.type === "transformer" ? "e.g., strip, lowercase" : "Skill or step name",
            onChange: (e) => onUpdate(index, { ...step, name: e.target.value })
          })
        ),
        // Transformer params
        step.type === "transformer" && h57(
          "div",
          { className: "cacao-chain-step-field" },
          h57("label", null, "Parameters (JSON)"),
          h57("textarea", {
            className: "cacao-input",
            rows: 2,
            value: step.params ? JSON.stringify(step.params) : "",
            placeholder: '{"key": "value"}',
            onChange: (e) => {
              try {
                const params = e.target.value ? JSON.parse(e.target.value) : null;
                onUpdate(index, { ...step, params });
              } catch {
              }
            }
          })
        ),
        // Branch condition
        step.type === "branch" && h57(
          "div",
          { className: "cacao-chain-step-field" },
          h57("label", null, 'Condition (Python expression using "v")'),
          h57("input", {
            className: "cacao-input",
            value: step.condition || "",
            placeholder: 'e.g., "@" in v',
            onChange: (e) => onUpdate(index, { ...step, condition: e.target.value })
          })
        ),
        // Parallel merge strategy
        step.type === "parallel" && h57(
          "div",
          { className: "cacao-chain-step-field" },
          h57("label", null, "Merge strategy"),
          h57(
            "select",
            {
              className: "cacao-input",
              value: step.merge || "dict",
              onChange: (e) => onUpdate(index, { ...step, merge: e.target.value })
            },
            h57("option", { value: "dict" }, "Dict (key \u2192 result)"),
            h57("option", { value: "list" }, "List"),
            h57("option", { value: "first" }, "First success")
          )
        )
      )
    );
  }
  function ChainBuilder({ props }) {
    const {
      title = "Chain Builder",
      initial_steps = [],
      show_output = true,
      height = "600px"
    } = props;
    const [steps, setSteps] = useState22(initial_steps.length > 0 ? initial_steps : []);
    const [inputValue, setInputValue] = useState22("");
    const [output, setOutput] = useState22(null);
    const [stepResults, setStepResults] = useState22([]);
    const [loading, setLoading] = useState22(false);
    const [error, setError] = useState22(null);
    const [addType, setAddType] = useState22("transformer");
    const chainId = useRef14(`chain_${Date.now()}_${Math.random().toString(36).slice(2)}`);
    const dropRef = useRef14(null);
    const addStep = useCallback13(() => {
      setSteps((prev) => [...prev, { type: addType, name: "", params: null }]);
    }, [addType]);
    const removeStep = useCallback13((index) => {
      setSteps((prev) => prev.filter((_2, i) => i !== index));
    }, []);
    const updateStep = useCallback13((index, newStep) => {
      setSteps((prev) => prev.map((s, i) => i === index ? newStep : s));
    }, []);
    const moveStep = useCallback13((from, to) => {
      setSteps((prev) => {
        const arr = [...prev];
        const [item] = arr.splice(from, 1);
        arr.splice(to, 0, item);
        return arr;
      });
    }, []);
    const handleDrop = useCallback13((e) => {
      e.preventDefault();
      const fromIndex = parseInt(e.dataTransfer.getData("text/plain"), 10);
      if (isNaN(fromIndex))
        return;
      const rect = dropRef.current.getBoundingClientRect();
      const y2 = e.clientY - rect.top;
      const stepHeight = rect.height / (steps.length || 1);
      let toIndex = Math.round(y2 / stepHeight);
      toIndex = Math.max(0, Math.min(toIndex, steps.length - 1));
      if (fromIndex !== toIndex)
        moveStep(fromIndex, toIndex);
    }, [steps.length, moveStep]);
    const runChain = useCallback13(() => {
      if (steps.length === 0 || loading)
        return;
      setLoading(true);
      setError(null);
      setOutput(null);
      setStepResults([]);
      const id = `chain_${Date.now()}_${Math.random().toString(36).slice(2)}`;
      chainId.current = id;
      const handler = (msg) => {
        if (msg.id !== id)
          return;
        switch (msg.type) {
          case "chain:step_result":
            setStepResults((prev) => [...prev, {
              index: msg.step_index,
              name: msg.step_name,
              value: msg.value,
              success: msg.success,
              error: msg.error
            }]);
            break;
          case "chain:result":
            setOutput(msg.value);
            setLoading(false);
            cacaoWs.removeListener(handler);
            break;
          case "chain:error":
            setError(msg.error);
            setLoading(false);
            cacaoWs.removeListener(handler);
            break;
        }
      };
      cacaoWs.addListener(handler);
      cacaoWs.send({
        type: "chain:run",
        id,
        steps: steps.filter((s) => s.name),
        // Only named steps
        input: inputValue
      });
    }, [steps, inputValue, loading]);
    return h57(
      "div",
      { className: "cacao-chain-builder", style: { height } },
      // Header
      h57(
        "div",
        { className: "cacao-chain-builder-header" },
        h57("h3", { className: "cacao-chain-builder-title" }, title),
        h57("span", { className: "cacao-badge" }, `${steps.length} steps`)
      ),
      h57(
        "div",
        { className: "cacao-chain-builder-content" },
        // Left: chain editor
        h57(
          "div",
          { className: "cacao-chain-builder-editor" },
          // Add step controls
          h57(
            "div",
            { className: "cacao-chain-builder-add" },
            h57(
              "select",
              {
                className: "cacao-input",
                value: addType,
                onChange: (e) => setAddType(e.target.value)
              },
              ...STEP_TYPES.map(
                (t) => h57("option", { key: t.value, value: t.value }, `${t.icon} ${t.label}`)
              )
            ),
            h57("button", {
              className: "cacao-btn cacao-btn-secondary",
              onClick: addStep
            }, "+ Add Step")
          ),
          // Steps list (droppable)
          h57(
            "div",
            {
              ref: dropRef,
              className: "cacao-chain-builder-steps",
              onDragOver: (e) => e.preventDefault(),
              onDrop: handleDrop
            },
            steps.length === 0 ? h57(
              "div",
              { className: "cacao-chain-builder-empty" },
              "Add steps to build your chain"
            ) : steps.map(
              (step, i) => h57(
                "div",
                { key: i },
                i > 0 && h57("div", { className: "cacao-chain-builder-connector" }, "\u2193"),
                h57(StepCard, {
                  step,
                  index: i,
                  onRemove: removeStep,
                  onUpdate: updateStep,
                  onMoveUp: (idx) => moveStep(idx, idx - 1),
                  onMoveDown: (idx) => moveStep(idx, idx + 1),
                  isFirst: i === 0,
                  isLast: i === steps.length - 1
                })
              )
            )
          )
        ),
        // Right: input/output
        show_output && h57(
          "div",
          { className: "cacao-chain-builder-io" },
          // Input
          h57(
            "div",
            { className: "cacao-chain-builder-input" },
            h57("label", { className: "cacao-chain-builder-label" }, "Input"),
            h57("textarea", {
              className: "cacao-input",
              rows: 4,
              value: inputValue,
              placeholder: "Enter input value...",
              onChange: (e) => setInputValue(e.target.value)
            }),
            h57("button", {
              className: "cacao-btn cacao-btn-primary",
              onClick: runChain,
              disabled: loading || steps.length === 0
            }, loading ? "Running..." : "Run Chain")
          ),
          // Step results
          stepResults.length > 0 && h57(
            "div",
            { className: "cacao-chain-builder-step-results" },
            h57("label", { className: "cacao-chain-builder-label" }, "Step Results"),
            ...stepResults.map(
              (r, i) => h57(
                "div",
                {
                  key: i,
                  className: `cacao-chain-builder-step-result ${r.success ? "" : "cacao-chain-builder-step-error"}`
                },
                h57("span", { className: "cacao-chain-builder-step-name" }, r.name || `Step ${r.index}`),
                h57(
                  "span",
                  { className: "cacao-chain-builder-step-value" },
                  r.success ? typeof r.value === "object" ? JSON.stringify(r.value) : String(r.value ?? "") : r.error
                )
              )
            )
          ),
          // Final output
          h57(
            "div",
            { className: "cacao-chain-builder-output" },
            h57("label", { className: "cacao-chain-builder-label" }, "Output"),
            error && h57("div", { className: "cacao-alert cacao-alert-error" }, error),
            output !== null && h57(
              "pre",
              { className: "cacao-chain-builder-result" },
              typeof output === "object" ? JSON.stringify(output, null, 2) : String(output)
            ),
            output === null && !error && !loading && h57(
              "div",
              { className: "cacao-chain-builder-placeholder" },
              "Run the chain to see output"
            )
          )
        )
      )
    );
  }

  // src/components/form/Chat.js
  var { createElement: h58, useState: useState23, useEffect: useEffect19, useRef: useRef15, useCallback: useCallback14 } = React;
  function Chat({ props }) {
    const {
      signal,
      on_send,
      on_clear,
      placeholder = "Type a message...",
      title,
      height = "500px",
      show_clear = false,
      persist = false,
      llm_enabled = false
    } = props;
    const [messages, setMessages] = useState23([]);
    const [inputText, setInputText] = useState23("");
    const [streamingText, setStreamingText] = useState23("");
    const [isStreaming, setIsStreaming] = useState23(false);
    const messagesEndRef = useRef15(null);
    const inputRef = useRef15(null);
    const signalName = signal?.__signal__;
    const storageKey = persist && signalName ? `cacao-chat-${signalName}` : null;
    useEffect19(() => {
      if (storageKey) {
        try {
          const saved = localStorage.getItem(storageKey);
          if (saved) {
            const parsed = JSON.parse(saved);
            if (Array.isArray(parsed) && parsed.length > 0) {
              setMessages(parsed);
            }
          }
        } catch {
        }
      }
    }, [storageKey]);
    useEffect19(() => {
      if (signalName) {
        const unsubscribe = cacaoWs.subscribe((signals) => {
          if (signals[signalName] !== void 0) {
            const newMsgs = signals[signalName];
            setMessages(newMsgs);
            if (storageKey && Array.isArray(newMsgs)) {
              try {
                localStorage.setItem(storageKey, JSON.stringify(newMsgs));
              } catch {
              }
            }
          }
        });
        const initial = cacaoWs.getSignal(signalName);
        if (initial !== void 0 && Array.isArray(initial) && initial.length > 0) {
          setMessages(initial);
        }
        return unsubscribe;
      }
    }, [signalName, storageKey]);
    useEffect19(() => {
      if (!signalName)
        return;
      const unsubscribe = cacaoWs.subscribeChatStream((msg) => {
        if (msg.signal !== signalName)
          return;
        if (msg.type === "chat_delta") {
          setIsStreaming(true);
          setStreamingText((prev) => prev + msg.delta);
        } else if (msg.type === "chat_done") {
          setStreamingText("");
          setIsStreaming(false);
        }
      });
      return unsubscribe;
    }, [signalName]);
    useEffect19(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
      }
    }, [messages, streamingText]);
    const handleSend = useCallback14(() => {
      const text2 = inputText.trim();
      if (!text2 || isStreaming)
        return;
      if (llm_enabled && signalName) {
        cacaoWs.sendChatMessage(signalName, text2);
      } else {
        const eventName = on_send?.__event__ || on_send;
        if (eventName) {
          cacaoWs.sendEvent(eventName, { text: text2 });
        }
      }
      setInputText("");
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, [inputText, isStreaming, on_send, llm_enabled, signalName]);
    const handleKeyDown = useCallback14((e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    }, [handleSend]);
    const handleClear = useCallback14(() => {
      const eventName = on_clear?.__event__ || on_clear;
      if (eventName) {
        cacaoWs.sendEvent(eventName, {});
      }
      if (storageKey) {
        try {
          localStorage.removeItem(storageKey);
        } catch {
        }
      }
    }, [on_clear, storageKey]);
    const renderToolCalls = (toolCalls) => {
      if (!toolCalls || !toolCalls.length)
        return null;
      return toolCalls.map((tc, i) => {
        let args = tc.arguments;
        try {
          args = JSON.stringify(JSON.parse(tc.arguments), null, 2);
        } catch {
        }
        return h58("div", { className: "c-chat-tool-call", key: `tc-${i}` }, [
          h58("div", { className: "c-chat-tool-call__header", key: "hdr" }, [
            h58("span", { className: "c-chat-tool-call__icon", key: "icon" }, "\u2699"),
            h58("span", { className: "c-chat-tool-call__name", key: "name" }, tc.name)
          ]),
          h58("pre", { className: "c-chat-tool-call__args", key: "args" }, args)
        ]);
      });
    };
    const renderMessage = (msg, index) => {
      const isUser = msg.role === "user";
      const isError = msg.role === "error";
      const isTool = msg.role === "tool";
      if (isTool) {
        return h58("div", {
          className: "c-chat-message c-chat-message--tool",
          key: index
        }, [
          h58(
            "div",
            { className: "c-chat-message__role", key: "role" },
            `\u2699 ${msg.name || "Tool"}`
          ),
          h58("div", { className: "c-chat-message__content", key: "content" }, msg.content)
        ]);
      }
      return h58("div", {
        className: `c-chat-message c-chat-message--${isError ? "error" : isUser ? "user" : "assistant"}`,
        key: index
      }, [
        h58(
          "div",
          { className: "c-chat-message__role", key: "role" },
          isError ? "Error" : isUser ? "You" : "Assistant"
        ),
        // Tool calls (shown before text content for assistant messages)
        msg.tool_calls && renderToolCalls(msg.tool_calls),
        h58("div", { className: "c-chat-message__content", key: "content" }, msg.content)
      ]);
    };
    const allMessages = [...messages];
    return h58("div", { className: "c-chat", style: { height } }, [
      // Header
      title && h58("div", { className: "c-chat__header", key: "header" }, [
        h58("span", { className: "c-chat__title", key: "title" }, title),
        show_clear && h58("button", {
          className: "c-chat__clear",
          onClick: handleClear,
          title: "Clear conversation",
          key: "clear"
        }, "\xD7")
      ]),
      // Messages area
      h58("div", { className: "c-chat__messages", key: "messages" }, [
        // Empty state
        allMessages.length === 0 && !isStreaming && h58("div", {
          className: "c-chat__empty",
          key: "empty"
        }, "Start a conversation..."),
        // Message bubbles
        ...allMessages.map(renderMessage),
        // Streaming message (in progress)
        isStreaming && streamingText && h58("div", {
          className: "c-chat-message c-chat-message--assistant c-chat-message--streaming",
          key: "streaming"
        }, [
          h58("div", { className: "c-chat-message__role", key: "role" }, "Assistant"),
          h58("div", { className: "c-chat-message__content", key: "content" }, streamingText)
        ]),
        // Streaming indicator (waiting for first chunk)
        isStreaming && !streamingText && h58("div", {
          className: "c-chat-message c-chat-message--assistant c-chat-message--streaming",
          key: "thinking"
        }, [
          h58("div", { className: "c-chat-message__role", key: "role" }, "Assistant"),
          h58(
            "div",
            { className: "c-chat-message__content c-chat-message__typing", key: "content" },
            h58("span", { className: "c-chat__dots" }, [
              h58("span", { key: "d1" }, "."),
              h58("span", { key: "d2" }, "."),
              h58("span", { key: "d3" }, ".")
            ])
          )
        ]),
        // Scroll anchor
        h58("div", { ref: messagesEndRef, key: "anchor" })
      ]),
      // Input area
      h58("div", { className: "c-chat__input-area", key: "input" }, [
        h58("textarea", {
          ref: inputRef,
          className: "c-chat__input",
          placeholder,
          value: inputText,
          rows: 1,
          disabled: isStreaming,
          onChange: (e) => setInputText(e.target.value),
          onKeyDown: handleKeyDown,
          key: "textarea"
        }),
        h58("button", {
          className: "c-chat__send",
          onClick: handleSend,
          disabled: !inputText.trim() || isStreaming,
          title: "Send message",
          key: "send"
        }, h58("svg", {
          width: 18,
          height: 18,
          viewBox: "0 0 24 24",
          fill: "none",
          stroke: "currentColor",
          strokeWidth: 2,
          strokeLinecap: "round",
          strokeLinejoin: "round"
        }, [
          h58("line", { x1: 22, y1: 2, x2: 11, y2: 13, key: "l1" }),
          h58("polygon", { points: "22 2 15 22 11 13 2 9 22 2", key: "p1" })
        ]))
      ])
    ]);
  }

  // src/components/form/Checkbox.js
  var { createElement: h59 } = React;
  function Checkbox({ props }) {
    return h59("div", { className: "checkbox-container" }, [
      h59("input", { type: "checkbox", className: "checkbox", key: "input" }),
      h59("div", { key: "text" }, [
        h59("div", { className: "checkbox-label", key: "label" }, props.label),
        props.description && h59("div", { className: "checkbox-desc", key: "desc" }, props.description)
      ])
    ]);
  }

  // src/components/form/Compare.js
  init_static_runtime();
  var { createElement: h60, useState: useState24, useEffect: useEffect20, useCallback: useCallback15 } = React;
  function Compare({ props }) {
    const {
      functions = [],
      inputs = [],
      param_names = [],
      submit_label = "Compare"
    } = props;
    const [values, setValues] = useState24(() => {
      const initial = {};
      inputs.forEach((inp) => {
        initial[inp.param_name] = inp.default != null ? inp.default : "";
      });
      return initial;
    });
    const [outputs, setOutputs] = useState24({});
    const [errors, setErrors] = useState24({});
    const [loading, setLoading] = useState24({});
    useEffect20(() => {
      if (!cacaoWs.ws)
        return;
      const handler = (event) => {
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }
        const fnIndex = functions.findIndex((fn) => fn.id === msg.id);
        if (fnIndex === -1)
          return;
        if (msg.type === "interface:result") {
          setOutputs((prev) => ({ ...prev, [fnIndex]: msg.output }));
          setLoading((prev) => ({ ...prev, [fnIndex]: false }));
        } else if (msg.type === "interface:error") {
          setErrors((prev) => ({ ...prev, [fnIndex]: msg }));
          setLoading((prev) => ({ ...prev, [fnIndex]: false }));
        }
      };
      cacaoWs.ws.addEventListener("message", handler);
      return () => cacaoWs.ws?.removeEventListener("message", handler);
    }, [functions]);
    const updateValue = useCallback15((paramName, val) => {
      setValues((prev) => ({ ...prev, [paramName]: val }));
    }, []);
    const handleSubmit = useCallback15(() => {
      setOutputs({});
      setErrors({});
      const newLoading = {};
      functions.forEach((_2, i) => {
        newLoading[i] = true;
      });
      setLoading(newLoading);
      functions.forEach((fn) => {
        if (cacaoWs.ws && cacaoWs.connected) {
          cacaoWs.ws.send(JSON.stringify({
            type: "interface:submit",
            id: fn.id,
            inputs: values
          }));
        }
      });
    }, [values, functions]);
    return h60("div", { className: "c-compare" }, [
      // Shared inputs panel
      h60("div", { className: "c-compare__inputs", key: "inputs" }, [
        ...inputs.map(
          (inp) => h60(CompareInputField, {
            key: inp.param_name,
            spec: inp,
            value: values[inp.param_name],
            onChange: (val) => updateValue(inp.param_name, val)
          })
        ),
        !isStaticMode() && h60("button", {
          className: "btn btn-primary c-compare__submit",
          onClick: handleSubmit,
          disabled: Object.values(loading).some(Boolean),
          key: "submit"
        }, Object.values(loading).some(Boolean) ? "Running..." : submit_label)
      ]),
      // Side-by-side output panels
      h60(
        "div",
        { className: "c-compare__outputs", key: "outputs" },
        functions.map(
          (fn, i) => h60("div", { className: "c-compare__output", key: i }, [
            h60("div", { className: "c-compare__output-title", key: "title" }, fn.title),
            loading[i] ? h60(
              "div",
              { className: "c-iface__loading", key: "loading" },
              h60("span", { className: "c-iface__spinner c-iface__spinner--lg" })
            ) : outputs[i] ? h60(CompareOutputDisplay, { output: outputs[i], key: "result" }) : errors[i] ? h60("div", { className: "c-iface__error", key: "error" }, [
              h60("strong", { key: "type" }, errors[i].error),
              h60("span", { key: "msg" }, `: ${errors[i].message}`)
            ]) : h60("div", { className: "c-iface__empty", key: "empty" }, "Output will appear here")
          ])
        )
      )
    ]);
  }
  function CompareInputField({ spec, value, onChange }) {
    const { component, label, param_name, type: inputType, options, min, max, step, placeholder } = spec;
    const inputId = `compare-${param_name}`;
    const wrapper = (children) => h60("div", { className: "c-iface__field" }, [
      h60("label", { className: "c-input-label", htmlFor: inputId, key: "label" }, label),
      children
    ]);
    switch (component) {
      case "Checkbox":
        return wrapper(h60("input", { type: "checkbox", id: inputId, checked: !!value, onChange: (e) => onChange(e.target.checked), key: "input" }));
      case "Select":
        return wrapper(h60(
          "select",
          { className: "c-input", id: inputId, value: value ?? "", onChange: (e) => onChange(e.target.value), key: "input" },
          (options || []).map((opt) => h60("option", { value: opt, key: opt }, String(opt)))
        ));
      case "Textarea":
        return wrapper(h60("textarea", { className: "c-input", id: inputId, value: value ?? "", rows: 3, onChange: (e) => onChange(e.target.value), key: "input" }));
      case "Slider":
        return wrapper(h60("div", { className: "c-iface__slider-wrap", key: "input" }, [
          h60("input", { type: "range", className: "c-iface__slider", id: inputId, min: min ?? 0, max: max ?? 1, step: step ?? 0.01, value: value ?? 0.5, onChange: (e) => onChange(parseFloat(e.target.value)), key: "slider" }),
          h60("span", { className: "c-iface__slider-value", key: "val" }, typeof value === "number" ? value.toFixed(2) : String(value ?? 0.5))
        ]));
      default:
        return wrapper(h60("input", { type: inputType || "text", className: "c-input", id: inputId, value: value ?? "", placeholder: placeholder || "", onChange: (e) => onChange(e.target.value), key: "input" }));
    }
  }
  function CompareOutputDisplay({ output }) {
    if (!output)
      return null;
    const { type, value } = output;
    switch (type) {
      case "text":
        return h60("div", { className: "c-iface__result" }, h60("pre", { className: "c-iface__text" }, String(value)));
      case "metric":
        return h60("div", { className: "c-iface__result c-iface__result--metric" }, h60("span", { className: "c-iface__metric-value" }, String(value)));
      case "json":
        return h60("div", { className: "c-iface__result" }, h60("pre", { className: "c-iface__json" }, JSON.stringify(value, null, 2)));
      case "image":
        return h60("div", { className: "c-iface__result" }, h60("img", { src: value, className: "c-iface__image", alt: "Output" }));
      case "badge":
        return h60("div", { className: "c-iface__result" }, h60("span", { className: `c-iface__badge c-iface__badge--${value === "Yes" ? "success" : "muted"}` }, value));
      case "table":
        if (!Array.isArray(value) || !value.length)
          return h60("div", { className: "c-iface__result" }, "Empty");
        const cols = Object.keys(value[0]);
        return h60(
          "div",
          { className: "c-iface__result c-iface__result--table" },
          h60("table", { className: "c-iface__table" }, [
            h60("thead", { key: "h" }, h60("tr", null, cols.map((c) => h60("th", { key: c }, c)))),
            h60("tbody", { key: "b" }, value.slice(0, 50).map((row, i) => h60("tr", { key: i }, cols.map((c) => h60("td", { key: c }, String(row[c] ?? ""))))))
          ])
        );
      default:
        return h60("div", { className: "c-iface__result" }, h60("pre", { className: "c-iface__text" }, String(value)));
    }
  }

  // src/components/form/CostDashboard.js
  var { createElement: h61, useState: useState25, useEffect: useEffect21, useCallback: useCallback16 } = React;
  function CostDashboard({ props }) {
    const {
      title = "Usage & Costs",
      show_budget = true,
      show_breakdown = true,
      compact = false
    } = props;
    const [summary, setSummary] = useState25(null);
    const fetchCosts = useCallback16(() => {
      cacaoWs.send({ type: "cost:get" });
    }, []);
    useEffect21(() => {
      const handler = (msg) => {
        if (msg.type === "cost:summary") {
          setSummary(msg.summary);
        }
      };
      cacaoWs.addListener(handler);
      fetchCosts();
      const interval = setInterval(fetchCosts, 5e3);
      return () => {
        cacaoWs.removeListener(handler);
        clearInterval(interval);
      };
    }, [fetchCosts]);
    if (!summary) {
      return h61(
        "div",
        { className: "cacao-cost-dashboard cacao-cost-empty" },
        h61("h3", null, title),
        h61("p", null, "No usage data yet")
      );
    }
    const { total_cost, total_tokens, call_count, by_model, budget } = summary;
    const formatCost = (c) => c < 0.01 ? `$${c.toFixed(4)}` : `$${c.toFixed(2)}`;
    const formatTokens = (t) => t >= 1e3 ? `${(t / 1e3).toFixed(1)}k` : `${t}`;
    const budgetPct = budget.max_cost ? Math.min(100, total_cost / budget.max_cost * 100) : budget.max_tokens ? Math.min(100, total_tokens / budget.max_tokens * 100) : null;
    return h61(
      "div",
      { className: `cacao-cost-dashboard ${compact ? "cacao-cost-compact" : ""}` },
      h61("h3", { className: "cacao-cost-title" }, title),
      // Metrics row
      h61(
        "div",
        { className: "cacao-cost-metrics" },
        h61(
          "div",
          { className: "cacao-cost-metric" },
          h61("div", { className: "cacao-cost-metric-value" }, formatCost(total_cost)),
          h61("div", { className: "cacao-cost-metric-label" }, "Total Cost")
        ),
        h61(
          "div",
          { className: "cacao-cost-metric" },
          h61("div", { className: "cacao-cost-metric-value" }, formatTokens(total_tokens)),
          h61("div", { className: "cacao-cost-metric-label" }, "Tokens")
        ),
        h61(
          "div",
          { className: "cacao-cost-metric" },
          h61("div", { className: "cacao-cost-metric-value" }, String(call_count)),
          h61("div", { className: "cacao-cost-metric-label" }, "API Calls")
        )
      ),
      // Budget gauge
      show_budget && budgetPct !== null && h61(
        "div",
        { className: "cacao-cost-budget" },
        h61(
          "div",
          { className: "cacao-cost-budget-header" },
          h61("span", null, "Budget"),
          h61(
            "span",
            null,
            budget.max_cost ? `${formatCost(total_cost)} / ${formatCost(budget.max_cost)}` : `${formatTokens(total_tokens)} / ${formatTokens(budget.max_tokens)}`
          )
        ),
        h61(
          "div",
          { className: "cacao-cost-budget-bar" },
          h61("div", {
            className: `cacao-cost-budget-fill ${budget.over_budget ? "over" : budget.degraded ? "warning" : ""}`,
            style: { width: `${budgetPct}%` }
          })
        ),
        budget.degraded && !budget.over_budget && h61(
          "div",
          { className: "cacao-cost-budget-note" },
          "Auto-degraded to cheaper model (80% threshold)"
        ),
        budget.over_budget && h61(
          "div",
          { className: "cacao-cost-budget-note cacao-cost-budget-over" },
          "Budget exceeded \u2014 requests blocked"
        )
      ),
      // Per-model breakdown
      show_breakdown && by_model && by_model.length > 0 && !compact && h61(
        "div",
        { className: "cacao-cost-breakdown" },
        h61(
          "table",
          { className: "cacao-cost-table" },
          h61(
            "thead",
            null,
            h61(
              "tr",
              null,
              h61("th", null, "Model"),
              h61("th", null, "Calls"),
              h61("th", null, "Tokens"),
              h61("th", null, "Cost")
            )
          ),
          h61(
            "tbody",
            null,
            by_model.map(
              (m2, i) => h61(
                "tr",
                { key: i },
                h61("td", null, `${m2.provider}/${m2.model}`),
                h61("td", null, String(m2.calls)),
                h61("td", null, formatTokens(m2.total_tokens)),
                h61("td", null, formatCost(m2.cost))
              )
            )
          )
        )
      )
    );
  }

  // src/components/form/DatePicker.js
  var { createElement: h62, useState: useState26 } = React;
  function DatePicker({ props }) {
    const { label, placeholder = "Select date", disabled = false, signal } = props;
    const [value, setValue] = useState26("");
    const handleChange = (e) => {
      setValue(e.target.value);
    };
    return h62("div", { className: "c-datepicker-wrapper" }, [
      label && h62("label", { className: "c-datepicker-label", key: "label" }, label),
      h62("input", {
        type: "date",
        className: "c-datepicker",
        placeholder,
        disabled,
        value,
        onChange: handleChange,
        key: "input"
      })
    ]);
  }

  // src/components/form/DocumentUpload.js
  var { createElement: h63, useState: useState27, useRef: useRef16, useCallback: useCallback17 } = React;
  function DocumentUpload({ props }) {
    const {
      schema,
      provider = "openai",
      model = "gpt-4o",
      title = "Document Upload",
      accept = ".pdf,.docx,.csv,.xlsx,.md,.txt,.html",
      show_preview = true,
      extract_on_upload = false
    } = props;
    const [docText, setDocText] = useState27("");
    const [extracted, setExtracted] = useState27(null);
    const [metadata, setMetadata] = useState27(null);
    const [loading, setLoading] = useState27(false);
    const [extracting, setExtracting] = useState27(false);
    const [error, setError] = useState27(null);
    const [fileName, setFileName] = useState27("");
    const fileInputRef = useRef16(null);
    const docId = useRef16(`doc_${Date.now()}_${Math.random().toString(36).slice(2)}`);
    const handleFileChange = useCallback17(async (e) => {
      const file = e.target.files[0];
      if (!file)
        return;
      setFileName(file.name);
      setLoading(true);
      setError(null);
      setDocText("");
      setExtracted(null);
      const reader = new FileReader();
      reader.onload = () => {
        const handler = (msg) => {
          if (msg.type === "document:result" && msg.id === docId.current) {
            setDocText(msg.text || "");
            setMetadata(msg.metadata);
            if (msg.extracted)
              setExtracted(msg.extracted);
            setLoading(false);
            cacaoWs.removeListener(handler);
          } else if (msg.type === "document:error" && msg.id === docId.current) {
            setError(msg.error);
            setLoading(false);
            cacaoWs.removeListener(handler);
          }
        };
        cacaoWs.addListener(handler);
        cacaoWs.send({
          type: "document:upload",
          id: docId.current,
          file_path: file.name,
          file_data: reader.result.split(",")[1],
          // base64 data
          schema: extract_on_upload ? schema : null,
          model: `${provider}/${model}`
        });
      };
      reader.readAsDataURL(file);
    }, [schema, provider, model, extract_on_upload]);
    const handleExtract = useCallback17(() => {
      if (!docText || extracting || !schema)
        return;
      setExtracting(true);
      setError(null);
      const handler = (msg) => {
        if (msg.type === "extract:result" && msg.id === docId.current) {
          setExtracted(msg.result);
          setExtracting(false);
          cacaoWs.removeListener(handler);
        } else if (msg.type === "extract:error" && msg.id === docId.current) {
          setError(msg.error);
          setExtracting(false);
          cacaoWs.removeListener(handler);
        }
      };
      cacaoWs.addListener(handler);
      cacaoWs.send({
        type: "extract:submit",
        id: docId.current,
        text: docText,
        schema,
        model: `${provider}/${model}`
      });
    }, [docText, extracting, schema, provider, model]);
    return h63(
      "div",
      { className: "cacao-document-upload" },
      h63(
        "div",
        { className: "cacao-document-header" },
        h63("h3", null, title)
      ),
      // File input area
      h63(
        "div",
        {
          className: `cacao-document-dropzone ${loading ? "loading" : ""}`,
          onClick: () => fileInputRef.current?.click()
        },
        h63("input", {
          ref: fileInputRef,
          type: "file",
          accept,
          onChange: handleFileChange,
          style: { display: "none" }
        }),
        loading ? h63("div", { className: "cacao-document-loading" }, "Parsing document...") : fileName ? h63(
          "div",
          { className: "cacao-document-filename" },
          h63("span", null, "\u{1F4C4} "),
          h63("strong", null, fileName),
          metadata && h63(
            "span",
            { className: "cacao-document-meta" },
            ` (${(metadata.length || 0).toLocaleString()} chars)`
          )
        ) : h63(
          "div",
          { className: "cacao-document-placeholder" },
          h63("div", null, "\u{1F4C1}"),
          h63("div", null, "Click to upload or drag & drop"),
          h63("small", null, accept.split(",").join(", "))
        )
      ),
      error && h63("div", { className: "cacao-alert cacao-alert-error" }, error),
      // Preview
      show_preview && docText && h63(
        "div",
        { className: "cacao-document-preview" },
        h63(
          "details",
          { open: !extracted },
          h63("summary", null, "Parsed Text Preview"),
          h63("pre", { className: "cacao-document-text" }, docText.slice(0, 5e3)),
          docText.length > 5e3 && h63("small", null, `... ${docText.length - 5e3} more characters`)
        )
      ),
      // Extract button (when schema is set but extract_on_upload is off)
      schema && docText && !extract_on_upload && !extracted && h63("button", {
        className: "cacao-btn cacao-btn-primary",
        onClick: handleExtract,
        disabled: extracting
      }, extracting ? "Extracting..." : "Extract Data"),
      // Extracted data
      extracted && h63(
        "div",
        { className: "cacao-document-extracted" },
        h63("h4", null, "Extracted Data"),
        h63("pre", { className: "cacao-extract-result" }, JSON.stringify(extracted, null, 2))
      )
    );
  }

  // src/components/form/Extract.js
  var { createElement: h64, useState: useState28, useRef: useRef17, useCallback: useCallback18 } = React;
  function Extract({ props }) {
    const {
      schema,
      pydantic_model_name,
      provider = "openai",
      model = "gpt-4o",
      title = "Extract",
      description = "",
      submit_label = "Extract",
      height = "400px"
    } = props;
    const [inputText, setInputText] = useState28("");
    const [result, setResult] = useState28(null);
    const [usage, setUsage] = useState28(null);
    const [loading, setLoading] = useState28(false);
    const [error, setError] = useState28(null);
    const extractId = useRef17(`extract_${Date.now()}_${Math.random().toString(36).slice(2)}`);
    const handleSubmit = useCallback18(() => {
      if (!inputText.trim() || loading)
        return;
      setLoading(true);
      setError(null);
      setResult(null);
      const handler = (msg) => {
        if (msg.type === "extract:result" && msg.id === extractId.current) {
          setResult(msg.result);
          setUsage(msg.usage);
          setLoading(false);
          cacaoWs.removeListener(handler);
        } else if (msg.type === "extract:error" && msg.id === extractId.current) {
          setError(msg.error);
          setLoading(false);
          cacaoWs.removeListener(handler);
        }
      };
      cacaoWs.addListener(handler);
      cacaoWs.send({
        type: "extract:submit",
        id: extractId.current,
        text: inputText,
        schema,
        model: `${provider}/${model}`
      });
    }, [inputText, loading, schema, provider, model]);
    return h64(
      "div",
      { className: "cacao-extract", style: { height } },
      // Header
      h64(
        "div",
        { className: "cacao-extract-header" },
        h64("h3", { className: "cacao-extract-title" }, title),
        description && h64("p", { className: "cacao-extract-description" }, description)
      ),
      // Main content
      h64(
        "div",
        { className: "cacao-extract-body" },
        // Left: text input
        h64(
          "div",
          { className: "cacao-extract-input" },
          h64("label", { className: "cacao-extract-label" }, "Text to extract from"),
          h64("textarea", {
            className: "cacao-extract-textarea",
            value: inputText,
            onChange: (e) => setInputText(e.target.value),
            placeholder: "Paste or type text here..."
          }),
          // Schema preview
          schema && h64(
            "div",
            { className: "cacao-extract-schema" },
            h64(
              "details",
              null,
              h64(
                "summary",
                null,
                "Schema ",
                pydantic_model_name && h64("span", { className: "cacao-badge" }, pydantic_model_name)
              ),
              h64("pre", null, JSON.stringify(schema, null, 2))
            )
          ),
          h64("button", {
            className: "cacao-btn cacao-btn-primary",
            onClick: handleSubmit,
            disabled: loading || !inputText.trim()
          }, loading ? "Extracting..." : submit_label)
        ),
        // Right: result
        h64(
          "div",
          { className: "cacao-extract-output" },
          h64("label", { className: "cacao-extract-label" }, "Extracted Data"),
          error && h64("div", { className: "cacao-alert cacao-alert-error" }, error),
          result && h64("pre", { className: "cacao-extract-result" }, JSON.stringify(result, null, 2)),
          usage && Object.keys(usage).length > 0 && h64(
            "div",
            { className: "cacao-extract-usage" },
            h64(
              "small",
              null,
              usage.total_tokens && `${usage.total_tokens} tokens`,
              usage.cost && ` \xB7 $${usage.cost.toFixed(4)}`
            )
          ),
          !result && !error && !loading && h64(
            "div",
            { className: "cacao-extract-placeholder" },
            "Results will appear here"
          )
        )
      )
    );
  }

  // src/components/form/FileUpload.js
  var { createElement: h65, useRef: useRef18 } = React;
  function FileUpload({ props }) {
    const { label, accept, multiple = false, on_upload } = props;
    const inputRef = useRef18(null);
    const handleClick = () => {
      inputRef.current?.click();
    };
    const handleChange = (e) => {
      const files = Array.from(e.target.files || []);
      if (on_upload && files.length > 0) {
        console.log("Files selected:", files);
      }
    };
    return h65("div", { className: "c-upload-wrapper" }, [
      h65("input", {
        ref: inputRef,
        type: "file",
        accept,
        multiple,
        onChange: handleChange,
        style: { display: "none" },
        key: "input"
      }),
      h65("button", {
        type: "button",
        className: "c-upload-button",
        onClick: handleClick,
        key: "button"
      }, [
        h65("span", { className: "c-upload-icon", key: "icon" }, "\u2191"),
        h65("span", { key: "label" }, label || "Upload File")
      ])
    ]);
  }

  // src/components/form/Input.js
  var { createElement: h66, useState: useState29, useEffect: useEffect22 } = React;
  function Input({ props }) {
    const {
      label,
      placeholder = "",
      type = "text",
      disabled = false,
      signal,
      on_change
    } = props;
    const [value, setValue] = useState29("");
    const signalName = signal?.__signal__;
    useEffect22(() => {
      if (signalName) {
        const unsubscribe = cacaoWs.subscribe((signals) => {
          if (signals[signalName] !== void 0) {
            setValue(signals[signalName]);
          }
        });
        const initial = cacaoWs.getSignal(signalName);
        if (initial !== void 0) {
          setValue(initial);
        }
        return unsubscribe;
      }
    }, [signalName]);
    const handleChange = (e) => {
      const newValue = e.target.value;
      setValue(newValue);
      const eventName = on_change?.__event__ || on_change;
      if (eventName) {
        cacaoWs.sendEvent(eventName, { value: newValue });
      }
    };
    return h66("div", { className: "c-input-wrapper" }, [
      label && h66("label", { className: "c-input-label", key: "label" }, label),
      h66("input", {
        type,
        className: "c-input",
        placeholder,
        disabled,
        value,
        onChange: handleChange,
        key: "input"
      })
    ]);
  }

  // src/components/form/Interface.js
  init_static_runtime();
  var { createElement: h67, useState: useState30, useEffect: useEffect23, useRef: useRef19, useCallback: useCallback19, useMemo: useMemo7 } = React;
  function simpleMarkdown(text2) {
    if (!text2)
      return "";
    return String(text2).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/^### (.+)$/gm, "<h3>$1</h3>").replace(/^## (.+)$/gm, "<h2>$1</h2>").replace(/^# (.+)$/gm, "<h1>$1</h1>").replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\*(.+?)\*/g, "<em>$1</em>").replace(/`(.+?)`/g, "<code>$1</code>").replace(/\n/g, "<br>");
  }
  function PlotlyOutput({ value }) {
    const containerRef = useRef19(null);
    useEffect23(() => {
      if (containerRef.current && window.Plotly) {
        try {
          const data = typeof value === "string" ? JSON.parse(value) : value;
          window.Plotly.newPlot(containerRef.current, data.data || [], data.layout || {}, { responsive: true });
        } catch (e) {
          console.warn("Plotly render error:", e);
        }
      }
    }, [value]);
    if (!window.Plotly) {
      return h67(
        "div",
        { className: "c-iface__result" },
        h67("pre", { className: "c-iface__json" }, typeof value === "string" ? value : JSON.stringify(value, null, 2))
      );
    }
    return h67("div", { className: "c-iface__result c-iface__result--plotly", ref: containerRef });
  }
  function Interface({ props }) {
    const {
      id,
      title,
      description,
      submit_label = "Submit",
      layout = "auto",
      inputs = [],
      output_mode = "text",
      exec_mode = "simple",
      examples,
      param_names = [],
      live = false,
      flagging = false
    } = props;
    const [values, setValues] = useState30(() => {
      const initial = {};
      inputs.forEach((inp) => {
        initial[inp.param_name] = inp.default != null ? inp.default : "";
      });
      return initial;
    });
    const [output, setOutput] = useState30(null);
    const [loading, setLoading] = useState30(false);
    const [progress, setProgress] = useState30(0);
    const [streamText, setStreamText] = useState30("");
    const [isStreaming, setIsStreaming] = useState30(false);
    const [error, setError] = useState30(null);
    const [showTraceback, setShowTraceback] = useState30(false);
    const [cached, setCached] = useState30(false);
    const [flagged, setFlagged] = useState30(false);
    const liveTimerRef = useRef19(null);
    useEffect23(() => {
      const unsubWs = cacaoWs.subscribe(() => {
      });
      const handler = (event) => {
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }
        if (!msg.id || msg.id !== id)
          return;
        switch (msg.type) {
          case "interface:result":
            setOutput(msg.output);
            setCached(!!msg.cached);
            setLoading(false);
            setProgress(0);
            break;
          case "interface:error":
            setError({ error: msg.error, message: msg.message, traceback: msg.traceback });
            setLoading(false);
            setProgress(0);
            setIsStreaming(false);
            break;
          case "interface:progress":
            setProgress(msg.value);
            break;
          case "interface:stream":
            setStreamText((prev) => prev + msg.token);
            break;
          case "interface:stream_done":
            setIsStreaming(false);
            setLoading(false);
            setStreamText((prev) => {
              if (prev) {
                setOutput({ type: "text", value: prev });
              }
              return "";
            });
            break;
          case "interface:flagged":
            setFlagged(true);
            setTimeout(() => setFlagged(false), 2e3);
            break;
        }
      };
      if (cacaoWs.ws) {
        cacaoWs.ws.addEventListener("message", handler);
        return () => {
          cacaoWs.ws?.removeEventListener("message", handler);
          unsubWs();
        };
      }
      return unsubWs;
    }, [id]);
    const updateValue = useCallback19((paramName, value) => {
      setValues((prev) => {
        const next = { ...prev, [paramName]: value };
        if (live) {
          if (liveTimerRef.current)
            clearTimeout(liveTimerRef.current);
          liveTimerRef.current = setTimeout(() => {
            doSubmit(next);
          }, 300);
        }
        return next;
      });
    }, [live]);
    const doSubmit = useCallback19((overrideValues) => {
      const submitValues = overrideValues || values;
      setError(null);
      setOutput(null);
      setCached(false);
      setStreamText("");
      setLoading(true);
      setProgress(0);
      if (exec_mode === "stream") {
        setIsStreaming(true);
      }
      if (cacaoWs.ws && cacaoWs.connected) {
        cacaoWs.ws.send(JSON.stringify({
          type: "interface:submit",
          id,
          inputs: submitValues
        }));
      }
    }, [values, id, exec_mode]);
    const handleSubmit = useCallback19(() => {
      doSubmit(null);
    }, [doSubmit]);
    const handleFlag = useCallback19(() => {
      if (!output)
        return;
      if (cacaoWs.ws && cacaoWs.connected) {
        cacaoWs.ws.send(JSON.stringify({
          type: "interface:flag",
          id,
          inputs: values,
          output
        }));
      }
    }, [id, values, output]);
    const loadExample = useCallback19((exampleValues) => {
      const newValues = {};
      param_names.forEach((name, i) => {
        newValues[name] = exampleValues[i] != null ? exampleValues[i] : "";
      });
      setValues(newValues);
      if (live) {
        setTimeout(() => doSubmit(newValues), 50);
      }
    }, [param_names, live, doSubmit]);
    const layoutClass = layout === "vertical" ? "c-iface--vertical" : layout === "horizontal" ? "c-iface--horizontal" : "c-iface--auto";
    return h67("div", { className: `c-iface ${layoutClass}` }, [
      // Header
      (title || description) && h67("div", { className: "c-iface__header", key: "header" }, [
        title && h67("h3", { className: "c-iface__title", key: "title" }, title),
        description && h67("p", { className: "c-iface__desc", key: "desc" }, description)
      ]),
      // Body: inputs + outputs
      h67("div", { className: "c-iface__body", key: "body" }, [
        // Input panel
        h67("div", { className: "c-iface__inputs", key: "inputs" }, [
          ...inputs.map(
            (inp, i) => h67(InputField, {
              key: inp.param_name,
              spec: inp,
              value: values[inp.param_name],
              onChange: (val) => updateValue(inp.param_name, val)
            })
          ),
          // Examples
          examples && examples.length > 0 && h67("div", { className: "c-iface__examples", key: "examples" }, [
            h67("span", { className: "c-iface__examples-label", key: "label" }, "Examples:"),
            ...examples.map(
              (ex, i) => h67("button", {
                className: "c-iface__example-btn",
                key: `ex-${i}`,
                onClick: () => loadExample(ex)
              }, `Example ${i + 1}`)
            )
          ]),
          // Submit button (not shown in live mode)
          !live && !isStaticMode() && h67(
            "button",
            {
              className: "btn btn-primary c-iface__submit",
              onClick: handleSubmit,
              disabled: loading,
              key: "submit"
            },
            loading ? h67("span", { className: "c-iface__spinner" }) : submit_label
          ),
          // Static mode fallback
          !live && isStaticMode() && h67("div", {
            className: "c-iface__static-fallback",
            key: "static-fallback"
          }, "This interface requires a Python server. Run: cacao run app.py")
        ]),
        // Output panel
        h67("div", { className: "c-iface__output", key: "output" }, [
          // Loading states
          loading && exec_mode === "progress" && h67("div", { className: "c-iface__progress", key: "progress" }, [
            h67(
              "div",
              { className: "c-iface__progress-bar", key: "bar" },
              h67("div", {
                className: "c-iface__progress-fill",
                style: { width: `${Math.round(progress * 100)}%` }
              })
            ),
            h67(
              "span",
              { className: "c-iface__progress-text", key: "text" },
              `${Math.round(progress * 100)}%`
            )
          ]),
          loading && exec_mode === "simple" && !isStreaming && h67("div", {
            className: "c-iface__loading",
            key: "loading"
          }, h67("span", { className: "c-iface__spinner c-iface__spinner--lg" })),
          // Streaming output
          isStreaming && streamText && h67("div", {
            className: "c-iface__result c-iface__result--streaming",
            key: "stream"
          }, h67("pre", { className: "c-iface__text" }, streamText)),
          // Result output
          !loading && output && !isStreaming && h67(OutputDisplay, {
            output,
            key: "result"
          }),
          // Cached badge
          cached && h67("span", { className: "c-iface__badge c-iface__badge--cached", key: "cached" }, "Cached"),
          // Error display
          error && h67("div", { className: "c-iface__error", key: "error" }, [
            h67("div", { className: "c-iface__error-header", key: "header" }, [
              h67("strong", { key: "type" }, error.error),
              h67("span", { key: "msg" }, `: ${error.message}`)
            ]),
            error.traceback && h67("button", {
              className: "c-iface__error-toggle",
              onClick: () => setShowTraceback(!showTraceback),
              key: "toggle"
            }, showTraceback ? "Hide traceback" : "Show traceback"),
            showTraceback && error.traceback && h67("pre", {
              className: "c-iface__traceback",
              key: "tb"
            }, error.traceback)
          ]),
          // Empty state
          !loading && !output && !error && !isStreaming && h67("div", {
            className: "c-iface__empty",
            key: "empty"
          }, "Output will appear here"),
          // Flag button
          flagging && output && !loading && h67("button", {
            className: `c-iface__flag ${flagged ? "c-iface__flag--done" : ""}`,
            onClick: handleFlag,
            key: "flag"
          }, flagged ? "Flagged!" : "Flag")
        ])
      ])
    ]);
  }
  function InputField({ spec, value, onChange }) {
    const {
      component,
      label,
      description: desc,
      param_name,
      type: inputType,
      options,
      min,
      max,
      step,
      placeholder,
      monospace,
      accept,
      optional
    } = spec;
    const inputId = `iface-${param_name}`;
    const wrapper = (children) => h67("div", { className: "c-iface__field" }, [
      h67("label", { className: "c-input-label", htmlFor: inputId, key: "label" }, [
        label,
        optional && h67("span", { className: "c-iface__optional", key: "opt" }, " (optional)")
      ]),
      desc && h67("span", { className: "c-iface__field-desc", key: "desc" }, desc),
      children
    ]);
    switch (component) {
      case "Checkbox":
        return wrapper(
          h67("label", { className: "c-iface__checkbox", key: "input" }, [
            h67("input", {
              type: "checkbox",
              id: inputId,
              checked: !!value,
              onChange: (e) => onChange(e.target.checked),
              key: "cb"
            }),
            h67("span", { key: "text" }, value ? "Yes" : "No")
          ])
        );
      case "Select":
        return wrapper(
          h67("select", {
            className: "c-input c-iface__select",
            id: inputId,
            value: value ?? "",
            onChange: (e) => onChange(e.target.value),
            key: "input"
          }, (options || []).map(
            (opt) => h67("option", { value: opt, key: opt }, String(opt))
          ))
        );
      case "Slider":
        return wrapper(
          h67("div", { className: "c-iface__slider-wrap", key: "input" }, [
            h67("input", {
              type: "range",
              className: "c-iface__slider",
              id: inputId,
              min: min ?? 0,
              max: max ?? 1,
              step: step ?? 0.01,
              value: value ?? 0.5,
              onChange: (e) => onChange(parseFloat(e.target.value)),
              key: "slider"
            }),
            h67(
              "span",
              { className: "c-iface__slider-value", key: "val" },
              typeof value === "number" ? value.toFixed(2) : String(value ?? 0.5)
            )
          ])
        );
      case "Textarea":
        return wrapper(
          h67("textarea", {
            className: `c-input c-iface__textarea ${monospace ? "c-iface__textarea--mono" : ""}`,
            id: inputId,
            placeholder: placeholder || "",
            value: value ?? "",
            rows: 4,
            onChange: (e) => onChange(e.target.value),
            key: "input"
          })
        );
      case "FileUpload":
        return wrapper(
          h67("div", { className: "c-iface__file-wrap", key: "input" }, [
            h67("input", {
              type: "file",
              className: "c-iface__file",
              id: inputId,
              accept: accept || void 0,
              onChange: (e) => {
                const file = e.target.files?.[0];
                if (file) {
                  const reader = new FileReader();
                  reader.onload = () => onChange(reader.result);
                  reader.readAsDataURL(file);
                }
              },
              key: "file-input"
            }),
            // Image preview
            value && accept && accept.startsWith("image") && h67("img", {
              src: value,
              className: "c-iface__file-preview",
              alt: "Preview",
              key: "preview"
            }),
            // Audio preview
            value && accept && accept.startsWith("audio") && h67("audio", {
              src: value,
              controls: true,
              className: "c-iface__audio-preview",
              key: "audio-preview"
            }),
            // Video preview
            value && accept && accept.startsWith("video") && h67("video", {
              src: value,
              controls: true,
              className: "c-iface__video-preview",
              key: "video-preview"
            })
          ])
        );
      case "Input":
      default:
        return wrapper(
          h67("input", {
            type: inputType || "text",
            className: "c-input",
            id: inputId,
            placeholder: placeholder || "",
            value: value ?? "",
            onChange: (e) => onChange(inputType === "number" ? e.target.value : e.target.value),
            key: "input"
          })
        );
    }
  }
  function OutputDisplay({ output }) {
    if (!output)
      return null;
    const { type, value } = output;
    switch (type) {
      case "text":
        return h67(
          "div",
          { className: "c-iface__result" },
          h67("pre", { className: "c-iface__text" }, String(value))
        );
      case "metric":
        return h67(
          "div",
          { className: "c-iface__result c-iface__result--metric" },
          h67("span", { className: "c-iface__metric-value" }, String(value))
        );
      case "badge":
        return h67(
          "div",
          { className: "c-iface__result" },
          h67("span", { className: `c-iface__badge c-iface__badge--${value === "Yes" ? "success" : "muted"}` }, value)
        );
      case "json":
        return h67(
          "div",
          { className: "c-iface__result" },
          h67("pre", { className: "c-iface__json" }, JSON.stringify(value, null, 2))
        );
      case "table":
        if (!Array.isArray(value) || value.length === 0) {
          return h67(
            "div",
            { className: "c-iface__result" },
            h67("span", { className: "c-iface__empty" }, "Empty result")
          );
        }
        const columns = Object.keys(value[0]);
        return h67(
          "div",
          { className: "c-iface__result c-iface__result--table" },
          h67("table", { className: "c-iface__table" }, [
            h67(
              "thead",
              { key: "head" },
              h67("tr", null, columns.map(
                (col) => h67("th", { key: col }, col)
              ))
            ),
            h67(
              "tbody",
              { key: "body" },
              value.map(
                (row, i) => h67(
                  "tr",
                  { key: i },
                  columns.map(
                    (col) => h67("td", { key: col }, String(row[col] ?? ""))
                  )
                )
              )
            )
          ])
        );
      case "code":
        return h67(
          "div",
          { className: "c-iface__result" },
          h67(
            "pre",
            { className: "c-iface__code" },
            h67("code", null, String(value))
          )
        );
      case "image":
        return h67(
          "div",
          { className: "c-iface__result c-iface__result--image" },
          h67("img", {
            src: value,
            className: "c-iface__image",
            alt: "Output image",
            loading: "lazy"
          })
        );
      case "audio":
        return h67(
          "div",
          { className: "c-iface__result c-iface__result--audio" },
          h67("audio", {
            src: value,
            controls: true,
            className: "c-iface__audio"
          })
        );
      case "video":
        return h67(
          "div",
          { className: "c-iface__result c-iface__result--video" },
          h67("video", {
            src: value,
            controls: true,
            className: "c-iface__video"
          })
        );
      case "file":
        return h67(
          "div",
          { className: "c-iface__result c-iface__result--file" },
          h67("a", {
            href: value,
            download: "output",
            className: "c-iface__file-download"
          }, "Download file")
        );
      case "plotly":
        return h67(PlotlyOutput, { value });
      case "markdown":
        return h67("div", {
          className: "c-iface__result c-iface__result--markdown",
          dangerouslySetInnerHTML: { __html: simpleMarkdown(value) }
        });
      case "multi":
        return h67(
          "div",
          { className: "c-iface__result c-iface__result--multi" },
          value.map((item, i) => h67(OutputDisplay, { output: item, key: i }))
        );
      default:
        return h67(
          "div",
          { className: "c-iface__result" },
          h67("pre", { className: "c-iface__text" }, String(value))
        );
    }
  }

  // src/components/form/ModelPicker.js
  var { createElement: h68, useState: useState31, useEffect: useEffect24, useCallback: useCallback20, useMemo: useMemo8, useRef: useRef20 } = React;
  function ModelPicker({ props }) {
    const {
      signal,
      label = "Model",
      grouped = true
    } = props;
    const [models, setModels] = useState31(null);
    const [loading, setLoading] = useState31(true);
    const [error, setError] = useState31(null);
    const [search, setSearch] = useState31("");
    const [isOpen, setIsOpen] = useState31(false);
    const [selectedModel, setSelectedModel] = useState31(props.default || "");
    const dropdownRef = useRef20(null);
    const signalName = signal?.__signal__;
    useEffect24(() => {
      if (!signalName)
        return;
      const handler = (msg) => {
        if (msg.type === "update" && msg.signal === signalName) {
          setSelectedModel(msg.value || "");
        }
      };
      cacaoWs.addListener(handler);
      if (cacaoWs.signals[signalName] !== void 0) {
        setSelectedModel(cacaoWs.signals[signalName] || "");
      }
      return () => cacaoWs.removeListener(handler);
    }, [signalName]);
    useEffect24(() => {
      const handler = (msg) => {
        if (msg.type === "models:result") {
          setModels(msg.models);
          setLoading(false);
          cacaoWs.removeListener(handler);
        } else if (msg.type === "models:error") {
          setError(msg.error);
          setLoading(false);
          cacaoWs.removeListener(handler);
        }
      };
      cacaoWs.addListener(handler);
      cacaoWs.send({ type: "models:discover", grouped });
      return () => cacaoWs.removeListener(handler);
    }, [grouped]);
    useEffect24(() => {
      const handleClick = (e) => {
        if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
          setIsOpen(false);
        }
      };
      document.addEventListener("mousedown", handleClick);
      return () => document.removeEventListener("mousedown", handleClick);
    }, []);
    const handleSelect = useCallback20((modelStr) => {
      setSelectedModel(modelStr);
      setIsOpen(false);
      setSearch("");
      if (signalName) {
        cacaoWs.send({
          type: "event",
          name: `signal:set:${signalName}`,
          data: { value: modelStr }
        });
      }
    }, [signalName]);
    const filteredModels = useMemo8(() => {
      if (!models)
        return [];
      const q2 = search.toLowerCase();
      if (grouped && typeof models === "object" && !Array.isArray(models)) {
        const result = [];
        for (const [provider, info] of Object.entries(models)) {
          const providerModels = (info.models || []).filter((m2) => {
            const name = typeof m2 === "string" ? m2 : m2.model || m2.id || "";
            return !q2 || name.toLowerCase().includes(q2) || provider.toLowerCase().includes(q2);
          });
          if (providerModels.length > 0) {
            result.push({
              provider,
              displayName: info.display_name || provider,
              models: providerModels
            });
          }
        }
        return result;
      }
      const list = Array.isArray(models) ? models : [];
      return list.filter((m2) => {
        const name = typeof m2 === "string" ? m2 : m2.model || m2.id || "";
        return !q2 || name.toLowerCase().includes(q2);
      });
    }, [models, search, grouped]);
    if (loading) {
      return h68(
        "div",
        { className: "cacao-model-picker" },
        h68("label", { className: "cacao-input-label" }, label),
        h68("div", { className: "cacao-model-picker-loading" }, "Discovering models...")
      );
    }
    if (error) {
      return h68(
        "div",
        { className: "cacao-model-picker" },
        h68("label", { className: "cacao-input-label" }, label),
        h68("div", { className: "cacao-alert cacao-alert-error" }, error)
      );
    }
    return h68(
      "div",
      { className: "cacao-model-picker", ref: dropdownRef },
      h68("label", { className: "cacao-input-label" }, label),
      h68(
        "div",
        {
          className: `cacao-model-picker-trigger ${isOpen ? "open" : ""}`,
          onClick: () => setIsOpen(!isOpen)
        },
        h68("span", null, selectedModel || "Select a model..."),
        h68("span", { className: "cacao-model-picker-arrow" }, isOpen ? "\u25B2" : "\u25BC")
      ),
      isOpen && h68(
        "div",
        { className: "cacao-model-picker-dropdown" },
        h68("input", {
          className: "cacao-model-picker-search",
          type: "text",
          placeholder: "Search models...",
          value: search,
          onChange: (e) => setSearch(e.target.value),
          autoFocus: true
        }),
        h68(
          "div",
          { className: "cacao-model-picker-list" },
          grouped && Array.isArray(filteredModels) && filteredModels.map(
            (group, gi) => h68(
              "div",
              { key: gi, className: "cacao-model-picker-group" },
              h68("div", { className: "cacao-model-picker-group-header" }, group.displayName),
              group.models.map((m2, mi) => {
                const modelStr = typeof m2 === "string" ? m2 : m2.model || m2.id || "";
                return h68("div", {
                  key: mi,
                  className: `cacao-model-picker-item ${modelStr === selectedModel ? "selected" : ""}`,
                  onClick: () => handleSelect(modelStr)
                }, modelStr);
              })
            )
          ),
          !grouped && Array.isArray(filteredModels) && filteredModels.map((m2, i) => {
            const modelStr = typeof m2 === "string" ? m2 : m2.model || m2.id || "";
            return h68("div", {
              key: i,
              className: `cacao-model-picker-item ${modelStr === selectedModel ? "selected" : ""}`,
              onClick: () => handleSelect(modelStr)
            }, modelStr);
          }),
          filteredModels.length === 0 && h68(
            "div",
            { className: "cacao-model-picker-empty" },
            "No models found"
          )
        )
      )
    );
  }

  // src/components/form/MultiAgent.js
  var { createElement: h69, useState: useState32, useEffect: useEffect25, useRef: useRef21, useCallback: useCallback21 } = React;
  function MultiAgent({ props }) {
    const {
      multi_id,
      mode = "debate",
      agent_names = [],
      rounds = 3,
      title,
      height = "600px"
    } = props;
    const [inputText, setInputText] = useState32("");
    const [isRunning, setIsRunning] = useState32(false);
    const [turns, setTurns] = useState32([]);
    const [streamingTexts, setStreamingTexts] = useState32({});
    const [routingInfo, setRoutingInfo] = useState32(null);
    const [error, setError] = useState32(null);
    const [isDone, setIsDone] = useState32(false);
    const [finalData, setFinalData] = useState32(null);
    const contentEndRef = useRef21(null);
    const inputRef = useRef21(null);
    useEffect25(() => {
      const handler = (msg) => {
        if (msg.multi_id !== multi_id)
          return;
        switch (msg.type) {
          case "multi_agent:started":
            setIsRunning(true);
            setTurns([]);
            setStreamingTexts({});
            setRoutingInfo(null);
            setError(null);
            setIsDone(false);
            setFinalData(null);
            break;
          case "multi_agent:routing":
            setRoutingInfo(msg);
            break;
          case "multi_agent:turn":
            if (msg.status === "done") {
              setTurns((prev) => [
                ...prev,
                {
                  agent_name: msg.agent_name,
                  agent_index: msg.agent_index,
                  round: msg.round,
                  content: msg.content,
                  pipeline_step: msg.pipeline_step,
                  pipeline_total: msg.pipeline_total
                }
              ]);
              setStreamingTexts((prev) => {
                const next = { ...prev };
                delete next[msg.agent_index];
                return next;
              });
            } else {
              setStreamingTexts((prev) => ({ ...prev, [msg.agent_index]: "" }));
            }
            break;
          case "multi_agent:delta":
            setStreamingTexts((prev) => ({
              ...prev,
              [msg.agent_index]: (prev[msg.agent_index] || "") + msg.delta
            }));
            break;
          case "multi_agent:done":
            setIsRunning(false);
            setIsDone(true);
            setFinalData(msg);
            break;
          case "multi_agent:error":
            setIsRunning(false);
            setError(msg.error);
            break;
        }
      };
      cacaoWs.addListener(handler);
      return () => cacaoWs.removeListener(handler);
    }, [multi_id]);
    useEffect25(() => {
      if (contentEndRef.current) {
        contentEndRef.current.scrollIntoView({ behavior: "smooth" });
      }
    }, [turns, streamingTexts]);
    const handleSend = useCallback21(() => {
      const text2 = inputText.trim();
      if (!text2 || isRunning)
        return;
      cacaoWs.send({
        type: "multi_agent:run",
        multi_id,
        text: text2
      });
      setInputText("");
      if (inputRef.current)
        inputRef.current.focus();
    }, [inputText, isRunning, multi_id]);
    const handleKeyDown = useCallback21(
      (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleSend();
        }
      },
      [handleSend]
    );
    const agentColors = [
      "var(--accent-primary)",
      "#e57373",
      "#81c784",
      "#ffb74d",
      "#64b5f6",
      "#ba68c8"
    ];
    const getAgentColor = (idx) => agentColors[idx % agentColors.length];
    const modeLabel = mode === "debate" ? "Debate" : mode === "router" ? "Router" : "Pipeline";
    const renderTurn = (turn, index) => {
      const color = getAgentColor(turn.agent_index);
      return h69(
        "div",
        { className: "c-multi-agent__turn", key: index },
        [
          h69("div", { className: "c-multi-agent__turn-header", key: "hdr" }, [
            h69(
              "span",
              {
                className: "c-multi-agent__agent-name",
                style: { color },
                key: "name"
              },
              turn.agent_name
            ),
            turn.round && h69(
              "span",
              { className: "c-multi-agent__round-badge", key: "round" },
              `Round ${turn.round}`
            ),
            turn.pipeline_step && h69(
              "span",
              { className: "c-multi-agent__round-badge", key: "pipe" },
              `Step ${turn.pipeline_step}/${turn.pipeline_total}`
            )
          ]),
          h69(
            "div",
            {
              className: "c-multi-agent__turn-content",
              style: { borderLeftColor: color },
              key: "content"
            },
            turn.content
          )
        ]
      );
    };
    const renderStreaming = () => {
      return Object.entries(streamingTexts).map(([idxStr, text2]) => {
        const idx = parseInt(idxStr, 10);
        const name = agent_names[idx] || `Agent ${idx + 1}`;
        const color = getAgentColor(idx);
        return h69(
          "div",
          { className: "c-multi-agent__turn c-multi-agent__turn--streaming", key: `stream-${idx}` },
          [
            h69("div", { className: "c-multi-agent__turn-header", key: "hdr" }, [
              h69(
                "span",
                { className: "c-multi-agent__agent-name", style: { color }, key: "name" },
                name
              ),
              h69("span", { className: "c-multi-agent__streaming-dot", key: "dot" })
            ]),
            h69(
              "div",
              {
                className: "c-multi-agent__turn-content",
                style: { borderLeftColor: color },
                key: "content"
              },
              text2 || "..."
            )
          ]
        );
      });
    };
    return h69("div", { className: "c-multi-agent", style: { height } }, [
      // Header
      h69("div", { className: "c-multi-agent__header", key: "header" }, [
        h69(
          "span",
          { className: "c-multi-agent__title", key: "title" },
          title || `Multi-Agent (${modeLabel})`
        ),
        h69("div", { className: "c-multi-agent__badges", key: "badges" }, [
          h69(
            "span",
            { className: "c-multi-agent__mode-badge", key: "mode" },
            modeLabel
          ),
          h69(
            "span",
            { className: "c-multi-agent__count-badge", key: "count" },
            `${agent_names.length} agents`
          )
        ])
      ]),
      // Agent list
      h69(
        "div",
        { className: "c-multi-agent__agents", key: "agents" },
        agent_names.map(
          (name, i) => h69(
            "span",
            {
              className: "c-multi-agent__agent-chip",
              style: { borderColor: getAgentColor(i), color: getAgentColor(i) },
              key: i
            },
            name
          )
        )
      ),
      // Content area
      h69("div", { className: "c-multi-agent__content", key: "content" }, [
        // Router info
        routingInfo && h69("div", { className: "c-multi-agent__routing", key: "routing" }, [
          h69(
            "div",
            { className: "c-multi-agent__routing-label", key: "lbl" },
            routingInfo.status === "done" ? `Routed to: ${routingInfo.chosen_agent}` : "Routing decision..."
          ),
          routingInfo.reason && h69("div", { className: "c-multi-agent__routing-reason", key: "reason" }, routingInfo.reason)
        ]),
        // Turns
        ...turns.map(renderTurn),
        // Streaming turns
        ...renderStreaming(),
        // Error
        error && h69("div", { className: "c-multi-agent__error", key: "error" }, error),
        // Empty state
        !isRunning && turns.length === 0 && !error && h69(
          "div",
          { className: "c-multi-agent__empty", key: "empty" },
          `Send a message to start the ${modeLabel.toLowerCase()}.`
        ),
        h69("div", { ref: contentEndRef, key: "anchor" })
      ]),
      // Input area
      h69("div", { className: "c-multi-agent__input-area", key: "input" }, [
        h69("textarea", {
          ref: inputRef,
          className: "c-multi-agent__input",
          placeholder: `Type a message for the ${modeLabel.toLowerCase()}...`,
          value: inputText,
          rows: 1,
          disabled: isRunning,
          onChange: (e) => setInputText(e.target.value),
          onKeyDown: handleKeyDown,
          key: "textarea"
        }),
        h69(
          "button",
          {
            className: "c-multi-agent__send",
            onClick: handleSend,
            disabled: !inputText.trim() || isRunning,
            key: "send"
          },
          isRunning ? h69("span", { className: "c-multi-agent__send-spinner" }) : "\u25B6"
        )
      ])
    ]);
  }

  // src/components/form/SafetyPolicy.js
  var { createElement: h70, useState: useState33, useEffect: useEffect26, useCallback: useCallback22 } = React;
  var PRESETS = [
    { id: "permissive", label: "Permissive", desc: "All access allowed", icon: "\u{1F7E2}" },
    { id: "network_only", label: "Network Only", desc: "Network yes, filesystem no", icon: "\u{1F310}" },
    { id: "filesystem_only", label: "Filesystem Only", desc: "Filesystem yes, network no", icon: "\u{1F4C1}" },
    { id: "restrictive", label: "Restrictive", desc: "No imports, no network, no filesystem", icon: "\u{1F512}" },
    { id: "custom", label: "Custom", desc: "Configure manually", icon: "\u2699" }
  ];
  function SafetyPolicy({ props }) {
    const {
      title = "Safety Policy",
      preset: initialPreset = null,
      show_presets = true,
      show_advanced = true,
      compact = false
    } = props;
    const [activePreset, setActivePreset] = useState33(initialPreset || "permissive");
    const [policy, setPolicy] = useState33(null);
    const [allowNetwork, setAllowNetwork] = useState33(true);
    const [allowFilesystem, setAllowFilesystem] = useState33(true);
    const [allowedImports, setAllowedImports] = useState33("");
    const [blockedImports, setBlockedImports] = useState33("");
    const [saving, setSaving] = useState33(false);
    const [saved, setSaved] = useState33(false);
    const [error, setError] = useState33(null);
    useEffect26(() => {
      const handler = (msg) => {
        if (msg.type === "safety:get_result") {
          if (msg.policy) {
            setPolicy(msg.policy);
            setAllowNetwork(msg.policy.allow_network !== false);
            setAllowFilesystem(msg.policy.allow_filesystem !== false);
            if (msg.policy.allowed_imports)
              setAllowedImports(msg.policy.allowed_imports.join(", "));
            if (msg.policy.blocked_imports)
              setBlockedImports(msg.policy.blocked_imports.join(", "));
          }
          cacaoWs.removeListener(handler);
        }
      };
      cacaoWs.addListener(handler);
      cacaoWs.send({ type: "safety:get" });
      return () => cacaoWs.removeListener(handler);
    }, []);
    useEffect26(() => {
      if (initialPreset && initialPreset !== "custom") {
        applyPreset(initialPreset);
      }
    }, [initialPreset]);
    const applyPreset = useCallback22((presetId) => {
      setActivePreset(presetId);
      setSaved(false);
      switch (presetId) {
        case "permissive":
          setAllowNetwork(true);
          setAllowFilesystem(true);
          setAllowedImports("");
          setBlockedImports("");
          break;
        case "network_only":
          setAllowNetwork(true);
          setAllowFilesystem(false);
          setAllowedImports("");
          setBlockedImports("");
          break;
        case "filesystem_only":
          setAllowNetwork(false);
          setAllowFilesystem(true);
          setAllowedImports("");
          setBlockedImports("");
          break;
        case "restrictive":
          setAllowNetwork(false);
          setAllowFilesystem(false);
          setAllowedImports("");
          setBlockedImports("");
          break;
      }
      if (presetId !== "custom") {
        savePolicy(presetId);
      }
    }, []);
    const savePolicy = useCallback22((presetOverride) => {
      setSaving(true);
      setError(null);
      setSaved(false);
      const policyConfig = presetOverride && presetOverride !== "custom" ? { preset: presetOverride } : {
        allow_network: allowNetwork,
        allow_filesystem: allowFilesystem,
        allowed_imports: allowedImports ? allowedImports.split(",").map((s) => s.trim()).filter(Boolean) : [],
        blocked_imports: blockedImports ? blockedImports.split(",").map((s) => s.trim()).filter(Boolean) : []
      };
      const handler = (msg) => {
        if (msg.type === "safety:set_result") {
          setSaving(false);
          setSaved(true);
          if (msg.policy)
            setPolicy(msg.policy);
          cacaoWs.removeListener(handler);
          setTimeout(() => setSaved(false), 2e3);
        } else if (msg.type === "safety:set_error") {
          setSaving(false);
          setError(msg.error);
          cacaoWs.removeListener(handler);
        }
      };
      cacaoWs.addListener(handler);
      cacaoWs.send({ type: "safety:set", policy: policyConfig });
    }, [allowNetwork, allowFilesystem, allowedImports, blockedImports]);
    return h70(
      "div",
      { className: `cacao-safety-policy ${compact ? "cacao-safety-policy-compact" : ""}` },
      // Header
      h70(
        "div",
        { className: "cacao-safety-policy-header" },
        h70("h3", { className: "cacao-safety-policy-title" }, title),
        saved && h70("span", { className: "cacao-badge", style: { background: "var(--success-color, #22c55e)" } }, "Saved")
      ),
      // Presets
      show_presets && h70(
        "div",
        { className: "cacao-safety-policy-presets" },
        ...PRESETS.map(
          (p) => h70(
            "button",
            {
              key: p.id,
              className: `cacao-safety-policy-preset ${activePreset === p.id ? "cacao-safety-policy-preset-active" : ""}`,
              onClick: () => applyPreset(p.id)
            },
            h70("span", { className: "cacao-safety-policy-preset-icon" }, p.icon),
            h70("span", { className: "cacao-safety-policy-preset-label" }, p.label),
            !compact && h70("span", { className: "cacao-safety-policy-preset-desc" }, p.desc)
          )
        )
      ),
      // Advanced configuration
      show_advanced && h70(
        "div",
        { className: "cacao-safety-policy-advanced" },
        // Toggles
        h70(
          "div",
          { className: "cacao-safety-policy-toggles" },
          h70(
            "label",
            { className: "cacao-safety-policy-toggle" },
            h70("input", {
              type: "checkbox",
              checked: allowNetwork,
              onChange: (e) => {
                setAllowNetwork(e.target.checked);
                setActivePreset("custom");
              }
            }),
            h70("span", null, "Allow Network Access")
          ),
          h70(
            "label",
            { className: "cacao-safety-policy-toggle" },
            h70("input", {
              type: "checkbox",
              checked: allowFilesystem,
              onChange: (e) => {
                setAllowFilesystem(e.target.checked);
                setActivePreset("custom");
              }
            }),
            h70("span", null, "Allow Filesystem Access")
          )
        ),
        // Import controls
        h70(
          "div",
          { className: "cacao-safety-policy-imports" },
          h70(
            "div",
            { className: "cacao-safety-policy-field" },
            h70("label", null, "Allowed Imports (comma-separated, empty = all)"),
            h70("input", {
              className: "cacao-input",
              value: allowedImports,
              placeholder: "json, re, datetime, math",
              onChange: (e) => {
                setAllowedImports(e.target.value);
                setActivePreset("custom");
              }
            })
          ),
          h70(
            "div",
            { className: "cacao-safety-policy-field" },
            h70("label", null, "Blocked Imports (comma-separated)"),
            h70("input", {
              className: "cacao-input",
              value: blockedImports,
              placeholder: "os, subprocess, sys",
              onChange: (e) => {
                setBlockedImports(e.target.value);
                setActivePreset("custom");
              }
            })
          )
        ),
        // Save button (for custom config)
        activePreset === "custom" && h70("button", {
          className: "cacao-btn cacao-btn-primary",
          onClick: () => savePolicy(),
          disabled: saving
        }, saving ? "Saving..." : "Apply Policy")
      ),
      // Error
      error && h70("div", { className: "cacao-alert cacao-alert-error" }, error),
      // Current policy summary
      policy && h70(
        "div",
        { className: "cacao-safety-policy-summary" },
        h70("small", null, "Active: "),
        h70("span", { className: "cacao-badge cacao-badge-sm" }, policy.allow_network ? "Network \u2713" : "Network \u2717"),
        h70("span", { className: "cacao-badge cacao-badge-sm" }, policy.allow_filesystem ? "Filesystem \u2713" : "Filesystem \u2717"),
        policy.allowed_imports && h70(
          "span",
          { className: "cacao-badge cacao-badge-sm" },
          `${policy.allowed_imports.length} allowed imports`
        )
      )
    );
  }

  // src/components/form/SearchInput.js
  init_static_runtime();
  var { createElement: h71, useState: useState34, useEffect: useEffect27, useRef: useRef22, useCallback: useCallback23 } = React;
  function SearchInput({ props }) {
    const {
      placeholder = "Search...",
      signal: signalRef,
      debounce = 300,
      size = "md",
      clearable = true,
      on_search,
      icon = true
    } = props;
    const signalName = signalRef?.__signal__;
    const [value, setValue] = useState34("");
    const timerRef = useRef22(null);
    const inputRef = useRef22(null);
    useEffect27(() => {
      if (!signalName)
        return;
      if (isStaticMode()) {
        const initial2 = staticSignals.get(signalName);
        if (initial2 !== void 0)
          setValue(initial2);
        return;
      }
      const unsubscribe = cacaoWs.subscribe((signals) => {
        if (signals[signalName] !== void 0) {
          setValue(signals[signalName]);
        }
      });
      const initial = cacaoWs.getSignal(signalName);
      if (initial !== void 0)
        setValue(initial);
      return unsubscribe;
    }, [signalName]);
    const emitValue = useCallback23((val) => {
      if (signalName) {
        if (isStaticMode()) {
          staticSignals.set(signalName, val);
        } else {
          cacaoWs.send({ type: "signal_update", name: signalName, value: val });
        }
      }
      if (on_search) {
        const eventName = on_search.__event__ || on_search;
        if (isStaticMode()) {
          Promise.resolve().then(() => (init_static_runtime(), static_runtime_exports)).then((m2) => m2.staticDispatcher(eventName, { value: val }));
        } else {
          cacaoWs.send({ type: "event", name: eventName, data: { value: val } });
        }
      }
    }, [signalName, on_search]);
    const handleInput = useCallback23((e) => {
      const val = e.target.value;
      setValue(val);
      if (timerRef.current)
        clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => emitValue(val), debounce);
    }, [debounce, emitValue]);
    const handleClear = useCallback23(() => {
      setValue("");
      emitValue("");
      inputRef.current?.focus();
    }, [emitValue]);
    const handleKeyDown = useCallback23((e) => {
      if (e.key === "Escape" && value) {
        e.preventDefault();
        handleClear();
      }
    }, [value, handleClear]);
    const sizeClass = size !== "md" ? " c-search--" + size : "";
    return h71("div", { className: "c-search" + sizeClass }, [
      icon && h71("svg", {
        key: "icon",
        className: "c-search-icon",
        viewBox: "0 0 16 16",
        fill: "none",
        stroke: "currentColor",
        strokeWidth: "1.5",
        width: size === "sm" ? 12 : 14,
        height: size === "sm" ? 12 : 14
      }, h71("path", { d: "M11.5 11.5L14 14M6.5 12A5.5 5.5 0 106.5 1a5.5 5.5 0 000 11z" })),
      h71("input", {
        key: "input",
        ref: inputRef,
        type: "text",
        className: "c-search-input",
        placeholder,
        value,
        onInput: handleInput,
        onKeyDown: handleKeyDown
      }),
      clearable && value && h71("button", {
        key: "clear",
        className: "c-search-clear",
        onClick: handleClear,
        "aria-label": "Clear search",
        type: "button"
      }, "\xD7")
    ]);
  }

  // src/components/form/Select.js
  var { createElement: h72, useState: useState35, useEffect: useEffect28 } = React;
  function Select({ props }) {
    const {
      label,
      options = [],
      placeholder = "Select...",
      signal,
      on_change,
      disabled = false
    } = props;
    const [value, setValue] = useState35("");
    const signalName = signal?.__signal__;
    useEffect28(() => {
      if (signalName) {
        const unsubscribe = cacaoWs.subscribe((signals) => {
          if (signals[signalName] !== void 0) {
            setValue(signals[signalName]);
          }
        });
        const initial = cacaoWs.getSignal(signalName);
        if (initial !== void 0) {
          setValue(initial);
        }
        return unsubscribe;
      }
    }, [signalName]);
    const handleChange = (e) => {
      const newValue = e.target.value;
      setValue(newValue);
      const eventName = on_change?.__event__ || on_change;
      if (eventName) {
        cacaoWs.sendEvent(eventName, { value: newValue });
      }
    };
    return h72("div", { className: "select-container" }, [
      label && h72("label", { className: "select-label", key: "label" }, label),
      h72("select", {
        className: "select",
        value,
        onChange: handleChange,
        disabled,
        key: "select"
      }, [
        h72("option", { value: "", disabled: true, key: "placeholder" }, placeholder),
        ...options.map((o, i) => h72("option", {
          key: i,
          value: o.value || o.label || o
        }, o.label || o))
      ])
    ]);
  }

  // src/components/form/Series.js
  init_static_runtime();
  var { createElement: h73, useState: useState36, useEffect: useEffect29, useRef: useRef23, useCallback: useCallback24 } = React;
  function Series({ props }) {
    const {
      interfaces = [],
      submit_label = "Run"
    } = props;
    const [currentStep, setCurrentStep] = useState36(0);
    const [stepOutputs, setStepOutputs] = useState36({});
    const [stepErrors, setStepErrors] = useState36({});
    const [loading, setLoading] = useState36(false);
    const [values, setValues] = useState36(() => {
      if (!interfaces[0])
        return {};
      const initial = {};
      interfaces[0].inputs.forEach((inp) => {
        initial[inp.param_name] = inp.default != null ? inp.default : "";
      });
      return initial;
    });
    useEffect29(() => {
      if (!cacaoWs.ws)
        return;
      const handler = (event) => {
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }
        const stepIndex = interfaces.findIndex((iface) => iface.id === msg.id);
        if (stepIndex === -1)
          return;
        if (msg.type === "interface:result") {
          setStepOutputs((prev) => ({ ...prev, [stepIndex]: msg.output }));
          if (stepIndex < interfaces.length - 1) {
            const nextIface = interfaces[stepIndex + 1];
            const nextInputs = {};
            if (msg.output && nextIface.param_names.length > 0) {
              const outputVal = msg.output.value;
              if (typeof outputVal === "object" && outputVal !== null && !Array.isArray(outputVal)) {
                nextIface.param_names.forEach((name) => {
                  nextInputs[name] = outputVal[name] !== void 0 ? outputVal[name] : "";
                });
              } else {
                nextInputs[nextIface.param_names[0]] = typeof outputVal === "string" ? outputVal : JSON.stringify(outputVal);
              }
            }
            setCurrentStep(stepIndex + 1);
            if (cacaoWs.ws && cacaoWs.connected) {
              cacaoWs.ws.send(JSON.stringify({
                type: "interface:submit",
                id: nextIface.id,
                inputs: nextInputs
              }));
            }
          } else {
            setLoading(false);
            setCurrentStep(stepIndex);
          }
        } else if (msg.type === "interface:error") {
          setStepErrors((prev) => ({ ...prev, [stepIndex]: msg }));
          setLoading(false);
        }
      };
      cacaoWs.ws.addEventListener("message", handler);
      return () => cacaoWs.ws?.removeEventListener("message", handler);
    }, [interfaces]);
    const updateValue = useCallback24((paramName, val) => {
      setValues((prev) => ({ ...prev, [paramName]: val }));
    }, []);
    const handleSubmit = useCallback24(() => {
      setStepOutputs({});
      setStepErrors({});
      setCurrentStep(0);
      setLoading(true);
      if (cacaoWs.ws && cacaoWs.connected && interfaces[0]) {
        cacaoWs.ws.send(JSON.stringify({
          type: "interface:submit",
          id: interfaces[0].id,
          inputs: values
        }));
      }
    }, [values, interfaces]);
    return h73("div", { className: "c-series" }, [
      // Header with step indicators
      h73(
        "div",
        { className: "c-series__steps", key: "steps" },
        interfaces.map(
          (iface, i) => h73("div", {
            className: `c-series__step ${i === currentStep ? "c-series__step--active" : ""} ${stepOutputs[i] ? "c-series__step--done" : ""} ${stepErrors[i] ? "c-series__step--error" : ""}`,
            key: i
          }, [
            h73("span", { className: "c-series__step-num", key: "num" }, String(i + 1)),
            h73("span", { className: "c-series__step-title", key: "title" }, iface.title || `Step ${i + 1}`),
            i < interfaces.length - 1 && h73("span", { className: "c-series__step-arrow", key: "arrow" }, "\u2192")
          ])
        )
      ),
      // Input panel (only for first function)
      h73("div", { className: "c-series__input", key: "input" }, [
        ...interfaces[0].inputs.map(
          (inp) => h73(SeriesInputField, {
            key: inp.param_name,
            spec: inp,
            value: values[inp.param_name],
            onChange: (val) => updateValue(inp.param_name, val)
          })
        ),
        !isStaticMode() && h73("button", {
          className: "btn btn-primary c-series__submit",
          onClick: handleSubmit,
          disabled: loading,
          key: "submit"
        }, loading ? "Running..." : submit_label)
      ]),
      // Output panels for each step
      h73(
        "div",
        { className: "c-series__outputs", key: "outputs" },
        interfaces.map(
          (iface, i) => h73("div", {
            className: `c-series__output ${stepOutputs[i] ? "c-series__output--has-result" : ""}`,
            key: i
          }, [
            h73("div", { className: "c-series__output-header", key: "header" }, iface.title || `Step ${i + 1}`),
            stepOutputs[i] ? h73(SeriesOutputDisplay, { output: stepOutputs[i], key: "result" }) : stepErrors[i] ? h73("div", { className: "c-iface__error", key: "error" }, [
              h73("strong", { key: "type" }, stepErrors[i].error),
              h73("span", { key: "msg" }, `: ${stepErrors[i].message}`)
            ]) : loading && i <= currentStep ? h73(
              "div",
              { className: "c-iface__loading", key: "loading" },
              h73("span", { className: "c-iface__spinner c-iface__spinner--lg" })
            ) : h73("div", { className: "c-iface__empty", key: "empty" }, "Waiting...")
          ])
        )
      )
    ]);
  }
  function SeriesInputField({ spec, value, onChange }) {
    const { component, label, param_name, type: inputType, options, min, max, step, placeholder } = spec;
    const inputId = `series-${param_name}`;
    const wrapper = (children) => h73("div", { className: "c-iface__field" }, [
      h73("label", { className: "c-input-label", htmlFor: inputId, key: "label" }, label),
      children
    ]);
    switch (component) {
      case "Checkbox":
        return wrapper(h73("input", { type: "checkbox", id: inputId, checked: !!value, onChange: (e) => onChange(e.target.checked), key: "input" }));
      case "Select":
        return wrapper(h73(
          "select",
          { className: "c-input", id: inputId, value: value ?? "", onChange: (e) => onChange(e.target.value), key: "input" },
          (options || []).map((opt) => h73("option", { value: opt, key: opt }, String(opt)))
        ));
      case "Textarea":
        return wrapper(h73("textarea", { className: "c-input", id: inputId, value: value ?? "", rows: 3, onChange: (e) => onChange(e.target.value), key: "input" }));
      default:
        return wrapper(h73("input", { type: inputType || "text", className: "c-input", id: inputId, value: value ?? "", placeholder: placeholder || "", onChange: (e) => onChange(e.target.value), key: "input" }));
    }
  }
  function SeriesOutputDisplay({ output }) {
    if (!output)
      return null;
    const { type, value } = output;
    switch (type) {
      case "text":
        return h73("pre", { className: "c-iface__text" }, String(value));
      case "metric":
        return h73("span", { className: "c-iface__metric-value", style: { fontSize: "1.5rem" } }, String(value));
      case "json":
        return h73("pre", { className: "c-iface__json" }, JSON.stringify(value, null, 2));
      case "image":
        return h73("img", { src: value, className: "c-iface__image", alt: "Output" });
      case "table":
        if (!Array.isArray(value) || !value.length)
          return h73("span", null, "Empty");
        const cols = Object.keys(value[0]);
        return h73("table", { className: "c-iface__table" }, [
          h73("thead", { key: "h" }, h73("tr", null, cols.map((c) => h73("th", { key: c }, c)))),
          h73("tbody", { key: "b" }, value.slice(0, 20).map((row, i) => h73("tr", { key: i }, cols.map((c) => h73("td", { key: c }, String(row[c] ?? ""))))))
        ]);
      default:
        return h73("pre", { className: "c-iface__text" }, String(value));
    }
  }

  // src/components/form/SkillBrowser.js
  var { createElement: h74, useState: useState37, useEffect: useEffect30, useCallback: useCallback25, useRef: useRef24 } = React;
  function SkillBrowser({ props }) {
    const {
      title = "Skill Browser",
      show_search = true,
      show_categories = true,
      compact = false,
      on_select,
      height = "500px"
    } = props;
    const [index, setIndex] = useState37(null);
    const [loading, setLoading] = useState37(true);
    const [error, setError] = useState37(null);
    const [search, setSearch] = useState37("");
    const [searchResults, setSearchResults] = useState37(null);
    const [selectedSkill, setSelectedSkill] = useState37(null);
    const [skillDetails, setSkillDetails] = useState37(null);
    const [detailsLoading, setDetailsLoading] = useState37(false);
    const searchTimeout = useRef24(null);
    useEffect30(() => {
      const handler = (msg) => {
        if (msg.type === "skill:browse_result") {
          setIndex(msg.index);
          setLoading(false);
          cacaoWs.removeListener(handler);
        } else if (msg.type === "skill:browse_error") {
          setError(msg.error);
          setLoading(false);
          cacaoWs.removeListener(handler);
        }
      };
      cacaoWs.addListener(handler);
      cacaoWs.send({ type: "skill:browse" });
      return () => cacaoWs.removeListener(handler);
    }, []);
    const handleSearch = useCallback25((query) => {
      setSearch(query);
      if (searchTimeout.current)
        clearTimeout(searchTimeout.current);
      if (!query.trim()) {
        setSearchResults(null);
        return;
      }
      searchTimeout.current = setTimeout(() => {
        const handler = (msg) => {
          if (msg.type === "skill:search_result") {
            setSearchResults(msg.results);
            cacaoWs.removeListener(handler);
          } else if (msg.type === "skill:search_error") {
            setSearchResults(null);
            cacaoWs.removeListener(handler);
          }
        };
        cacaoWs.addListener(handler);
        cacaoWs.send({ type: "skill:search", query, limit: 30 });
      }, 300);
    }, []);
    const handleSelectSkill = useCallback25((name) => {
      setSelectedSkill(name);
      setDetailsLoading(true);
      setSkillDetails(null);
      const handler = (msg) => {
        if (msg.type === "skill:details_result") {
          setSkillDetails(msg.details && msg.details.length > 0 ? msg.details[0] : null);
          setDetailsLoading(false);
          cacaoWs.removeListener(handler);
        } else if (msg.type === "skill:details_error") {
          setDetailsLoading(false);
          cacaoWs.removeListener(handler);
        }
      };
      cacaoWs.addListener(handler);
      cacaoWs.send({ type: "skill:details", names: [name] });
      if (on_select) {
        cacaoWs.sendEvent(on_select, { skill: name });
      }
    }, [on_select]);
    const renderSkillList = () => {
      if (loading)
        return h74("div", { className: "cacao-skill-browser-loading" }, "Loading skills...");
      if (error)
        return h74("div", { className: "cacao-alert cacao-alert-error" }, error);
      if (!index)
        return h74("div", { className: "cacao-skill-browser-empty" }, "No skills found");
      if (searchResults) {
        return h74(
          "div",
          { className: "cacao-skill-browser-results" },
          searchResults.length === 0 ? h74("div", { className: "cacao-skill-browser-empty" }, "No matching skills") : searchResults.map((r) => renderSkillItem(
            typeof r === "string" ? r : r.name || r,
            typeof r === "object" ? r.description : ""
          ))
        );
      }
      const plugins = index.plugins || {};
      if (show_categories) {
        return h74(
          "div",
          { className: "cacao-skill-browser-categories" },
          ...Object.entries(plugins).map(
            ([pluginName, info]) => h74(
              "div",
              { key: pluginName, className: "cacao-skill-browser-category" },
              h74(
                "div",
                { className: "cacao-skill-browser-category-header" },
                h74("span", { className: "cacao-skill-browser-category-name" }, pluginName),
                h74("span", { className: "cacao-badge cacao-badge-sm" }, String(info.tool_count || Object.keys(info.tools || {}).length))
              ),
              h74(
                "div",
                { className: "cacao-skill-browser-category-tools" },
                ...Object.entries(info.tools || {}).map(
                  ([name, desc]) => renderSkillItem(name, desc)
                )
              )
            )
          )
        );
      }
      const allTools = [];
      Object.values(plugins).forEach((info) => {
        Object.entries(info.tools || {}).forEach(([name, desc]) => {
          allTools.push({ name, description: desc });
        });
      });
      return h74(
        "div",
        { className: "cacao-skill-browser-results" },
        ...allTools.map((t) => renderSkillItem(t.name, t.description))
      );
    };
    const renderSkillItem = (name, description) => {
      const isSelected = selectedSkill === name;
      return h74(
        "div",
        {
          key: name,
          className: `cacao-skill-browser-item ${isSelected ? "cacao-skill-browser-item-selected" : ""}`,
          onClick: () => handleSelectSkill(name)
        },
        h74("div", { className: "cacao-skill-browser-item-name" }, name),
        !compact && description && h74("div", { className: "cacao-skill-browser-item-desc" }, description)
      );
    };
    const renderDetails = () => {
      if (!selectedSkill)
        return h74("div", { className: "cacao-skill-browser-detail-empty" }, "Select a skill to see details");
      if (detailsLoading)
        return h74("div", { className: "cacao-skill-browser-loading" }, "Loading details...");
      if (!skillDetails)
        return h74("div", { className: "cacao-skill-browser-detail-empty" }, "No details available");
      const d = skillDetails;
      return h74(
        "div",
        { className: "cacao-skill-browser-detail" },
        h74("h4", { className: "cacao-skill-browser-detail-name" }, d.name || selectedSkill),
        d.description && h74("p", { className: "cacao-skill-browser-detail-desc" }, d.description),
        // Parameters
        d.parameters && h74(
          "div",
          { className: "cacao-skill-browser-detail-section" },
          h74("h5", null, "Parameters"),
          h74("pre", { className: "cacao-skill-browser-detail-schema" }, JSON.stringify(d.parameters, null, 2))
        ),
        // Examples
        d.examples && d.examples.length > 0 && h74(
          "div",
          { className: "cacao-skill-browser-detail-section" },
          h74("h5", null, "Examples"),
          ...d.examples.map(
            (ex, i) => h74(
              "pre",
              { key: i, className: "cacao-skill-browser-detail-example" },
              typeof ex === "string" ? ex : JSON.stringify(ex, null, 2)
            )
          )
        ),
        // Tags
        d.tags && d.tags.length > 0 && h74(
          "div",
          { className: "cacao-skill-browser-detail-tags" },
          ...d.tags.map((tag) => h74("span", { key: tag, className: "cacao-badge cacao-badge-outline cacao-badge-sm" }, tag))
        )
      );
    };
    return h74(
      "div",
      { className: `cacao-skill-browser ${compact ? "cacao-skill-browser-compact" : ""}`, style: { height } },
      // Header
      h74(
        "div",
        { className: "cacao-skill-browser-header" },
        h74("h3", { className: "cacao-skill-browser-title" }, title),
        index && h74("span", { className: "cacao-badge" }, `${index.total_count || 0} skills`)
      ),
      // Search
      show_search && h74(
        "div",
        { className: "cacao-skill-browser-search" },
        h74("input", {
          className: "cacao-input",
          type: "text",
          placeholder: "Search skills...",
          value: search,
          onChange: (e) => handleSearch(e.target.value)
        })
      ),
      // Content: list + details
      h74(
        "div",
        { className: "cacao-skill-browser-content" },
        h74("div", { className: "cacao-skill-browser-list" }, renderSkillList()),
        !compact && h74("div", { className: "cacao-skill-browser-details" }, renderDetails())
      )
    );
  }

  // src/components/form/SkillRunner.js
  var { createElement: h75, useState: useState38, useRef: useRef25, useCallback: useCallback26 } = React;
  function schemaToFields(schema) {
    if (!schema || !schema.properties)
      return [];
    const required = new Set(schema.required || []);
    return Object.entries(schema.properties).map(([name, prop]) => ({
      name,
      type: prop.type || "string",
      description: prop.description || "",
      default: prop.default,
      required: required.has(name),
      enum: prop.enum || null
    }));
  }
  function FieldInput({ field, value, onChange }) {
    const { name, type, description, required, enum: enumValues } = field;
    if (enumValues) {
      return h75(
        "select",
        {
          className: "cacao-input",
          value: value || "",
          onChange: (e) => onChange(name, e.target.value)
        },
        h75("option", { value: "" }, `Select ${name}...`),
        ...enumValues.map((v2) => h75("option", { key: v2, value: v2 }, v2))
      );
    }
    if (type === "boolean") {
      return h75(
        "label",
        { className: "cacao-skill-checkbox-label" },
        h75("input", {
          type: "checkbox",
          checked: !!value,
          onChange: (e) => onChange(name, e.target.checked)
        }),
        h75("span", null, name)
      );
    }
    if (type === "number" || type === "integer") {
      return h75("input", {
        className: "cacao-input",
        type: "number",
        value: value ?? "",
        placeholder: description || name,
        step: type === "integer" ? 1 : "any",
        onChange: (e) => onChange(name, e.target.value === "" ? "" : Number(e.target.value))
      });
    }
    if (type === "string" && description && description.toLowerCase().includes("text")) {
      return h75("textarea", {
        className: "cacao-input cacao-skill-textarea",
        value: value || "",
        placeholder: description || name,
        rows: 3,
        onChange: (e) => onChange(name, e.target.value)
      });
    }
    return h75("input", {
      className: "cacao-input",
      type: "text",
      value: value || "",
      placeholder: description || name,
      onChange: (e) => onChange(name, e.target.value)
    });
  }
  function SkillRunner({ props }) {
    const {
      skill_name,
      title = "Skill",
      description = "",
      descriptor = {},
      show_metadata = true,
      show_timing = true,
      height = "auto"
    } = props;
    const fields = schemaToFields(descriptor.input_schema);
    const [values, setValues] = useState38(() => {
      const initial = {};
      fields.forEach((f) => {
        if (f.default !== void 0)
          initial[f.name] = f.default;
      });
      return initial;
    });
    const [result, setResult] = useState38(null);
    const [error, setError] = useState38(null);
    const [loading, setLoading] = useState38(false);
    const [duration, setDuration] = useState38(null);
    const invokeId = useRef25(`skill_${Date.now()}_${Math.random().toString(36).slice(2)}`);
    const handleChange = useCallback26((name, value) => {
      setValues((prev) => ({ ...prev, [name]: value }));
    }, []);
    const handleInvoke = useCallback26(() => {
      if (loading)
        return;
      setLoading(true);
      setError(null);
      setResult(null);
      setDuration(null);
      const handler = (msg) => {
        if (msg.id !== invokeId.current)
          return;
        if (msg.type === "skill:result") {
          setResult(msg.value);
          setDuration(msg.duration_ms);
          setLoading(false);
          if (!msg.success && msg.error)
            setError(msg.error);
          cacaoWs.removeListener(handler);
        } else if (msg.type === "skill:error") {
          setError(msg.error);
          setLoading(false);
          cacaoWs.removeListener(handler);
        }
      };
      cacaoWs.addListener(handler);
      cacaoWs.send({
        type: "skill:invoke",
        id: invokeId.current,
        skill_name,
        inputs: values
      });
      invokeId.current = `skill_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    }, [loading, skill_name, values]);
    const riskColors = {
      SAFE: "var(--success-color, #22c55e)",
      MODERATE: "var(--warning-color, #f59e0b)",
      DANGEROUS: "var(--error-color, #ef4444)",
      CRITICAL: "var(--error-color, #ef4444)"
    };
    return h75(
      "div",
      { className: "cacao-skill-runner", style: height !== "auto" ? { height } : void 0 },
      // Header
      h75(
        "div",
        { className: "cacao-skill-runner-header" },
        h75(
          "div",
          { className: "cacao-skill-runner-title-row" },
          h75("h3", { className: "cacao-skill-runner-title" }, title),
          descriptor.version && h75("span", { className: "cacao-badge" }, `v${descriptor.version}`),
          descriptor.risk_level && descriptor.risk_level !== "AUTO" && h75("span", {
            className: "cacao-badge",
            style: { background: riskColors[descriptor.risk_level] || "var(--text-secondary)" }
          }, descriptor.risk_level)
        ),
        description && h75("p", { className: "cacao-skill-runner-description" }, description),
        // Metadata
        show_metadata && (descriptor.category || descriptor.tags && descriptor.tags.length > 0) && h75(
          "div",
          { className: "cacao-skill-runner-meta" },
          descriptor.category && h75("span", { className: "cacao-badge cacao-badge-outline" }, descriptor.category),
          ...(descriptor.tags || []).map(
            (tag) => h75("span", { key: tag, className: "cacao-badge cacao-badge-outline cacao-badge-sm" }, tag)
          ),
          descriptor.requires_network && h75("span", { className: "cacao-badge cacao-badge-outline cacao-badge-sm" }, "network"),
          descriptor.requires_filesystem && h75("span", { className: "cacao-badge cacao-badge-outline cacao-badge-sm" }, "filesystem")
        )
      ),
      // Body
      h75(
        "div",
        { className: "cacao-skill-runner-body" },
        // Input fields
        h75(
          "div",
          { className: "cacao-skill-runner-inputs" },
          fields.length > 0 ? fields.map(
            (field) => h75(
              "div",
              { key: field.name, className: "cacao-skill-runner-field" },
              h75(
                "label",
                { className: "cacao-skill-runner-label" },
                field.name,
                field.required && h75("span", { className: "cacao-skill-required" }, " *")
              ),
              field.description && h75("small", { className: "cacao-skill-runner-hint" }, field.description),
              h75(FieldInput, { field, value: values[field.name], onChange: handleChange })
            )
          ) : h75("div", { className: "cacao-skill-runner-no-inputs" }, "This skill takes no inputs"),
          h75("button", {
            className: "cacao-btn cacao-btn-primary",
            onClick: handleInvoke,
            disabled: loading
          }, loading ? "Running..." : "Run Skill")
        ),
        // Output
        h75(
          "div",
          { className: "cacao-skill-runner-output" },
          h75("label", { className: "cacao-skill-runner-label" }, "Output"),
          error && h75("div", { className: "cacao-alert cacao-alert-error" }, error),
          result !== null && h75(
            "pre",
            { className: "cacao-skill-runner-result" },
            typeof result === "object" ? JSON.stringify(result, null, 2) : String(result)
          ),
          show_timing && duration !== null && h75(
            "div",
            { className: "cacao-skill-runner-timing" },
            h75("small", null, `Completed in ${duration.toFixed(1)}ms`)
          ),
          result === null && !error && !loading && h75(
            "div",
            { className: "cacao-skill-runner-placeholder" },
            "Run the skill to see output"
          )
        )
      )
    );
  }

  // src/components/form/Slider.js
  var { createElement: h76, useState: useState39, useEffect: useEffect31 } = React;
  function Slider({ props }) {
    const {
      label,
      min = 0,
      max = 100,
      step = 1,
      value: initialValue,
      signal,
      on_change
    } = props;
    const [value, setValue] = useState39(initialValue || min);
    const signalName = signal?.__signal__;
    useEffect31(() => {
      if (signalName) {
        const unsubscribe = cacaoWs.subscribe((signals) => {
          if (signals[signalName] !== void 0) {
            setValue(signals[signalName]);
          }
        });
        const initial = cacaoWs.getSignal(signalName);
        if (initial !== void 0) {
          setValue(initial);
        }
        return unsubscribe;
      }
    }, [signalName]);
    const handleChange = (e) => {
      const newValue = parseFloat(e.target.value);
      setValue(newValue);
      const eventName = on_change?.__event__ || on_change;
      if (eventName) {
        cacaoWs.sendEvent(eventName, { value: newValue });
      }
    };
    return h76("div", { className: "slider-container" }, [
      h76("label", { className: "slider-label", key: "label" }, `${label}: ${value}`),
      h76("input", {
        type: "range",
        className: "slider",
        min,
        max,
        step,
        value,
        onChange: handleChange,
        key: "input"
      })
    ]);
  }

  // src/components/form/SqlQuery.js
  var { createElement: h77, useState: useState40, useCallback: useCallback27, useEffect: useEffect32, useRef: useRef26 } = React;
  function SqlQuery({ props }) {
    const title = props.title;
    const editable = props.editable !== false;
    const autoRun = props.autoRun || false;
    const pageSize = props.pageSize || 25;
    const initialQuery = props.query || "";
    const [query, setQuery] = useState40(initialQuery);
    const [results, setResults] = useState40(null);
    const [columns, setColumns] = useState40([]);
    const [error, setError] = useState40(null);
    const [loading, setLoading] = useState40(false);
    const [page, setPage] = useState40(0);
    const ranAutoRun = useRef26(false);
    const runQuery = useCallback27(() => {
      if (!query.trim())
        return;
      setLoading(true);
      setError(null);
      cacaoWs.send({
        type: "sql_query",
        connection: props.connection,
        connType: props.connType,
        query: query.trim(),
        maxRows: props.maxRows || 1e3
      });
    }, [query, props.connection, props.connType, props.maxRows]);
    useEffect32(() => {
      const handler = (msg) => {
        if (msg.type === "sql:result") {
          setResults(msg.data || []);
          setColumns(msg.columns || []);
          setError(null);
          setLoading(false);
          setPage(0);
        } else if (msg.type === "sql:error") {
          setError(msg.error || "Unknown error");
          setResults(null);
          setLoading(false);
        }
      };
      cacaoWs.addListener(handler);
      return () => cacaoWs.removeListener(handler);
    }, []);
    useEffect32(() => {
      if (autoRun && initialQuery.trim() && !ranAutoRun.current) {
        ranAutoRun.current = true;
        setTimeout(() => runQuery(), 300);
      }
    }, [autoRun, initialQuery, runQuery]);
    const totalPages = results ? Math.ceil(results.length / pageSize) : 0;
    const pageData = results ? results.slice(page * pageSize, (page + 1) * pageSize) : [];
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        runQuery();
      }
    };
    return h77("div", { className: "sql-query" }, [
      title && h77("div", { className: "sql-query__title", key: "title" }, title),
      h77("div", { className: "sql-query__editor", key: "editor" }, [
        h77("textarea", {
          key: "textarea",
          className: "sql-query__input",
          value: query,
          readOnly: !editable,
          onInput: (e) => setQuery(e.target.value),
          onKeyDown: handleKeyDown,
          placeholder: "SELECT * FROM ...",
          rows: Math.min(query.split("\n").length + 1, 12),
          spellCheck: false
        }),
        h77("div", { className: "sql-query__actions", key: "actions" }, [
          h77("button", {
            key: "run",
            className: "sql-query__run-btn",
            onClick: runQuery,
            disabled: loading || !query.trim()
          }, loading ? "Running..." : "\u25B6 Run"),
          h77("span", { key: "hint", className: "sql-query__hint" }, "Ctrl+Enter to run")
        ])
      ]),
      error && h77("div", { className: "sql-query__error", key: "error" }, error),
      results && h77("div", { className: "sql-query__results", key: "results" }, [
        h77(
          "div",
          { className: "sql-query__results-info", key: "info" },
          `${results.length} row${results.length !== 1 ? "s" : ""} returned`
        ),
        h77(
          "div",
          { className: "df-table-wrap", key: "table" },
          h77("table", { className: "df-table df-table--striped" }, [
            h77(
              "thead",
              { key: "head" },
              h77("tr", null, columns.map(
                (c) => h77("th", { key: c, className: "df-th" }, c)
              ))
            ),
            h77("tbody", { key: "body" }, pageData.map(
              (row, i) => h77("tr", { key: i }, columns.map(
                (c) => h77("td", { key: c }, formatValue(row[c]))
              ))
            ))
          ])
        ),
        totalPages > 1 && h77("div", { className: "df-footer", key: "footer" }, [
          h77(
            "span",
            { className: "df-footer__info", key: "info" },
            `Showing ${page * pageSize + 1}\u2013${Math.min((page + 1) * pageSize, results.length)} of ${results.length}`
          ),
          h77("div", { className: "df-pagination", key: "pages" }, [
            h77("button", {
              key: "prev",
              className: "df-page-btn",
              disabled: page === 0,
              onClick: () => setPage((p) => p - 1)
            }, "\u2190"),
            h77("span", { key: "current", className: "df-page-info" }, `${page + 1} / ${totalPages}`),
            h77("button", {
              key: "next",
              className: "df-page-btn",
              disabled: page >= totalPages - 1,
              onClick: () => setPage((p) => p + 1)
            }, "\u2192")
          ])
        ])
      ])
    ]);
  }

  // src/components/form/Switch.js
  var { createElement: h78, useState: useState41 } = React;
  function Switch({ props }) {
    const { label, disabled = false, signal } = props;
    const [checked, setChecked] = useState41(false);
    const handleChange = () => {
      if (!disabled) {
        setChecked(!checked);
      }
    };
    return h78("label", { className: "c-switch-wrapper" }, [
      h78("span", { className: "c-switch-label", key: "label" }, label),
      h78(
        "button",
        {
          type: "button",
          className: `c-switch ${checked ? "active" : ""}`,
          disabled,
          onClick: handleChange,
          role: "switch",
          "aria-checked": checked,
          key: "switch"
        },
        h78("span", { className: "c-switch-thumb" })
      )
    ]);
  }

  // src/components/form/Tabs.js
  var { createElement: h79, useRef: useRef27, useState: useState42 } = React;
  function Tabs({ props, children }) {
    const tabs = children.filter((c) => c && c.props && c.props.type === "Tab");
    const defaultTab = props.default || tabs[0]?.props?.props?.tabKey;
    const [localTab, setLocalTab] = useState42(defaultTab);
    const current = localTab || defaultTab;
    const tabListRef = useRef27(null);
    const handleKeyDown = (e) => {
      const tabKeys = tabs.map((t) => t.props.props.tabKey);
      const currentIdx = tabKeys.indexOf(current);
      let nextIdx;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        nextIdx = (currentIdx + 1) % tabKeys.length;
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        nextIdx = (currentIdx - 1 + tabKeys.length) % tabKeys.length;
      } else if (e.key === "Home") {
        e.preventDefault();
        nextIdx = 0;
      } else if (e.key === "End") {
        e.preventDefault();
        nextIdx = tabKeys.length - 1;
      } else {
        return;
      }
      setLocalTab(tabKeys[nextIdx]);
      if (tabListRef.current) {
        const buttons = tabListRef.current.querySelectorAll('[role="tab"]');
        if (buttons[nextIdx])
          buttons[nextIdx].focus();
      }
    };
    const tabPanelId = "tabpanel-" + current;
    const tabId = (key) => "tab-" + key;
    return h79("div", null, [
      h79("div", { className: "tabs", key: "tabs", role: "tablist", ref: tabListRef }, tabs.map(
        (t) => h79("button", {
          className: "tab " + (t.props.props.tabKey === current ? "active" : ""),
          key: t.props.props.tabKey,
          id: tabId(t.props.props.tabKey),
          role: "tab",
          "aria-selected": t.props.props.tabKey === current,
          "aria-controls": t.props.props.tabKey === current ? tabPanelId : void 0,
          tabIndex: t.props.props.tabKey === current ? 0 : -1,
          onClick: () => setLocalTab(t.props.props.tabKey),
          onKeyDown: handleKeyDown
        }, t.props.props.label)
      )),
      h79(
        "div",
        { key: "content", className: "tab-content", role: "tabpanel", id: tabPanelId, "aria-labelledby": tabId(current) },
        tabs.find((t) => t.props.props.tabKey === current)
      )
    ]);
  }
  function Tab({ props, children }) {
    return h79("div", null, children);
  }

  // src/components/form/Textarea.js
  var { createElement: h80, useState: useState43, useEffect: useEffect33 } = React;
  function Textarea({ props }) {
    const {
      label,
      placeholder = "",
      rows = 4,
      disabled = false,
      signal,
      on_change
    } = props;
    const [value, setValue] = useState43("");
    const signalName = signal?.__signal__;
    useEffect33(() => {
      if (signalName) {
        const unsubscribe = cacaoWs.subscribe((signals) => {
          if (signals[signalName] !== void 0) {
            setValue(signals[signalName]);
          }
        });
        const initial = cacaoWs.getSignal(signalName);
        if (initial !== void 0) {
          setValue(initial);
        }
        return unsubscribe;
      }
    }, [signalName]);
    const handleChange = (e) => {
      const newValue = e.target.value;
      setValue(newValue);
      const eventName = on_change?.__event__ || on_change;
      if (eventName) {
        cacaoWs.sendEvent(eventName, { value: newValue });
      }
    };
    return h80("div", { className: "c-textarea-wrapper" }, [
      label && h80("label", { className: "c-textarea-label", key: "label" }, label),
      h80("textarea", {
        className: "c-textarea",
        placeholder,
        rows,
        disabled,
        value,
        onChange: handleChange,
        key: "textarea"
      })
    ]);
  }

  // src/components/form/ToolTimeline.js
  var { createElement: h81, useState: useState44, useEffect: useEffect34 } = React;
  function ToolTimeline({ props }) {
    const {
      agent_id = null,
      title = "Tool Call Timeline",
      height = "400px",
      show_args = true,
      show_results = true,
      show_cost = true,
      compact = false
    } = props;
    const [steps, setSteps] = useState44([]);
    const [expandedSteps, setExpandedSteps] = useState44(/* @__PURE__ */ new Set());
    useEffect34(() => {
      const handler = (msg) => {
        if (agent_id && msg.agent_id !== agent_id)
          return;
        if (msg.type === "agent:started") {
          setSteps([]);
          setExpandedSteps(/* @__PURE__ */ new Set());
        } else if (msg.type === "agent:step") {
          setSteps((prev) => {
            const existing = prev.findIndex((s) => s.id === msg.step.id);
            if (existing >= 0) {
              const updated = [...prev];
              updated[existing] = { ...msg.step, status: msg.status };
              return updated;
            }
            return [...prev, { ...msg.step, status: msg.status }];
          });
        }
      };
      cacaoWs.addListener(handler);
      return () => cacaoWs.removeListener(handler);
    }, [agent_id]);
    const toggleExpand = (stepId) => {
      setExpandedSteps((prev) => {
        const next = new Set(prev);
        if (next.has(stepId))
          next.delete(stepId);
        else
          next.add(stepId);
        return next;
      });
    };
    const getStepColor = (type) => {
      switch (type) {
        case "think":
          return "var(--accent-primary)";
        case "tool_call":
          return "#ffb74d";
        case "response":
          return "#81c784";
        case "error":
          return "var(--danger)";
        default:
          return "var(--text-muted)";
      }
    };
    const getStepLabel = (step) => {
      switch (step.type) {
        case "think":
          return "Reasoning";
        case "tool_call":
          return `Tool: ${step.tool_name || "unknown"}`;
        case "response":
          return "Final Response";
        case "error":
          return "Error";
        default:
          return step.type;
      }
    };
    const formatDuration = (d) => {
      if (!d || d <= 0)
        return "";
      if (d < 1)
        return `${(d * 1e3).toFixed(0)}ms`;
      return `${d.toFixed(1)}s`;
    };
    const renderStep = (step, index) => {
      const isExpanded = expandedSteps.has(step.id);
      const isActive = step.status === "running";
      const color = getStepColor(step.type);
      const hasExpandable = show_args && step.tool_args || show_results && step.tool_result || step.type === "think" && step.content || step.type === "response" && step.content;
      return h81(
        "div",
        {
          className: `c-tool-timeline__step ${isActive ? "c-tool-timeline__step--active" : ""} ${compact ? "c-tool-timeline__step--compact" : ""}`,
          key: step.id || index
        },
        [
          // Timeline connector
          h81("div", { className: "c-tool-timeline__connector", key: "conn" }, [
            h81("div", {
              className: "c-tool-timeline__dot",
              style: { borderColor: color, background: isActive ? color : "transparent" },
              key: "dot"
            }),
            index < steps.length - 1 && h81("div", { className: "c-tool-timeline__line", key: "line" })
          ]),
          // Step content
          h81(
            "div",
            {
              className: "c-tool-timeline__step-body",
              onClick: hasExpandable ? () => toggleExpand(step.id) : void 0,
              style: hasExpandable ? { cursor: "pointer" } : void 0,
              key: "body"
            },
            [
              h81("div", { className: "c-tool-timeline__step-header", key: "hdr" }, [
                h81(
                  "span",
                  { className: "c-tool-timeline__step-label", style: { color }, key: "lbl" },
                  getStepLabel(step)
                ),
                h81("div", { className: "c-tool-timeline__step-meta", key: "meta" }, [
                  step.duration > 0 && h81(
                    "span",
                    { className: "c-tool-timeline__duration", key: "dur" },
                    formatDuration(step.duration)
                  ),
                  show_cost && step.tokens > 0 && h81(
                    "span",
                    { className: "c-tool-timeline__tokens", key: "tok" },
                    `${step.tokens.toLocaleString()} tok`
                  ),
                  show_cost && step.cost > 0 && h81(
                    "span",
                    { className: "c-tool-timeline__cost", key: "cost" },
                    `$${step.cost.toFixed(4)}`
                  ),
                  isActive && h81("span", { className: "c-tool-timeline__spinner", key: "spin" }),
                  hasExpandable && h81(
                    "span",
                    { className: "c-tool-timeline__expand-icon", key: "expand" },
                    isExpanded ? "\u25BC" : "\u25B6"
                  )
                ])
              ]),
              // Expandable details
              isExpanded && h81("div", { className: "c-tool-timeline__details", key: "details" }, [
                show_args && step.tool_args && h81("div", { className: "c-tool-timeline__detail-section", key: "args" }, [
                  h81("div", { className: "c-tool-timeline__detail-label", key: "lbl" }, "Arguments"),
                  h81(
                    "pre",
                    { className: "c-tool-timeline__detail-code", key: "code" },
                    JSON.stringify(step.tool_args, null, 2)
                  )
                ]),
                show_results && step.tool_result && h81("div", { className: "c-tool-timeline__detail-section", key: "result" }, [
                  h81("div", { className: "c-tool-timeline__detail-label", key: "lbl" }, "Result"),
                  h81("pre", { className: "c-tool-timeline__detail-code", key: "code" }, step.tool_result)
                ]),
                (step.type === "think" || step.type === "response") && step.content && h81("div", { className: "c-tool-timeline__detail-section", key: "text" }, [
                  h81("div", { className: "c-tool-timeline__detail-label", key: "lbl" }, "Content"),
                  h81("div", { className: "c-tool-timeline__detail-text", key: "txt" }, step.content)
                ])
              ])
            ]
          )
        ]
      );
    };
    return h81("div", { className: "c-tool-timeline", style: { height } }, [
      // Header
      title && h81("div", { className: "c-tool-timeline__header", key: "header" }, title),
      // Steps
      h81("div", { className: "c-tool-timeline__steps", key: "steps" }, [
        steps.length === 0 && h81(
          "div",
          { className: "c-tool-timeline__empty", key: "empty" },
          "No agent steps yet."
        ),
        ...steps.map(renderStep)
      ])
    ]);
  }

  // src/components/charts/index.js
  var charts_exports = {};
  __export(charts_exports, {
    AreaChart: () => AreaChart,
    BarChart: () => BarChart,
    FunnelChart: () => FunnelChart,
    GaugeChart: () => GaugeChart,
    HeatmapChart: () => HeatmapChart,
    LineChart: () => LineChart,
    PieChart: () => PieChart,
    PlotlyChart: () => PlotlyChart,
    RadarChart: () => RadarChart,
    ScatterChart: () => ScatterChart,
    TreemapChart: () => TreemapChart
  });

  // src/components/charts/AreaChart.js
  var { createElement: h82 } = React;
  function AreaChart({ props }) {
    const data = props.data || [];
    const yKeys = props.yFields || [];
    const xField = props.xField;
    const chartData = {
      labels: data.map((d) => d[xField]),
      datasets: yKeys.map((k2, i) => ({
        label: k2,
        data: data.map((d) => d[k2]),
        borderColor: COLORS[i % COLORS.length],
        backgroundColor: COLORS[i % COLORS.length] + "40",
        fill: true,
        tension: 0.4
      }))
    };
    return h82(ChartWrapper, { type: "line", data: chartData, height: props.height });
  }

  // src/components/charts/BarChart.js
  var { createElement: h83 } = React;
  function BarChart({ props }) {
    const data = props.data || [];
    const yKeys = props.yFields || [];
    const xField = props.xField;
    const chartData = {
      labels: data.map((d) => d[xField]),
      datasets: yKeys.map((k2, i) => ({
        label: k2,
        data: data.map((d) => d[k2]),
        backgroundColor: COLORS[i % COLORS.length]
      }))
    };
    return h83(ChartWrapper, {
      type: "bar",
      data: chartData,
      height: props.height,
      options: { indexAxis: props.horizontal ? "y" : "x" }
    });
  }

  // src/components/charts/FunnelChart.js
  var { createElement: h84 } = React;
  function FunnelChart({ props }) {
    const data = props.data || [];
    const chartData = {
      labels: data.map((d) => d[props.nameField]),
      datasets: [{
        data: data.map((d) => d[props.valueField]),
        backgroundColor: COLORS.slice(0, data.length)
      }]
    };
    return h84(ChartWrapper, {
      type: "bar",
      data: chartData,
      height: props.height,
      options: { indexAxis: "y" }
    });
  }

  // src/components/charts/GaugeChart.js
  var { createElement: h85 } = React;
  function GaugeChart({ props }) {
    const pct = props.value / (props.maxValue || 100) * 100;
    const angle = pct / 100 * 180;
    return h85("div", { className: "gauge-container" }, [
      h85("svg", { className: "gauge-svg", viewBox: "0 0 120 80", key: "svg" }, [
        h85("defs", { key: "defs" }, h85("linearGradient", { id: "gaugeGradient2", x1: "0%", y1: "0%", x2: "100%", y2: "0%" }, [
          h85("stop", { offset: "0%", stopColor: "var(--gradient-start)", key: "s1" }),
          h85("stop", { offset: "100%", stopColor: "var(--gradient-end)", key: "s2" })
        ])),
        h85("path", { d: "M10 70 A50 50 0 0 1 110 70", fill: "none", stroke: "var(--bg-tertiary)", strokeWidth: 12, strokeLinecap: "round", key: "bg" }),
        h85("path", { d: "M10 70 A50 50 0 0 1 110 70", fill: "none", stroke: "url(#gaugeGradient2)", strokeWidth: 12, strokeLinecap: "round", strokeDasharray: angle / 180 * 157 + " 157", key: "fill" })
      ]),
      h85("div", { className: "gauge-value", key: "value" }, props.format ? props.format.replace("{value}", props.value) : props.value + "%"),
      props.title && h85("div", { className: "gauge-title", key: "title" }, props.title)
    ]);
  }

  // src/components/charts/HeatmapChart.js
  var { createElement: h86 } = React;
  function HeatmapChart({ props }) {
    return h86("div", { className: "chart-placeholder" }, "[Heatmap: Coming soon]");
  }

  // src/components/charts/LineChart.js
  var { createElement: h87 } = React;
  function LineChart({ props }) {
    const data = props.data || [];
    const yKeys = props.yFields || [];
    const xField = props.xField;
    const chartData = {
      labels: data.map((d) => d[xField]),
      datasets: yKeys.map((k2, i) => ({
        label: k2,
        data: data.map((d) => d[k2]),
        borderColor: COLORS[i % COLORS.length],
        backgroundColor: props.area ? COLORS[i % COLORS.length] + "40" : "transparent",
        fill: props.area,
        tension: props.smooth ? 0.4 : 0
      }))
    };
    return h87(ChartWrapper, { type: "line", data: chartData, height: props.height });
  }

  // src/components/charts/PieChart.js
  var { createElement: h88 } = React;
  function PieChart({ props }) {
    const data = props.data || [];
    const chartData = {
      labels: data.map((d) => d[props.nameField]),
      datasets: [{
        data: data.map((d) => d[props.valueField]),
        backgroundColor: COLORS.slice(0, data.length)
      }]
    };
    return h88(ChartWrapper, {
      type: props.donut ? "doughnut" : "pie",
      data: chartData,
      height: props.height
    });
  }

  // src/components/charts/PlotlyChart.js
  var { createElement: h89, useRef: useRef28, useEffect: useEffect35, useState: useState45 } = React;
  var PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js";
  var plotlyLoaded = false;
  var plotlyLoading = false;
  var plotlyCallbacks = [];
  function loadPlotly() {
    if (plotlyLoaded)
      return Promise.resolve();
    if (plotlyLoading) {
      return new Promise((resolve) => plotlyCallbacks.push(resolve));
    }
    plotlyLoading = true;
    return new Promise((resolve, reject) => {
      plotlyCallbacks.push(resolve);
      const script = document.createElement("script");
      script.src = PLOTLY_CDN;
      script.onload = () => {
        plotlyLoaded = true;
        plotlyLoading = false;
        plotlyCallbacks.forEach((cb) => cb());
        plotlyCallbacks.length = 0;
      };
      script.onerror = () => {
        plotlyLoading = false;
        reject(new Error("Failed to load Plotly.js"));
      };
      document.head.appendChild(script);
    });
  }
  function PlotlyChart({ props }) {
    const containerRef = useRef28(null);
    const [ready, setReady] = useState45(plotlyLoaded);
    const figure = props.figure || {};
    const height = props.height || 400;
    const responsive = props.responsive !== false;
    const config = props.config || {};
    useEffect35(() => {
      if (!plotlyLoaded) {
        loadPlotly().then(() => setReady(true));
      }
    }, []);
    useEffect35(() => {
      if (!ready || !containerRef.current || !window.Plotly)
        return;
      const plotData = figure.data || [];
      const plotLayout = {
        ...figure.layout || {},
        height,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: getComputedStyle(document.documentElement).getPropertyValue("--text-primary").trim() || "#ccc" },
        margin: figure.layout?.margin || { l: 50, r: 30, t: 40, b: 40 }
      };
      const plotConfig = {
        responsive,
        displayModeBar: "hover",
        ...config
      };
      window.Plotly.react(containerRef.current, plotData, plotLayout, plotConfig);
      return () => {
        if (containerRef.current && window.Plotly) {
          window.Plotly.purge(containerRef.current);
        }
      };
    }, [ready, figure, height, responsive, config]);
    if (!ready) {
      return h89(
        "div",
        { className: "plotly-chart plotly-chart--loading" },
        h89("span", { className: "plotly-chart__spinner" }, "Loading Plotly...")
      );
    }
    return h89(
      "div",
      { className: "plotly-chart" },
      h89("div", { ref: containerRef, style: { width: "100%", minHeight: height } })
    );
  }

  // src/components/charts/RadarChart.js
  var { createElement: h90 } = React;
  function RadarChart({ props }) {
    const data = props.data || [];
    const valueFields = props.valueFields || [];
    const chartData = {
      labels: data.map((d) => d[props.categoryField]),
      datasets: valueFields.map((k2, i) => ({
        label: k2,
        data: data.map((d) => d[k2]),
        borderColor: COLORS[i % COLORS.length],
        backgroundColor: COLORS[i % COLORS.length] + "40",
        fill: props.fill
      }))
    };
    return h90(ChartWrapper, { type: "radar", data: chartData, height: props.height });
  }

  // src/components/charts/ScatterChart.js
  var { createElement: h91 } = React;
  function ScatterChart({ props }) {
    const data = props.data || [];
    const chartData = {
      datasets: [{
        label: "Data",
        data: data.map((d) => ({ x: d[props.xField], y: d[props.yField] })),
        backgroundColor: COLORS[0]
      }]
    };
    return h91(ChartWrapper, { type: "scatter", data: chartData, height: props.height });
  }

  // src/components/charts/TreemapChart.js
  var { createElement: h92 } = React;
  function TreemapChart({ props }) {
    return h92("div", { className: "chart-placeholder" }, "[Treemap: Coming soon]");
  }

  // src/components/App.js
  init_static_runtime();

  // src/components/core/NotificationCenter.js
  var { createElement: h93, useState: useState46, useEffect: useEffect36, useCallback: useCallback28, useRef: useRef29 } = React;
  var STORAGE_KEY2 = "cacao-notifications";
  function loadNotifications() {
    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY2) || "[]");
    } catch {
      return [];
    }
  }
  function saveNotifications(notifications) {
    sessionStorage.setItem(STORAGE_KEY2, JSON.stringify(notifications));
  }
  var _addNotification = null;
  var _notifId = 0;
  function addNotification(notification) {
    if (_addNotification) {
      _addNotification(notification);
    }
  }
  window.CacaoNotifications = { add: addNotification };
  function NotificationCenter() {
    const [notifications, setNotifications] = useState46(loadNotifications);
    const [open, setOpen] = useState46(false);
    const panelRef = useRef29(null);
    const unreadCount = notifications.filter((n) => !n.read).length;
    useEffect36(() => {
      _addNotification = (notif) => {
        const newNotif = {
          id: ++_notifId,
          title: notif.title || "",
          message: notif.message || "",
          variant: notif.variant || "info",
          timestamp: Date.now(),
          read: false
        };
        setNotifications((prev) => {
          const updated = [newNotif, ...prev].slice(0, 100);
          saveNotifications(updated);
          return updated;
        });
      };
      return () => {
        _addNotification = null;
      };
    }, []);
    useEffect36(() => {
      if (!open)
        return;
      const handleClick = (e) => {
        if (panelRef.current && !panelRef.current.contains(e.target)) {
          setOpen(false);
        }
      };
      document.addEventListener("mousedown", handleClick);
      return () => document.removeEventListener("mousedown", handleClick);
    }, [open]);
    const markAllRead = useCallback28(() => {
      setNotifications((prev) => {
        const updated = prev.map((n) => ({ ...n, read: true }));
        saveNotifications(updated);
        return updated;
      });
    }, []);
    const dismiss = useCallback28((id) => {
      setNotifications((prev) => {
        const updated = prev.filter((n) => n.id !== id);
        saveNotifications(updated);
        return updated;
      });
    }, []);
    const clearAll = useCallback28(() => {
      setNotifications([]);
      saveNotifications([]);
    }, []);
    const variantColors = {
      info: "var(--info)",
      success: "var(--success)",
      warning: "var(--warning)",
      error: "var(--danger)"
    };
    const timeAgo = (ts) => {
      const diff = Date.now() - ts;
      if (diff < 6e4)
        return "just now";
      if (diff < 36e5)
        return Math.floor(diff / 6e4) + "m ago";
      if (diff < 864e5)
        return Math.floor(diff / 36e5) + "h ago";
      return Math.floor(diff / 864e5) + "d ago";
    };
    return h93("div", { className: "notification-center", ref: panelRef }, [
      // Bell button
      h93("button", {
        key: "bell",
        className: "notification-bell",
        onClick: () => {
          setOpen(!open);
          if (!open)
            markAllRead();
        },
        "aria-label": "Notifications"
      }, [
        getIcon("bell"),
        unreadCount > 0 && h93(
          "span",
          { key: "badge", className: "notification-badge" },
          unreadCount > 99 ? "99+" : unreadCount
        )
      ]),
      // Panel
      open && h93("div", { key: "panel", className: "notification-panel" }, [
        h93("div", { key: "header", className: "notification-panel-header" }, [
          h93("span", { key: "title" }, "Notifications"),
          notifications.length > 0 && h93("button", {
            key: "clear",
            className: "notification-clear",
            onClick: clearAll
          }, "Clear all")
        ]),
        h93(
          "div",
          { key: "list", className: "notification-list" },
          notifications.length === 0 ? h93("div", { className: "notification-empty" }, "No notifications") : notifications.map(
            (n) => h93("div", {
              key: n.id,
              className: "notification-item" + (n.read ? "" : " unread")
            }, [
              h93("div", {
                key: "dot",
                className: "notification-dot",
                style: { background: variantColors[n.variant] || variantColors.info }
              }),
              h93("div", { key: "content", className: "notification-content" }, [
                n.title && h93("div", { key: "title", className: "notification-title" }, n.title),
                h93("div", { key: "msg", className: "notification-message" }, n.message),
                h93("div", { key: "time", className: "notification-time" }, timeAgo(n.timestamp))
              ]),
              h93("button", {
                key: "dismiss",
                className: "notification-dismiss",
                onClick: (e) => {
                  e.stopPropagation();
                  dismiss(n.id);
                },
                "aria-label": "Dismiss"
              }, "\xD7")
            ])
          )
        )
      ])
    ]);
  }

  // src/components/core/LoginPage.js
  var { createElement: h94, useState: useState47, useCallback: useCallback29 } = React;
  function LoginPage({ onLogin, title }) {
    const [username, setUsername] = useState47("");
    const [password, setPassword] = useState47("");
    const [error, setError] = useState47("");
    const [loading, setLoading] = useState47(false);
    const handleSubmit = useCallback29(async (e) => {
      e.preventDefault();
      setError("");
      setLoading(true);
      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
          sessionStorage.setItem("cacao-auth-token", data.token);
          if (onLogin)
            onLogin(data);
        } else {
          setError(data.message || "Invalid credentials");
        }
      } catch (err) {
        setError("Connection error");
      } finally {
        setLoading(false);
      }
    }, [username, password, onLogin]);
    return h94(
      "div",
      { className: "login-page" },
      h94("form", { className: "login-form", onSubmit: handleSubmit }, [
        h94("h2", { key: "title", className: "login-title" }, title || "Sign In"),
        error && h94("div", { key: "error", className: "login-error" }, error),
        h94("div", { key: "field-user", className: "login-field" }, [
          h94("label", { key: "label", htmlFor: "login-username" }, "Username"),
          h94("input", {
            key: "input",
            id: "login-username",
            type: "text",
            value: username,
            onChange: (e) => setUsername(e.target.value),
            autoFocus: true,
            autoComplete: "username",
            required: true
          })
        ]),
        h94("div", { key: "field-pass", className: "login-field" }, [
          h94("label", { key: "label", htmlFor: "login-password" }, "Password"),
          h94("input", {
            key: "input",
            id: "login-password",
            type: "password",
            value: password,
            onChange: (e) => setPassword(e.target.value),
            autoComplete: "current-password",
            required: true
          })
        ]),
        h94("button", {
          key: "submit",
          type: "submit",
          className: "login-submit",
          disabled: loading
        }, loading ? "Signing in..." : "Sign In")
      ])
    );
  }

  // src/components/core/ErrorOverlay.js
  var { createElement: h95, useState: useState48, useEffect: useEffect37, useCallback: useCallback30 } = React;
  function ErrorOverlay() {
    const [errors, setErrors] = useState48([]);
    const [collapsed, setCollapsed] = useState48({});
    const addError = useCallback30((err) => {
      setErrors((prev) => {
        const next = [...prev, { ...err, id: Date.now() + Math.random() }];
        return next.slice(-10);
      });
    }, []);
    const dismissError = useCallback30((id) => {
      setErrors((prev) => prev.filter((e) => e.id !== id));
    }, []);
    const dismissAll = useCallback30(() => {
      setErrors([]);
    }, []);
    const toggleTraceback = useCallback30((id) => {
      setCollapsed((prev) => ({ ...prev, [id]: !prev[id] }));
    }, []);
    useEffect37(() => {
      window.__CACAO_ERROR_OVERLAY__ = { addError };
      return () => {
        delete window.__CACAO_ERROR_OVERLAY__;
      };
    }, [addError]);
    if (!errors.length)
      return null;
    return h95(
      "div",
      { className: "cacao-error-overlay" },
      h95(
        "div",
        { className: "cacao-error-overlay__header" },
        h95("span", { className: "cacao-error-overlay__badge" }, errors.length),
        h95("span", null, "Server Error" + (errors.length > 1 ? "s" : "")),
        h95(
          "div",
          { className: "cacao-error-overlay__actions" },
          errors.length > 1 && h95("button", {
            className: "cacao-error-overlay__btn",
            onClick: dismissAll
          }, "Dismiss All"),
          h95("button", {
            className: "cacao-error-overlay__close",
            onClick: dismissAll,
            title: "Close overlay"
          }, "\xD7")
        )
      ),
      h95(
        "div",
        { className: "cacao-error-overlay__list" },
        errors.map(
          (err) => h95(
            "div",
            { key: err.id, className: "cacao-error-overlay__item" },
            h95(
              "div",
              { className: "cacao-error-overlay__item-header" },
              h95("span", { className: "cacao-error-overlay__item-type" }, err.title || err.type || "Error"),
              h95("button", {
                className: "cacao-error-overlay__item-dismiss",
                onClick: () => dismissError(err.id)
              }, "\xD7")
            ),
            h95("p", { className: "cacao-error-overlay__item-message" }, err.message),
            err.suggestion && h95("p", { className: "cacao-error-overlay__item-suggestion" }, err.suggestion),
            err.context && h95(
              "p",
              { className: "cacao-error-overlay__item-context" },
              "While: ",
              err.context
            ),
            err.traceback && h95(
              "div",
              { className: "cacao-error-overlay__traceback-toggle" },
              h95("button", {
                className: "cacao-error-overlay__btn cacao-error-overlay__btn--small",
                onClick: () => toggleTraceback(err.id)
              }, collapsed[err.id] ? "Hide Traceback" : "Show Traceback"),
              collapsed[err.id] && h95("pre", { className: "cacao-error-overlay__traceback" }, err.traceback)
            )
          )
        )
      )
    );
  }

  // src/components/core/DevTools.js
  init_static_runtime();
  var { createElement: h96, useState: useState49, useEffect: useEffect38, useCallback: useCallback31, useRef: useRef30, useMemo: useMemo9 } = React;
  var eventLog = [];
  var MAX_LOG_ENTRIES = 200;
  var _eventLogListeners = /* @__PURE__ */ new Set();
  function pushEvent(entry) {
    eventLog.push({ ...entry, id: Date.now() + Math.random(), ts: Date.now() });
    if (eventLog.length > MAX_LOG_ENTRIES)
      eventLog.shift();
    _eventLogListeners.forEach((fn) => fn());
  }
  var perfData = {
    signalUpdates: [],
    // { name, ts, duration }
    renderCounts: {},
    // componentType -> count
    totalRenders: 0,
    sessionStart: Date.now()
  };
  var _perfListeners = /* @__PURE__ */ new Set();
  function recordSignalUpdate(name, duration) {
    perfData.signalUpdates.push({ name, ts: Date.now(), duration });
    if (perfData.signalUpdates.length > 500)
      perfData.signalUpdates.shift();
    _perfListeners.forEach((fn) => fn());
  }
  function recordRender(componentType) {
    perfData.renderCounts[componentType] = (perfData.renderCounts[componentType] || 0) + 1;
    perfData.totalRenders++;
    _perfListeners.forEach((fn) => fn());
  }
  function instrumentWebSocket() {
    if (cacaoWs._devtoolsInstrumented)
      return;
    cacaoWs._devtoolsInstrumented = true;
    const origHandle = cacaoWs.handleMessage.bind(cacaoWs);
    cacaoWs.handleMessage = function(message) {
      const start = performance.now();
      pushEvent({ type: "ws:recv", msgType: message.type, data: message });
      if (message.type === "update" && message.changes) {
        Object.keys(message.changes).forEach((name) => {
          recordSignalUpdate(name, performance.now() - start);
        });
      }
      origHandle(message);
    };
    const origSend = cacaoWs.sendEvent.bind(cacaoWs);
    cacaoWs.sendEvent = function(eventName, eventData) {
      pushEvent({ type: "ws:send", msgType: "event", data: { name: eventName, data: eventData } });
      origSend(eventName, eventData);
    };
    const origRawSend = cacaoWs.send.bind(cacaoWs);
    cacaoWs.send = function(message) {
      pushEvent({ type: "ws:send", msgType: message.type || "raw", data: message });
      origRawSend(message);
    };
  }
  function instrumentRenderer() {
    if (window.__CACAO_RENDER_INSTRUMENTED__)
      return;
    window.__CACAO_RENDER_INSTRUMENTED__ = true;
    window.__CACAO_DEVTOOLS__ = {
      onRender: recordRender,
      pushEvent,
      eventLog,
      perfData
    };
  }
  function SignalInspector() {
    const [signals, setSignals] = useState49({});
    const [filter, setFilter] = useState49("");
    const [expandedKeys, setExpandedKeys] = useState49(/* @__PURE__ */ new Set());
    useEffect38(() => {
      const update = (sigs) => setSignals({ ...sigs });
      if (isStaticMode()) {
        setSignals({ ...window.__CACAO_INITIAL_SIGNALS__ || {} });
      } else {
        setSignals({ ...cacaoWs.signals });
      }
      const unsub = cacaoWs.subscribe(update);
      return unsub;
    }, []);
    const filtered = useMemo9(() => {
      const entries = Object.entries(signals);
      if (!filter)
        return entries;
      const lower = filter.toLowerCase();
      return entries.filter(([k2]) => k2.toLowerCase().includes(lower));
    }, [signals, filter]);
    const toggleExpand = useCallback31((key) => {
      setExpandedKeys((prev) => {
        const next = new Set(prev);
        next.has(key) ? next.delete(key) : next.add(key);
        return next;
      });
    }, []);
    return h96(
      "div",
      { className: "cacao-devtools__tab-content" },
      h96(
        "div",
        { className: "cacao-devtools__toolbar" },
        h96("input", {
          className: "cacao-devtools__search",
          placeholder: "Filter signals...",
          value: filter,
          onChange: (e) => setFilter(e.target.value)
        }),
        h96("span", { className: "cacao-devtools__count" }, `${filtered.length} signal${filtered.length !== 1 ? "s" : ""}`)
      ),
      h96(
        "div",
        { className: "cacao-devtools__signal-list" },
        filtered.length === 0 ? h96("div", { className: "cacao-devtools__empty" }, "No signals found") : filtered.map(([name, value]) => {
          const isExpandable = typeof value === "object" && value !== null;
          const expanded = expandedKeys.has(name);
          return h96(
            "div",
            { key: name, className: "cacao-devtools__signal-item" },
            h96(
              "div",
              {
                className: "cacao-devtools__signal-header",
                onClick: isExpandable ? () => toggleExpand(name) : void 0
              },
              isExpandable && h96("span", { className: "cacao-devtools__expand-icon" }, expanded ? "\u25BC" : "\u25B6"),
              h96("span", { className: "cacao-devtools__signal-name" }, name),
              h96("span", { className: "cacao-devtools__signal-type" }, typeLabel(value)),
              !isExpandable && h96("span", { className: "cacao-devtools__signal-value" }, formatPreview(value))
            ),
            expanded && isExpandable && h96(
              "pre",
              { className: "cacao-devtools__signal-expanded" },
              JSON.stringify(value, null, 2)
            )
          );
        })
      )
    );
  }
  function EventLog() {
    const [, forceUpdate] = useState49(0);
    const [filter, setFilter] = useState49("");
    const [autoScroll, setAutoScroll] = useState49(true);
    const listRef = useRef30(null);
    useEffect38(() => {
      const listener = () => forceUpdate((n) => n + 1);
      _eventLogListeners.add(listener);
      return () => _eventLogListeners.delete(listener);
    }, []);
    useEffect38(() => {
      if (autoScroll && listRef.current) {
        listRef.current.scrollTop = listRef.current.scrollHeight;
      }
    });
    const filtered = useMemo9(() => {
      if (!filter)
        return eventLog;
      const lower = filter.toLowerCase();
      return eventLog.filter(
        (e) => (e.msgType || "").toLowerCase().includes(lower) || JSON.stringify(e.data || "").toLowerCase().includes(lower)
      );
    }, [eventLog.length, filter]);
    const clearLog = useCallback31(() => {
      eventLog.length = 0;
      forceUpdate((n) => n + 1);
    }, []);
    return h96(
      "div",
      { className: "cacao-devtools__tab-content" },
      h96(
        "div",
        { className: "cacao-devtools__toolbar" },
        h96("input", {
          className: "cacao-devtools__search",
          placeholder: "Filter events...",
          value: filter,
          onChange: (e) => setFilter(e.target.value)
        }),
        h96(
          "label",
          { className: "cacao-devtools__checkbox-label" },
          h96("input", { type: "checkbox", checked: autoScroll, onChange: () => setAutoScroll(!autoScroll) }),
          "Auto-scroll"
        ),
        h96("button", { className: "cacao-devtools__btn", onClick: clearLog }, "Clear"),
        h96("span", { className: "cacao-devtools__count" }, `${filtered.length} events`)
      ),
      h96(
        "div",
        { className: "cacao-devtools__event-list", ref: listRef },
        filtered.length === 0 ? h96("div", { className: "cacao-devtools__empty" }, "No events yet") : filtered.map(
          (entry) => h96(
            "div",
            {
              key: entry.id,
              className: `cacao-devtools__event-item cacao-devtools__event-item--${entry.type === "ws:send" ? "out" : "in"}`
            },
            h96("span", { className: "cacao-devtools__event-dir" }, entry.type === "ws:send" ? "\u2191" : "\u2193"),
            h96("span", { className: "cacao-devtools__event-time" }, formatTime(entry.ts)),
            h96("span", { className: "cacao-devtools__event-type" }, entry.msgType),
            h96("span", { className: "cacao-devtools__event-preview" }, eventPreview(entry))
          )
        )
      )
    );
  }
  function ComponentTree() {
    const [tree, setTree] = useState49(null);
    const [expandedPaths, setExpandedPaths] = useState49(/* @__PURE__ */ new Set([""]));
    useEffect38(() => {
      if (isStaticMode() && window.__CACAO_PAGES__) {
        setTree(window.__CACAO_PAGES__);
      } else {
        fetch("/api/pages").then((r) => r.json()).then((data) => setTree(data)).catch(() => setTree(null));
      }
    }, []);
    const togglePath = useCallback31((path) => {
      setExpandedPaths((prev) => {
        const next = new Set(prev);
        next.has(path) ? next.delete(path) : next.add(path);
        return next;
      });
    }, []);
    if (!tree)
      return h96(
        "div",
        { className: "cacao-devtools__tab-content" },
        h96("div", { className: "cacao-devtools__empty" }, "Loading component tree...")
      );
    const pages = tree.pages || {};
    return h96(
      "div",
      { className: "cacao-devtools__tab-content" },
      h96(
        "div",
        { className: "cacao-devtools__tree" },
        Object.entries(pages).map(
          ([pagePath, components]) => h96(
            "div",
            { key: pagePath, className: "cacao-devtools__tree-page" },
            h96(
              "div",
              {
                className: "cacao-devtools__tree-page-header",
                onClick: () => togglePath(pagePath)
              },
              h96(
                "span",
                { className: "cacao-devtools__expand-icon" },
                expandedPaths.has(pagePath) ? "\u25BC" : "\u25B6"
              ),
              h96("span", { className: "cacao-devtools__tree-page-name" }, pagePath || "/"),
              h96("span", { className: "cacao-devtools__count" }, `${components.length} root`)
            ),
            expandedPaths.has(pagePath) && h96(
              "div",
              { className: "cacao-devtools__tree-children" },
              components.map((comp, i) => renderTreeNode(comp, `${pagePath}/${i}`, 0, expandedPaths, togglePath))
            )
          )
        )
      )
    );
  }
  function renderTreeNode(comp, path, depth, expandedPaths, togglePath) {
    if (!comp || !comp.type)
      return null;
    const children = comp.children || [];
    const hasChildren = children.length > 0;
    const expanded = expandedPaths.has(path);
    const propKeys = Object.keys(comp.props || {}).filter((k2) => k2 !== "children");
    return h96(
      "div",
      { key: path, className: "cacao-devtools__tree-node", style: { paddingLeft: depth * 16 } },
      h96(
        "div",
        {
          className: "cacao-devtools__tree-node-header",
          onClick: hasChildren ? () => togglePath(path) : void 0
        },
        hasChildren ? h96("span", { className: "cacao-devtools__expand-icon" }, expanded ? "\u25BC" : "\u25B6") : h96("span", { className: "cacao-devtools__expand-icon cacao-devtools__expand-icon--leaf" }, "\xB7"),
        h96("span", { className: "cacao-devtools__tree-type" }, comp.type),
        propKeys.length > 0 && h96(
          "span",
          { className: "cacao-devtools__tree-props" },
          propKeys.slice(0, 3).map((k2) => `${k2}=${JSON.stringify(comp.props[k2])}`).join(" ") + (propKeys.length > 3 ? " ..." : "")
        ),
        hasChildren && h96("span", { className: "cacao-devtools__count" }, children.length)
      ),
      expanded && hasChildren && h96(
        "div",
        { className: "cacao-devtools__tree-children" },
        children.map((child, i) => renderTreeNode(child, `${path}/${i}`, depth + 1, expandedPaths, togglePath))
      )
    );
  }
  function PerfProfiler() {
    const [, forceUpdate] = useState49(0);
    const [sortBy, setSortBy] = useState49("count");
    useEffect38(() => {
      const listener = () => forceUpdate((n) => n + 1);
      _perfListeners.add(listener);
      return () => _perfListeners.delete(listener);
    }, []);
    const uptime = ((Date.now() - perfData.sessionStart) / 1e3).toFixed(0);
    const signalStats = useMemo9(() => {
      const stats = {};
      for (const u3 of perfData.signalUpdates) {
        if (!stats[u3.name])
          stats[u3.name] = { name: u3.name, count: 0, totalDuration: 0, lastTs: 0 };
        stats[u3.name].count++;
        stats[u3.name].totalDuration += u3.duration;
        stats[u3.name].lastTs = u3.ts;
      }
      return Object.values(stats);
    }, [perfData.signalUpdates.length]);
    const renderStats = useMemo9(() => {
      return Object.entries(perfData.renderCounts).map(([type, count]) => ({ type, count })).sort((a, b2) => sortBy === "count" ? b2.count - a.count : a.type.localeCompare(b2.type));
    }, [perfData.totalRenders, sortBy]);
    const clearPerf = useCallback31(() => {
      perfData.signalUpdates.length = 0;
      Object.keys(perfData.renderCounts).forEach((k2) => delete perfData.renderCounts[k2]);
      perfData.totalRenders = 0;
      perfData.sessionStart = Date.now();
      forceUpdate((n) => n + 1);
    }, []);
    return h96(
      "div",
      { className: "cacao-devtools__tab-content" },
      h96(
        "div",
        { className: "cacao-devtools__toolbar" },
        h96("span", { className: "cacao-devtools__perf-stat" }, `Uptime: ${uptime}s`),
        h96("span", { className: "cacao-devtools__perf-stat" }, `Total renders: ${perfData.totalRenders}`),
        h96("span", { className: "cacao-devtools__perf-stat" }, `Signal updates: ${perfData.signalUpdates.length}`),
        h96("button", { className: "cacao-devtools__btn", onClick: clearPerf }, "Reset")
      ),
      h96(
        "div",
        { className: "cacao-devtools__perf-section" },
        h96("h4", { className: "cacao-devtools__perf-heading" }, "Signal Update Frequency"),
        signalStats.length === 0 ? h96("div", { className: "cacao-devtools__empty" }, "No signal updates yet") : h96(
          "div",
          { className: "cacao-devtools__perf-table" },
          h96(
            "div",
            { className: "cacao-devtools__perf-row cacao-devtools__perf-row--header" },
            h96("span", null, "Signal"),
            h96("span", null, "Updates"),
            h96("span", null, "Avg (ms)"),
            h96("span", null, "Last")
          ),
          signalStats.map(
            (s) => h96(
              "div",
              { key: s.name, className: "cacao-devtools__perf-row" },
              h96("span", { className: "cacao-devtools__signal-name" }, s.name),
              h96("span", null, s.count),
              h96("span", null, (s.totalDuration / s.count).toFixed(2)),
              h96("span", { className: "cacao-devtools__event-time" }, formatTime(s.lastTs))
            )
          )
        )
      ),
      h96(
        "div",
        { className: "cacao-devtools__perf-section" },
        h96(
          "div",
          { className: "cacao-devtools__perf-heading-row" },
          h96("h4", { className: "cacao-devtools__perf-heading" }, "Render Counts"),
          h96("button", {
            className: "cacao-devtools__btn cacao-devtools__btn--tiny",
            onClick: () => setSortBy(sortBy === "count" ? "name" : "count")
          }, `Sort: ${sortBy}`)
        ),
        renderStats.length === 0 ? h96("div", { className: "cacao-devtools__empty" }, "No renders tracked yet") : h96(
          "div",
          { className: "cacao-devtools__perf-table" },
          h96(
            "div",
            { className: "cacao-devtools__perf-row cacao-devtools__perf-row--header" },
            h96("span", null, "Component"),
            h96("span", null, "Renders")
          ),
          renderStats.map(
            (s) => h96(
              "div",
              { key: s.type, className: "cacao-devtools__perf-row" },
              h96("span", { className: "cacao-devtools__tree-type" }, s.type),
              h96("span", null, s.count)
            )
          )
        )
      )
    );
  }
  function SessionInfo() {
    const sessionId = cacaoWs.sessionId || "(unknown)";
    const connected = cacaoWs.connected;
    const signalCount = Object.keys(cacaoWs.signals || {}).length;
    return h96(
      "div",
      { className: "cacao-devtools__session-info" },
      h96(
        "div",
        { className: "cacao-devtools__session-row" },
        h96("span", { className: "cacao-devtools__session-label" }, "Session ID"),
        h96("span", { className: "cacao-devtools__session-value" }, sessionId)
      ),
      h96(
        "div",
        { className: "cacao-devtools__session-row" },
        h96("span", { className: "cacao-devtools__session-label" }, "Status"),
        h96("span", {
          className: `cacao-devtools__session-value cacao-devtools__session-value--${connected ? "ok" : "err"}`
        }, connected ? "Connected" : "Disconnected")
      ),
      h96(
        "div",
        { className: "cacao-devtools__session-row" },
        h96("span", { className: "cacao-devtools__session-label" }, "Signals"),
        h96("span", { className: "cacao-devtools__session-value" }, signalCount)
      ),
      h96(
        "div",
        { className: "cacao-devtools__session-row" },
        h96("span", { className: "cacao-devtools__session-label" }, "Mode"),
        h96("span", { className: "cacao-devtools__session-value" }, isStaticMode() ? "Static" : "WebSocket")
      )
    );
  }
  var TABS = [
    { id: "signals", label: "Signals" },
    { id: "events", label: "Events" },
    { id: "tree", label: "Tree" },
    { id: "perf", label: "Perf" }
  ];
  function DevTools() {
    const [open, setOpen] = useState49(false);
    const [activeTab, setActiveTab] = useState49("signals");
    const [position, setPosition] = useState49("bottom");
    useEffect38(() => {
      instrumentWebSocket();
      instrumentRenderer();
      const handler = (e) => {
        if (e.ctrlKey && e.shiftKey && e.key === "D") {
          e.preventDefault();
          setOpen((prev) => !prev);
        }
      };
      window.addEventListener("keydown", handler);
      return () => window.removeEventListener("keydown", handler);
    }, []);
    const toggle = h96("button", {
      className: "cacao-devtools__toggle",
      onClick: () => setOpen(!open),
      title: "Cacao DevTools (Ctrl+Shift+D)"
    }, "\u{1F6E0}");
    if (!open)
      return toggle;
    const tabContent = {
      signals: h96(
        React.Fragment,
        null,
        h96(SessionInfo, null),
        h96(SignalInspector, null)
      ),
      events: h96(EventLog, null),
      tree: h96(ComponentTree, null),
      perf: h96(PerfProfiler, null)
    };
    return h96(
      React.Fragment,
      null,
      toggle,
      h96(
        "div",
        { className: `cacao-devtools cacao-devtools--${position}` },
        h96(
          "div",
          { className: "cacao-devtools__header" },
          h96("span", { className: "cacao-devtools__title" }, "Cacao DevTools"),
          h96(
            "div",
            { className: "cacao-devtools__header-actions" },
            h96("button", {
              className: "cacao-devtools__btn",
              onClick: () => setPosition(position === "bottom" ? "right" : "bottom"),
              title: "Toggle position"
            }, position === "bottom" ? "\u2B95" : "\u2B07"),
            h96("button", {
              className: "cacao-devtools__close",
              onClick: () => setOpen(false)
            }, "\xD7")
          )
        ),
        h96(
          "div",
          { className: "cacao-devtools__tabs" },
          TABS.map(
            (tab) => h96("button", {
              key: tab.id,
              className: `cacao-devtools__tab ${activeTab === tab.id ? "cacao-devtools__tab--active" : ""}`,
              onClick: () => setActiveTab(tab.id)
            }, tab.label)
          )
        ),
        h96(
          "div",
          { className: "cacao-devtools__body" },
          tabContent[activeTab]
        )
      )
    );
  }
  function typeLabel(value) {
    if (value === null)
      return "null";
    if (Array.isArray(value))
      return `array[${value.length}]`;
    return typeof value;
  }
  function formatPreview(value) {
    if (value === null || value === void 0)
      return String(value);
    if (typeof value === "string")
      return value.length > 60 ? `"${value.slice(0, 57)}..."` : `"${value}"`;
    if (typeof value === "boolean" || typeof value === "number")
      return String(value);
    return JSON.stringify(value).slice(0, 60);
  }
  function formatTime(ts) {
    const d = new Date(ts);
    return d.toLocaleTimeString("en-US", { hour12: false }) + "." + String(d.getMilliseconds()).padStart(3, "0");
  }
  function eventPreview(entry) {
    const d = entry.data;
    if (!d)
      return "";
    if (d.name)
      return d.name;
    if (d.changes)
      return Object.keys(d.changes).join(", ");
    if (d.signal)
      return d.signal;
    return "";
  }

  // src/components/core/contracts.js
  var contracts = {
    AppShell: {
      expectedChildren: ["NavSidebar"]
    },
    NavSidebar: {
      expectedChildren: ["NavGroup"],
      requiredParent: ["AppShell"]
    },
    ShellContent: {
      requiredParent: ["AppShell"]
    },
    NavGroup: {
      expectedChildren: ["NavItem"],
      requiredParent: ["NavSidebar"]
    },
    NavItem: {
      requiredParent: ["NavGroup"]
    }
  };

  // src/components/core/validateTree.js
  function validateTree(components) {
    if (!window.__CACAO_DEBUG__)
      return;
    const issues = [];
    walkTree(components, null, issues);
    if (issues.length === 0)
      return;
    console.groupCollapsed(
      `%c[Cacao] Tree validation: ${issues.length} issue${issues.length > 1 ? "s" : ""} found`,
      "color: #f59e0b; font-weight: bold"
    );
    for (const issue of issues) {
      console.warn(issue);
    }
    console.groupEnd();
  }
  function walkTree(components, parentType, issues) {
    if (!Array.isArray(components))
      return;
    const childTypes = components.map((c) => c?.type).filter(Boolean);
    if (parentType && contracts[parentType]?.expectedChildren) {
      for (const expected of contracts[parentType].expectedChildren) {
        if (!childTypes.includes(expected)) {
          issues.push(
            `${parentType} expects a <${expected}> child but none was found. Children present: [${childTypes.join(", ") || "none"}]`
          );
        }
      }
    }
    if (parentType && contracts[parentType]?.allowedChildren) {
      const allowed = contracts[parentType].allowedChildren;
      for (const childType of childTypes) {
        if (!allowed.includes(childType)) {
          issues.push(
            `${parentType} does not expect <${childType}> as a child. Allowed: [${allowed.join(", ")}]`
          );
        }
      }
    }
    for (const comp of components) {
      if (!comp?.type)
        continue;
      const contract = contracts[comp.type];
      if (contract?.requiredParent) {
        if (!parentType || !contract.requiredParent.includes(parentType)) {
          issues.push(
            `<${comp.type}> must be a child of [${contract.requiredParent.join(", ")}] but found inside ${parentType ? `<${parentType}>` : "root"}`
          );
        }
      }
      if (comp.children) {
        walkTree(comp.children, comp.type, issues);
      }
    }
  }

  // src/components/App.js
  var { createElement: h97, useState: useState50, useEffect: useEffect39, useCallback: useCallback32 } = React;
  function getRouteFromPath() {
    if (window.location.hash) {
      const hash = window.location.hash.replace(/^#\/?/, "");
      if (hash)
        return hash;
    }
    if (isStaticMode() || window.location.protocol === "file:") {
      return null;
    }
    const path = window.location.pathname;
    const route = path.replace(/^\/+/, "");
    return route || null;
  }
  function App({ renderers: renderers2 }) {
    const [pages, setPages] = useState50(null);
    const [currentPage, setCurrentPage] = useState50("/");
    const [activeTab, setActiveTab] = useState50(() => getRouteFromPath());
    const [error, setError] = useState50(null);
    const [authRequired, setAuthRequired] = useState50(false);
    const [authenticated, setAuthenticated] = useState50(false);
    const setActiveTabWithRoute = useCallback32((tab) => {
      setActiveTab(tab);
      if (tab) {
        if (isStaticMode()) {
          const newHash = "#/" + tab;
          if (window.location.hash !== newHash) {
            window.history.pushState({ tab }, "", newHash);
          }
        } else {
          const newPath = "/" + tab;
          if (window.location.pathname !== newPath) {
            window.history.pushState({ tab }, "", newPath);
          }
        }
      }
    }, []);
    useEffect39(() => {
      const handleNavigation = (event) => {
        const tab = event?.state?.tab || getRouteFromPath();
        setActiveTab(tab);
      };
      window.addEventListener("popstate", handleNavigation);
      window.addEventListener("hashchange", handleNavigation);
      return () => {
        window.removeEventListener("popstate", handleNavigation);
        window.removeEventListener("hashchange", handleNavigation);
      };
    }, []);
    useEffect39(() => {
      if (activeTab) {
        const url = isStaticMode() ? "#/" + activeTab : "/" + activeTab;
        window.history.replaceState({ tab: activeTab }, "", url);
      }
    }, []);
    useEffect39(() => {
      if (isStaticMode() && window.__CACAO_PAGES__) {
        setPages(window.__CACAO_PAGES__);
        const sp = window.__CACAO_PAGES__.pages || {};
        Object.values(sp).forEach((comps) => validateTree(comps));
        return;
      }
      fetch("/api/pages").then((r) => r.json()).then((data) => {
        window.__CACAO_SLOTS__ = data.slots || {};
        const headSlot = (data.slots || {}).head;
        if (headSlot && headSlot.length) {
          headSlot.forEach((item) => {
            if (item.type === "RawHtml" && item.props && item.props.html) {
              const container = document.createElement("div");
              container.innerHTML = item.props.html;
              while (container.firstChild) {
                document.head.appendChild(container.firstChild);
              }
            }
          });
        }
        if (data.error && window.__CACAO_DEBUG__) {
          setTimeout(() => {
            if (window.__CACAO_ERROR_OVERLAY__) {
              window.__CACAO_ERROR_OVERLAY__.addError(data.error);
            }
          }, 100);
        }
        const dp = data.pages || {};
        Object.values(dp).forEach((comps) => validateTree(comps));
        return setPages(data);
      }).catch((e) => setError(e.message));
    }, []);
    useEffect39(() => {
      const check = () => {
        if (window.__CACAO_AUTH_REQUIRED__ && !authenticated) {
          setAuthRequired(true);
        }
      };
      check();
      const interval = setInterval(check, 500);
      return () => clearInterval(interval);
    }, [authenticated]);
    if (authRequired && !authenticated) {
      const title = pages?.metadata?.title || "Cacao App";
      return h97(LoginPage, {
        title,
        onLogin: (data) => {
          window.__CACAO_AUTH_REQUIRED__ = false;
          setAuthenticated(true);
          setAuthRequired(false);
        }
      });
    }
    if (error)
      return h97("div", { className: "loading", style: { color: "var(--danger)" } }, "Error: " + error);
    if (!pages)
      return h97("div", { className: "loading" }, h97("div", { className: "loading-spinner" }));
    const pageData = pages.pages || {};
    const components = pageData[currentPage] || [];
    const render = (comp, key) => renderComponent(comp, key, setActiveTabWithRoute, activeTab, renderers2);
    const overlays = [
      h97(CommandPalette, { key: "cmd-palette", setActiveTab: setActiveTabWithRoute, pages: pageData }),
      h97(ToastContainer, { key: "toast" }),
      h97(NotificationCenter, { key: "notifications" }),
      window.__CACAO_DEBUG__ && h97(ErrorOverlay, { key: "error-overlay" }),
      window.__CACAO_DEBUG__ && h97(DevTools, { key: "devtools" })
    ].filter(Boolean);
    const appShellIdx = components.findIndex((c) => c.type === "AppShell");
    if (appShellIdx >= 0) {
      const allRendered = components.map((c, i) => render(c, i));
      return h97(React.Fragment, null, [
        ...allRendered,
        ...overlays
      ]);
    }
    const sidebarIdx = components.findIndex((c) => c.type === "Sidebar");
    const sidebar = sidebarIdx >= 0 ? components[sidebarIdx] : null;
    const mainComponents = sidebarIdx >= 0 ? [...components.slice(0, sidebarIdx), ...components.slice(sidebarIdx + 1)] : components;
    return h97(React.Fragment, null, [
      h97("div", { className: "app-container", key: "app" }, [
        h97("div", { className: "main-content", key: "main" }, mainComponents.map((c, i) => render(c, i))),
        sidebar && h97("div", { className: "sidebar", key: "sidebar" }, (sidebar.children || []).map((c, i) => render(c, i)))
      ]),
      ...overlays
    ]);
  }

  // src/components/index.js
  var categoryModules = {
    layout: layout_exports,
    display: display_exports,
    typography: typography_exports,
    form: form_exports,
    charts: charts_exports
  };
  var loadedCategories = /* @__PURE__ */ new Set(["layout", "typography"]);
  var pendingLoads = /* @__PURE__ */ new Map();
  var renderers = {
    ...layout_exports,
    ...typography_exports
  };
  function loadCategory(categoryName) {
    if (loadedCategories.has(categoryName))
      return Promise.resolve();
    if (pendingLoads.has(categoryName))
      return pendingLoads.get(categoryName);
    const mod = categoryModules[categoryName];
    if (mod) {
      Object.assign(renderers, mod);
      loadedCategories.add(categoryName);
      return Promise.resolve();
    }
    return Promise.resolve();
  }
  function ensureCategories(categories) {
    if (!categories || categories.length === 0) {
      return loadAllCategories();
    }
    return Promise.all(categories.map(loadCategory));
  }
  function loadAllCategories() {
    const promises = Object.keys(categoryModules).map(loadCategory);
    return Promise.all(promises);
  }
  loadAllCategories();
  initShortcuts();
  initTheme();
  window.Cacao = {
    initStatic: initStaticMode,
    isStaticMode,
    signals: staticSignals,
    dispatcher: staticDispatcher,
    renderers,
    // WebSocket / chat streaming
    ws: cacaoWs,
    // Feature APIs
    toast: showToast,
    setTheme,
    toggleTheme,
    openCommandPalette,
    registerCommand,
    // Shortcuts
    registerShortcut,
    getShortcuts,
    // Theme registration (for plugins)
    registerTheme(name, vars) {
      const root = document.documentElement;
      const style = document.createElement("style");
      const props = Object.entries(vars).map(([k2, v2]) => `--${k2}: ${v2};`).join("\n  ");
      style.textContent = `[data-theme="${name}"] {
  ${props}
}`;
      document.head.appendChild(style);
    },
    // Custom component registration (for plugins)
    registerComponent(name, renderFn) {
      renderers[name] = renderFn;
    },
    // Panel manager
    panelManager: PanelManager,
    // Lazy loading API
    loadCategory,
    ensureCategories,
    loadAllCategories,
    loadedCategories
  };
  function mountApp() {
    ReactDOM.createRoot(document.getElementById("root")).render(
      React.createElement(App, { renderers })
    );
  }
  if (!window.__CACAO_DEFER_MOUNT__) {
    mountApp();
  }
  window.Cacao.mount = mountApp;
})();
