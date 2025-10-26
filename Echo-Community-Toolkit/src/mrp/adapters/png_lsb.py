# PNG LSB adapter (length-prefixed bitstream per channel)
from __future__ import annotations

import math
from typing import Dict, Iterable, List

from PIL import Image

CHANNEL_INDEX = {"R": 0, "G": 1, "B": 2}
SUPPORTED_BPC = (1, 4)


def _bytes_to_bits_msb(data: bytes) -> List[int]:
    return [(byte >> i) & 1 for byte in data for i in range(7, -1, -1)]


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


def _chunk_bits(bits: List[int], chunk_size: int) -> Iterable[List[int]]:
    for i in range(0, len(bits), chunk_size):
        block = bits[i : i + chunk_size]
        if len(block) < chunk_size:
            block = block + [0] * (chunk_size - len(block))
        yield block


def embed_frames(
    cover_png: str,
    out_png: str,
    frames: Dict[str, bytes],
    *,
    bits_per_channel: int = 1,
) -> None:
    if bits_per_channel not in SUPPORTED_BPC:
        raise ValueError(f"Unsupported bits_per_channel: {bits_per_channel}")

    img = Image.open(cover_png).convert("RGB")
    pixels = list(img.getdata())
    width, height = img.size
    capacity = width * height

    mask = 0xFF ^ ((1 << bits_per_channel) - 1)

    for channel in ("R", "G", "B"):
        payload = frames.get(channel)
        if payload is None:
            continue
        bits = _bytes_to_bits_msb(len(payload).to_bytes(4, "big") + payload)
        required_pixels = math.ceil(len(bits) / bits_per_channel)
        if required_pixels > capacity:
            raise ValueError(f"Insufficient capacity for channel {channel}")

        ch_idx = CHANNEL_INDEX[channel]
        for pixel_idx, block in enumerate(_chunk_bits(bits, bits_per_channel)):
            value = 0
            for bit in block:
                value = (value << 1) | bit
            r, g, b = pixels[pixel_idx]
            vals = [r, g, b]
            vals[ch_idx] = (vals[ch_idx] & mask) | value
            pixels[pixel_idx] = tuple(vals)

    out = Image.new("RGB", img.size)
    out.putdata(pixels)
    out.save(out_png, "PNG")


def _extract_bits(
    pixels: List[tuple],
    channel_idx: int,
    bit_count: int,
    bits_per_channel: int,
    *,
    start_pixel: int = 0,
) -> List[int]:
    mask = (1 << bits_per_channel) - 1
    values_needed = math.ceil(bit_count / bits_per_channel)
    bits: List[int] = []
    for pixel_idx in range(values_needed):
        component = pixels[start_pixel + pixel_idx][channel_idx] & mask
        for shift in range(bits_per_channel - 1, -1, -1):
            bits.append((component >> shift) & 1)
    return bits[:bit_count]


def extract_frames(stego_png: str, *, bits_per_channel: int = 1) -> Dict[str, bytes]:
    if bits_per_channel not in SUPPORTED_BPC:
        raise ValueError(f"Unsupported bits_per_channel: {bits_per_channel}")

    img = Image.open(stego_png).convert("RGB")
    pixels = list(img.getdata())
    out: Dict[str, bytes] = {}

    header_bits = 32
    for channel in ("R", "G", "B"):
        ch_idx = CHANNEL_INDEX[channel]
        length_bits = _extract_bits(pixels, ch_idx, header_bits, bits_per_channel)
        length = int.from_bytes(_bits_to_bytes_msb(length_bits)[:4], "big")
        header_pixels = math.ceil(header_bits / bits_per_channel)
        payload_bits = _extract_bits(
            pixels,
            ch_idx,
            length * 8,
            bits_per_channel,
            start_pixel=header_pixels,
        )
        out[channel] = _bits_to_bytes_msb(payload_bits)
    return out
