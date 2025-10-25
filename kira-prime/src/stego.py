"""Simple LSB steganography helpers for Vessel Narrative MRP.

The encoder embeds chapter metadata into a PNG by storing the payload bits in the
least-significant bit of each colour channel. A small header identifies the
payload and encodes the payload length so we know when to stop during decode.

The module relies on Pillow when available. Callers should check
``is_available()`` before attempting to encode/decode, and degrade gracefully if
Pillow is missing.
"""
from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Tuple

try:  # Optional dependency
    from PIL import Image
except ImportError:  # pragma: no cover - handled at runtime
    Image = None  # type: ignore[misc]


HEADER = b"VMRP\0"
VERSION = 1
_META_KEYS_TO_EXCLUDE = {"stego_png"}


@dataclass(frozen=True)
class StegoDoc:
    """Structured payload recovered from a stego PNG."""

    chapter: int
    narrator: str
    flags: Dict[str, str]
    glyphs: Tuple[str, ...]
    file: str
    summary: str
    timestamp: str
    provenance: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "StegoDoc":
        return cls(
            chapter=int(data["chapter"]),
            narrator=str(data["narrator"]),
            flags={k: str(v) for k, v in dict(data["flags"]).items()},
            glyphs=tuple(str(g) for g in data["glyphs"]),
            file=str(data["file"]),
            summary=str(data["summary"]),
            timestamp=str(data["timestamp"]),
            provenance=dict(data.get("provenance", {})),
        )

    def as_dict(self) -> Dict[str, object]:
        return {
            "chapter": self.chapter,
            "narrator": self.narrator,
            "flags": dict(self.flags),
            "glyphs": list(self.glyphs),
            "file": self.file,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "provenance": dict(self.provenance),
        }


def is_available() -> bool:
    """Return True when Pillow is importable and PNG stego support is enabled."""

    return Image is not None


def _ensure_available() -> None:
    if not is_available():  # pragma: no cover - runtime guard
        raise RuntimeError(
            "Pillow is required for steganography support. Install it via 'pip install Pillow'."
        )


def _payload_bytes(chapter_meta: Dict[str, object]) -> bytes:
    doc = {k: v for k, v in chapter_meta.items() if k not in _META_KEYS_TO_EXCLUDE}
    payload_json = json.dumps(doc, separators=(",", ":"), sort_keys=True)
    payload_data = payload_json.encode("utf-8")
    header = HEADER + bytes([VERSION]) + struct.pack(">I", len(payload_data))
    return header + payload_data


def _bits_from_bytes(data: bytes) -> Iterator[int]:
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1


def _read_bytes(bit_iter: Iterator[int], count: int) -> bytes:
    result = bytearray()
    for _ in range(count):
        byte = 0
        for _ in range(8):
            try:
                bit = next(bit_iter)
            except StopIteration as exc:  # pragma: no cover - defensive
                raise ValueError("Image does not contain enough embedded data") from exc
            byte = (byte << 1) | bit
        result.append(byte)
    return bytes(result)


def _lsb_bit_stream(img: "Image.Image") -> Iterator[int]:
    pixels = img.convert("RGB").getdata()
    for pixel in pixels:
        yield from read_pixel_bits(pixel)


def _embed_bits(img: "Image.Image", payload: bytes) -> None:
    bits = list(_bits_from_bytes(payload))
    width, height = img.size
    pixels = img.load()
    total_channels = width * height * 3
    if len(bits) > total_channels:
        raise ValueError("Base image too small for payload")
    bit_iter = iter(bits)
    for y in range(height):
        for x in range(width):
            next_bits: list[int] = []
            for _ in range(3):
                try:
                    next_bits.append(next(bit_iter))
                except StopIteration:
                    break
            if not next_bits:
                return
            pixels[x, y] = write_pixel_bits(pixels[x, y], tuple(next_bits))


def _prepare_image(payload: bytes, base_image_path: Path | None) -> "Image.Image":
    if base_image_path is not None:
        return Image.open(base_image_path).convert("RGB")

    bits = len(payload) * 8
    pixels_needed = math.ceil(bits / 3)
    side = max(32, math.ceil(math.sqrt(pixels_needed)))
    return Image.new("RGB", (side, side), color=(12, 12, 12))


def encode_chapter_payload(
    chapter_meta: Dict[str, object],
    output_path: Path,
    *,
    base_image: Path | None = None,
) -> Path:
    """Embed chapter metadata into a PNG stored at ``output_path``."""

    _ensure_available()
    payload = _payload_bytes(chapter_meta)
    image = _prepare_image(payload, base_image)
    _embed_bits(image, payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")
    return output_path


def decode_chapter_payload(image_path: Path) -> StegoDoc:
    """Decode and return the metadata embedded in ``image_path``."""

    _ensure_available()
    img = Image.open(image_path).convert("RGB")
    bit_iter = _lsb_bit_stream(img)
    header_size = len(HEADER) + 1 + 4
    header = _read_bytes(bit_iter, header_size)
    if header[: len(HEADER)] != HEADER:
        raise ValueError("Stego header mismatch")
    version = header[len(HEADER)]
    if version != VERSION:
        raise ValueError(f"Unsupported stego version: {version}")
    payload_len = struct.unpack(">I", header[len(HEADER) + 1 :])[0]
    payload = _read_bytes(bit_iter, payload_len)
    data = json.loads(payload.decode("utf-8"))
    return StegoDoc.from_dict(data)


def read_pixel_bits(pixel: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Return the least-significant bits from an RGB ``pixel``."""

    return tuple(channel & 1 for channel in pixel)


def write_pixel_bits(pixel: Tuple[int, int, int], bits: Tuple[int, ...]) -> Tuple[int, int, int]:
    """Return a new pixel with ``bits`` (≤3) written into the LSB of each channel."""

    if len(bits) > 3:
        raise ValueError("At most 3 bits can be embedded per RGB pixel")
    channels = list(pixel)
    for idx, bit in enumerate(bits):
        channels[idx] = (channels[idx] & ~1) | (bit & 1)
    return tuple(channels)


def read_lsb_stream(image_path: Path, *, limit: int | None = None) -> Iterator[int]:
    """Yield LSB bits from ``image_path`` for debugging and validation tooling."""

    _ensure_available()
    img = Image.open(image_path).convert("RGB")
    stream = _lsb_bit_stream(img)
    if limit is None:
        yield from stream
    else:
        for _, bit in zip(range(limit), stream):
            yield bit


def extract_flags(image_path: Path) -> Dict[str, str]:
    """Decode only the chapter flags from ``image_path``."""

    doc = decode_chapter_payload(image_path)
    return dict(doc.flags)


__all__ = [
    "StegoDoc",
    "is_available",
    "encode_chapter_payload",
    "decode_chapter_payload",
    "extract_flags",
    "read_lsb_stream",
    "read_pixel_bits",
    "write_pixel_bits",
]
