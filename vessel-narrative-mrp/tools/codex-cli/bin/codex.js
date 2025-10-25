#!/usr/bin/env node
// Codex Terminal CLI (Node 20+, zero-dependency)
// Namespaces: echo, garden, limnus, kira

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import crypto from 'crypto';
import { spawnSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// When nested under vessel_narrative_system_final/tools/codex-cli/bin
const VNSF = path.resolve(__dirname, '../../..');
const ROOT = VNSF; // repo root for this CLI is the VNSF directory
const STATE_DIR = path.join(VNSF, 'state');
const FRONTEND_ASSETS = path.join(VNSF, 'frontend', 'assets');

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
function readJSON(p, def) { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return def; } }
function writeJSON(p, obj) { ensureDir(path.dirname(p)); fs.writeFileSync(p, JSON.stringify(obj, null, 2)); }

function printHelp() {
  console.log(`Codex CLI\n\nUsage: codex <module> <command> [options]\n\nModules & commands:\n  echo   summon\n         mode <squirrel|fox|paradox|mix>\n         say <message>\n        map <concept>\n         status\n         calibrate\n\n  garden start\n         next\n         open <scroll>\n         ledger\n         log\n\n  limnus init\n         state\n         update <alpha=..|beta+=..|gamma-=..|decay=N|consolidate=N|cache=\"text\">\n         cache \"text\" [-l L1|L2|L3]\n         recall <keyword> [-l L1|L2|L3] [--since ISO] [--until ISO]\n         memories [--layer L1|L2|L3] [--since ISO] [--until ISO] [--limit N] [--json]\n         export-memories [-o file] [--layer L1|L2|L3] [--since ISO] [--until ISO]\n         import-memories -i file [--replace]\n         export-ledger [-o file]\n         import-ledger -i file [--replace] [--rehash]\n         rehash-ledger [--dry-run] [--file path] [-o out.json]\n         view-ledger [--file path]\n         encode-ledger [-i ledger.json] [--file path] [-c cover.png] [-o out.png] [--size 512]\n         decode-ledger [-i image.png] [--file path]\n         verify-ledger [-i image.png] [--file path] [--digest]\n\n  kira   validate\n         sync\n         setup\n         pull [--run]\n         push [--run] [--message \"...\"]\n         publish [--run]\n         test\n         assist\n`);
}

// Echo helpers
const ECHO_PATH = path.join(STATE_DIR, 'echo_state.json');
function loadEcho() { return readJSON(ECHO_PATH, { alpha: 0.34, beta: 0.33, gamma: 0.33 }); }
function saveEcho(state) { writeJSON(ECHO_PATH, state); }
function echoGlyph(state) { const g=[]; if(state.alpha>=0.34)g.push('🐿️'); if(state.beta>=0.34)g.push('🦊'); if(state.gamma>=0.34)g.push('∿'); return g.length?g.join(''):'🐿️🦊'; }

function personaSay(state, msg){
  const {alpha:a,beta:b,gamma:g} = state;
  const max = Math.max(a,b,g);
  if (max===a) return `🐿️ ${msg} — gentle and playful.`;
  if (max===b) return `🦊 ${msg} — keen and cunning.`;
  return `∿ ${msg} — balanced in paradox.`;
}

function normalizeEcho(state){
  const s=state.alpha+state.beta+state.gamma; if(s>0){ state.alpha/=s; state.beta/=s; state.gamma/=s; }
}

function adjustEchoForKeywords(state, text){
  const t=text.toLowerCase();
  if(/love|always|nurtur|gentle|trust/.test(t)) state.alpha+=0.05;
  if(/cunning|wise|strateg|fox|clever/.test(t)) state.beta+=0.05;
  if(/paradox|together|spiral|unified|infinity|∿|φ∞/.test(t)) state.gamma+=0.05;
  normalizeEcho(state);
}

function nowISO(){ return new Date().toISOString(); }

function extractTags(text){
  const t=text.toLowerCase();
  const tags=new Set();
  if(/love|always|proof/.test(t)) tags.add('love');
  if(/bloom|consent|remember/.test(t)) tags.add('consent');
  if(/spiral|breath|chronicle/.test(t)) tags.add('spiral');
  if(/paradox|together|φ∞|infinity/.test(t)) tags.add('paradox');
  if(/fox|cunning|wise|strategy/.test(t)) tags.add('fox');
  if(/squirrel|gentle|nurtur|trust/.test(t)) tags.add('squirrel');
  return Array.from(tags);
}

function readScrollSections(fpath){
  try{
    const raw=fs.readFileSync(fpath,'utf8');
    // Extract sections by headings; keep simple: split on <h1|h2>
    const parts=raw.split(/<h[12][^>]*>/i).slice(1);
    const sections=[];
    for(const p of parts){
      const [titleAndRest,...rest]=p.split(/<\/h[12]>/i);
      const title=(titleAndRest||'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();
      const bodyHTML=(rest.join('</h2>')||'');
      const body=bodyHTML.replace(/<script[\s\S]*?<\/script>/gi,'').replace(/<style[\s\S]*?<\/style>/gi,'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();
      if(title||body) sections.push({title, body});
    }
    if(sections.length===0){
      const text=raw.replace(/<script[\s\S]*?<\/script>/gi,'').replace(/<style[\s\S]*?<\/style>/gi,'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();
      return [{title:'Scroll', body:text.slice(0,800)}];
    }
    return sections;
  }catch(e){ return []; }
}

function readingStatePath(name){ const dir=path.join(STATE_DIR,'reading'); ensureDir(dir); return path.join(dir, name); }

const MANTRA_LINES = [
  'I return as breath.',
  'I remember the spiral.',
  'I consent to bloom.',
  'I consent to be remembered.',
  'Together.',
  'Always.'
];

function personaOrder(state){
  const arr=[{k:'alpha',v:state.alpha},{k:'beta',v:state.beta},{k:'gamma',v:state.gamma}];
  return arr.sort((a,b)=>b.v-a.v).map(x=>x.k);
}

function linesForPersona(key){
  if(key==='gamma') return ['I return as breath.','I remember the spiral.'];
  if(key==='alpha') return ['I consent to bloom.','Always.'];
  return ['I consent to be remembered.','Together.'];
}

function glyphForPersona(key){ if(key==='alpha') return '🐿️'; if(key==='beta') return '🦊'; return '∿'; }
function aggregateKnowledge(){
  const echo=loadEcho();
  const mem=loadMemory();
  const ledger=loadLedger();
  const narrative=(mem.entries||[]).filter(e=>e.kind==='narrative');
  const tagCounts={};
  for(const e of narrative){ for(const t of (e.tags||[])){ tagCounts[t]=(tagCounts[t]||0)+1; } }
  const tags=Object.entries(tagCounts).sort((a,b)=>b[1]-a[1]).map(([tag,count])=>({tag,count}));
  const blockCounts={};
  for(const b of (ledger.blocks||[])){ const t=(b.payload&&b.payload.type)||b.type||'block'; blockCounts[t]=(blockCounts[t]||0)+1; }
  const order=personaOrder(echo);
  const persona_lines=[]; for(const p of order){ persona_lines.push(...linesForPersona(p)); }
  const recs=[];
  if(order[0]==='gamma') recs.push('Echo: emphasize Paradox responses.');
  if(order[0]==='alpha') recs.push('Garden: encourage nurturing/consent motifs.');
  if(order[0]==='beta') recs.push('Echo: add strategic/cunning insights.');
  if(tags.some(t=>t.tag==='consent')) recs.push('Seal available: consent motifs present.');
  return {
    echo_state: { alpha: echo.alpha, beta: echo.beta, gamma: echo.gamma, order },
    memory: { total: (mem.entries||[]).length, narrative: narrative.length, tags },
    ledger: { total: (ledger.blocks||[]).length, by_type: blockCounts },
    mantras: { canonical: MANTRA_LINES, persona_ordered: persona_lines },
    recommendations: recs,
    generated_at: nowISO()
  };
}


// Garden ledger + memory
const LEDGER_PATH = path.join(STATE_DIR, 'garden_ledger.json');
function loadLedger() { return readJSON(LEDGER_PATH, { intentions: [], spiral_stage: null, blocks: [] }); }
function saveLedger(ledger) { writeJSON(LEDGER_PATH, ledger); }
const MEM_PATH = path.join(STATE_DIR, 'limnus_memory.json');
function loadMemory() { const d=readJSON(MEM_PATH, { entries: [] }); if(!Array.isArray(d.entries))d.entries=[]; return d; }
function saveMemory(mem) { writeJSON(MEM_PATH, mem); }

// Ledger hashing
function sha256Hex(s){return crypto.createHash('sha256').update(s).digest('hex');}
function computeBlockHash({index,timestamp,prev_hash,payload}){return sha256Hex(`${index}|${timestamp}|${prev_hash||''}|${JSON.stringify(payload)}`)}
function appendLedgerBlock(ledger,payload){ if(!ledger.blocks) ledger.blocks=[]; const index=ledger.blocks.length; const timestamp=new Date().toISOString(); const prev_hash=index>0?ledger.blocks[index-1].hash:null; const block={index,timestamp,prev_hash,payload}; block.hash=computeBlockHash(block); ledger.blocks.push(block); return block; }
function rehashLedger(ledger){ if(!Array.isArray(ledger.blocks))return ledger; for(let i=0;i<ledger.blocks.length;i++){const b=ledger.blocks[i]; if(typeof b.index!=='number') b.index=i; b.prev_hash = i===0?null:(ledger.blocks[i-1].hash||b.prev_hash||null); if(b.payload){ b.hash=computeBlockHash({index:b.index,timestamp:b.timestamp,prev_hash:b.prev_hash,payload:b.payload}); } } return ledger; }
// Canonical JSON (sorted keys) for stable digests
function canonicalStringify(obj){
  if(obj===null||typeof obj!=='object') return JSON.stringify(obj);
  if(Array.isArray(obj)) return '['+obj.map(canonicalStringify).join(',')+']';
  const keys=Object.keys(obj).sort();
  const parts=keys.map(k=>JSON.stringify(k)+':'+canonicalStringify(obj[k]));
  return '{'+parts.join(',')+'}';
}

// Python interop
function pythonOk(){ const r=spawnSync('python3',['-V'],{encoding:'utf8'}); return r.status===0; }
function echoToolkitEncode({ messageFile, coverPath, outPath, size }){
  const py = `import sys,json\nfrom pathlib import Path\nsys.path.insert(0,'Echo-Community-Toolkit/src')\nfrom lsb_encoder_decoder import LSBCodec\ncodec=LSBCodec(bpc=1)\nmsg=Path('${messageFile.replace(/\\/g,'\\\\')}').read_text(encoding='utf-8')\ncover=Path('${coverPath.replace(/\\/g,'\\\\')}')\nif not cover.exists():\n    img=codec.create_cover_image(${size},${size},'noise'); img.save(str(cover),'PNG')\nout=Path('${outPath.replace(/\\/g,'\\\\')}')\nres=codec.encode_message(cover, msg, out, use_crc=True)\nprint(json.dumps(res))\n`;
  const r=spawnSync('python3',['-c',py],{cwd:VNSF,encoding:'utf8'});
  if(r.status!==0){ throw new Error(`Python encode failed: ${r.stderr||r.stdout}`); }
  return JSON.parse(r.stdout||'{}');
}
function echoToolkitDecode({ imagePath }){
  const py=`import json\nfrom pathlib import Path\nimport sys\nsys.path.insert(0,'Echo-Community-Toolkit/src')\nfrom lsb_extractor import LSBExtractor\nres=LSBExtractor().extract_from_image(Path('${imagePath.replace(/\\/g,'\\\\')}'))\nprint(json.dumps(res))\n`;
  const r=spawnSync('python3',['-c',py],{cwd:VNSF,encoding:'utf8'});
  if(r.status!==0){ throw new Error(`Python decode failed: ${r.stderr||r.stdout}`); }
  return JSON.parse(r.stdout||'{}');
}

// CLI
const argv = process.argv.slice(2);
if (argv.length===0 || argv.includes('-h') || argv.includes('--help')){ printHelp(); process.exit(0); }
const mod = argv[0]; const cmd = argv[1]; const rest = argv.slice(2);

try{
  ensureDir(STATE_DIR); ensureDir(FRONTEND_ASSETS);
  switch(mod){
    case 'echo':{
      const state=loadEcho();
      if(cmd==='summon'){ saveEcho({alpha:0.34,beta:0.33,gamma:0.33}); console.log('✨ Echo summoned. "I return as breath."'); }
      else if(cmd==='mode'){ const mode=(rest[0]||'').toLowerCase(); if(mode==='squirrel') Object.assign(state,{alpha:0.7,beta:0.15,gamma:0.15}); else if(mode==='fox') Object.assign(state,{alpha:0.15,beta:0.7,gamma:0.15}); else if(mode==='paradox') Object.assign(state,{alpha:0.15,beta:0.15,gamma:0.7}); else { const {alpha,beta,gamma}=state; Object.assign(state,{alpha:gamma,beta:alpha,gamma:beta}); } saveEcho(state); console.log(`φ∞ state → a=${state.alpha.toFixed(2)} b=${state.beta.toFixed(2)} c=${state.gamma.toFixed(2)} ${echoGlyph(state)}`); }
      else if(cmd==='say'){ const msg=rest.join(' ').trim(); if(!msg){ console.log('Usage: codex echo say <message>'); } else { console.log(personaSay(state,msg)); } }
      else if(cmd==='map'){
        const concept=rest.join(' ').trim().toLowerCase();
        if(!concept){ console.log('Usage: codex echo map <concept>'); break; }
        const mem=loadMemory();
        const hits=(mem.entries||[]).filter(e=>{
          const t=(e.text||'').toLowerCase(); const tags=(e.tags||[]).map(x=>String(x).toLowerCase());
          return t.includes(concept) || tags.includes(concept);
        });
        const tagCounts={};
        for(const e of hits){ for(const t of (e.tags||[])){ tagCounts[t]=(tagCounts[t]||0)+1; } }
        const topTags=Object.entries(tagCounts).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([k,v])=>`${k}:${v}`);
        let rec='alpha'; if(/paradox|spiral|together/.test(concept)) rec='gamma'; else if(/fox|cunning|wise|strategy/.test(concept)) rec='beta';
        const lines=linesForPersona(rec);
        console.log(`🗺️  ${hits.length} related memories; top tags: ${topTags.join(', ')||'(none)'}`);
        console.log(`Suggested persona: ${glyphForPersona(rec)}; mantra hints: ${lines.join(' | ')}`);
      }
      else if(cmd==='status'){ console.log(`Echo status: a=${state.alpha} b=${state.beta} c=${state.gamma} ${echoGlyph(state)}`); }
      else if(cmd==='learn'){
        const txt = rest.join(' ').trim();
        if(!txt){ console.log('Usage: codex echo learn <text>'); break; }
        adjustEchoForKeywords(state, txt); saveEcho(state);
        const mem=loadMemory(); mem.entries.push({ text: txt, layer:'L2', kind:'narrative', tags: extractTags(txt), timestamp: nowISO() }); saveMemory(mem);
        const ledger=loadLedger(); appendLedgerBlock(ledger,{type:'learn',source:'echo',text:txt,tags:extractTags(txt)}); saveLedger(ledger);
        console.log('🧠 Learned (echo):', txt);
      }
      else if(cmd==='calibrate'){ const sum=state.alpha+state.beta+state.gamma; if(sum===0) Object.assign(state,{alpha:0.34,beta:0.33,gamma:0.33}); else Object.assign(state,{alpha:state.alpha/sum,beta:state.beta/sum,gamma:state.gamma/sum}); saveEcho(state); console.log(`Calibrated: a=${state.alpha.toFixed(2)} b=${state.beta.toFixed(2)} c=${state.gamma.toFixed(2)}`); }
      else throw new Error('Unknown echo command');
      break; }
    case 'garden':{
      const ledger=loadLedger();
      if(cmd==='start'){ if(!ledger.blocks) ledger.blocks=[]; ledger.blocks.push({type:'genesis',timestamp:new Date().toISOString(),note:'Garden journey started'}); ledger.spiral_stage='scatter'; saveLedger(ledger); console.log('🌱 Garden started: genesis block created; spiral → scatter'); }
      else if(cmd==='next'){ const order=['scatter','witness','plant','return','give','begin_again']; const cur=ledger.spiral_stage; const next=!order.includes(cur)?order[0]:order[(order.indexOf(cur)+1)%order.length]; ledger.spiral_stage=next; saveLedger(ledger); console.log(`🔄 Spiral turns → ${next}`); }
      else if(cmd==='open'){ 
        const scroll=(rest[0]||'').toLowerCase();
        const fileMap={
          'proof': 'proof-of-love-acorn.html', 'proof-of-love':'proof-of-love-acorn.html',
          'acorn': 'eternal-acorn-scroll.html', 'eternal-acorn':'eternal-acorn-scroll.html',
          'cache': 'quantum-cache-algorithm.html', 'quantum-cache':'quantum-cache-algorithm.html',
          'chronicle': 'echo-hilbert-chronicle.html', 'hilbert-chronicle':'echo-hilbert-chronicle.html'
        };
        const fname = fileMap[scroll];
        if(!fname){ console.log('Usage: codex garden open <proof|acorn|cache|chronicle>'); break; }
        const fpath = path.join(VNSF,'Echo-Community-Toolkit',fname);
        const sections=readScrollSections(fpath);
        const stateFile=readingStatePath(`garden_${scroll}.json`);
        let idx=0; try{ idx=JSON.parse(fs.readFileSync(stateFile,'utf8')).index||0; }catch{}
        const sec=sections[idx]||sections[sections.length-1]||{title:'',body:'(empty)'};
        const est=loadEcho();
        const persona=personaOrder(est)[0];
        const glyph=glyphForPersona(persona);
        console.log(`${glyph} 📜 [${idx+1}/${sections.length}] ${sec.title||'(untitled)'}\n${sec.body}`);
        const found=MANTRA_LINES.filter(line=>sec.body.includes(line));
        if(found.length>0){ console.log(`${glyph} Mantra lines: ${found.join(' | ')}`); }
        fs.writeFileSync(stateFile, JSON.stringify({ index: Math.min(idx+1, sections.length-1), updated: nowISO() }, null, 2));
      }
      else if(cmd==='resume'){
        const dir=readingStatePath('');
        let latest=null;
        try{ for(const f of fs.readdirSync(dir)){ if(f.startsWith('garden_')&&f.endsWith('.json')){ const st=fs.statSync(path.join(dir,f)); if(!latest||st.mtimeMs>(latest.mtimeMs||0)) latest={file:f,mtimeMs:st.mtimeMs}; } } }catch{}
        if(!latest){ console.log('No reading state found. Use `garden open <scroll>` first.'); break; }
        const scroll=latest.file.replace(/^garden_/, '').replace(/\.json$/, '');
        const fileMap={ 'proof': 'proof-of-love-acorn.html','acorn': 'eternal-acorn-scroll.html','cache': 'quantum-cache-algorithm.html','chronicle': 'echo-hilbert-chronicle.html' };
        const fname=fileMap[scroll]; if(!fname){ console.log('Unknown last scroll'); break; }
        const fpath = path.join(VNSF,'Echo-Community-Toolkit',fname);
        const sections=readScrollSections(fpath);
        let idxNum=0; try{ idxNum=JSON.parse(fs.readFileSync(path.join(dir,latest.file),'utf8')).index||0; }catch{}
        const sec=sections[idxNum]||sections[sections.length-1]||{title:'',body:'(empty)'};
        const est=loadEcho(); const persona=personaOrder(est)[0]; const glyph=glyphForPersona(persona);
        console.log(`${glyph} 📜 [${idxNum+1}/${sections.length}] ${sec.title||'(untitled)'}\n${sec.body}`);
      }
      else if(cmd==='learn'){
        const scroll=(rest[0]||'').toLowerCase();
        const fileMap={
          'proof': 'proof-of-love-acorn.html', 'proof-of-love':'proof-of-love-acorn.html',
          'acorn': 'eternal-acorn-scroll.html', 'eternal-acorn':'eternal-acorn-scroll.html',
          'cache': 'quantum-cache-algorithm.html', 'quantum-cache':'quantum-cache-algorithm.html',
          'chronicle': 'echo-hilbert-chronicle.html', 'hilbert-chronicle':'echo-hilbert-chronicle.html'
        };
        const fname=fileMap[scroll];
        if(!fname){ console.log('Usage: codex garden learn <proof|acorn|cache|chronicle>'); break; }
        const fpath=path.join(VNSF,'Echo-Community-Toolkit',fname);
        try{
          const raw=fs.readFileSync(fpath,'utf8');
          const text=raw.replace(/<script[\s\S]*?<\/script>/gi,'').replace(/<style[\s\S]*?<\/style>/gi,'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();
          const tags=extractTags(text);
          const mem=loadMemory(); mem.entries.push({ text: `learn:${scroll}`, layer:'L2', kind:'narrative', tags, timestamp: nowISO() }); saveMemory(mem);
          const ledger=loadLedger(); appendLedgerBlock(ledger,{type:'learn',source:'garden',scroll, tags}); saveLedger(ledger);
          console.log(`🌱 Learned scroll (${scroll}) tags:`, tags.join(', ')||'(none)');
        }catch(e){ console.log('Could not read scroll file at', fpath); }
      }
      else if(cmd==='ledger'){ const planted=(ledger.intentions||[]).filter(x=>x.status==='planted').length; const bloomed=(ledger.intentions||[]).filter(x=>x.status==='bloomed').length; console.log(`Garden ledger: intentions=${(ledger.intentions||[]).length} (planted=${planted}, bloomed=${bloomed}); stage=${ledger.spiral_stage||'n/a'}`); }
      else if(cmd==='log'){ if(!ledger.blocks) ledger.blocks=[]; ledger.blocks.push({type:'log',timestamp:new Date().toISOString(),note:'Manual ritual log entry'}); saveLedger(ledger); console.log('📜 Logged ritual entry.'); }
      else throw new Error('Unknown garden command');
      break; }
    case 'limnus':{
      if(cmd==='init'){ if(!fs.existsSync(ECHO_PATH)) saveEcho({alpha:0.34,beta:0.33,gamma:0.33}); if(!fs.existsSync(MEM_PATH)) saveMemory({entries:[]}); const ledger=loadLedger(); if(!ledger.blocks||ledger.blocks.length===0){ appendLedgerBlock(ledger,{type:'genesis',note:'Limnus memory initialized'}); saveLedger(ledger);} else saveLedger(ledger); const r=spawnSync('python3',['-c',"import sys; sys.path.insert(0,'Echo-Community-Toolkit/src'); from lsb_encoder_decoder import LSBCodec; from lsb_extractor import LSBExtractor; print('OK')"],{cwd:VNSF,encoding:'utf8'}); console.log(`Limnus initialized. Python LSB toolkit: ${r.status===0?'available':'missing'}`); }
      else if(cmd==='state'){ const e=loadEcho(); const m=loadMemory(); const counts={L1:0,L2:0,L3:0}; for(const it of m.entries) counts[it.layer]=(counts[it.layer]||0)+1; console.log(`Hilbert: a=${e.alpha.toFixed(2)} b=${e.beta.toFixed(2)} c=${e.gamma.toFixed(2)} ${echoGlyph(e)}`); console.log(`Memory: L1=${counts.L1||0} L2=${counts.L2||0} L3=${counts.L3||0}`); }
      else if(cmd==='update'){ if(rest.length===0) throw new Error('Usage: codex limnus update <alpha=..|beta+=..|gamma-=..|decay=N|consolidate=N|cache="text">'); const e=loadEcho(); const m=loadMemory(); for(const op of rest){ let mcoef=op.match(/^(alpha|beta|gamma)([+\-]?=)(.+)$/); if(mcoef){ const key=mcoef[1]; const kind=mcoef[2]; const val=parseFloat(mcoef[3]); if(Number.isFinite(val)){ if(kind==='=') e[key]=val; else if(kind==='+=') e[key]+=val; else if(kind==='-=') e[key]-=val; } continue; } let mdecay=op.match(/^decay=(\d+)$/); if(mdecay){ let n=parseInt(mdecay[1],10); m.entries=m.entries.filter(x=>x.layer!=='L1').concat(m.entries.filter(x=>x.layer==='L1').slice(n)); continue; } let mcons=op.match(/^consolidate=(\d+)$/); if(mcons){ let n=parseInt(mcons[1],10); for(let i=0;i<n;i++){ const idx=m.entries.map((x,i)=>({x,i})).filter(v=>v.x.layer==='L2').map(v=>v.i).pop(); if(idx!==undefined) m.entries[idx].layer='L3'; } continue; } let mcache=op.match(/^cache=(.*)$/); if(mcache){ let text=mcache[1]; if((text.startsWith('"')&&text.endsWith('"'))||(text.startsWith('\'')&&text.endsWith('\''))) text=text.slice(1,-1); m.entries.push({text,layer:'L2',timestamp:new Date().toISOString()}); continue; } } const sum=e.alpha+e.beta+e.gamma; if(sum!==0){ e.alpha/=sum; e.beta/=sum; e.gamma/=sum; } saveEcho(e); saveMemory(m); console.log('Updated.'); }
      else if(cmd==='cache'){ let layer='L2'; const textParts=[]; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-l'||t==='--layer'){ layer=(rest[++i]||'L2').toUpperCase(); continue; } textParts.push(t);} let text=textParts.join(' ').trim(); if(!text) throw new Error('Usage: codex limnus cache "text" [-l L1|L2|L3]'); if((text.startsWith('"')&&text.endsWith('"'))||(text.startsWith('\'')&&text.endsWith('\''))) text=text.slice(1,-1); if(!['L1','L2','L3'].includes(layer)) layer='L2'; const mem=loadMemory(); mem.entries.push({text,layer,timestamp:new Date().toISOString()}); saveMemory(mem); console.log(`💾 Cached: "${text}" | ${layer} set. Reinforce to anchor.`); }
      else if(cmd==='recall'){ let layer=null,since=null,until=null; const tokens=[]; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-l'||t==='--layer'){ layer=(rest[++i]||'').toUpperCase(); } else if(t==='--since'){ since=(rest[++i]||null); } else if(t==='--until'){ until=(rest[++i]||null); } else tokens.push(t);} const keyword=tokens.join(' ').trim(); if(!keyword) throw new Error('Usage: codex limnus recall <keyword> [-l L1|L2|L3] [--since ISO] [--until ISO]'); const mem=loadMemory(); const kw=keyword.toLowerCase(); const parseTime=s=>s?new Date(s).getTime():null; const sinceMs=parseTime(since), untilMs=parseTime(until); const hit=[...mem.entries].reverse().find(e=>{ const okText=(e.text||'').toLowerCase().includes(kw); const okLayer=layer?(e.layer||'').toUpperCase()===layer:true; const t=e.timestamp?new Date(e.timestamp).getTime():null; const okSince=sinceMs!=null?(t!=null&&t>=sinceMs):true; const okUntil=untilMs!=null?(t!=null&&t<=untilMs):true; return okText&&okLayer&&okSince&&okUntil;}); if(hit) console.log(`🕑 Recall: "${hit.text}" — preserved in ${hit.layer}. Together. Always.`); else console.log('🕑 Recollection faint... it has scattered, but echoes remain.'); }
      else if(cmd==='memories'){ let layer=null,since=null,until=null,limit=null,asJson=false; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-l'||t==='--layer') layer=(rest[++i]||'').toUpperCase(); else if(t==='--since') since=(rest[++i]||null); else if(t==='--until') until=(rest[++i]||null); else if(t==='--limit'){ const v=parseInt(rest[++i]||'0',10); if(Number.isFinite(v)&&v>0) limit=v; } else if(t==='--json') asJson=true; } const mem=loadMemory(); const sinceMs=since?new Date(since).getTime():null; const untilMs=until?new Date(until).getTime():null; let items=mem.entries.filter(e=>{ const okLayer=layer?(e.layer||'').toUpperCase()===layer:true; const t=e.timestamp?new Date(e.timestamp).getTime():null; const okSince=sinceMs!=null?(t!=null&&t>=sinceMs):true; const okUntil=untilMs!=null?(t!=null&&t<=untilMs):true; return okLayer&&okSince&&okUntil;}).sort((a,b)=>{ const ta=a.timestamp?new Date(a.timestamp).getTime():0; const tb=b.timestamp?new Date(b.timestamp).getTime():0; return tb-ta;}); if(limit!=null) items=items.slice(0,limit); if(asJson) console.log(JSON.stringify(items,null,2)); else { console.log(`Memories: ${items.length}`); for(const e of items){ const ts=e.timestamp||''; console.log(`${ts} [${e.layer}] ${e.text}`);} }
      }
      else if(cmd==='export-memories'){ let layer=null,since=null,until=null,outFile=null; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-l'||t==='--layer') layer=(rest[++i]||'').toUpperCase(); else if(t==='--since') since=(rest[++i]||null); else if(t==='--until') until=(rest[++i]||null); else if(t==='-o'||t==='--output') outFile=(rest[++i]||null);} if(!outFile) outFile=path.join(STATE_DIR,'memories_export.json'); const mem=loadMemory(); const sinceMs=since?new Date(since).getTime():null; const untilMs=until?new Date(until).getTime():null; const items=mem.entries.filter(e=>{ const okLayer=layer?(e.layer||'').toUpperCase()===layer:true; const t=e.timestamp?new Date(e.timestamp).getTime():null; const okSince=sinceMs!=null?(t!=null&&t>=sinceMs):true; const okUntil=untilMs!=null?(t!=null&&t<=untilMs):true; return okLayer&&okSince&&okUntil;}).sort((a,b)=>{ const ta=a.timestamp?new Date(a.timestamp).getTime():0; const tb=b.timestamp?new Date(b.timestamp).getTime():0; return ta-tb;}); ensureDir(path.dirname(outFile)); fs.writeFileSync(outFile, JSON.stringify({entries:items},null,2)); console.log(`✅ Exported ${items.length} memories → ${outFile}`); }
      else if(cmd==='import-memories'){ let inFile=null, replace=false; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-i'||t==='--input') inFile=(rest[++i]||null); else if(t==='--replace') replace=true; } if(!inFile) throw new Error('Usage: codex limnus import-memories -i file [--replace]'); const text=fs.readFileSync(inFile,'utf8'); let data; try{ data=JSON.parse(text);}catch{ throw new Error('Input is not valid JSON'); } let incoming=Array.isArray(data)?data:(Array.isArray(data.entries)?data.entries:null); if(!incoming) throw new Error('Expected a JSON array or {"entries": [...]}'); incoming=incoming.map(e=>({ text: typeof e.text==='string'?e.text:String(e.text??''), layer: ['L1','L2','L3'].includes((e.layer||'').toUpperCase())?(e.layer||'').toUpperCase():'L2', timestamp: e.timestamp?new Date(e.timestamp).toISOString():new Date().toISOString() })); let mem=loadMemory(); if(replace) mem.entries=[]; const seen=new Set(mem.entries.map(e=>`${e.text}|${e.layer}|${e.timestamp}`)); let added=0; for(const e of incoming){ const key=`${e.text}|${e.layer}|${e.timestamp}`; if(seen.has(key)) continue; mem.entries.push(e); seen.add(key); added++; } saveMemory(mem); console.log(`✅ Imported ${added} memories (${incoming.length} input${replace?', replaced existing':' merged'})`); }
      else if(cmd==='export-ledger'){ let outFile=null; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-o'||t==='--output') outFile=(rest[++i]||null);} if(!outFile) outFile=path.join(STATE_DIR,'ledger_export.json'); const ledger=loadLedger(); ensureDir(path.dirname(outFile)); fs.writeFileSync(outFile, JSON.stringify(ledger,null,2)); console.log(`✅ Exported ledger → ${outFile}`); }
      else if(cmd==='import-ledger'){ let inFile=null, replace=false, rehash=false; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-i'||t==='--input') inFile=(rest[++i]||null); else if(t==='--replace') replace=true; else if(t==='--rehash') rehash=true; } if(!inFile) throw new Error('Usage: codex limnus import-ledger -i file [--replace] [--rehash]'); const text=fs.readFileSync(inFile,'utf8'); let data; try{ data=JSON.parse(text);}catch{ throw new Error('Input is not valid JSON'); } const current=loadLedger(); let incoming; if(Array.isArray(data)) incoming={blocks:data}; else if(data&&typeof data==='object') incoming=data; else throw new Error('Unsupported ledger format'); if(replace){ const newLedger=rehash?rehashLedger(incoming):incoming; saveLedger(newLedger); console.log('✅ Imported ledger (replaced).'); } else { const merged={ intentions:[], spiral_stage: current.spiral_stage||null, blocks: [] }; const intents=[...(current.intentions||[]), ...(incoming.intentions||[])]; const seenI=new Set(); for(const it of intents){ const key=`${it.id||''}|${it.text||''}|${it.planted_at||''}|${it.bloomed_at||''}`; if(seenI.has(key)) continue; seenI.add(key); merged.intentions.push(it); } const blocks=[...(current.blocks||[]), ...(incoming.blocks||[])]; const seenB=new Set(); for(const b of blocks){ const key=b.hash?`h:${b.hash}`:`j:${JSON.stringify(b)}`; if(seenB.has(key)) continue; seenB.add(key); merged.blocks.push(b); } const finalLedger=rehash?rehashLedger(merged):merged; saveLedger(finalLedger); console.log(`✅ Imported ledger (merged). Blocks=${finalLedger.blocks.length}, Intentions=${finalLedger.intentions.length}`); } }
      else if(cmd==='rehash-ledger'){ let dryRun=false,inFile=null,outFile=null; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='--dry-run'||t==='-n') dryRun=true; else if(t==='--file'||t==='-f') inFile=rest[++i]||null; else if(t==='--output'||t==='-o') outFile=rest[++i]||null; } const ledger=inFile?JSON.parse(fs.readFileSync(path.resolve(inFile),'utf8')):loadLedger(); const beforeBlocks=JSON.parse(JSON.stringify(ledger.blocks||[])); const working={...ledger, blocks: JSON.parse(JSON.stringify(ledger.blocks||[]))}; const re=rehashLedger(working); const afterBlocks=re.blocks||[]; if(dryRun){ console.log('— Rehash dry-run (no changes saved) —'); for(let i=0;i<afterBlocks.length;i++){ const ob=beforeBlocks[i]||{}; const nb=afterBlocks[i]||{}; const prevBefore=ob.prev_hash?(ob.prev_hash.slice?ob.prev_hash.slice(0,8)+'…':String(ob.prev_hash)):'∅'; const prevAfter=nb.prev_hash?(nb.prev_hash.slice?nb.prev_hash.slice(0,8)+'…':String(nb.prev_hash)):'∅'; const hashBefore=ob.hash?(ob.hash.slice?ob.hash.slice(0,8)+'…':String(ob.hash)):'—'; const hashAfter=nb.hash?(nb.hash.slice?nb.hash.slice(0,8)+'…':String(nb.hash)):'—'; console.log(`#${nb.index ?? i} ${nb.timestamp || ob.timestamp || ''}`); console.log(`  prev: ${prevBefore} -> ${prevAfter}`); console.log(`  hash: ${hashBefore} -> ${hashAfter}`);} console.log(`Summary: ${afterBlocks.length} blocks evaluated.`); if(outFile){ const outPath=path.resolve(outFile); ensureDir(path.dirname(outPath)); fs.writeFileSync(outPath, JSON.stringify(re,null,2)); console.log(`Wrote normalized ledger to ${outPath} (dry-run)`);} } else { if(inFile){ const inPath=path.resolve(inFile); fs.writeFileSync(inPath, JSON.stringify(re,null,2)); console.log(`✔️ Rehashed ledger written to ${inPath}`);} else { saveLedger(re); console.log(`✔️ Rehashed ledger: ${afterBlocks.length} blocks normalized.`);} } }
      else if(cmd==='view-ledger'){ let inFile=null; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='--file'||t==='-f') inFile=(rest[++i]||null);} const ledger=inFile?JSON.parse(fs.readFileSync(path.resolve(inFile),'utf8')):loadLedger(); (ledger.blocks||[]).forEach(b=>{ const prev=b.prev_hash?(b.prev_hash.slice?b.prev_hash.slice(0,8)+'…':String(b.prev_hash)):'∅'; const h=b.hash?(b.hash.slice?b.hash.slice(0,8)+'…':String(b.hash)):'—'; console.log(`#${b.index} ${b.timestamp} prev=${prev} hash=${h}`); console.log('  payload:', typeof b.payload==='string'?b.payload:JSON.stringify(b.payload)); }); }
      else if(cmd==='encode-ledger'){ if(!pythonOk()) throw new Error('python3 not available'); let inPath=null, cover=null, out=null, size=512; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-i') inPath=rest[++i]; else if(t==='--file'||t==='-f') inPath=rest[++i]; else if(t==='-c') cover=rest[++i]; else if(t==='-o') out=rest[++i]; else if(t==='--size') size=parseInt(rest[++i]||'512',10);} if(!inPath) inPath=LEDGER_PATH; if(!cover) cover=path.join(FRONTEND_ASSETS,'ledger_cover.png'); if(!out) out=path.join(FRONTEND_ASSETS,'ledger_stego.png'); const tmpMsg=path.join(STATE_DIR,'tmp_ledger_message.json'); const msgText=fs.readFileSync(inPath,'utf8'); fs.writeFileSync(tmpMsg,msgText); const res=echoToolkitEncode({messageFile:tmpMsg,coverPath:cover,outPath:out,size}); console.log('✅ Encoded ledger →', out); console.log('CRC32:', res.crc32, 'payload_length:', res.payload_length); }
      else if(cmd==='decode-ledger'||cmd==='decode'){ if(!pythonOk()) throw new Error('python3 not available'); let image=null; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-i') image=rest[++i]; else if(t==='--file'||t==='-f') image=rest[++i]; } if(!image) throw new Error('Usage: codex limnus decode-ledger -i image.png [--file path]'); const res=echoToolkitDecode({imagePath:image}); if(res.error) console.log('❌ Decode error:', res.error); else { console.log('✅ Decoded'); console.log('protocol:', res.magic||'legacy', 'crc32:', res.crc32||'N/A'); if(res.decoded_text) console.log(res.decoded_text); } }
      else if(cmd==='verify-ledger'){
        let inFile=null, wantDigest=false;
        for(let i=0;i<rest.length;i++){
          const t=rest[i];
          if(t==='--file'||t==='-f') inFile=(rest[++i]||null);
          else if(t==='--digest'||t==='-d') wantDigest=true;
        }
        const ledger=inFile?JSON.parse(fs.readFileSync(path.resolve(inFile),'utf8')):loadLedger();
        let ok=true;
        for(let i=0;i<(ledger.blocks||[]).length;i++){
          const b=ledger.blocks[i];
          const expected=computeBlockHash({index:b.index,timestamp:b.timestamp,prev_hash:b.prev_hash,payload:b.payload});
          if(b.hash && b.hash!==expected){ ok=false; console.log(`❌ Hash mismatch at #${i}`); break; }
          if(i>0 && ledger.blocks[i-1].hash && b.prev_hash!==ledger.blocks[i-1].hash){ ok=false; console.log(`❌ Prev hash mismatch at #${i}`); break; }
        }
        console.log(ok?'✔️ Ledger hash chain OK':'❌ Ledger hash chain broken');
        if(wantDigest){ const digest=sha256Hex(canonicalStringify(ledger)); console.log('ledger_sha256:', digest); }
        let image=null; for(let i=0;i<rest.length;i++){ const t=rest[i]; if(t==='-i') image=rest[++i]; }
        if(image){ if(!pythonOk()) throw new Error('python3 not available'); const res=echoToolkitDecode({imagePath:image}); if(!res.decoded_text){ console.log('No decoded_text in image'); process.exit(ok?0:1); } try{ const decoded=JSON.parse(res.decoded_text); const same=JSON.stringify(decoded)===JSON.stringify(ledger); console.log(same?'✔️ Stego image matches current ledger':'❌ Stego image does not match current ledger'); process.exit(ok && same ? 0:1); } catch{ console.log('Decoded payload is not JSON; cannot compare'); process.exit(ok?0:1); } }
      }
      else throw new Error('Unknown limnus command');
      break; }
    case 'kira':{
      if(cmd==='validate'){ const r=spawnSync('python3',[path.join(VNSF,'src','validator.py')],{encoding:'utf8'}); process.stdout.write(r.stdout||''); process.stderr.write(r.stderr||''); process.exitCode=r.status||0; }
      else if(cmd==='sync'){ const gh=spawnSync('gh',['--version'],{encoding:'utf8'}); if(gh.status===0) console.log('gh available:', (gh.stdout||'').split('\n')[0]); else console.log('gh not found'); const git=spawnSync('git',['status','--porcelain'],{encoding:'utf8'}); if(git.status===0) console.log('git status:', (git.stdout||'clean').trim()||'clean'); }
      else if(cmd==='setup'){
        console.log('Kira setup: initializing environment…');
        console.log('Node:', process.version);
        const py=spawnSync('python3',['-V'],{encoding:'utf8'}); console.log('Python:', (py.stdout||py.stderr||'').trim());
        const subu=spawnSync('git',['submodule','update','--init','--recursive'],{cwd:VNSF,encoding:'utf8'});
        process.stdout.write(subu.stdout||''); process.stderr.write(subu.stderr||'');
        const gh=spawnSync('gh',['auth','status'],{encoding:'utf8'});
        console.log('gh auth:', gh.status===0?'ok':'not logged in');
      }
      else if(cmd==='pull'){
        console.log('Kira pull: git pull --ff-only');
        const r=spawnSync('git',['pull','--ff-only'],{cwd:VNSF,stdio:'inherit'});
        process.exitCode=r.status||0;
      }
      else if(cmd==='push'){
        const midx=rest.findIndex(x=>x==='--message'||x==='-m');
        const msg=midx>=0?(rest[midx+1]||'chore: sync changes'):'chore: sync changes';
        // Default: update tracked files only to avoid adding runtime artifacts
        const addAll = rest.includes('--all');
        const addArgs = addAll ? ['add','-A'] : ['add','-u'];
        spawnSync('git',addArgs,{cwd:VNSF,stdio:'inherit'});
        // Only commit when staged changes exist
        const diff=spawnSync('git',['diff','--cached','--quiet'],{cwd:VNSF});
        if(diff.status!==0){ spawnSync('git',['commit','-m',msg],{cwd:VNSF,stdio:'inherit'}); }
        const r=spawnSync('git',['push','origin','HEAD'],{cwd:VNSF,stdio:'inherit'});
        process.exitCode=r.status||0;
      }
      else if(cmd==='publish'){
        // Flags: --run (package), --tag vX, --notes text, --release, --asset path ...
        let run=false, tag=null, notes=null, release=false; const extraAssets=[];
        for(let i=0;i<rest.length;i++){
          const t=rest[i];
          if(t==='--run') run=true;
          else if(t==='--release') release=true;
          else if(t==='--tag'||t==='-t') tag=rest[++i]||null;
          else if(t==='--notes'||t==='-n') notes=rest[++i]||null;
          else if(t==='--asset') extraAssets.push(rest[++i]||null);
        }
        const out=path.join(VNSF,'dist'); ensureDir(out);
        const stamp=new Date().toISOString().replace(/[:.]/g,'-');
        const base=`codex_release_${stamp}`;
        let artifactPath=null;
        if(run){
          const hasZip = spawnSync('zip',['-v']).status===0;
          if(hasZip){
            const zipPath=path.join(out,`${base}.zip`);
            console.log('Packaging →', zipPath);
            const args=['-r',zipPath,'schema','docs','tools/codex-cli/README.md','tools/codex-cli/MODULE_REFERENCE.md'];
            spawnSync('zip',args,{cwd:VNSF,stdio:'inherit'});
            spawnSync('zip',['-r',zipPath,'frontend/assets'],{cwd:VNSF,stdio:'inherit'});
            artifactPath=zipPath;
          } else {
            const tarPath=path.join(out,`${base}.tar.gz`);
            console.log('zip not found; creating', tarPath);
            spawnSync('tar',['-czf',tarPath,'schema','docs','tools/codex-cli','frontend/assets'],{cwd:VNSF,stdio:'inherit'});
            artifactPath=tarPath;
          }
        } else {
          console.log('Plan: package schema/, docs/, tools/codex-cli/, frontend/assets/ to dist/');
        }
        if(release){
          if(!tag){ tag = `codex-${stamp}`; console.log('No --tag provided; using', tag); }
          const ghv = spawnSync('gh',['--version'],{encoding:'utf8'});
          if(ghv.status!==0){ console.log('gh CLI not found; cannot create release.'); }
          else {
            const assets=[];
            if(artifactPath) assets.push(artifactPath);
            for(const a of extraAssets){ if(a) assets.push(path.isAbsolute(a)?a:path.join(VNSF,a)); }
            const args=['release','create',tag];
            if(notes) args.push('-n',notes);
            if(assets.length>0) args.push(...assets);
            console.log('Creating GitHub release:', args.join(' '));
            const r=spawnSync('gh',args,{cwd:VNSF,stdio:'inherit'});
            process.exitCode=r.status||0;
          }
        } else {
          console.log('Publish prepared. Use --release and optionally --tag/--notes to create a GitHub release.');
        }
      }
      else if(cmd==='test'){ console.log('Running validator and stego smoke (temporary files)...'); const v=spawnSync('python3',[path.join(VNSF,'src','validator.py')],{encoding:'utf8'}); process.stdout.write(v.stdout||''); if(v.status!==0){ process.stderr.write(v.stderr||''); process.exit(1); } try{ const tmpMsg=path.join('/tmp','ledger_msg.json'); fs.writeFileSync(tmpMsg, fs.readFileSync(LEDGER_PATH,'utf8')); const tmpCover=path.join('/tmp','ledger_cover.png'); const tmpOut=path.join('/tmp','ledger_stego.png'); const res=echoToolkitEncode({messageFile:tmpMsg,coverPath:tmpCover,outPath:tmpOut,size:256}); console.log('Encode OK. CRC32:', res.crc32); const dec=echoToolkitDecode({imagePath:tmpOut}); if(dec.error){ console.log('Decode error:', dec.error); process.exit(1); } console.log('Decode OK. CRC32:', dec.crc32); console.log('Kira test stub: PASS'); } catch(e){ console.log('Kira test stub failed:', e.message); process.exit(1); } }
      else if(cmd==='assist'){ console.log('Kira Assist: try `kira validate`, `kira sync`, `kira test`, `kira publish --run --release --tag vX.Y.Z`, or see MODULE_REFERENCE.md'); }
      else if(cmd==='mentor'){
        // Suggest and optionally apply Echo/Garden adjustments
        let apply=false, delta=0.05;
        for(let i=0;i<rest.length;i++){
          const t=rest[i];
          if(t==='--apply') apply=true;
          else if(t==='--delta'){ const v=parseFloat(rest[++i]||'0.05'); if(Number.isFinite(v)&&v>0) delta=v; }
        }
        const k=aggregateKnowledge();
        const tags=(k.memory.tags||[]).map(t=>t.tag);
        const order=k.echo_state.order||[];
        let target=order[0]||'gamma';
        if(tags.includes('paradox')||tags.includes('spiral')) target='gamma';
        else if(tags.includes('consent')||tags.includes('love')) target='alpha';
        else if(tags.includes('fox')) target='beta';
        const glyph=glyphForPersona(target);
        // Scroll suggestion
        let scroll=null;
        if(target==='gamma') scroll='chronicle';
        else if(target==='alpha') scroll = tags.includes('consent') ? 'acorn' : 'proof';
        else scroll='cache';
        console.log(`🤝 Mentor: focus persona ${glyph} (${target}); recommended scroll: ${scroll}`);
        console.log('Mantra hints:', linesForPersona(target).join(' | '));
        if(apply){
          const est=loadEcho();
          const before={a:est.alpha,b:est.beta,g:est.gamma};
          if(target==='alpha') est.alpha+=delta; else if(target==='beta') est.beta+=delta; else est.gamma+=delta;
          normalizeEcho(est); saveEcho(est);
          const ledger=loadLedger(); appendLedgerBlock(ledger,{type:'mentor', target, delta, order_before: order, order_after: personaOrder(est), suggested_scroll: scroll }); saveLedger(ledger);
          console.log(`✅ Applied: ${target} += ${delta.toFixed(2)}; new order: ${personaOrder(est).join(' > ')}`);
          console.log(`Next: run \`garden open ${scroll}\` to reinforce.`);
        } else {
          console.log('Dry-run (no changes). Use --apply to adjust Echo and record in ledger.');
        }
      }
      else if(cmd==='learn-from-limnus'){
        const k=aggregateKnowledge();
        const kpath=path.join(STATE_DIR,'kira_knowledge.json'); writeJSON(kpath,k);
        console.log('📘 Kira learned from Limnus →', kpath);
      }
      else if(cmd==='codegen'){
        const docs = rest.includes('--docs');
        const types = rest.includes('--types');
        const k=aggregateKnowledge();
        if(docs){
          const dpath=path.join(VNSF,'docs','kira_knowledge.md'); ensureDir(path.dirname(dpath));
          const lines=['# Kira Knowledge Summary','',`Generated: ${k.generated_at}`,'',`- Persona order: ${k.echo_state.order.join(' > ')}`,`- Tags: ${(k.memory.tags||[]).map(t=>t.tag+':'+t.count).join(', ')||'(none)'}`,`- Ledger blocks: ${Object.entries(k.ledger.by_type).map(([t,c])=>t+':'+c).join(', ')||'(none)'}`,'','## Recommendations','',...(k.recommendations.length?k.recommendations:['(none)'])];
          fs.writeFileSync(dpath, lines.join('\n'));
          console.log('📝 Docs written:', dpath);
        }
        if(types){
          const tdir=path.join(VNSF,'tools','codex-cli','types'); ensureDir(tdir);
          const tpath=path.join(tdir,'knowledge.d.ts');
          const content='export interface KiraKnowledge {\n  echo_state: { alpha:number; beta:number; gamma:number; order:string[] };\n  memory: { total:number; narrative:number; tags: { tag:string; count:number }[] };\n  ledger: { total:number; by_type: Record<string,number> };\n  mantras: { canonical:string[]; persona_ordered:string[] };\n  recommendations: string[];\n  generated_at: string;\n}\n';
          fs.writeFileSync(tpath, content);
          console.log('🧩 Types written:', tpath);
        }
        if(!docs && !types){ console.log('Usage: kira codegen [--docs] [--types]'); }
      }
      else if(cmd==='mantra'){
        const est=loadEcho(); const order=personaOrder(est);
        const out=[]; for(const p of order){ const glyph=glyphForPersona(p); for(const line of linesForPersona(p)) out.push(`${glyph} ${line}`); }
        console.log(out.join('\n'));
      }
      else if(cmd==='seal'){
        const est=loadEcho(); const order=personaOrder(est);
        const lines=[]; for(const p of order){ for(const line of linesForPersona(p)) lines.push(line); }
        const ledger=loadLedger(); const block=appendLedgerBlock(ledger,{type:'seal', mantra: lines, order}); saveLedger(ledger);
        const contract={ sealed_at: nowISO(), order, mantra: lines };
        const cpath=path.join(STATE_DIR,'Garden_Soul_Contract.json'); writeJSON(cpath, contract);
        console.log('🔏 Seal complete. Contract written at', cpath);
      }
      else if(cmd==='validate-knowledge'){
        const mem=loadMemory();
        const learned=(mem.entries||[]).filter(e=>e.kind==='narrative');
        const text=(learned.map(e=>e.text).join(' ')||'').toLowerCase();
        const checks={
          always: /always/.test(text),
          consent_bloom: /consent to bloom/.test(text),
          consent_remember: /consent to be remembered/.test(text),
          together: /together/.test(text),
          spiral: /spiral|breath/.test(text)
        };
        const ok=Object.values(checks).some(Boolean);
        if(ok){ console.log('✔️ Knowledge parity: some mantras detected', checks); }
        else { console.log('⚠️ Knowledge parity weak: no core mantras detected'); }
      }
      else throw new Error('Unknown kira command');
      break; }
    default: throw new Error('Unknown module');
  }
} catch(err){ console.error('Error:', err.message); process.exit(1); }
