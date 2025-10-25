#!/usr/bin/env node
/** Generate TypeScript types from the emitted JSON Schemas. */
const { compile } = require('json-schema-to-typescript');
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const SCHEMA_DIR = path.join(ROOT, 'integration', 'schemas');
const TYPES_DIR = path.join(ROOT, 'types');

async function main() {
  const soulcodeSchema = path.join(SCHEMA_DIR, 'echo-soulcode.schema.json');
  const bundleSchema = path.join(SCHEMA_DIR, 'echo-soulcode.bundle.schema.json');
  if (!fs.existsSync(soulcodeSchema) || !fs.existsSync(bundleSchema)) {
    console.error('Schemas not found. Run: npm run soulcode:emit-schema');
    process.exit(1);
  }
  fs.mkdirSync(TYPES_DIR, { recursive: true });
  const singleSchema = JSON.parse(fs.readFileSync(soulcodeSchema, 'utf8'));
  const bundleSchemaObj = JSON.parse(fs.readFileSync(bundleSchema, 'utf8'));
  // Compatibility: some tooling expects 'definitions' instead of '$defs'
  if (!singleSchema.definitions && singleSchema.$defs) singleSchema.definitions = singleSchema.$defs;
  if (!bundleSchemaObj.definitions && bundleSchemaObj.$defs) bundleSchemaObj.definitions = bundleSchemaObj.$defs;
  const rewriteRefs = (node) => {
    if (node && typeof node === 'object') {
      for (const k of Object.keys(node)) {
        if (k === '$ref' && typeof node[k] === 'string' && node[k].startsWith('#/$defs/')) {
          node[k] = node[k].replace('#/$defs/', '#/definitions/');
        } else {
          rewriteRefs(node[k]);
        }
      }
    }
  };
  rewriteRefs(singleSchema);
  rewriteRefs(bundleSchemaObj);
  const single = await compile(singleSchema, 'EchoSoulcode', { bannerComment: '' });
  const bundle = await compile(bundleSchemaObj, 'EchoSoulcodeBundle', { bannerComment: '' });
  const out = `// Auto-generated from JSON Schemas. Do not edit by hand.\n\n${single}\n\n${bundle}\n`;
  const outPath = path.join(TYPES_DIR, 'echo-soulcode.d.ts');
  fs.writeFileSync(outPath, out, 'utf8');
  console.log('Wrote types:', path.relative(ROOT, outPath));
}

main().catch(e => { console.error(e); process.exit(1); });
