# VesselOS Custom Command Researcher Brief (In-Development)

**Audience**: Principal investigators, staff engineers, and research leads extending VesselOS.  
**Status**: In-development reference (2025-05-26).  
**Scope**: Command-layer specifications, orchestration contracts, and reproducible build instructions for working directly with the VesselOS custom command surface.

---

## 1. System Orientation

- **Modal focus**: All interactive control flows through `python3 vesselos.py ...`, which routes either to the Prime CLI (`cli/prime/`) or the Click-based audit commands (`src_py/vesselos/cli/`).
- **Agent order**: Garden -> Echo -> Limnus -> Kira. Each agent appends to shared state under `workspaces/<workspace_id>/`.
- **Consent ledger**: Limnus enforces a hash-chained ledger (`state/ledger.json`) that Kira validates before high-impact actions (`push`, `publish`, `seal`).
- **Dispatcher**: `pipeline/dispatcher_enhanced.py` binds the four agents into a single ritual pass. The dispatcher accepts a `PipelineContext` payload and records results in `logs/voice_log.json`.
- **Log surfaces**: Per-agent journaling lands in `workspaces/<workspace_id>/logs/<agent>.jsonl`. Researchers should tail these when experimenting with novel commands.

### 1.1 Command Routing Snapshot

```
input_text -> intent_parser -> EnhancedMRPDispatcher
    |-- Garden Agent (stage orchestration, consent detection)
    |-- Echo Agent (persona & styled text)
    |-- Limnus Agent (memory cache + ledger block)
    `-- Kira Agent (integrity validation, mentorship)
-> aggregated agent_results -> voice log + state updates
```

---

## 2. Command Surface Inventory

| Agent | Entry Command | Stable Primitives | Active In-Dev Primitives | Outputs of Record |
| --- | --- | --- | --- | --- |
| Garden (`library_core/agents/garden_agent.py`) | `python3 vesselos.py garden ...` | `start`, `next`, `resume`, `open`, `ledger`, `log` | Scroll state resumptions with consent tagging | `stage`, `cycle`, `consent_given`, `ledger_ref` |
| Echo (`library_core/agents/echo_agent.py`) | `python3 vesselos.py echo ...` | `summon`, `mode`, `status`, `say`, `learn` | Persona `map`, paradox cycling refinements | `styled_text`, `quantum_state (alpha,beta,gamma)`, `persona`, `glyph` |
| Limnus (`library_core/agents/limnus_agent.py`) | `python3 vesselos.py limnus ...` | `cache`, `recall`, `commit-block`, `encode-ledger`, `decode-ledger`, `reindex` | Layer-aware mentoring hooks (`--backend faiss`) | `cached`, `memory_id`, `layer`, `block_hash`, `stats` |
| Kira (`library_core/agents/kira_agent.py`) | `python3 vesselos.py kira ...` | `validate`, `mentor`, `seal`, `mantra` | Release automation (`push`, `publish`, `mentor --apply`) | `passed`, `issues`, `checks`, `summary` |
| Audit CLI (`src_py/vesselos/cli/audit_commands.py`) | `python3 vesselos.py audit ...` | `scan`, `summary`, `diff` (per module) | Extended compliance bundles | Results streamed to stdout + JSON when `--json` |

> **Tip**: Every Prime CLI command remains available through `vesselos.py`. Experimental primitives landing in `cli/prime` should document state side effects before integration runs.

---

## 3. In-Development Specifications

### 3.1 Pipeline Contracts

- **Intent envelope**: `pipeline/intent_parser.py` maps raw input to ritual stages (`/plant`, `/witness`, `/seal`). Custom commands must either respect existing mantras or define a new slash-command and register it in the parser.
- **Context payload**: `PipelineContext` (see `pipeline/dispatcher_enhanced.py`) requires `input_text`, `user_id`, `workspace_id`, `intent`, `timestamp`, `agent_results`, `trace`, and `metrics`.
- **Stage ledger**: Garden writes the stage ledger reference (`ledger_ref`) into `agent_results`. Downstream consumers must not mutate the ledger entry; treat it as append-only.
- **Quantum state continuity**: Echo emits persona weights (`alpha/beta/gamma`) that Limnus trusts when calculating cache deltas. Any custom command adjusting persona weights must normalise them before returning control.

### 3.2 Agent Implementation Notes

- **Garden**: Consent detection remains heuristics-based. When extending, respect the boolean `consent_given` flag--Kira halts validations if false.
- **Echo**: `quantum_state` is represented as floats rounded to two decimals. Avoid integer coercion; downstream tests (`tests/test_echo_agent.py`) assume floats.
- **Limnus**: Ledger blocks chain via `block_hash`. Research prototypes can add metadata fields, but the hash must include the canonical fields to preserve integrity.
- **Kira**: Mentor routines read from `state/kira_knowledge.json` and expect ledger continuity. Augmenting mentor advice requires updating both TypeScript types (`tools/codex-cli/types/knowledge.d.ts`) and the JSON emitter.

### 3.3 State and Ledger Expectations

- Workspace root: `workspaces/<workspace_id>/`.
- State contracts:
  - `state/garden_state.json`
  - `state/echo_state.json`
  - `state/limnus_memory.json`
  - `state/ledger.json`
- Logs:
  - `logs/voice_log.json`
  - `logs/<agent>.jsonl`
- Ledger validation: Kira recomputes `block_hash` for the latest block and compares it to its predecessor. Experimental commands must append blocks via Limnus utilities (`limnus commit-block`) rather than writing files directly.

---

## 4. Developer Build Instructions

### 4.1 Environment Prerequisites

- Python >= 3.10 (with `venv` module).
- Node.js >= 20 for the Prime CLI and collab server tooling.
- Git, `make` (optional), and Docker if running the smoke stack.
- Recommended Python dependencies: `pip install -r requirements.txt` (base) and `pip install -r requirements-dev.txt` for tests.

### 4.2 Bootstrapping VesselOS for Command Research

```bash
# Clone the upstream VesselOS codebase in sibling directory
git clone https://github.com/your-org/vesselos.git
cd vesselos

# Python environment isolating research tooling
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Optional: install dev/test helpers
python3 -m pip install -r requirements-dev.txt

# Node toolchain for Prime CLI + collab server
npm install  # root package.json aggregates CLI helpers

# Validate CLI wiring
python3 vesselos.py garden start --help
python3 vesselos.py audit --help
```

### 4.3 Running the Development Loop

1. **Seed workspace state**:  
   `python3 vesselos.py garden start` (creates ledger genesis)  
   `python3 vesselos.py echo summon` (normalises persona weights)
2. **Experiment with commands**: leverage `vesselos.py <agent> <command>` to inspect state transitions. Prefer the `--json` flags where available (Limnus recall, Kira validate).
3. **Monitor state**: tail `workspaces/<workspace_id>/logs/voice_log.json` while executing commands to ensure pipeline trace continuity.
4. **Resetting between runs**: use `python3 vesselos.py garden open <scroll> --reset` and `python3 vesselos.py limnus reindex --backend faiss` to rehydrate caches without manual file edits.

### 4.4 Instrumentation & Tests

- Run targeted tests while iterating:
  - `python -m pytest -q tests/test_garden_agent.py`
  - `python -m pytest -q -k "limnus"`
- Full suites before integrating experimental commands:
  - `python scripts/integration_complete.py`
  - `python vesselos.py audit full --workspace integration-test`
- Collab smoke (if Docker is available):
  - `docker compose up -d`
  - `COLLAB_SMOKE_ENABLED=1 python -m pytest tests/test_collab_server.py -q`
- Use `python3 vesselos.py kira validate` after each command mutation to confirm ledger integrity.

---

## 5. Extension Workflow for Custom Commands

1. **Define intent**: add new slash-command or ritual alias in `pipeline/intent_parser.py`.
2. **Extend dispatcher**: register the command within `pipeline/dispatcher_enhanced.py`, ensuring Garden is still first touch for consent checks.
3. **Augment agent**: implement the handler under the relevant `library_core/agents/<agent>_agent.py`, respecting the output schema listed in Section 2.
4. **Expose CLI entry**: wire the command through `cli/prime` or the audit Click group to maintain `vesselos.py` parity.
5. **Document state changes**: update `docs/VesselOS_Command_Reference.md` and note any new fields in `state/` JSON artefacts.

> For long-lived research branches, place provisional documentation in `docs/experimental/` and migrate once the command stabilises.

---

## 6. Observability & Research Notes

- **Metrics**: `pipeline/metrics.py` emits counters for stage transitions, consent confirmations, and validation outcomes. Hook new commands into these metrics early to maintain observability parity.
- **Circuit breaker**: `pipeline/circuit_breaker.py` guards against runaway rituals. Custom commands should emit context-rich errors to simplify breaker tuning.
- **Golden fixtures**: Extend `tests/fixtures/golden/` if the new commands affect ritual flows. Keep fixtures deterministic for repeatability.
- **Ledger backups**: Always snapshot `workspaces/<workspace_id>/state/ledger.json` before destructive experiments; the ledger is append-only and powers release validation.

This brief will evolve alongside the command surface. Researchers are encouraged to append findings, pitfalls, and state schema changes in follow-on PRs to keep VesselOS institutional knowledge current.
