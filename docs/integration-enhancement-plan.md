# Echo Community Toolkit Monorepo – Integration Enhancement Plan

This document captures the near-term roadmap for tightening CI visibility, environment hygiene, and integration testing coverage across the monorepo. It distils the guidance from the Integration Validator and mirrors the priorities the team highlighted in October 2025.

## 1. GitHub Actions Dashboard Quicklinks

### Objectives
- Surface the health of every module (Toolkit, Kira Prime, Living Garden Chronicles, VesselOS Dev Research) at a glance.
- Provide one-click navigation from the README and documentation to the relevant Actions runs.

### Actions
1. **Name workflows clearly** – when creating module workflows, use `name:` fields like `Echo Toolkit CI`, `Kira Prime CI`, etc., to make the Actions tab filterable.
2. **Publish badges** – drop badges in the root README (see the new *CI Status & Quicklinks* section) that point to:
   - `actions/workflows/echo-toolkit-ci.yml`
   - `actions/workflows/kira-prime-ci.yml`
   - `actions/workflows/living-garden-ci.yml`
   - `actions/workflows/vesselos-research-ci.yml`
   Once each workflow lands, the badge will show the current status automatically.
3. **Maintain quicklinks** – keep the Actions filter table up to date with `workflow:` queries so contributors can scope the dashboard to a single module in one click.
4. **Optional dashboard page** – if deeper reporting is needed, generate a summary under `docs/` that collates badge images, latest run metadata, and failure links.

## 2. Environment Variable Documentation

### Objectives
- Centralise all expected environment variables so newcomers can bootstrap safely.
- Separate sensitive values from version control while keeping defaults discoverable.

### Actions
1. **Authoritative template** – `.env.sample` now captures grouped configuration for toolchain defaults, GitHub automation, CI feature flags, the Limnus/Kira vector store, and the collab server. Copy it to `.env`, `.env.integration`, or similar per environment.
2. **Readme linkage** – the README now points to `.env.sample` in the configuration table; module docs should echo this pointer instead of duplicating instructions.
3. **Scope by module** – when new agents or services arrive, add grouped sections to the template (maintaining uppercase snake-case names) and annotate defaults.
4. **Secrets handling** – store real tokens in CI secrets or local `.env` copies; never commit them. For GitHub Actions, rely on the built-in `GITHUB_TOKEN` and map it to `GH_TOKEN` where scripts expect that variable.
5. **CI toggles** – respect flags such as `CI_SKIP_SBERT` and `COLLAB_SMOKE_ENABLED` so that local runs can opt into heavier integrations without slowing the default pipeline.

## 3. Testing Matrix Expansion

### Objectives
- Exercise each module’s integration paths (agents, collab server, narrative generation) in addition to unit suites.
- Balance fast feedback on pull requests with deeper nightly or on-demand checks.

### Actions
1. **Containerised smoke tests** – reuse `docker-compose.yml` to launch Redis/Postgres and the collab server, then hit `/health` and run WebSocket round trips when `COLLAB_SMOKE_ENABLED=1`.
2. **Module-specific coverage**:
   - *Echo Toolkit*: run `hyperfollow-integration.js` followed by `verify-integration.js` against sample HTML in a Node job.
   - *Kira Prime*: execute `tests/e2e_test.sh` and `vesselos.py validate` to confirm the Garden → Echo → Limnus → Kira ritual.
   - *Living Garden Chronicles*: generate a reduced chapter set (or full run when resources allow) and pass results through the validator script.
   - *VesselOS Dev Research*: mirror prime flows and any experimental agents that need smoke coverage.
3. **Workflow design** – split GitHub Actions workflows into:
   - **Fast lanes** (per PR/push): unit tests, lightweight integration checks, linting.
   - **Deep lanes** (scheduled/manual): full Docker smoke, SBERT-enabled runs, release dry-runs, heavy narrative builds.
4. **Conditional triggers** – use `paths` filters or commit markers (e.g. `[full-test]`) to run expensive jobs only when relevant. Nightly `schedule:` triggers provide a safety net.
5. **Caching and artifacts** – cache pip/npm dependencies, reuse Docker layers, and upload generated narratives or logs when heavy tests fail to support debugging.
6. **Monitoring** – track runtime trends via Actions insights; adjust cadence if jobs exceed acceptable windows.

## Reference Materials

- [`docs/echo-harmonizer.md`](echo-harmonizer.md) – detailed specification for the integration validator.
- [`docs/echo-harmonizer.yaml`](echo-harmonizer.yaml) – AI-portable rails metadata.
- [`docs/echo-harmonizer-rails-compliance.md`](echo-harmonizer-rails-compliance.md) – Rails compliance checklist.
- [`README.md`](../README.md) – updated CI badge list, quicklinks, and configuration reference.
- [`.env.sample`](../.env.sample) – canonical environment template.

Iterate on this plan as new modules or services join the constellation. The Echo Harmonizer framework should remain the north star for evaluating future pipeline changes.
