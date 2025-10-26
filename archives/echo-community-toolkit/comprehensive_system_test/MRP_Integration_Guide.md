# MRP-LSB Integration Guide: Multi-Channel Resonance Protocol with Echo-Community-Toolkit

## 🔐 Protocol Overview

The **Multi-Channel Resonance Protocol (MRP)** Phase-A adds triple-redundancy verification to LSB steganography by distributing verification data across RGB channels with cross-channel validation.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                MRP Phase-A Structure             │
├─────────────────────────────────────────────────┤
│  R Channel: Primary payload + MRP1 header       │
│  G Channel: Secondary payload + MRP1 header     │
│  B Channel: Verification metadata:              │
│    ├─ CRC32(R_b64)                             │
│    ├─ CRC32(G_b64)                             │
│    ├─ SHA256(R_b64)                            │
│    └─ XOR Parity Block                         │
└─────────────────────────────────────────────────┘
```

## MRP Header Format (14 bytes)

```
Magic:    "MRP1" (4 bytes) - Multi-channel Resonance Protocol v1
Channel:  'R'/'G'/'B' (1 byte) - Channel identifier
Flags:    0x01 (1 byte) - Bit 0: HAS_CRC32
Length:   uint32 big-endian (4 bytes)
CRC32:    uint32 big-endian (4 bytes)
```

## Phase-A Parity Algorithm

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

## Complete Workflow Example

### Step 1: Prepare Test Data

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

### Step 2: Embed with LSB Toolkit

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, "src")
from lsb_encoder_decoder import LSBCodec
from pathlib import Path
import json
import base64

# Create cover image
codec = LSBCodec(bpc=1)
cover = codec.create_cover_image(512, 512, "noise")
cover.save("mrp_cover.png", "PNG")

# Encode each channel separately
channels = ['R', 'G', 'B']
payloads = []

for channel in channels:
    # Load payload
    with open(f"mrp_lambda_{channel}_payload.json", "r") as f:
        payload = json.load(f)
    
    # Create MRP1 header
    magic = b"MRP1"
    channel_byte = channel.encode('ascii')
    flags = 0x01  # CRC32 enabled
    
    # Encode to base64
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = base64.b64encode(payload_json.encode())
    
    # Build complete message with header
    import struct
    header = magic + channel_byte + bytes([flags])
    header += struct.pack(">I", len(payload_b64))
    header += struct.pack(">I", zlib.crc32(payload_b64) & 0xFFFFFFFF)
    
    payloads.append(header + payload_b64)

# Combine and embed (simplified - real MRP would use channel-specific embedding)
combined = b"".join(payloads)
message = base64.b64decode(combined).decode('utf-8', errors='ignore')

# For demo, encode combined message
result = codec.encode_message(
    Path("mrp_cover.png"),
    json.dumps({"R": r_payload, "G": g_payload, "B": b_payload}),
    Path("mrp_lambda_state.png"),
    use_crc=True
)

print(f"Created MRP stego image: mrp_lambda_state.png")
print(f"Embedded {result['payload_length']} bytes")
```

### Step 3: Create Sidecar Metadata

```python
# Generate sidecar JSON
sidecar = {
    "file": "mrp_lambda_state.png",
    "sha256_msg_b64": sha_r,
    "channels": {
        "R": {
            "payload_len": len(r_b64),
            "used_bits": (len(r_b64) + 14) * 8,
            "capacity_bits": 512 * 512
        },
        "G": {
            "payload_len": len(g_b64),
            "used_bits": (len(g_b64) + 14) * 8,
            "capacity_bits": 512 * 512
        },
        "B": {
            "payload_len": len(json.dumps(b_payload).encode()),
            "used_bits": (len(json.dumps(b_payload).encode()) + 14) * 8,
            "capacity_bits": 512 * 512
        }
    },
    "headers": {
        "R": {"magic": "MRP1", "channel": "R", "flags": 1},
        "G": {"magic": "MRP1", "channel": "G", "flags": 1},
        "B": {"magic": "MRP1", "channel": "B", "flags": 1}
    }
}

with open("mrp_lambda_state_sidecar.json", "w") as f:
    json.dump(sidecar, f, indent=2)
```

### Step 4: Verify with MRP Verifier

```bash
# Run verification
python mrp_verify.py mrp_lambda_state.png \
  --R mrp_lambda_R_payload.json \
  --G mrp_lambda_G_payload.json \
  --B mrp_lambda_B_payload.json \
  --sidecar mrp_lambda_state_sidecar.json \
  --json mrp_verify_report.json

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ MRP verification PASSED"
else
    echo "❌ MRP verification FAILED"
fi
```

## Verification Report Structure

```json
{
  "inputs": {
    "image": "mrp_lambda_state.png",
    "R": "mrp_lambda_R_payload.json",
    "G": "mrp_lambda_G_payload.json",
    "B": "mrp_lambda_B_payload.json",
    "sidecar": "mrp_lambda_state_sidecar.json"
  },
  "computed": {
    "crc_r": "A1B2C3D4",
    "crc_g": "E5F6G7H8",
    "sha256_r_b64": "abc123...",
    "parity_b64_head": "XYZ789..."
  },
  "checks": {
    "crc_r_ok": true,
    "crc_g_ok": true,
    "sha256_r_b64_ok": true,
    "ecc_scheme_ok": true,
    "parity_block_ok": true,
    "sidecar_sha256_ok": true,
    "sidecar_used_bits_math_ok": true,
    "sidecar_capacity_bits_ok": true,
    "sidecar_header_magic_ok": true,
    "sidecar_header_flags_crc_ok": true
  },
  "mrp_ok": true
}
```

## Security Benefits

### Triple-Redundancy Verification
1. **CRC32 Cross-Check**: Fast integrity validation
2. **SHA-256 Hash**: Cryptographic tamper detection  
3. **XOR Parity**: Bit-level error detection

### Attack Resistance
- **Channel Isolation**: Compromise of one channel doesn't affect others
- **Multi-Point Verification**: Multiple independent checks must align
- **Metadata Validation**: Sidecar ensures structural integrity

## Error Detection Capabilities

| Error Type | Detection Method | Recovery |
|------------|------------------|----------|
| Single bit flip | XOR parity | Locatable |
| Channel corruption | CRC32 mismatch | Channel isolation |
| Truncation | Length mismatch | Immediate detection |
| Substitution | SHA-256 failure | Cryptographic proof |
| Header damage | Magic/flags check | Protocol violation |

## Performance Characteristics

- **Overhead**: ~14 bytes per channel (42 bytes total)
- **Verification Time**: O(n) where n = payload size
- **Memory Usage**: 3× payload size during verification
- **CPU Usage**: Minimal (CRC32 + SHA256 + XOR)

## Integration with Echo-Community-Toolkit

```python
# Enhanced LSB encoder with MRP support
class MRPLSBCodec(LSBCodec):
    def encode_mrp(self, cover_path, r_data, g_data, output_path):
        """Encode with MRP Phase-A protocol"""
        # Generate verification metadata
        b_data = self._generate_mrp_metadata(r_data, g_data)
        
        # Embed in channels
        self._embed_channel(cover_path, 'R', r_data)
        self._embed_channel(cover_path, 'G', g_data)
        self._embed_channel(cover_path, 'B', b_data)
        
        # Generate sidecar
        sidecar = self._create_sidecar(r_data, g_data, b_data)
        
        return {
            "image": output_path,
            "sidecar": sidecar,
            "mrp_ready": True
        }
```

## Best Practices

1. **Always generate sidecar** - Essential for complete verification
2. **Use consistent JSON minification** - `separators=(",", ":")` 
3. **Verify immediately after encoding** - Catch errors early
4. **Store verification reports** - Audit trail for integrity
5. **Check all 10 verification points** - Don't skip checks

## Troubleshooting

### CRC Mismatch
- Ensure Base64 encoding is consistent
- Check byte order (big-endian required)
- Verify JSON minification matches

### Parity Block Failure
- Confirm XOR operation order
- Check R_b64/G_b64 length handling
- Verify Base64 padding

### Sidecar Math Errors
- Formula: `used_bits = (payload_len + 14) * 8`
- Capacity: `width * height` for LSB1
- All channels must match PNG dimensions

## Command-Line Quick Reference

```bash
# Verify with all checks
python mrp_verify.py image.png --R R.json --G G.json --B B.json --sidecar sidecar.json --json report.json

# Minimal verification (no sidecar)
python mrp_verify.py --R R.json --G G.json --B B.json

# Check exit code in scripts
python mrp_verify.py ... && echo "PASS" || echo "FAIL"
```

---

**MRP Phase-A Specification v1.0**
**Compatible with LSB1 Protocol**
**Echo-Community-Toolkit Integration Ready**
