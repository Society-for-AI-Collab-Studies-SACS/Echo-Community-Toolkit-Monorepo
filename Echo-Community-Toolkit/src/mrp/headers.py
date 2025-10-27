"""Lightweight JSON header helpers for legacy MRP tooling."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .frame import FLAG_CRC32, MRPFrame, crc32_hex as frame_crc32_hex

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
    _binary_source: bool = field(default=False, init=False, repr=False, compare=False)

    def to_json_bytes(self) -> bytes:
        if self._binary_source:
            payload = base64.b64decode(self.payload_b64.encode("ascii"))
            crc_int = int(self.crc32, 16) if self.crc32 else None
            flags = self.flags if self.flags is not None else (FLAG_CRC32 if crc_int is not None else 0)
            frame = MRPFrame(
                magic=MAGIC,
                channel=self.channel,
                payload=payload,
                flags=flags,
                crc32=crc_int,
                crc_ok=True,
                channel_valid=True,
            )
            return frame.to_bytes()
        payload_dict = {
            "magic": self.magic,
            "channel": self.channel,
            "flags": self.flags,
            "length": self.length,
            "crc32": self.crc32,
            "payload_b64": self.payload_b64,
        }
        return json.dumps(payload_dict, separators=(",", ":"), sort_keys=True).encode("utf-8")

    @staticmethod
    def from_json_bytes(data: bytes) -> "MRPHeader":
        binary_source = False
        try:
            payload: Dict[str, Any] = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            frame, _ = MRPFrame.parse_from(data)
            payload = {
                "magic": frame.magic,
                "channel": frame.channel,
                "flags": frame.flags,
                "length": frame.length,
                "crc32": f"{frame.crc32:08X}" if frame.crc32 is not None else None,
                "payload_b64": base64.b64encode(frame.payload).decode("ascii"),
            }
            binary_source = True
        header = MRPHeader(**payload)
        header._binary_source = binary_source
        return header


def crc32_hex(data: bytes) -> str:
    return frame_crc32_hex(data)


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
