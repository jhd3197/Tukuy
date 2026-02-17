/**
 * Tukuy Encoding Transformers — JS port
 *
 * Ports of tukuy/plugins/encoding Python transformers.
 * Uses browser-native APIs (TextEncoder, encodeURIComponent, etc.).
 */

export const encodingTransformers = [
  {
    name: 'url_encode',
    displayName: 'URL Encode',
    description: 'Percent-encode text for URLs',
    category: 'encoding',
    inputType: 'string',
    outputType: 'string',
    params: [
      { name: 'safe', type: 'string', default: '', description: 'Characters to leave unencoded' },
    ],
    transform(input, { safe = '' } = {}) {
      let encoded = encodeURIComponent(input);
      if (safe) {
        for (const ch of safe) {
          encoded = encoded.replaceAll(encodeURIComponent(ch), ch);
        }
      }
      return encoded;
    },
  },

  {
    name: 'url_decode',
    displayName: 'URL Decode',
    description: 'Decode percent-encoded text',
    category: 'encoding',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return decodeURIComponent(input);
    },
  },

  {
    name: 'hex_encode',
    displayName: 'Hex Encode',
    description: 'Encode UTF-8 text to hexadecimal',
    category: 'encoding',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      const bytes = new TextEncoder().encode(input);
      return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
    },
  },

  {
    name: 'hex_decode',
    displayName: 'Hex Decode',
    description: 'Decode hexadecimal to UTF-8 text',
    category: 'encoding',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      const hex = input.replace(/\s/g, '');
      const bytes = new Uint8Array(hex.length / 2);
      for (let i = 0; i < hex.length; i += 2) {
        bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
      }
      return new TextDecoder().decode(bytes);
    },
  },

  {
    name: 'html_entities_encode',
    displayName: 'HTML Entities Encode',
    description: 'Escape HTML special characters',
    category: 'encoding',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
    },
  },

  {
    name: 'html_entities_decode',
    displayName: 'HTML Entities Decode',
    description: 'Unescape HTML entities',
    category: 'encoding',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      // Works in both browser (DOM) and Node (manual map)
      if (typeof document !== 'undefined') {
        const el = document.createElement('textarea');
        el.innerHTML = input;
        return el.value;
      }
      // Node.js fallback
      const entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&#x27;': "'", '&#39;': "'", '&apos;': "'",
      };
      return input.replace(/&(?:#x?[0-9a-fA-F]+|[a-zA-Z]+);/g, match => {
        if (entities[match]) return entities[match];
        if (match.startsWith('&#x')) return String.fromCodePoint(parseInt(match.slice(3, -1), 16));
        if (match.startsWith('&#')) return String.fromCodePoint(parseInt(match.slice(2, -1), 10));
        return match;
      });
    },
  },

  {
    name: 'rot13',
    displayName: 'ROT13',
    description: 'ROT13 cipher (self-reversing)',
    category: 'encoding',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return input.replace(/[a-zA-Z]/g, c => {
        const base = c <= 'Z' ? 65 : 97;
        return String.fromCharCode(((c.charCodeAt(0) - base + 13) % 26) + base);
      });
    },
  },

  {
    name: 'unicode_escape',
    displayName: 'Unicode Escape',
    description: 'Escape non-ASCII characters to \\uXXXX sequences',
    category: 'encoding',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return Array.from(input).map(ch => {
        const code = ch.codePointAt(0);
        if (code < 128) return ch;
        if (code <= 0xFFFF) return '\\u' + code.toString(16).padStart(4, '0');
        return '\\U' + code.toString(16).padStart(8, '0');
      }).join('');
    },
  },

  {
    name: 'unicode_unescape',
    displayName: 'Unicode Unescape',
    description: 'Convert \\uXXXX sequences to characters',
    category: 'encoding',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return input
        .replace(/\\U([0-9a-fA-F]{8})/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
        .replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16)));
    },
  },
];
