/**
 * Tukuy Text Transformers — JS port
 *
 * Ports of tukuy/plugins/text Python transformers.
 * All pure logic, no external dependencies.
 */

export const textTransformers = [
  {
    name: 'strip',
    displayName: 'Strip',
    description: 'Remove leading/trailing whitespace',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return input.trim();
    },
  },

  {
    name: 'lowercase',
    displayName: 'Lowercase',
    description: 'Convert to lowercase',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return input.toLowerCase();
    },
  },

  {
    name: 'uppercase',
    displayName: 'Uppercase',
    description: 'Convert to uppercase',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return input.toUpperCase();
    },
  },

  {
    name: 'title_case',
    displayName: 'Title Case',
    description: 'Capitalize the first letter of each word',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      // Matches Python's string.capwords: split on whitespace, capitalize each, rejoin
      return input.split(/\s+/).filter(w => w).map(w =>
        w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()
      ).join(' ');
    },
  },

  {
    name: 'camel_case',
    displayName: 'camelCase',
    description: 'Convert to camelCase',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      const words = input.trim().split(/[\s_-]+/).filter(w => w).map(w => w.toLowerCase());
      if (words.length === 0) return '';
      return words[0] + words.slice(1).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('');
    },
  },

  {
    name: 'snake_case',
    displayName: 'snake_case',
    description: 'Convert to snake_case',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      const words = input.trim().split(/[\s\-_]+/).filter(w => w).map(w => w.toLowerCase());
      return words.join('_');
    },
  },

  {
    name: 'slugify',
    displayName: 'Slugify',
    description: 'Convert text to URL-friendly slug',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      let text = input.toLowerCase();
      text = text.replace(/[\s_]+/g, '-');
      text = text.replace(/[^\w-]/g, '');
      text = text.replace(/^-+|-+$/g, '');
      return text;
    },
  },

  {
    name: 'truncate',
    displayName: 'Truncate',
    description: 'Truncate text with suffix',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [
      { name: 'length', type: 'number', default: 50, description: 'Maximum length' },
      { name: 'suffix', type: 'string', default: '...', description: 'Suffix to append' },
    ],
    transform(input, { length = 50, suffix = '...' } = {}) {
      if (input.length <= length) return input;

      const truncateLength = length - suffix.length;
      if (truncateLength <= 0) return suffix;

      // Don't break words if possible
      const slice = input.slice(0, truncateLength);
      if (slice.includes(' ')) {
        const lastSpace = slice.lastIndexOf(' ');
        if (lastSpace > 0) return input.slice(0, lastSpace) + suffix;
      }

      return slice + suffix;
    },
  },

  {
    name: 'remove_emojis',
    displayName: 'Remove Emojis',
    description: 'Strip emoji characters from text',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return input.replace(
        /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}]+/gu,
        ''
      );
    },
  },

  {
    name: 'redact_sensitive',
    displayName: 'Redact Sensitive',
    description: 'Mask credit card numbers (keep first/last 4 digits)',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return input.replace(/\b\d{13,16}\b/g, match =>
        match.slice(0, 4) + '*'.repeat(match.length - 8) + match.slice(-4)
      );
    },
  },

  {
    name: 'regex',
    displayName: 'Regex',
    description: 'Regex search or replace',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [
      { name: 'pattern', type: 'string', default: '', description: 'Regular expression pattern' },
      { name: 'template', type: 'string', default: null, description: 'Replacement template (null = extract match)' },
    ],
    transform(input, { pattern = '', template = null } = {}) {
      if (!pattern) return input;
      if (template !== null && template !== undefined) {
        return input.replace(new RegExp(pattern, 'g'), template);
      }
      const match = new RegExp(pattern).exec(input);
      return match ? match[0] : input;
    },
  },

  {
    name: 'split',
    displayName: 'Split',
    description: 'Split string and extract a part by index',
    category: 'text',
    inputType: 'string',
    outputType: 'string',
    params: [
      { name: 'delimiter', type: 'string', default: ':', description: 'Character to split on' },
      { name: 'index', type: 'number', default: -1, description: 'Index of part to extract (-1 = last)' },
    ],
    transform(input, { delimiter = ':', index = -1 } = {}) {
      const parts = input.split(delimiter);
      let idx = index;
      if (idx < 0) idx = parts.length + idx;
      if (idx >= 0 && idx < parts.length) return parts[idx].trim();
      return input;
    },
  },
];
