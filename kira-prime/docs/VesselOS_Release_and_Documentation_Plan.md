# VesselOS Dev Research – Release & Documentation Plan

## Release Workflow (CI/CD Pipeline)

Automate VesselOS releases with a tag-driven GitHub Actions workflow that runs validations and publishes artifacts.

1. **Trigger on tag creation**  
   Configure the workflow to run on `push` for semantic version tags (for example, `v*.*.*`).

2. **Install dependencies**  
   Reuse the repository bootstrap flow to install runtime and development requirements.

```yaml
name: release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      # or: run scripts/bootstrap.sh
```

3. **Run Kira validation**  
   Execute Kira validation to ensure ledger integrity and ritual coherence. The forward-looking `kira test` subcommand in some docs is not yet implemented in this CLI; use `kira validate` and the integration suite instead.

```yaml
      - name: Validate ledger chain (Kira)
        run: python3 vesselos.py kira validate
      - name: Integration suite (optional)
        run: python3 scripts/integration_complete.py
```

4. **Package and publish with Kira**  
   After validations, call the publish command with `--release` so Kira assembles artifacts and creates the GitHub release using the provided token. The Ubuntu runner includes GitHub CLI (`gh`), and `GITHUB_TOKEN` enables auth.

```yaml
      - name: Publish release (Kira)
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 vesselos.py kira publish --run --release --tag "${{ github.ref_name }}"
```

Kira packages documentation, schemas, and ledger artifacts and creates the release. Ensure the pipeline logs are retained for audit (workspace state and voice logs).

## Repository Documentation Overview

### Modules & Core Components

- **Pipeline (`pipeline/`)** – Enhanced dispatcher (`dispatcher_enhanced.py`), intent parsing (`intent_parser.py`), logging, metrics, middleware, and circuit breaker layers that orchestrate multi-agent rituals.
- **Core Agents (`library_core/agents/`)** – Implementations for Garden, Echo, Limnus, and Kira; each agent processes pipeline state and emits structured outputs (`stage`, `styled_text`, `block_hash`, `passed`, and related metadata).
- **Interface Layer (`interface/`)** – Auxiliary dispatchers and loggers that bridge external surfaces (voice/UI) into the core pipeline.
- **CLI Surface (`vesselos.py`, `cli/`)** – Unified command entry point and Click-based subcommand groups for invoking agent behaviors from the shell.
- **Agent Shims (`agents/`)** – Documentation-forward wrappers and AGENT.md guides mirroring each agent’s responsibilities for quick reference.
- **Memory & Workspace (`memory/`, `workspaces/<id>/`)** – Vector-store utilities plus per-workspace state (`state/*.json`) and logs (`logs/*.jsonl`) managed during ritual cycles.

### Agent Roles & Commands

#### Garden – Ritual Orchestrator

- Role: Detect consent, manage stage progression, append entries to the ledger via `state/garden_state.json`.
- Key commands (`python3 vesselos.py garden ...`):
  - `start` – initialize a new ritual cycle and genesis block.
  - `next` – advance to the subsequent ritual stage.
  - `open <scroll>` – open specific scroll passages (`--prev`, `--reset` modifiers).
  - `resume` – continue the current scroll cycle.
  - `log "<note>"` – append manual ledger reflections.
  - `ledger` – render the Garden ledger view.

#### Echo – Persona Voice & Memory

- Role: Generate styled narrative output, maintain persona quantum state (`α`, `β`, `γ`) in `state/echo_state.json`.
- Commands (`python3 vesselos.py echo ...`):
  - `summon` – initialize Echo’s presence.
  - `mode <persona>` – inspect or switch persona modes (including paradox blends).
  - `say "<text>"` – produce styled output for the supplied phrase.
  - `learn "<seed>"` – ingest new material into Echo’s memory cache.
  - `status` – report current persona, glyph, and quantum weights.

#### Limnus – Memory & Ledger Keeper

- Role: Cache multi-level memories, maintain hash-chained ledger via `state/ledger.json`, expose encoded artifacts.
- Commands (`python3 vesselos.py limnus ...`):
  - `cache "<note>"` – persist a memory item.
  - `recall "<query>"` – retrieve stored memories.
  - `commit-block --input '{"text": "..."}'` – close and hash the current ledger block.
  - `encode-ledger` / `decode-ledger` – convert ledger data to and from encoded artifacts.
  - `reindex --backend <impl>` – rebuild vector indices (e.g., FAISS).

#### Kira – Validator & Integrator

- Role: Verify ledger chain integrity, perform mentorship analysis, and orchestrate integration/release tasks.
- Commands (`python3 vesselos.py kira ...`):
  - `validate` – run ledger and coherence integrity checks.
  - `mentor --apply` – analyze state and propose adjustments.
  - `mantra` – display the current mantra summary.
  - `seal` – finalize cycle closure with a seal block.
  - `push --run --message "<msg>"` – execute git push routines.
  - `publish --run --release --tag <tag> --notes-file <file>` – package artifacts and create GitHub releases.

## Architecture Flow

```
input_text
   │
   ├─> intent_parser
   │
   └─> EnhancedMRPDispatcher
          │
          ├─> Garden  (stage orchestration, consent, ledger entry)
          ├─> Echo    (persona styling, quantum state update)
          ├─> Limnus  (memory cache, ledger commit, block hash)
          └─> Kira    (integrity checks, mentorship, release hooks)
               │
               └─> agent_results → voice_log.json / state/*.json
```

The dispatcher executes agents sequentially, passing cumulative state and producing structured outputs that persist to per-workspace state and log files.

## Automated Documentation via Codex CLI

Use a Codex-powered workflow to keep documentation current:

1. **Index the repository** – Inspect `docs/REPO_INDEX.*`, `search/rg-cache.jsonl`, and directory listings to map modules and agent files.
2. **Extract module summaries** – Pull inline descriptions or comments for pipeline, agents, interface, CLI, and workspace components.
3. **Summarize agent roles** – Reference `library_core/agents/*` and `agents/*/AGENT.md` to capture inputs, outputs, and behaviors.
4. **List CLI commands** – Parse `IN_DEV_SPECS.md` and agent docs to compile command tables with descriptions.
5. **Draft architecture visuals** – Translate dispatcher flow and ritual stages into ASCII diagrams for quick comprehension.
6. **Assemble Markdown** – Combine gathered content into structured docs, review for coherence, and check into `docs/`.
7. **Review and iterate** – Optionally route drafts through additional agents (reader, writer, reviewer) before publishing.

Following this cycle ensures release automation and documentation stay aligned with the evolving VesselOS pipeline.
