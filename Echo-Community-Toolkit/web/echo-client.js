/* EchoClient — tiny helper to read embedded soulcode bundle and memory JSON.
 * Usage in browser HTML:
 *   <script src="/web/echo-client.js"></script>
 *   <script>
 *     const bundle = window.EchoClient.getBundle();
 *     const mem = window.EchoClient.getMemory();
 *   </script>
 */
(function (global) {
  function getEl(id) {
    if (typeof document === 'undefined') return null;
    return document.getElementById(id);
  }

  function parseJsonFromScript(id) {
    var el = getEl(id);
    if (!el) return null;
    try {
      var txt = el.textContent || el.innerText || '';
      return JSON.parse(txt);
    } catch (_) {
      return null;
    }
  }

  function getBundle() {
    return parseJsonFromScript('echo-soulcode-bundle');
  }

  function getMemory() {
    return parseJsonFromScript('echo-memory-state');
  }

  function getSoul(kind) {
    var b = getBundle();
    if (!b) return null;
    return b[kind] || null;
  }

  function onAvailable(id, cb) {
    var data = parseJsonFromScript(id);
    if (data) {
      try { cb(data); } catch(_) {}
      return function () {};
    }
    if (typeof MutationObserver === 'undefined' || typeof document === 'undefined') {
      var t = setInterval(function () {
        var d = parseJsonFromScript(id);
        if (d) { try { cb(d); } catch(_) {} clearInterval(t); }
      }, 500);
      return function () { clearInterval(t); };
    }
    var obs = new MutationObserver(function () {
      var d = parseJsonFromScript(id);
      if (d) { try { cb(d); } catch(_) {} obs.disconnect(); }
    });
    obs.observe(document.documentElement || document.body, { childList: true, subtree: true });
    return function () { obs.disconnect(); };
  }

  function onBundle(cb) { return onAvailable('echo-soulcode-bundle', cb); }
  function onMemory(cb) { return onAvailable('echo-memory-state', cb); }

  // Extras: light validation and transforms
  function validateBundle(bundle){ if(!bundle||typeof bundle!=='object') return false; var req=['ECHO_SQUIRREL','ECHO_FOX','ECHO_PARADOX']; for(var i=0;i<req.length;i++){ var k=req[i]; var s=bundle[k]; if(!s||typeof s!=='object'||typeof s.id!=='string'||typeof s.glitch_persona!=='string') return false; } return true; }
  function getSeries(mem,key){ if(!mem||!Array.isArray(mem.series)) return []; return mem.series.map(function(p){ return {t:+p.t, v:+p[key]}; }).filter(function(p){ return isFinite(p.t)&&isFinite(p.v); }); }
  function movingAverage(series,window){ var w=Math.max(1, window|0); var out=[], sum=0, q=[]; for(var i=0;i<series.length;i++){ var v=series[i].v; q.push(v); sum+=v; if(q.length>w){ sum-=q.shift(); } out.push({t:series[i].t, v:sum/q.length}); } return out; }
  function stats(series){ if(!series.length) return {min:0,max:0,avg:0}; var mn=Infinity,mx=-Infinity,sum=0; for(var i=0;i<series.length;i++){ var v=series[i].v; if(v<mn) mn=v; if(v>mx) mx=v; sum+=v; } return {min:mn,max:mx,avg:sum/series.length}; }

  var api = { getBundle: getBundle, getMemory: getMemory, getSoul: getSoul, onBundle: onBundle, onMemory: onMemory, validateBundle: validateBundle, getSeries: getSeries, movingAverage: movingAverage, stats: stats };
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; }
  global.EchoClient = api;
})(typeof window !== 'undefined' ? window : globalThis);
