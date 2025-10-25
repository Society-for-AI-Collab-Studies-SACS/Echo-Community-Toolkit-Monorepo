g2v_repo Workspace (Staging)
============================

This directory is a staging workspace for the upcoming repository move to `g2v_repo`.
It preserves the Python workflow locally so you can run the same checks CI does while
we shuffle code into the new repo structure.

What’s included
---------------
- Local Python workflow script: `scripts/python_ci_local.sh`
- Make targets for convenience: `Makefile`
- Optional GH Actions (python-only): `.github/workflows/python-ci.yml`
- Optional GH Actions (npm publish placeholder): `.github/workflows/npm-publish.yml`

How to use locally
------------------
- From this directory:

  make ci-python

This will:
- Create a venv in `.venv`
- Install `requirements.txt` (if present)
- Install dev extras (flake8, pytest, grpcio, grpcio-tools, websockets)
- Generate protobufs if `protos/agents.proto` exists
- Lint `agents/` (if present)
- Run tests with `pytest` (if tests are present)

Migration hints
---------------
When you move code into `g2v_repo`, keep the original layout:
- `agents/` (sigprint, limnus, garden, etc.)
- `journal/` (JSONL ledger + CLI + serial monitor)
- `stylus/firmware/` (PlatformIO projects)
- `requirements.txt` (top-level)
- `protos/` (if used for gRPC/Protobuf)

Recommended sequence:
1) Create a new repo from this folder (or rename this dir to be the repo root).
2) Move or copy the above directories/files into this folder.
3) Run `make ci-python` and fix any findings.
4) Wire up GitHub Actions if desired (python-only and npm publish placeholder are included). The npm publish workflow will auto-skip when no publishable packages are found.
