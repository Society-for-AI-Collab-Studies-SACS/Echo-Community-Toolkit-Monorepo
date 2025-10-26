# Auto-generated MRP Phase A stubs — 2025-10-13T05:14:22.138385Z
# SPDX-License-Identifier: MIT

from __future__ import annotations
import json, base64
from typing import Dict, Any, Tuple
from .headers import make_frame, parse_frame, crc32_hex, MRPHeader
from .adapters import png_lsb

def _parity_byte(b: bytes) -> int:
    x = 0
    for v in b:
        x ^= v
    return x

def _mk_b_json(r_hdr: MRPHeader, g_hdr: MRPHeader) -> Dict[str, Any]:
    r_b = base64.b64decode(r_hdr.payload_b64.encode("ascii"))
    g_b = base64.b64decode(g_hdr.payload_b64.encode("ascii"))
    parity = _parity_byte(base64.b64encode(r_b) + base64.b64encode(g_b))
    return {
        "crc_r": r_hdr.crc32,
        "crc_g": g_hdr.crc32,
        "ecc_scheme": "none",
        "parity": f"{parity:02X}",
    }

def encode(cover_png: str, out_png: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    msg_bytes = message.encode("utf-8")
    meta_bytes = json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode("utf-8")

    r_frame = make_frame("R", msg_bytes, with_crc=True)
    g_frame = make_frame("G", meta_bytes, with_crc=True)

    b_json = _mk_b_json(parse_frame(r_frame), parse_frame(g_frame))
    b_frame = make_frame("B", json.dumps(b_json).encode("utf-8"), with_crc=True)

    # Delegate to adapter (Phase A: adapter may be stub; raise if unavailable)
    png_lsb.embed_frames(cover_png, out_png, {
        "R": r_frame,
        "G": g_frame,
        "B": b_frame,
    })
    return {"out": out_png, "r": b_json["crc_r"], "g": b_json["crc_g"], "parity": b_json["parity"]}

def decode(stego_png: str) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    frames = png_lsb.extract_frames(stego_png)
    r_hdr = parse_frame(frames["R"])
    g_hdr = parse_frame(frames["G"])
    b_hdr = parse_frame(frames["B"])

    message = base64.b64decode(r_hdr.payload_b64.encode("ascii")).decode("utf-8")
    metadata = json.loads(base64.b64decode(g_hdr.payload_b64.encode("ascii")).decode("utf-8"))
    b_json = json.loads(base64.b64decode(b_hdr.payload_b64.encode("ascii")).decode("utf-8"))

    # Quick parity check
    parity_expect = _mk_b_json(r_hdr, g_hdr)["parity"]
    ecc_report = {
        "crc_match": (b_json.get("crc_r") == r_hdr.crc32) and (b_json.get("crc_g") == g_hdr.crc32),
        "parity_match": (b_json.get("parity") == parity_expect),
        "ecc_scheme": b_json.get("ecc_scheme", "none"),
    }
    return message, metadata, ecc_report
