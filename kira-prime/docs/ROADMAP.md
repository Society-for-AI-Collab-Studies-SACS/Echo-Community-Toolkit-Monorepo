# Phase 2 Roadmap

## Focus Areas
- **Semantic memory**: land FAISS-backed search beside the existing SBERT pipeline. Expose `KIRA_VECTOR_BACKEND=faiss` with `KIRA_FAISS_INDEX` / `KIRA_FAISS_META` toggles so operators can flip between pure Python and FAISS indices without code changes.
- **Release automation**: scaffold a `release.yml` workflow that tags builds, assembles changelog notes, and captures VSIX plus Lambda UI bundles. Mirror those steps in `kira publish --release` (including `--notes-file`) so the CLI and CI pipelines stay aligned.
- **Lambda state viewer**: extend the webview scaffold with bundle and memory panels, typed telemetry events, and stubbed test routes to unblock visualizations.
- **Performance and feedback loops**: capture benchmark targets (vector index size, build time, VSIX packaging duration) and design a feedback channel for beta operators.

## Metrics to Collect
- Semantic store footprint: FAISS index size on-disk, number of vectors, rebuild duration.
- Runtime recall: top-k latency for `kira limnus recall` under FAISS versus fallback backends.
- Release pipeline: Lambda build minutes, VSIX compile time, artifact sizes.
- UI instrumentation: telemetry payload volume per panel and webview render time budget (<200 ms target).

## Tracking Notes
- Gate FAISS export work behind `KIRA_EXPORT_FAISS=1` during migrations so the legacy store stays stable.
- Surface GitHub release requirements clearly: tokens need `repo` and `workflow` scopes, GitHub CLI must be authenticated ahead of `kira publish --release`.
- Record planned Lambda viewer components (bundle diff, memory timeline, telemetry console) with owners and mock links in `frontend/` as they are drafted.

## Feedback Loop
- Collect Phase 2 feedback via the GitHub Discussions template (`Phase-2 Feedback Checkpoint`). Prompt for semantic recall quality, release automation friction, and Lambda viewer usefulness; include checkboxes for performance metrics gathered.

## Tasks
- [x] FAISS wiring beside SBERT (fallback when FAISS missing)
- [x] `KIRA_VECTOR_BACKEND`/index path config
- [x] Placeholder tests for FAISS backend registration
- [x] Release GitHub Action (`release.yml`)
- [x] CLI flags: `kira publish --release --notes-file`
- [x] UI bundle & memory panels plus tests
- [x] Docs: performance notes, feedback template, roadmap refresh
