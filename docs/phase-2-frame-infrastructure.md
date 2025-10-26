# Phase 2 – Frame Infrastructure

## Objectives
- Define a binary `MRPFrame` abstraction that encapsulates per-channel metadata (magic, channel id, flags, length, CRC).
- Extend the codec to encode/decode both single-frame LSB1 and multi-frame MRP layouts without breaking backwards compatibility.
- Unify bit-packing and capacity logic for 1-bit and 4-bit modes.

## Scope & Deliverables
1. **Frame Abstraction**
   - Introduce `mrp/frame.py` containing:
     - `ChannelId` Enum (`R`, `G`, `B`).
     - `FrameFlags` with bit masks (`CRC_ENABLED = 0x01`, future reserved bits).
     - `MRPFrame` dataclass storing header + payload.
   - Methods: `MRPFrame.to_bytes()`, `MRPFrame.from_bytes(buffer: bytes, *, expect_crc: bool | None)` with rigorous validation (magic `"MRP1"`, length bounds, CRC verification when flag set).
   - Provide convenience constructors: `MRPFrame.message(payload, flags)`, `.metadata(...)`, `.integrity(...)`.
   - Add helper `split_frames(bit_stream)` returning dictionary keyed by channel.
2. **Encoder/Decoder Refactor**
   - Extend `mrp.codec` with strategy classes:
     - `LSB1SingleStrategy` (legacy).
     - `MRPMultiStrategy` (new).
   - `LSBCodec.encode()` chooses strategy based on kwargs (`mode`, `metadata`, `integrity`).
   - Multi-frame encode steps:
     1. Build R frame (message) with optional CRC.
     2. Build G frame (metadata JSON).
     3. Build B frame (integrity JSON produced by Phase 3 design placeholder).
     4. Pack frames into channel-specific bit streams respecting bits-per-channel.
   - Decode path inspects first bytes; if header `"MRP1"` found, parse into frames, assemble outputs, populate structured response object `DecodeResult(message, metadata, integrity, frames)`.
   - Ensure fallback: if `"LSB1"` or legacy path detected, short-circuit to existing single-frame decode.
3. **Bit Packing & Capacity**
   - Implement `capacity.py`:
     - `total_capacity(width, height, bpc, channels=3)`.
     - `channel_capacity(total_capacity, strategy)` e.g. equal split or weighted allocation.
   - Update packing utilities to accept `bpc` parameter and produce iterables for each channel.
   - Add tests verifying 1-bit vs 4-bit packing all share same helpers.
4. **Metadata & Integrity Structures**
   - Define `MRPEncodeRequest` (message, metadata dict, integrity options, mode, bpc).
   - Define `MRPDecodeResult` with explicit fields and `to_dict()` for CLI/SDK.
   - Ensure metadata is always JSON serialised with canonical ordering.
5. **CLI / SDK Exposure**
   - Update CLI commands:
     - `encode --mode single|mrp --bpc 1|4 --meta FILE|JSON`.
     - Provide `--show-frames` option to print header summaries.
   - SDK to expose `encode_mrp` and `decode_mrp` convenience wrappers.
6. **Documentation & Diagrams**
   - Include ASCII diagram showing image -> channel bit streams -> MRP frames -> sidecar.
   - Update README and `docs/phase-5-polish-ux.md` with new CLI options.

## Testing
- Unit tests:
  - `test_mrp_frame_roundtrip()` for all channels and flag combinations.
  - `test_mrp_frame_crc_validation()` ensuring CRC flag toggles behaviour.
- Strategy tests:
  - Single vs multi encode/decode parity.
  - Multi-frame decode returns structured result with expected payloads.
- Capacity tests:
  - Validate errors when payload exceeds per-channel capacity.
  - 1-bit vs 4-bit equivalence using golden sample sized images.
- CLI tests:
  - `pytest tests/cli/test_encode_decode.py -k "mrp"` verifying flags.
- Regression tests:
  - Golden sample remains decodable.
  - New sample (R/G/B frames) verifies metadata and integrity placeholders.

## Exit Criteria
- Codec strategies merged with thorough tests across modes and bit depths.
- Capacity helper documented and validated.
- CLI/SDK documentation updated; diagrams committed.
- No regressions in legacy decoding paths (CI ensures single-frame tests still pass).
