# LSB1 PNG decoder
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Tuple, List
import base64, binascii, zlib
from PIL import Image

MAGIC = b"LSB1"

def _bits_to_bytes_msb(bits: List[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        v = 0
        for j, bit in enumerate(chunk):
            v |= (bit & 1) << (7 - j)
        out.append(v)
    return bytes(out)

def _extract_bits_rgb_lsb(img: Image.Image) -> list[int]:
    img = img.convert("RGB")
    w, h = img.size
    px = img.load()
    bits: list[int] = []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            bits.extend([r & 1, g & 1, b & 1])
    return bits

def _find_magic(buf: bytes) -> int | None:
    i = buf.find(MAGIC)
    return None if i < 0 else i

def _decode_base64_payload(payload: bytes) -> Tuple[str, str]:
    """Return (base64_text, decoded_utf8) or raise ValueError."""
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
        raise ValueError(f"UTF-8 decode failed: {exc}") from exc
    return payload_ascii, decoded_text

class LSBExtractor:
    """Extracts LSB1 payloads from PNG files."""
    def extract_from_image(self, path: Path | str, include_bits: bool = False) -> Dict[str, Any]:
        p = Path(path)
        img = Image.open(p).convert("RGB")
        bits = _extract_bits_rgb_lsb(img)
        data = _bits_to_bytes_msb(bits)

        # Skip leading zeros and search for magic
        # First remove leading 0x00s
        i = 0
        while i < len(data) and data[i] == 0:
            i += 1
        # Search for MAGIC from i
        rel = _find_magic(data[i:])
        if rel is None:
            # Legacy fallback: collect until next 0x00 as base64
            j = i
            while j < len(data) and data[j] != 0:
                j += 1
            payload_b64 = data[i:j]
            try:
                base64_text, decoded_text = _decode_base64_payload(payload_b64)
            except Exception as e:
                return {"filename": str(p), "error": f"No header and legacy decode failed: {e}"}
            out = {
                "filename": str(p),
                "base64_payload": base64_text,
                "decoded_text": decoded_text,
                "message_length_bytes": len(payload_b64),
                "magic": None,
                "version": None,
                "flags": None,
                "payload_length": None,
                "crc32": None,
            }
            if include_bits:
                out["binary_lsb_data"] = data.hex()
            return out

        start = i + rel
        # Parse LSB1 header
        try:
            if start + 10 > len(data):
                raise ValueError("Truncated header")
            magic = data[start:start+4]
            ver = data[start+4]
            flags = data[start+5]
            n = int.from_bytes(data[start+6:start+10], "big")
            pos = start + 10
            crc_hex = None
            if flags & 0x01:
                if pos + 4 > len(data):
                    raise ValueError("Truncated CRC32")
                crc_val = int.from_bytes(data[pos:pos+4], "big")
                crc_hex = f"{crc_val:08X}"
                pos += 4
            if pos + n > len(data):
                raise ValueError("Truncated payload")
            payload = data[pos:pos+n]
            # Validate CRC if present
            if flags & 0x01:
                calc = zlib.crc32(payload) & 0xFFFFFFFF
                if calc != int(crc_hex, 16):
                    raise ValueError("CRC mismatch")
            # Decode payload as base64 text
            base64_text, decoded_text = _decode_base64_payload(payload)
            out = {
                "filename": str(p),
                "base64_payload": base64_text,
                "decoded_text": decoded_text,
                "message_length_bytes": len(payload),
                "magic": magic.decode("ascii", errors="ignore"),
                "version": int(ver),
                "flags": int(flags),
                "payload_length": n,
                "crc32": crc_hex,
            }
            if include_bits:
                out["binary_lsb_data"] = data.hex()
            return out
        except Exception as e:
            return {"filename": str(p), "error": str(e)}

if __name__ == "__main__":
    import argparse, json, sys, glob
    ap = argparse.ArgumentParser("lsb_extractor")
    ap.add_argument("images", nargs="+", help="PNG files or globs")
    ap.add_argument("-o", "--out", default="", help="Write JSON results to file (list for multiple inputs)")
    ap.add_argument("--include-bits", action="store_true", help="Include raw assembled LSB bytes as hex")
    args = ap.parse_args()

    # Expand globs
    paths: List[str] = []
    for pattern in args.images:
        matches = glob.glob(pattern)
        if not matches:
            paths.append(pattern)
        else:
            paths.extend(matches)

    results = [LSBExtractor().extract_from_image(p, include_bits=args.include_bits) for p in paths]
    if args.out:
        Path(args.out).write_text(json.dumps(results if len(results) > 1 else results[0], indent=2), encoding="utf-8")
    print(json.dumps(results if len(results) > 1 else results[0], indent=2))
