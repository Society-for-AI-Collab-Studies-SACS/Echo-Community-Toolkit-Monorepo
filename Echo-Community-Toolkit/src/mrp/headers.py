"""Lightweight JSON header helpers for legacy MRP tooling."""

from __future__ import annotations

import base64
import json
import zlib
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .frame import FLAG_CRC32, MRPFrame

MAGIC = "MRP1"
FLAG_CRC = 0x01
FLAG_ECC = 0x02  # reserved for future use


@dataclass
class MRPHeader:
    magic: str
    channel: str
    flags: int
    length: int
    crc32: Optional[str] = None
    payload_b64: str = ""
    _format: str = field(default="json", repr=False, compare=False)

    def to_json_bytes(self) -> bytes:
        payload = {
            "magic": self.magic,
            "channel": self.channel,
            "flags": self.flags,
            "length": self.length,
            "crc32": self.crc32,
            "payload_b64": self.payload_b64,
        }
        if self._format == "binary":
            payload_bytes = base64.b64decode(self.payload_b64.encode("ascii"))
            with_crc = bool(self.flags & FLAG_CRC32)
            frame = MRPFrame.build(self.channel, payload_bytes, with_crc=with_crc)
            if with_crc and self.crc32 is not None:
                frame.crc32 = int(self.crc32, 16)
            return frame.to_bytes()
        return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    @staticmethod
    def from_json_bytes(data: bytes) -> "MRPHeader":
        try:
            payload: Dict[str, Any] = json.loads(data.decode("utf-8"))
            header = MRPHeader(**payload)
            header._format = "json"
            return header
        except (UnicodeDecodeError, json.JSONDecodeError):
            frame, _ = MRPFrame.parse_from(data)
            return MRPHeader(
                magic=frame.magic,
                channel=frame.channel,
                flags=frame.flags,
                length=frame.length,
                crc32=f"{frame.crc32:08X}" if frame.crc32 is not None else None,
                payload_b64=base64.b64encode(frame.payload).decode("ascii"),
                _format="binary",
            )


def crc32_hex(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08X}"


def make_frame(channel: str, payload: bytes, with_crc: bool = True) -> bytes:
    if channel not in ("R", "G", "B"):
        raise ValueError(f"Unsupported channel: {channel}")
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
    header = MRPHeader.from_json_bytes(frame_bytes)
    if header.magic != MAGIC:
        raise ValueError(f"Unexpected magic: {header.magic}")
    if header.channel not in ("R", "G", "B"):
        raise ValueError(f"Unexpected channel: {header.channel}")

    payload = base64.b64decode(header.payload_b64.encode("ascii"))
    if len(payload) != header.length:
        raise ValueError("Payload length mismatch")

    if header.crc32 and (header.flags & FLAG_CRC):
        expected_crc = crc32_hex(payload)
        if header.crc32.upper() != expected_crc:
            raise ValueError("CRC32 mismatch")
    return header
