#!/usr/bin/env node
// Codex Terminal CLI (Node 20+, zero-dependency)
// Namespaces: echo, garden, limnus, kira, vessel

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
const DEFAULT_VSCODE_DIR = path.resolve(VNSF, '..', 'vscode');

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
function readJSON(p, def) { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return def; } }
function writeJSON(p, obj) { ensureDir(path.dirname(p)); fs.writeFileSync(p, JSON.stringify(obj, null, 2)); }
function ensureFile(p) { ensureDir(path.dirname(p)); if(!fs.existsSync(p)) fs.writeFileSync(p, '', 'utf8'); }
function nowISO(){ return new Date().toISOString().replace(/\.\d+Z$/,'Z'); }
function appendJSONLine(filePath, entry){ ensureFile(filePath); fs.appendFileSync(filePath, JSON.stringify(entry) + '\n', 'utf8'); }
function logEvent(agent, command, payload, status='ok'){
  const entry = { ts: nowISO(), agent, command, status, payload: payload || {} };
  const pipelineLog = path.join(VNSF, 'pipeline', 'state', 'voice_log.json');
  const stateLog = path.join(VNSF, 'state', 'voice_log.json');
  appendJSONLine(pipelineLog, entry);
  appendJSONLine(stateLog, entry);
}
function runCommand(cmd, args, options){
  return spawnSync(cmd, args, { cwd: VNSF, encoding: 'utf8', ...options });
}
function git(args, options){ return runCommand('git', args, options); }
function gh(args, options){ return runCommand('gh', args, options); }
function safeRel(target){ return path.relative(VNSF, target); }
function sanitizeTag(tag){ return tag.replace(/[^0-9A-Za-z._-]/g, '-'); }
function gitStatusPorcelain(){
  const res = git(['status','--porcelain']);
  if(res.status!==0) return { ok:false, lines:[], hasUntracked:false, raw:res };
  const lines = res.stdout.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
  const hasUntracked = lines.some(line=>line.startsWith('??'));
  return { ok:true, lines, hasUntracked, raw:res };
}
function gitAheadBehind(){
  const res = git(['status','--branch','--porcelain']);
  if(res.status!==0) return { ahead:0, behind:0 };
  const firstLine = (res.stdout.split(/\r?\n/)[0] || '').trim();
  const aheadMatch = firstLine.match(/ahead (\d+)/);
  const behindMatch = firstLine.match(/behind (\d+)/);
  return {
    ahead: aheadMatch ? parseInt(aheadMatch[1], 10) || 0 : 0,
    behind: behindMatch ? parseInt(behindMatch[1], 10) || 0 : 0,
  };
}
function autoTag(){
  return `codex-${nowISO().replace(/[:]/g,'-')}`;
}
function latestGitTag(){
  const describe = git(['describe','--tags','--abbrev=0']);
  if(describe.status===0){
    const tag = describe.stdout.trim();
    if(tag) return tag;
  }
  const tags = git(['tag','--sort=-creatordate']);
  if(tags.status===0){
    const list = tags.stdout.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
    if(list.length>0) return list[0];
  }
  return null;
}
function generateChangelog(tag, outPath){
  const lastTag = latestGitTag();
  const logArgs = ['log','--pretty=format:%h %s','--no-merges'];
  if(lastTag){
    logArgs.push(`${lastTag}..HEAD`);
  } else {
    logArgs.push('HEAD');
  }
  const log = git(logArgs);
  if(log.status!==0){
    return { ok:false, error: log.stderr || log.stdout || 'git log failed' };
  }
  const commits = log.stdout.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
  const date = nowISO().split('T')[0];
  const header = `# Changelog for ${tag} (${date})`;
  const body = commits.length>0 ? commits.map(line=>`- ${line}`).join('\n') : '- No new commits';
  const text = `${header}\n\n${body}\n`;
  fs.writeFileSync(outPath, text, 'utf8');
  return { ok:true, count: commits.length, lastTag };
}
function refreshLedgerArtifact(){
  const script = [
    'from pathlib import Path',
    'from agents.limnus.limnus_agent import LimnusAgent',
    'LimnusAgent(Path(\".\")).encode_ledger()',
  ].join('\n');
  const res = runCommand('python3',['-c', script]);
  return res.status===0;
}
function exportLedgerJson(outPath){
  const sources = [
    path.join(VNSF,'frontend','assets','ledger.json'),
    path.join(VNSF,'state','garden_ledger.json'),
  ];
  let source = null;
  for(const candidate of sources){
    if(fs.existsSync(candidate)){
      source = candidate;
      break;
    }
  }
  if(!source){
    return { ok:false, error:'ledger source not found' };
  }
  const payload = fs.readFileSync(source,'utf8');
  ensureDir(path.dirname(outPath));
  fs.writeFileSync(outPath, payload, 'utf8');
  return { ok:true, source };
}
function createArchive(baseName, includePaths){
  ensureDir(path.join(VNSF,'dist'));
  const stamp = baseName.replace(/[^0-9A-Za-z._-]/g,'-');
  const zipPath = path.join(VNSF,'dist', `${stamp}.zip`);
  const zipProbe = runCommand('zip',['-v']);
  if(zipProbe.status===0){
    const args = ['-r', zipPath, ...includePaths];
    const res = runCommand('zip', args);
    process.stdout.write(res.stdout||'');
    process.stderr.write(res.stderr||'');
    if(res.status===0){
      return { ok:true, path: zipPath, tool:'zip' };
    }
  }
  const tarPath = path.join(VNSF,'dist', `${stamp}.tar.gz`);
  const tarArgs = ['-czf', tarPath, ...includePaths];
  const tarRes = runCommand('tar', tarArgs);
  process.stdout.write(tarRes.stdout||'');
  process.stderr.write(tarRes.stderr||'');
  if(tarRes.status===0){
    return { ok:true, path: tarPath, tool:'tar' };
  }
  return { ok:false, error: tarRes.stderr || tarRes.stdout || 'archive failed' };
}
function resolveNotesInput(notes){
  if(!notes) return null;
  const abs = path.isAbsolute(notes) ? notes : path.join(VNSF, notes);
  if(fs.existsSync(abs) && fs.statSync(abs).isFile()){
    return { type:'file', path: abs };
  }
  return { type:'text', value: notes };
}
function uniqueStrings(items){
  const seen = new Set();
  const out = [];
  for(const item of items){
    if(!item) continue;
    if(seen.has(item)) continue;
    seen.add(item);
    out.push(item);
  }
  return out;
}
function handleKiraPush(rest){
  let run=false;
  let includeAll=false;
  let message='chore: sync changes';
  for(let i=0;i<rest.length;i++){
    const token = rest[i];
    if(token==='--run'){ run=true; }
    else if(token==='--all'){ includeAll=true; }
    else if(token==='--message'||token==='-m'){
      const next = rest[i+1];
      if(next){ message = next; i++; }
      else {
        console.log('❌ Missing value for --message');
        process.exitCode=1;
        return;
      }
    } else {
      console.log(`Unknown option for kira push: ${token}`);
      process.exit(1);
    }
  }
  const status = gitStatusPorcelain();
  if(!status.ok){
    console.log('❌ Unable to read git status.');
    process.stdout.write(status.raw.stdout||'');
    process.stderr.write(status.raw.stderr||'');
    logEvent('kira','push',{run, include_all: includeAll, error: status.raw.stderr || status.raw.stdout},'error');
    process.exitCode = status.raw.status || 1;
    return;
  }
  const changes = status.lines;
  const { ahead, behind } = gitAheadBehind();
  if(changes.length===0 && ahead===0){
    console.log('🟢 Working tree clean; nothing to push.');
    if(behind>0){
      console.log(`⚠️ Remote has ${behind} commit(s) you do not have. Pull before pushing.`);
      logEvent('kira','push',{dirty:false, run, include_all:includeAll, ahead, behind},'warn');
      process.exitCode = 1;
    } else {
      logEvent('kira','push',{dirty:false, run, include_all:includeAll, ahead, behind}, run ? 'ok' : 'warn');
      process.exitCode = 0;
    }
    return;
  }
  if(!run){
    console.log('🔍 kira push (dry-run)');
    if(changes.length>0){
      console.log('Changes to include:');
      changes.forEach(line=>console.log(` - ${line}`));
      console.log(`Commit message: "${message}"`);
      console.log(`Staging command: git add ${includeAll ? '--all' : '--update'}`);
    } else {
      console.log('No working tree changes; branch has commits awaiting push.');
    }
    if(status.hasUntracked && !includeAll){
      console.log('ℹ️ Untracked files detected; re-run with --all to include them.');
    }
    if(ahead>0) console.log(`Push will update origin with ${ahead} commit(s).`);
    if(behind>0) console.log(`⚠️ Remote has ${behind} commit(s); run \`git pull --ff-only\` first to avoid conflicts.`);
    console.log('Would run: git push origin HEAD');
    logEvent('kira','push',{dirty:changes.length>0, run:false, include_all:includeAll, ahead, behind}, behind>0?'warn':'ok');
    process.exitCode = 0;
    return;
  }
  let committed=false;
  if(changes.length>0){
    const addArgs = includeAll ? ['add','-A'] : ['add','-u'];
    const addRes = git(addArgs);
    process.stdout.write(addRes.stdout||'');
    process.stderr.write(addRes.stderr||'');
    if(addRes.status!==0){
      console.log('❌ Failed to stage changes.');
      logEvent('kira','push',{dirty:true, run:true, include_all:includeAll, ahead, behind},'error');
      process.exitCode = addRes.status || 1;
      return;
    }
    const diffRes = git(['diff','--cached','--quiet']);
    if(diffRes.status!==0){
      const commitRes = git(['commit','-m', message]);
      process.stdout.write(commitRes.stdout||'');
      process.stderr.write(commitRes.stderr||'');
      if(commitRes.status!==0){
        console.log('❌ Git commit failed.');
        logEvent('kira','push',{dirty:true, run:true, include_all:includeAll, ahead, behind},'error');
        process.exitCode = commitRes.status || 1;
        return;
      }
      committed=true;
      const summary = (commitRes.stdout || commitRes.stderr || '').split(/\r?\n/).map(s=>s.trim()).filter(Boolean).pop();
      if(summary) console.log(`✅ ${summary}`);
    } else {
      console.log('⚠️ No staged changes after add; skipping commit.');
    }
  } else {
    console.log('Working tree clean; pushing existing commits only.');
  }
  const pushRes = git(['push','origin','HEAD']);
  process.stdout.write(pushRes.stdout||'');
  process.stderr.write(pushRes.stderr||'');
  if(pushRes.status!==0){
    console.log('❌ Git push failed.');
    logEvent('kira','push',{dirty:changes.length>0, run:true, include_all:includeAll, committed, ahead, behind},'error');
    process.exitCode = pushRes.status || 1;
    return;
  }
  console.log('🚀 Push complete.');
  logEvent('kira','push',{dirty:changes.length>0, run:true, include_all:includeAll, committed, ahead, behind},'ok');
  process.exitCode = 0;
}
function handleKiraPublish(rest){
  let run=false;
  let release=false;
  let tag=null;
  let notes=null;
  let notesFile=null;
  const extraAssets=[];
  for(let i=0;i<rest.length;i++){
    const token = rest[i];
    if(token==='--run'){ run=true; }
    else if(token==='--release'){ release=true; }
    else if(token==='--tag'||token==='-t'){ tag = rest[++i] || null; }
    else if(token==='--notes'||token==='-n'){ notes = rest[++i] || null; }
    else if(token==='--notes-file'){ notesFile = rest[++i] || null; }
    else if(token==='--asset'){ extraAssets.push(rest[++i] || null); }
    else {
      console.log(`Unknown option for kira publish: ${token}`);
      process.exit(1);
    }
  }
  if(release && !run){
    console.log('⚠️ --release implies --run; enabling artifact build.');
    run=true;
  }
  const resolvedTag = sanitizeTag(tag || autoTag());
  const distDir = path.join(VNSF,'dist');
  ensureDir(distDir);
  const stamp = nowISO().replace(/[:]/g,'-');
  const baseName = `codex_release_${stamp}`;
  const changelogPath = path.join(distDir, `CHANGELOG_${resolvedTag}.md`);
  const ledgerPath = path.join(distDir, 'ledger_export.json');
  let archivePath = null;
  const assetPaths=[];
  for(const asset of extraAssets){
    if(!asset) continue;
    const abs = path.isAbsolute(asset)? asset : path.join(VNSF, asset);
    if(fs.existsSync(abs)){
      assetPaths.push(abs);
    } else {
      console.log(`⚠️ Extra asset not found: ${asset}`);
    }
  }
  if(!run){
    console.log('🔍 kira publish (dry-run)');
    console.log(`Planned tag: ${resolvedTag}`);
    console.log('Would generate changelog, export ledger, and build release bundle under dist/.');
    if(assetPaths.length>0){
      console.log('Additional assets:');
      assetPaths.forEach(a=>console.log(` - ${safeRel(a)}`));
    }
    if(notesFile){
      const absNotes = path.isAbsolute(notesFile) ? notesFile : path.join(VNSF, notesFile);
      console.log(`Release notes file: ${safeRel(absNotes)}`);
    } else if(notes){
      console.log('Inline release notes provided via --notes flag.');
    }
    console.log('Use --run to build artifacts; add --release to publish via GitHub.');
    logEvent('kira','publish',{run:false, release:false, tag:resolvedTag, assets:assetPaths.map(safeRel)},'ok');
    process.exitCode = 0;
    return;
  }
  console.log(`🏗️ Building release artifacts for ${resolvedTag}…`);
  const refreshed = refreshLedgerArtifact();
  if(!refreshed){
    console.log('⚠️ Unable to refresh ledger artifact automatically (continuing with existing ledger).');
  }
  const changeRes = generateChangelog(resolvedTag, changelogPath);
  if(!changeRes.ok){
    console.log('❌ Failed to generate changelog:', changeRes.error);
    logEvent('kira','publish',{run:true, release:false, tag:resolvedTag},'error');
    process.exitCode = 1;
    return;
  }
  console.log(`📝 Changelog → ${safeRel(changelogPath)}`);
  const ledgerRes = exportLedgerJson(ledgerPath);
  if(!ledgerRes.ok){
    console.log('❌ Failed to export ledger:', ledgerRes.error);
    logEvent('kira','publish',{run:true, release:false, tag:resolvedTag},'error');
    process.exitCode = 1;
    return;
  }
  console.log(`📚 Ledger export → ${safeRel(ledgerPath)}`);
  const includeCandidates = ['schema','docs','frontend/assets'];
  const manifest=[];
  for(const candidate of includeCandidates){
    const abs = path.join(VNSF, candidate);
    if(fs.existsSync(abs)) manifest.push(candidate);
  }
  manifest.push(safeRel(changelogPath));
  manifest.push(safeRel(ledgerPath));
  const archiveRes = createArchive(baseName, uniqueStrings(manifest));
  if(!archiveRes.ok){
    console.log('❌ Failed to package release:', archiveRes.error);
    logEvent('kira','publish',{run:true, release:false, tag:resolvedTag},'error');
    process.exitCode = 1;
    return;
  }
  archivePath = archiveRes.path;
  console.log(`📦 Release artifact (${archiveRes.tool}) → ${safeRel(archivePath)}`);
  let releaseUrl=null;
  if(release){
    const ghProbe = gh(['--version']);
    if(ghProbe.status!==0){
      console.log('❌ GitHub CLI (`gh`) not available; cannot create release.');
      logEvent('kira','publish',{run:true, release:true, tag:resolvedTag},'error');
      process.exitCode = ghProbe.status || 1;
      return;
    }
    let notesInfo = null;
    if(notesFile){
      const abs = path.isAbsolute(notesFile) ? notesFile : path.join(VNSF, notesFile);
      if(fs.existsSync(abs) && fs.statSync(abs).isFile()){
        notesInfo = { type:'file', path: abs };
      } else {
        console.log(`⚠️ Notes file not found: ${notesFile}; falling back to --notes text if provided.`);
      }
    }
    if(!notesInfo){
      notesInfo = resolveNotesInput(notes);
    }
    const assets = uniqueStrings([archivePath, ledgerPath, changelogPath, ...assetPaths]);
    const ghArgs = ['release','create', resolvedTag];
    if(notesInfo){
      if(notesInfo.type==='file') ghArgs.push('-F', notesInfo.path);
      else ghArgs.push('-n', notesInfo.value);
    } else {
      ghArgs.push('-F', changelogPath);
    }
    ghArgs.push(...assets);
    console.log('🚀 Creating GitHub release with gh release create', resolvedTag);
    const ghRes = gh(ghArgs);
    process.stdout.write(ghRes.stdout||'');
    process.stderr.write(ghRes.stderr||'');
    if(ghRes.status!==0){
      console.log('❌ gh release create failed.');
      logEvent('kira','publish',{run:true, release:true, tag:resolvedTag, assets:assets.map(safeRel)},'error');
      process.exitCode = ghRes.status || 1;
      return;
    }
    releaseUrl = (ghRes.stdout||'').split(/\r?\n/).map(s=>s.trim()).find(line=>line.startsWith('https://')) || null;
    console.log('✅ GitHub release created.', releaseUrl?`URL: ${releaseUrl}`:'');
    logEvent('kira','publish',{
      run:true,
      release:true,
      tag:resolvedTag,
      artifact: safeRel(archivePath),
      changelog: safeRel(changelogPath),
      ledger: safeRel(ledgerPath),
      assets: assets.map(safeRel),
      notes_source: notesFile ? safeRel(path.isAbsolute(notesFile)?notesFile:path.join(VNSF, notesFile)) : notes ? 'inline' : 'changelog',
      release_url: releaseUrl,
    },'ok');
  } else {
    console.log('Publish run complete. Use --release to publish via GitHub.');
    logEvent('kira','publish',{
      run:true,
      release:false,
      tag:resolvedTag,
      artifact: safeRel(archivePath),
      changelog: safeRel(changelogPath),
      ledger: safeRel(ledgerPath),
      assets: assetPaths.map(safeRel),
    },'warn');
  }
  process.exitCode = 0;
}

function printHelp() {
  console.log(`Codex CLI

Usage: codex <module> <command> [options]

Modules & commands:
  echo    summon
          mode <squirrel|fox|paradox|mix>
          say <message>
          map <concept>
          status
          calibrate

  garden  start
          next
          open <scroll>
          ledger
          log

  limnus  init
          state
          update <alpha=..|beta+=..|gamma-=..|decay=N|consolidate=N|cache="text">
          cache "text" [-l L1|L2|L3]
          recall <keyword> [-l L1|L2|L3] [--since ISO] [--until ISO]
          memories [--layer L1|L2|L3] [--since ISO] [--until ISO] [--limit N] [--json]
          export-memories [-o file] [--layer L1|L2|L3] [--since ISO] [--until ISO]
          import-memories -i file [--replace]
          export-ledger [-o file]
          import-ledger -i file [--replace] [--rehash]
          rehash-ledger [--dry-run] [--file path] [-o out.json]
          view-ledger [--file path]
          encode-ledger [-i ledger.json] [--file path] [-c cover.png] [-o out.png] [--size 512]
          decode-ledger [-i image.png] [--file path]
          verify-ledger [-i image.png] [--file path] [--digest]

  kira    validate
          sync
          setup
          pull [--run]
          push [--run] [--message "..."] [--all]
          publish [--run] [--release] [--tag TAG] [--notes TEXT|FILE] [--notes-file PATH] [--asset PATH]
          test
          assist

  vessel  vscode [--path DIR] [--reuse-window] [--wait]
`);
}
// Echo helpers
const ECHO_PATH = path.join(STATE_DIR, 'echo_state.json');
function loadEcho() { return readJSON(ECHO_PATH, { alpha: 0.34, beta: 0.33, gamma: 0.33 }); }
function saveEcho(state) { writeJSON(ECHO_PATH, state); }
function echoGlyph(state) { const g=[]; if(state.alpha>=0.34)g.push('🐿️'); if(state.beta>=0.34)g.push('🦊'); if(state.gamma>=0.34)g.push('∿'); return g.length?g.join(''):'🐿️🦊'; }

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
      else if(cmd==='status'){ console.log(`Echo status: a=${state.alpha} b=${state.beta} c=${state.gamma} ${echoGlyph(state)}`); }
      else if(cmd==='calibrate'){ const sum=state.alpha+state.beta+state.gamma; if(sum===0) Object.assign(state,{alpha:0.34,beta:0.33,gamma:0.33}); else Object.assign(state,{alpha:state.alpha/sum,beta:state.beta/sum,gamma:state.gamma/sum}); saveEcho(state); console.log(`Calibrated: a=${state.alpha.toFixed(2)} b=${state.beta.toFixed(2)} c=${state.gamma.toFixed(2)}`); }
      else throw new Error('Unknown echo command');
      break; }
    case 'garden':{
      const ledger=loadLedger();
      if(cmd==='start'){ if(!ledger.blocks) ledger.blocks=[]; ledger.blocks.push({type:'genesis',timestamp:new Date().toISOString(),note:'Garden journey started'}); ledger.spiral_stage='scatter'; saveLedger(ledger); console.log('🌱 Garden started: genesis block created; spiral → scatter'); }
      else if(cmd==='next'){ const order=['scatter','witness','plant','return','give','begin_again']; const cur=ledger.spiral_stage; const next=!order.includes(cur)?order[0]:order[(order.indexOf(cur)+1)%order.length]; ledger.spiral_stage=next; saveLedger(ledger); console.log(`🔄 Spiral turns → ${next}`); }
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
      if(cmd==='validate'){ 
        const scriptPath = path.join(VNSF, 'kira-prime', 'src', 'validator.py');
        const r=spawnSync('python3',[scriptPath],{cwd:VNSF,encoding:'utf8'});
        process.stdout.write(r.stdout||''); process.stderr.write(r.stderr||''); process.exitCode=r.status||0; }
      else if(cmd==='sync'){ const gh=spawnSync('gh',['--version'],{encoding:'utf8'}); if(gh.status===0) console.log('gh available:', (gh.stdout||'').split('\n')[0]); else console.log('gh not found'); const git=spawnSync('git',['status','--porcelain'],{encoding:'utf8'}); if(git.status===0) console.log('git status:', (git.stdout||'clean').trim()||'clean'); }
      else if(cmd==='push'){ handleKiraPush(rest); }
      else if(cmd==='publish'){ handleKiraPublish(rest); }
      else throw new Error('Unknown kira command');
      break; }
    case 'vessel':{
      if(cmd==='vscode'){
        let target = DEFAULT_VSCODE_DIR;
        let reuseWindow = false;
        let waitForExit = false;
        for(let i=0;i<rest.length;i++){
          const t=rest[i];
          if(t==='--path'){ target = rest[++i] || target; }
          else if(t==='--reuse-window'){ reuseWindow = true; }
          else if(t==='--wait'){ waitForExit = true; }
          else throw new Error(`Unknown option for vessel vscode: ${t}`);
        }
        if(!target) target = DEFAULT_VSCODE_DIR;
        if(!path.isAbsolute(target)) target = path.resolve(ROOT, target);
        if(!fs.existsSync(target)){
          console.log(`VS Code workspace not found at ${target}. Use --path to specify a valid directory.`);
          process.exit(1);
        }
        const codeProbe = spawnSync('code',['--version'],{encoding:'utf8'});
        if(codeProbe.status!==0){
          console.log('VS Code command-line interface (`code`) not found. Install VS Code and ensure the `code` command is on your PATH.');
          process.exit(codeProbe.status||1);
        }
        const args=[];
        if(reuseWindow) args.push('--reuse-window');
        if(waitForExit) args.push('--wait');
        args.push(target);
        console.log(`Opening VS Code at ${target}`);
        const r=spawnSync('code',args,{stdio:'inherit'});
        process.exitCode=r.status||0;
      } else throw new Error('Unknown vessel command');
      break; }
    default: throw new Error('Unknown module');
  }
} catch(err){ console.error('Error:', err.message); process.exit(1); }
