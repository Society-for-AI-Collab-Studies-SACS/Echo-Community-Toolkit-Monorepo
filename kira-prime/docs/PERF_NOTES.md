# Performance & Optimization Notes

Collect for each build on Linux:
- **Vector index**
  - Memory count (N) and embedding dimension (d, default 384)
  - FAISS index size on disk (bytes)
  - Reindex time (s)
  - Mean recall latency (ms) at k=5 for representative queries
- **UI build**
  - `lambda-vite` `npm run build` total time (s)
  - `dist/` bundle size (KB)
- **CLI throughput**
  - `vesselos limnus recall` median latency (ms) across 100 queries
  - Logger I/O health (structured JSON + concise human logs)

Record measurements under `reports/perf/YYYYMMDD-<commit>.json` to track trends.
