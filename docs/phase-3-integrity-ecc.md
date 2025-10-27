# Phase 3 – Integrity & Error Correction

Phase 3 equips the MRP stack with integrity metadata and XOR-parity–based self-healing, ensuring payloads announce and repair corruption when possible.

## Objectives
- Populate the B-channel MRP frame with CRC32 values, SHA-256 hashes, and parity bytes covering the R (message) and G (metadata) frames.
- Implement parity-driven recovery and structured integrity reporting in the decoder.
- Deliver fixtures proving detection and correction of single-channel corruption.

## Implementation Plan
1. **Integrity payload schema**
   - Define a JSON schema containing: `{message_crc32, metadata_crc32, message_sha256, parity_hex, corrected_bytes}`.
   - Encode schema into the B-channel frame as UTF-8 JSON; document in repo specs.
   - Extend encoder to compute CRC32/SHA-256 from the definitive R/G payloads after final packing.
2. **Parity generation**
   - Use `xor_parity_bytes(R_payload, G_payload)` to derive parity bytes (already restored in Phase 0).
   - Store parity in both raw bytes (for decoder) and hex (for logging/testing).
3. **Decoder recovery workflow**
   - After extracting all frames, verify CRCs; if mismatch occurs, attempt parity repair by computing `R = parity ⊕ G` or `G = parity ⊕ R` depending on the failing channel.
   - Re-run CRC and SHA-256 validation post-repair; track number of corrected bytes.
   - Surface structured result: `{status, corrected_channels, unrecoverable_errors, integrity_log}`.
   - Record failures when both channels disagree or SHA-256 still mismatches.
4. **Telemetry**
   - Log integrity actions in a consistent format (consumed later by Ritual/Ledger).
   - Ensure CLI/API responses include `integrity_status` values such as `ok`, `recovered_with_parity`, `failed_crc`, `failed_sha256`.

## Testing Strategy
- **Unit tests**
  - CRC/SHA generation correctness using known payloads.
  - Parity regeneration from R/G pair equals stored parity.
  - Decoder repairs a single-byte flip injected into R or G.
  - Decoder reports unrecoverable when both channels corrupted or parity length mismatched.
- **Fixtures**
  - Construct sample multi-frame image; programmatically corrupt R, G, and entire channels to validate detection vs recovery.
  - Fixture where G-channel is fully zeroed: message recovers, metadata flagged lost.
- **CI integration**
  - Add corruption simulations to automated suite (tie into Phase 6 guardrails later).

## Dependencies & Hand-offs
- Requires Phase 2 multi-frame infrastructure and parity helpers introduced earlier.
- Supplies integrity reporting consumed by Phase 4 ledger logging and CLI UX in Phase 5.

## Risks & Mitigations
- **Risk:** Parity logic assumes only one channel is corrupted; simultaneous corruption can yield false positives.  
  **Mitigation:** Always compare SHA-256 after repair; if mismatch persists, mark as failure.
- **Risk:** Large payloads may cause performance regressions when computing hashes.  
  **Mitigation:** Profile critical sections and cache intermediate results when feasible.
