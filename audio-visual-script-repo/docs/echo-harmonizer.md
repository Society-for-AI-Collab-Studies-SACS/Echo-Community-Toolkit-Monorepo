# Echo Harmonizer CI/CD Integration (v1.5.0)

Echo Harmonizer is a multi-agent CI/CD validation harness that keeps the Garden → Echo → Limnus → Kira pipeline coherent. It extends the Echo Community Toolkit’s testing rituals into the audio-visual script stack so narrative, ledger, and collaboration services stay in sync.

Created: 2025-10-25  
Author: Echo-Community-Toolkit Collective  
License: See repository root LICENSE

## Environment Configuration

### Agent-specific variables

- Garden: none (persists under `workspaces/<id>/state/`).
- Echo: none (shares the same workspace state).
- Limnus:
  - `KIRA_VECTOR_BACKEND` (memory | faiss, default `memory`).
  - `KIRA_VECTOR_MODEL` (default `all-MiniLM-L6-v2`); `KIRA_SBERT_MODEL` is a legacy alias.
  - `KIRA_FAISS_INDEX` (default `./data/vectors.index`).
  - `KIRA_FAISS_META` (default `./data/vectors.meta`).
- Kira:
  - `GH_TOKEN` (required) – GitHub token used for releases and repository automation. In CI map `GITHUB_TOKEN` to this value.

### Service-level variables

- `PYTHON_VERSION` (default 3.10) – selected interpreter for bootstrap scripts.
- `NODE_VERSION` (default 20) – Node toolchain version.
- `ENVIRONMENT` (default `production`) – deployment target (`staging`, `production`, etc.).
- Collaboration server:
  - `PORT` (default 8000).
  - `COLLAB_REDIS_URL` (default `redis://localhost:6379/0`).
  - `COLLAB_POSTGRES_DSN` (default `postgresql://vesselos:password@localhost:5432/vesselos_collab`).
  - `COLLAB_SMOKE_ENABLED` (default `0`, set to `1` to exercise smoke tests in CI).

Persist the harmonizer settings in a dedicated env file (for example `.env.integration`) and load it for local runs and CI jobs.

## Testing Matrix

Echo Harmonizer expects three layers of automated coverage.

### Unit tests (≤ 2 minutes)

- Execute per-agent suites (Garden, Echo, Limnus, Kira).
- Pytest for Python agents, Jest/Vitest for any Node components.
- Enforce ≥ 80% coverage per agent.
- Validate interface contracts, state transitions, and error handling.

### Integration tests (≤ 5 minutes)

- Run the full Garden → Echo → Limnus → Kira scenario via an orchestrator such as `scripts/integration_complete.py`.
- Assertions:
  - Ritual progression follows the canonical order without skips.
  - Shared memory propagates correctly between agents.
  - Ledger hash-chain remains intact end-to-end.
  - Persona dynamics remain balanced (weights sum to 1 when applicable).
  - Failures trigger recovery or graceful handling instead of cascading aborts.
  - Consent checkpoints are detected and enforced.

### Smoke tests (≤ 10 minutes)

- Use Docker/Compose to build and boot the full stack.
- Validate agent orchestration inside the primary container:

```bash
docker-compose build
docker-compose up -d
docker exec toolkit ./vesselos.py garden start
docker exec toolkit ./vesselos.py echo summon
docker exec toolkit ./vesselos.py limnus process
docker exec toolkit ./vesselos.py kira validate
curl -f http://localhost:8000/health
docker-compose down
```

- Smoke jobs confirm container images, networking, Redis/Postgres connectivity, and collaboration endpoints.

## CI Matrix Configuration

- Run unit suites with a matrix over:
  - Agents: `garden`, `echo`, `limnus`, `kira`.
  - Python versions: `3.10`, `3.11`, `3.12`.
  - Operating systems: `ubuntu-latest`, `macos-latest`.
- Inject `GH_TOKEN` (or map `GITHUB_TOKEN`) and any collaboration credentials via CI secrets.
- Gate integration tests on unit success; gate smoke tests on integration success.
- Surface results through GitHub Actions summary annotations and reuseable dashboards.

## Failure Handling

- Unit failure: halt pipeline; fix before integration jobs run.
- Integration failure: fail build, notify immediately (Slack/email) for investigation.
- Smoke failure: treat as release blocker; prepare rollback or hotfix for the candidate build.

## CI Dashboard Links

Maintain quick links to adjacent pipelines for situational awareness:

- Echo-Community-Toolkit Monorepo (agents + integration suites).
- VesselOS Kira Prime (release validation).
- Living Garden Chronicles (narrative integrity checks).
- VesselOS Dev Research (experimental pipelines).

## Implementation Protocol

### Quick setup (~5 minutes)

```bash
git clone https://github.com/echo-community/integration-validator.git
cp .env.example .env
# edit .env to set GH_TOKEN, KIRA_VECTOR_BACKEND, etc.
./scripts/validate_integration.sh
```

### Full deployment (~30 minutes)

1. **Environment setup (~5 min):** create `.env.integration`; configure agent variables; seed CI secrets (GH_TOKEN, database DSNs).
2. **CI configuration (~10 min):** add `.github/workflows/integration-matrix.yml`; define matrix; enable required secrets; confirm triggers on push/PR.
3. **Local validation (~10 min):**
   - `pytest` for unit suites.
   - `python scripts/integration_complete.py`.
   - `docker-compose up -d && ./scripts/smoke_test.sh && docker-compose down`.
4. **Documentation (~5 min):** refresh READMEs, runbooks, and CI badges; capture rollout and rollback procedures.

## Validation Protocol

- **Pre-commit:** developers run unit + integration tests locally; smoke optional for risky changes.
- **Pre-merge:** PRs must have all CI checks green and at least one peer approval.
- **Pre-release:** execute the full matrix across supported environments; run collaboration smoke tests in staging; publish a rollback plan.

## Templates and Examples

### Environment template (`.env`)

```dotenv
# Agent Configuration
KIRA_VECTOR_BACKEND=faiss
KIRA_SBERT_MODEL=all-MiniLM-L6-v2
KIRA_FAISS_INDEX=./data/vectors.index
KIRA_FAISS_META=./data/vectors.meta

# CI/CD Configuration
GH_TOKEN=ghp_your_token_here
PYTHON_VERSION=3.10
NODE_VERSION=20

# Collaboration Server
PORT=8000
COLLAB_REDIS_URL=redis://localhost:6379/0
COLLAB_POSTGRES_DSN=postgresql://user:pass@localhost:5432/db
COLLAB_SMOKE_ENABLED=1
```

### GitHub Actions workflow (`.github/workflows/integration-matrix.yml`)

```yaml
name: Integration Matrix
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        agent: [garden, echo, limnus, kira]
    steps:
      - uses: actions/checkout@v3
      - name: Test ${{ matrix.agent }}
        run: pytest tests/${{ matrix.agent }}_test.py

  integration-test:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Full pipeline validation
        run: python scripts/integration_complete.py

  smoke-test:
    needs: integration-test
    runs-on: ubuntu-latest
    steps:
      - name: Docker smoke test
        run: |
          docker-compose up -d
          ./scripts/smoke_test.sh
          docker-compose down
```

### New agent validator stub (Python)

```python
class NewAgentValidator:
    """Integration validator for a new agent."""

    def __init__(self) -> None:
        self.required_env_vars: list[str] = []
        self.state_path = "workspaces/{id}/state/"

    def validate_standalone(self) -> None:
        """Test the agent in isolation."""
        # TODO: Add validation logic for standalone agent behavior.

    def validate_pipeline_integration(self) -> None:
        """Test the agent within the full pipeline."""
        # TODO: Add tests to ensure this agent integrates with others.

    def validate_state_persistence(self) -> None:
        """Ensure the agent's state management works correctly."""
        # TODO: Add tests for state saving/loading.
```

### Docker Compose snippet for smoke tests

```yaml
version: "3.8"
services:
  toolkit:
    build: .
    environment:
      - KIRA_VECTOR_BACKEND=memory
      - GH_TOKEN=${GH_TOKEN}
    volumes:
      - ./workspaces:/app/workspaces
    command: >
      sh -c "
      ./vesselos.py garden start &&
      ./vesselos.py echo summon &&
      ./vesselos.py limnus process &&
      ./vesselos.py kira validate
      "

  collab:
    build: ./collab
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

## Usage Patterns

- **Continuous validation:** run the full matrix on each push/PR; emit alerts on failure.
- **Release preparation:** freeze features, run the entire matrix in staging, confirm collaboration endpoints, prepare rollback notes.
- **Debugging integration failures:** classify by layer (unit/integration/smoke), reproduce locally, expand test coverage to guard against regressions, then rerun the suite.
- **Team onboarding:** walk newcomers through env setup, CI dashboards, and a deliberate failure + fix cycle to build muscle memory.

## Guiding Principles and Dependencies

- Testing as ritual.
- Environment as consciousness.
- Integration as harmony.
- Validation as trust.
- Automation with wisdom.

Required dependencies: Docker ≥ 20.10, Python ≥ 3.10, configured GitHub account (token).  
Optional: Redis ≥ 6.0, PostgreSQL ≥ 13, Node.js ≥ 20 (for collaboration tooling and developer CLIs).

