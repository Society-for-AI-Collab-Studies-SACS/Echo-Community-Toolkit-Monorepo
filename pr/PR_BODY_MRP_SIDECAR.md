Title: feat(mrp): Phase‑A sidecar helpers + docs; update submodule pointer

Summary
- Implement Phase‑A sidecar helpers aligned to spec:
  - Parity over concatenated base64 payload strings: (r.payload_b64 + g.payload_b64).encode()
  - sha256_msg_b64 = base64(SHA‑256 over raw R payload bytes)
  - crc_r / crc_g taken from headers (uppercase 8‑hex)
  - ecc_scheme = "parity"
- Update docs to explicitly state parity definition and required keys.
- Bump Echo‑Community‑Toolkit submodule pointer to include these changes.

Submodule commit
- Echo‑Community‑Toolkit @ d76c02b (feat+docs for Phase‑A sidecar)

Echo Toolkit changes (in submodule)
- src/mrp/sidecar.py
  - generate_sidecar: parity over base64 strings; sha256_msg_b64; header CRCs
  - validate_sidecar: checks updated; required keys minimal
- src/mrp/meta.py
  - sidecar_from_headers aligned with Phase‑A minimal schema
- README_MRP_SCAFFOLD.md, README_SOURCE_SCAFFOLD.md, MRP-LSB-Integration-Guide.md, HOW_TO_BE_YOU.md
  - Document Phase‑A minimal sidecar and parity definition

Why
- Bring the Echo Toolkit Phase‑A sidecar into compliance with the current spec and make the definition of parity + required keys explicit across code and docs.

Testing
- Local smoke test: generate_sidecar/validate_sidecar round‑trip returns valid with expected details.
- Full pytest to be run in CI (no env network/pip here). No interface breaks.

Notes
- Extended descriptor keys (carrier/channels/phase) remain optional and are not required by the validator.

