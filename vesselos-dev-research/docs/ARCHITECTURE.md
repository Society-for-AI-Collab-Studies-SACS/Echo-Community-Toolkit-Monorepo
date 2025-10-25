# VesselOS Dev Research – Architecture Overview

## Core System Components
- Pipeline (`pipeline/`): `dispatcher_enhanced.py` drives Garden → Echo → Limnus → Kira, using `intent_parser.py` to map ritual stages and `middleware/` + `metrics.py` for logging, timing, and safety.
- Agents (`library_core/agents/`): Garden manages ritual stages and consent; Echo stylises text and personas; Limnus maintains layered memory and the hash-chained ledger; Kira validates chain integrity, coherence, and release gates.
- Interface (`interface/`, `workspace/`): Glue layers that connect dispatcher events to storage, voice logging, and collaboration endpoints.
- CLI (`vesselos.py`, `cli/`): Unified entry point for routing, audits, and per-agent commands (Prime CLI). All automation flows (CI, releases) invoke this surface.
- Memory & Ledger (`memory/`, `workspaces/<id>/state/`): Vector stores, FAISS indices, and ledger encoders. Limnus appends blocks while tracking L1/L2/L3 stats and `block_hash`.
- Workspaces & Logs (`workspaces/<id>/`): Runtime state snapshots (`state/*.json`) and transcripts (`logs/*.jsonl`, `logs/voice_log.json`) kept per user workspace.

## Agent Roles & Commands
- **Garden — Ritual Orchestrator** (`stage`, `cycle`, `consent_given`, `ledger_ref`)
  - `python3 vesselos.py garden start|next|open <scroll> [--prev|--reset]|resume|log "<note>"|ledger`
- **Echo — Persona Voice** (`styled_text`, `quantum_state`, `persona`, `glyph`)
  - `python3 vesselos.py echo summon|mode <persona>|say "<text>"|learn "<seed>"|status`
- **Limnus — Memory & Ledger** (`cached`, `memory_id`, `layer`, `block_hash`, `stats`)
  - `python3 vesselos.py limnus cache "<note>"|recall "<query>"|commit-block input '<json>'|encode-ledger|decode-ledger|reindex --backend <name>`
- **Kira — Integrity & Release** (`passed`, `issues`, `checks`, `summary`)
  - `python3 vesselos.py kira validate|test|mentor --apply|mantra|seal|push --run --message "<msg>"|publish --run --release --tag vX.Y.Z --notes-file CHANGELOG_RELEASE.md|codegen --docs [--types]`

Reference: `AGENTS.md` (root) contains the canonical checklist and extended command catalogue.

## Pipeline Flow
```
input_text -> intent_parser -> EnhancedMRPDispatcher
    |-- Garden (stage, consent)
    |-- Echo (persona & styled_text)
    |-- Limnus (memory + ledger block)
    `-- Kira (integrity + coherence checks)
-> aggregated results -> voice log + state updates
```
`PipelineContext` threads `input_text`, `user_id`, `workspace_id`, `intent`, timestamps, accumulated `agent_results`, execution `trace`, and `metrics` through each stage. Garden appends to its stage ledger, Echo updates persona state, Limnus writes a ledger block and memory cache, and Kira signs off on integrity.

## Module Map & Navigation
- Pipeline orchestration: `pipeline/dispatcher_enhanced.py`, `pipeline/intent_parser.py`, `pipeline/middleware/`, `pipeline/metrics.py`.
- Agents & storage: `library_core/agents/`, `library_core/storage.py`, `library_core/workspace/`.
- Interface services: `interface/`, collaborative server (`collab-server/src/`) with TypeScript build via `npm run build`.
- Scripts & tooling: `scripts/` for integration/audit helpers (e.g. `scripts/generate_release_docs.py` for release notes + Kira knowledge exports), `search/` for generated file indices.
- Documentation: `docs/REPO_INDEX.md` (file index), `docs/IN_DEV_SPECS.md` (detailed command/state spec), and `docs/RELEASE_AND_DOCS_PLAN.md` (release checklist).

For deeper walkthroughs, see `docs/IN_DEV_SPECS.md` and agent briefs under `agents/`. The README quick start demonstrates running the full ritual loop locally.
