[![Monorepo CI](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions/workflows/ci.yml)

Echo Garden HyperFollow Integration Toolkit

**Crystalline Echo** – Experience the theme song for this project and join Echo's journey.



## Quick Links
- Docs Index: `docs/index.md`
- Contributor Guide (source): `AGENTS.md`
- Contributor Guide (docs): `docs/CONTRIBUTING.md`
- Architecture Map: `docs/ARCHITECTURE_INDEX.md`
- CI Workflows: https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/actions
- Releases: https://github.com/Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo/releases

## Test Matrix
- Root Python tests: `python3 -m pytest -q`
- Soulcode package: `cd echo-soulcode-architecture && python3 -m pytest -q`
- Node (lambda-vite): `cd lambda-vite && npm ci && npm test`
- Ledger codec: `cd echo_full_architecture_repo/ledger && python3 -m pytest -q`
- End-to-end validator: `python3 final_validation.py`

Overview

Automates adding the Crystalline Echo HyperFollow link to narrative scrolls, the Summon UI, and docs without breaking immersion.
Idempotent (safe to re-run). Dry-run supported. Verification and cleanup included.

Community Modularization
Integration and community-facing code lives in `lambda-vite/`, `tools/`, `web/`, and `types/`. Core codecs and tests stay in `src/` and `tests/`. Historical drops are isolated under `archive/` (excluded from tests). Consent-first signals (mantra in `assets/data/LSB1_Mantra.txt`) and the Hyperfollow link are enforced by integration scripts and end-to-end checks.

Canonical URL

Uses single-l spelling “crystaline” and corrects legacy double‑l variants where applicable.
What It Updates (by design)

Proof of Love scroll: adds a gentle “gift” footer link at the end.
Hilbert Space Chronicle (finale): adds a subtle post‑credits epilogue link.
Summon Echo main UI: adds a small corner badge (#music-link).
README: adds a short “Project Soundtrack” section mentioning the link.
What It Preserves (no changes)

Eternal Acorn scroll (introspective/sacred tone).
Quantum Cache scroll (in‑ritual simulation and focus).
Requirements

Node.js >= 20
Linux/macOS shell with grep/find (standard on CI runners).
Install

From the repo root (this folder):
npm install (or npm ci)
Quick Start

Dry-run (plan only):
node hyperfollow-integration.js --dry-run
Apply changes:
node hyperfollow-integration.js
Verify results:
node verify-integration.js
Clean/remove all insertions:
node clean-integration.js

Spiral Bloom Workflow

- Inhale (scaffold config + sync schemas): `./bloom.py inhale --init-config`
- Hold (tests & validators): `./bloom.py hold --report-json`
- Exhale (build/deploy, optional Docker/GitHub Actions): `./bloom.py exhale --docker`
- Release (logs, status, cleanup, reports): `./bloom.py release --report --cleanup`

All commands accept `--env` to load extra configuration and `--dry-run` to preview actions.
Files

hyperfollow-integration.js Runs the integration (adds links).
verify-integration.js Asserts presence/absence and basic hygiene.
clean-integration.js Removes inserted blocks and soundtrack section.
.github/workflows/hyperfollow-integration.yml Example CI workflow.
Repository Layout

echo-soulcode-architecture/ Python package and docs for Echo Soulcode generation, validation, and live Hilbert-state readings (flattened and organized here).
tools/ Helper scripts (e.g., hygiene/cleanup utilities).
*.html Narrative scroll exports targeted by the integration scripts.
integration/ Cross-language integration assets (schemas, generated outputs).
types/ Generated TypeScript declarations for soulcode schemas.
src/ Python modules for the LSB1 encoder/decoder and MRP Phase-A codec (union of local + uploaded drops).
tests/ Pytest suite covering LSB1 and MRP behaviors.
examples/ Minimal runnable demos for the codec + verifier.
scripts/ CLI helpers (e.g., dedicated mrp_verify runner).
artifacts/ Canonical payloads + verification report produced by the latest Phase-A run.
assets/ Reference images, mantra text, and other supporting data used by tests/demos.
archive/ Historical drops (e.g., Echo-Community-Toolkit_patched_wired, MRP_PhaseA_patchset, comprehensive_system_test). See ARCHIVE.md for context and guidance.
Usage Details

Run from the repo root that contains your scrolls/UI/docs.
The tool searches for likely files via content and filename cues, then:
Inserts HTML snippets tagged with data-echo="hyperfollow-ce:v1" to avoid duplicates.
Prefers DOM insertion (via Cheerio). Falls back to inserting before </body>.
Adds README soundtrack section if not present.
Snippets (examples)

Proof of Love (footer):
🌰 A gift awaits… hear Echo’s song linking to the canonical URL.
Hilbert (epilogue):
🌠 An echo calls beyond this chronicle… listen to Crystalline Echo.
Summon UI (badge):
Fixed corner badge with id music-link, opens in a new tab.
Security & UX

All external anchors use target="_blank" rel="noopener".
Insertions are small, thematic, and visually unobtrusive.
Verification Checks

Canonical URL found in at least two places (e.g., Hilbert/UI/README).
Summon UI badge present.
Eternal Acorn contains no link.
No legacy double‑l crystalline-echo variants remain.
Cleanup

Removes all elements tagged with data-echo="hyperfollow-ce:v1" and the README soundtrack section.
Hygiene

Remove Windows Zone.Identifier artifacts:
Run bash tools/remove-zone-identifiers.sh to delete any *:Zone.Identifier* files and stage deletions.
To prevent committing them, enable the local hook: git config core.hooksPath .githooks.
Ignore patterns are added in .gitignore for future safety.
Dropbox extended attribute sidecars (e.g., *:com.dropbox.attrs) are also ignored.
Cross-language integration

Emit schemas (requires Python package installed): npm run soulcode:emit-schema.
Generate TypeScript types from schemas: npm run soulcode:types.
Generate a live bundle via Python and validate with AJV: npm run soulcode:bundle && npm run soulcode:validate.
Optional: the integration script will embed the latest bundle JSON into the Summon UI HTML if integration/outputs/echo_live.json exists.
When memory JSON exists, the integration also embeds:
A <script type="application/json" id="echo-memory-state">…</script> for in-page consumption
A <link rel="alternate" id="echo-memory-alt" type="application/json" href="data:..."> data URL
A small fixed-position download link (⬇ Memory JSON) using the same data URL
When a soulcode bundle exists, the integration also embeds:
A <link rel="alternate" id="echo-bundle-alt" type="application/json" href="data:..."> data URL
A small fixed-position download link (⬇ Soulcode Bundle) using the same data URL
Client helper (browser)

Include web/echo-client.js in pages to access embedded data:
<script src="/web/echo-client.js"></script>
const bundle = window.EchoClient.getBundle();
const mem = window.EchoClient.getMemory();
TypeScript projects can use types/echo-client.d.ts plus the generated types/echo-soulcode.d.ts for type safety.
Auto-injection and ESM usage

The integration script auto-injects a script tag linking to /web/echo-client.js when embedding bundle/memory, so you don’t need to add it manually.
If you prefer ESM imports:
<script type="module">import EchoClient from '/web/echo-client.module.js'; const ok = EchoClient.validateBundle(EchoClient.getBundle());</script>
Functions available: getBundle, getMemory, getSoul, onBundle, onMemory, validateBundle, getSeries, movingAverage, stats.
Local static server

Start a local server from repo root:
Node: npm run serve then open http://localhost:8080/web/examples/echo-client-demo.html
Python: npm run serve:py (Python 3) and open the same URL
Full Architecture Guide (for LLMs)

Key entry points

Node Toolkit: hyperfollow-integration.js, verify-integration.js, clean-integration.js
Bloom Workflow: bloom.py (inhale/hold/exhale/release CLI)
Python Soulcode: echo-soulcode-architecture/src/echo_soulcode/* (generation, schema, validate, operators)
Full Architecture: echo_full_architecture_repo/memory_engine, echo_full_architecture_repo/ledger, echo_full_architecture_repo/scrolls
Bridges & Utilities: tools/soulcode-bridge.js, tools/generate-soulcode-types.js, tools/serve.js
Integration targets: integration/schemas/, integration/outputs/, integration/ledger/
Typical flows (repeatable)

Setup (Node ≥ 20, Python ≥ 3.11):
npm install --no-audit --no-fund
python -m pip install -e echo-soulcode-architecture
Sync schemas & types:
npm run soulcode:emit-schema
npm run soulcode:types
Generate artifacts:
Bundle: npm run soulcode:bundle && npm run soulcode:validate
Memory: npm run mem:simulate
Ledger: npm run ledger:build && npm run ledger:extract
Embed + preview:
npm run integrate then npm run serve
Integrity & schema

Bundle validated with AJV 2020 against emitted JSON Schemas.
Ledger PNG payload uses an envelope (MAGIC|CRC32|HMAC|JSON). Set ECHO_LEDGER_HMAC_KEY for HMAC.
Dev Tools panel shows short SHA‑256 • size for Bundle/Memory/Ledger and provides copy buttons.
Dev Tools (auto)

Floating panel bottom‑left; collapse ▾/▸, hide/show Ctrl+Shift+D.
Actions: download, copy SHA, copy full JSON, Toggle Viz (memory sparkline).
Client helper: /web/echo-client.js or ESM /web/echo-client.module.js.
CI & filters

.github/workflows/monorepo-all.yml: gates Node vs Python jobs via path filters.
.github/workflows/echo-soulcode-ci.yml: Python matrix + smoke + codec tests.
.github/workflows/hyperfollow-integration.yml: Node/HTML scoped.
Conventions (LLM)

Prefer idempotent edits; stage examples under web/examples/.
Avoid committing large media and ADS files; use tools/remove-zone-identifiers.sh.
Keep integration/* generated; don’t hand‑edit emitted outputs.
Full architecture integration

Source folder: echo_full_architecture_repo/ (docs, memory_engine, ledger, scrolls, songs, images).
Memory Engine: simulate and export JSON time series
npm run mem:simulate → writes integration/outputs/memory_state.json.
Ledger block: build JSON and PNG via Python LSB steganography
npm run ledger:build → writes integration/ledger/block.json (+ block.png if Pillow available).
npm run ledger:extract → reads PNG back into integration/ledger/extracted.json.
HTML/UI: if integration/ledger/block.png exists, the integration script can embed a small image badge (optional, see code).
CI / GitHub Actions

Example workflow: .github/workflows/hyperfollow-integration.yml
Dispatch with dry_run=true to preview.
Run without dry-run to commit/PR changes.
FAQ

“It didn’t find my Proof of Love file.”
Ensure you run from the project root and that the scroll export is checked in. The tool uses content/filename cues (e.g., “Proof of Love”, “proof-of-love”) to locate the file.
“I need a different copy/placement.”
Edit the snippets and/or heuristics inside hyperfollow-integration.js (look for the INTEGRATION_CONFIG object).
“Can it target JSX/TSX?”
Current version targets HTML/Markdown safely. For JSX/TSX, place a badge or link in the main layout manually, or extend the script to parse JSX with a codemod.
Contributing

Read the contributor guide: see `AGENTS.md` (root) and `docs/CONTRIBUTING.md`.
Docs index: `docs/index.md`.
For an overview of modules and paths, see `docs/ARCHITECTURE_INDEX.md`.

Issues and PRs welcome. Please keep changes idempotent and narrative‑aware.
Together. Always.

Echo-Community-Toolkit
