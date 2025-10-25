# Repository Guidelines

## Project Structure & Module Organization
- **Root modules:**  
  - `Echo-Community-Toolkit/` – HyperFollow + soulcode integrations, LSB/MRP codecs.  
  - `kira-prime/` – Unified VesselOS CLI, collab server, VS Code extension.  
  - `The-Living-Garden-Chronicles/`, `vessel-narrative-mrp/` – Narrative generation + stego validation.  
  - `vesselos-dev-research/` – Research CLI, specs, and workspace scaffolding.  
  - Shared packages: `agents/`, `protos/`, `sigprint/`, `scripts/`, `docker/`, `tests/`.  
- Use `architecture.md` for a full ASCII map of subdirectories.

## Build, Test, and Development Commands
- **Bootstrap:** `./scripts/deploy.sh --bootstrap-only` – creates a venv and installs root Python deps.  
- **Toolkit:** `(cd Echo-Community-Toolkit && npm ci && python3 -m pytest -q)` – installs Node deps and runs core tests.  
- **Kira Prime CLI:** `(cd kira-prime && pip install -r requirements.txt && python3 vesselos.py validate)` – ensures CLI + agents are healthy.  
- **Global smoke:** `python3 -m pytest -q` – exercises top-level integration tests under `tests/`.

Next steps (choose what’s relevant):
```bash
# Regenerate protobuf stubs after editing protos/agents.proto
python -m grpc_tools.protoc -Iprotos --python_out=protos --grpc_python_out=protos protos/agents.proto

# Generate soulcode bundle and verify HTML integrations
(cd Echo-Community-Toolkit && node hyperfollow-integration.js && node verify-integration.js)

# Run the multi-agent pipeline end-to-end
(cd kira-prime && python3 vesselos.py listen --text "Begin the ritual.")
```

## Coding Style & Naming Conventions
- **Python:** PEP 8, 4-space indentation. Prefer `snake_case` for functions/variables, `CamelCase` for classes.  
- **TypeScript/JavaScript:** Follow ESLint defaults (`npm run lint` in module folders when available).  
- **Docs:** Markdown headers in Title Case; keep lines ≤ 120 chars when practical.  
- Run module-specific formatters (e.g., `npm run format`, `python -m black .`) before committing when provided.

## Testing Guidelines
- **Frameworks:** Pytest for Python, Jest/Vite test harnesses for Node packages.  
- **Naming:** Place tests under each module’s `tests/` directory (e.g., `test_mrp.py`, `tests/agents/test_kira_agent.py`).  
- **Coverage:** Aim to match existing suites; add regression tests for bug fixes.  
- Run targeted tests before PRs (e.g., `python3 vesselos.py validate`, `node verify-integration.js`).

## Commit & Pull Request Guidelines
- **Messages:** Use conventional prefixes seen in history (`docs:`, `chore:`, `feat:`, `fix:`). Keep subject lines ≤ 72 characters.  
- **PR expectations:** Provide a concise summary, list key commands run, link relevant issues, and attach screenshots/logs when visuals change.  
- Ensure CI passes and the working tree is clean (`git status`) before requesting review.

Suggested workflow:
```bash
# 1. Sync with main
git pull --rebase origin main

# 2. Create topic branch
git checkout -b feat/<short-description>

# 3. Stage, commit, push
git add <files>
git commit -m "feat: describe concise change"
git push -u origin feat/<short-description>
```
