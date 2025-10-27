# Phase 1 – Legacy Refresh

Phase 1 modernises the core LSB extractor while preserving backwards compatibility with archived payloads. The goal is to yield a clean separation between modern LSB1 headers and historic null-terminated streams, backed by a regression suite that guarantees the golden sample continues to decode.

## Objectives
- Refactor the LSB decoding stack into explicit parsers for the three supported formats (LSB1 header, legacy null-terminated, raw bit stream).
- Harden error handling around CRC32 and Base64 decoding so malformed payloads fail fast without yielding plaintext.
- Wire the golden-sample regression into CI to certify the refactor did not break compatibility.

## Implementation Plan
1. **Parser separation**
   - Introduce helpers such as `parse_lsb1_header(data: bytes) -> Header` to detect the "LSB1" magic, version, flags, payload length, and CRC32.
   - Split legacy handling into `extract_legacy_payload(bits: Iterable[int]) -> bytes`, retaining the null-terminated parsing logic.
   - Provide a raw bit stream reader to fall back gracefully when neither header nor null terminator is detected.
   - Update `LSBExtractor` to orchestrate the parsers and return structured decode results (payload, mode, metadata, crc status).
2. **Robust validation**
   - Validate header lengths, flag combinations, and CRC/length before attempting decode.
   - Trap Base64 errors explicitly; surface a `DecodeError` that contains the failing step (`crc_mismatch`, `invalid_base64`, etc.).
   - Ensure CRC mismatches abort the decode path and never return best-effort plaintext.
3. **Surface metadata**
   - Preserve header metadata (flags, version, bits-per-channel) so downstream tooling can make mode decisions in Phase 2.
   - Map flag bits to symbolic names and document them in the README/Phase docs.

## Testing Strategy
- **Unit tests**
  - Valid header parse/decode, ensuring payload and metadata match fixtures.
  - Corrupted magic, wrong length, and CRC mismatch cases each raise the expected error.
  - Base64 decode failure surfaces a clear validation error.
  - Legacy null-terminated payload decodes correctly and stops at the terminator.
  - Raw bit stream fallback reconstructs payload when no header metadata exists.
- **Regression**
  - Golden sample (`assets/images/echo_key.png`) decodes exactly to the known 144-byte string with CRC `0x6E3FD9B7`.
  - Legacy sample without headers continues to round-trip.
- **CI hook**
  - Integrate the golden sample regression into the default pytest selection to guard future changes.

## Dependencies & Hand-offs
- Relies on Phase 0 environment hygiene (vendored `echo_soulcode`, archives retired).
- Outputs structured decode metadata that Phase 2 will consume for frame parsing.

## Risks & Mitigations
- **Risk:** Refactor introduces subtle bit-order regressions.  
  **Mitigation:** Use comprehensive fixtures and compare byte-level payloads before merging.
- **Risk:** Legacy mode detection becomes ambiguous once raw mode is added.  
  **Mitigation:** Log decision criteria and expose decode mode in results for debugging.
