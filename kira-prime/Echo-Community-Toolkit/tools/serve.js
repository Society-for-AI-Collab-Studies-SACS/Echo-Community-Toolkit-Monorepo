#!/usr/bin/env node
/* Simple static file server for local testing.
 * Usage:
 *   node tools/serve.js --port 8080 --dir .
 *   PORT=8080 node tools/serve.js
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
function argVal(flags, def) {
  for (let i = 0; i < args.length; i++) {
    if (flags.includes(args[i])) return args[i + 1];
  }
  return def;
}

const PORT = parseInt(process.env.PORT || argVal(['-p', '--port'], '8080'), 10);
const ROOT = path.resolve(argVal(['-d', '--dir'], '.'));

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.wav': 'audio/wav',
};

function safeJoin(root, reqPath) {
  const seg = decodeURIComponent(reqPath.split('?')[0]).split('#')[0];
  const p = path.normalize(path.join(root, seg));
  if (!p.startsWith(root)) return null; // prevent path traversal
  return p;
}

const server = http.createServer((req, res) => {
  const urlPath = req.url || '/';
  let filePath = safeJoin(ROOT, urlPath);
  if (!filePath) {
    res.statusCode = 400;
    res.end('Bad Request');
    return;
  }
  fs.stat(filePath, (err, stat) => {
    if (err) {
      res.statusCode = 404;
      res.end('Not Found');
      return;
    }
    if (stat.isDirectory()) {
      const indexPath = path.join(filePath, 'index.html');
      fs.stat(indexPath, (e2, st2) => {
        if (!e2 && st2.isFile()) return streamFile(indexPath, res);
        res.statusCode = 403;
        res.setHeader('Content-Type', 'text/plain; charset=utf-8');
        res.end('Directory listing not allowed');
      });
    } else {
      streamFile(filePath, res);
    }
  });
});

function streamFile(p, res) {
  const ext = path.extname(p).toLowerCase();
  const type = MIME[ext] || 'application/octet-stream';
  res.statusCode = 200;
  res.setHeader('Content-Type', type);
  const stream = fs.createReadStream(p);
  stream.on('error', () => {
    res.statusCode = 500;
    res.end('Internal Server Error');
  });
  stream.pipe(res);
}

server.listen(PORT, () => {
  console.log(`Static server listening on http://localhost:${PORT}`);
  console.log(`Serving directory: ${ROOT}`);
  console.log('Try: /web/examples/echo-client-demo.html');
});

