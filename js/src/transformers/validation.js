/**
 * Tukuy Validation Transformers — JS port
 *
 * Ports of tukuy/plugins/validation Python transformers.
 * Pure JS — no dependencies.
 */

const TRUE_VALUES = new Set(['true', '1', 'yes', 'y', 't', 'on', 'si', 'sí', 'verdadero']);
const FALSE_VALUES = new Set(['false', '0', 'no', 'n', 'f', 'off', 'falso']);

export const validationTransformers = [
  {
    name: 'bool',
    displayName: 'Boolean',
    description: 'Convert to boolean (yes/no/true/false/1/0)',
    category: 'validation',
    inputType: 'any',
    outputType: 'boolean',
    params: [],
    transform(input) {
      if (typeof input === 'boolean') return input;
      const s = String(input).trim().toLowerCase();
      if (TRUE_VALUES.has(s)) return true;
      if (FALSE_VALUES.has(s)) return false;
      return null;
    },
  },

  {
    name: 'email_validator',
    displayName: 'Email Validator',
    description: 'Validate email address format',
    category: 'validation',
    inputType: 'string',
    outputType: 'string',
    params: [
      { name: 'allowed_domains', type: 'array', default: null, description: 'Restrict to domains' },
    ],
    transform(input, { allowed_domains = null } = {}) {
      const value = String(input).trim();
      if (!/^[^@]+@[^@]+\.[^@]+$/.test(value)) return null;

      if (allowed_domains && Array.isArray(allowed_domains)) {
        const domain = value.split('@')[1];
        if (!allowed_domains.includes(domain)) return null;
      }
      return value;
    },
  },

  {
    name: 'phone_formatter',
    displayName: 'Phone Formatter',
    description: 'Format 10-digit phone number',
    category: 'validation',
    inputType: 'string',
    outputType: 'string',
    params: [
      { name: 'format', type: 'string', default: '({area}) {prefix}-{line}', description: 'Output format' },
    ],
    transform(input, { format = '({area}) {prefix}-{line}' } = {}) {
      let digits = String(input).replace(/\D/g, '');

      if (digits.length === 11 && digits[0] === '1') {
        digits = digits.slice(1);
      }

      if (digits.length !== 10) {
        throw new Error('Invalid phone number length');
      }

      return format
        .replace('{area}', digits.slice(0, 3))
        .replace('{prefix}', digits.slice(3, 6))
        .replace('{line}', digits.slice(6));
    },
  },

  {
    name: 'credit_card_check',
    displayName: 'Credit Card Validator',
    description: 'Validate via Luhn algorithm',
    category: 'validation',
    inputType: 'string',
    outputType: 'string',
    params: [
      { name: 'mask', type: 'boolean', default: false, description: 'Mask middle digits' },
    ],
    transform(input, { mask = false } = {}) {
      const original = String(input);
      const digits = original.replace(/\D/g, '');

      if (digits.length < 13 || digits.length > 19) return null;

      // Luhn algorithm
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
        const maskedLen = digits.length - (2 * visible);
        return digits.slice(0, visible) + '*'.repeat(maskedLen) + digits.slice(-visible);
      }

      return original;
    },
  },

  {
    name: 'type_enforcer',
    displayName: 'Type Enforcer',
    description: 'Convert value to target type',
    category: 'validation',
    inputType: 'any',
    outputType: 'any',
    params: [
      { name: 'target_type', type: 'string', default: 'str', description: 'Target type', options: ['int', 'float', 'str', 'bool'] },
    ],
    transform(input, { target_type = 'str' } = {}) {
      switch (target_type) {
        case 'int': {
          const n = typeof input === 'string' ? parseInt(parseFloat(input), 10) : parseInt(input, 10);
          if (isNaN(n)) throw new Error(`Cannot convert to int: ${input}`);
          return n;
        }
        case 'float': {
          const n = parseFloat(input);
          if (isNaN(n)) throw new Error(`Cannot convert to float: ${input}`);
          return n;
        }
        case 'str':
          return String(input);
        case 'bool': {
          if (typeof input === 'boolean') return input;
          if (typeof input === 'string') {
            const s = input.toLowerCase();
            if (['true', '1', 'yes', 'y'].includes(s)) return true;
            if (['false', '0', 'no', 'n'].includes(s)) return false;
          }
          return Boolean(input);
        }
        default:
          throw new Error(`Unsupported type: ${target_type}`);
      }
    },
  },
];
