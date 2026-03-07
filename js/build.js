const esbuild = require('esbuild');
const { execSync } = require('child_process');
const path = require('path');

const watch = process.argv.includes('--watch');

// Shared config
const shared = {
  entryPoints: ['src/index.js'],
  bundle: true,
  minify: false,
  sourcemap: true,
};

async function build() {
  // ESM (for import)
  await esbuild.build({
    ...shared,
    outfile: 'dist/tukuy.mjs',
    format: 'esm',
  });

  // CJS (for require)
  await esbuild.build({
    ...shared,
    outfile: 'dist/tukuy.js',
    format: 'cjs',
  });

  // IIFE (for <script> tag — exposes window.Tukuy)
  await esbuild.build({
    ...shared,
    outfile: 'dist/tukuy.iife.js',
    format: 'iife',
    globalName: 'Tukuy',
  });

  // Generate JS registry manifest — consumed by Python for platform matrix
  const { tukuy } = require('./dist/tukuy.js');
  const manifest = {
    version: require('./package.json').version,
    transformers: tukuy.getMetadata(),
    categories: Object.fromEntries(
      tukuy.getCategories().map(cat => [cat, tukuy.list(cat)])
    ),
  };
  const fs = require('fs');
  fs.writeFileSync(
    path.join(__dirname, 'dist', 'js-registry.json'),
    JSON.stringify(manifest, null, 2) + '\n'
  );
  // Also write to Python package so it's accessible at runtime
  const pyTarget = path.join(__dirname, '..', 'tukuy', 'js-registry.json');
  fs.writeFileSync(pyTarget, JSON.stringify(manifest, null, 2) + '\n');

  console.log('[tukuy.js] Build complete:');
  console.log('  dist/tukuy.mjs          (ESM)');
  console.log('  dist/tukuy.js           (CJS)');
  console.log('  dist/tukuy.iife.js      (Browser)');
  console.log(`  dist/js-registry.json   (${tukuy.size} transformers)`);
  console.log(`  tukuy/js-registry.json  (Python copy)`);
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
