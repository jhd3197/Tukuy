var Tukuy = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // src/index.js
  var index_exports = {};
  __export(index_exports, {
    TukuyRegistry: () => TukuyRegistry,
    tukuy: () => tukuy
  });

  // src/transformers/text.js
  var textTransformers = [
    {
      name: "strip",
      displayName: "Strip",
      description: "Remove leading/trailing whitespace",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return input.trim();
      }
    },
    {
      name: "lowercase",
      displayName: "Lowercase",
      description: "Convert to lowercase",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return input.toLowerCase();
      }
    },
    {
      name: "uppercase",
      displayName: "Uppercase",
      description: "Convert to uppercase",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return input.toUpperCase();
      }
    },
    {
      name: "title_case",
      displayName: "Title Case",
      description: "Capitalize the first letter of each word",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return input.split(/\s+/).filter((w) => w).map(
          (w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()
        ).join(" ");
      }
    },
    {
      name: "camel_case",
      displayName: "camelCase",
      description: "Convert to camelCase",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        const words = input.trim().split(/[\s_-]+/).filter((w) => w).map((w) => w.toLowerCase());
        if (words.length === 0) return "";
        return words[0] + words.slice(1).map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join("");
      }
    },
    {
      name: "snake_case",
      displayName: "snake_case",
      description: "Convert to snake_case",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        const words = input.trim().split(/[\s\-_]+/).filter((w) => w).map((w) => w.toLowerCase());
        return words.join("_");
      }
    },
    {
      name: "slugify",
      displayName: "Slugify",
      description: "Convert text to URL-friendly slug",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        let text = input.toLowerCase();
        text = text.replace(/[\s_]+/g, "-");
        text = text.replace(/[^\w-]/g, "");
        text = text.replace(/^-+|-+$/g, "");
        return text;
      }
    },
    {
      name: "truncate",
      displayName: "Truncate",
      description: "Truncate text with suffix",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [
        { name: "length", type: "number", default: 50, description: "Maximum length" },
        { name: "suffix", type: "string", default: "...", description: "Suffix to append" }
      ],
      transform(input, { length = 50, suffix = "..." } = {}) {
        if (input.length <= length) return input;
        const truncateLength = length - suffix.length;
        if (truncateLength <= 0) return suffix;
        const slice = input.slice(0, truncateLength);
        if (slice.includes(" ")) {
          const lastSpace = slice.lastIndexOf(" ");
          if (lastSpace > 0) return input.slice(0, lastSpace) + suffix;
        }
        return slice + suffix;
      }
    },
    {
      name: "remove_emojis",
      displayName: "Remove Emojis",
      description: "Strip emoji characters from text",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return input.replace(
          /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}]+/gu,
          ""
        );
      }
    },
    {
      name: "redact_sensitive",
      displayName: "Redact Sensitive",
      description: "Mask credit card numbers (keep first/last 4 digits)",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return input.replace(
          /\b\d{13,16}\b/g,
          (match) => match.slice(0, 4) + "*".repeat(match.length - 8) + match.slice(-4)
        );
      }
    },
    {
      name: "regex",
      displayName: "Regex",
      description: "Regex search or replace",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [
        { name: "pattern", type: "string", default: "", description: "Regular expression pattern" },
        { name: "template", type: "string", default: null, description: "Replacement template (null = extract match)" }
      ],
      transform(input, { pattern = "", template = null } = {}) {
        if (!pattern) return input;
        if (template !== null && template !== void 0) {
          return input.replace(new RegExp(pattern, "g"), template);
        }
        const match = new RegExp(pattern).exec(input);
        return match ? match[0] : input;
      }
    },
    {
      name: "split",
      displayName: "Split",
      description: "Split string and extract a part by index",
      category: "text",
      inputType: "string",
      outputType: "string",
      params: [
        { name: "delimiter", type: "string", default: ":", description: "Character to split on" },
        { name: "index", type: "number", default: -1, description: "Index of part to extract (-1 = last)" }
      ],
      transform(input, { delimiter = ":", index = -1 } = {}) {
        const parts = input.split(delimiter);
        let idx = index;
        if (idx < 0) idx = parts.length + idx;
        if (idx >= 0 && idx < parts.length) return parts[idx].trim();
        return input;
      }
    }
  ];

  // src/transformers/encoding.js
  var encodingTransformers = [
    {
      name: "url_encode",
      displayName: "URL Encode",
      description: "Percent-encode text for URLs",
      category: "encoding",
      inputType: "string",
      outputType: "string",
      params: [
        { name: "safe", type: "string", default: "", description: "Characters to leave unencoded" }
      ],
      transform(input, { safe = "" } = {}) {
        let encoded = encodeURIComponent(input);
        if (safe) {
          for (const ch of safe) {
            encoded = encoded.replaceAll(encodeURIComponent(ch), ch);
          }
        }
        return encoded;
      }
    },
    {
      name: "url_decode",
      displayName: "URL Decode",
      description: "Decode percent-encoded text",
      category: "encoding",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return decodeURIComponent(input);
      }
    },
    {
      name: "hex_encode",
      displayName: "Hex Encode",
      description: "Encode UTF-8 text to hexadecimal",
      category: "encoding",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        const bytes = new TextEncoder().encode(input);
        return Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
      }
    },
    {
      name: "hex_decode",
      displayName: "Hex Decode",
      description: "Decode hexadecimal to UTF-8 text",
      category: "encoding",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        const hex = input.replace(/\s/g, "");
        const bytes = new Uint8Array(hex.length / 2);
        for (let i = 0; i < hex.length; i += 2) {
          bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
        }
        return new TextDecoder().decode(bytes);
      }
    },
    {
      name: "html_entities_encode",
      displayName: "HTML Entities Encode",
      description: "Escape HTML special characters",
      category: "encoding",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return input.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#x27;");
      }
    },
    {
      name: "html_entities_decode",
      displayName: "HTML Entities Decode",
      description: "Unescape HTML entities",
      category: "encoding",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        if (typeof document !== "undefined") {
          const el = document.createElement("textarea");
          el.innerHTML = input;
          return el.value;
        }
        const entities = {
          "&amp;": "&",
          "&lt;": "<",
          "&gt;": ">",
          "&quot;": '"',
          "&#x27;": "'",
          "&#39;": "'",
          "&apos;": "'"
        };
        return input.replace(/&(?:#x?[0-9a-fA-F]+|[a-zA-Z]+);/g, (match) => {
          if (entities[match]) return entities[match];
          if (match.startsWith("&#x")) return String.fromCodePoint(parseInt(match.slice(3, -1), 16));
          if (match.startsWith("&#")) return String.fromCodePoint(parseInt(match.slice(2, -1), 10));
          return match;
        });
      }
    },
    {
      name: "rot13",
      displayName: "ROT13",
      description: "ROT13 cipher (self-reversing)",
      category: "encoding",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return input.replace(/[a-zA-Z]/g, (c) => {
          const base = c <= "Z" ? 65 : 97;
          return String.fromCharCode((c.charCodeAt(0) - base + 13) % 26 + base);
        });
      }
    },
    {
      name: "unicode_escape",
      displayName: "Unicode Escape",
      description: "Escape non-ASCII characters to \\uXXXX sequences",
      category: "encoding",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return Array.from(input).map((ch) => {
          const code = ch.codePointAt(0);
          if (code < 128) return ch;
          if (code <= 65535) return "\\u" + code.toString(16).padStart(4, "0");
          return "\\U" + code.toString(16).padStart(8, "0");
        }).join("");
      }
    },
    {
      name: "unicode_unescape",
      displayName: "Unicode Unescape",
      description: "Convert \\uXXXX sequences to characters",
      category: "encoding",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return input.replace(/\\U([0-9a-fA-F]{8})/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16))).replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16)));
      }
    }
  ];

  // src/transformers/crypto.js
  function bufferToHex(buffer) {
    return Array.from(new Uint8Array(buffer)).map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  function utf8ToBase64(str) {
    const bytes = new TextEncoder().encode(str);
    let binary = "";
    for (const b of bytes) binary += String.fromCharCode(b);
    return btoa(binary);
  }
  function base64ToUtf8(b64) {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return new TextDecoder().decode(bytes);
  }
  var cryptoTransformers = [
    {
      name: "hash_text",
      displayName: "Hash Text",
      description: "Hash string (SHA-1, SHA-256, SHA-512)",
      category: "crypto",
      inputType: "string",
      outputType: "string",
      async: true,
      params: [
        {
          name: "algorithm",
          type: "string",
          default: "sha256",
          description: "Hash algorithm",
          options: ["sha1", "sha256", "sha512"]
        }
      ],
      async transform(input, { algorithm = "sha256" } = {}) {
        const algoMap = {
          sha1: "SHA-1",
          sha256: "SHA-256",
          sha512: "SHA-512",
          "SHA-1": "SHA-1",
          "SHA-256": "SHA-256",
          "SHA-512": "SHA-512"
        };
        const algo = algoMap[algorithm];
        if (!algo) return `Unsupported: ${algorithm} (use sha1, sha256, sha512)`;
        const data = new TextEncoder().encode(input);
        const hash = await crypto.subtle.digest(algo, data);
        return bufferToHex(hash);
      }
    },
    {
      name: "base64_encode",
      displayName: "Base64 Encode",
      description: "Encode text to Base64",
      category: "crypto",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return utf8ToBase64(input);
      }
    },
    {
      name: "base64_decode",
      displayName: "Base64 Decode",
      description: "Decode Base64 to text",
      category: "crypto",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        return base64ToUtf8(input);
      }
    },
    {
      name: "uuid_generate",
      displayName: "Generate UUID",
      description: "Generate a UUID v4",
      category: "crypto",
      inputType: "any",
      outputType: "string",
      params: [
        { name: "version", type: "number", default: 4, description: "UUID version (v4 in browser)" }
      ],
      transform(_input, _options) {
        return crypto.randomUUID();
      }
    },
    {
      name: "hmac_sign",
      displayName: "HMAC Sign",
      description: "Generate HMAC signature",
      category: "crypto",
      inputType: "string",
      outputType: "string",
      async: true,
      params: [
        { name: "key", type: "string", default: "", description: "Secret key" },
        {
          name: "algorithm",
          type: "string",
          default: "sha256",
          description: "Hash algorithm",
          options: ["sha1", "sha256", "sha512"]
        }
      ],
      async transform(input, { key = "", algorithm = "sha256" } = {}) {
        const algoMap = { sha1: "SHA-1", sha256: "SHA-256", sha512: "SHA-512" };
        const algo = algoMap[algorithm] || "SHA-256";
        const enc = new TextEncoder();
        const cryptoKey = await crypto.subtle.importKey(
          "raw",
          enc.encode(key),
          { name: "HMAC", hash: algo },
          false,
          ["sign"]
        );
        const sig = await crypto.subtle.sign("HMAC", cryptoKey, enc.encode(input));
        return bufferToHex(sig);
      }
    }
  ];

  // src/transformers/numerical.js
  var SUFFIX_MAP = {
    k: 1e3,
    m: 1e6,
    b: 1e9,
    t: 1e12,
    bn: 1e9,
    mm: 1e6,
    tr: 1e12
  };
  var CURRENCY_PREFIX = new Set("$\u20AC\xA3\xA5\u20BF\u20BD\u20B9\u20A9\u20AB\u20AA\u20B4\u20A6\u20B2\u20B5\u20A1\u20B1\u20BA\u20B8");
  var NUM_STRIP_RE = /[,\s_]/g;
  var NUMBER_RE = /^\s*([-+]?)\s*((?:\d+(?:[,_]\d+)*|\d*\.\d+|\d+)(?:e[-+]?\d+)?)\s*([a-z]{1,2})?\s*$/i;
  function stripCurrencyPrefix(s) {
    return s && CURRENCY_PREFIX.has(s[0]) ? s.slice(1).trimStart() : s;
  }
  function parseShorthandNumber(value, { allowCurrency = true, allowPercent = true, percentBase = 1 } = {}) {
    if (value == null) throw new Error("Null/undefined value");
    if (typeof value === "number") return value;
    let s = String(value).trim();
    if (!s) throw new Error("Empty string");
    if (allowCurrency) s = stripCurrencyPrefix(s);
    let isPercent = false;
    if (allowPercent && s.endsWith("%")) {
      isPercent = true;
      s = s.slice(0, -1).trim();
    }
    const core = s.replace(NUM_STRIP_RE, "");
    const m = NUMBER_RE.exec(core);
    if (!m) throw new Error(`Invalid number format: ${value}`);
    const body = m[2];
    const suffix = (m[3] || "").toLowerCase();
    let multiplier = 1;
    if (suffix) {
      multiplier = SUFFIX_MAP[suffix];
      if (multiplier === void 0) throw new Error(`Unknown numeric suffix '${suffix}' in ${value}`);
    }
    let num = parseFloat(body);
    if (isNaN(num)) throw new Error(`Invalid number '${body}'`);
    num *= multiplier;
    if (isPercent) {
      num = num * percentBase / 100;
    }
    if (Math.abs(num - Math.round(num)) < 1e-12) {
      return Math.round(num);
    }
    return num;
  }
  function mean(arr) {
    return arr.reduce((a, b) => a + b, 0) / arr.length;
  }
  function median(arr) {
    const sorted = [...arr].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }
  function stdev(arr) {
    const m = mean(arr);
    const variance = arr.reduce((sum, v) => sum + (v - m) ** 2, 0) / (arr.length - 1);
    return Math.sqrt(variance);
  }
  var numericalTransformers = [
    {
      name: "int",
      displayName: "Integer",
      description: "Convert to integer",
      category: "numerical",
      inputType: "any",
      outputType: "number",
      params: [
        { name: "min_value", type: "number", default: null, description: "Minimum allowed value" },
        { name: "max_value", type: "number", default: null, description: "Maximum allowed value" }
      ],
      transform(input, { min_value = null, max_value = null } = {}) {
        let value = input;
        if (typeof value === "string") {
          value = value.replace(/[^\d-]/g, "");
        }
        const result = Math.trunc(parseFloat(value));
        if (isNaN(result)) throw new Error(`Invalid integer: ${input}`);
        if (min_value !== null && result < min_value) throw new Error(`Value ${result} < minimum ${min_value}`);
        if (max_value !== null && result > max_value) throw new Error(`Value ${result} > maximum ${max_value}`);
        return result;
      }
    },
    {
      name: "float",
      displayName: "Float",
      description: "Convert to float",
      category: "numerical",
      inputType: "any",
      outputType: "number",
      params: [
        { name: "min_value", type: "number", default: null, description: "Minimum allowed value" },
        { name: "max_value", type: "number", default: null, description: "Maximum allowed value" }
      ],
      transform(input, { min_value = null, max_value = null } = {}) {
        let value = input;
        if (typeof value === "string") {
          value = value.replace(/[^\d.\-]/g, "");
        }
        const result = parseFloat(value);
        if (isNaN(result)) throw new Error(`Invalid float: ${input}`);
        if (min_value !== null && result < min_value) throw new Error(`Value ${result} < minimum ${min_value}`);
        if (max_value !== null && result > max_value) throw new Error(`Value ${result} > maximum ${max_value}`);
        return result;
      }
    },
    {
      name: "round",
      displayName: "Round",
      description: "Round to N decimal places",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [
        { name: "decimals", type: "number", default: 0, description: "Decimal places" }
      ],
      transform(input, { decimals = 0 } = {}) {
        const factor = 10 ** decimals;
        return Math.round(parseFloat(input) * factor) / factor;
      }
    },
    {
      name: "currency_convert",
      displayName: "Currency Convert",
      description: "Multiply by exchange rate",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [
        { name: "rate", type: "number", default: 1, description: "Exchange rate" }
      ],
      transform(input, { rate = 1 } = {}) {
        if (rate == null) throw new Error("Exchange rate not provided");
        return parseFloat(input) * rate;
      }
    },
    {
      name: "unit_convert",
      displayName: "Unit Convert",
      description: "Multiply by conversion rate",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [
        { name: "rate", type: "number", default: 1, description: "Conversion rate" }
      ],
      transform(input, { rate = 1 } = {}) {
        if (rate == null) throw new Error("Conversion rate not provided");
        return parseFloat(input) * rate;
      }
    },
    {
      name: "math_operation",
      displayName: "Math Operation",
      description: "Perform add/subtract/multiply/divide",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [
        { name: "operation", type: "string", default: "add", description: "Operation", options: ["add", "subtract", "multiply", "divide"] },
        { name: "operand", type: "number", default: 0, description: "Operand value" }
      ],
      transform(input, { operation = "add", operand = 0 } = {}) {
        const x = parseFloat(input);
        const y = parseFloat(operand);
        switch (operation) {
          case "add":
            return x + y;
          case "subtract":
            return x - y;
          case "multiply":
            return x * y;
          case "divide":
            if (y === 0) throw new Error("Division by zero");
            return x / y;
          default:
            throw new Error(`Invalid operation '${operation}'. Use: add, subtract, multiply, divide`);
        }
      }
    },
    {
      name: "extract_numbers",
      displayName: "Extract Numbers",
      description: "Extract all numbers from text",
      category: "numerical",
      inputType: "string",
      outputType: "array",
      params: [],
      transform(input) {
        return String(input).match(/\d+(?:\.\d+)?/g) || [];
      }
    },
    {
      name: "abs",
      displayName: "Absolute Value",
      description: "Compute |x|",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [],
      transform(input) {
        return Math.abs(parseFloat(input));
      }
    },
    {
      name: "floor",
      displayName: "Floor",
      description: "Round down to nearest integer",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [],
      transform(input) {
        return Math.floor(parseFloat(input));
      }
    },
    {
      name: "ceil",
      displayName: "Ceiling",
      description: "Round up to nearest integer",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [],
      transform(input) {
        return Math.ceil(parseFloat(input));
      }
    },
    {
      name: "clamp",
      displayName: "Clamp",
      description: "Clamp value between min and max",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [
        { name: "min_value", type: "number", default: null, description: "Minimum value" },
        { name: "max_value", type: "number", default: null, description: "Maximum value" }
      ],
      transform(input, { min_value = null, max_value = null } = {}) {
        let v = parseFloat(input);
        if (min_value !== null) v = Math.max(v, min_value);
        if (max_value !== null) v = Math.min(v, max_value);
        return v;
      }
    },
    {
      name: "scale",
      displayName: "Scale",
      description: "Scale from one range to another",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [
        { name: "src_min", type: "number", default: 0, description: "Source range min" },
        { name: "src_max", type: "number", default: 1, description: "Source range max" },
        { name: "dst_min", type: "number", default: 0, description: "Dest range min" },
        { name: "dst_max", type: "number", default: 1, description: "Dest range max" }
      ],
      transform(input, { src_min = 0, src_max = 1, dst_min = 0, dst_max = 1 } = {}) {
        const v = parseFloat(input);
        if (src_max === src_min) return dst_min;
        return dst_min + (v - src_min) * (dst_max - dst_min) / (src_max - src_min);
      }
    },
    {
      name: "stats",
      displayName: "Statistics",
      description: "Compute count/sum/mean/median/min/max/stdev",
      category: "numerical",
      inputType: "array",
      outputType: "object",
      params: [],
      transform(input) {
        const nums = (Array.isArray(input) ? input : []).filter((v) => typeof v === "number" && !isNaN(v)).map(Number);
        if (!nums.length) return {};
        const out = {
          count: nums.length,
          sum: nums.reduce((a, b) => a + b, 0),
          mean: mean(nums),
          median: median(nums),
          min: Math.min(...nums),
          max: Math.max(...nums)
        };
        if (nums.length > 1) out.stdev = stdev(nums);
        return out;
      }
    },
    {
      name: "format_number",
      displayName: "Format Number",
      description: "Format with thousand separators",
      category: "numerical",
      inputType: "number",
      outputType: "string",
      params: [
        { name: "decimals", type: "number", default: 2, description: "Decimal places" }
      ],
      transform(input, { decimals = 2 } = {}) {
        const num = parseFloat(input);
        const parts = num.toFixed(decimals).split(".");
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        return parts.join(".");
      }
    },
    {
      name: "random",
      displayName: "Random Number",
      description: "Generate random number in range",
      category: "numerical",
      inputType: "any",
      outputType: "number",
      params: [
        { name: "min_value", type: "number", default: 0, description: "Minimum value" },
        { name: "max_value", type: "number", default: 1, description: "Maximum value" }
      ],
      transform(_input, { min_value = 0, max_value = 1 } = {}) {
        return min_value + Math.random() * (max_value - min_value);
      }
    },
    {
      name: "pow",
      displayName: "Power",
      description: "Raise to a power",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [
        { name: "exponent", type: "number", default: 2, description: "Exponent" }
      ],
      transform(input, { exponent = 2 } = {}) {
        return parseFloat(input) ** exponent;
      }
    },
    {
      name: "sqrt",
      displayName: "Square Root",
      description: "Compute square root",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [],
      transform(input) {
        const v = parseFloat(input);
        if (v < 0) throw new Error("sqrt not defined for negative values");
        return Math.sqrt(v);
      }
    },
    {
      name: "log",
      displayName: "Logarithm",
      description: "Compute logarithm (natural or custom base)",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [
        { name: "base", type: "number", default: null, description: "Log base (null = natural log)" }
      ],
      transform(input, { base = null } = {}) {
        const v = parseFloat(input);
        if (v <= 0) throw new Error("log requires v > 0");
        if (base === null || base === void 0) return Math.log(v);
        return Math.log(v) / Math.log(base);
      }
    },
    {
      name: "shorthand_number",
      displayName: "Parse Shorthand Number",
      description: "Parse 1.2k, $3.5m, 50% etc.",
      category: "numerical",
      inputType: "any",
      outputType: "number",
      params: [
        { name: "allow_currency", type: "boolean", default: true, description: "Accept currency prefix" },
        { name: "allow_percent", type: "boolean", default: true, description: "Accept % suffix" },
        { name: "percent_base", type: "number", default: 1, description: "Base for percentage (1.0 => fraction)" }
      ],
      transform(input, { allow_currency = true, allow_percent = true, percent_base = 1 } = {}) {
        if (typeof input === "number") return input;
        return parseShorthandNumber(input, {
          allowCurrency: allow_currency,
          allowPercent: allow_percent,
          percentBase: percent_base
        });
      }
    },
    {
      name: "shorthand_decimal",
      displayName: "Parse Shorthand Decimal",
      description: "Parse shorthand notation (returns float)",
      category: "numerical",
      inputType: "any",
      outputType: "number",
      params: [
        { name: "allow_currency", type: "boolean", default: true, description: "Accept currency prefix" },
        { name: "allow_percent", type: "boolean", default: true, description: "Accept % suffix" },
        { name: "percent_base", type: "number", default: 1, description: "Base for percentage (1.0 => fraction)" }
      ],
      transform(input, { allow_currency = true, allow_percent = true, percent_base = 1 } = {}) {
        if (typeof input === "number") return input;
        return parseShorthandNumber(input, {
          allowCurrency: allow_currency,
          allowPercent: allow_percent,
          percentBase: percent_base
        });
      }
    },
    {
      name: "percentage_calc",
      displayName: "Percentage Calculate",
      description: "Convert to percentage (0.5 -> 50)",
      category: "numerical",
      inputType: "number",
      outputType: "number",
      params: [],
      transform(input) {
        const v = parseFloat(input);
        return Math.abs(v) <= 1 ? v * 100 : v;
      }
    }
  ];

  // src/transformers/date.js
  function parseDateString(str, format) {
    const tokens = {
      "%Y": "(?<Y>\\d{4})",
      "%m": "(?<m>\\d{2})",
      "%d": "(?<d>\\d{2})",
      "%H": "(?<H>\\d{2})",
      "%M": "(?<M>\\d{2})",
      "%S": "(?<S>\\d{2})"
    };
    let pattern = format.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&");
    for (const [tok, re] of Object.entries(tokens)) {
      pattern = pattern.replace(tok.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), re);
    }
    const match = new RegExp(`^${pattern}$`).exec(str);
    if (!match) throw new Error(`Date '${str}' doesn't match format '${format}'`);
    const g = match.groups || {};
    return new Date(
      parseInt(g.Y || "1970", 10),
      parseInt(g.m || "1", 10) - 1,
      parseInt(g.d || "1", 10),
      parseInt(g.H || "0", 10),
      parseInt(g.M || "0", 10),
      parseInt(g.S || "0", 10)
    );
  }
  var dateTransformers = [
    {
      name: "date",
      displayName: "Parse Date",
      description: "Parse date string to ISO format",
      category: "date",
      inputType: "string",
      outputType: "string",
      params: [
        { name: "format", type: "string", default: "%Y-%m-%d", description: "Date format (strftime codes)" }
      ],
      transform(input, { format = "%Y-%m-%d" } = {}) {
        const d = parseDateString(input, format);
        return d.toISOString();
      }
    },
    {
      name: "duration_calc",
      displayName: "Duration Calculator",
      description: "Calculate duration between dates",
      category: "date",
      inputType: "string",
      outputType: "number",
      params: [
        { name: "unit", type: "string", default: "days", description: "Unit", options: ["days", "months", "years"] },
        { name: "format", type: "string", default: "%Y-%m-%d", description: "Date format" },
        { name: "end", type: "string", default: null, description: "End date (null = today)" }
      ],
      transform(input, { unit = "days", format = "%Y-%m-%d", end = null } = {}) {
        const startDate = parseDateString(input, format);
        const endDate = end ? parseDateString(end, format) : /* @__PURE__ */ new Date();
        if (unit === "days") {
          const msPerDay = 864e5;
          const startUTC = Date.UTC(startDate.getFullYear(), startDate.getMonth(), startDate.getDate());
          const endUTC = Date.UTC(endDate.getFullYear(), endDate.getMonth(), endDate.getDate());
          return Math.round((endUTC - startUTC) / msPerDay);
        } else if (unit === "months") {
          return (endDate.getFullYear() - startDate.getFullYear()) * 12 + endDate.getMonth() - startDate.getMonth();
        } else if (unit === "years") {
          return endDate.getFullYear() - startDate.getFullYear();
        }
        throw new Error(`Invalid unit: ${unit}`);
      }
    },
    {
      name: "age_calc",
      displayName: "Age Calculator",
      description: "Calculate age in years from birth date",
      category: "date",
      inputType: "string",
      outputType: "number",
      params: [
        { name: "reference_date", type: "string", default: null, description: "Reference date (null = today)" }
      ],
      transform(input, { reference_date = null } = {}) {
        const birth = parseDateString(input, "%Y-%m-%d");
        const ref = reference_date ? parseDateString(reference_date, "%Y-%m-%d") : /* @__PURE__ */ new Date();
        let years = ref.getFullYear() - birth.getFullYear();
        const refMonth = ref.getMonth(), refDay = ref.getDate();
        const birthMonth = birth.getMonth(), birthDay = birth.getDate();
        if (refMonth < birthMonth || refMonth === birthMonth && refDay < birthDay) {
          years -= 1;
        }
        return years;
      }
    }
  ];

  // src/transformers/validation.js
  var TRUE_VALUES = /* @__PURE__ */ new Set(["true", "1", "yes", "y", "t", "on", "si", "s\xED", "verdadero"]);
  var FALSE_VALUES = /* @__PURE__ */ new Set(["false", "0", "no", "n", "f", "off", "falso"]);
  var validationTransformers = [
    {
      name: "bool",
      displayName: "Boolean",
      description: "Convert to boolean (yes/no/true/false/1/0)",
      category: "validation",
      inputType: "any",
      outputType: "boolean",
      params: [],
      transform(input) {
        if (typeof input === "boolean") return input;
        const s = String(input).trim().toLowerCase();
        if (TRUE_VALUES.has(s)) return true;
        if (FALSE_VALUES.has(s)) return false;
        return null;
      }
    },
    {
      name: "email_validator",
      displayName: "Email Validator",
      description: "Validate email address format",
      category: "validation",
      inputType: "string",
      outputType: "string",
      params: [
        { name: "allowed_domains", type: "array", default: null, description: "Restrict to domains" }
      ],
      transform(input, { allowed_domains = null } = {}) {
        const value = String(input).trim();
        if (!/^[^@]+@[^@]+\.[^@]+$/.test(value)) return null;
        if (allowed_domains && Array.isArray(allowed_domains)) {
          const domain = value.split("@")[1];
          if (!allowed_domains.includes(domain)) return null;
        }
        return value;
      }
    },
    {
      name: "phone_formatter",
      displayName: "Phone Formatter",
      description: "Format 10-digit phone number",
      category: "validation",
      inputType: "string",
      outputType: "string",
      params: [
        { name: "format", type: "string", default: "({area}) {prefix}-{line}", description: "Output format" }
      ],
      transform(input, { format = "({area}) {prefix}-{line}" } = {}) {
        let digits = String(input).replace(/\D/g, "");
        if (digits.length === 11 && digits[0] === "1") {
          digits = digits.slice(1);
        }
        if (digits.length !== 10) {
          throw new Error("Invalid phone number length");
        }
        return format.replace("{area}", digits.slice(0, 3)).replace("{prefix}", digits.slice(3, 6)).replace("{line}", digits.slice(6));
      }
    },
    {
      name: "credit_card_check",
      displayName: "Credit Card Validator",
      description: "Validate via Luhn algorithm",
      category: "validation",
      inputType: "string",
      outputType: "string",
      params: [
        { name: "mask", type: "boolean", default: false, description: "Mask middle digits" }
      ],
      transform(input, { mask = false } = {}) {
        const original = String(input);
        const digits = original.replace(/\D/g, "");
        if (digits.length < 13 || digits.length > 19) return null;
        let sum = 0;
        let alt = false;
        for (let i = digits.length - 1; i >= 0; i--) {
          let d = parseInt(digits[i], 10);
          if (alt) {
            d *= 2;
            if (d > 9) d -= 9;
          }
          sum += d;
          alt = !alt;
        }
        if (sum % 10 !== 0) return null;
        if (mask) {
          const visible = 4;
          const maskedLen = digits.length - 2 * visible;
          return digits.slice(0, visible) + "*".repeat(maskedLen) + digits.slice(-visible);
        }
        return original;
      }
    },
    {
      name: "type_enforcer",
      displayName: "Type Enforcer",
      description: "Convert value to target type",
      category: "validation",
      inputType: "any",
      outputType: "any",
      params: [
        { name: "target_type", type: "string", default: "str", description: "Target type", options: ["int", "float", "str", "bool"] }
      ],
      transform(input, { target_type = "str" } = {}) {
        switch (target_type) {
          case "int": {
            const n = typeof input === "string" ? parseInt(parseFloat(input), 10) : parseInt(input, 10);
            if (isNaN(n)) throw new Error(`Cannot convert to int: ${input}`);
            return n;
          }
          case "float": {
            const n = parseFloat(input);
            if (isNaN(n)) throw new Error(`Cannot convert to float: ${input}`);
            return n;
          }
          case "str":
            return String(input);
          case "bool": {
            if (typeof input === "boolean") return input;
            if (typeof input === "string") {
              const s = input.toLowerCase();
              if (["true", "1", "yes", "y"].includes(s)) return true;
              if (["false", "0", "no", "n"].includes(s)) return false;
            }
            return Boolean(input);
          }
          default:
            throw new Error(`Unsupported type: ${target_type}`);
        }
      }
    }
  ];

  // src/transformers/json-transforms.js
  function getValueByPath(data, path) {
    if (!path || data == null) return void 0;
    if (path.includes("[*]")) {
      const [before, after] = path.split("[*]", 2);
      let current2 = before ? getValueByPath(data, before) : data;
      if (!Array.isArray(current2)) return void 0;
      if (!after || after === "") return current2;
      const rest = after.startsWith(".") ? after.slice(1) : after;
      return current2.map((item) => getValueByPath(item, rest));
    }
    const parts = path.split(/\.(?![^\[]*\])/);
    let current = data;
    for (const part of parts) {
      if (!part) continue;
      if (current == null) return void 0;
      const match = /^(.+?)\[(\d+)\]$/.exec(part);
      if (match) {
        const [, key, index] = match;
        current = current[key];
        if (!Array.isArray(current)) return void 0;
        const idx = parseInt(index, 10);
        current = idx >= 0 && idx < current.length ? current[idx] : void 0;
      } else {
        current = typeof current === "object" ? current[part] : void 0;
      }
    }
    return current;
  }
  function validateSchema(data, schema) {
    if (!schema || typeof schema !== "object") return true;
    if ("type" in schema) {
      const t = schema.type;
      if (t === "object" && (typeof data !== "object" || data === null || Array.isArray(data))) return false;
      if (t === "array" && !Array.isArray(data)) return false;
      if (t === "string" && typeof data !== "string") return false;
      if (t === "number" && typeof data !== "number") return false;
      if (t === "boolean" && typeof data !== "boolean") return false;
      if (t === "null" && data !== null) return false;
    }
    if (schema.properties && typeof data === "object" && data !== null) {
      for (const [key, propSchema] of Object.entries(schema.properties)) {
        if (!(key in data)) {
          const required = schema.required || [key];
          if (required.includes(key)) return false;
          continue;
        }
        if (!validateSchema(data[key], propSchema)) return false;
      }
    }
    if (schema.items && Array.isArray(data)) {
      return data.every((item) => validateSchema(item, schema.items));
    }
    return true;
  }
  var jsonTransformers = [
    {
      name: "json_parse",
      displayName: "JSON Parse",
      description: "Parse JSON string with optional schema validation",
      category: "json",
      inputType: "string",
      outputType: "any",
      params: [
        { name: "strict", type: "boolean", default: true, description: "Throw on invalid JSON" },
        { name: "schema", type: "object", default: null, description: "JSON schema for validation" }
      ],
      transform(input, { strict = true, schema = null } = {}) {
        let data;
        try {
          data = JSON.parse(input);
        } catch (e) {
          if (strict) throw new Error(`Invalid JSON: ${e.message}`);
          return input;
        }
        if (schema && !validateSchema(data, schema)) {
          throw new Error("JSON data does not match schema");
        }
        return data;
      }
    },
    {
      name: "json_extract",
      displayName: "JSON Extract",
      description: "Extract values using dot-notation paths",
      category: "json",
      inputType: "any",
      outputType: "any",
      params: [
        { name: "path", type: "string", default: "", description: "Dot-notation path (e.g. user.name, items[0], items[*].id)" },
        { name: "default_value", type: "any", default: null, description: "Default if path not found" }
      ],
      transform(input, { path = "", default_value = null } = {}) {
        if (!path) return input;
        const data = typeof input === "string" ? JSON.parse(input) : input;
        const result = getValueByPath(data, path);
        return result !== void 0 ? result : default_value;
      }
    }
  ];

  // src/transformers/html-transforms.js
  var htmlTransformers = [
    {
      name: "strip_html_tags",
      displayName: "Strip HTML Tags",
      description: "Remove all HTML tags, keep text content",
      category: "html",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        let text = String(input);
        text = text.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "");
        text = text.replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "");
        text = text.replace(/<[^>]+>/g, "");
        text = text.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&#39;/g, "'").replace(/&nbsp;/g, " ");
        return text.replace(/\s+/g, " ").trim();
      }
    },
    {
      name: "html_sanitize",
      displayName: "HTML Sanitize",
      description: "Remove dangerous tags (script, style, iframe, etc.)",
      category: "html",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        let html = String(input);
        const dangerousTags = ["script", "style", "iframe", "object", "embed", "frame", "frameset", "meta", "link"];
        for (const tag of dangerousTags) {
          html = html.replace(new RegExp(`<${tag}\\b[^>]*>[\\s\\S]*?<\\/${tag}>`, "gi"), "");
          html = html.replace(new RegExp(`<${tag}\\b[^>]*\\/?>`, "gi"), "");
        }
        html = html.replace(/\s+on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, "");
        html = html.replace(/(href|src|action)\s*=\s*(?:"javascript:[^"]*"|'javascript:[^']*')/gi, "");
        return html;
      }
    },
    {
      name: "link_extraction",
      displayName: "Extract Links",
      description: "Extract all href URLs from anchor tags",
      category: "html",
      inputType: "string",
      outputType: "array",
      params: [],
      transform(input) {
        const links = [];
        const re = /<a\s[^>]*href\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))[^>]*>/gi;
        let match;
        while ((match = re.exec(input)) !== null) {
          links.push(match[1] || match[2] || match[3]);
        }
        return links;
      }
    },
    {
      name: "extract_domain",
      displayName: "Extract Domain",
      description: "Extract domain from URL",
      category: "html",
      inputType: "string",
      outputType: "string",
      params: [],
      transform(input) {
        try {
          const url = input.startsWith("//") ? `https:${input}` : input;
          return new URL(url).hostname;
        } catch {
          const match = /^(?:https?:)?\/\/([^/:?#]+)/.exec(input);
          return match ? match[1] : "";
        }
      }
    },
    {
      name: "resolve_url",
      displayName: "Resolve URL",
      description: "Resolve relative URL against a base",
      category: "html",
      inputType: "string",
      outputType: "string",
      params: [
        { name: "base_url", type: "string", default: "", description: "Base URL" }
      ],
      transform(input, { base_url = "" } = {}) {
        if (!base_url) return input;
        try {
          return new URL(input, base_url).href;
        } catch {
          return input;
        }
      }
    }
  ];

  // src/index.js
  var TukuyRegistry = class {
    constructor() {
      this.transformers = /* @__PURE__ */ new Map();
      this.categories = /* @__PURE__ */ new Map();
    }
    /**
     * Register a transformer object.
     */
    register(transformer) {
      this.transformers.set(transformer.name, transformer);
      const cat = this.categories.get(transformer.category) || [];
      cat.push(transformer.name);
      this.categories.set(transformer.category, cat);
    }
    /**
     * Get a transformer by name. Returns undefined if not found.
     */
    get(name) {
      return this.transformers.get(name);
    }
    /**
     * Check if a transformer exists.
     */
    has(name) {
      return this.transformers.has(name);
    }
    /**
     * Run a transformer. Handles both sync and async.
     *
     * @param {string} name - Transformer name
     * @param {*} input - Input value
     * @param {object} options - Transformer-specific options
     * @returns {Promise<*>} Transformed value
     */
    async transform(name, input, options = {}) {
      const t = this.get(name);
      if (!t) throw new Error(`Unknown transformer: ${name}`);
      return t.async ? await t.transform(input, options) : t.transform(input, options);
    }
    /**
     * Run a transformer synchronously. Throws if transformer is async.
     */
    transformSync(name, input, options = {}) {
      const t = this.get(name);
      if (!t) throw new Error(`Unknown transformer: ${name}`);
      if (t.async) throw new Error(`Transformer '${name}' is async \u2014 use transform() instead`);
      return t.transform(input, options);
    }
    /**
     * Chain multiple transformers: input → A → B → C → output.
     *
     * @param {Array<string|{name: string, options: object}>} steps
     * @param {*} input - Initial input
     * @returns {Promise<{output: *, intermediates: Array}>}
     */
    async chain(steps, input) {
      const intermediates = [];
      let value = input;
      for (const step of steps) {
        const name = typeof step === "string" ? step : step.name;
        const options = typeof step === "string" ? {} : step.options || {};
        value = await this.transform(name, value, options);
        intermediates.push({ name, value });
      }
      return { output: value, intermediates };
    }
    /**
     * List transformer names, optionally filtered by category.
     */
    list(category = null) {
      if (category) return this.categories.get(category) || [];
      return Array.from(this.transformers.keys());
    }
    /**
     * Get all category names.
     */
    getCategories() {
      return Array.from(this.categories.keys());
    }
    /**
     * Get metadata for all transformers (for UI rendering).
     */
    getMetadata() {
      return Array.from(this.transformers.values()).map((t) => ({
        name: t.name,
        displayName: t.displayName,
        description: t.description,
        category: t.category,
        params: t.params || [],
        async: t.async || false,
        inputType: t.inputType || "string",
        outputType: t.outputType || "string"
      }));
    }
    /**
     * Get metadata grouped by category.
     */
    getMetadataByCategory() {
      const result = {};
      for (const [category, names] of this.categories) {
        result[category] = names.map((name) => {
          const t = this.transformers.get(name);
          return {
            name: t.name,
            displayName: t.displayName,
            description: t.description,
            params: t.params || [],
            async: t.async || false
          };
        });
      }
      return result;
    }
    /**
     * Total number of registered transformers.
     */
    get size() {
      return this.transformers.size;
    }
  };
  var tukuy = new TukuyRegistry();
  var allTransformers = [
    ...textTransformers,
    ...encodingTransformers,
    ...cryptoTransformers,
    ...numericalTransformers,
    ...dateTransformers,
    ...validationTransformers,
    ...jsonTransformers,
    ...htmlTransformers
  ];
  for (const t of allTransformers) {
    tukuy.register(t);
  }
  return __toCommonJS(index_exports);
})();
//# sourceMappingURL=tukuy.iife.js.map
