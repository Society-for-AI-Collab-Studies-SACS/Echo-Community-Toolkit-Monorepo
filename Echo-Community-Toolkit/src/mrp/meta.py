from __future__ import annotations

import base64
from typing import Dict, Any

from .headers import MRPHeader, crc32_hex
from .ecc import parity_hex


def _payload_bytes(header: MRPHeader) -> bytes:
    return base64.b64decode(header.payload_b64.encode("utf-8"))

def sidecar_from_headers(r: MRPHeader, g: MRPHeader) -> Dict[str, Any]:
    r_bytes = _payload_bytes(r)
    g_bytes = _payload_bytes(g)
    return {
        "crc_r": (r.crc32 or crc32_hex(r_bytes)).upper(),
        "crc_g": (g.crc32 or crc32_hex(g_bytes)).upper(),
        "parity": parity_hex(r_bytes, g_bytes),
        "ecc_scheme": "xor",
    }
