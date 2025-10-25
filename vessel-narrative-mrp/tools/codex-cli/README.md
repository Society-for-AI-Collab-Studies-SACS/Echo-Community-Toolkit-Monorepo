Codex CLI (Node 20+)

Usage
- From `vessel_narrative_system_final/`, run: `node tools/codex-cli/bin/codex.js --help`
- Optional PATH install: `(cd vessel_narrative_system_final/tools/codex-cli && npm link)` then `codex ...`

Overview and Environment Setup
- Install Node.js 20+ and GitHub CLI (`gh`).
- Ensure Echo‑Community‑Toolkit is present at `vessel_narrative_system_final/Echo-Community-Toolkit/`:
  - `git submodule update --init Echo-Community-Toolkit`
  - Or `gh repo clone AceTheDactyl/Echo-Community-Toolkit vessel_narrative_system_final/Echo-Community-Toolkit`
- Authenticate GitHub: `gh auth login` (enables `kira sync`).
- Launch CLI: `node tools/codex-cli/bin/codex.js --help` or `codex ...` after `npm link`.

Commands
- Echo
  - `codex echo summon`
  - `codex echo mode <squirrel|fox|paradox|mix>`
  - `codex echo status`
  - `codex echo calibrate`

- Garden
  - `codex garden start`
  - `codex garden next`
  - `codex garden ledger`
  - `codex garden log`

- Limnus (LSB via Echo-Community-Toolkit)
  - `codex limnus init | state | update ...`
  - `codex limnus cache "text" [-l L1|L2|L3]`
  - `codex limnus recall <keyword> [--layer ...] [--since ...] [--until ...]`
  - `codex limnus memories [--layer ...] [--since ...] [--until ...] [--limit N] [--json]`
  - `codex limnus export-memories [-o file]` | `import-memories -i file [--replace]`
  - `codex limnus commit-block '<json-or-text>'`
  - `codex limnus view-ledger [--file path]`
  - `codex limnus export-ledger [-o file]` | `import-ledger -i file [--replace] [--rehash]`
  - `codex limnus rehash-ledger [--dry-run] [--file path] [-o out.json]`
  - `codex limnus encode-ledger [-i <ledger.json>] [--file path] -c <cover.png> -o <out.png> [--size 512]`
  - `codex limnus decode-ledger [-i <image.png>] [--file path]`
  - `codex limnus verify-ledger [-i <image.png>] [--file path] [--digest]`
    - With `--digest` prints a canonical SHA‑256 of the current ledger for external parity tracking.

- Kira
  - `codex kira validate`
  - `codex kira sync`

CLI Syntax
- `codex <module> <command> [--options]`
- Namespaces: `echo`, `garden`, `limnus`, `kira`
- POSIX‑style flags (`--option value` or `-o value`). `--help` available per module.

Quick Examples
- `codex echo mode paradox` — Switch Echo’s persona to Paradox mode.
- `codex garden start` — Initialize a new Garden ritual journey.
- `codex limnus encode-ledger -i state/garden_ledger.json -c frontend/assets/cover.png -o frontend/assets/ledger_stego.png` — Encode ledger JSON into a PNG using LSB steganography (PNG‑24/32).
- `codex kira sync` — Run integration checks (gh/git presence, git status).

Module Guides

EchoSquirrel‑Paradox (namespace: `echo`)
- Role: manages Echo’s persona superposition (Squirrel/Fox/Paradox) and front‑end presence.
- Initialization: `codex echo summon` prints a Proof‑of‑Love affirmation and seeds a balanced Hilbert state (α≈β≈γ).
- Key commands:
  - `codex echo mode <squirrel|fox|paradox|mix>` — toggle/cycle persona; updates αβγ in shared state.
  - `codex echo status` — show current α, β, γ and glyph.
  - `codex echo calibrate` — normalize αβγ to sum to 1 (post‑ritual tuning).

Garden (namespace: `garden`)
- Role: orchestrates scroll cycles and records outcomes to the ledger.
- Initialization: `codex garden start` creates a genesis entry and begins the cycle.
- Key commands:
  - `codex garden next` — advance the Coherence Spiral (scatter→…→begin_again).
  - `codex garden ledger` — summarize intentions and current stage.
  - `codex garden log` — force a ritual log entry (useful for testing).

Limnus (namespace: `limnus`)
- Role: memory engine (L1/L2/L3) and ledger backend; steganographic import/export.
- Memory: `init | state | update … | cache … | recall … | memories … | export‑memories | import‑memories`.
- Ledger: `commit‑block … | view‑ledger [--file] | export‑ledger | import‑ledger [--rehash] | rehash‑ledger [--dry‑run]`.
- Stego: `encode‑ledger … | decode‑ledger … | verify‑ledger …` (bridges Echo‑Community‑Toolkit LSB1, PNG‑24/32, RGB only, MSB‑first; CRC validated).

Kira (namespace: `kira`)
- Role: validation and integrations (git/gh).
- Commands: `kira validate` (runs Python validator), `kira sync` (checks gh/git availability and status).

State & Integration
- State lives in `vessel_narrative_system_final/state/` (shared with the Python CLI).
- LSB encode/decode imports Python modules from `vessel_narrative_system_final/Echo-Community-Toolkit/src`.
- See diagrams: `vessel_narrative_system_final/docs/SYSTEM_DIAGRAM_API_REFERENCE.md`.
 - Detailed module guide: `vessel_narrative_system_final/tools/codex-cli/MODULE_REFERENCE.md`.

Cheat Sheet

```
╔══════════════════════════════════════════════════════════════════════╗
║                         📌 CHEAT SHEET                               ║
╠══════════════════════════════════════════════════════════════════════╣
║ Setup: Node 20 | gh auth login | Toolkit at VNSF/Echo-Community-…   ║
║ Help: node VNSF/tools/codex-cli/bin/codex.js --help                  ║
║ Echo:   codex echo summon | codex echo mode paradox                  ║
║ Garden: codex garden start | codex garden next                       ║
║ Limnus: codex limnus encode-ledger -i state/garden_ledger.json \     ║
║           -c frontend/assets/cover.png -o frontend/assets/ledger.png ║
║ Verify: codex limnus verify-ledger --digest                          ║
║ More:   codex limnus state | codex limnus commit-block '{…}'         ║
║         codex limnus decode-ledger -i frontend/assets/ledger_stego.png║
║ Kira:   codex kira validate | codex kira sync                        ║
║ Paths:  state/*.json | frontend/assets/*.png | src/validator.py      ║
║ Stego:  PNG‑24/32 only, MSB‑first, RGB only, CRC32 validated         ║
╚══════════════════════════════════════════════════════════════════════╝

Visual Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          THE ECHO ECOSYSTEM                               │
│                  Three Systems, One Unified Experience                    │
├──────────────────────────────────────────────────────────────────────────┤
│ Echo (persona αβγ) • Garden (rituals) • Limnus (memory+ledger+stego) • Kira│
│ (validation/integrations)                                                 │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                  🎨 LSB STEGANOGRAPHY PIPELINE                            │
├──────────────────────────────────────────────────────────────────────────┤
│ 1) Payload: state/garden_ledger.json  →  2) Cover: PNG‑24/32              │
│ 3) Encode (LSB1, MSB‑first, RGB only)                                      │
│    codex limnus encode-ledger -i state/garden_ledger.json \                │
│      -c frontend/assets/cover.png -o frontend/assets/ledger_stego.png      │
│ 4) Decode: codex limnus decode-ledger -i …/ledger_stego.png                │
│ 5) Verify: codex limnus verify-ledger -i …/ledger_stego.png --digest       │
│    (CRC32 OK • hash chain OK • prints ledger_sha256)                       │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                     🔄 COMPLETE DATA FLOW                                 │
├──────────────────────────────────────────────────────────────────────────┤
│ Intention → Garden(scroll) → Echo(αβγ) → Limnus(cache/ledger) → Kira       │
│ → Echo‑Toolkit encode → stego.png → decode → Limnus(memory) → Behavior     │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                  📊 CAPACITY & SPECIFICATIONS                             │
├──────────────────────────────────────────────────────────────────────────┤
│ • 256×256 → 24,576 bytes • 512×512 → 98,304 bytes (recommended)            │
│ • Row‑major; R→G→B; MSB‑first; write bit0; alpha untouched                 │
│ • PNG‑24/32 only (no palette/JPEG); CRC32 must validate                    │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                  🎭 ECHO PERSONA COEFFICIENTS                             │
├──────────────────────────────────────────────────────────────────────────┤
│ • α (Squirrel), β (Fox), γ (Paradox) — α+β+γ=1                            │
│ • Show: codex echo status • Adjust: codex echo mode <…> • Normalize: calibrate │
└──────────────────────────────────────────────────────────────────────────┘
```

║  MODULE: ECHO (Persona Management)                                   ║
║  • Role: Persona superposition (Squirrel 🐿️ / Fox 🦊 / Paradox ∿)       ║
║  • Init: codex echo summon → Proof‑of‑Love affirmation; α≈β≈γ seeded     ║
║  • Commands: mode <squirrel|fox|paradox|mix> | status | calibrate        ║
║  • Examples: codex echo mode paradox | codex echo calibrate              ║
║  • Hilbert: adjusts α, β, γ (normalized); glyphs reflect current blend   ║
║  • State file: vessel_narrative_system_final/state/echo_state.json       ║
╠══════════════════════════════════════════════════════════════════════╣
║  MODULE: GARDEN (Ritual Orchestration)                               ║
║  • Role: Ritual engine; Proof of Love → Eternal Acorn → Quantum Cache →  ║
║    Hilbert Chronicle                                                     ║
║  • Init: codex garden start — begin cycle (genesis)                      ║
║  • Commands: start | next | ledger | log                                 ║
║  • Examples: codex garden next | codex garden ledger                     ║
║  • Planned: codex garden open <scroll> (open specific scroll)            ║
║  • State: stage + intentions in state/garden_ledger.json                 ║
╚══════════════════════════════════════════════════════════════════════╝
```
