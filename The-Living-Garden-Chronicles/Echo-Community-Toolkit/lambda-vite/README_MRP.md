
# MRP Seed — Multi-Channel Resonance Protocol

**Channels**
- **R**: primary message (UTF-8), base64-wrapped with header + CRC32
- **G**: metadata (UTF-8 JSON), base64-wrapped with header + CRC32
- **B**: ECC/integrity: JSON with `crc_r`, `crc_g`, `sha256_msg_b64`, and `parity_block_b64` (XOR over R_b64||G_b64)

**Header layout per channel**
```
magic="MRP1" (4B) | channel ('R'|'G'|'B') (1B) | flags (1B, bit0=CRC32) | length (4B, big) | [crc32 over payload] (4B) | payload (length B, ASCII)
```

## Quickstart

```python
from mrp import encode_mrp, decode_mrp

encode_mrp("cover.png", "stego.png", "hello world", {"timestamp":"...","note":"..."})
out = decode_mrp("stego.png")
print(out["message"], out["report"])
```
