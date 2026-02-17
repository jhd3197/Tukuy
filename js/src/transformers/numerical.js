/**
 * Tukuy Numerical Transformers — JS port
 *
 * Ports of tukuy/plugins/numerical Python transformers.
 * Pure JS math — no dependencies.
 */

// ── Shorthand number parsing utility ──────────────────────────────────

const SUFFIX_MAP = {
  k: 1_000,
  m: 1_000_000,
  b: 1_000_000_000,
  t: 1_000_000_000_000,
  bn: 1_000_000_000,
  mm: 1_000_000,
  tr: 1_000_000_000_000,
};

const CURRENCY_PREFIX = new Set('$€£¥₿₽₹₩₫₪₴₦₲₵₡₱₺₸');
const NUM_STRIP_RE = /[,\s_]/g;
const NUMBER_RE = /^\s*([-+]?)\s*((?:\d+(?:[,_]\d+)*|\d*\.\d+|\d+)(?:e[-+]?\d+)?)\s*([a-z]{1,2})?\s*$/i;

function stripCurrencyPrefix(s) {
  return s && CURRENCY_PREFIX.has(s[0]) ? s.slice(1).trimStart() : s;
}

function parseShorthandNumber(value, { allowCurrency = true, allowPercent = true, percentBase = 1.0 } = {}) {
  if (value == null) throw new Error('Null/undefined value');
  if (typeof value === 'number') return value;

  let s = String(value).trim();
  if (!s) throw new Error('Empty string');

  if (allowCurrency) s = stripCurrencyPrefix(s);

  let isPercent = false;
  if (allowPercent && s.endsWith('%')) {
    isPercent = true;
    s = s.slice(0, -1).trim();
  }

  const core = s.replace(NUM_STRIP_RE, '');
  const m = NUMBER_RE.exec(core);
  if (!m) throw new Error(`Invalid number format: ${value}`);

  const body = m[2];
  const suffix = (m[3] || '').toLowerCase();

  let multiplier = 1;
  if (suffix) {
    multiplier = SUFFIX_MAP[suffix];
    if (multiplier === undefined) throw new Error(`Unknown numeric suffix '${suffix}' in ${value}`);
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

// ── Stats helpers ─────────────────────────────────────────────────────

function mean(arr) { return arr.reduce((a, b) => a + b, 0) / arr.length; }
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

// ── Transformers ──────────────────────────────────────────────────────

export const numericalTransformers = [
  {
    name: 'int',
    displayName: 'Integer',
    description: 'Convert to integer',
    category: 'numerical',
    inputType: 'any',
    outputType: 'number',
    params: [
      { name: 'min_value', type: 'number', default: null, description: 'Minimum allowed value' },
      { name: 'max_value', type: 'number', default: null, description: 'Maximum allowed value' },
    ],
    transform(input, { min_value = null, max_value = null } = {}) {
      let value = input;
      if (typeof value === 'string') {
        value = value.replace(/[^\d-]/g, '');
      }
      const result = Math.trunc(parseFloat(value));
      if (isNaN(result)) throw new Error(`Invalid integer: ${input}`);
      if (min_value !== null && result < min_value) throw new Error(`Value ${result} < minimum ${min_value}`);
      if (max_value !== null && result > max_value) throw new Error(`Value ${result} > maximum ${max_value}`);
      return result;
    },
  },

  {
    name: 'float',
    displayName: 'Float',
    description: 'Convert to float',
    category: 'numerical',
    inputType: 'any',
    outputType: 'number',
    params: [
      { name: 'min_value', type: 'number', default: null, description: 'Minimum allowed value' },
      { name: 'max_value', type: 'number', default: null, description: 'Maximum allowed value' },
    ],
    transform(input, { min_value = null, max_value = null } = {}) {
      let value = input;
      if (typeof value === 'string') {
        value = value.replace(/[^\d.\-]/g, '');
      }
      const result = parseFloat(value);
      if (isNaN(result)) throw new Error(`Invalid float: ${input}`);
      if (min_value !== null && result < min_value) throw new Error(`Value ${result} < minimum ${min_value}`);
      if (max_value !== null && result > max_value) throw new Error(`Value ${result} > maximum ${max_value}`);
      return result;
    },
  },

  {
    name: 'round',
    displayName: 'Round',
    description: 'Round to N decimal places',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [
      { name: 'decimals', type: 'number', default: 0, description: 'Decimal places' },
    ],
    transform(input, { decimals = 0 } = {}) {
      const factor = 10 ** decimals;
      return Math.round(parseFloat(input) * factor) / factor;
    },
  },

  {
    name: 'currency_convert',
    displayName: 'Currency Convert',
    description: 'Multiply by exchange rate',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [
      { name: 'rate', type: 'number', default: 1, description: 'Exchange rate' },
    ],
    transform(input, { rate = 1 } = {}) {
      if (rate == null) throw new Error('Exchange rate not provided');
      return parseFloat(input) * rate;
    },
  },

  {
    name: 'unit_convert',
    displayName: 'Unit Convert',
    description: 'Multiply by conversion rate',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [
      { name: 'rate', type: 'number', default: 1, description: 'Conversion rate' },
    ],
    transform(input, { rate = 1 } = {}) {
      if (rate == null) throw new Error('Conversion rate not provided');
      return parseFloat(input) * rate;
    },
  },

  {
    name: 'math_operation',
    displayName: 'Math Operation',
    description: 'Perform add/subtract/multiply/divide',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [
      { name: 'operation', type: 'string', default: 'add', description: 'Operation', options: ['add', 'subtract', 'multiply', 'divide'] },
      { name: 'operand', type: 'number', default: 0, description: 'Operand value' },
    ],
    transform(input, { operation = 'add', operand = 0 } = {}) {
      const x = parseFloat(input);
      const y = parseFloat(operand);
      switch (operation) {
        case 'add': return x + y;
        case 'subtract': return x - y;
        case 'multiply': return x * y;
        case 'divide':
          if (y === 0) throw new Error('Division by zero');
          return x / y;
        default:
          throw new Error(`Invalid operation '${operation}'. Use: add, subtract, multiply, divide`);
      }
    },
  },

  {
    name: 'extract_numbers',
    displayName: 'Extract Numbers',
    description: 'Extract all numbers from text',
    category: 'numerical',
    inputType: 'string',
    outputType: 'array',
    params: [],
    transform(input) {
      return (String(input).match(/\d+(?:\.\d+)?/g) || []);
    },
  },

  {
    name: 'abs',
    displayName: 'Absolute Value',
    description: 'Compute |x|',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [],
    transform(input) {
      return Math.abs(parseFloat(input));
    },
  },

  {
    name: 'floor',
    displayName: 'Floor',
    description: 'Round down to nearest integer',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [],
    transform(input) {
      return Math.floor(parseFloat(input));
    },
  },

  {
    name: 'ceil',
    displayName: 'Ceiling',
    description: 'Round up to nearest integer',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [],
    transform(input) {
      return Math.ceil(parseFloat(input));
    },
  },

  {
    name: 'clamp',
    displayName: 'Clamp',
    description: 'Clamp value between min and max',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [
      { name: 'min_value', type: 'number', default: null, description: 'Minimum value' },
      { name: 'max_value', type: 'number', default: null, description: 'Maximum value' },
    ],
    transform(input, { min_value = null, max_value = null } = {}) {
      let v = parseFloat(input);
      if (min_value !== null) v = Math.max(v, min_value);
      if (max_value !== null) v = Math.min(v, max_value);
      return v;
    },
  },

  {
    name: 'scale',
    displayName: 'Scale',
    description: 'Scale from one range to another',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [
      { name: 'src_min', type: 'number', default: 0, description: 'Source range min' },
      { name: 'src_max', type: 'number', default: 1, description: 'Source range max' },
      { name: 'dst_min', type: 'number', default: 0, description: 'Dest range min' },
      { name: 'dst_max', type: 'number', default: 1, description: 'Dest range max' },
    ],
    transform(input, { src_min = 0, src_max = 1, dst_min = 0, dst_max = 1 } = {}) {
      const v = parseFloat(input);
      if (src_max === src_min) return dst_min;
      return dst_min + (v - src_min) * (dst_max - dst_min) / (src_max - src_min);
    },
  },

  {
    name: 'stats',
    displayName: 'Statistics',
    description: 'Compute count/sum/mean/median/min/max/stdev',
    category: 'numerical',
    inputType: 'array',
    outputType: 'object',
    params: [],
    transform(input) {
      const nums = (Array.isArray(input) ? input : [])
        .filter(v => typeof v === 'number' && !isNaN(v))
        .map(Number);
      if (!nums.length) return {};
      const out = {
        count: nums.length,
        sum: nums.reduce((a, b) => a + b, 0),
        mean: mean(nums),
        median: median(nums),
        min: Math.min(...nums),
        max: Math.max(...nums),
      };
      if (nums.length > 1) out.stdev = stdev(nums);
      return out;
    },
  },

  {
    name: 'format_number',
    displayName: 'Format Number',
    description: 'Format with thousand separators',
    category: 'numerical',
    inputType: 'number',
    outputType: 'string',
    params: [
      { name: 'decimals', type: 'number', default: 2, description: 'Decimal places' },
    ],
    transform(input, { decimals = 2 } = {}) {
      const num = parseFloat(input);
      const parts = num.toFixed(decimals).split('.');
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      return parts.join('.');
    },
  },

  {
    name: 'random',
    displayName: 'Random Number',
    description: 'Generate random number in range',
    category: 'numerical',
    inputType: 'any',
    outputType: 'number',
    params: [
      { name: 'min_value', type: 'number', default: 0, description: 'Minimum value' },
      { name: 'max_value', type: 'number', default: 1, description: 'Maximum value' },
    ],
    transform(_input, { min_value = 0, max_value = 1 } = {}) {
      return min_value + Math.random() * (max_value - min_value);
    },
  },

  {
    name: 'pow',
    displayName: 'Power',
    description: 'Raise to a power',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [
      { name: 'exponent', type: 'number', default: 2, description: 'Exponent' },
    ],
    transform(input, { exponent = 2 } = {}) {
      return parseFloat(input) ** exponent;
    },
  },

  {
    name: 'sqrt',
    displayName: 'Square Root',
    description: 'Compute square root',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [],
    transform(input) {
      const v = parseFloat(input);
      if (v < 0) throw new Error('sqrt not defined for negative values');
      return Math.sqrt(v);
    },
  },

  {
    name: 'log',
    displayName: 'Logarithm',
    description: 'Compute logarithm (natural or custom base)',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [
      { name: 'base', type: 'number', default: null, description: 'Log base (null = natural log)' },
    ],
    transform(input, { base = null } = {}) {
      const v = parseFloat(input);
      if (v <= 0) throw new Error('log requires v > 0');
      if (base === null || base === undefined) return Math.log(v);
      return Math.log(v) / Math.log(base);
    },
  },

  {
    name: 'shorthand_number',
    displayName: 'Parse Shorthand Number',
    description: 'Parse 1.2k, $3.5m, 50% etc.',
    category: 'numerical',
    inputType: 'any',
    outputType: 'number',
    params: [
      { name: 'allow_currency', type: 'boolean', default: true, description: 'Accept currency prefix' },
      { name: 'allow_percent', type: 'boolean', default: true, description: 'Accept % suffix' },
      { name: 'percent_base', type: 'number', default: 1.0, description: 'Base for percentage (1.0 => fraction)' },
    ],
    transform(input, { allow_currency = true, allow_percent = true, percent_base = 1.0 } = {}) {
      if (typeof input === 'number') return input;
      return parseShorthandNumber(input, {
        allowCurrency: allow_currency,
        allowPercent: allow_percent,
        percentBase: percent_base,
      });
    },
  },

  {
    name: 'shorthand_decimal',
    displayName: 'Parse Shorthand Decimal',
    description: 'Parse shorthand notation (returns float)',
    category: 'numerical',
    inputType: 'any',
    outputType: 'number',
    params: [
      { name: 'allow_currency', type: 'boolean', default: true, description: 'Accept currency prefix' },
      { name: 'allow_percent', type: 'boolean', default: true, description: 'Accept % suffix' },
      { name: 'percent_base', type: 'number', default: 1.0, description: 'Base for percentage (1.0 => fraction)' },
    ],
    transform(input, { allow_currency = true, allow_percent = true, percent_base = 1.0 } = {}) {
      if (typeof input === 'number') return input;
      return parseShorthandNumber(input, {
        allowCurrency: allow_currency,
        allowPercent: allow_percent,
        percentBase: percent_base,
      });
    },
  },

  {
    name: 'percentage_calc',
    displayName: 'Percentage Calculate',
    description: 'Convert to percentage (0.5 -> 50)',
    category: 'numerical',
    inputType: 'number',
    outputType: 'number',
    params: [],
    transform(input) {
      const v = parseFloat(input);
      return Math.abs(v) <= 1 ? v * 100 : v;
    },
  },
];
