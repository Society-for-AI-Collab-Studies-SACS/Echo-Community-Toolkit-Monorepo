# Changelog

## [1.2.0-alpha] – 2025-10-16

### Added
- **FAISS backbone (optional):** `KIRA_VECTOR_BACKEND=faiss` enables fast cosine recall over SBERT vectors; falls back to NumPy if FAISS unavailable. Index persisted to `state/limnus.faiss` + meta.
- **Release workflow:** tag-based `release.yml` builds UI, packages assets (dist tarball, optional VSIX), assembles changelog, and creates a GitHub Release.
- **LambdaStateViewer panels:** new **Bundle** and **Memory** panels plus a typed telemetry bus for future instrumentation.

### Changed
- **Kira publish:** supports `--release`, `--notes-file`, and `--asset` options (via CLI invocation mapping), attaching artifacts (e.g., `ledger_export.json`) to releases.

### Docs
- Phase 2 roadmap, performance notes, and Discussions template added.
