# Dictation & Self-Collaboration Architecture

This document outlines the shared dictation system that bridges the four
foundation repositories bundled inside **The Living Library**:

| Repository | Role in Dictation Workflow |
|------------|---------------------------|
| `echo-community-toolkit/` | Sentence-level tooling, memory helpers, and steganography primitives used by Limnus for long-term storage. |
| `vessel-narrative-MRP/` | Canonical 20-chapter narrative engine (schema builder + chapter generator) harvested by dictation workflows. |
| `The-Living_Garden-Chronicles/` | Rendered chapter templates and ritual scaffolding for Garden orchestration. |
| `kira-prime/` | Core agent engines (Garden, Echo, Limnus, Kira) and validation utilities invoked by the dispatcher. |

## Goals

1. **Shared Dictation Module** – Both the end user and Codex CLI agent
   can append turns to the same session, creating a transparent
   self-collaboration channel.
2. **MRP Integration** – Dictation sessions can trigger a full
   20-chapter run of the vessel-narrative system, harvesting content into
   the local library.
3. **Workspace Storage** – All transcripts and generated artifacts are
   persisted under `workspace/<id>/` for future recall or encoding.

## Component Layout

```
library_core/
├── dictation/
│   ├── __init__.py           # Public helpers
│   ├── session.py            # DictationSession + turn logging
│   └── pipeline.py           # Bridges to MRP / agent dispatcher
├── mrp/                      # Existing MRP helpers (façade wrappers)
├── collab/                   # Collaboration stubs (to be expanded)
└── interfaces/               # CLI exports (future: `prime dictation …`)

workspace/
└── <workspace_id>/
    ├── logs/dictation_<session>.json      # turn-by-turn transcript
    └── outputs/mrp/<session>/             # generated chapters + metadata
```

## Flow Overview

1. **Session Start**  
   `DictationSession.start()` records metadata (participants,
   workspace id, context) and prepares log files.

2. **Turn Logging**  
   `session.record_turn(role, text, tags)` appends an entry with ISO
   timestamp, source (`user` / `agent`), and optional tags (e.g.
   `stage: scatter`).

3. **Pipeline Trigger**  
   `DictationPipeline.run_full_cycle(session)` invokes the Vessel MRP
   scripts located in `vessel-narrative-MRP/src/`, ensuring the
   20-chapter narrative is rebuilt and copied into `workspace/<id>/outputs`.

4. **Agent Orchestration**  
   The pipeline will call into `kira-prime`’s agent interfaces:
   Garden → Echo → Limnus → Kira, mirroring the Phase 3 sequential flow.
   Echo-specific utilities may draw on `echo-community-toolkit`,
   while Limnus employs toolkit steganography for memory encoding.

## Next Steps

1. Implement `library_core/dictation/session.py` (turn model, logging,
   serialization).
2. Implement `library_core/dictation/pipeline.py` (wrappers around MRP
   scripts and agent dispatcher calls).
3. Expose CLI entry-points (`prime dictation start …`) hooking into the
   session manager and pipeline.
4. Expand collaboration features so the Codex CLI agent can consume the
   same session log for co-authoring loops.

Once these pieces are in place, we can introduce higher-level scripts
(`scripts/run_mrp_cycle.py`) that orchestrate full 20-chapter runs using
live dictation transcripts as seeds.

## Running a Cycle

After recording turns, trigger the 20-chapter build directly from the
repo root:

```bash
python scripts/run_mrp_cycle.py --workspace default --input "Seed insight"
```

The script will:

1. Create (or resume) a dictation session under the chosen workspace.
2. Log the optional `--input` seed as the first turn.
3. Execute `schema_builder.py` (unless `--no-schema` is supplied) and
   `generate_chapters.py` inside `vessel-narrative-MRP`.
4. Copy the generated MRP frontend and Living Garden Chronicle templates
   into `workspace/<id>/outputs/mrp/<session>/`.
5. Optionally run `kira-prime` validation when `--validate` is passed.

All transcript lines remain accessible via
`workspace/<id>/logs/dictation_<session>.jsonl`.
