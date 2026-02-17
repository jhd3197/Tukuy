/**
 * Tukuy Crypto Transformers — JS port
 *
 * Ports of tukuy/plugins/crypto Python transformers.
 * Uses Web Crypto API (crypto.subtle) for hashing/HMAC — async.
 * Uses browser-native btoa/atob for base64 with UTF-8 wrappers.
 * Uses crypto.randomUUID() for UUID generation.
 *
 * Node.js >=18 supports all of these via globalThis.crypto.
 */

function bufferToHex(buffer) {
  return Array.from(new Uint8Array(buffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * UTF-8 safe base64 encode (works in both browser and Node).
 */
function utf8ToBase64(str) {
  const bytes = new TextEncoder().encode(str);
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}

/**
 * UTF-8 safe base64 decode (works in both browser and Node).
 */
function base64ToUtf8(b64) {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}

export const cryptoTransformers = [
  {
    name: 'hash_text',
    displayName: 'Hash Text',
    description: 'Hash string (SHA-1, SHA-256, SHA-512)',
    category: 'crypto',
    inputType: 'string',
    outputType: 'string',
    async: true,
    params: [
      {
        name: 'algorithm',
        type: 'string',
        default: 'sha256',
        description: 'Hash algorithm',
        options: ['sha1', 'sha256', 'sha512'],
      },
    ],
    async transform(input, { algorithm = 'sha256' } = {}) {
      const algoMap = {
        sha1: 'SHA-1', sha256: 'SHA-256', sha512: 'SHA-512',
        'SHA-1': 'SHA-1', 'SHA-256': 'SHA-256', 'SHA-512': 'SHA-512',
      };
      const algo = algoMap[algorithm];
      if (!algo) return `Unsupported: ${algorithm} (use sha1, sha256, sha512)`;
      const data = new TextEncoder().encode(input);
      const hash = await crypto.subtle.digest(algo, data);
      return bufferToHex(hash);
    },
  },

  {
    name: 'base64_encode',
    displayName: 'Base64 Encode',
    description: 'Encode text to Base64',
    category: 'crypto',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return utf8ToBase64(input);
    },
  },

  {
    name: 'base64_decode',
    displayName: 'Base64 Decode',
    description: 'Decode Base64 to text',
    category: 'crypto',
    inputType: 'string',
    outputType: 'string',
    params: [],
    transform(input) {
      return base64ToUtf8(input);
    },
  },

  {
    name: 'uuid_generate',
    displayName: 'Generate UUID',
    description: 'Generate a UUID v4',
    category: 'crypto',
    inputType: 'any',
    outputType: 'string',
    params: [
      { name: 'version', type: 'number', default: 4, description: 'UUID version (v4 in browser)' },
    ],
    transform(_input, _options) {
      return crypto.randomUUID();
    },
  },

  {
    name: 'hmac_sign',
    displayName: 'HMAC Sign',
    description: 'Generate HMAC signature',
    category: 'crypto',
    inputType: 'string',
    outputType: 'string',
    async: true,
    params: [
      { name: 'key', type: 'string', default: '', description: 'Secret key' },
      {
        name: 'algorithm',
        type: 'string',
        default: 'sha256',
        description: 'Hash algorithm',
        options: ['sha1', 'sha256', 'sha512'],
      },
    ],
    async transform(input, { key = '', algorithm = 'sha256' } = {}) {
      const algoMap = { sha1: 'SHA-1', sha256: 'SHA-256', sha512: 'SHA-512' };
      const algo = algoMap[algorithm] || 'SHA-256';
      const enc = new TextEncoder();
      const cryptoKey = await crypto.subtle.importKey(
        'raw', enc.encode(key),
        { name: 'HMAC', hash: algo },
        false, ['sign']
      );
      const sig = await crypto.subtle.sign('HMAC', cryptoKey, enc.encode(input));
      return bufferToHex(sig);
    },
  },
];
