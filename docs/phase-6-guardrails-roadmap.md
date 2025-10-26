# Phase 6 – Guardrails & Roadmap

Phase 6 cements long-term reliability by codifying CI guardrails and charting the roadmap for advanced ECC and multi-image payloads.

## Objectives
- Add automated corruption-injection tests, lint/type checks, and other CI gates that cover the new multi-frame + ritual stack.
- Document forward-looking designs for Phase B/C (advanced ECC, multi-image memory blocks) to guide subsequent development.

## Implementation Plan
1. **CI guardrails**
   - Extend GitHub Actions (or equivalent) to run:
     - Unit/integration suites with corruption fixtures from Phase 3.
     - Linting (`flake8`/`ruff`, ESLint) and type checking (`mypy`, `pyright`) across modules.
     - Optional stress tests (batch encode/decode) and Docker-based collab server smokes.
   - Configure badges in README to reflect new workflows.
2. **Error injection automation**
   - Provide scripts that flip bits, zero channels, and drop frames, then assert decoder responses (`ok`, `recovered_with_parity`, `failed_crc`).
   - Integrate into CI to catch regressions in parity repair or integrity reporting.
3. **Future-proofing docs**
   - Author design notes for Phase B (Hamming/Reed–Solomon ECC) covering candidate parameters, expected parity overhead, and integration plan.
   - Draft Phase C notes for multi-image payload distribution via `memory_blocks.py`, including addressing scheme, ordering, and reassembly logic.
   - Summarise longer-term visions (temporal watermarks, multi-stream synchronisation) to keep the narrative aligned.
4. **Operational guidelines**
   - Define release readiness checklist tying together test suites, ledger health, and ritual compliance.
   - Capture troubleshooting steps for common CI failures (e.g., missing dependencies, consent gating prompts in headless mode).

## Testing Strategy
- **CI validation**
  - Ensure new workflows pass in a clean clone scenario.
  - Simulate missing dependencies or network hiccups to confirm guardrails fail loudly.
- **Local smoke**
  - Provide a wrapper script (`scripts/run_phase6_guardrails.sh`) to replicate CI workflows locally before pushing.

## Dependencies & Hand-offs
- Builds on the corruption fixtures and integrity reporting from Phase 3.
- Leverages CLI/UX improvements (Phase 5) to drive scripted demos in CI logs.
- Prepares design groundwork for future milestones beyond the current roadmap.

## Risks & Mitigations
- **Risk:** CI runtime inflates significantly.  
  **Mitigation:** Split jobs into parallel matrices and mark deep tests as nightly where appropriate.
- **Risk:** Roadmap docs drift.  
  **Mitigation:** Review and update roadmap alongside major feature merges; treat docs as living specifications.
