# Echo-Community-Toolkit — MRP (Phase‑A) Scaffold

Copy‑pasteable code for the Multi‑Channel Resonance Protocol modules, including headers, channels, ECC/meta helpers, codec, and PNG/WAV adapters. Includes a minimal demo and tests.

## Modules
- `src/mrp/headers.py`
```python
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
import json, zlib, base64

MAGIC = "MRP1"; FLAG_CRC = 0x01

@dataclass
class MRPHeader:
    magic: str; channel: str; flags: int; length: int
    crc32: Optional[str] = None; payload_b64: str = ""
    def to_json_bytes(self) -> bytes: return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True).encode()
    @staticmethod
    def from_json_bytes(b: bytes) -> "MRPHeader": return MRPHeader(**json.loads(b.decode()))

def crc32_hex(b: bytes) -> str: return f"{zlib.crc32(b) & 0xFFFFFFFF:08X}"

def make_frame(ch: str, payload: bytes, with_crc: bool = True) -> bytes:
    h = MRPHeader(MAGIC, ch, FLAG_CRC if with_crc else 0, len(payload),
                  crc32_hex(payload) if with_crc else None, base64.b64encode(payload).decode())
    return h.to_json_bytes()

def parse_frame(frame: bytes) -> MRPHeader:
    h = MRPHeader.from_json_bytes(frame)
    p = base64.b64decode(h.payload_b64.encode())
    if h.magic != MAGIC or h.length != len(p): raise ValueError("Bad MRP frame")
    if (h.flags & FLAG_CRC) and h.crc32 and h.crc32 != crc32_hex(p): raise ValueError("CRC mismatch")
    return h
```

- `src/mrp/channels.py`
```python
from typing import Literal
Channel = Literal["R","G","B"]
CHANNEL_INDEX = {"R":0, "G":1, "B":2}

def ensure_channel(ch: str) -> Channel:
    if ch not in CHANNEL_INDEX: raise ValueError(f"Unsupported channel {ch}")
    return ch  # type: ignore[return-value]
```

- `src/mrp/ecc.py`
```python
def parity_hex(b: bytes) -> str:
    x = 0
    for v in b: x ^= v
    return f"{x:02X}"

def encode_ecc(payload: bytes) -> bytes:
    return payload

def decode_ecc(payload: bytes) -> tuple[bytes, dict]:
    return payload, {"ecc_scheme": "none"}
```

- `src/mrp/meta.py`
```python
from __future__ import annotations
from typing import Dict, Any
import base64, hashlib
from .headers import MRPHeader
from .ecc import parity_hex

def sidecar_from_headers(r: MRPHeader, g: MRPHeader) -> Dict[str, Any]:
    r_bytes = base64.b64decode(r.payload_b64.encode())
    sha_b64 = base64.b64encode(hashlib.sha256(r_bytes).digest()).decode()
    return {
        "crc_r": r.crc32,
        "crc_g": g.crc32,
        "parity": parity_hex((r.payload_b64 + g.payload_b64).encode()),
        "ecc_scheme": "parity",
        "sha256_msg_b64": sha_b64,
    }
```

- `src/mrp/codec.py`
```python
from __future__ import annotations
import json, base64
from typing import Dict, Any, Tuple
from .headers import make_frame, parse_frame, MRPHeader
from .meta import sidecar_from_headers
from .adapters import png_lsb

def encode(cover_png: str, out_png: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    r = make_frame("R", message.encode(), True)
    g = make_frame("G", json.dumps(metadata, separators=(",",":"), sort_keys=True).encode(), True)
    b = make_frame("B", json.dumps(sidecar_from_headers(parse_frame(r), parse_frame(g))).encode(), True)
    png_lsb.embed_frames(cover_png, out_png, {"R": r, "G": g, "B": b})
    return {"out": out_png}

def decode(stego_png: str) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    f = png_lsb.extract_frames(stego_png)
    r, g, b = parse_frame(f["R"]), parse_frame(f["G"]), parse_frame(f["B"])
    msg = base64.b64decode(r.payload_b64).decode()
    meta = json.loads(base64.b64decode(g.payload_b64).decode())
    b_json = json.loads(base64.b64decode(b.payload_b64).decode())
    ecc = {"crc_match": (b_json.get("crc_r")==r.crc32 and b_json.get("crc_g")==g.crc32),
           "parity_match": bool(b_json.get("parity")),"ecc_scheme": b_json.get("ecc_scheme","none")}
    return msg, meta, ecc
```

- `src/mrp/adapters/png_lsb.py`
```python
from typing import Dict, List
from PIL import Image
CHANNEL_INDEX = {"R":0,"G":1,"B":2}

def _bytes_to_bits_msb(b: bytes) -> List[int]:
    return [ (byte>>i)&1 for byte in b for i in range(7,-1,-1) ]

def _bits_to_bytes_msb(bits: List[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8: break
        v = 0
        for bit in chunk: v = (v<<1) | (bit&1)
        out.append(v)
    return bytes(out)

def embed_frames(cover_png: str, out_png: str, frames: Dict[str, bytes]) -> None:
    img = Image.open(cover_png).convert("RGB"); pixels = list(img.getdata()); w,h = img.size; cap = w*h
    for ch in ("R","G","B"):
        if ch not in frames: continue
        bits = _bytes_to_bits_msb(len(frames[ch]).to_bytes(4,"big")+frames[ch])
        if len(bits)>cap: raise ValueError("Insufficient capacity")
        idx = CHANNEL_INDEX[ch]
        for i,bit in enumerate(bits):
            r,g,b = pixels[i]; vals = [r,g,b]; vals[idx] = (vals[idx]&0xFE) | bit; pixels[i] = tuple(vals)
    out = Image.new("RGB", img.size); out.putdata(pixels); out.save(out_png,"PNG")

def extract_frames(stego_png: str) -> Dict[str, bytes]:
    img = Image.open(stego_png).convert("RGB"); pixels = list(img.getdata()); out: Dict[str, bytes] = {}
    for ch in ("R","G","B"):
        idx = CHANNEL_INDEX[ch]
        len_bits = [(pixels[i][idx]&1) for i in range(32)]
        n = int.from_bytes(_bits_to_bytes_msb(len_bits)[:4],"big")
        data_bits = [(pixels[i][idx]&1) for i in range(32, 32+n*8)]
        out[ch] = _bits_to_bytes_msb(data_bits)
    return out
```

- `src/mrp/adapters/wav_lsb.py`
```python
from typing import Dict

def embed_frames(cover_wav: str, out_wav: str, frames: Dict[str, bytes]) -> None:
    raise NotImplementedError("WAV LSB adapter (Phase‑A stub)")

def extract_frames(stego_wav: str) -> Dict[str, bytes]:
    raise NotImplementedError("WAV LSB adapter (Phase‑A stub)")
```

## Demo
- `examples/mrp_demo.py`
```python
#!/usr/bin/env python3
from src.mrp.codec import encode, decode
info = encode("assets/images/mrp_cover_stub.png", "assets/images/mrp_stego_out.png", "Hello", {"phase":"A"})
print("Encoded:", info); print("Decoded:", decode("assets/images/mrp_stego_out.png"))
```

## Tests
- `tests/test_mrp.py`
```python
import json, pytest
from src.mrp.headers import make_frame, parse_frame
from src.mrp.ecc import parity_hex

def test_header_roundtrip():
    f=make_frame("R", b"seed", True); h=parse_frame(f)
    assert h.magic=="MRP1" and h.length==4 and h.crc32

def test_parity_hex():
    assert len(parity_hex(b"ab"))==2
```

## Phase‑A Sidecar (Echo Toolkit)

- Required keys (minimal):
  - `crc_r` — CRC32 of R payload (uppercase 8‑hex string)
  - `crc_g` — CRC32 of G payload (uppercase 8‑hex string)
  - `parity` — two‑digit hex XOR parity over the concatenation of the base64 payload strings: `(r.payload_b64 + g.payload_b64).encode()`
  - `ecc_scheme` — literal `"parity"`
  - `sha256_msg_b64` — base64‑encoded SHA‑256 digest of the raw R payload bytes

Notes:
- The minimal sidecar above is what the Echo Toolkit generates and validates in Phase‑A.
- Extended descriptors like `carrier/channels/phase` are optional and not required for validation.
