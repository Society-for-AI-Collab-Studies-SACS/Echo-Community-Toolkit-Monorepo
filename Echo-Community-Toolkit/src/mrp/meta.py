from __future__ import annotations
from typing import Dict, Any
from .headers import MRPHeader
from .ecc import parity_hex

def sidecar_from_headers(r: MRPHeader, g: MRPHeader) -> Dict[str, Any]:
    return {
        "crc_r": r.crc32,
        "crc_g": g.crc32,
        "parity": parity_hex((r.payload_b64 + g.payload_b64).encode()),
        "ecc_scheme": "none"
    }

