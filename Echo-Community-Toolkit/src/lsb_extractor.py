"""LSB1 PNG decoder with legacy fallback and MRP phase detection."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import zlib

from PIL import Image

from mrp.adapters import png_lsb
from mrp.codec import _decode_frames
from mrp.frame import MAGIC as MRP_MAGIC
from mrp.frame import parse_frame

MAGIC = b"LSB1"
HEADER_BYTES = 10
CRC_BYTES = 4
FLAG_HAS_CRC32 = 0x01
FLAG_BPC4 = 0x02


class LSBParseError(ValueError):
    """Raised when an LSB1 stream fails structural validation."""


@dataclass
class LSB1Header:
    """Parsed representation of an LSB1 header."""

    magic: str
    version: int
    flags: int
    payload_length: int
    crc32: Optional[int] = None

    @property
    def has_crc(self) -> bool:
        return bool(self.flags & FLAG_HAS_CRC32)

    @property
    def uses_bpc4(self) -> bool:
        return bool(self.flags & FLAG_BPC4)


def _bits_to_bytes_msb(bits: Iterable[int]) -> bytes:
    out = bytearray()
    chunk: List[int] = []
    for bit in bits:
        chunk.append(bit & 1)
        if len(chunk) == 8:
            value = 0
            for b in chunk:
                value = (value << 1) | b
            out.append(value)
            chunk.clear()
    if chunk:
        while len(chunk) < 8:
            chunk.append(0)
        value = 0
        for b in chunk:
            value = (value << 1) | b
        out.append(value)
    return bytes(out)


def _extract_bits_rgb_lsb(img: Image.Image, bpc: int) -> List[int]:
    pixels = img.load()
    width, height = img.size
    mask = (1 << bpc) - 1
    bits: List[int] = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for value in (r, g, b):
                component = value & mask
                for shift in range(bpc - 1, -1, -1):
                    bits.append((component >> shift) & 1)
    return bits


def _strip_leading_nulls(data: bytes) -> int:
    idx = 0
    while idx < len(data) and data[idx] == 0:
        idx += 1
    return idx


def find_lsb1_magic(buffer: bytes, *, start: int = 0) -> Optional[int]:
    """Locate the LSB1 magic starting at ``start``. Returns absolute index or None."""
    offset = buffer.find(MAGIC, start)
    return None if offset < 0 else offset


def parse_lsb1_header(data: bytes, *, start: int = 0) -> Tuple[LSB1Header, int]:
    """Parse an LSB1 header starting at ``start``; returns (header, payload_start)."""
    end = start + HEADER_BYTES
    if len(data) < end:
        raise LSBParseError("Truncated LSB1 header")
    if data[start : start + 4] != MAGIC:
        raise LSBParseError("LSB1 magic mismatch")

    version = data[start + 4]
    flags = data[start + 5]
    payload_length = int.from_bytes(data[start + 6 : start + 10], "big")

    cursor = end
    crc_val: Optional[int] = None
    if flags & FLAG_HAS_CRC32:
        crc_end = cursor + CRC_BYTES
        if len(data) < crc_end:
            raise LSBParseError("Truncated CRC32")
        crc_val = int.from_bytes(data[cursor:crc_end], "big")
        cursor = crc_end

    header = LSB1Header(
        magic=MAGIC.decode("ascii"),
        version=int(version),
        flags=int(flags),
        payload_length=payload_length,
        crc32=crc_val,
    )
    return header, cursor


def parse_lsb1_packet(
    data: bytes, *, start: int = 0, validate_crc: bool = True
) -> Tuple[LSB1Header, bytes, int]:
    """Parse an LSB1 packet and return (header, payload_bytes, next_index)."""
    header, payload_start = parse_lsb1_header(data, start=start)
    payload_end = payload_start + header.payload_length
    if len(data) < payload_end:
        raise LSBParseError("Truncated payload")
    payload = data[payload_start:payload_end]

    if validate_crc and header.has_crc:
        calc = zlib.crc32(payload) & 0xFFFFFFFF
        if header.crc32 is None or calc != header.crc32:
            raise LSBParseError("CRC mismatch")
    return header, payload, payload_end


def extract_legacy_payload(data: bytes, *, start: int = 0) -> Tuple[bytes, int]:
    """Extract null-terminated legacy payload bytes starting at ``start``."""
    cursor = start
    payload = bytearray()
    while cursor < len(data) and data[cursor] != 0:
        payload.append(data[cursor])
        cursor += 1
    if not payload:
        raise LSBParseError("Legacy payload missing or empty")
    return bytes(payload), cursor


def decode_base64_payload(payload: bytes) -> Tuple[str, str]:
    """Decode payload bytes returning (base64_text, decoded_utf8)."""
    try:
        payload_ascii = payload.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("Payload is not ASCII") from exc
    try:
        decoded_bytes = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"Base64 decode failed: {exc}") from exc
    try:
        decoded_text = decoded_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("UTF-8 decode failed") from exc
    return payload_ascii, decoded_text


class LSBExtractor:
    """Extract LSB payloads (legacy, LSB1 headered, or Phase-2 MRP frames)."""

    def __init__(self, bpc: int = 1) -> None:
        if bpc not in (1, 4):
            raise ValueError("bits-per-channel must be 1 or 4")
        self.bpc = bpc

    # --- Modular Parsers -------------------------------------------------

    @staticmethod
    def parse_lsb1_header(data: bytes, *, start: int = 0) -> Tuple[LSB1Header, int]:
        return parse_lsb1_header(data, start=start)

    @staticmethod
    def parse_lsb1_packet(
        data: bytes, *, start: int = 0, validate_crc: bool = True
    ) -> Tuple[LSB1Header, bytes, int]:
        return parse_lsb1_packet(data, start=start, validate_crc=validate_crc)

    @staticmethod
    def extract_legacy_payload(data: bytes, *, start: int = 0) -> Tuple[bytes, int]:
        return extract_legacy_payload(data, start=start)

    # --- Helpers ---------------------------------------------------------

    def _candidate_bpcs(self) -> List[int]:
        order: List[int] = [self.bpc]
        if 1 not in order:
            order.append(1)
        if 4 not in order:
            order.append(4)
        return order

    def _read_bitstream(self, path: Path) -> bytes:
        with Image.open(path).convert("RGB") as img:
            try:
                bits = _extract_bits_rgb_lsb(img, self.bpc)
            except TypeError:
                # Support older monkeypatch signatures present in regression tests
                bits = _extract_bits_rgb_lsb(img)
        return _bits_to_bytes_msb(bits)

    def _try_extract_mrp(self, path: Path) -> Optional[Dict[str, Any]]:
        for bpc in self._candidate_bpcs():
            try:
                frames = png_lsb.extract_frames(str(path), bits_per_channel=bpc)
            except (ValueError, IndexError):
                continue
            try:
                for channel in ("R", "G", "B"):
                    parse_frame(frames[channel], expected_channel=channel)
            except ValueError:
                continue
            if any(not frames[ch].startswith(MRP_MAGIC) for ch in ("R", "G", "B")):
                continue
            try:
                decoded = _decode_frames(frames, bits_per_channel=bpc)
            except ValueError as exc:
                return {
                    "filename": str(path),
                    "mode": "MRP",
                    "detected_format": "mrp",
                    "bits_per_channel": bpc,
                    "error": str(exc),
                }
            decoded.pop("message_length", None)
            decoded.update(
                {
                    "filename": str(path),
                    "mode": "MRP",
                    "detected_format": "mrp",
                    "bits_per_channel": bpc,
                }
            )
            return decoded
        return None

    # --- Public API ------------------------------------------------------

    def extract_from_image(self, path: Path | str, include_bits: bool = False) -> Dict[str, Any]:
        p = Path(path)
        mrp_candidate = self._try_extract_mrp(p)
        if mrp_candidate is not None:
            if include_bits:
                mrp_candidate["binary_lsb_data"] = "<multi-channel>"
            return mrp_candidate

        bitstream = self._read_bitstream(p)
        leading_offset = _strip_leading_nulls(bitstream)
        header_offset = find_lsb1_magic(bitstream, start=leading_offset)

        if header_offset is None:
            try:
                payload_bytes, _ = self.extract_legacy_payload(bitstream, start=leading_offset)
                base64_text, decoded_text = decode_base64_payload(payload_bytes)
            except (LSBParseError, ValueError) as exc:
                return {"filename": str(p), "error": f"Legacy decode failed: {exc}"}
            result = {
                "filename": str(p),
                "mode": "LSB1",
                "detected_format": "legacy",
                "bits_per_channel": self.bpc,
                "base64_payload": base64_text,
                "decoded_text": decoded_text,
                "message_length_bytes": len(payload_bytes),
                "magic": None,
                "version": None,
                "flags": None,
                "payload_length": None,
                "crc32": None,
            }
            if include_bits:
                result["binary_lsb_data"] = bitstream.hex()
            return result

        try:
            header, payload_bytes, _ = self.parse_lsb1_packet(
                bitstream,
                start=header_offset,
                validate_crc=True,
            )
            base64_text, decoded_text = decode_base64_payload(payload_bytes)
        except LSBParseError as exc:
            return {"filename": str(p), "error": str(exc)}
        except ValueError as exc:
            return {"filename": str(p), "error": str(exc)}

        result = {
            "filename": str(p),
            "mode": "LSB1",
            "detected_format": "lsb1",
            "bits_per_channel": self.bpc,
            "base64_payload": base64_text,
            "decoded_text": decoded_text,
            "message_length_bytes": len(payload_bytes),
            "magic": header.magic,
            "version": header.version,
            "flags": header.flags,
            "payload_length": header.payload_length,
            "crc32": f"{header.crc32:08X}" if header.crc32 is not None else None,
        }
        if include_bits:
            result["binary_lsb_data"] = bitstream.hex()
        return result


__all__ = [
    "FLAG_BPC4",
    "FLAG_HAS_CRC32",
    "LSB1Header",
    "LSBExtractor",
    "LSBParseError",
    "decode_base64_payload",
    "extract_legacy_payload",
    "find_lsb1_magic",
    "parse_lsb1_header",
    "parse_lsb1_packet",
]


if __name__ == "__main__":
    import argparse
    import glob
    import json

    parser = argparse.ArgumentParser("lsb_extractor")
    parser.add_argument("images", nargs="+", help="PNG files or globs")
    parser.add_argument(
        "-o",
        "--out",
        default="",
        help="Write JSON results to file (list for multiple inputs)",
    )
    parser.add_argument(
        "--include-bits",
        action="store_true",
        help="Include raw assembled LSB bytes as hex",
    )
    args = parser.parse_args()

    paths: List[str] = []
    for pattern in args.images:
        matches = glob.glob(pattern)
        if matches:
            paths.extend(matches)
        else:
            paths.append(pattern)

    extractor = LSBExtractor()
    results = [extractor.extract_from_image(p, include_bits=args.include_bits) for p in paths]
    payload = results if len(results) > 1 else results[0]
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
