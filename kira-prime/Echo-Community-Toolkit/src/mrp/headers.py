# Auto-generated MRP Phase A stubs — 2025-10-13T05:14:22.138385Z
# SPDX-License-Identifier: MIT

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import json, zlib, base64

MAGIC = "MRP1"
FLAG_CRC = 0x01
FLAG_ECC = 0x02  # reserved for Phase B

@dataclass
class MRPHeader:
    magic: str
    channel: str  # 'R' | 'G' | 'B'
    flags: int
    length: int
    crc32: Optional[str] = None  # hex8 string when FLAG_CRC set
    payload_b64: str = ""

    def to_json_bytes(self) -> bytes:
        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True).encode("utf-8")

    @staticmethod
    def from_json_bytes(b: bytes) -> "MRPHeader":
        d = json.loads(b.decode("utf-8"))
        return MRPHeader(**d)

def crc32_hex(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08X}"

def make_frame(channel: str, payload: bytes, with_crc: bool = True) -> bytes:
    assert channel in ("R", "G", "B")
    flags = FLAG_CRC if with_crc else 0
    header = MRPHeader(
        magic=MAGIC,
        channel=channel,
        flags=flags,
        length=len(payload),
        crc32=crc32_hex(payload) if with_crc else None,
        payload_b64=base64.b64encode(payload).decode("ascii"),
    )
    return header.to_json_bytes()

def parse_frame(frame_bytes: bytes) -> MRPHeader:
    hdr = MRPHeader.from_json_bytes(frame_bytes)
    if hdr.magic != MAGIC:
        raise ValueError(f"Bad magic: {hdr.magic!r}")
    if hdr.channel not in ("R","G","B"):
        raise ValueError(f"Bad channel: {hdr.channel!r}")
    payload = base64.b64decode(hdr.payload_b64.encode("ascii"))
    if hdr.length != len(payload):
        raise ValueError("Length mismatch")
    if (hdr.flags & FLAG_CRC) and hdr.crc32:
        expect = crc32_hex(payload)
        if hdr.crc32.upper() != expect:
            raise ValueError(f"CRC32 mismatch: got {hdr.crc32}, expect {expect}")
    return hdr
