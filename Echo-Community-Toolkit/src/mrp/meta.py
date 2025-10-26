from __future__ import annotations

import base64
from hashlib import sha256
from typing import Dict, Any

from .headers import MRPHeader, crc32_hex
from .ecc import parity_hex


def _payload_bytes(header: MRPHeader) -> bytes:
    return base64.b64decode(header.payload_b64.encode("utf-8"))


def sidecar_from_headers(r: MRPHeader, g: MRPHeader, *, bits_per_channel: int = 1) -> Dict[str, Any]:
    r_bytes = _payload_bytes(r)
    g_bytes = _payload_bytes(g)
    parity = parity_hex(r_bytes, g_bytes)
    digest = sha256(r_bytes).digest()

    return {
        "crc_r": (r.crc32 or crc32_hex(r_bytes)).upper(),
        "crc_g": (g.crc32 or crc32_hex(g_bytes)).upper(),
        "parity": parity,
        "parity_len": max(len(r_bytes), len(g_bytes)),
        "sha256_msg": digest.hex(),
        "sha256_msg_b64": base64.b64encode(digest).decode("ascii"),
        "ecc_scheme": "xor",
        "bits_per_channel": bits_per_channel,
    }
