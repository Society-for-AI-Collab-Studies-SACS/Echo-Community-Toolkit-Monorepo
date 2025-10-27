# Phase 2 – Frame Infrastructure

Phase 2 introduces the Multi-Channel Resonance Protocol (MRP) frame format and extends the codec to support multi-frame layouts across RGB channels while remaining backward-compatible with legacy single-frame LSB1 payloads.

## Objectives
- Define an `MRPFrame` binary structure with magic, channel id, flags, payload length, and optional CRC.
- Extend the encoder/decoder to emit and consume multi-frame payloads spanning R/G/B channels.
- Generalise capacity and bit-packing helpers to work with both 1-bit and 4-bit modes.

## Implementation Plan
1. **Frame definition**
   - Create `MRPFrame` dataclass/helpers encapsulating header pack/unpack logic.
   - Header layout: `magic(4="MRP1")`, `channel(1)`, `flags(1)`, `length(4)`, `crc32(4, optional if flag enabled)`.
   - Document valid flag bits (e.g., `CRC_ENABLED`, `BPC4`, `PARITY_PRESENT`) for downstream phases.
2. **Codec updates**
   - Update `LSBCodec.encode` to accept a mode argument (`single`, `multi`) and optional channel payload map.
   - In multi-frame mode, split inputs: primary message → R, metadata → G, integrity skeleton → B (placeholder until Phase 3 populates data).
   - During decode, inspect each channel stream; if it begins with "MRP1", parse via `MRPFrame`, otherwise fall back to LSB1 legacy logic.
   - Normalise decode results into a structured object: `{mode, frames, metadata, integrity}`.
3. **Capacity management**
   - Refactor bit-packing helpers so both encoder and decoder share a single implementation aware of `bits_per_channel`.
   - Compute per-channel capacity when splitting payloads; ensure total bits ≤ image capacity calculated via `floor(W*H*channels*bpc/8)`.
   - Introduce guardrails that raise descriptive errors when payloads exceed capacity in single or multi mode.
4. **Backwards compatibility**
   - Maintain seamless decode for images containing only `LSB1` headers.
   - Ensure encode defaults to legacy single-frame unless multi-frame explicitly requested.

## Testing Strategy
- **Unit tests**
  - Pack/unpack of `MRPFrame` headers for each channel with and without CRC flag.
  - Encode/decode round-trip in single-frame mode to verify no regressions from Phase 1.
  - Multi-frame encode/decode using synthetic payloads for R/G/B verifying frame metadata and payload separation.
  - Capacity overflow tests for both modes.
- **Integration**
  - Update golden sample tests to confirm they still pass when decoder auto-detects legacy format.
  - Add fixture covering multi-frame image with dummy metadata/integrity payloads.

## Dependencies & Hand-offs
- Builds on Phase 1 structured header parsing and metadata extraction.
- Provides the scaffolding Phase 3 will use to embed CRC, SHA-256, and parity data in the B channel.

## Risks & Mitigations
- **Risk:** Increased complexity in codec paths introduces regressions.  
  **Mitigation:** Keep single vs multi logic segregated with exhaustive tests for each path.
- **Risk:** Capacity calculations drift across modules.  
  **Mitigation:** Centralise the helper in a shared utility and exercise via property-based tests where feasible.
