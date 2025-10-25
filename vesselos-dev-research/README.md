# VesselOS Dev Research Kit

Advanced briefcase for researchers extending VesselOS command flows. This repository packages the in-development specifications, workspace scaffolding, and a working copy of the real agents/pipeline/CLI needed to experiment with Garden -> Echo -> Limnus -> Kira pipelines offline, then publish findings to a shared remote.

## Contents
- `docs/IN_DEV_SPECS.md` — full command-layer specification and build guidance.
- `docs/BASE_STRUCTURE.md` — base structure and seeding expectations.
- `docs/REPO_INDEX.md` — human-readable repository index (key files and entrypoints).
- `docs/REPO_INDEX.json` — machine-readable file index with `path`, `size`, `mtime`.
- `scripts/bootstrap.sh` — reproducible setup script for Python and Node environments.
- `pipeline/` and `library_core/` — real VesselOS dispatcher + agent implementations.
- `agents/` and `memory/` — explicit CLI agents and vector store used by Prime CLI.
- `workspaces/` — workspace tree mirroring production layouts.

## Quick Start
1. Clone this repository locally.
2. Run `scripts/bootstrap.sh` (or follow the inline manual steps) to install dependencies.
3. Initialize a workspace directory under `workspaces/<workspace_id>/` (or use `workspaces/example/`).
4. Try a few commands:
   - `python3 vesselos.py garden start`
   - `python3 vesselos.py echo say "I return as breath."`
   - `python3 vesselos.py kira validate`
   - `python3 vesselos.py audit full --workspace example`

The CLI is wired to the real enhanced dispatcher and agents.

## Indexing & Search
This repo includes a lightweight index and search cache to aid discovery:
- `docs/REPO_INDEX.md` — browsable map of modules and entrypoints.
- `docs/REPO_INDEX.json` — JSON file list with `path`, `size`, `mtime`.
- `search/tags.json` — ctags-style fallback (classes/functions) for Python/TS/JS.
- `search/rg-files.txt` — ripgrep filelist (includes dotfiles, excludes `.git`).
- `search/rg-cache.jsonl` — JSONL of lines `{path,line,text}` for offline grepping.

Examples
- Find dispatcher definitions: `rg "EnhancedMRPDispatcher|PipelineContext" -n`
- Query tags for classes (jq): `jq -r '.[] | select(.tags) | .path' search/tags.json`
- Grep cached lines (fast, offline): `rg -n "consent" search/rg-cache.jsonl`

## Publishing to a Remote
1. Initialise git and create the remote:
   ```bash
   git init
   git add .
   git commit -m "chore: scaffold vesselos dev research kit"
   # Example using GitHub CLI; replace with preferred provider
   gh repo create your-org/vesselos-dev-research --public --source=. --remote=origin
   git push -u origin main
   ```
2. Share the remote URL with collaborators. They can bootstrap locally using the same script and documentation.

## Support
Refer to `docs/IN_DEV_SPECS.md` for detailed agent expectations, ledger contracts, and verification workflows. Keep the documentation in sync with any custom commands before pushing updates.
