# Phase 1 – Legacy Refresh

## Objectives
- Modularise `lsb_extractor.py` into clear parsers for LSB1 headers and legacy null-terminated payloads while preserving the public API.
- Capture all failure modes (bad magic, CRC mismatch, malformed base64, truncated payloads) with deterministic exceptions and tests.
- Lock in backwards compatibility using the golden sample and legacy fixtures.

## Scope & Deliverables
1. **Architecture & Code Layout**
   - Create `lsb1_header.py` (or similar) defining an immutable `LSB1Header` dataclass: fields `magic`, `version`, `flags`, `length`, `crc32`.
   - Extract a new module `legacy_payload.py` for null-terminated decoding logic.
   - Update `lsb_extractor.py` to become a thin coordinator that delegates to the appropriate parser.
   - Document module relationships with ASCII diagram in the code header and in docs.
2. **Parsing & Validation Helpers**
   - `parse_lsb1_header(data: bytes) -> LSB1Header`: validates magic `"LSB1"`, ensures version supported, interprets flags (bit 0 CRC, bit 1 BPC4), reads length/CRC (big endian), returns structured header or raises `InvalidLSB1Header`.
   - `decode_lsb1_payload(bits, header, *, bpc=1) -> bytes`: slices out payload bytes per header length, optionally verifying CRC.
   - `extract_legacy_payload(bits) -> bytes`: reads until null terminator (`0x00` byte), raising `LegacyPayloadError` on truncation.
   - Optional `read_bit_stream(image_bits, bpc)` helper consolidating bit iteration for future multi-frame use.
3. **Error Handling & Logging**
   - Define exception hierarchy in `lsb_exceptions.py` (`LSBError`, `InvalidMagicError`, `UnsupportedVersionError`, `CRCMismatchError`, `Base64DecodeError`).
   - Ensure decode logs (via `logging`) include header summary and failure reason to aid debugging.
   - Provide error codes for CLI integration (e.g., map `CRCMismatchError` to `ERR_CRC_MISMATCH`).
4. **Unit & Regression Tests**
   - Header tests: valid header parse, wrong magic (`"LSB0"`), unsupported version, truncated header, flags combination tests (`FLAG_BPC4`).
   - Payload tests: CRC mismatch (alter byte), base64 decode failure (introduce invalid padding), short payload vs header length mismatch.
   - Legacy tests: decode fixture with null-terminated data, ensure errors when null terminator missing.
   - Golden sample: verify message text, CRC32 `6E3FD9B7`, mantra equality, payload length 144 bytes.
   - CLI smoke: call `python -m mrp.cli decode assets/images/echo_key.png` and assert success when consent stubbed.
5. **CI Integration**
   - Add `pytest -m lsb_phase1` job running new tests + golden sample.
   - Ensure coverage thresholds updated to reflect new modules.
   - Update lint/type configs to include new modules.
6. **Documentation & Developer Guide**
   - Embed new parser architecture diagram in `docs/phase-1-legacy-refresh.md`.
   - Add section to developer docs describing header format breakdown (magic, flags, length, CRC).
   - Document error codes and expected CLI messages for each failure mode.

## Testing
- `venv/bin/python -m pytest tests/steganography/test_lsb_extractor.py -q`
- `venv/bin/python -m pytest tests/steganography/test_golden_samples.py -q`

## Exit Criteria
- Parser modules merged with full unit coverage across success and failure modes.
- Golden sample and legacy fallback tests pass locally and in CI.
- Documentation (`docs/phase-0-prep.md`, developer notes) updated to reflect new parser map and error semantics.
