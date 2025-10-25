// ESM wrapper for EchoClient helper.
// Usage:
//   import EchoClient from '/web/echo-client.module.js';
//   const bundle = EchoClient.getBundle();

function getEl(id){ if(typeof document==='undefined') return null; return document.getElementById(id); }
function parseJsonFromScript(id){ const el=getEl(id); if(!el) return null; try{ return JSON.parse(el.textContent||el.innerText||''); }catch(_){ return null; } }
function getBundle(){ return parseJsonFromScript('echo-soulcode-bundle'); }
function getMemory(){ return parseJsonFromScript('echo-memory-state'); }
function getSoul(kind){ const b=getBundle(); return b? (b[kind]||null):null; }
function onAvailable(id,cb){ const d=parseJsonFromScript(id); if(d){ try{cb(d);}catch(_){ } return ()=>{}; } if(typeof MutationObserver==='undefined'||typeof document==='undefined'){ const t=setInterval(()=>{ const d2=parseJsonFromScript(id); if(d2){ try{cb(d2);}catch(_){ } clearInterval(t);} },500); return ()=>clearInterval(t);} const obs=new MutationObserver(()=>{ const d3=parseJsonFromScript(id); if(d3){ try{cb(d3);}catch(_){ } obs.disconnect(); }}); obs.observe(document.documentElement||document.body,{childList:true,subtree:true}); return ()=>obs.disconnect(); }
function onBundle(cb){ return onAvailable('echo-soulcode-bundle',cb); }
function onMemory(cb){ return onAvailable('echo-memory-state',cb); }

// Extras: light validation and transforms
function validateBundle(bundle){ if(!bundle||typeof bundle!=='object') return false; const req=['ECHO_SQUIRREL','ECHO_FOX','ECHO_PARADOX']; for(const k of req){ if(!bundle[k]||typeof bundle[k]!=='object') return false; const s=bundle[k]; if(typeof s.id!=='string'||typeof s.glitch_persona!=='string') return false; } return true; }
function getSeries(mem,key){ if(!mem||!Array.isArray(mem.series)) return []; return mem.series.map(p=>({t:+p.t, v:+p[key]})).filter(p=>Number.isFinite(p.t)&&Number.isFinite(p.v)); }
function movingAverage(series,window){ const w=Math.max(1,window|0); const out=[]; let sum=0; const q=[]; for(const p of series){ q.push(p.v); sum+=p.v; if(q.length>w){ sum-=q.shift(); } out.push({t:p.t, v:sum/q.length}); } return out; }
function stats(series){ if(!series.length) return {min:0,max:0,avg:0}; let mn=Infinity,mx=-Infinity,sum=0; for(const p of series){ if(p.v<mn) mn=p.v; if(p.v>mx) mx=p.v; sum+=p.v; } return {min:mn,max:mx,avg:sum/series.length}; }

export const EchoClient = { getBundle, getMemory, getSoul, onBundle, onMemory, validateBundle, getSeries, movingAverage, stats };
export default EchoClient;

