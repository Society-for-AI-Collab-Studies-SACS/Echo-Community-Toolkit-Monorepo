# LSB1 encoder & CLI helpers
from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw  # pillow

from mrp.adapters import png_lsb
from mrp.frame import MRPFrame, make_frame
from mrp.meta import sidecar_from_frames

MAGIC = b"LSB1"


def _bytes_to_bits_msb(b: bytes) -> List[int]:
    return [(byte >> i) & 1 for byte in b for i in range(7, -1, -1)]

class LSBCodec:
    def __init__(self, bpc: int = 1) -> None:
        if bpc not in (1, 4):
            raise ValueError("bits-per-channel must be 1 or 4")
        self.bpc = bpc

    def create_cover_image(self, w: int, h: int, style: str = "texture") -> Image.Image:
        img = Image.new("RGB", (w, h), "white")
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w-1, h-1], outline="black")
        return img

    def calculate_capacity(self, w: int, h: int) -> int:
        return (w * h * 3 * self.bpc) // 8  # bytes

    def calculate_channel_capacity(self, w: int, h: int) -> int:
        """Per-channel capacity in bytes for the configured bits-per-channel."""
        return (w * h * self.bpc) // 8

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
        cap_bits = w * h * 3 * self.bpc
        if len(bits) > cap_bits:
            raise ValueError("Oversized payload for cover image")
        mask = (1 << self.bpc) - 1
        clear_mask = 0xFF ^ mask
        bit_iter = iter(bits)
        for y in range(h):
            for x in range(w):
                r, g, b = px[x, y]
                comps = [r, g, b]
                updated = False
                for idx in range(3):
                    chunk: List[int] = []
                    try:
                        for _ in range(self.bpc):
                            chunk.append(next(bit_iter))
                    except StopIteration:
                        if not chunk:
                            break
                    while len(chunk) < self.bpc:
                        chunk.append(0)
                    value = 0
                    for bit in chunk:
                        value = (value << 1) | (bit & 1)
                    comps[idx] = (comps[idx] & clear_mask) | value
                    updated = True
                if not updated:
                    px[x, y] = (r, g, b)
                    return img
                px[x, y] = tuple(comps)
        return img

    def _build_mrp_frames(
        self, message: str, metadata: Optional[Dict[str, Any]]
    ) -> tuple[Dict[str, bytes], Dict[str, Any], Dict[str, int]]:
        meta = dict(metadata or {})
        message_bytes = message.encode("utf-8")
        metadata_bytes = json.dumps(meta, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

        payload_r = base64.b64encode(message_bytes)
        payload_g = base64.b64encode(metadata_bytes)

        frames: Dict[str, bytes] = {
            "R": make_frame("R", payload_r, True),
            "G": make_frame("G", payload_g, True),
        }

        r_frame, _ = MRPFrame.parse_from(frames["R"], expected_channel="R")
        g_frame, _ = MRPFrame.parse_from(frames["G"], expected_channel="G")
        sidecar = sidecar_from_frames(r_frame, g_frame, bits_per_channel=self.bpc)

        payload_b = json.dumps(sidecar, separators=(",", ":"), sort_keys=True).encode("utf-8")
        frames["B"] = make_frame("B", payload_b, True)

        payload_lengths = {"r": len(payload_r), "g": len(payload_g)}
        return frames, sidecar, payload_lengths

    def encode_message(
        self,
        cover_png: Path | str,
        message: str,
        out_png: Path | str,
        use_crc: bool = True,
        *,
        mode: str = "lsb1",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if mode not in ("lsb1", "mrp"):
            raise ValueError("mode must be 'lsb1' or 'mrp'")

        cover_path = str(cover_png)
        out_path = str(out_png)

        if mode == "lsb1":
            cover = Image.open(cover_path).convert("RGB")
            packet = self._build_lsb1_packet(message, use_crc)
            bits = _bytes_to_bits_msb(packet)
            stego = self._embed_bits_lsb(cover, bits)
            stego.save(out_path, "PNG")
            cover.close()
            stego.close()
            payload_b64 = base64.b64encode(message.encode("utf-8"))
            return {
                "mode": "lsb1",
                "bits_per_channel": self.bpc,
                "payload_length": len(payload_b64),
                "crc32": f"{zlib.crc32(payload_b64) & 0xFFFFFFFF:08X}" if use_crc else None,
                "total_embedded": len(packet),
            }

        frames, sidecar, payload_lengths = self._build_mrp_frames(message, metadata)
        with Image.open(cover_path) as cover_img:
            w, h = cover_img.size
        channel_capacity = self.calculate_channel_capacity(w, h)
        for channel, payload in frames.items():
            required = len(payload) + 4  # length prefix during embedding
            if required > channel_capacity:
                raise ValueError(
                    f"Channel {channel} payload ({required} bytes) exceeds capacity "
                    f"{channel_capacity} for {w}x{h} @ {self.bpc}bpc"
                )

        png_lsb.embed_frames(cover_path, out_path, frames, bits_per_channel=self.bpc)
        return {
            "mode": "mrp",
            "bits_per_channel": self.bpc,
            "payload_lengths": payload_lengths,
            "integrity": sidecar,
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
