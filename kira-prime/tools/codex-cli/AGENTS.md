# Repository Guidelines

## Project Structure & Module Organization
- `bin/codex.js` – Node 20 CLI entry (ESM). Namespaces: `echo`, `garden`, `limnus`, `kira`.
- `package.json` – `bin` map registers the `codex` binary.
- State is shared with the Python repo under `vessel_narrative_system_final/state/`.

## Build, Test, and Development Commands
- Run CLI directly (from `vessel_narrative_system_final/`): `node tools/codex-cli/bin/codex.js --help`
- Optional link: `(cd vessel_narrative_system_final/tools/codex-cli && npm link)` then `codex ...`
- Examples:
  - `codex echo mode paradox`
  - `codex limnus state`
  - `codex limnus encode-ledger --file vessel_narrative_system_final/state/ledger_export.json -o vessel_narrative_system_final/frontend/assets/ledger.png`

## Coding Style & Naming Conventions
- JS (Node 20): ESM modules, 2‑space indent, `camelCase` identifiers.
- Keep the CLI zero‑dependency; prefer core modules (`fs`, `path`, `child_process`).
- Small, single‑purpose functions; synchronous I/O is acceptable for CLI UX.

## Testing Guidelines
- Smoke tests: invoke representative commands and inspect output/exit codes.
- Validate stego flows by decoding an output image and checking CRC.
- Keep tests hermetic; avoid network. Prefer fixtures under `vessel_narrative_system_final/state/`.

## Commit & Pull Request Guidelines
- Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`). Subject ≤ 72 chars.
- Group changes by namespace (e.g., limnus: add export/import) and update README/help.
- Include example commands in PR descriptions; note any behavior changes.

## Security & Configuration Tips
- Node 20+ required. No secrets in code or logs.
- Stego: PNG‑24/32 only; never JPEG/palette PNG. Bit order MSB‑first; RGB channels only.
- Python bridge expects Echo‑Community‑Toolkit at `vessel_narrative_system_final/Echo-Community-Toolkit`; verify golden CRC (6E3FD9B7).

