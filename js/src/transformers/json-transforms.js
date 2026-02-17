/**
 * Tukuy JSON Transformers — JS port
 *
 * Ports of tukuy/plugins/json Python transformers.
 * Pure JS — no dependencies.
 */

/**
 * Navigate a JSON object using dot-notation path with array index/wildcard support.
 *
 *   "user.name"        => obj.user.name
 *   "users[0].name"    => obj.users[0].name
 *   "users[*].name"    => obj.users.map(u => u.name)
 */
function getValueByPath(data, path) {
  if (!path || data == null) return undefined;

  // Handle array wildcard
  if (path.includes('[*]')) {
    const [before, after] = path.split('[*]', 2);
    let current = before ? getValueByPath(data, before) : data;
    if (!Array.isArray(current)) return undefined;
    if (!after || after === '') return current;
    const rest = after.startsWith('.') ? after.slice(1) : after;
    return current.map(item => getValueByPath(item, rest));
  }

  // Split on dots that are not inside brackets
  const parts = path.split(/\.(?![^\[]*\])/);
  let current = data;

  for (const part of parts) {
    if (!part) continue;
    if (current == null) return undefined;

    // Check for array index: "key[0]"
    const match = /^(.+?)\[(\d+)\]$/.exec(part);
    if (match) {
      const [, key, index] = match;
      current = current[key];
      if (!Array.isArray(current)) return undefined;
      const idx = parseInt(index, 10);
      current = idx >= 0 && idx < current.length ? current[idx] : undefined;
    } else {
      current = typeof current === 'object' ? current[part] : undefined;
    }
  }

  return current;
}

/**
 * Simple JSON schema validation (mirrors Python JsonParser._validate_schema).
 */
function validateSchema(data, schema) {
  if (!schema || typeof schema !== 'object') return true;

  if ('type' in schema) {
    const t = schema.type;
    if (t === 'object' && (typeof data !== 'object' || data === null || Array.isArray(data))) return false;
    if (t === 'array' && !Array.isArray(data)) return false;
    if (t === 'string' && typeof data !== 'string') return false;
    if (t === 'number' && typeof data !== 'number') return false;
    if (t === 'boolean' && typeof data !== 'boolean') return false;
    if (t === 'null' && data !== null) return false;
  }

  if (schema.properties && typeof data === 'object' && data !== null) {
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
    return data.every(item => validateSchema(item, schema.items));
  }

  return true;
}

export const jsonTransformers = [
  {
    name: 'json_parse',
    displayName: 'JSON Parse',
    description: 'Parse JSON string with optional schema validation',
    category: 'json',
    inputType: 'string',
    outputType: 'any',
    params: [
      { name: 'strict', type: 'boolean', default: true, description: 'Throw on invalid JSON' },
      { name: 'schema', type: 'object', default: null, description: 'JSON schema for validation' },
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
        throw new Error('JSON data does not match schema');
      }
      return data;
    },
  },

  {
    name: 'json_extract',
    displayName: 'JSON Extract',
    description: 'Extract values using dot-notation paths',
    category: 'json',
    inputType: 'any',
    outputType: 'any',
    params: [
      { name: 'path', type: 'string', default: '', description: 'Dot-notation path (e.g. user.name, items[0], items[*].id)' },
      { name: 'default_value', type: 'any', default: null, description: 'Default if path not found' },
    ],
    transform(input, { path = '', default_value = null } = {}) {
      if (!path) return input;
      const data = typeof input === 'string' ? JSON.parse(input) : input;
      const result = getValueByPath(data, path);
      return result !== undefined ? result : default_value;
    },
  },
];
