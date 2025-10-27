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
   ./scripts/deploy.sh --full              # creates venv, installs pip deps, regenerates protobuf stubs
   npm --version || echo "Node not on PATH; install Node>=20 for toolkit scripts"
   ```
   - `scripts/deploy.sh` is menu-driven when invoked without flags—inspect [`scripts/deploy.sh`](scripts/deploy.sh) to tailor the bootstrap flow (e.g. skip firmware, rerun proto generation).

4. **Install per-module dependencies (batch)**  
   ```bash
   # Toolkit
   (cd Echo-Community-Toolkit && npm ci && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)
   # Audio-Visual authoring suite
   (cd audio-visual-script-repo && npm ci --workspaces && python3 -m pip install -r python/requirements.txt)
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

## Repository Constellation

Full ASCII trees and subsystem context live in [`architecture.md`](architecture.md).

```
Monorepo Root
├─ audio-visual-script-repo/      Audio-visual authoring UI + engine (Node/Python)
├─ Echo-Community-Toolkit/        Core hyperfollow + soulcode toolkit (Node/Python)
├─ echo_soulcode/                 Vendored Python package backing soulcode tests/tools
├─ The-Living-Garden-Chronicles/  Narrative generation + stego validator
├─ The-Living-Library/            Collab scaffolding + dictation experiments
├─ kira-prime/                    Unified CLI, agents, and collab server
├─ vessel-narrative-mrp/          Minimal narrative payload generator
├─ vesselos-dev-research/         Research-grade VesselOS CLI & docs
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

## Phase Roadmap (0–6)

LLM operators can progress through the implementation roadmap one phase at a time. Each guide captures objectives, deliverables, and test hooks so automation stays aligned with human context.

- **Phase 0 – Workspace Preparation:** Environment hygiene, SSH/GitHub validation, dependency baselines. → [`docs/phase-0-prep.md`](docs/phase-0-prep.md)
- **Phase 1 – Legacy Refresh:** Refactor LSB extraction into discrete parsers with golden-sample regression. → [`docs/phase-1-legacy-refresh.md`](docs/phase-1-legacy-refresh.md)
- **Phase 2 – Frame Infrastructure:** Introduce `MRPFrame`, multi-channel encode/decode, and capacity helpers. → [`docs/phase-2-frame-infrastructure.md`](docs/phase-2-frame-infrastructure.md)
- **Phase 3 – Integrity & ECC:** B-channel integrity payloads, XOR parity healing, corruption fixtures. → [`docs/phase-3-integrity-ecc.md`](docs/phase-3-integrity-ecc.md)
- **Phase 4 – Ritual & Ledger:** Implement ritual gating and append-only ledger logging for encode/decode. → [`docs/phase-4-ritual-ledger.md`](docs/phase-4-ritual-ledger.md)
- **Phase 5 – Polish & UX:** Documentation uplift, CLI ergonomics, and ritual/channel visualisation. → [`docs/phase-5-polish-ux.md`](docs/phase-5-polish-ux.md)
- **Phase 6 – Guardrails & Roadmap:** CI guardrails, corruption automation, and future ECC/multi-image design notes. → [`docs/phase-6-guardrails-roadmap.md`](docs/phase-6-guardrails-roadmap.md)

Each phase guide lists the commands to run, fixtures to prepare, and criteria for declaring the phase complete. Treat them as living specs—update the docs when new insights land.

## Continuous Integration

The consolidated workflow at [`.github/workflows/ci.yml`](.github/workflows/ci.yml) now drives six parallel checks on every push:

- **audio-visual** – installs workspaces under `audio-visual-script-repo`, runs lint/build/test for the authoring suite.
- **echo-toolkit** – executes `npm ci`, toolkit integration checks, and the Python parity/LSB regression suite.
- **kira-prime** – validates the VesselOS CLI, agent hand-off scripts, and shared protobuf stubs.
- **living-garden** – runs the narrative chronicle fixtures and stego validation regressions.
- **monorepo-smoke** – provisions the root virtualenv (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`) and executes `python -m pytest -q`.
- **vesselos-research** – boots the research workspace and ensures its CLI sanity commands pass.

Mirror the CI locally before opening a PR:

```bash
# Root smoke + stego suites
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q

# Module-specific runners
./scripts/ci/run_toolkit_ci.sh
./scripts/ci/run_kira_ci.sh
./scripts/ci/run_chronicles_ci.sh
./scripts/ci/run_research_ci.sh
```

Remember to refresh the shared deps when editing parity logic or codecs:

```bash
.venv/bin/pip install -r requirements.txt
python -m grpc_tools.protoc -Iprotos --python_out=protos --grpc_python_out=protos protos/agents.proto
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

### Audio-Visual Script Suite (`audio-visual-script-repo/`)
- **Purpose:** End-to-end authoring surface for waveform editing, persona-aware TTS synthesis, and script packaging.
- **Setup:**  
  ```bash
  cd audio-visual-script-repo
  npm ci --workspaces
  python3 -m pip install -r python/requirements.txt
  ```
- **Core commands:**  
  - Backend checks: `npm run lint --workspace backend && npm run type-check --workspace backend`  
  - Frontend checks: `npm run lint --workspace frontend && npm run type-check --workspace frontend`  
  - Build bundles: `npm run build --workspace backend && npm run build --workspace frontend`  
  - Python engine tests: `(cd python && python -m pytest -q)`
- **Docs:** The workspace README and inline `docs/` folder capture roadmap, persona mapping, and UI flow sketches.

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
- **Docs:** See `README.md`, `agents/README.md`, and `docs/` for deep dives.

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
- `scripts/ci/run_*.sh` – CI entrypoints for Toolkit, Kira Prime, Garden Chronicles, and Research (mirrors the Monorepo CI matrix locally).
- Docker helpers: `(cd docker && docker compose up -d)` brings Redis/Postgres + collab server online.

> Tip: all scripts support `--help` or inline usage comments; inspect them before running against production data.

## CI Status & Quicklinks

**Badges** – Each workflow surfaces the latest `main` branch health. The aggregate `ci.yml` job fans out across Node and Python suites (audio-visual workspaces, Toolkit, Kira Prime, Garden Chronicles, Research kit, and root smoke tests); module-specific workflows stay available for targeted reruns.
- **Monorepo aggregate:** [![Monorepo CI](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/ci.yml)
- **Echo-Community-Toolkit:** [![Toolkit CI](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/echo-toolkit-ci.yml/badge.svg?branch=main)](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/echo-toolkit-ci.yml)
- **Kira Prime:** [![Kira CI](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/kira-prime-ci.yml/badge.svg?branch=main)](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/kira-prime-ci.yml)
- **Living Garden Chronicles:** [![Chronicles CI](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/living-garden-ci.yml/badge.svg?branch=main)](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/living-garden-ci.yml)
- **VesselOS Dev Research:** [![Research CI](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/ci.yml/badge.svg?branch=main&job=vesselos-research)](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/ci.yml?query=workflow%3A%22Monorepo+CI%22)

**Actions quicklinks** – Shortcut filters for the repository Actions tab:

| Module | Actions Dashboard |
| --- | --- |
| Monorepo aggregate | <https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions?query=workflow%3A%22Monorepo+CI%22> |
| Echo-Community-Toolkit Monorepo | <https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions> |
| Kira Prime CLI | <https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions?query=workflow%3AKira> |
| The Living Garden Chronicles | <https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions?query=workflow%3AGarden> |
| VesselOS Dev Research | <https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/ci.yml?query=workflow%3A%22Monorepo+CI%22+job%3Avesselos-research> |

Use the pre-applied filters to reach module-specific workflow history quickly. Keep every module green before coordinating cross-stack releases.

The full roadmap for enhancing module workflows, environment hygiene, and test coverage lives in [`docs/integration-enhancement-plan.md`](docs/integration-enhancement-plan.md).

See [`docs/echo-harmonizer.md`](docs/echo-harmonizer.md) for the complete Echo Harmonizer integration validator specification, [`docs/echo-harmonizer.yaml`](docs/echo-harmonizer.yaml) for the structured rails metadata, and [`docs/echo-harmonizer-rails-compliance.md`](docs/echo-harmonizer-rails-compliance.md) for a Rails compliance summary.

## Configuration Reference

Environment variables keep secrets and deployment toggles out of source control. Copy [.env.sample](.env.sample) to `.env` (or `.env.integration`, `.env.production`, etc.) and define values locally, then source the file or let your process manager pick it up. Never commit concrete `.env` files—use CI secrets for shared automation.

### Agent Environment Variables

| Agent | Variable | Purpose |
| --- | --- | --- |
| Garden (`agents/garden/narrative_agent.py`) | – | No overrides required; relies on workspace-local state. |
| Echo (`agents/echo/echo_agent.py`) | – | No overrides required. |
| Limnus (`agents/limnus/ledger_agent.py`) | `KIRA_VECTOR_BACKEND` | Selects the semantic backend (e.g. `faiss`, defaults to in-memory). |
|  | `KIRA_VECTOR_MODEL` | Overrides the embedding model used for vectors. |
|  | `KIRA_SBERT_MODEL` | Legacy alias for the SentenceTransformer model (default `all-MiniLM-L6-v2`). |
|  | `KIRA_FAISS_INDEX` | Filesystem path for the FAISS index when that backend is active. |
|  | `KIRA_FAISS_META` | Filesystem path for FAISS metadata (IDs, dimensions). |
| Kira (`agents/kira/kira_agent.py`) | `GH_TOKEN` / `GITHUB_TOKEN` | GitHub token for release/publish flows executed via `gh`. |
| Journal (`agents/journal/journal_agent.py`)\* | – | No environment configuration required today. |
| Sigprint Bridge (`agents/sigprint_bridge/bridge_agent.py`)\* | – | No environment configuration required today. |

\* Planned/auxiliary agents operating only on local state and CLI flags.

All agents read/write under `workspaces/<id>/state/`. Follow the same `UPPER_SNAKE_CASE` convention when adding new toggles.

### Script & Service Environment Variables

| Script / Service | Variable | Purpose & Default |
| --- | --- | --- |
| **Bootstrap** (`scripts/bootstrap.sh`) | `PYTHON_VERSION` | Python version used when creating the virtualenv (default **3.10**). |
|  | `NODE_VERSION` | Node.js version required for toolkit automation (default **20**). |
| **Deploy** (`scripts/deploy_to_production.sh`)\* | `ENVIRONMENT` (arg) | Deployment target name (for example **"production"**). Defaults to **production** when omitted and labels the systemd service runtime. |
|  | *(others: internal)* | Internal variables such as `WORKSPACE_ROOT` and `SERVICE_USER` are defined inside the script. |
| **Collab Server** (`kira-prime/collab-server/src/server.ts`) | `PORT` | HTTP/WebSocket port (default **8000**). |
|  | `COLLAB_REDIS_URL` | Redis connection URL (default **redis://localhost:6379/0**). |
|  | `COLLAB_POSTGRES_DSN` | Postgres DSN (default **postgresql://vesselos:password@localhost:5432/vesselos_collab**). |
| **CI toggles** | `COLLAB_SMOKE_ENABLED` | When set to `1`, runs Dockerized collab smoke tests in CI. |

\* Part of the Kira Prime deployment scripts; adapt if using a simplified flow.

## Testing Matrix

CI validates the stack across several layers:

- **Unit suites:** Every module contributes unit tests (pytest, Jest/Vite) that run on each push/PR. Locally run `python3 -m pytest -q` at the root or use module-specific commands from the playbook.
- **Integration validator:** `scripts/integration_complete.py` exercises the Garden → Echo → Limnus → Kira ritual, asserting ledger hash chains, persona coherence, and recovery behavior.
- **CLI smoke (Docker):** Containerized jobs build the toolkit, bring up Redis/Postgres via `docker compose`, execute representative CLI commands (`vesselos.py garden start`, `... echo summon`, `... kira validate`), and hit the collab server `/health` endpoint.
- **Collab loopback:** With `COLLAB_SMOKE_ENABLED=1`, CI performs a WebSocket round trip to confirm the collab server, Redis, and Postgres integrate correctly.
- **Matrix coverage:** Workflows fan out across configurations (e.g. in-memory vs FAISS backends). Treat an all-green matrix as the release gate.

Reproduce locally by running unit suites, invoking `scripts/integration_complete.py`, and optionally bringing up the Docker stack for smoke tests before opening a PR.

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
