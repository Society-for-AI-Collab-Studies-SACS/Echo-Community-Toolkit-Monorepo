# LSB1 encoder & CLI helpers
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import base64, zlib, json
from PIL import Image, ImageDraw  # pillow

MAGIC = b"LSB1"

def _bytes_to_bits_msb(b: bytes) -> List[int]:
    return [(byte >> i) & 1 for byte in b for i in range(7, -1, -1)]

class LSBCodec:
    def __init__(self, bpc: int = 1) -> None:
        self.bpc = bpc

    def create_cover_image(self, w: int, h: int, style: str = "texture") -> Image.Image:
        img = Image.new("RGB", (w, h), "white")
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w-1, h-1], outline="black")
        return img

    def calculate_capacity(self, w: int, h: int) -> int:
        return (w * h * 3 * self.bpc) // 8  # bytes

    def _build_lsb1_packet(self, message: str, use_crc: bool = True) -> bytes:
        payload = base64.b64encode(message.encode("utf-8"))
        flags = 0x01 if use_crc else 0x00
        parts = [MAGIC, bytes([1]), bytes([flags]), len(payload).to_bytes(4, "big")]
        if use_crc:
            crc = zlib.crc32(payload) & 0xFFFFFFFF
            parts.append(crc.to_bytes(4, "big"))
        parts.append(payload)
        return b"".join(parts)

    def _embed_bits_lsb(self, img: Image.Image, bits: List[int]) -> Image.Image:
        img = img.convert("RGB")
        w, h = img.size
        px = img.load()
        cap_bits = w * h * 3
        if len(bits) > cap_bits:
            raise ValueError("Oversized payload for cover image")
        i = 0
        for y in range(h):
            for x in range(w):
                if i >= len(bits):
                    break
                r, g, b = px[x, y]
                if i < len(bits):
                    r = (r & 0xFE) | (bits[i] & 1)
                i += 1
                if i < len(bits):
                    g = (g & 0xFE) | (bits[i] & 1)
                i += 1
                if i < len(bits):
                    b = (b & 0xFE) | (bits[i] & 1)
                i += 1
                px[x, y] = (r, g, b)
            if i >= len(bits):
                break
        return img

    def encode_message(self, cover_png: Path | str, message: str, out_png: Path | str, use_crc: bool = True) -> Dict[str, str | int]:
        cover = Image.open(cover_png).convert("RGB")
        packet = self._build_lsb1_packet(message, use_crc)
        bits = _bytes_to_bits_msb(packet)
        stego = self._embed_bits_lsb(cover, bits)
        stego.save(out_png, "PNG")
        return {
            "payload_length": len(base64.b64encode(message.encode("utf-8"))),
            "crc32": f"{(zlib.crc32(base64.b64encode(message.encode('utf-8'))) & 0xFFFFFFFF):08X}" if use_crc else None,
            "total_embedded": len(packet),
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("lsb_codec")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_cov = sub.add_parser("cover")
    p_cov.add_argument("output")
    p_cov.add_argument("--width", type=int, default=512)
    p_cov.add_argument("--height", type=int, default=512)
    p_enc = sub.add_parser("encode")
    p_enc.add_argument("message")
    p_enc.add_argument("cover")
    p_enc.add_argument("output")
    p_dec = sub.add_parser("decode")
    p_dec.add_argument("image")
    args = parser.parse_args()
    if args.cmd == "cover":
        img = LSBCodec().create_cover_image(args.width, args.height)
        img.save(args.output, "PNG")
        print(json.dumps({"op": "cover", "output": args.output}))
    elif args.cmd == "encode":
        info = LSBCodec().encode_message(args.cover, args.message, args.output, True)
        print(json.dumps({"op": "encode", **info, "output": args.output}))
    elif args.cmd == "decode":
        from .lsb_extractor import LSBExtractor
        import json as _json
        out = LSBExtractor().extract_from_image(args.image)
        print(_json.dumps(out, indent=2))
