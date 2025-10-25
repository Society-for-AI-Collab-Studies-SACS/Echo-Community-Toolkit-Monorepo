#!/usr/bin/env node
const { promisify } = require('util');
const exec = promisify(require('child_process').exec);
const URL = 'https://distrokid.com/hyperfollow/echosquirrel/crystaline-echo';

async function count(globs, needle) {
  const { stdout } = await exec(`grep -r ${q(needle)} . ${globs} 2>/dev/null | wc -l`);
  return parseInt((stdout||'0').trim(),10)||0;
}
async function has(globs, needle) {
  const { stdout } = await exec(`grep -r ${q(needle)} . ${globs} 2>/dev/null || true`);
  return stdout.trim().length>0;
}
function q(s){return `'${String(s).replace(/'/g,"\\'")}'`}

(async () => {
  const globs = '--include="*.html" --include="*.htm" --include="*.md"';
  const n = await count(globs, URL);
  console.log(`Canonical URL occurrences: ${n}`);
  const badge = await has(globs, 'id="music-link"');
  console.log(`Summon UI badge: ${badge ? 'present' : 'missing'}`);
  process.exit(n>0 && badge ? 0 : 1);
})().catch(e=>{console.error(e.message);process.exit(1)});

