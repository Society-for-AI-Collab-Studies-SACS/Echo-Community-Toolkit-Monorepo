from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
import json, zlib, base64

MAGIC = "MRP1"; FLAG_CRC = 0x01

@dataclass
class MRPHeader:
    magic: str; channel: str; flags: int; length: int
    crc32: Optional[str] = None; payload_b64: str = ""

    def to_json_bytes(self) -> bytes:
        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True).encode()

    @staticmethod
    def from_json_bytes(b: bytes) -> "MRPHeader":
        return MRPHeader(**json.loads(b.decode()))

def crc32_hex(b: bytes) -> str:
    return f"{zlib.crc32(b) & 0xFFFFFFFF:08X}"

def make_frame(ch: str, payload: bytes, with_crc: bool = True) -> bytes:
    h = MRPHeader(
        MAGIC, ch, FLAG_CRC if with_crc else 0, len(payload),
        crc32_hex(payload) if with_crc else None,
        base64.b64encode(payload).decode()
    )
    return h.to_json_bytes()

def parse_frame(frame: bytes) -> MRPHeader:
    h = MRPHeader.from_json_bytes(frame)
    p = base64.b64decode(h.payload_b64.encode())
    if h.magic != MAGIC or h.length != len(p):
        raise ValueError("Bad MRP frame")
    if (h.flags & FLAG_CRC) and h.crc32 and h.crc32 != crc32_hex(p):
        raise ValueError("CRC mismatch")
    return h

