# MRP-LSB Quick Reference Card

## 🚀 Quick Start

```bash
# 1. Test the verifier
python test_mrp_verification.py

# 2. Verify existing MRP data
python mrp_verify.py image.png \
  --R R_payload.json \
  --G G_payload.json \
  --B B_payload.json \
  --sidecar sidecar.json \
  --json report.json
```

## 📊 MRP Phase-A Protocol

### Channel Allocation
- **R Channel**: Primary payload + MRP1 header
- **G Channel**: Secondary payload + MRP1 header  
- **B Channel**: Verification metadata (CRCs + SHA + Parity)

### Verification Layers
1. **CRC32**: Fast integrity check
2. **SHA-256**: Cryptographic verification
3. **XOR Parity**: Bit-level error detection
4. **Sidecar**: Structural validation

## 🔧 Integration with Echo-Toolkit

### Enhanced Encoding
```python
# Standard LSB
codec.encode_message(cover, message, output)

# With MRP verification
mrp_metadata = generate_mrp_verification(message)
codec.encode_message(cover, mrp_metadata, output)
```

### Verification Flow
```
LSB Decode → Extract Channels → Generate Payloads → MRP Verify
```

## ✅ All Verification Checks

| Check | Purpose | Critical? |
|-------|---------|-----------|
| `crc_r_ok` | R channel integrity | Yes |
| `crc_g_ok` | G channel integrity | Yes |
| `sha256_r_b64_ok` | Cryptographic validation | Yes |
| `ecc_scheme_ok` | Protocol compliance | Yes |
| `parity_block_ok` | XOR error detection | Yes |
| `sidecar_sha256_ok` | Metadata integrity | No |
| `sidecar_used_bits_math_ok` | Capacity validation | No |
| `sidecar_capacity_bits_ok` | Dimension check | No |
| `sidecar_header_magic_ok` | Protocol header | No |
| `sidecar_header_flags_crc_ok` | CRC flag set | No |

## 📝 Example Output

```
=== MRP Phase‑A Verify ===
R_b64 crc32: 9AE59113  (expect 9AE59113) ✓
G_b64 crc32: 7A2EFB1C  (expect 7A2EFB1C) ✓
SHA256(R_b64): e1ee6cce...  (expect e1ee6cce...) ✓
Parity OK: True  ECC scheme: parity ✓
MRP: PASS
```

## 🎯 Exit Codes
- **0**: All checks passed
- **1**: One or more checks failed

## 📦 Files Available

1. **mrp_verify.py** - Main verifier script
2. **test_mrp_verification.py** - Test suite
3. **MRP_Integration_Guide.md** - Full documentation
4. **MRP_LSB_Quick_Reference.md** - This card

---

*MRP Phase-A v1.0 | LSB1 Compatible | Echo-Community-Toolkit Ready*
