"""
Binary frame helpers for the Multi-Channel Resonance Protocol (MRP).

Each frame corresponds to a payload embedded in a single colour channel.  The
layout is:

    magic      (4 bytes) : ASCII "MRP1"
    channel    (1 byte)  : ASCII 'R', 'G', or 'B'
    flags      (1 byte)  : bit 0 indicates CRC32 field present
    length     (4 bytes) : big-endian payload length
    [crc32]    (4 bytes) : present when CRC flag set, big-endian
    payload    (length bytes)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import zlib

MAGIC = b"MRP1"
FLAG_CRC32 = 0x01
HEADER_BYTES = 4 + 1 + 1 + 4
CRC_BYTES = 4
HEADER_WITH_CRC_BYTES = HEADER_BYTES + CRC_BYTES


def crc32_hex(payload: bytes) -> str:
    """Return an uppercase CRC32 string for the payload."""
    return f"{zlib.crc32(payload) & 0xFFFFFFFF:08X}"


@dataclass
class MRPFrame:
    """Represents a decoded MRP frame."""

    magic: str
    channel: str
    payload: bytes
    flags: int
    crc32: Optional[int]
    crc_ok: bool
    channel_valid: bool

    @property
    def length(self) -> int:
        return len(self.payload)

    def to_bytes(self) -> bytes:
        """Serialise the frame to bytes."""
        if len(self.channel) != 1:
            raise ValueError("Channel identifier must be a single ASCII character.")
        header = bytearray()
        header += MAGIC
        header += self.channel.encode("ascii")
        header.append(self.flags & 0xFF)
        header += self.length.to_bytes(4, "big")
        if self.flags & FLAG_CRC32:
            crc_val = self.crc32
            if crc_val is None:
                crc_val = zlib.crc32(self.payload) & 0xFFFFFFFF
                self.crc32 = crc_val
            header += crc_val.to_bytes(4, "big")
        return bytes(header) + self.payload

    @classmethod
    def build(cls, channel: str, payload: bytes, *, with_crc: bool = True) -> "MRPFrame":
        """Construct a frame for the provided payload."""
        flags = FLAG_CRC32 if with_crc else 0
        crc_val = zlib.crc32(payload) & 0xFFFFFFFF if with_crc else None
        return cls(
            magic=MAGIC.decode("ascii"),
            channel=channel,
            payload=payload,
            flags=flags,
            crc32=crc_val,
            crc_ok=True,
            channel_valid=True,
        )

    @classmethod
    def parse_from(
        cls, data: bytes, *, expected_channel: Optional[str] = None
    ) -> Tuple["MRPFrame", int]:
        """Parse a frame from the beginning of ``data``.

        Returns the decoded frame and the number of bytes consumed.
        """
        if len(data) < HEADER_BYTES:
            raise ValueError("Frame too short")
        if data[:4] != MAGIC:
            raise ValueError("MRP magic mismatch")

        channel = chr(data[4])
        flags = data[5]
        length = int.from_bytes(data[6:10], "big")
        cursor = HEADER_BYTES

        crc_val: Optional[int] = None
        if flags & FLAG_CRC32:
            if len(data) < cursor + CRC_BYTES:
                raise ValueError("Frame missing CRC32 bytes")
            crc_val = int.from_bytes(data[cursor : cursor + CRC_BYTES], "big")
            cursor += CRC_BYTES

        end = cursor + length
        if len(data) < end:
            raise ValueError("Frame payload truncated")
        payload = data[cursor:end]

        crc_ok = True
        if flags & FLAG_CRC32:
            crc_ok = (zlib.crc32(payload) & 0xFFFFFFFF) == crc_val

        channel_valid = expected_channel is None or channel == expected_channel
        frame = cls(
            magic=MAGIC.decode("ascii"),
            channel=channel,
            payload=payload,
            flags=flags,
            crc32=crc_val,
            crc_ok=crc_ok,
            channel_valid=channel_valid,
        )
        return frame, end


def make_frame(channel: str, payload: bytes, with_crc: bool = True) -> bytes:
    """Create a serialised frame for the given channel."""
    return MRPFrame.build(channel, payload, with_crc=with_crc).to_bytes()


def parse_frame(frame_bytes: bytes, expected_channel: Optional[str] = None) -> MRPFrame:
    frame, consumed = MRPFrame.parse_from(frame_bytes, expected_channel=expected_channel)
    if consumed < len(frame_bytes):
        # Allow trailing padding but require it to be all zeros.
        if any(byte != 0 for byte in frame_bytes[consumed:]):
            raise ValueError("Trailing data present after frame")
    return frame


__all__ = [
    "FLAG_CRC32",
    "HEADER_BYTES",
    "HEADER_WITH_CRC_BYTES",
    "CRC_BYTES",
    "MAGIC",
    "MRPFrame",
    "crc32_hex",
    "make_frame",
    "parse_frame",
]
