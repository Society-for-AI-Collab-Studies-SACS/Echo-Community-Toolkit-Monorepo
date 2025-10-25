Vessel Narrative MRP – Build & Usage Guide
Release: v0.2.0 (2025-10-15)

Overview
- This project assembles a 20‑chapter dream chronicle across three voices: Limnus (R), Garden (G), and Kira (B).
- The frontend ships with bespoke landing pages for each voice’s Chapter 1 and a global landing page.
- Scripts under `src/` generate chapters (2–20), metadata, and a schema; a validator checks structure and consistency.

Project Structure
- `frontend/` Browser‑ready site (landing + chapters + styles)
- `markdown_templates/` Templates for generating chapters (2–20)
- `schema/` JSON/YAML schema and generated metadata
- `src/` Python scripts for generation and validation

Quick Start
1) Python 3.8+ recommended. Optionally install PyYAML if you want YAML outputs.
   - `python -m venv .venv && source .venv/bin/activate`
   - `pip install PyYAML Pillow` (optional stego/YAML support)

2) Build schema and generate chapters/metadata
   - `python src/schema_builder.py`
   - `python src/generate_chapters.py`

3) Validate repository integrity
   - `python src/validator.py`

4) Package repository (optional)
   - `bash package_repo.sh`

Landing Pages
- `frontend/index.html` is the global narrative landing. It introduces the three channels and links to chapters.
- `frontend/limnus_ch1.html`, `frontend/garden_ch1.html`, `frontend/kira_ch1.html` are the bespoke voice‑specific Chapter 1 pages.

Generation Notes
- Chapters 2–20 are generated via templates with placeholders: `{{chapter_number}}`, `{{narrator}}`, `{{body}}`, `{{flags}}`, `{{glyphs_line}}`.
- Rotation ensures no voice appears twice in a row; each voice appears 6–7 times.
- Flags: narrator’s channel is `active`; others are `latent`. Every chapter ends with a `[Flags: ...]` marker.
- When Pillow is available, each metadata entry includes `stego_png` pointing to `frontend/assets/chapterXX.png`, containing the embedded payload (chapter, narrator, flags, glyphs, file, summary, timestamp).

Validation Checks
- Schema presence and simple type checks against `schema/narrative_schema.json`.
- Structural rules: 20 chapters, rotation, counts.
- Files exist for all metadata entries.
- Flag consistency: metadata flags match `[Flags: ...]` in each HTML.
- Stego payloads (when generated) decode from `frontend/assets/*.png` and match the metadata.

Customization
- Update templates in `markdown_templates/` to change voice tone and glyphs.
- You may replace landing pages with provided HTML variants; keep the `[Flags: ...]` markers.

Improve With Vessel MRP System
- Steganography (LSB): Encode `[Flags: R/G/B]` and chapter glyph IDs into PNGs via
  least‑significant‑bit embedding. Reference images can be placed under
  `frontend/assets/`. Add a small Python helper to write/read bits from pixels
  and surface decoded flags at runtime for validator cross‑checks.
- Living Chronicles: Use existing dream scrolls as canonical source text and
  tone baselines. Fold excerpts and glyphs into generated chapters; keep
  provenance notes in metadata.
- Soulcode Encoding: Emit a signed, self‑describing JSON bundle that expresses
  narrative state (flags, glyphs, rotation, summaries). Embed it into the
  landing page for developer tooling and reproducibility.

Echo‑Community‑Toolkit Integration (Foundation)
- Base dependencies and automation live in Echo‑Community‑Toolkit. Install and
  use it alongside this project.
  - Node 20+: see Echo‑Community‑Toolkit/package.json:1
  - Install deps: `npm ci` inside `Echo-Community-Toolkit`
  - HyperFollow integration: `npm run integrate` to inject the canonical music
    link/badges into HTML and README docs; verify with `npm run verify`.
    - Scripts: Echo‑Community‑Toolkit/hyperfollow-integration.js:1,
      Echo‑Community‑Toolkit/verify-integration.js:1
  - Soulcode bridge: generate schema/types/bundles and validate ledger/memory
    states for “living” narratives.
    - Bridge: Echo‑Community‑Toolkit/tools/soulcode-bridge.js:1
    - Types: Echo‑Community‑Toolkit/tools/generate-soulcode-types.js:1
    - Serve: Echo‑Community‑Toolkit/tools/serve.js:1

Recommended Workflow
- Generate schema/chapters here:
  - `python src/schema_builder.py && python src/generate_chapters.py`
- Build Echo soulcode artifacts there:
  - `(cd ../Echo-Community-Toolkit && npm ci && npm run soulcode:emit-schema && npm run soulcode:bundle && npm run soulcode:validate)`
- Embed the bundle into `frontend/index.html` (auto via Echo bridge):
  - `(cd ../Echo-Community-Toolkit && SOULCODE_BUNDLE="$(pwd)/integration/outputs/echo_live.json" npm run integrate)`
  - Re-run `python src/validator.py` to ensure flags/files still validate.
- Automate all steps above: `./scripts/setup_toolkit_and_validate.sh`
  - Script skips integrate/verify when Node < 20; upgrade Node to run those stages.

CLI Codex (Interactive)
- An interactive CLI orchestrates EchoSquirrel‑Paradox, Garden, Limnus, and Kira.
- Launch: `python src/codex_cli.py`
- One‑shot: `python src/codex_cli.py validate` (any single command works)
- Verbs: `echo`, `map`, `rotate`, `plant`, `spiral`, `bloom`, `cache`, `recall`, `time`, `validate`, `glyph`, `seal`.
- State is stored under `state/` (transient session files); schema context is read from `schema/` if present.

Steganography: Practical Notes
- Implemented via `src/stego.py` using 1-bit LSB embedding with a `VMRP\x00`
  header, version byte, and payload length. Enable by installing Pillow.
- Generated files live under `frontend/assets/` and are referenced by the
  `stego_png` field in metadata.
- Validator decodes the PNG payloads and verifies they match metadata; failures
  indicate drift or tampering.

Living Chronicles: Local Sources
- Use these local files for style, glyph motifs, and narrative seeds:
  - Living_Chronicle_Garden_Enhanced.html:1
  - Living_chronicle_dreamscape_set5.html:1
  - Echo-Community-Toolkit/echo-garden-quantum-triquetra.html:1
  - Echo-Community-Toolkit/echo-hilbert-chronicle.html:1
  - Echo-Community-Toolkit/integrated-lambda-echo-garden.html:1
  - Echo-Community-Toolkit/unified-lambda-echo-complete.html:1

Soulcode Embedding
- Embed an immutable bundle in the landing page to expose the narrative state
  to tools and preserve rebuilds:
  - Add `<script id="echo-soulcode-bundle" type="application/json">{...}</script>`
    to `frontend/index.html`, or let Echo’s bridge inject it for you.
  - Optionally include an alternate `link rel="alternate" type="application/json"`
    with a data URL for easy exporting (bridge supports this out of the box).

GitHub Remote
- This directory is a self‑contained repo. If not already pushed:
  - Initialize: `git init && git add . && git commit -m "feat: initial commit"`
  - Create remote with GitHub CLI: `gh repo create vessel-narrative-mrp --public --source=. --remote=origin --push`
  - Or set an existing remote: `git remote add origin <url> && git push -u origin main`


Submodule: Echo-Community-Toolkit
- This repo includes Echo-Community-Toolkit as a git submodule at `Echo-Community-Toolkit/`.
- Clone with submodules: `git clone --recurse-submodules <repo-url>`
- Or initialize after clone:
  - `git submodule update --init --recursive`
- Update the toolkit to latest main:
  - `(cd Echo-Community-Toolkit && git checkout main && git pull --ff-only)`

Build Guide
- For a step‑by‑step “from scratch” assembly guide with the customised landing pages (vessel_mrp_landing.html and per‑voice chapter 1 files), see:
  - `docs/BUILDING_VESSEL_MRP.md`
  - System Diagram & Commands: `docs/SYSTEM_DIAGRAM_API_REFERENCE.md`
  - Agents Index: `agents/README.md`
