#!/usr/bin/env node
const fs = require('fs').promises;
const path = require('path');
const { promisify } = require('util');
const exec = promisify(require('child_process').exec);
const URL = 'https://distrokid.com/hyperfollow/echosquirrel/crystaline-echo';

async function listFiles() {
  const { stdout } = await exec(`grep -rl ${q(URL)} . --include="*.html" --include="*.htm" --include="*.md" 2>/dev/null || true`);
  return stdout.split('\n').filter(Boolean);
}
function q(s){return `'${String(s).replace(/'/g,"\\'")}'`}

async function clean(file){
  let txt = await fs.readFile(file,'utf-8');
  const orig = txt;
  txt = txt.replace(/\n?\s*<[^>]*data-echo=\"hyperfollow-ce:v1\"[\s\S]*?>[\s\S]*?<\/[^>]+>\s*/g,'\n');
  txt = txt.replace(/\n## 🎶 Project Soundtrack[\s\S]*?\n\n/g,'\n');
  if (txt.includes(URL)) txt = txt.split('\n').filter(l=>!l.includes(URL)).join('\n');
  if (txt !== orig) await fs.writeFile(file,txt,'utf-8');
}

(async()=>{
  const files = await listFiles();
  for (const f of files) { await clean(f).catch(()=>{}); }
  console.log(`Cleaned ${files.length} file(s)`);
})().catch(e=>{console.error(e.message);process.exit(1)});

