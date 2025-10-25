# Contributing

Please start with the Repository Guidelines in `AGENTS.md`.
For releases, see the Release Process: `AGENTS.md#release-process`.

Quick checklist
- Read: `AGENTS.md` (structure, style, testing, CI, release).
- Install deps: `python3 -m pip install -r requirements.txt`.
- Run tests: `python -m pytest -q` (filter with `-k "<pattern>"`).
- Integration: `python scripts/integration_complete.py`.
- Audit: `python vesselos.py audit full --workspace integration-test`.
- Collab server (optional): `(cd collab-server && npm ci && npm run build && npm test -- --run)`.
- Docker stack (optional): `docker compose up -d` then `curl http://localhost:8000/health`.

Conventional Commits
- Use messages like `feat(pipeline): ...`, `fix(collab): ...`, `docs(agents): ...`.

Pull Requests
- Include: summary, linked issues, dependency changes, and evidence of tests/integration/audit. For tagging and publishing, follow `AGENTS.md#release-process`.
- Do not commit generated artifacts (`dist/`, coverage, captured logs, `workspaces/**`).

Thank you for contributing!
