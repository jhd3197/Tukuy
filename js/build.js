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

  console.log('[tukuy.js] Build complete:');
  console.log('  dist/tukuy.mjs      (ESM)');
  console.log('  dist/tukuy.js       (CJS)');
  console.log('  dist/tukuy.iife.js  (Browser)');
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
