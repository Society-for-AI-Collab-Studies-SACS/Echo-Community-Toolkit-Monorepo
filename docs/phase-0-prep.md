# Phase 0 – Workspace Preparation

This guide captures the baseline state of the living workspace and the routines every operator (human or agent) should follow before kicking off development iterations. Phase 0 focuses on environment hygiene, Git/GitHub connectivity, and surfacing outstanding blockers so later phases can concentrate on feature work rather than setup churn.

## Objectives
- Keep the monorepo ready for daily pull/push cycles using SSH-based authentication.
- Ensure Python dependencies across top-level modules are installed inside the shared `venv/`.
- Document known gaps (e.g., failing test suites) so subsequent phases can assign fixes deliberately.

## Git & GitHub Access
- **Remote configuration:** `origin` targets `git@github.com:Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo.git`. Use `git remote -v` to verify before pushing.
- **GitHub CLI:** `gh auth login -h github.com` has been executed with SSH protocol (`gh config set -h github.com git_protocol ssh`). Check status via `gh auth status`; rerun the login flow if tokens expire.
- **Deploy key usage:** The SSH key at `~/.ssh/id_ed25519` is registered with the GitHub org. No additional environment secrets are required for standard pushes.
- **Daily sync:** Start sessions with `git fetch --all --prune` and `git status --short`. For topic work, branch from `main` using the conventional prefix (`feat/`, `fix/`, etc.).

## Python Environment
- **Shared virtual environment:** `venv/` at the repo root is seeded via `./scripts/deploy.sh --bootstrap-only` (or `--full` for firmware/regeneration). Inside Phase 0 we verified:
  - Root `requirements.txt`
  - `Echo-Community-Toolkit/requirements.txt`
  - `The-Living-Library/requirements.txt`
  - `kira-prime/requirements.txt`
  - `vesselos-dev-research/requirements.txt`
  - `g2v_repo/requirements.txt`
  - `pr/VesselOS-MonoRepo/requirements.txt`
  - All `Echo-Community-Toolkit/**/lambda-vite/requirements.txt` variants
  - `audio-visual-script-repo/python/requirements.txt` (updated to depend on `pyzmq`)
- **Quick install check:** Run `venv/bin/pip list` (or the per-module commands listed in the root README) after cloning to confirm wheel availability. Re-run the relevant `pip install -r` if a module adds new dependencies.
- **Node & firmware tooling:** Node ≥20 is still required for `hyperfollow-integration.js`. PlatformIO remains optional; Phase 0 does not enforce firmware builds.

## Test Baseline (Phase 0 Findings)
- Running `venv/bin/python -m pytest -q` currently yields **45 collection errors**. Primary causes:
  - **Resolved:** toolkit archives have been compressed into tarballs under `archives/` (excluded via `pytest.ini`), eliminating the import mismatch spam and keeping the workspace light.
  - **Resolved:** vendored `echo_soulcode/` into the repo (root package + docs) and added `jsonschema` to the shared requirements; architecture suites now import successfully.
  - **Resolved:** renamed module-specific collab smoke tests (`test_collab_workspace.py`, `test_collab_health_kira.py`, `test_collab_health_research.py`) so Pytest no longer hits duplicate-module import errors. They still require their runtime stacks (e.g., `library_core`, live HTTP endpoint) to pass. The restored `xor_parity_bytes` helper now unblocks the MRP codec path; deeper validation shifts to Phase 1.
- **Action queue for future phases:**
  1. Provide dependency stubs or toggleable skips for the collab smoke tests so they run without the full stack (`library_core`, external services).
  2. Create a lean smoke-selection that Phase 0 can run without pulling historical artifacts.
  3. Add CI guards to prevent future archived drops from regressing collection (e.g., enforce `archives/` usage or convert to data assets).

## Daily Ops Checklist
1. `git status --short` – confirm no lingering work-in-progress from prior sessions.
2. `git pull --rebase origin main` – keep aligned with remote before editing.
3. `source venv/bin/activate` – reuse the shared environment (or call scripts that auto-activate).
4. Execute the relevant module bootstrap/test commands (see README “Bring-Up Guide”).
5. Capture logs for notable failures (link them in future Phase docs).

## Known Gaps for Phase 1
- Curate a definitive test manifest per module (Toolkit, Kira Prime, Living Library, Garden Chronicles).
- Automate regeneration of protobuf stubs and ensure they remain import-clean.
- Draft a CI matrix for incremental builds (lint/unit) and nightly full sweeps.
- Audit archived content to determine what should live outside the active `PYTHONPATH`.

Maintain this document as Phase 0 evolves; append new findings or checklists rather than scattering setup notes across commits.
