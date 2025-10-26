# Multi-Channel Resonance Protocol (MRP) — Phase A

**Status:** Draft (stubs) — 2025-10-13T05:14:22.138385Z

## Overview
MRP multiplexes message, metadata, and integrity into RGB channels of an LSB1-compatible carrier.
Phase A introduces a per-channel JSON frame with CRC; ECC is deferred.

## Channel Roles (Phase A)
| Channel | Role     | Contents                 |
|---------|----------|--------------------------|
| R       | Message  | UTF‑8 text payload       |
| G       | Metadata | JSON (sorted keys)       |
| B       | Integrity| CRC mirror + parity byte |

## Frame Format (JSON)
```json
{
  "magic": "MRP1",
  "channel": "R|G|B",
  "flags": <bitfield>,  // 0x01:CRC, 0x02:ECC(reserved)
  "length": <int>,      // raw payload byte length
  "crc32": "8-hex",     // present when CRC flag set
  "payload_b64": "<base64>"
}
```

## Parity (temporary ECC)
Byte-wise XOR parity computed over `base64(R_payload) + base64(G_payload)`.
Stored in B JSON as two-hex-digit string `parity` alongside `crc_r`, `crc_g`.

## Adapter (Phase A stub)
The PNG LSB adapter must reuse the project’s canonical plane order (row-major, RGB, MSB-first)
and capacity math. The stubs intentionally raise `NotImplementedError` to prevent silent fallback.

## Compatibility
- LSB1 golden sample remains unchanged and must continue to decode to the canonical mantra with CRC32 `6E3FD9B7`.
- MRP code paths are additive and do not alter LSB1 paths.

## Next
- Implement `src/mrp/adapters/png_lsb.py` plane I/O binding to existing LSB encoder/decoder.
- Add `scripts/verify_updated_system.py` MRP block invoking `encode`/`decode` and printing “MRP: PASS” when checks succeed.
