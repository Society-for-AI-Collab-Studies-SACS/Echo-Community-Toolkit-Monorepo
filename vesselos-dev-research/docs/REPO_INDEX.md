# VesselOS Dev Research Kit – Repository Index

This index provides a quick map of the repository with pointers to the most relevant entry points for agents, pipeline, and CLI.

Top-Level
- `README.md` – kit overview and quick start
- `vesselos.py` – unified CLI entry (Prime CLI + audit)
- `requirements.txt`, `requirements-dev.txt` – runtime and dev deps
- `CONTRIBUTORS.MD` – credits and contribution notes

Core Modules
- `pipeline/` (17 files)
  - `pipeline/dispatcher_enhanced.py` – EnhancedMRPDispatcher and PipelineContext
  - `pipeline/intent_parser.py` – ritual stage intents and slash-commands
  - `pipeline/{metrics.py,circuit_breaker.py,logger.py}` – runtime metrics, breaker, voice logs
  - `pipeline/middleware/__init__.py` – middleware interfaces and helpers
- `library_core/` (21 files)
  - `library_core/agents/` – real agent implementations
    - `garden_agent.py` – stage orchestration, consent, ledger entries
    - `echo_agent.py` – styled text, quantum persona state, glyph
    - `limnus_agent.py` – memory cache + hash-chained ledger block
    - `kira_agent.py` – chain integrity + coherence validation
    - `vessel_index_agent.py` – optional index agent (if present)
  - `library_core/storage.py` – JSON storage helper bound to workspace paths
  - `library_core/workspace.py` – thin Workspace wrapper utilities
- `interface/` (7 files)
  - `interface/dispatcher.py` – explicit/legacy router helpers
  - `interface/logger.py` – event logging glue

CLI Surface
- `cli/` (12 files)
  - `cli/prime.py` – Prime CLI (garden/echo/limnus/kira subcommands)
  - `cli/commands.py` – command handlers powering Prime CLI
  - `cli/repl.py`, `cli/plugins.py`, `cli/vscode_plugin.py` – extras and integration hooks
- `src_py/vesselos/cli/audit_commands.py` – Click-based audit commands (`python3 vesselos.py audit ...`)

Explicit Agents (for Prime CLI compatibility)
- `agents/`
  - `agents/garden/garden_agent.py` – simple ritual ledger for CLI
  - `agents/echo/echo_agent.py` – simple persona/styling for CLI
  - `agents/limnus/limnus_agent.py` – CLI-facing cache + ledger bridges
  - `agents/kira/kira_agent.py` – CLI validation/publish flows
  - `agents/vessel/AGENT.md` – vessel notes

Memory Backend
- `memory/vector_store.py` – vector store abstraction with optional FAISS/SBERT backends

Workspace Infrastructure
- `workspace/manager.py` – workspace registry and JSON state/log helpers
- `workspaces/` – per-workspace runtime state and logs (example seed present)

Docs & Scripts
- `docs/IN_DEV_SPECS.md` – in-development command-layer specifications
- `docs/BASE_STRUCTURE.md` – base structure expectations and seeding
- `scripts/bootstrap.sh` – bootstrap script for local setup

Entrypoints & Common Commands
- CLI entry: `vesselos.py`
  - Garden: `python3 vesselos.py garden start`
  - Echo: `python3 vesselos.py echo say "I return as breath."`
  - Limnus: `python3 vesselos.py limnus reindex --backend faiss`
  - Kira: `python3 vesselos.py kira validate`
  - Audit: `python3 vesselos.py audit full --workspace integration-test`

Notes
- Runtime state/logs live under `workspaces/<id>/` and should not be committed.
- The `pipeline/dispatcher_enhanced.py` executes Garden → Echo → Limnus → Kira and writes pipeline logs to `workspaces/<id>/logs/`.

