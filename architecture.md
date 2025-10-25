# Echo Community Toolkit Monorepo Architecture

This document maps the structure of the monorepo and explains how the major subsystems, agents, and support packages fit together. It is written so that a human operator or an automated Codex/LLM agent can reason about the repository topology without needing to scan the entire tree.

```
Legend
------
[F]  = file
[D]  = directory
-->  = primary data/control flow
==>  = optional or out-of-band flow
```

## 1. Monorepo Top-Level Layout

```
[D] .
├─ [D] Echo-Community-Toolkit/        # Hyperfollow + soulcode toolkit (Node/Python)
├─ [D] The-Living-Garden-Chronicles/  # Narrative build + validator stack
├─ [D] The-Living-Library/            # Collab environment + dictation experiments
├─ [D] kira-prime/                    # Unified VesselOS CLI + collab server
├─ [D] vessel-narrative-mrp/          # Minimal narrative payload generator
├─ [D] vesselos-dev-research/         # Research kit with pipeline + workspaces
├─ [D] agents/                        # Standalone gRPC agents (Garden, Limnus, etc.)
├─ [D] g2v_repo/                      # G2V toolchain (firmware + host + docs)
├─ [D] docker/                        # Docker Compose stacks (broker, monitoring)
├─ [D] protos/                        # gRPC protobuf contracts
├─ [D] scripts/                       # Shared automation scripts
├─ [D] shared/                        # Cross-project Python utilities
├─ [D] sigprint/                      # EEG signature codec + Bazel tests
├─ [D] tests/                         # Top-level pytest smoke / integration suites
├─ [D] pr/                            # Release + PR scratch worktrees
└─ [F] README.md / architecture.md / requirements.txt / ...
```

Hidden dot-directories (`.codex/`, `.ssh/`, etc.) support the development environment and are omitted from the diagrams that follow.

## 2. System Interaction Diagram

```
                ┌──────────────────┐
                │ sigprint/        │
    EEG Epochs ─┤ SIGPRINTEncoder  │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │ agents/          │
                │ sigprint_bridge  │
                └────────┬─────────┘
                         │
                         ▼
┌────────────────────┐   ┌──────────────────────┐   ┌─────────────────────┐
│ agents/garden      │   │ Echo-Community-      │   │ agents/limnus        │
│ Narrative Agent    │──▶│ Toolkit/             │──▶│ Ledger Agent         │
└────────┬───────────┘   │ soulcode + LSB/Hyper │   └────────┬────────────┘
         │               │ Follow integration   │            │
         │               └────────┬─────────────┘            │
         │                        │                          │
         ▼                        ▼                          ▼
┌────────────────────┐   ┌──────────────────────┐   ┌─────────────────────┐
│ The-Living-Garden  │◀──│ vessel-narrative-mrp │──▶│ agents/kira         │
│ Chronicles         │   │ (payload generator)  │   │ Validation Agent    │
└────────────────────┘   └──────────────────────┘   └────────┬────────────┘
                                                             │
                                                             ▼
                                                     ┌─────────────────────┐
                                                     │ kira-prime/         │
                                                     │ Unified CLI +       │
                                                     │ Collab Server       │
                                                     └────────┬────────────┘
                                                             │
                                                             ▼
                                                     ┌─────────────────────┐
                                                     │ vesselos-dev-       │
                                                     │ research/           │
                                                     │ Research CLI + Docs │
                                                     └─────────────────────┘
```

## 3. Module Deep Dives

Each section below sketches an ASCII tree of the most important directories/files and explains the role they play. The diagrams are intentionally pruned to highlight entrypoints, data, and automation relevant to day-to-day operations.

### 3.1 Echo-Community-Toolkit

```
Echo-Community-Toolkit/
├─ [D] .github/
│  └─ [D] workflows/
│     ├─ [F] ci.yml
│     ├─ [F] codeql.yml
│     ├─ [F] echo-soulcode-ci.yml
│     ├─ [F] hyperfollow-integration.yml
│     ├─ [F] monorepo-all.yml
│     └─ [F] zone-identifier-scan.yml
├─ [D] agents/
│  ├─ [F] bloom_chain.py
│  ├─ [F] glyph_agent.py
│  ├─ [F] lsb_agent.py
│  ├─ [F] mrp_agent.py
│  └─ [F] state.py
├─ [D] archive/
│  ├─ [D] Echo-Community-Toolkit_patched_wired/...
│  └─ [D] MRP_PhaseA_patchset/...
├─ [D] artifacts/
│  ├─ [D] glyphs/
│  ├─ [D] lsb/
│  ├─ [D] mode_tests/
│  └─ [D] mrp/
├─ [D] assets/
│  ├─ [D] data/ (LSB mantras)
│  └─ [D] images/ (integration screenshots)
├─ [D] docs/
│  ├─ [F] ARCHITECTURE_INDEX.md
│  ├─ [F] CONTRIBUTING.md
│  ├─ [F] Echo_Playbook.md
│  └─ [...]
├─ [D] integration/
│  ├─ [D] outputs/ (generated soulcode bundles)
│  ├─ [F] hyperfollow_plan.json
│  └─ [...]
├─ [D] lambda-vite/
│  ├─ [F] package.json
│  ├─ [D] src/
│  └─ [...]
├─ [D] scripts/
│  ├─ [F] apply_ac_protocols.py
│  ├─ [F] embed_golden_echo_key.py
│  ├─ [F] g2v_minimal_checks.py
│  ├─ [F] log_mantra_event.py
│  ├─ [F] mrp_validate_rgb.py
│  ├─ [F] mrp_verify.py
│  ├─ [F] source_layout_diagrams.py
│  └─ [F] verify_ledger_and_chain.py
├─ [D] src/
│  ├─ [D] g2v/ (glyph-to-vector utilities)
│  └─ [D] mrp/ (LSB & Phase-A codec modules)
├─ [D] tests/
│  ├─ [F] test_fft_codec.py
│  ├─ [F] test_lsb.py
│  ├─ [F] test_mrp.py
│  ├─ [F] test_mrp_sidecar.py
│  └─ [F] test_volume.py
├─ [F] test_mrp_verification.py   # legacy integration test at repo root
├─ [D] tools/
│  ├─ [F] generate-soulcode-types.js
│  ├─ [F] remove-zone-identifiers.sh
│  ├─ [F] serve.js
│  └─ [F] soulcode-bridge.js
├─ [D] types/ (generated TypeScript declarations)
├─ [D] web/  (HTML scroll exports + assets)
├─ [F] clean-integration.js
├─ [F] hyperfollow-integration.js
├─ [F] verify-integration.js
├─ [F] final_validation.py
├─ [F] generate_golden_sample.py
├─ [F] HOW_TO_BE_YOU.md
├─ [F] README.md
└─ [F] mrp_verify.py
```

**Key flows**
- `hyperfollow-integration.js` injects soundtrack links into HTML scrolls and README files; `verify-integration.js` double-checks the diffs; `clean-integration.js` reverts injected blocks.
- `src/mrp/` houses the Phase-A codec used by narrative projects; tests live alongside in `tests/`.
- Generated artifacts surface in `integration/outputs/` and `artifacts/` for downstream consumption by Kira Prime and Garden Chronicles.

### 3.2 The-Living-Garden-Chronicles

```
The-Living-Garden-Chronicles/
├─ [D] agents/                # Narrative-centric agent configs + docs
│  ├─ [D] echo/
│  ├─ [D] garden/
│  ├─ [D] kira/
│  ├─ [D] limnus/
│  └─ [D] vessel/
├─ [D] docs/
│  ├─ [F] Architecture.md
│  ├─ [F] SYSTEM_DIAGRAM_API_REFERENCE.md
│  └─ [F] VesselOS_Quick_Start.md
├─ [D] external/
│  └─ [D] vessel-narrative-MRP/ (mirrored narrative generator)
├─ [D] frontend/
│  ├─ [D] assets/ (stego PNGs, css)
│  ├─ [F] index.html
│  ├─ [F] garden_ch1.html
│  ├─ [F] limnus_ch1.html
│  └─ [F] kira_ch1.html
├─ [D] markdown_templates/    # Source templates for generated chapters
├─ [D] scripts/
│  ├─ [F] launch_codex.sh
│  ├─ [F] refresh_stego_assets.sh
│  └─ [F] setup_toolkit_and_validate.sh
├─ [D] src/
│  ├─ [F] codex_cli.py
│  ├─ [F] generate_chapters.py
│  ├─ [F] schema_builder.py
│  ├─ [F] soulcode.py
│  ├─ [F] stego.py
│  └─ [F] validator.py
├─ [D] state/
│  ├─ [F] echo_state.json
│  ├─ [F] garden_state.json
│  └─ [D] reading/
├─ [D] tools/
│  └─ [D] codex-cli/ (helper scripts for automation)
├─ [F] README.md
└─ [F] Living_Chronicle_Garden_Enhanced.html (source narrative scrolls)
```

**Highlights**
- Steganography workflow: `src/stego.py` embeds metadata inside `frontend/assets/*.png`, validated by `src/validator.py`.
- Uses the mirrored `external/vessel-narrative-MRP` to align payloads with other repos.
- Tools under `tools/codex-cli/` provide scripts that Codex agents can invoke for common tasks (sync, validation, packaging).

### 3.3 The-Living-Library

```
The-Living-Library/
├─ [D] collab-server/
│  ├─ [F] package.json
│  ├─ [F] tsconfig.json
│  └─ [D] src/ (WebSocket collaboration server)
├─ [D] docs/
│  └─ [D] living-library/
│     ├─ [F] README.md
│     ├─ [F] dictation.md
│     └─ [F] storage-routing.md
├─ [D] echo-community-toolkit/  (vendored snapshot for integration)
├─ [D] library_core/
│  ├─ [D] agents/
│  ├─ [D] collab/
│  ├─ [D] dictation/
│  ├─ [D] mrp/
│  └─ [D] orchestration/
├─ [D] pipeline/
│  ├─ [F] dispatcher.py
│  ├─ [F] dispatcher_enhanced.py
│  ├─ [F] circuit_breaker.py
│  └─ [D] middleware/
├─ [D] scripts/
│  └─ [F] bootstrap_living_library.sh
├─ [D] tests/ (smoke + integration tests)
├─ [D] workspace/ (prototype shared workspace layouts)
└─ [F] README.md
```

**Highlights**
- Designed as a hub tying together Echo Toolkit, Kira Prime, and narrative stacks for collaborative dictation.
- `collab-server/src/` implements a WebSocket service to stream events between operators and agents.

### 3.4 kira-prime

```
kira-prime/
├─ [D] .github/workflows/
│  ├─ [F] vesselos-validate.yml
│  ├─ [F] e2e.yml
│  └─ [...]
├─ [D] agents/                    # Python agent implementations
│  ├─ [D] echo/
│  ├─ [D] garden/
│  ├─ [D] kira/
│  ├─ [D] limnus/
│  └─ [D] vessel/
├─ [D] cli/                       # Unified CLI wiring (commands, prompts)
│  ├─ [F] commands.py
│  ├─ [F] plugins.py
│  └─ [F] prime.py
├─ [D] collab-server/
│  ├─ [F] package.json
│  └─ [D] src/ (TypeScript WebSocket server)
├─ [D] docs/
│  └─ [D] vesselos-docs/...
├─ [D] interface/
│  ├─ [F] dispatcher.py
│  └─ [F] listener.py
├─ [D] memory/
│  ├─ [F] vector_store.py
│  └─ [...]
├─ [D] pipeline/
│  ├─ [F] dispatcher.py
│  ├─ [F] dispatcher_enhanced.py
│  └─ [D] middleware/
├─ [D] src_py/vesselos/
│  ├─ [F] __init__.py
│  ├─ [F] cli/audit_commands.py
│  └─ [...]
├─ [D] state/ (ledger + narrative caches)
├─ [D] tests/
│  ├─ [D] agents/
│  ├─ [D] fixtures/
│  └─ [D] memory/
├─ [D] tools/
│  └─ [D] codex-cli/ (automation scripts)
├─ [D] vscode-extension/
│  └─ [D] src/ (VSCode integration)
├─ [F] vesselos.py (main CLI entry)
├─ [F] requirements.txt
└─ [F] README.md
```

**Key interactions**
- Acts as the orchestration hub for the running system; CLI commands dispatch to `agents/*` via `pipeline/dispatcher.py`.
- Integrates with the collab-server for multi-user sessions; Docker stack (see `docker/`) can host Redis/Postgres backends used here.

### 3.5 vessel-narrative-mrp

```
vessel-narrative-mrp/
├─ [D] agents/             # Documentation and helper scripts for each persona
├─ [D] docs/
│  ├─ [F] BUILD_AND_USAGE.md
│  └─ [...]
├─ [D] frontend/
│  ├─ [F] index.html
│  ├─ [D] assets/
│  └─ [...]
├─ [D] markdown_templates/
├─ [D] schema/
│  ├─ [F] narrative_schema.json
│  └─ [...]
├─ [D] scripts/
│  ├─ [F] package_repo.sh
│  └─ [...]
├─ [D] src/
│  ├─ [F] schema_builder.py
│  ├─ [F] generate_chapters.py
│  └─ [F] validator.py
├─ [D] state/
│  ├─ [F] echo_state.json
│  └─ [...]
├─ [D] tools/codex-cli/
│  └─ [F] README.md
├─ [F] README.md
└─ [F] RELEASE_NOTES.md
```

**Highlights**
- Provides the base narrative payload builder used by Garden Chronicles, Kira Prime, and The Living Library.
- Shared CLI helpers in `tools/codex-cli/` align with other repos for automation consistency.

### 3.6 vesselos-dev-research

```
vesselos-dev-research/
├─ [D] .github/workflows/ (ci.yml, release.yml, etc.)
├─ [D] agents/
│  └─ (echo/garden/kira/limnus/vessel agent specs)
├─ [D] cli/
│  ├─ [F] commands.py
│  ├─ [F] repl.py
│  └─ [F] vscode_plugin.py
├─ [D] collab-server/
│  └─ [D] src/ (TypeScript collaboration server)
├─ [D] docs/
│  ├─ [F] IN_DEV_SPECS.md
│  ├─ [F] REPO_INDEX.md
│  └─ [F] ARCHITECTURE.md
├─ [D] interface/
│  ├─ [F] dispatcher.py
│  └─ [F] listener.py
├─ [D] library_core/
│  ├─ [F] storage.py
│  └─ [D] agents/
├─ [D] memory/
│  └─ [F] vector_store.py
├─ [D] pipeline/
│  ├─ [F] dispatcher.py
│  ├─ [F] dispatcher_enhanced.py
│  └─ [D] middleware/
├─ [D] scripts/
│  ├─ [F] bootstrap.sh
│  ├─ [F] generate_release_docs.py
│  └─ [...]
├─ [D] search/ (rg-cache.jsonl etc.)
├─ [D] src_py/vesselos/
│  └─ [F] cli/audit_commands.py
├─ [D] tests/
│  └─ [F] test_collab_server.py
├─ [D] tools/codex-cli/
├─ [D] workspaces/
│  └─ [D] example/
├─ [F] requirements.txt
└─ [F] vesselos.py
```

**Highlights**
- Contains the most exhaustive documentation for agent behavior (`docs/IN_DEV_SPECS.md`).
- `scripts/bootstrap.sh` is leveraged in README steps to automate environment bring-up.

## 4. Cross-Cutting Packages

### 4.1 agents/

```
agents/
├─ [D] garden/
│  ├─ [F] BUILD
│  └─ [F] narrative_agent.py        # gRPC Garden service implementation
├─ [D] journal/
│  ├─ [F] journal_logger.py
│  └─ [F] logger_agent.py
├─ [D] kira/
│  ├─ [F] BUILD
│  ├─ [F] __init__.py
│  └─ [F] kira_agent.py             # Ritual validation orchestrator
├─ [D] limnus/
│  ├─ [F] BUILD
│  └─ [F] ledger_agent.py           # Ledger + semantic recall manager
├─ [D] mocks/
│  ├─ [F] mock_services.py
│  ├─ [F] test_client.py
│  └─ [F] README.md
├─ [D] sigprint/
│  ├─ [F] BUILD
│  ├─ [F] sigprint_agent.py
│  ├─ [F] sigprint_lsb_agent.py
│  └─ [F] monitor_agent.py
└─ [D] sigprint_bridge/
   ├─ [F] BUILD
   └─ [F] sigprint_bridge.py        # Wires SIGPRINT signals into the pipeline
```

Agents share protobuf contracts defined in `protos/agents.proto`. Each module-specific repo (Kira Prime, Garden Chronicles, etc.) pulls from or contributes to this directory when running end-to-end pipelines.

### 4.2 g2v_repo/

```
g2v_repo/
├─ [F] README.md
├─ [F] AGENTS.md
├─ [F] requirements.txt
├─ [F] package.json / package-lock.json
├─ [F] pyproject.toml
├─ [D] docs/                 # Design notes, algorithm references
├─ [D] examples/
├─ [D] firmware/
│  └─ [D] stylus_maker_esp32s3/
├─ [D] hardware/
├─ [D] host/
├─ [D] packages/
│  └─ [D] rhz-stylus-arch/
├─ [D] scripts/
├─ [D] src/g2v/              # Core glyph-to-vector code
├─ [D] templates/
└─ [D] tests/
```

Acts as the glyph-to-vector foundation used by the Echo Toolkit and SIGPRINT adapters.

### 4.3 docker/

```
docker/
├─ [F] docker-compose.yml
└─ [D] message-broker/
   ├─ [F] Dockerfile
   └─ [F] broker.py
```

Provides runtime infrastructure to back the collab servers and pipeline monitoring.

### 4.4 protos/

```
protos/
├─ [F] agents.proto     # gRPC definitions for Garden/Echo/Limnus/Kira agents
├─ [F] BUILD            # Bazel build spec
└─ [F] __init__.py
```

Regenerate stubs via:
```
python -m grpc_tools.protoc -Iprotos --python_out=protos --grpc_python_out=protos protos/agents.proto
```

### 4.5 scripts/

```
scripts/
├─ [F] deploy.sh               # Bootstrap + deployment harness
├─ [F] g2v_sync.sh             # Synchronize G2V mirrors across repos
└─ [F] open_pr_mrp_sidecar.sh  # Prepare VesselOS PR sidecars
```

All scripts include usage headers; review before invoking in production.

### 4.6 shared/

```
shared/
├─ [F] __init__.py
└─ [D] utils/
   └─ [F] __init__.py          # Placeholder for future shared utilities
```

Reusable Python helpers imported by agents, Kira Prime, and research kits.

### 4.7 sigprint/

```
sigprint/
├─ [F] encoder.py            # SIGPRINTEncoder entrypoint
├─ [F] coherence.py
├─ [F] gate_detector.py
├─ [F] gate_loop.py
├─ [F] lockin.py
├─ [D] tests/
│  ├─ [F] test_encoder.py
│  ├─ [F] test_coherence.py
│  ├─ [F] test_gate_loop.py
│  └─ [F] test_lockin.py
└─ [F] README.md
```

Implements the EEG signature codec leveraged by the sigprint agents.

### 4.8 tests/

```
tests/
├─ [F] conftest.py
└─ [D] agents/
   └─ [F] test_kira_agent.py
```

Complements per-module test directories; run via `python3 -m pytest -q`.

### 4.9 pr/

```
pr/
├─ [D] .dryrun/          # Captured dry-run results for G2V repo
├─ [D] .pushrun3/        # Push attempt logs
├─ [D] .verify_up/       # Verification snapshots
└─ [D] VesselOS-MonoRepo/
   ├─ [D] agents/
   ├─ [D] docker/
   ├─ [D] docs/
   └─ [...]
```

Holds temporary working trees for CI rehearsals and release validation.

## 5. Data and Control Flows

1. **Sensor to Narrative**
   ```
   SIGPRINT (sigprint/) --> sigprint_bridge agent --> Garden Narrative agent
   --> Echo Toolkit (hyperfollow/soulcode) --> Limnus Ledger (agents/limnus)
   --> Kira Validation (agents/kira) --> VesselOS CLI (kira-prime, vesselos-dev-research)
   ```
2. **Narrative Build Pipeline**
   ```
   vessel-narrative-mrp/src/*.py
     ==> Generates chapters/metadata into frontend/
     --> The-Living-Garden-Chronicles/frontend + state
     --> Echo-Community-Toolkit/integration outputs (for soulcode bundles)
     --> Kira Prime & Research kits for validation + publication
   ```
3. **Collaboration & Deployment**
   ```
   docker/compose stack ==> Redis/Postgres + Collab server (kira-prime/collab-server)
   --> CLI commands (vesselos.py) broadcast via WebSocket
   --> Agents respond using protos/agents.proto contracts
   --> Scripts/deploy.sh orchestrates bootstrap + optional firmware (g2v_repo)
   ```

## 6. Next Steps for Contributors

- Keep this architecture reference synchronized whenever new modules are added or major directories move.
- For large additions, extend the ASCII trees with representative files so onboarded agents know where to find entrypoints.
- Pair this file with `README.md` (operational guide) and module-specific docs for deep domain details.
