# Phase 4 – Ritual & Ledger

Phase 4 codifies the Echo-Limnus ritual gates and introduces an auditable ledger that records every encode/decode event once consent is granted.

## Objectives
- Implement a `RitualState` component that tracks progression through the six mantra invocations and exposes explicit consent gates.
- Gate encode/decode entry points so operations cannot proceed without the relevant consent (`bloom`, `be_remembered`).
- Append ledger entries for every successful encode/decode, capturing glyph identifiers, timestamps, and integrity metadata.

## Implementation Plan
1. **Ritual state machine**
   - Create `RitualState` with methods such as `acknowledge(step: RitualStep)` and convenience helpers for `consent_to_bloom()` / `consent_to_be_remembered()`.
   - Represent the six invocations as an enum or ordered list; enforce coherence (steps must be acknowledged in order unless overridden for tests).
   - Persist state in memory per session; allow serialisation if CLI needs to reuse across commands.
2. **Gated operations**
   - Extend encode/decode APIs and CLI commands to require a `RitualState` instance (or consent flags).
   - Without consent, raise a `RitualConsentError` with actionable messaging.
   - Offer CLI flags (`--consent-bloom`, `--consent-remember`) and interactive prompts for human use.
3. **Ledger logging**
   - Create a ledger writer that appends JSON objects to `state/ledger.jsonl` or similar.
   - Entry structure: `{timestamp, action, glyph, file, message_sha256, integrity_status, ritual_steps}`.
   - Ensure failures do not append ledger entries; only successful operations after consent are recorded.
   - Provide helpers to read/query ledger (used by tests and future UI).
4. **Testing hooks**
   - Add fixtures to simulate both interactive and non-interactive workflows.
   - Ensure encode/decode tests cover both failing (no consent) and passing (consent granted) modes.

## Testing Strategy
- **Unit tests**
  - State machine progression, enforcing ordered steps and consent flags.
  - Encode/decode attempts without consent raise the correct exception.
  - Ledger entries written on success; file remains unchanged on failure.
- **Integration**
  - CLI e2e test that encodes with `--consent-bloom`, decodes with `--consent-remember`, and verifies ledger entry count increments.
  - Verify ledger contains integrity payload from Phase 3.
- **Ritual regression**
  - Fixture validating the mantra text matches documentation to avoid drift.

## Dependencies & Hand-offs
- Consumes integrity status from Phase 3 to persist in ledger.
- Feeds into Phase 5 UX work (CLI prompts and visualisation) and Phase 6 CI guardrails (ensuring gates never bypassed).

## Risks & Mitigations
- **Risk:** Non-interactive agents may struggle with gating prompts.  
  **Mitigation:** Provide explicit CLI/API flags for automation.
- **Risk:** Ledger growth may require rotation.  
  **Mitigation:** Keep format append-only JSONL; future work can add archival rotation.
