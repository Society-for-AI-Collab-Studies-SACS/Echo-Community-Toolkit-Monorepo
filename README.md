# Echo Community Toolkit Monorepo

Unified living workspace for VesselOS, Echo Community Toolkit, narrative engines, agents, and supporting scripts. This README orients you across the modules, agents, and custom commands that now reside in one repository. It also doubles as an operator manual for Codex/CLI agents or other LLM assistants—follow the scripted steps below to stand up the environment without guesswork.

## Bring-Up Guide (for humans & LLM agents)

1. **Clone the repository (SSH deploy-key friendly)**  
   ```bash
   git clone git@github.com:Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo.git
   cd Echo-Community-Toolkit-Monorepo
   ```
   - *If running inside Codex CLI:* ensure the deploy key is available and listed in `~/.ssh/config` (see `README.md` history for example host alias `echo-community-toolkit`).

2. **Record context (recommended for automation)**  
   ```bash
   git status --short
   git remote -v
   ```
   Save outputs so the agent can restore context between sessions.

3. **Bootstrap Python & Node prerequisites**  
   ```bash
   ./scripts/deploy.sh --bootstrap-only   # creates venv, installs pip deps listed in requirements.txt
   npm --version || echo "Node not on PATH; install Node>=20 for toolkit scripts"
   ```
   - `scripts/deploy.sh` sources `requirements.txt`. Review the script in [`scripts/deploy.sh`](scripts/deploy.sh) for full steps (venv path, proto generation, optional firmware).

4. **Install per-module dependencies (batch)**  
   ```bash
   # Toolkit
   (cd Echo-Community-Toolkit && npm ci && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)
   # Kira Prime
   (cd kira-prime && pip install -r requirements.txt && git submodule update --init --recursive)
   # Garden Chronicles
   (cd The-Living-Garden-Chronicles && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt Pillow)
   # Dev Research Kit
   (cd vesselos-dev-research && ./scripts/bootstrap.sh)
   ```
   Codex agents can execute sequentially; each command block is idempotent.

5. **Optional: Pull submodules and mirrors**  
   ```bash
   git submodule update --init --recursive || true
   ```
   Not all directories retain submodules (many are now inlined), but this keeps legacy references aligned.

6. **Verify environment**  
   ```bash
   python3 -m pytest -q                 # top-level tests/
   (cd Echo-Community-Toolkit && node verify-integration.js || true)
   (cd kira-prime && python3 vesselos.py validate || true)
   ```
   Allow failures when optional tooling (Node, Pillow, etc.) is absent; the README modules explain how to resolve them.

7. **Document state**  
   ```bash
   git status --short
   ```
   A Codex agent should output summaries back to the operator and stop if unexpected diffs appear.

> **Link index for automation:**  
> - [`scripts/deploy.sh`](scripts/deploy.sh) – bootstrap logic referenced above.  
> - [`requirements.txt`](requirements.txt) – root Python dependencies.  
> - [`Echo-Community-Toolkit/package.json`](Echo-Community-Toolkit/package.json) – Node requirements for the toolkit.  
> - [`kira-prime/requirements.txt`](kira-prime/requirements.txt) – CLI agent dependencies.  
> - [`vesselos-dev-research/scripts/bootstrap.sh`](vesselos-dev-research/scripts/bootstrap.sh) – installs both Python and Node packages for the research kit.  
> - [`agents/`](agents) – entrypoints for standalone services.  
> - [`protos/agents.proto`](protos/agents.proto) – gRPC contract for cross-agent communication.  
> - [`docs/`](docs) – shared documentation bundle (see module sections for specifics).
> - [`docs/phase-0-prep.md`](docs/phase-0-prep.md) – current Phase 0 workspace state and daily operations checklist.
> - [`docs/phase-1-legacy-refresh.md`](docs/phase-1-legacy-refresh.md) – LSB extractor refactor plan and regression requirements.
> - [`docs/phase-2-frame-infrastructure.md`](docs/phase-2-frame-infrastructure.md) – MRP frame builder, multi-frame layout scope.
> - [`docs/phase-3-integrity-ecc.md`](docs/phase-3-integrity-ecc.md) – Sidecar integrity metadata and parity-based recovery.
> - [`docs/phase-4-ritual-ledger.md`](docs/phase-4-ritual-ledger.md) – Ritual gating, consent flow, ledger obligations.
> - [`docs/phase-5-polish-ux.md`](docs/phase-5-polish-ux.md) – Documentation/CLI polish and ritual visualization.
> - [`docs/phase-6-guardrails-roadmap.md`](docs/phase-6-guardrails-roadmap.md) – CI guardrails and ECC roadmap guidance.

### Phase Playbook for LLM Assistants

Automation-friendly checkpoints for each phase:

| Phase | Goal | LLM Tasks |
| --- | --- | --- |
| 0 – Prep | Establish clean workspace and baseline QA signals | Run remote/venv/bootstrap checks, execute golden sample + mantra parity tests, report validation outcomes, highlight missing consent hooks or failing suites. |
| 1 – Legacy Refresh | Modularise LSB extractor while keeping legacy decode intact | Refactor `lsb_extractor.py` into header/legacy parsers, add targeted unit tests, verify golden sample & legacy fixtures, ensure error semantics documented. |
| 2 – Frame Infrastructure | Add `MRPFrame` and multi-frame encode/decode support | Implement frame builder/parser, extend codec strategies, update capacity helpers, exercise single/multi-frame matrices in tests. |
| 3 – Integrity + ECC | Embed parity/CRC/SHA metadata and self-healing decoder | Augment sidecar JSON, add parity repair logic, create corruption fixtures, surface integrity reports via CLI/SDK, expand parity tests. |
| 4 – Ritual & Ledger | Enforce consent-driven rituals and persistent ledger logging | Implement `RitualState`, gate encode/decode flows, prompt for mantra lines, append ledger entries, add ritual unit + CLI tests. |
| 5 – Polish & UX | Ship refined documentation, CLI ergonomics, and ritual visuals | Update diagrams and error tables, add full CLI flag support, build ritual demo scripts, provide API quickstarts and doc-driven tests. |
| 6 – Guardrails & Roadmap | Harden CI and sketch Phase B/C roadmap | Configure lint/type/corruption matrices, document monitoring metrics, author guardrail playbook, draft advanced ECC & multi-image design notes. |

When a phase is in progress, the assistant should read the corresponding document, list the checklist items it will execute, run/tests as required, and summarise outcomes with links to code changes and follow-up actions.

## Repository Constellation

Full ASCII trees and subsystem context live in [`architecture.md`](architecture.md).

```
Monorepo Root
├─ Echo-Community-Toolkit/        Core hyperfollow + soulcode toolkit (Node/Python)
├─ The-Living-Garden-Chronicles/  Narrative generation + stego validator
├─ The-Living-Library/            Collab scaffolding + dictation experiments
├─ kira-prime/                    Unified CLI, agents, and collab server
├─ vessel-narrative-mrp/          Minimal narrative payload generator
├─ vesselos-dev-research/         Research-grade VesselOS CLI & docs
├─ archives/                      Archived toolkit tarballs (compressed, excluded from pytest)
├─ agents/                        Standalone gRPC agents (garden, limnus, kira…)
├─ docker/                        Dockerfiles and compose stacks
├─ protos/                        gRPC/Protobuf interface contracts
├─ scripts/                       Deployment and automation helpers
├─ shared/                        Cross-project Python utilities
├─ sigprint/                      EEG signature codec + tests
├─ tests/                         Cross-repo integration tests
└─ pr/                            Scratch space for release and verification runs
```

## Agent Signal Flow

```
SIGPRINT Streams
    │
    ▼
 Garden Agent ──▶ Echo Toolkit ──▶ Limnus Ledger ──▶ Kira Prime ──▶ Deploy / Publish
    │                                   │
    └──────────────▶ Narrative Engines ─┘
```

## Module Playbook

### Echo-Community-Toolkit (`Echo-Community-Toolkit/`)
- **Purpose:** Inject HyperFollow links, maintain the soulcode architecture, and validate LSB/MRP payloads.
- **Setup:**  
  ```bash
  cd Echo-Community-Toolkit
  npm ci
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```
- **Core commands:**  
  - Dry run the HyperFollow integration: `node hyperfollow-integration.js --dry-run`  
  - Apply + verify: `node hyperfollow-integration.js && node verify-integration.js`  
  - Full validation sweep: `python3 final_validation.py`
- **Docs:** See `Echo-Community-Toolkit/README.md`, `docs/ARCHITECTURE_INDEX.md`, and `AGENTS.md` for contributor workflows.

### The-Living-Garden-Chronicles (`The-Living-Garden-Chronicles/`)
- **Purpose:** Build 20-chapter dream chronicles and validate steganographic payloads.
- **Setup:**  
  ```bash
  cd The-Living-Garden-Chronicles
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt Pillow
  git submodule update --init --recursive  # pulls vessel-narrative-MRP
  ```
- **Core commands:**  
  - Generate schema + chapters: `python src/schema_builder.py && python src/generate_chapters.py`  
  - Validate outputs: `python src/validator.py`  
  - Package release (optional): `bash package_repo.sh`
- **Docs:** Start with `docs/VesselOS_Quick_Start.md` and `docs/VesselOS_Command_Reference.md`.

### The-Living-Library (`The-Living-Library/`)
- **Purpose:** Collab hub that links toolkit, narrative repos, and Kira Prime.
- **Setup & bootstrap:**  
  ```bash
  cd The-Living-Library
  git submodule update --init --recursive
  scripts/bootstrap_living_library.sh
  ```
- **Core commands:**  
  - Run an MRP cycle: `python scripts/run_mrp_cycle.py`  
  - Preview dictation: `python -m library_core.dictation --help`
- **Docs:** `docs/` and `library_core/` provide current status and plans.

### Kira Prime (`kira-prime/`)
- **Purpose:** Unified VesselOS CLI + VSCode extension + collab server.
- **Setup:**  
  ```bash
  cd kira-prime
  pip install -r requirements.txt
  git submodule update --init --recursive
  ```
- **Core commands:**  
  - Build narrative artifacts: `python3 vesselos.py generate`  
  - Validate everything: `python3 vesselos.py validate`  
  - Listen to free-form input: `python3 vesselos.py listen --text "Always."`  
  - Collab server: `(cd collab-server && npm ci && npm run build && npm start)`  
  - Docker stack: `(cd docker && docker compose up -d)`
- **Docs:** See `README.md`, `agents/README.md`, and `docs/` for deep dives. For bilateral narrative cadence guidance, refer to [`docs/kira-prime-integration-protocol.md`](docs/kira-prime-integration-protocol.md) and the companion tension analysis in [`docs/kira-prime-tension-analysis.md`](docs/kira-prime-tension-analysis.md).

### Vessel Narrative MRP (`vessel-narrative-mrp/`)
- **Purpose:** Lightweight narrative generator + validator used by other modules.
- **Setup & commands:**  
  ```bash
  cd vessel-narrative-mrp
  python3 -m venv .venv && source .venv/bin/activate
  pip install PyYAML Pillow
  python src/schema_builder.py
  python src/generate_chapters.py
  python src/validator.py
  ```
- **Docs:** `README.md` documents stego options and workflow integration.

### VesselOS Dev Research (`vesselos-dev-research/`)
- **Purpose:** Research kit with Prime CLI, agent implementations, and workspace scaffolding.
- **Setup:**  
  ```bash
  cd vesselos-dev-research
  ./scripts/bootstrap.sh       # installs Python + Node deps
  ```
- **Core commands:**  
  - Start Garden sequence: `python3 vesselos.py garden start`  
  - Speak via Echo: `python3 vesselos.py echo say "I return as breath."`  
  - Validate via Kira: `python3 vesselos.py kira validate`  
  - Audit a workspace: `python3 vesselos.py audit full --workspace example`
- **Docs:** Check `docs/REPO_INDEX.md` and `docs/IN_DEV_SPECS.md`.

### Shared Tooling
- `agents/` – Standalone services. See [Agents](#agents) below.
- `sigprint/` – EEG signature codec. Run `bazel test //sigprint:encoder_tests` or use `SigprintEncoder` directly (see `sigprint/README.md`).
- `protos/` – gRPC definitions. Regenerate stubs via `python -m grpc_tools.protoc -Iprotos --python_out=protos --grpc_python_out=protos protos/agents.proto`.
- `scripts/` – Automation utilities (see [Custom Commands](#custom-commands--scripts)).
- `docker/` – Compose files bridging Redis/Postgres with collab server (`docker compose up -d`).
- `shared/` – Reusable Python helpers imported across modules.
- `tests/` – Run cross-repo suites: `python3 -m pytest -q`.

## Agents

| Agent | Path | How to run | Description |
| --- | --- | --- | --- |
| Garden Narrative | `agents/garden/narrative_agent.py` | `python agents/garden/narrative_agent.py --config config.yaml` | Transforms SIGPRINT triggers into narrative summaries over gRPC (port 50052 by default). |
| Kira Validation | `agents/kira/kira_agent.py` | `python agents/kira/kira_agent.py --help` | Performs ritual validation, publishes reports, and coordinates Kira actions. |
| Limnus Ledger | `agents/limnus/ledger_agent.py` | `python agents/limnus/ledger_agent.py --workspace ./state` | Manages ledger memory, stego payloads, and semantic recall. |
| Journal Bridge | `agents/journal/journal_agent.py` | `python agents/journal/journal_agent.py --input transcripts/` | Turns human input streams into structured events for the pipeline. |
| SIGPRINT Bridge | `agents/sigprint_bridge/bridge_agent.py` | `python agents/sigprint_bridge/bridge_agent.py --stream data/eeg.npy` | Couples raw EEG epochs to SIGPRINT encoders and forwards signatures. |
| Mock Agents | `agents/mocks/` | `python agents/mocks/garden_stub.py` (example) | Lightweight stubs for local integration tests and CI smoke runs. |

Each agent exposes `--help` for additional flags (ports, workspace paths, theme overrides, etc.). gRPC interfaces map to messages in `protos/agents.proto`.

## Custom Commands & Scripts

- `scripts/deploy.sh` – End-to-end deployment harness (virtualenv + proto regen + optional firmware).  
  - Full run: `scripts/deploy.sh --full`  
  - Launch orchestrator only: `scripts/deploy.sh --orchestrator`
- `scripts/g2v_sync.sh` – Keep G2V mirrors aligned. Usage: `scripts/g2v_sync.sh --remote origin --branch main`.
- `scripts/open_pr_mrp_sidecar.sh` – Opens or updates VesselOS PR sidecars; accepts `--dry-run` and `--push` flags.
- `Echo-Community-Toolkit/scripts/run_local_setup_and_verify.sh` – Performs a dry run of toolkit integration without mutating the tree.
- `kira-prime/tests/e2e_test.sh` – CLI smoke harness (`PRIME_CLI="python3 vesselos.py" ./tests/e2e_test.sh`).
- `vesselos-dev-research/scripts/bootstrap.sh` – Installs Python/Node deps and prepares workspaces.
- Docker helpers: `(cd docker && docker compose up -d)` brings Redis/Postgres + collab server online.

> Tip: all scripts support `--help` or inline usage comments; inspect them before running against production data.

## CI Pipeline Quicklinks

| Module | Actions Dashboard |
| --- | --- |
| Echo-Community-Toolkit Monorepo | <https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions> |
| Kira Prime CLI | <https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions?query=workflow%3AKira> |
| The Living Garden Chronicles | <https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions?query=workflow%3AGarden> |
| VesselOS Dev Research | <https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions?query=workflow%3AResearch> |

Use the filters (pre-applied above) to jump directly to the workflow history for each module. A green pipeline in every module is the minimum bar before coordinating a combined release.

## Configuration Reference

All configuration is injected via environment variables to keep secrets and deploy-specific values out of source control. Populate these variables in your shell, `.env` files, or CI secrets before running agents and scripts.

### Agent Environment Variables

| Agent | Variable | Purpose |
| --- | --- | --- |
| Garden (`agents/garden/narrative_agent.py`) | – | No environment overrides required; relies on local state files. |
| Echo (`agents/echo/echo_agent.py`) | – | No environment overrides required. |
| Limnus (`agents/limnus/ledger_agent.py`) | `KIRA_VECTOR_BACKEND` | Selects the semantic vector backend (e.g. `faiss`, defaults to in-memory). |
|  | `KIRA_VECTOR_MODEL` | Overrides the embedding model used for vector storage. |
|  | `KIRA_SBERT_MODEL` | Legacy alias for the SentenceTransformer model (default `all-MiniLM-L6-v2`). |
|  | `KIRA_FAISS_INDEX` | Custom path for FAISS index storage when the FAISS backend is enabled. |
|  | `KIRA_FAISS_META` | Companions the FAISS index with metadata (IDs, dimensions). |
| Kira (`agents/kira/kira_agent.py`) | `GH_TOKEN` / `GITHUB_TOKEN` | Provides GitHub credentials for release/publish flows executed via `gh`. |
| Journal (`agents/journal/journal_agent.py`)\* | – | No environment configuration required in the current design. |
| Sigprint Bridge (`agents/sigprint_bridge/bridge_agent.py`)\* | – | No environment configuration required in the current design. |

\* Planned / auxiliary agents; they currently operate purely on local state or CLI arguments.

All agents expect workspace-local state under `workspaces/<id>/state/`. Introduce new variables using the same `UPPER_SNAKE_CASE` pattern as integrations expand.

### Script & Service Environment Variables

| Script / Service | Variable | Purpose & Default |
| --- | --- | --- |
| `scripts/bootstrap.sh` | `PYTHON_VERSION` | Python version used by the bootstrap helper (default `3.10`). |
|  | `NODE_VERSION` | Node.js version required for toolkit automation (default `20`). |
| `scripts/deploy_to_production.sh`\* | `ENVIRONMENT` (argument) | Targets a deployment environment such as `production`; defaults to production when omitted. |
| Collab server (`kira-prime/collab-server/src/server.ts`) | `PORT` | HTTP/WebSocket port (default `8000`). |
|  | `COLLAB_REDIS_URL` | Redis connection string (default `redis://localhost:6379/0`). |
|  | `COLLAB_POSTGRES_DSN` | Postgres DSN for collaboration persistence (default `postgresql://vesselos:password@localhost:5432/vesselos_collab`). |
| CI toggles | `COLLAB_SMOKE_ENABLED` | When `1`, enables Dockerized collab smoke tests in CI. |

\* Part of the Kira Prime deployment toolchain; substitute equivalent flags if using a simplified deploy script.

Secrets (API keys, tokens) should only be supplied via environment variables or your CI secret store—never commit them to the repository.

## Testing Matrix

The CI strategy exercises the stack from unit logic through containerized smoke tests:

- **Unit tests:** Every module contributes unit suites (pytest for Python, Jest/Vite for Node) that execute on each push/PR. Run `python3 -m pytest -q` at the root or the module-specific equivalents listed in the playbook.
- **Integration validator:** `scripts/integration_complete.py` orchestrates the Garden → Echo → Limnus → Kira pipeline, validating rituals, ledger chains, persona dynamics, and recovery paths. This scenario must pass before any coordinated release.
- **CLI smoke (Docker):** Containerized jobs build the toolkit, bring up Redis/Postgres via `docker compose`, and run key CLI workflows (`vesselos.py garden start`, `... echo summon`, `... kira validate`). The smoke harness also hits the collab server `/health` endpoint when enabled.
- **Collab loopback:** With `COLLAB_SMOKE_ENABLED=1`, CI performs a WebSocket round trip against the collaborative server to confirm Redis/Postgres wiring.
- **Matrix execution:** Workflows fan out across backends (e.g., in-memory vs FAISS for Limnus) and module combinations. Treat a fully green matrix as a release gate across the monorepo.

Reproducing locally: mirror the CI matrix by running module unit tests, invoking `scripts/integration_complete.py`, and (optionally) bringing up the Docker stack to execute smoke tests before pushing changes.

## README Improvement Backlog

- [ ] Embed rendered architecture diagrams (replace ASCII once stabilized).

## Appendix: Legacy Monorepo Generator

The historical VesselOS subtree generator remains available under `vesselos_unified_monorepo/`.

1. Enter the generator:
   ```bash
   cd vesselos_unified_monorepo
   ```
2. Offline scaffold (no network):
   ```bash
   ./scripts/vesselos_monorepo_consolidation.sh --offline --force
   ```
   Creates `vesselos_unified_monorepo/vesselos-monorepo/` with agents, firmware, shared libs, docker stack, and monorepo CI.
3. Verify:
   ```bash
   cd vesselos-monorepo
   ./scripts/verify_integration_enhanced.sh --tests
   ```
4. History-preserving imports:
   ```bash
   GITHUB_ORG=your-org ./scripts/vesselos_monorepo_consolidation.sh --force
   ```
5. Dry-run helper (no tree mutations):
   ```bash
   ./scripts/run_local_setup_and_verify.sh --tests
   ```
