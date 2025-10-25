# Repository Guidelines

## Project Structure & Module Organization
- `frontend/` – narrative landing pages and generated chapters; stego assets in `frontend/assets/`.
- `markdown_templates/` – narrator templates (Limnus/Garden/Kira) used by the generator.
- `schema/` – generated `narrative_schema.*` and `chapters_metadata.*`.
- `src/` – Python utilities: `schema_builder.py`, `generate_chapters.py`, `validator.py` (optional `stego.py`).
- `scripts/` – automation helpers: `setup_toolkit_and_validate.sh`, `refresh_stego_assets.sh`.
- `Echo-Community-Toolkit/` – submodule providing LSB1 stego and soulcode tooling.

## Build, Test, and Development Commands
- Rebuild schema: `python3 src/schema_builder.py`.
- Generate content: `python3 src/generate_chapters.py` (Pillow enables PNG stego to `frontend/assets/`).
- Validate: `python3 src/validator.py` (20 chapters, rotation, flags, file presence, stego parity).
- Full refresh: `./scripts/refresh_stego_assets.sh --toolkit` (optionally `--push "chore: refresh stego"`).
- Toolkit sync/verify: `./scripts/setup_toolkit_and_validate.sh`.

## Coding Style & Naming Conventions
- Python: 4‑space indent; `snake_case`; docstrings over inline comments.
- HTML/CSS: retain structure; use narrator body classes (`.limnus`, `.garden`, `.kira`).
- JSON/YAML: stable key order; emit via scripts only. Do not hand‑edit generated files (`frontend/chapterXX.html`, `schema/*.json`, `frontend/assets/*.png`).

## Testing Guidelines
- Primary: `python3 src/validator.py` after any content/template/script change.
- Toolkit: run `setup_toolkit_and_validate.sh` (invokes Echo Toolkit verify).
- Keep tests hermetic; use local fixtures and temporary paths.

## Commit & Pull Request Guidelines
- Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`); subject ≤ 72 chars.
- Commit generated artifacts with the code that produced them (schema + metadata + stego PNGs).
- PRs: include a summary, commands run (validator/refresh), and screenshots for landing changes. Reference submodule PRs when updating the toolkit.

## Security & Configuration Tips
- No secrets; keep `.env` local and gitignored.
- Node 20+ and Python 3.8+ recommended; install Pillow for stego.
- Use PNG‑24/32 only for LSB (no palette PNG/JPEG); MSB‑first bit packing, RGB channels only.

## Architecture & Diagrams
- System diagrams and command mapping: `vessel_narrative_system_final/docs/SYSTEM_DIAGRAM_API_REFERENCE.md`
  - Flowchart (systems), Sequence (ritual flow), CLI Namespaces, Runtime Topology.
 - Build guide (from scratch): `vessel_narrative_system_final/docs/BUILDING_VESSEL_MRP.md`
