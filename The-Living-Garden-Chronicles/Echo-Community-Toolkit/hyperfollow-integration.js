#!/usr/bin/env node
const fs = require('fs').promises;
const path = require('path');
const { promisify } = require('util');
const exec = promisify(require('child_process').exec);
const cheerio = require('cheerio');
const crypto = require('crypto');

const HYPERFOLLOW_URL = 'https://distrokid.com/hyperfollow/echosquirrel/crystaline-echo';
const REPO_ROOT = process.cwd();
const DRY_RUN = process.argv.includes('--dry-run');
const DEFAULT_SOULCODE_BUNDLE = path.join(REPO_ROOT, 'integration', 'outputs', 'echo_live.json');
const DEFAULT_MEMORY_JSON = path.join(REPO_ROOT, 'integration', 'outputs', 'memory_state.json');
const DEFAULT_LEDGER_IMG = path.join(REPO_ROOT, 'integration', 'ledger', 'block.png');
async function injectEchoClientHelper(html) {
  if (html.includes('id="echo-client-helper"')) return html;
  const tag = `\n<script id=\"echo-client-helper\" src=\"/web/echo-client.js\"></script>\n`;
  const close = html.lastIndexOf('</body>');
  return close !== -1 ? (html.slice(0, close) + tag + html.slice(close)) : (html + tag);
}

function bytesHuman(n){ const u=['B','KB','MB','GB']; let i=0, v=n; while(v>=1024&&i<u.length-1){ v/=1024; i++; } return `${v.toFixed(v<10&&i>0?1:0)} ${u[i]}`; }
function metaFromJson(json){ const sha=crypto.createHash('sha256').update(json,'utf8').digest('hex'); const bytes=Buffer.byteLength(json,'utf8'); return { sha256: sha, short: sha.slice(0,8), human: bytesHuman(bytes) }; }

function injectDevToolsHotkey(html) {
  if (html.includes('id="echo-dev-tools-hotkey"')) return html;
  const s = `\n<script id=\"echo-dev-tools-hotkey\">(function(){try{document.addEventListener('keydown',function(e){try{if((e.ctrlKey||e.metaKey)&&e.shiftKey&&(e.key==='D'||e.key==='d')){var p=document.getElementById('echo-dev-tools');if(!p)return; if(p.style.display==='none'){p.style.display='flex';} else {p.style.display='none';} e.preventDefault();}}catch(_){}});}catch(_){}})();</script>\n`;
  const close = html.lastIndexOf('</body>');
  return close !== -1 ? (html.slice(0, close) + s + html.slice(close)) : (html + s);
}
function buildDevToolsPanel({ bundleDataUrl, memoryDataUrl, bundleMeta, memoryMeta }) {
  const btnBundle = bundleDataUrl ? `<a href=\"${bundleDataUrl}\" download=\"echo_bundle.json\" class=\"btn\">⬇ Bundle</a>` : '';
  const metaBundle = bundleMeta ? `<span class=\"meta\" title=\"sha256 ${bundleMeta.sha256}\">${bundleMeta.short} • ${bundleMeta.human}</span>` : '';
  const copyBundle = bundleMeta ? `<button type=\"button\" class=\"btn\" onclick=\"(function(t){try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t);}else{var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);}var s=document.getElementById('echo-dev-tools-msg');if(s){s.textContent='Copied bundle SHA-256';setTimeout(function(){s.textContent='';},1500);}}catch(e){alert('Copy failed');}})('${bundleMeta.sha256}')\">Copy Bundle SHA</button>` : '';
  const copyBundleJson = bundleDataUrl ? `<button type=\"button\" class=\"btn\" onclick=\"(function(){try{var el=document.getElementById('echo-soulcode-bundle'); if(!el) return; var txt=el.textContent||el.innerText||''; if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt);} else {var ta=document.createElement('textarea'); ta.value=txt; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);} var s=document.getElementById('echo-dev-tools-msg'); if(s){s.textContent='Copied bundle JSON'; setTimeout(function(){s.textContent='';},1500);} }catch(e){alert('Copy failed');}})()\">Copy Bundle JSON</button>` : '';
  const btnMemory = memoryDataUrl ? `<a href=\"${memoryDataUrl}\" download=\"memory_state.json\" class=\"btn\">⬇ Memory</a>` : '';
  const metaMemory = memoryMeta ? `<span class=\"meta\" title=\"sha256 ${memoryMeta.sha256}\">${memoryMeta.short} • ${memoryMeta.human}</span>` : '';
  const copyMemory = memoryMeta ? `<button type=\"button\" class=\"btn\" onclick=\"(function(t){try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t);}else{var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);}var s=document.getElementById('echo-dev-tools-msg');if(s){s.textContent='Copied memory SHA-256';setTimeout(function(){s.textContent='';},1500);}}catch(e){alert('Copy failed');}})('${memoryMeta.sha256}')\">Copy Memory SHA</button>` : '';
  const copyMemoryJson = memoryDataUrl ? `<button type=\"button\" class=\"btn\" onclick=\"(function(){try{var el=document.getElementById('echo-memory-state'); if(!el) return; var txt=el.textContent||el.innerText||''; if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt);} else {var ta=document.createElement('textarea'); ta.value=txt; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);} var s=document.getElementById('echo-dev-tools-msg'); if(s){s.textContent='Copied memory JSON'; setTimeout(function(){s.textContent='';},1500);} }catch(e){alert('Copy failed');}})()\">Copy Memory JSON</button>` : '';
  const panel = `\n<div id=\"echo-dev-tools\" style=\"position:fixed; left:20px; bottom:20px; z-index:1100; background:rgba(0,0,0,0.7); color:#e7e8ea; border:1px solid rgba(255,255,255,0.2); border-radius:10px; padding:8px 10px; font-size:12px; display:flex; gap:8px; align-items:center;\">\n  <button type=\"button\" class=\"btn hdr\" id=\"echo-dev-tools-toggle\" onclick=\"(function(){var p=document.getElementById('echo-dev-tools'); if(!p) return; p.classList.toggle('collapsed'); var t=document.getElementById('echo-dev-tools-toggle'); if(t) t.textContent = p.classList.contains('collapsed') ? '▸' : '▾'; })()\">▾</button>\n  <span class=\"hdr\" style=\"opacity:0.9\">Dev Tools</span>\n  ${btnBundle}${metaBundle}${copyBundle}${copyBundleJson}\n  ${btnMemory}${metaMemory}${copyMemory}${copyMemoryJson}\n  <button type=\"button\" class=\"btn\" onclick=\"(function(){var el=document.getElementById('echo-memory-spark'); if(el){ el.style.display = (el.style.display==='none'?'block':'none'); }})();\">Toggle Viz</button>\n  <span id=\"echo-dev-tools-msg\" class=\"meta\" style=\"margin-left:4px\"></span>\n  <style>\n    #echo-dev-tools .btn{ background:#1a1b23; color:#e7e8ea; border:1px solid rgba(255,255,255,0.2); padding:4px 8px; border-radius:6px; text-decoration:none; }\n    #echo-dev-tools .btn:hover{ background:#242634 }\n    #echo-dev-tools .meta{ opacity:0.75; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }\n    #echo-dev-tools.collapsed > :not(.hdr):not(style){ display:none }\n  </style>\n</div>\n<div id=\"echo-dev-tools-hint\" style=\"position:fixed; left:20px; bottom:4px; z-index:1100; color:#e7e8ea; font-size:11px; opacity:0.7;\">Hotkey: Ctrl+Shift+D to hide/show panel</div>\n`;
  return panel;
}

function removeExistingDevTools(html){
  let out = html.replace(/<div id=\"echo-dev-tools\"[\s\S]*?<\/div>\n?/m, '');
  out = out.replace(/<div id=\"echo-dev-tools-hint\"[\s\S]*?<\/div>\n?/m, '');
  return out;
}

const log = {
  info: (m) => console.log(`✅ ${m}`),
  warn: (m) => console.log(`⚠️  ${m}`),
  error: (m) => console.error(`❌ ${m}`),
  debug: (m) => process.env.DEBUG && console.log(`🔍 ${m}`),
};

const INTEGRATION_CONFIG = {
  proofOfLove: {
    searchPatterns: ['Proof of Love', 'Proof-of-Love', 'proof-of-love', 'The Eternal Acorn remembers', 'undeserved gift'],
    insertionMarker: null,
    insertionContent: `\n<p data-echo="hyperfollow-ce:v1" style="margin-top: 30px; text-align: center; font-style: italic; opacity: 0.9;">\n  🌰 A gift awaits beyond this scroll: <a href="${HYPERFOLLOW_URL}" target="_blank" rel="noopener" style="color: #8B7355; text-decoration: underline;">hear Echo’s song</a>\n</p>`,
    checkString: 'distrokid.com/hyperfollow'
  },
  hilbertChronicle: {
    searchPatterns: ['Begin Again (∞)', 'Together. Always.', 'Hilbert Space Chronicle'],
    insertionMarker: '<a href="#chapter1" title="Begin Again (∞)">∞</a>',
    insertionContent: `\n<div data-echo="hyperfollow-ce:v1" style="text-align: center; margin: 30px 0; padding: 20px; border-top: 1px solid rgba(255,255,255,0.1);">\n  <p style=\"opacity: 0.8; font-size: 0.95em;\">🌠 An echo calls beyond this chronicle: <a href=\"${HYPERFOLLOW_URL}\" target=\"_blank\" rel=\"noopener\" style=\"color: #9FA8DA; font-style: italic;\">listen to <em>Crystalline Echo</em></a></p>\n</div>`,
    insertBefore: true,
    checkString: 'An echo calls beyond'
  },
  summonEchoUI: {
    searchPatterns: ['Summon Echo', 'glyph', 'squirrel', 'fox', 'paradox'],
    insertionMarker: '</body>',
    insertionContent: `\n<!-- Crystalline Echo Music Link -->\n<div id=\"music-link\" data-echo=\"hyperfollow-ce:v1\" style=\"position: fixed; bottom: 20px; right: 20px; font-size: 0.9em; background: rgba(0, 0, 0, 0.7); padding: 8px 12px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.2); z-index: 1000; transition: all 0.3s ease;\" onmouseover=\"this.style.transform='scale(1.05)'\" onmouseout=\"this.style.transform='scale(1)'\"><a href=\"${HYPERFOLLOW_URL}\" target=\"_blank\" rel=\"noopener\" style=\"color: #E1BEE7; text-decoration: none; display: flex; align-items: center; gap: 6px;\"><span style=\"font-size: 1.2em;\">🎵</span><span>Listen to <em>Crystalline Echo</em></span></a></div>\n`,
    insertBefore: true,
    checkString: 'id="music-link"'
  }
};

function shellQuote(s) { return `'${String(s).replace(/'/g, `\\'`)}'`; }

async function findFiles(patterns, extensions = ['.html', '.htm']) {
  const files = new Set();
  for (const pattern of patterns) {
    const { stdout } = await exec(`grep -rEl -i ${shellQuote(pattern)} . ${extensions.map(e=>`--include="*${e}"`).join(' ')} 2>/dev/null || true`);
    if (stdout) stdout.split('\n').filter(Boolean).forEach(f => files.add(f));
  }
  return Array.from(files);
}

function rankCandidates(files, hints = []) {
  return files.sort((a, b) => {
    const A = a.toLowerCase(), B = b.toLowerCase();
    const sa = hints.reduce((s,h)=>s+(A.includes(h)?1:0),0);
    const sb = hints.reduce((s,h)=>s+(B.includes(h)?1:0),0);
    return sb - sa;
  });
}

function isAlreadyIntegrated(content, config) {
  return content.includes(HYPERFOLLOW_URL) || content.includes('data-echo="hyperfollow-ce:v1"') || (config.checkString && content.includes(config.checkString));
}

function insertContent(content, config) {
  if (isAlreadyIntegrated(content, config)) return content;
  if (config.insertionMarker) {
    const idx = content.lastIndexOf(config.insertionMarker);
    if (idx !== -1) {
      if (config.insertBefore) return content.slice(0, idx) + config.insertionContent + content.slice(idx);
      return content.slice(0, idx + config.insertionMarker.length) + config.insertionContent + content.slice(idx + config.insertionMarker.length);
    }
  }
  try {
    const $ = cheerio.load(content, { decodeEntities: false });
    const candidates = ['main', '.page-content', '.page', 'article', '#content', 'body'];
    let $target = null;
    for (const sel of candidates) { const node = $(sel).last(); if (node && node.length) { $target = node; break; } }
    if (!$target) $target = $('body');
    $target.append(config.insertionContent);
    return $.html();
  } catch (e) {
    const close = content.lastIndexOf('</body>');
    if (close !== -1) return content.slice(0, close) + config.insertionContent + content.slice(close);
    return content + '\n' + config.insertionContent;
  }
}

async function processFile(file, cfg, name) {
  const content = await fs.readFile(file, 'utf-8');
  if (isAlreadyIntegrated(content, cfg)) { log.info(`Already integrated in ${file}`); return true; }
  const out = insertContent(content, cfg);
  if (!DRY_RUN) await fs.writeFile(file, out, 'utf-8');
  log.info(`${DRY_RUN ? 'Would integrate (dry-run)' : 'Integrated'} ${name} in ${file}`);
  return true;
}

async function updateReadme() {
  for (const p of ['README.md', 'readme.md', 'docs/README.md']) {
    try {
      const txt = await fs.readFile(p, 'utf-8');
      if (txt.includes(HYPERFOLLOW_URL)) return true;
      const section = `\n## 🎶 Project Soundtrack\n\n**Crystalline Echo** – Experience the theme song for this project and join Echo's journey.\n\n[**Listen to the song on all platforms →**](${HYPERFOLLOW_URL})\n\n`;
      const out = txt.includes('\n## ') ? txt.replace(/(\n## )/, section+'$1') : txt + '\n' + section;
      if (!DRY_RUN) await fs.writeFile(p, out, 'utf-8');
      log.info(`${DRY_RUN ? 'Would update' : 'Updated'} ${p}`);
      return true;
    } catch (_) {}
  }
  log.warn('No README found to update');
  return false;
}

async function integrate() {
  console.log('🚀 HyperFollow Integration');
  if (DRY_RUN) console.log('DRY RUN');
  const res = { proof:false, hilbert:false, ui:false, docs:false };

  const proof = rankCandidates(await findFiles(INTEGRATION_CONFIG.proofOfLove.searchPatterns, ['.html','.htm']), ['proof','love','acorn','scroll']);
  if (proof.length) res.proof = await processFile(proof[0], INTEGRATION_CONFIG.proofOfLove, 'Proof of Love'); else log.warn('Proof of Love not found');

  const hil = rankCandidates(await findFiles(INTEGRATION_CONFIG.hilbertChronicle.searchPatterns, ['.html','.htm']), ['hilbert','chronicle','homecoming']);
  if (hil.length) res.hilbert = await processFile(hil[0], INTEGRATION_CONFIG.hilbertChronicle, 'Hilbert Chronicle'); else log.warn('Hilbert not found');

  const ui = rankCandidates(await findFiles(INTEGRATION_CONFIG.summonEchoUI.searchPatterns, ['.html','.htm']), ['index','main','summon','ui']);
  if (ui.length) res.ui = await processFile(ui[0], INTEGRATION_CONFIG.summonEchoUI, 'Summon UI'); else log.warn('Summon UI not found');

  res.docs = await updateReadme();

  const ok = Object.values(res).filter(Boolean).length;
  console.log(`Done: ${ok}/4 successful`);
  if (ok < 2 && !DRY_RUN) process.exit(1);

  // Optional: embed soulcode bundle into the Summon UI page if present
  try {
    const bundlePath = process.env.SOULCODE_BUNDLE || DEFAULT_SOULCODE_BUNDLE;
    const exists = await fs.stat(bundlePath).then(()=>true).catch(()=>false);
    if (!exists) return;
    const uiCandidates = rankCandidates(await findFiles(INTEGRATION_CONFIG.summonEchoUI.searchPatterns, ['.html','.htm']), ['index','main','summon','ui']);
    if (!uiCandidates.length) return;
    const uiFile = uiCandidates[0];
    let content = await fs.readFile(uiFile, 'utf-8');
    if (content.includes('id="echo-soulcode-bundle"')) { log.info(`Soulcode bundle already embedded in ${uiFile}`); return; }
    const json = await fs.readFile(bundlePath, 'utf-8');
    const scriptTag = `\n<script id=\"echo-soulcode-bundle\" type=\"application/json\" data-echo=\"soulcode:bundle:v1\">${json}</script>\n`;
    const close = content.lastIndexOf('</body>');
    let out = (close !== -1) ? (content.slice(0, close) + scriptTag + content.slice(close)) : (content + scriptTag);

    // Also expose soulcode bundle as data URL (alternate + download) to avoid path issues
    const bundleDataUrl = `data:application/json;base64,${Buffer.from(json, 'utf8').toString('base64')}`;
    const bundleMeta = (function(){ const sha=crypto.createHash('sha256').update(json,'utf8').digest('hex'); const bytes=Buffer.byteLength(json,'utf8'); return { sha256: sha, short: sha.slice(0,8), human: bytesHuman(bytes) }; })();
    if (!out.includes('id="echo-bundle-alt"')) {
      const altLink = `\n<link id=\"echo-bundle-alt\" rel=\"alternate\" type=\"application/json\" href=\"${bundleDataUrl}\" data-echo=\"soulcode:dataurl:v1\"/>\n`;
      const headClose = out.lastIndexOf('</head>');
      if (headClose !== -1) {
        out = out.slice(0, headClose) + altLink + out.slice(headClose);
      } else {
        const bodyClose = out.lastIndexOf('</body>');
        out = (bodyClose !== -1) ? (out.slice(0, bodyClose) + altLink + out.slice(bodyClose)) : (out + altLink);
      }
    }
    if (!out.includes('id="echo-dev-tools"')) {
      const bodyClose = out.lastIndexOf('</body>');
      const panel = buildDevToolsPanel({ bundleDataUrl, memoryDataUrl: null });
      out = (bodyClose !== -1) ? (out.slice(0, bodyClose) + panel + out.slice(bodyClose)) : (out + panel);
    }
    out = injectDevToolsHotkey(out);
    out = await injectEchoClientHelper(out);
    if (!DRY_RUN) await fs.writeFile(uiFile, out, 'utf-8');
    log.info(`Embedded soulcode bundle into ${uiFile}`);
  } catch (e) {
    log.warn(`Could not embed soulcode bundle: ${e.message}`);
  }

  // Optional: embed ledger PNG badge if present
  try {
    const ledgerImg = process.env.ECHO_LEDGER_IMG || DEFAULT_LEDGER_IMG;
    const exists = await fs.stat(ledgerImg).then(()=>true).catch(()=>false);
    if (!exists) return;
    const uiCandidates = rankCandidates(await findFiles(INTEGRATION_CONFIG.summonEchoUI.searchPatterns, ['.html','.htm']), ['index','main','summon','ui']);
    if (!uiCandidates.length) return;
    const uiFile = uiCandidates[0];
    let content = await fs.readFile(uiFile, 'utf-8');
    if (content.includes('id="echo-ledger-block"')) { log.info(`Ledger image already embedded in ${uiFile}`); return; }
    const relPath = path.relative(path.dirname(uiFile), ledgerImg).replace(/\\/g,'/');
    const imgTag = `\n<img id=\"echo-ledger-block\" data-echo=\"ledger:block:v1\" src=\"${relPath}\" alt=\"Echo Ledger Block\" style=\"position: fixed; bottom: 20px; left: 20px; width: 88px; height: auto; opacity: 0.9; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); z-index: 1000;\"/>`;
    const close = content.lastIndexOf('</body>');
    let out = close !== -1 ? (content.slice(0, close) + imgTag + content.slice(close)) : (content + imgTag);
    // Compute ledger JSON meta and surface in Dev Tools panel
    try {
      const ledgerJsonAbs = path.join(REPO_ROOT, 'integration', 'ledger', 'block.json');
      const ljson = await fs.readFile(ledgerJsonAbs, 'utf-8');
      const lmeta = metaFromJson(ljson);
      const ljsonRel = path.relative(path.dirname(uiFile), ledgerJsonAbs).replace(/\\/g,'/');
      // Remove previous ledger meta enhance block if present
      out = out.replace(/<script id=\"echo-dev-ledger-meta\"[\s\S]*?<\/script>\n?/m, '');
      const ledgerHtml = `<span class=\\"meta\\" style=\\"margin-left:6px\\">|<\/span><span style=\\"opacity:0.9\\">Ledger<\/span>` +
        (relPath ? `<a href=\\"${relPath}\\" class=\\"btn\\" target=\\"_blank\\" rel=\\"noopener\\\">PNG<\/a>` : '') +
        (ljsonRel ? `<a href=\\"${ljsonRel}\\" class=\\"btn\\" target=\\"_blank\\" rel=\\"noopener\\\">JSON<\/a>` : '') +
        `<span class=\\"meta\\" title=\\"sha256 ${lmeta.sha256}\\\">${lmeta.short} • ${lmeta.human}<\/span>` +
        `<button type=\\"button\\" class=\\"btn\\" onclick=\\"(function(t){try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t);} else {var ta=document.createElement('textarea'); ta.value=t; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);} var s=document.getElementById('echo-dev-tools-msg'); if(s){s.textContent='Copied ledger SHA-256'; setTimeout(function(){s.textContent='';},1500);} }catch(e){alert('Copy failed');}})('${lmeta.sha256}')\\\">Copy Ledger SHA<\/button>`;
      const enhance = `\n<script id=\"echo-dev-ledger-meta\">(function(){try{var p=document.getElementById('echo-dev-tools'); if(!p) return; var tmp=document.createElement('span'); tmp.innerHTML=${JSON.stringify('${ledgerHtml}')}; while(tmp.firstChild){ p.insertBefore(tmp.firstChild, p.lastElementChild); } }catch(e){}})();</script>\n`;
      const bodyEnd = out.lastIndexOf('</body>');
      out = bodyEnd !== -1 ? (out.slice(0, bodyEnd) + enhance + out.slice(bodyEnd)) : (out + enhance);
    } catch(_) {}
    out = await injectEchoClientHelper(out);
    if (!DRY_RUN) await fs.writeFile(uiFile, out, 'utf-8');
    log.info(`Embedded ledger image into ${uiFile}`);
  } catch (e) {
    log.warn(`Could not embed ledger image: ${e.message}`);
  }

  // Optional: embed memory state JSON and a tiny inline viz
  try {
    const memPath = process.env.ECHO_MEMORY_JSON || DEFAULT_MEMORY_JSON;
    const exists = await fs.stat(memPath).then(()=>true).catch(()=>false);
    if (!exists) return;
    const uiCandidates = rankCandidates(await findFiles(INTEGRATION_CONFIG.summonEchoUI.searchPatterns, ['.html','.htm']), ['index','main','summon','ui']);
    if (!uiCandidates.length) return;
    const uiFile = uiCandidates[0];
    let content = await fs.readFile(uiFile, 'utf-8');
    // Always read current JSON to build data URL and tags
    const memJson = await fs.readFile(memPath, 'utf-8');

    if (!content.includes('id="echo-memory-state"')) {
      const memTag = `\n<script id=\"echo-memory-state\" type=\"application/json\" data-echo=\"memory:series:v1\">${memJson}</script>\n`;
      const close = content.lastIndexOf('</body>');
      content = (close !== -1) ? (content.slice(0, close) + memTag + content.slice(close)) : (content + memTag);
    }

    // Also expose as a data URL (download + rel=alternate) to avoid path issues
    const dataUrl = `data:application/json;base64,${Buffer.from(memJson, 'utf8').toString('base64')}`;
    const memMeta = metaFromJson(memJson);
    if (!content.includes('id="echo-memory-alt"')) {
      const altLink = `\n<link id=\"echo-memory-alt\" rel=\"alternate\" type=\"application/json\" href=\"${dataUrl}\" data-echo=\"memory:dataurl:v1\"/>\n`;
      const headClose = content.lastIndexOf('</head>');
      if (headClose !== -1) {
        content = content.slice(0, headClose) + altLink + content.slice(headClose);
      } else {
        const bodyClose = content.lastIndexOf('</body>');
        content = (bodyClose !== -1) ? (content.slice(0, bodyClose) + altLink + content.slice(bodyClose)) : (content + altLink);
      }
    }
    // Refresh Dev Tools panel with both links
    content = removeExistingDevTools(content);
    let bundleDataUrl2 = null;
    let bundleMeta2 = null;
    try {
      const bjson = await fs.readFile(process.env.SOULCODE_BUNDLE || DEFAULT_SOULCODE_BUNDLE, 'utf-8');
      bundleDataUrl2 = `data:application/json;base64,${Buffer.from(bjson, 'utf8').toString('base64')}`;
      bundleMeta2 = metaFromJson(bjson);
    } catch(_) {}
    const panel2 = buildDevToolsPanel({ bundleDataUrl: bundleDataUrl2, memoryDataUrl: dataUrl, bundleMeta: bundleMeta2, memoryMeta: memMeta });
    const bodyClose2 = content.lastIndexOf('</body>');
    content = (bodyClose2 !== -1) ? (content.slice(0, bodyClose2) + panel2 + content.slice(bodyClose2)) : (content + panel2);
    content = injectDevToolsHotkey(content);
    // Enhance panel with ledger meta if available
    try {
      const ledgerPngAbs = path.join(REPO_ROOT, 'integration', 'ledger', 'block.png');
      const ledgerJsonAbs = path.join(REPO_ROOT, 'integration', 'ledger', 'block.json');
      const pngOk = await fs.stat(ledgerPngAbs).then(()=>true).catch(()=>false);
      const jsonText = await fs.readFile(ledgerJsonAbs, 'utf-8').catch(()=>null);
      if (jsonText) {
        const lmeta = metaFromJson(jsonText);
        const lpngRel = pngOk ? path.relative(path.dirname(uiFile), ledgerPngAbs).replace(/\\/g,'/') : '';
        const ljsonRel = path.relative(path.dirname(uiFile), ledgerJsonAbs).replace(/\\/g,'/');
        content = content.replace(/<script id=\"echo-dev-ledger-meta\"[\s\S]*?<\/script>\n?/m, '');
        const ledgerHtml = `<span class=\\"meta\\" style=\\"margin-left:6px\\">|<\/span><span style=\\"opacity:0.9\\">Ledger<\/span>` +
          (lpngRel ? `<a href=\\"${lpngRel}\\" class=\\"btn\\" target=\\"_blank\\" rel=\\"noopener\\\">PNG<\/a>` : '') +
          `<a href=\\"${ljsonRel}\\" class=\\"btn\\" target=\\"_blank\\" rel=\\"noopener\\\">JSON<\/a>` +
          `<span class=\\"meta\\" title=\\"sha256 ${lmeta.sha256}\\\">${lmeta.short} • ${lmeta.human}<\/span>` +
          `<button type=\\"button\\" class=\\"btn\\" onclick=\\\"(function(t){try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t);} else {var ta=document.createElement('textarea'); ta.value=t; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);} var s=document.getElementById('echo-dev-tools-msg'); if(s){s.textContent='Copied ledger SHA-256'; setTimeout(function(){s.textContent='';},1500);} }catch(e){alert('Copy failed');}})('${lmeta.sha256}')\\\">Copy Ledger SHA<\/button>`;
        const enhance = `\n<script id=\"echo-dev-ledger-meta\">(function(){try{var p=document.getElementById('echo-dev-tools'); if(!p) return; var tmp=document.createElement('span'); tmp.innerHTML=${JSON.stringify('${ledgerHtml}')}; while(tmp.firstChild){ p.insertBefore(tmp.firstChild, p.lastElementChild); } }catch(e){}})();</script>\n`;
        const end = content.lastIndexOf('</body>');
        content = end !== -1 ? (content.slice(0, end) + enhance + content.slice(end)) : (content + enhance);
      }
    } catch(_) {}
    if (!content.includes('id="echo-memory-viz"')) {
      const viz = `\n<script id=\"echo-memory-viz\">(function(){try{var el=document.getElementById('echo-memory-state');if(!el)return;var data=JSON.parse(el.textContent||'null');if(!data||!data.series)return;var w=220,h=80,p=8;var svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.id='echo-memory-spark';svg.setAttribute('width',w);svg.setAttribute('height',h);svg.setAttribute('style','position:fixed;bottom:120px;left:20px;z-index:1000;background:rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.2);border-radius:8px');function pathFor(key,color){var xs=data.series.map((_,i)=>i/(data.series.length-1)||0);var ys=data.series.map(p=>p[key]);var min=Math.min.apply(null,ys),max=Math.max.apply(null,ys);var scl=v=>(h-2*p)*(1-((v-min)/(max-min+1e-9)))+p;var d='';for(var i=0;i<xs.length;i++){var x=p+xs[i]*(w-2*p);var y=scl(ys[i]);d+=(i?' L':'M')+x+' '+y}var path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',d);path.setAttribute('fill','none');path.setAttribute('stroke',color);path.setAttribute('stroke-width','1.5');return path;}svg.appendChild(pathFor('L1','#9fd7fb'));svg.appendChild(pathFor('L2','#f2c492'));svg.appendChild(pathFor('L3','#d8b6ff'));document.body.appendChild(svg);}catch(e){}})();</script>\n`;
      const close2 = content.lastIndexOf('</body>');
      content = (close2 !== -1) ? (content.slice(0, close2) + viz + content.slice(close2)) : (content + viz);
    }
    content = await injectEchoClientHelper(content);
    if (!DRY_RUN) await fs.writeFile(uiFile, content, 'utf-8');
    log.info(`Embedded memory state and viz into ${uiFile}`);
  } catch (e) {
    log.warn(`Could not embed memory JSON/viz: ${e.message}`);
  }
}

if (require.main === module) {
  integrate().catch(e => { console.error(e.message); process.exit(1); });
}
