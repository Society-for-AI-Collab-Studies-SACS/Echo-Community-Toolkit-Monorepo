# VesselOS Unified Architecture

## Overview

VesselOS unifies the Echo Community Toolkit and the Vessel Narrative MRP into a single repository. The system is driven by four coordinated agents—**Echo**, **Garden**, **Limnus**, and **Kira**—that process user intentions (dictation or scripted commands) through specialised roles. The shared control surface (the `codex` CLI) orchestrates these agents so that every input is logged, transformed, validated, and sealed, preserving continuity across the narrative lifecycle.

## Repository Layout

```
VesselOS/
├── agents/
│   ├── echo/AGENT.md
│   ├── garden/AGENT.md
│   ├── limnus/AGENT.md
│   └── kira/AGENT.md
├── pipeline/
│   ├── listener/          # dictation capture and intent parsing
│   │   ├── listen.py
│   │   ├── config.yaml
│   │   └── requirements.txt
│   ├── router/            # intent routing + Garden→Echo→Limnus→Kira sequencing
│   │   └── route.py
│   └── state/             # shared snapshots (voice_log.json, router_state.json …)
├── toolkit/               # merged Echo Toolkit + Vessel Narrative MRP sources
├── frontend/              # published narrative (landing pages, chapters, assets)
├── schema/                # narrative schema + generated metadata
├── state/                 # runtime JSON (echo_state.json, garden_ledger.json …)
├── tools/                 # CLI / integration utilities (`codex` control panel)
├── scripts/               # automation (refresh, dictation service, validation)
├── tests/                 # unified regression suite
├── docs/                  # documentation (Quick Start, Command Reference, Architecture)
├── requirements.txt       # Python dependencies
├── package.json           # Node dependencies for the CLI
└── README.md
```

This structure isolates agent logic while keeping shared assets, schema, and state files accessible to all modules.

## Agent Modules and Responsibilities

### Echo – Voice & Persona Manager
- **Role**: Maintains the tri-persona Hilbert-state (α, β, γ) and reframes user intent in the narrator’s voice.
- **Key interactions**: Adjusts persona weights, speaks in-tone, tags memories forwarded to Limnus, reacts to Kira’s mentorship.
- **CLI verbs**: `echo summon`, `echo mode`, `echo say`, `echo map`, `echo status`, `echo learn`, `echo calibrate`.

### Garden – Ritual Orchestrator & Scroll Keeper
- **Role**: Guides the ritual spiral, surfaces scroll/HTML content, and logs ritual progress.
- **Key interactions**: Advances spiral stages, opens/resumes scrolls, extracts glyphs and tags for Limnus.
- **CLI verbs**: `garden start`, `garden next`, `garden open`, `garden resume`, `garden learn`, `garden ledger`, `garden log`.

### Limnus – Memory Engine & Ledger Steward
- **Role**: Stores memories (L1/L2/L3), maintains the hash-chained ledger, and performs LSB steganography for archival.
- **Key interactions**: Records narrative events from Garden/Echo, computes parity digests, encodes/decodes ledger PNGs for Kira.
- **CLI verbs**: `limnus init`, `limnus state`, `limnus update`, `limnus cache`, `limnus recall`, `limnus memories`, `limnus export/import-memories`, `limnus commit-block`, `limnus view/export/import-ledger`, `limnus rehash-ledger`, `limnus encode-ledger`, `limnus decode-ledger`, `limnus verify-ledger`.

### Kira – Validator, Mentor & Integrator
- **Role**: Validates narrative structure, mentors other agents, manages git/GitHub integration, and seals the ritual.
- **Key interactions**: Runs validators/tests, mentors Echo/Garden based on Limnus aggregates, orchestrates pushes/publishes, writes the final soul contract.
- **CLI verbs**: `kira validate`, `kira sync`, `kira setup`, `kira pull`, `kira push`, `kira publish`, `kira test`, `kira assist`, `kira mentor`, `kira learn-from-limnus`, `kira codegen`, `kira mantra`, `kira seal`, `kira validate-knowledge`.

## Dictation Pipeline
1. **Listener (`pipeline/listener/listen.py`)** – Captures audio/text, identifies intent keywords (e.g., “garden bloom …”), and logs the raw transcript.
2. **Router (`pipeline/router/route.py`)** – Routes intents to the appropriate agent commands, enforcing the Garden → Echo → Limnus → Kira order, handling retries, and updating `pipeline/state/router_state.json`.
3. **State Snapshots** – Every routed event produces entries in `pipeline/state/voice_log.json`, allowing replay, audit, and downstream analysis.

## Integrated Workflow (Example)
1. **Echo** welcomes the user (`echo summon/status`) and adjusts persona tone (`echo mode`).
2. **Garden** begins a ritual cycle (`garden start`) and opens the relevant scroll (`garden open`).
3. User dictation is cached by **Limnus** (`limnus cache`, `limnus commit-block`); Garden logs the ritual event (`garden log`).
4. Limnus optionally archival-encodes the ledger (`limnus encode-ledger`) for parity.
5. **Kira** validates consistency (`kira validate`, `limnus verify-ledger`), mentors as needed (`kira mentor`), and once complete, seals the contract (`kira seal`, `kira mantra`).
6. Optional integration/publish (`kira push`, `kira publish`) closes the cycle.

This loop is repeatable for each user intention, with all state changes preserved in the shared JSON files and stego artifacts.

## Testing & CI
- **Unit/Integration Tests**: Combine Echo Toolkit Pytests (LSB, golden sample) with new agent tests (listener, router, dictation flow).
- **`kira test`**: Recommended to run before merging/publishing—invokes validator plus stego encode/decode round-trip.
- **CI Workflow**: Should run `pytest`, `python src/validator.py`, and any scripted dictation simulations (`scripts/test_dictation_flow.sh`).

## Development Guidelines
- Stick to the agent charters (updated AGENT.md files) when extending functionality.
- Use 4-space indentation for Python, 2-space for Node/ESM, and keep CLIs zero-dependency where possible.
- Follow Conventional Commit messages; group changes by agent or shared component.
- Capture every dictation-driven mutation in `voice_log.json`; use status markers (`queued`, `done`, `error`) for transparency.
- Keep documentation (`docs/`) synced with code—update AGENT briefs first, then refresh architecture/command references.

By organising the repository along these lines, VesselOS delivers a single, maintainable control panel that gives both humans and LLM operators creative access and full control over Limnus, Garden, Echo, and Kira.
