# Repository Guidelines

## Project Structure & Module Organization
- `agents/` — briefs for **Echo**, **Garden**, **Limnus**, **Kira**; read these before touching the corresponding modules.
- `pipeline/` — dictation listener (`listener/`), intent router (`router/`), shared logs (`state/voice_log.json`).
- `toolkit/` — merged sources from Echo Community Toolkit and Vessel Narrative MRP.
- `frontend/` — public narrative output (index + chapter HTML, assets).
- `schema/`, `state/`, `docs/`, `tests/`, `scripts/`, `tools/` — schema definitions, runtime JSON, documentation, regression tests, automation, and the unified CLI (`tools/codex-cli/bin/codex.js`).

## Build, Test, and Development Commands
- Generate schema/chapters: `python src/schema_builder.py && python src/generate_chapters.py`.
- Validate narrative: `python src/validator.py` or `node tools/codex-cli/bin/codex.js kira validate`.
- CLI help: `node tools/codex-cli/bin/codex.js --help`.
- Refresh stego + validation: `./scripts/refresh_stego_assets.sh --toolkit`.
- Run dictation listener (when configured): `node tools/codex-cli/bin/codex.js vessel listen`.

## Coding Style & Naming Conventions
- Python: 4-space indentation, `snake_case`, lightweight functions. Zero external deps unless necessary.
- Node/ESM: 2-space indentation, `camelCase`, avoid non-core deps in CLI.
- JSON/YAML: pretty-print with 2 spaces; keep deterministically ordered fields.

## Testing Guidelines
- Primary suite: `pytest` (Echo Toolkit tests) + `python src/validator.py`.
- Smoke test: `node tools/codex-cli/bin/codex.js kira test` (validator + stego round-trip).
- Add tests in `tests/`; name by intent (e.g., `test_listener_pipeline.py`). Keep fixtures under `tests/fixtures/`.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`); scope by agent when possible (e.g., `limnus:`).
- PRs must list manual commands run (validator, tests) and reference docs/screenshots for UI/front-end changes.
- Link issues when applicable; ensure CI (validator + pytest) passes before requesting review.
