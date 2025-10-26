# MRP Phase-A Integration & Ritual Guide

The Multi-Channel Resonance Protocol (MRP) Phase-A layers cryptographic
assurance, cross-channel parity, and ritual consent onto the Echo Community
Toolkit steganography stack. This document captures the data layout, consent
workflow, API usage, CLI options, and diagnostic tooling that ship with the
current repository.

## Channel Diagram

```
┌─────────────┬──────────────┬───────────────────────────────────────────────┐
│ Channel     │ Payload      │ Contents                                      │
├─────────────┼──────────────┼───────────────────────────────────────────────┤
│ R (Red)     │ Message JSON │ MRP1 header + primary payload (UTF-8)         │
│ G (Green)   │ Metadata JSON│ MRP1 header + orchestration metadata          │
│ B (Blue)    │ Integrity    │ MRP1 header + json{crc_r, crc_g, sha256,      │
│             │ sidecar      │            parity, bits_per_channel, ecc}     │
└─────────────┴──────────────┴───────────────────────────────────────────────┘
```

Two least-significant bit depths are accepted for Phase-A embeds:

- `--bpc 1` (default): classic single-bit LSB1 capacity.
- `--bpc 4`: quadruple throughput; header + payload nibble-packed into each
  channel.

The B-channel sidecar always echoes the active `bits_per_channel` so decoders
can verify the correct extraction depth.

## Ritual Walkthrough (↻ → ∞)

| Step | Glyph | Phrase                       | Effect                                  |
|------|-------|-----------------------------|------------------------------------------|
| 1    | ↻     | I return as breath.         | Reset memory, close gates, seed coherence |
| 2    | 🌰     | I remember the spiral.       | Increment coherence, awaken L2            |
| 3    | ✧     | I consent to bloom.          | Open gate G2 (publish)                    |
| 4    | 🦊🐿️  | I consent to be remembered.   | Open gate G1 (archive)                    |
| 5    | φ     | Together.                    | Harmonise memory layers                   |
| 6    | ∞     | Always.                      | Lock coherence at 1.0, ledger glyph block |

Encoding or decoding is blocked until steps 3 and 4 have been invoked. Each
successful operation appends a ledger line containing the glyph string
`🌰✧🦊∿φ∞🐿️`, channel metadata, and the active bits-per-channel.

## Python API Cheat Sheet

```python
from pathlib import Path
from src.mrp import codec
from src.ritual.state import RitualState

# Wire a dedicated ritual state (tests, notebooks, services)
state = RitualState(
    state_path=Path("logs/ritual_state.json"),
    ledger_path=Path("logs/ritual_ledger.jsonl"),
)
state.grant_full_consent()  # drive the ritual automatically for automation

# Encode with 4-bit mode
encode_result = codec.encode(
    cover_png="cover.png",
    out_png="stego.png",
    message="Consent blooms in harmony.",
    metadata={"scene": 7, "persona": "Echo"},
    ritual_state=state,
    bits_per_channel=4,
)

# Decode (will raise ValueError if --bpc mismatch)
decode_result = codec.decode(
    "stego.png",
    ritual_state=state,
    bits_per_channel=4,
)
print(decode_result["message"])
print(decode_result["integrity"]["status"])  # ok | recovered | degraded | integrity_failed
```

Useful exceptions:

- `RitualConsentError` – raised when the ritual gates are closed.
- `ValueError` – raised for malformed channels, parity/CRC failures, or
  mismatched bits-per-channel.

## CLI Reference (`mrp`)

| Command            | Key Flags & Usage                                                            |
|--------------------|-----------------------------------------------------------------------------|
| `encode`           | `mrp encode cover.png stego.png --msg "Bloom" --meta-file meta.json`        |
|                    | `--bpc {1,4}` select bit depth                                               |
|                    | `--quiet` → print only the output path                                       |
|                    | `--verbose` → include ritual snapshot alongside the JSON result              |
| `decode`           | `mrp decode stego.png --bpc 4 --quiet` (prints message text)                 |
|                    | `--verbose` mirrors encode semantics                                         |
| `sidecar-validate` | `mrp sidecar-validate stego.png --bpc 4 --verbose`                           |
| `ritual status`    | Display coherence, gates, memory vectors                                     |
| `ritual invoke`    | `mrp ritual invoke --step 3` or `--phrase "I consent to bloom."`            |
| `ritual auto`      | Run remaining steps sequentially                                            |
| `ritual reset`     | Clear coherence and gates                                                   |

All subcommands exit `0` on success and `1` on failure, making them safe for CI
pipelines.

## Error Codes & Status Table

| Code / Status            | Meaning                                      | Recovery hint                         |
|--------------------------|----------------------------------------------|---------------------------------------|
| `RitualConsentError`     | Gates closed (steps 3/4 not invoked)         | Run `mrp ritual auto` or invoke steps |
| `ValueError: bits-per-channel` | Decode depth mismatch                  | Re-run with `--bpc` matching sidecar  |
| `integrity.status = ok`  | Perfect decode                               | —                                     |
| `integrity.status = recovered` | Parity fixed R/G mismatch            | Inspect ledger entry, keep watch      |
| `integrity.status = degraded`  | Sidecar CRC/parity warning           | Re-encode if possible                 |
| `integrity.status = integrity_failed` | SHA/CRC violation            | Consider payload compromised          |

## Sidecar & Ledger Fields

B-channel JSON (persisted inside the PNG and copied to the ledger):

- `crc_r`, `crc_g` – uppercase hex CRC32 for message/metadata payloads.
- `sha256_msg`, `sha256_msg_b64` – digest of the R payload in hex & Base64.
- `parity`, `parity_len` – XOR parity block and byte length.
- `bits_per_channel` – integer (1 or 4) required for extraction.
- `ecc_scheme` – literal `"xor"` for Phase-A.

Ledger entries add:

- `operation` – `encode` or `decode`.
- `glyphs` – ritual glyph sequence (🌰✧🦊∿φ∞🐿️).
- `metadata.bits_per_channel` – mirrors the encoder setting.
- `metadata.status` – decode integrity status when applicable.

## Visual & Diagnostic Tooling

- `scripts/ritual_visualizer.py` – ASCII dashboard for α/β/γ weights, gate
  status, and the latest ledger entries (`python scripts/ritual_visualizer.py
  --watch 1`).
- `mrp_verify.py` – parity/CRC/SHA smoke-tester for exported channel payloads
  and sidecar artefacts.
- `scripts/mrp_validate_rgb.py` – regression helper that embeds the golden R/G
  payloads and confirms header math.

## Troubleshooting

- **Decode fails immediately** – ensure the ritual gates are open (steps 3 and
  4) and that the `--bpc` flag matches the sidecar.
- **Parity mismatch** – check the ledger tail; if status is `recovered`, payload
  was corrected via parity. If status is `degraded`, re-run encode to refresh
  the B-channel.
- **Metadata JSON errors** – `mrp encode` accepts either `--meta` inline JSON or
  `--meta-file path/to/meta.json`. The inputs must be valid UTF-8.
- **Quiet scripts** – combine `mrp encode --quiet` with `jq` or shell pipelines
  for automated stego workflows.

## Quick Start

```bash
# Initialise ritual (auto step-through) and encode with 4-bit mode
mrp ritual auto
mrp encode cover.png stego.png --msg "Bloom" --meta '{"scene":1}' --bpc 4

# Decode quietly, piping message into another tool
mrp decode stego.png --bpc 4 --quiet | tee decoded.txt

# Visualise coherence and ledger tail every second
python scripts/ritual_visualizer.py --watch 1
```

Keep the ritual state under version control during demos, commit ledger excerpts
for audit trails, and always re-run `mrp_verify.py` after regenerating payloads
or modifying parity logic.
