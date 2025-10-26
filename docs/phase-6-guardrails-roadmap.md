# Phase 6 – Guardrails & Roadmap

## Objectives
- Harden CI/CD guardrails to keep parity/ECC features reliable and code quality high.
- Document future ECC and multi-image enhancements (Phase B/C roadmap).
- Establish monitoring/alerting strategies for ritual and integrity failures.

## Scope & Deliverables
1. **CI Guardrails**
   - Establish workflow suite:
     - `lint-and-type.yml`: run `ruff`, `black --check`, `pyright`/`mypy`, `eslint` (where applicable); fail fast with annotated output.
     - `corruption-suite.yml`: generate corrupted fixtures (bit flips, parity tamper, zeroed channel) using Phase 3 utilities, decode, and assert expected integrity statuses.
     - `matrix-tests.yml`: run encode/decode matrix across {single,mrp} × {1-bit,4-bit} × representative image sizes; include golden sample.
     - `docs-check.yml`: build documentation (mkdocs or similar), run doctests, ensure diagrams/scripts referenced exist.
   - Publish coverage reports and parity health dashboards as artifacts (possible integration with Codecov/Coveralls).
   - Mark critical workflows as required checks for PR merges.
2. **Monitoring / Alerts Plan**
   - Define metrics/log schema:
     - Ritual metrics: consent granted/denied counts, average time to consent, automation mode usage.
     - Integrity metrics: parity repair count, CRC failure rate, SHA mismatch occurrences.
     - Ledger metrics: entries appended per interval, duplicate/rotation warnings.
   - Outline how to export metrics (Prometheus exporters, JSON logs, OpenTelemetry spans) for future observability stack.
   - Provide runbook stubs for responding to repeated CRC failures or ritual denials.
3. **Developer Tooling**
   - Add pre-commit hooks aligning with CI (lint/format/type).
   - Provide makefile tasks (`make lint`, `make type`, `make corruption-suite`) mirroring pipeline steps.
   - Document local setup for running guardrail workflows (e.g., optional Docker compose for environment parity).
4. **Roadmap Notes (Phase B/C)**
   - Phase B (Advanced ECC):
     - Evaluate Hamming(7,4) / Reed–Solomon RS(255,223) integration, required libs, complexity/overhead, compatibility with existing parity.
     - Plan migration path (e.g., dual parity+RS, versioned frames).
   - Phase C (Multi-Image Memory Blocks):
     - Design manifest format for multi-image payloads, block indexing, parity across images (RAID-like).
     - Expand `memory_blocks.py` with APIs for block assemble/disassemble.
   - Stretch goals: temporal watermarks, multi-stream synchronization, integration with narrative system telemetry.
5. **Documentation & Communication**
   - Create guardrail playbook summarizing workflows, metrics, and response procedures.
   - Update README roadmap table linking to Phase B/C notes and guardrail docs.

## Testing
- CI pipelines running corruption suite + static analysis must report green before merge.
- Manual review of roadmap docs to confirm clarity and alignment with stakeholders.

## Exit Criteria
- Guardrail workflows merged and enforced (required checks).
- Monitoring plan documented with actionable follow-ups.
- Phase B/C roadmap published in `docs/` with next steps and owners.
