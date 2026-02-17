/**
 * Tukuy.js — Browser & Node transformer engine
 *
 * JS ports of Tukuy's Python transformers for instant,
 * zero-latency transformations without a server.
 *
 * Usage (ESM):
 *   import { tukuy } from 'tukuy';
 *   const result = await tukuy.transform('slugify', 'Hello World');
 *
 * Usage (Browser):
 *   <script src="tukuy.iife.js"></script>
 *   const result = await Tukuy.tukuy.transform('sha256', 'Hello');
 */

import { textTransformers } from './transformers/text.js';
import { encodingTransformers } from './transformers/encoding.js';
import { cryptoTransformers } from './transformers/crypto.js';
import { numericalTransformers } from './transformers/numerical.js';
import { dateTransformers } from './transformers/date.js';
import { validationTransformers } from './transformers/validation.js';
import { jsonTransformers } from './transformers/json-transforms.js';
import { htmlTransformers } from './transformers/html-transforms.js';

class TukuyRegistry {
  constructor() {
    this.transformers = new Map();
    this.categories = new Map();
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
    return t.async
      ? await t.transform(input, options)
      : t.transform(input, options);
  }

  /**
   * Run a transformer synchronously. Throws if transformer is async.
   */
  transformSync(name, input, options = {}) {
    const t = this.get(name);
    if (!t) throw new Error(`Unknown transformer: ${name}`);
    if (t.async) throw new Error(`Transformer '${name}' is async — use transform() instead`);
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
      const name = typeof step === 'string' ? step : step.name;
      const options = typeof step === 'string' ? {} : (step.options || {});
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
    return Array.from(this.transformers.values()).map(t => ({
      name: t.name,
      displayName: t.displayName,
      description: t.description,
      category: t.category,
      params: t.params || [],
      async: t.async || false,
      inputType: t.inputType || 'string',
      outputType: t.outputType || 'string',
    }));
  }

  /**
   * Get metadata grouped by category.
   */
  getMetadataByCategory() {
    const result = {};
    for (const [category, names] of this.categories) {
      result[category] = names.map(name => {
        const t = this.transformers.get(name);
        return {
          name: t.name,
          displayName: t.displayName,
          description: t.description,
          params: t.params || [],
          async: t.async || false,
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
}

// Singleton registry with all built-in transformers
const tukuy = new TukuyRegistry();

const allTransformers = [
  ...textTransformers,
  ...encodingTransformers,
  ...cryptoTransformers,
  ...numericalTransformers,
  ...dateTransformers,
  ...validationTransformers,
  ...jsonTransformers,
  ...htmlTransformers,
];

for (const t of allTransformers) {
  tukuy.register(t);
}

export { tukuy, TukuyRegistry };
