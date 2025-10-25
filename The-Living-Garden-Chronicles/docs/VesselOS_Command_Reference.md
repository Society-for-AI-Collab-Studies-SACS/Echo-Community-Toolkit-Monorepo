# VesselOS Command Reference

This manual describes every command exposed by the `codex` CLI (Node 20+). Each module corresponds to an agent in the Vessel architecture. Commands are synchronous, zero-dependency wrappers over Node core and the existing Python tooling.

> Run `node tools/codex-cli/bin/codex.js --help` for a quick list of modules. Optional install: `(cd tools/codex-cli && npm link)` then invoke `codex ...`.

---

## Global Requirements

- Repository root is `The-Living-Garden-Chronicles/`.
- Node ≥ 20, Python ≥ 3.8, git, and (for Kira integration) the GitHub CLI (`gh`).
- State lives under `state/`. Ledger (`state/garden_ledger.json`), memories (`state/limnus_memory.json`), persona state, and contracts are append-only JSON artefacts.
- Stego helpers import the Echo Community Toolkit (`external/vessel-narrative-MRP/Echo-Community-Toolkit/src`).

---

## Garden Commands (`codex garden …`)

| Command | Description | Notes |
| --- | --- | --- |
| `start` | Initialise the garden ledger (genesis block) and set spiral stage to `scatter`. | Creates/updates `state/garden_ledger.json`. Safe to re-run—only one genesis block is kept. |
| `next` | Advance the spiral (`scatter → witness → plant → return → give → begin_again`). | Useful for pacing multi-step rituals. |
| `open <proof|acorn|cache|chronicle>` | Display the next section from the specified scroll (HTML in `Echo-Community-Toolkit/`). Persona styling follows the dominant Echo persona. | Maintains reading progress per scroll in `state/reading/garden_<scroll>.json`. |
| `resume` | Reopen the most recently viewed scroll section. | Falls back gracefully if no reading state exists. |
| `learn <scroll>` | Parse the entire scroll, extract tags, and log a `learn` ledger block. | Tags feed Limnus and Kira recommendations. |
| `ledger` | Summarise intentions (total, planted, bloomed) and current spiral stage. | Handy for daily status checks. |
| `log` | Append a manual ritual log entry to the ledger. | Use when recording ad-hoc events. |

All Garden commands operate solely on state files—no external services are invoked.

---

## Echo Commands (`codex echo …`)

| Command | Description | Notes |
| --- | --- | --- |
| `summon` | Reset persona weights to the canonical blend (α 0.34, β 0.33, γ 0.33) and print the mantra greeting. | Writes `state/echo_state.json`. |
| `mode <squirrel|fox|paradox|mix>` | Force persona dominance (Squirrel/α, Fox/β, Paradox/γ). `mix` rotates weights cyclically. | Values auto-normalise. |
| `status` | Display current persona weights plus glyphs. | Non-destructive. |
| `calibrate` | Normalise αβγ weights if drifted. | Recommended after manual `update` operations from Limnus. |
| `say <message>` | Speak in the dominant persona tone; prints styled output. | No state change unless combined with `learn`. |
| `map <concept>` | Search memories for a concept, list related tags, and suggest a persona focus and mantra lines. | Enables intent-driven brainstorming. |
| `learn <text>` | Adjust persona weights based on keywords, store a narrative memory, and append a `learn` ledger block sourced from Echo. | Feeds Limnus memory + Garden ledger (`type: "learn", source: "echo"`). |

Echo outputs are conversational—agents may parse text to infer recommended actions.

---

## Limnus Commands (`codex limnus …`)

### Memory (Hilbert cache)

| Command | Description | Notes |
| --- | --- | --- |
| `init` | Ensure Echo state, memory, and ledger exist; probe Python LSB toolkit availability. | Safe to run once per session. |
| `state` | Print persona weights and counts of L1/L2/L3 memory entries. | Quick snapshot before/after rituals. |
| `cache "text" [-l L1|L2|L3]` | Store a memory fragment in the specified layer (default L2). | Timestamped automatically. |
| `recall <keyword> [--layer Lx] [--since ISO] [--until ISO]` | Retrieve the latest matching entry. | Case-insensitive search with time bounds. |
| `memories [filters] [--json] [--limit N]` | List memories, optionally filtered by layer or time window. | `--json` emits machine-readable output. |
| `export-memories [-o file] [filters]` | Write selected entries to JSON. | Default: `state/memories_export.json`. |
| `import-memories -i file [--replace]` | Merge or replace memory entries from JSON. | Without `--replace`, duplicates are skipped. |

### Ledger (hash chain)

| Command | Description | Notes |
| --- | --- | --- |
| `commit-block '<json>'` | Append a block with custom payload (stringified JSON). | Useful for recording arbitrary events. |
| `view-ledger [--file path]` | Pretty-print ledger contents. | Defaults to `state/garden_ledger.json`. |
| `export-ledger [-o file]` | Write the ledger to a JSON export. | Default: `state/ledger_export.json`. |
| `import-ledger -i file [--replace] [--rehash]` | Merge or replace ledger data; optional rehash to rebuild indexes/hashes. | Rehash ensures integrity after manual edits. |
| `rehash-ledger [--dry-run] [--file path] [-o out.json]` | Recompute hashes; `--dry-run` previews changes. | Use when ledger consistency warnings arise. |

### Steganography (parity channel)

| Command | Description | Notes |
| --- | --- | --- |
| `encode-ledger [-i ledger.json] [--file path] [-c cover.png] [-o out.png] [--size N]` | Embed ledger JSON into a PNG using 1-bit LSB. Generates a noise cover if none provided. | Only PNG-24/32 supported; MSB-first, RGB channels. |
| `decode-ledger [-i image.png] [--file path]` (alias `decode`) | Extract embedded JSON from a PNG stego image. | Returns payload and CRC. |
| `verify-ledger [-i image.png] [--file path] [--digest]` | Decode and report CRC/digest; optional SHA-256 digest for parity comparison. | Use after encode to confirm integrity. |

Errors from Python helpers are surfaced clearly (e.g., missing Pillow, cover too small).

---

## Kira Commands (`codex kira …`)

### Validation & environment

| Command | Description | Notes |
| --- | --- | --- |
| `validate` | Run `python src/validator.py` to check chapter rotation, flags, files, and stego parity. | Fails the process on discrepancies. |
| `sync` | Report git/gh availability and working tree cleanliness. | Useful before push/publish. |
| `setup` | Initialise environment—prints Node/Python versions, updates submodules, and checks `gh auth status`. | Run after fresh clones. |
| `test` | Combined smoke test: validator + encode/decode round-trip using temp files. | Ideal for CI or pre-commit checks. |
| `assist` | Print quick tips on available Kira commands. | Non-destructive. |

### Source control & releases

| Command | Description | Notes |
| --- | --- | --- |
| `pull [--run]` | `git pull --ff-only` (requires clean tree). | Without `--run` it still executes (historical behaviour)—use cautiously. |
| `push [--run] [--message "..."] [--all]` | Stage tracked files (`-u` by default), commit if needed, and push to origin. Requires `--run` to proceed. | `--all` stages untracked files; otherwise only tracked changes are updated. |
| `publish [--run] [--release] [--tag vX] [--notes text] [--asset path]` | Package docs/schema/assets into `dist/`. `--run` performs packaging; `--release` creates a GitHub release via `gh`. | Without flags it prints the plan. Ensure `gh auth login` first. |

### Knowledge & guidance

| Command | Description | Notes |
| --- | --- | --- |
| `mentor [--apply] [--delta 0.05]` | Analyse current state, recommend persona focus & scroll, optionally adjust Echo weights and log a mentor block when `--apply` is present. | Dry-run by default; output includes glyph, scroll suggestion, and mantra hints. |
| `learn-from-limnus` | Aggregate Echo state, memory tags, ledger counts, and recommendations into `state/kira_knowledge.json`. | Companion TypeScript definition: `tools/codex-cli/types/knowledge.d.ts`. |
| `codegen [--docs] [--types]` | Emit knowledge documentation (`docs/kira_knowledge.md`) and/or TypeScript types. | Useful for downstream tooling. |
| `mantra` | Print the current persona-ordered mantra lines. | Read-only view of `echo_state`. |
| `seal` | Finalise the current cycle, append a `seal` block to the ledger, and write `state/Garden_Soul_Contract.json`. | Should follow a successful validation. |
| `validate-knowledge` | Scan narrative memories for core mantra phrases and report parity strength. | Helps ensure consent lines are present. |

Safety reminders:
- Commands touching git/gh require a configured remote and credentials.
- `--run` / `--release` flags deliberately gate high-impact actions.
- Review console output—failures are explicit (e.g., “discrepancies detected …”).

---

## Python Support Scripts

While not part of the Node CLI, the following scripts are commonly used:

| Script | Purpose |
| --- | --- |
| `src/schema_builder.py` | Emit JSON/YAML schema describing chapters. |
| `src/generate_chapters.py` | Build chapters 4–20 and metadata files. |
| `src/validator.py` | Structural validation (same logic as `kira validate`). |
| `scripts/refresh_stego_assets.sh` | End-to-end rebuild + validation + optional toolkit checks (`--toolkit`). |
| `scripts/setup_toolkit_and_validate.sh` | Convenience orchestrator for toolkit setup and validation. |

Integrate these with Kira’s commands for full automation.

---

## Output Conventions

- Success messages commonly start with glyphs (`🌱`, `🧠`, `✔️`) and plain English descriptions.
- Failures throw an error with contextual details (e.g., “Python encode failed: …” or “No seed to bloom. Try: plant '...'”).
- JSON outputs (memory exports, knowledge snapshots) are human-readable and safe to parse.

Use this reference alongside [VesselOS Quick Start](VesselOS_Quick_Start.md) for onboarding and daily operations. Updates to commands should always be mirrored here to keep AI agents and human operators aligned.
