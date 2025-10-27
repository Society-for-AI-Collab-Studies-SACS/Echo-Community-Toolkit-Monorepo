# Repository Guidelines

## Project Structure & Module Organization
- `src/` Python modules (LSB1 encoder/decoder, MRP Phase‑A).
- `tests/` Pytest suite mirroring `src/` (e.g., `tests/test_lsb.py`).
- `assets/` Images and data (e.g., `assets/images/echo_key.png`, `assets/data/LSB1_Mantra.txt`).
- `artifacts/` Generated MRP payloads and reports.
- `lambda-vite/` UI demo and MRP seed package (Node/Vite; `src/*.tsx`).
- `tools/`, `web/`, `types/` Integration helpers and client assets.
- `docs/` Contributor docs (see `docs/ARCHITECTURE_INDEX.md`).
- `archive/` Historical drops (read‑only; excluded from tests).

## Build, Test, and Development Commands
- Python tests: `python3 -m pytest` (uses `pytest.ini`, `PYTHONPATH=src`).
- Full validation: `python3 final_validation.py` (rebuilds golden sample, verifies MRP).
- UI (lambda‑vite): `cd lambda-vite && npm ci && npm run build`.
- Hyperfollow integration: `node hyperfollow-integration.js --dry-run` then `node verify-integration.js`.
- Bloom workflow: `./bloom.py inhale` • `./bloom.py hold --report-json` • `./bloom.py exhale --docker` • `./bloom.py release --cleanup`.

## Coding Style & Naming Conventions
- Python: 4‑space indent, `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE` constants.
- JS/TS: 2‑space indent, `camelCase`; keep CLI filenames kebab‑case.
- Use Black/isort and Prettier/ESLint if configured; prefer small, focused diffs.

## Testing Guidelines
- Framework: Pytest (see `pytest.ini` → `testpaths=tests`, `norecursedirs=archive`).
- Naming: `tests/test_<module>.py`; assertions only (no `return True`).
- Artifacts: tests may read `assets/` and `artifacts/`; do not mutate `archive/`.

## Commit & Pull Request Guidelines
- Conventional Commits (e.g., `feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- PRs include: clear description, linked issues, and screenshots for UI/HTML changes.
- Update docs when structure/tooling changes (e.g., `docs/ARCHITECTURE_INDEX.md`).

## Security & Agent Tips
- Never commit secrets; keep local env files out of VCS.
- Avoid committing large binaries or `dist/` outputs unless intentional.
- Treat `archive/` as historical reference; do not import from it in new code.
- Before merging, run `python3 final_validation.py` to ensure end‑to‑end integrity.
