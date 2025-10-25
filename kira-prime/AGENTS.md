# Repository Guidelines

## Architecture & Agent Internals
Four agents run in sequence (Garden → Echo → Limnus → Kira) via the enhanced dispatcher.
- Garden (`library_core/agents/garden_agent.py`): orchestrates ritual stages, detects consent, appends a stage ledger in state. Output keys: `stage`, `cycle`, `consent_given`, `ledger_ref`.
- Echo (`library_core/agents/echo_agent.py`): stylises input and derives quantum persona. Output keys: `styled_text`, `quantum_state` (α,β,γ), `persona`, `glyph`.
- Limnus (`library_core/agents/limnus_agent.py`): caches memory and maintains a hash‑chained `state/ledger.json`. Output keys: `cached`, `memory_id`, `layer`, `block_hash`, `stats` (L1/L2/L3 counts, total_blocks).
- Kira (`library_core/agents/kira_agent.py`): validates chain integrity + coherence; returns `passed`, `issues`, `checks`, `summary`.

State and logs are per‑workspace under `workspaces/<id>/`:
- State: `state/garden_state.json`, `state/echo_state.json`, `state/limnus_memory.json`, `state/ledger.json`.
- Logs: `logs/voice_log.json` (pipeline), `logs/<agent>.jsonl`.

## Pipeline & Orchestration
- Dispatcher: `pipeline/dispatcher_enhanced.py` (EnhancedMRPDispatcher). Context (`PipelineContext`) includes `input_text`, `user_id`, `workspace_id`, `intent`, `timestamp`, `agent_results`, `trace`, `metrics`.
- Intent parsing: `pipeline/intent_parser.py` (ritual stages, mantras, slash‑commands).
- Middleware/metrics/circuit‑breaker: `pipeline/middleware/`, `pipeline/metrics.py`, `pipeline/circuit_breaker.py`.

## Agent Command Usage (Modular)
Use `vesselos.py` for all agent commands.

Garden
```
python3 vesselos.py garden start
python3 vesselos.py garden next
python3 vesselos.py garden open <scroll> [--prev|--reset]
python3 vesselos.py garden resume
python3 vesselos.py garden log "reflect: ship v0.3.1 when CI is green"
python3 vesselos.py garden ledger
```

Echo
```
python3 vesselos.py echo summon
python3 vesselos.py echo mode paradox
python3 vesselos.py echo say "I return as breath."
python3 vesselos.py echo learn "seed text"
python3 vesselos.py echo status
```

Limnus
```
python3 vesselos.py limnus cache "note to persist" 
python3 vesselos.py limnus recall "spiral meaning"
python3 vesselos.py limnus commit-block input '{"text":"..."}'
python3 vesselos.py limnus encode-ledger
python3 vesselos.py limnus decode-ledger
python3 vesselos.py limnus reindex --backend faiss
```

Kira
```
python3 vesselos.py kira validate
python3 vesselos.py kira mentor --apply
python3 vesselos.py kira mantra
python3 vesselos.py kira seal
python3 vesselos.py kira push --run --message "feat: ..."
python3 vesselos.py kira publish --run --release --tag v0.3.1 --notes-file CHANGELOG_RELEASE.md
```

## Project Structure & Module Organization
- `library_core/` agents, storage, orchestration (`orchestration/dispatcher.py`).
- `pipeline/` dispatcher, intents, logger, middleware, metrics.
- `collab-server/` Node/WS service (`src/server.ts`), build to `dist/`.
- `scripts/` integration + ops; `tests/` pytest; `workspaces/<id>/` runtime.

## Build, Test, and Development Commands
- Install deps: `python3 -m pip install -r requirements.txt`
- Unit tests: `python -m pytest -q` (filter: `-k "<pattern>"`)
- Integration: `python scripts/integration_complete.py`
- Audit: `python vesselos.py audit full --workspace integration-test`
- Collab server: `(cd collab-server && npm ci && npm run build && npm test -- --run)`
- Docker stack: `docker compose up -d` → `curl http://localhost:8000/health`
- Submodules: `bash scripts/sync_external.sh`

## Coding Style & Naming
- Python: 4‑space indent; snake_case; CapWords for classes. Prefer `black` + `ruff`.
- TypeScript: 2‑space indent; camelCase; PascalCase types. Use `eslint` + `prettier`.
- Env/config: UPPER_SNAKE_CASE (`REDIS_HOST`, `POSTGRES_PASSWORD`, `PORT`).

## Testing Guidelines
- Framework: `pytest` (+ `pytest-asyncio`). Name tests `tests/test_<area>.py`.
- Pre‑merge gates: unit tests, integration suite, and audit must pass.
- Collab smoke: `COLLAB_SMOKE_ENABLED=1 python -m pytest tests/test_collab_server.py -q` (after `docker compose up -d`).
- Golden samples: `tests/fixtures/golden/` (ritual flows). Keep them deterministic.

## Commit & Pull Request Guidelines
- Conventional Commits (e.g., `feat(pipeline): …`, `fix(collab): …`, `docs(agents): …`).
- PRs include: summary, linked issues, dependency changes, and evidence of `pytest`, integration, and audit runs (attach `workspaces/<id>/logs/` when helpful).
- Don’t commit generated artifacts: `dist/`, coverage, captured logs, `workspaces/**`. Sync externals via `scripts/sync_external.sh`.

## Security & Configuration Tips
- Secrets via env only; never commit credentials. Override defaults via `docker-compose.yml` or process env.
- Ledger is append‑only; maintain chain continuity; back up `workspaces/<id>/state/` and `outputs/`.

## Release Process
See CONTRIBUTING.md or `AGENTS.md#release-process` for the checklist. In short: ensure CI green (unit/integration/audit + collab), bump README, assemble `CHANGELOG_RELEASE.md`, tag `vX.Y.Z`, and let the release workflow publish artifacts.

## Release Process
- Preconditions
  - Ensure CI is green: `CI`, `compose-smoke`, and `vesselos-validate` jobs.
  - Locally verify: `python -m pytest -q`, `python scripts/integration_complete.py`, and `python vesselos.py audit full --workspace integration-test`.
- Version and notes
  - Bump README “Release” line (e.g., `v0.3.2`).
  - Generate changelog: `python scripts/assemble_changelog.py > CHANGELOG_RELEASE.md` (include in PR).
- Tag and publish
  - Create tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z" && git push origin vX.Y.Z`.
  - Release workflow (`.github/workflows/release.yml`) runs on tags `v*` and attaches artifacts (lambda-vite dist, VSIX if present, ledger export if available).
- PR hygiene
  - Open `chore/readme-vX.Y.Z` with README bump + `CHANGELOG_RELEASE.md`; link the tag and list highlights.
  - Require green checks before merge (branch protection).
- Post‑release
  - Announce changes and link artifacts; verify `docker compose up -d` + `curl :8000/health` works on fresh clone.
  - For hotfixes: branch from last tag, apply fix, repeat tests, tag `vX.Y.Z+1`.
