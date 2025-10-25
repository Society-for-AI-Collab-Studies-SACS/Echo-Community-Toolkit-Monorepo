# PNG LSB adapter (length-prefixed bitstream per channel)
from typing import Dict, List, Tuple
from PIL import Image

CHANNEL_INDEX = {"R": 0, "G": 1, "B": 2}

def _bytes_to_bits_msb(b: bytes) -> List[int]:
    return [(byte >> i) & 1 for byte in b for i in range(7, -1, -1)]

def _bits_to_bytes_msb(bits: List[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        v = 0
        for bit in chunk:
            v = (v << 1) | (bit & 1)
        out.append(v)
    return bytes(out)

def embed_frames(cover_png: str, out_png: str, frames: Dict[str, bytes]) -> None:
    img = Image.open(cover_png).convert("RGB")
    pixels = list(img.getdata())
    w, h = img.size
    cap = w * h
    for ch in ("R", "G", "B"):
        if ch not in frames:
            continue
        bits = _bytes_to_bits_msb(len(frames[ch]).to_bytes(4, "big") + frames[ch])
        if len(bits) > cap:
            raise ValueError("Insufficient capacity")
        idx = CHANNEL_INDEX[ch]
        for i, bit in enumerate(bits):
            r, g, b = pixels[i]
            vals = [r, g, b]
            vals[idx] = (vals[idx] & 0xFE) | bit
            pixels[i] = tuple(vals)
    out = Image.new("RGB", img.size)
    out.putdata(pixels)
    out.save(out_png, "PNG")

def extract_frames(stego_png: str) -> Dict[str, bytes]:
    img = Image.open(stego_png).convert("RGB")
    pixels = list(img.getdata())
    out: Dict[str, bytes] = {}
    for ch in ("R", "G", "B"):
        idx = CHANNEL_INDEX[ch]
        len_bits = [(pixels[i][idx] & 1) for i in range(32)]
        n = int.from_bytes(_bits_to_bytes_msb(len_bits)[:4], "big")
        data_bits = [(pixels[i][idx] & 1) for i in range(32, 32 + n * 8)]
        out[ch] = _bits_to_bytes_msb(data_bits)
    return out

