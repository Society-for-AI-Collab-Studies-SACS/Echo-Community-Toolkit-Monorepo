# Phase 3 – Integrity & ECC

## Objectives
- Populate the B-channel with integrity metadata (CRC32, SHA-256, XOR parity) for the R/G payloads.
- Teach the decoder to perform parity-based repair and report detailed integrity status.
- Exercise corruption scenarios through automated fixtures.

## Scope & Deliverables
1. **Sidecar Augmentation**
   - Extend `mrp.meta.sidecar_from_headers` to compute:
     - `crc_r`, `crc_g` (uppercase hex strings, 8 chars).
     - `sha256_msg` (hex) and `sha256_msg_b64`.
     - `parity` (uppercase hex string of XOR parity bytes), `parity_len`.
     - `ecc_scheme="xor"`, `bits_per_channel`.
     - Optional `frame_version=1` for future upgrades.
   - Serialize B-frame payload as compact JSON (sorted keys) and ensure deterministic encoding for test comparisons.
2. **Decoder Repair Logic**
   - Implement helper `xor_recover(parity_bytes, healthy_payload, expected_len)` returning reconstructed bytes.
   - Flow:
     1. Parse frames.
     2. Validate CRC for R/G; record mismatches.
     3. If exactly one payload fails, attempt parity repair.
     4. Validate repaired payload via CRC and SHA.
     5. Build integrity report dataclass with fields:
        - `status`: `"ok"`, `"recovered_with_parity"`, `"degraded"`, `"integrity_failed"`.
        - `crc_checks`: per-channel boolean and expected/actual values.
        - `parity`: expected hex, actual hex, match boolean.
        - `sha256`: expected hex/b64, actual hex/b64, ok boolean.
        - `repaired_bytes`: count, channel.
        - `errors`: list of messages (e.g., "CRC mismatch after parity repair").
   - Ensure decoder gracefully handles missing parity data (treat as degraded).
3. **Fixtures & Fault Injection**
   - Add utilities in `tests/util/stego_mutations.py`:
     - `flip_bits(img_path, channel, indices)` (bit-level).
     - `zero_channel(img_path, channel)`.
     - `tamper_parity(img_path, hex_patch)`.
   - Create canonical corrupted fixtures:
     - `corrupt_r_single_bit.png`
     - `corrupt_g_single_bit.png`
     - `corrupt_parity.png`
     - `corrupt_b_sidecar.png`
     - `zeroed_g_channel.png`
   - Document the corruption operations so QA can reproduce.
4. **CLI/SDK Surface**
   - CLI: add `--integrity-report` to emit JSON to stdout or file.
   - CLI output (default) summarises status, corrected bytes, parity verdict.
   - SDK: `DecodeResult.integrity` property returning dataclass; `decode_mrp(..., report_handler=callable)` hook.
   - Ensure exit codes reflect severity (`0` success / recovered, `2` degraded, `3` integrity_failed).
5. **Documentation**
   - Update docs with flow diagram: decode → CRC check → parity repair → SHA verification → status.
   - Provide table explaining each status and recommended operator action.

## Testing
- `pytest tests/steganography/test_mrp_codec.py -q` expanded to cover new fixtures.
- Dedicated tests verifying parity math (round-trip parity bytes, parity_len correctness).
- Tests for SHA mismatch reporting when parity recovers CRC but hash differs.
- Integration test that corrupts payloads, runs CLI decode, and inspects exit codes/messages.

## Exit Criteria
- Decoder successfully repairs single-channel corruptions and reports failures otherwise.
- Integrity metadata consistently emitted and consumed across encode/decode.
- CI corruption suite passes (bit flip, parity tamper, channel loss).
