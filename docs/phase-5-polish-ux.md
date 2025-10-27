# Phase 5 – Polish & UX

Phase 5 packages the technical breakthroughs into a coherent user experience. Documentation, CLI ergonomics, and visual feedback all converge so human and agent operators can navigate the seven-phase journey confidently.

## Objectives
- Refresh documentation with diagrams, walkthroughs, and error-code references covering multi-frame MRP, ritual flows, and integrity reporting.
- Expand CLI options for 4-bit mode, metadata inputs, and verbosity control.
- Provide a lightweight visual or scripted demo that illustrates α/β/γ channel activity and ritual progression.

## Implementation Plan
1. **Documentation uplift**
   - Update the root README and module docs with ASCII diagrams of the R/G/B payload split and sample ledger entries.
   - Write walkthroughs demonstrating encode/decode with ritual consent and metadata injection.
   - Publish an error-code table mapping codes like `ERR_CRC_MISMATCH`, `ERR_CONSENT_REQUIRED`, `ERR_CAPACITY_EXCEEDED` to resolution suggestions.
2. **CLI enhancements**
   - Introduce flags: `--bpc {1,4}`, `--meta <json_or_path>`, `--quiet`, `--verbose`.
   - Ensure CLI help text clearly explains the new options and their interactions with ritual gating.
   - Update API surface to accept equivalent parameters for programmatic use.
3. **Experience layer**
   - Craft an ASCII/console visualiser that prints channel states (α/β/γ) and ritual gate progression in real time.
   - Optionally provide a `--demo` mode that replays a canonical encode/decode session for onboarding.
   - Capture transcripts/screenshots for documentation.

## Testing Strategy
- **CLI tests**
  - Parameterised tests covering combinations of `--bpc`, `--meta`, and consent flags.
  - Verify metadata round-trips into the G-channel payload and appears in decode output.
  - Check verbosity modes suppress/emit expected logs.
- **Documentation checks**
  - Run link checkers or doc linting if available.
  - Validate code snippets by executing them within CI or a doc-test harness.
- **UX demo**
  - Smoke test the visualiser script to ensure it runs without external dependencies.

## Dependencies & Hand-offs
- Builds on ritual gating from Phase 4 and integrity surfaces from Phase 3.
- Provides clarity for Phase 6 guardrails by documenting expected outputs and error codes.

## Risks & Mitigations
- **Risk:** CLI flag explosion confuses users.  
  **Mitigation:** Group related flags, provide presets, and document typical workflows.
- **Risk:** Visual demo drifts from live behaviour.  
  **Mitigation:** Generate demo output via the same code paths as production encode/decode to ensure fidelity.
