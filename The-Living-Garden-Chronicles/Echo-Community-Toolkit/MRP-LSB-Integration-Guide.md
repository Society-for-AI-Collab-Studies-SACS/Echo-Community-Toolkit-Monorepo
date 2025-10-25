# MRP‑LSB Integration Guide: Multi‑Channel Resonance Protocol with Echo‑Community‑Toolkit

## 🔐 Protocol Overview

The Multi‑Channel Resonance Protocol (MRP) Phase‑A adds triple‑redundancy
verification to LSB steganography by distributing verification data across RGB
channels with cross‑channel validation.

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            Encode (Authoring)                               │
├────────────────────────────────────────────────────────────────────────────┤
│ message.txt + metadata.json                                                 │
│         │                                                                   │
│         ▼                                                                   │
│   encode_mrp()                                                              │
│   ├─ R: UTF‑8 message → base64 → header + CRC32                             │
│   ├─ G: JSON metadata → base64 → header + CRC32                             │
│   └─ B: ECC JSON { CRC(R), CRC(G), SHA256(msg), parity(R||G,b=8) } → base64 │
│         ▼                                                                   │
│   Pack frames → bitstreams (MSB→LSB)                                        │
│         ▼                                                                   │
│   LSB embed per channel (R/G/B)                                             │
│         ▼                                                                   │
│   stego.png                                                                 │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                            Decode (Verification)                            │
├────────────────────────────────────────────────────────────────────────────┤
│ stego.png                                                                   │
│   ▼                                                                         │
│ Extract LSB bitstreams (R/G/B)                                              │
│   ▼                                                                         │
│ Parse headers + payloads                                                    │
│   ▼                                                                         │
│ Base64‑decode R,G,B → (message, metadata, ecc)                              │
│   ▼                                                                         │
│ Recompute SHA256(message), CRC32(b64(R)), CRC32(b64(G)), parity(R||G)       │
│   ▼                                                                         │
│ Cross‑validate → boolean report                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

## Repo Placement (Flattened)

- Code and assets live under `hyperfollow-toolkit/lambda-vite/`:
  - `MRP_Seed_Package/mrp.py` — reference encoder/decoder library
  - `MRP_Seed_Package/mrp_cover.png` — sample cover image
  - `MRP_Seed_Package/mrp_stego.png` — sample stego (pre‑built)
  - `MRP_Seed_Package/README_MRP.md` — seed package notes
  - `mrp_lambda_state_sidecar.json` — example sidecar metadata
  - `mrp_lambda_*.json` — example payloads

The Vite UI lives in the same folder and is independent of MRP, but you can
pipe MRP decode reports into UI views as needed.

## Python Setup

Requirements (local or venv):

```
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r hyperfollow-toolkit/lambda-vite/requirements.txt
```

## Encode Example

From `hyperfollow-toolkit/lambda-vite/`:

```
# Tiny CLI (encode)
python MRP_Seed_Package/mrp.py encode \
  --cover MRP_Seed_Package/mrp_cover.png \
  --out   MRP_Seed_Package/mrp_stego.out.png \
  --message "I return as breath." \
  --metadata '{"agent":"echo","phase":"A","note":"demo"}' \
  --report  MRP_Seed_Package/encode_report.json
```

Output includes bit sizes per channel and ECC summary. The resulting
`MRP_Seed_Package/mrp_stego.out.png` contains the embedded payloads.

## Decode + Verify Example

Decode a stego image (your output or the provided sample):

```
# Tiny CLI (decode)
python MRP_Seed_Package/mrp.py decode \
  --image MRP_Seed_Package/mrp_stego.png \
  --json  MRP_Seed_Package/decode_report.json \
  --message-out  MRP_Seed_Package/decoded_message.txt \
  --metadata-out MRP_Seed_Package/decoded_metadata.json
```

### NPM Scripts (optional)

From `hyperfollow-toolkit/lambda-vite/` you can also run via npm:

```
# One-time Python venv setup (Linux/macOS)
npm run mrp:setup

# On Windows (PowerShell/CMD)
npm run mrp:setup:win

# Encode (pass args after --)
npm run mrp:encode -- \
  --cover MRP_Seed_Package/mrp_cover.png \
  --out   MRP_Seed_Package/mrp_stego.out.png \
  --message "Hello from npm" \
  --metadata '{"origin":"npm"}'

# Decode (pass args after --)
npm run mrp:decode -- \
  --image MRP_Seed_Package/mrp_stego.out.png \
  --json  MRP_Seed_Package/decode_report.json
```

The `report` object contains booleans: `message_sha256_ok`, `crc_r_ok`,
`crc_g_ok`, and `parity_ok`. Treat all‑true as verification success.

## Data Model (Channel Frames)

Each channel carries a compact header followed by a base64 payload:

- `magic`: 4 bytes `MRP1`
- `channel_id`: 1 byte (`'R'|'G'|'B'`)
- `flags`: 1 byte (bit0 → CRC32 present)
- `length`: 4 bytes (big‑endian, base64 payload length)
- `[crc32]`: 4 bytes if flags has CRC bit set (over base64 payload)
- `payload`: ASCII base64 bytes

ECC channel (`B`) JSON includes:

- `crc_r`, `crc_g`: CRC32 over base64 bodies of R and G
- `sha256_msg`: SHA‑256 over decoded message bytes
- `parity_over_rg_b64`: base64 of parity bytes over `R||G` base64 streams
- `parity_block`: block size for parity computation (default 8)

## Capacity & Image Constraints

- Capacity per channel is `width * height` bits (1 LSB per pixel/channel).
- The encoder checks capacity and fails fast if insufficient.
- Use PNG (lossless). JPEG re‑encoding will destroy LSB payloads.
- Avoid image transforms (resize, rotate) after embedding.

## Integrating with Echo‑Community‑Toolkit

You can integrate MRP encode/decode as a sidecar step that produces a JSON
report for downstream consumers (UI, logs, or further automation).

Suggested flow:

1) Authoring
- Create `message.txt` and `metadata.json` from your pipeline.
- Call `encode_mrp()` to produce a `stego.png` next to your artifact.

2) Verification
- Call `decode_mrp()` on received `stego.png`.
- Gate downstream actions on: `message_sha256_ok && crc_r_ok && crc_g_ok && parity_ok`.
- Persist the `report` JSON next to the asset for audit.

### Node/TypeScript Bridge (example)

If your toolkit is Node‑first, call the Python lib via a short subprocess. For
example, to decode and print a JSON report:

```
// decode-mrp.ts
import { spawnSync } from 'node:child_process'
const py = `import json\nfrom MRP_Seed_Package.mrp import decode_mrp\nimport sys\nres = decode_mrp(sys.argv[1])\nprint(json.dumps(res['report']))\n`
const out = spawnSync('python', ['-c', py, 'MRP_Seed_Package/mrp_stego.png'], { encoding: 'utf8' })
if (out.status !== 0) throw new Error(out.stderr)
console.log(out.stdout)
```

You can then parse the JSON and render it in your UI or logs.

## Surfacing in the Vite UI (optional)

The Vite app under `hyperfollow-toolkit/lambda-vite/` is self‑contained. If you
want to surface MRP verification status, add a small fetch/loader that reads a
JSON report (e.g., from a known path) and displays booleans next to the visual
state. Keep the ops math in `src/ops/ops.ts` the source of truth for the UI.

## Troubleshooting

- Insufficient capacity: use a larger cover image or reduce payloads.
- Non‑normalized images: confirm PNG and no post‑processing after embed.
- Decode CRC mismatch: the image likely changed; re‑embed from originals.

## Security Notes

- Do not embed secrets; MRP‑LSB is for integrity/novelty, not confidentiality.
- Keep pipelines hermetic and avoid network IO in tests.
- Do not commit generated artifacts under `dist/` unless part of a release.

## License / Attribution

Internal prototype for MRP‑LSB and Echo‑Community‑Toolkit integration.
© LIMNUS — Mythopoetic AI Companion.

---

## Phase‑A Spec Excerpt

### MRP Header Format (14 bytes)

```
Magic:    "MRP1" (4 bytes) - Multi-channel Resonance Protocol v1
Channel:  'R'/'G'/'B' (1 byte) - Channel identifier
Flags:    0x01 (1 byte) - Bit 0: HAS_CRC32
Length:   uint32 big-endian (4 bytes)
CRC32:    uint32 big-endian (4 bytes)
```

### Phase‑A Parity Algorithm

```python
# XOR-based parity for error detection
def phase_a_parity(R_b64: bytes, G_b64: bytes) -> bytes:
    P = bytearray(len(G_b64))
    for i in range(len(G_b64)):
        if i < len(R_b64):
            P[i] = R_b64[i] ^ G_b64[i]  # XOR where both exist
        else:
            P[i] = G_b64[i]              # G only where R ends
    return base64.b64encode(P)
```

Notes:
- The reference encoder `MRP_Seed_Package/mrp.py` now emits Phase‑A fields:
  - `crc_r`, `crc_g` (over base64 bodies),
  - `sha256_msg_b64` (SHA‑256 over R_b64),
  - `ecc_scheme: "parity"`,
  - `parity_block_b64` (as above).
- The verifier `lambda-vite/mrp_verify.py` cross‑checks these values and optional
  sidecar math.

### Complete Workflow Example

This section shows a self‑contained authoring flow to generate R/G payloads and
the B‑channel ECC fields. It assumes an LSB1 carrier for embedding.

```python
#!/usr/bin/env python3
import json
import base64
import hashlib
import zlib
from pathlib import Path

# Create test payloads
r_payload = {
    "type": "primary",
    "data": "Secret message in R channel",
    "timestamp": "2025-01-12T12:00:00Z"
}

g_payload = {
    "type": "secondary", 
    "data": "Additional data in G channel",
    "metadata": {"version": 1}
}

# Save R and G payloads
with open("mrp_lambda_R_payload.json", "w") as f:
    json.dump(r_payload, f, indent=2)

with open("mrp_lambda_G_payload.json", "w") as f:
    json.dump(g_payload, f, indent=2)

# Compute verification data
r_min = json.dumps(r_payload, separators=(",", ":")).encode()
g_min = json.dumps(g_payload, separators=(",", ":")).encode()
r_b64 = base64.b64encode(r_min)
g_b64 = base64.b64encode(g_min)

# Calculate CRCs and SHA
crc_r = format(zlib.crc32(r_b64) & 0xFFFFFFFF, "08X")
crc_g = format(zlib.crc32(g_b64) & 0xFFFFFFFF, "08X")
sha_r = hashlib.sha256(r_b64).hexdigest()

# Generate parity block
parity = bytearray(len(g_b64))
for i in range(len(g_b64)):
    if i < len(r_b64):
        parity[i] = r_b64[i] ^ g_b64[i]
    else:
        parity[i] = g_b64[i]
parity_b64 = base64.b64encode(parity).decode()

# Create B channel verification payload
b_payload = {
    "crc_r": crc_r,
    "crc_g": crc_g,
    "sha256_msg_b64": sha_r,
    "ecc_scheme": "parity",
    "parity_block_b64": parity_b64
}

with open("mrp_lambda_B_payload.json", "w") as f:
    json.dump(b_payload, f, indent=2)

print(f"Created MRP payloads:")
print(f"  R CRC32: {crc_r}")
print(f"  G CRC32: {crc_g}")
print(f"  SHA256:  {sha_r}")
```

You can then embed with any LSB1 tool (PNG, 1 bit per channel) or use the
reference encoder in `MRP_Seed_Package/mrp.py`.

### Verify with the Included Verifier

```bash
cd hyperfollow-toolkit/lambda-vite
python mrp_verify.py mrp_lambda_state.png \
  --R mrp_lambda_R_payload.json \
  --G mrp_lambda_G_payload.json \
  --B mrp_lambda_B_payload.json \
  --sidecar mrp_lambda_state_sidecar.json \
  --json mrp_verify_report.json
```

Verification returns a JSON report with checks like:

```json
{
  "inputs": {"image": "mrp_lambda_state.png", "R": "mrp_lambda_R_payload.json", "G": "mrp_lambda_G_payload.json", "B": "mrp_lambda_B_payload.json", "sidecar": "mrp_lambda_state_sidecar.json"},
  "computed": {"crc_r": "A1B2C3D4", "crc_g": "E5F6A7B8", "sha256_r_b64": "abc123...", "parity_b64_head": "XYZ789..."},
  "checks": {"crc_r_ok": true, "crc_g_ok": true, "sha256_r_b64_ok": true, "ecc_scheme_ok": true, "parity_block_ok": true},
  "mrp_ok": true
}
```

### Error Detection & Benefits (Phase‑A)

- Triple‑redundancy: CRC32 (fast), SHA‑256 (tamper), XOR parity (bit‑level).
- Channel isolation: corruption in one channel is localized.
- Header validation ensures structural integrity (magic, flags, lengths).
