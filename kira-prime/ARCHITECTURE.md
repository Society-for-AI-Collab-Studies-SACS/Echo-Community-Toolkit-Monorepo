# VesselOS Dev Research – Architecture Summary

## Core System Areas
- Pipeline (`pipeline/`): The enhanced dispatcher (`dispatcher_enhanced.py`) receives parsed intents, then coordinates Garden → Echo → Limnus → Kira. Middleware (`pipeline/middleware/`), metrics (`pipeline/metrics.py`), and the circuit breaker enforce logging, timing, and resilience around each hop.
- Agents (`library_core/agents/`): Garden manages ritual stages and consent; Echo stylises text and derives quantum personas; Limnus persists layered memory and the hash‑chained ledger; Kira validates integrity, coherence, and release gates.
- CLI & Commands (`vesselos.py`, `cli/`): `vesselos.py` is the command surface for Garden/Echo/Limnus/Kira operations, audits, and release tooling. The CLI modules encapsulate option parsing and dispatch.
- Memory & Ledger (`memory/`, `workspaces/<id>/state/ledger.json`): Vector memory backends, cache layers, and ledger encoding live here. Limnus appends to the ledger while preserving block hashes and stats.
- Workspaces & Logs (`workspaces/<id>/`): Each workspace maintains agent state (`state/*.json`) and run transcripts (`logs/*.jsonl`, plus `logs/voice_log.json`). Runtime jobs read/write only within the active workspace.

## Orchestration Flow & Context
```
input_text → intent_parser → EnhancedMRPDispatcher
  → Garden (stage, consent, ledger_ref)
  → Echo   (styled_text, persona, quantum_state, glyph)
  → Limnus (memory cache, ledger block, stats)
  → Kira   (integrity checks, coherence summary)
→ aggregated agent_results → voice log + workspace state updates
```
`PipelineContext` threads shared metadata through this loop: `input_text`, `user_id`, `workspace_id`, `intent`, timestamps, intermediate `agent_results`, execution `trace`, and collected `metrics`. Garden appends each ritual pass to its stage ledger, Echo persists persona state, Limnus commits a new block into `state/ledger.json`, and Kira signs off by confirming chain integrity.

## Agent Roles & Primary Commands
- Garden — orchestrates rituals and consent (`stage`, `cycle`, `consent_given`, `ledger_ref`)
  - `python3 vesselos.py garden start|next|open <scroll> [--prev|--reset]|resume|log "<note>"|ledger`
- Echo — produces stylised voice and personas (`styled_text`, `quantum_state`, `persona`, `glyph`)
  - `python3 vesselos.py echo summon|mode <persona>|say "<text>"|learn "<seed>"|status`
- Limnus — captures memory layers and maintains the ledger (`cached`, `memory_id`, `layer`, `block_hash`, `stats`)
  - `python3 vesselos.py limnus cache "<note>"|recall "<query>"|commit-block input '<json>'|encode-ledger|decode-ledger|reindex --backend <name>`
- Kira — performs validation, mentorship, and release tasks (`passed`, `issues`, `checks`, `summary`)
  - `python3 vesselos.py kira validate|test|mentor --apply|mantra|seal|push --run --message "<msg>"|publish --run --release --tag vX.Y.Z --notes-file CHANGELOG_RELEASE.md`

## Module Map & Navigation
- Pipeline: dispatcher, intent parsing, middleware (`pipeline/dispatcher_enhanced.py`, `pipeline/intent_parser.py`, `pipeline/middleware/`).
- Agents: concrete implementations and storage helpers (`library_core/agents/`, `library_core/storage/`).
- Interface glue and services (`interface/`, `orchestration/`), collaborative server (`collab-server/src/`), and VS Code extension (`vscode-extension/`).
- Documentation indices live in `docs/` (`REPO_INDEX.md`, deep dives under `docs/vesselos-docs/`). Use these for per-feature exploration.

## Operational Hooks
- Continuous Integration: The default GitHub Actions workflow installs Python and Node toolchains, runs `python -m pytest -q`, executes `python3 vesselos.py kira test`, and performs `python3 vesselos.py audit full --workspace example` (non-blocking) before building the collab server and VS Code extension. Audit artifacts from `workspaces/example/` are uploaded when present.
- Release Flow: Tags `v*.*.*` trigger `.github/workflows/release.yml` to rebuild deliverables, run Kira validation, and publish artifacts. Follow `CONTRIBUTING.md` and `AGENTS.md#release-process` for the full checklist.

For extended specifications—data contracts, ritual transcripts, and command matrices—see `docs/Architecture.md`, `docs/VesselOS_Command_Reference.md`, and the agent briefs under `agents/`.
