# Repository Index

A quick, human-friendly map of major modules and key files.

- `vesselos.py` — Unified CLI entry (routes to Prime CLI or audit group).
- `cli/` — Prime CLI: argument parsing, command handlers, plugins.
  - `cli/prime.py` — Top-level CLI groups and subcommands.
  - `cli/commands.py` — Implements Garden/Echo/Limnus/Kira verbs.
- `library_core/` — Core agent implementations + storage/orchestration.
  - `library_core/agents/garden_agent.py` — Ritual stages, consent, ledger refs.
  - `library_core/agents/echo_agent.py` — Styled text, persona, quantum state αβγ.
  - `library_core/agents/limnus_agent.py` — Memory cache, hash-ledger, stats.
  - `library_core/agents/kira_agent.py` — Integrity checks, coherence, summary.
- `agents/` — CLI shims and AGENT.md briefs for each agent.
- `pipeline/` — Enhanced dispatcher, intents, middleware, metrics, circuit breaker.
  - `pipeline/dispatcher_enhanced.py` — EnhancedMRPDispatcher (Garden→Echo→Limnus→Kira).
  - `pipeline/intent_parser.py` — Ritual stages, mantras, slash-commands.
  - `pipeline/middleware/` — Logging/Metrics/Validation middleware.
- `interface/` — Dispatcher and logging bridges to external surfaces.
- `memory/` — Vector store backends and utilities.
- `workspaces/<id>/` — Per-workspace state and logs at runtime.
  - `state/garden_state.json`, `state/echo_state.json`, `state/limnus_memory.json`, `state/ledger.json`.
  - `logs/voice_log.json`, `logs/<agent>.jsonl`.
- `frontend/` — Published assets, including `frontend/assets/ledger.json`.
- `scripts/` — Integration and ops (e.g., `scripts/integration_complete.py`).
- `tests/` — Pytest suite (unit + integration + smoke gates).
- `.github/workflows/` — CI (validate, e2e, release).

Agent CLI surface (via `python3 vesselos.py`):
- `garden start|next|open|resume|log|ledger`
- `echo summon|mode|say|learn|status|calibrate`
- `limnus cache|recall|commit-block|encode-ledger|decode-ledger|status|reindex`
- `kira validate|mentor|mantra|seal|push|publish`

Dispatcher flow:
```
input_text → intent_parser → EnhancedMRPDispatcher
  → Garden → Echo → Limnus → Kira → agent_results → voice_log + state
```
