# VesselOS Dev Research – Release & Documentation Plan

## Release Workflow (CI/CD)

Automated releases run via GitHub Actions when a version tag is pushed.

- Trigger on tags: `v*.*.*` (e.g., `v0.3.2`).
- Install dependencies: use repository `requirements*.txt`.
- Validate + test: run pytest and Kira validation.
- Publish: package artifacts and create a GitHub release via `kira publish`.

See workflow: `.github/workflows/release.yml`.

Example steps (excerpt):

- Checkout and set up Python 3.12
- `python -m pip install -r requirements.txt -r requirements-dev.txt`
- `python -m pytest -q`
- `python3 vesselos.py kira validate`
- `python3 vesselos.py kira publish --run --release --tag "$GITHUB_REF_NAME"`

Notes
- The Kira publish step uploads a ZIP artifact from `dist/` and attaches a changelog and ledger export. The GitHub CLI (`gh`) uses `GH_TOKEN`/`GITHUB_TOKEN` injected by Actions.
- If you want to include additional assets, pass `--asset <path>` to the publish command or modify the workflow to list extra files.

## Repository Documentation (Modules, Agents, Commands)

Use these docs to navigate the project:

- `docs/REPO_INDEX.md` — overview of key modules and entrypoints.
- `docs/REPO_INDEX.json` — machine-readable file list (path/size/mtime).
- `AGENTS.md` (root) — canonical agent/pipeline guidelines and commands.

Core Areas
- Pipeline (`pipeline/`): enhanced dispatcher, intent parser, metrics, circuit breaker, logger.
- Agents (`library_core/agents/`): Garden, Echo, Limnus, Kira implementations.
- Interface (`interface/`): dispatcher and logging glue for explicit route flows.
- CLI (`vesselos.py`, `cli/`): unified command surface (Prime CLI + audit commands).
- Memory (`memory/`): vector store with FAISS/SBERT/hash backends (used by Limnus).
- Workspaces (`workspaces/<id>/`): runtime state (`state/*`) and logs (`logs/*.jsonl`).

Agent Roles & Common Commands
- Garden: stage orchestration, consent, ledger.
  - `python3 vesselos.py garden start|next|open|resume|log|ledger`
- Echo: styled text, quantum personas (αβγ), glyph.
  - `python3 vesselos.py echo summon|mode|status|say|learn`
- Limnus: memory cache + hash-chained ledger.
  - `python3 vesselos.py limnus cache|recall|commit-block|encode-ledger|decode-ledger|reindex`
- Kira: chain validation, mentorship, seal, release.
  - `python3 vesselos.py kira validate|mentor|mantra|seal|push|publish`

Architecture

```
input_text -> intent_parser -> EnhancedMRPDispatcher
    |-- Garden (stage, consent)
    |-- Echo (persona & styled_text)
    |-- Limnus (memory + ledger block)
    `-- Kira (integrity + coherence checks)
-> aggregated results -> voice log + state updates
```

Search & Indexing Helpers
- `search/tags.json` — ctags-style summary for classes/functions.
- `search/rg-files.txt` — ripgrep file list (includes dotfiles, excludes `.git`).
- `search/rg-cache.jsonl` — JSONL of lines for fast offline grepping.

Regenerate indexes:
- `python3 - <<'PY'` … (see `docs/REPO_INDEX.json` generator in commit history), or ask the assistant to refresh.

## Automating Release Documentation

Automate release artifacts so every tag ships with up-to-date knowledge:

- **Kira knowledge export:** Run `python3 vesselos.py kira codegen --docs` during the release workflow (before `kira publish`). This regenerates `docs/kira_knowledge.md` with the latest ledger and memory insights; pass it to `kira publish --asset docs/kira_knowledge.md` to bundle the document.
- **Deterministic changelog script:** Add a helper (Python or Node) that inspects commits since the previous tag, consults `docs/REPO_INDEX.json`, and emits a Markdown summary (features, agent updates, breaking changes). Run it locally or in CI to produce `CHANGELOG_RELEASE.md`.
- **Codex/GPT drafting prompt:** Provide an instruction like “Summarize commits since vX.Y.Z, highlight Garden/Echo/Limnus/Kira changes, list new docs, and draft release notes in Markdown.” Wire this into a `codex release-notes generate` helper so AI can supply a first draft for human review.

Integrate whichever options fit the workflow, then commit the generated artifacts alongside README bumps before tagging.
