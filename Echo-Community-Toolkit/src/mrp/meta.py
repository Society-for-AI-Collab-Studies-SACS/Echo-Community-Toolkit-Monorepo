from __future__ import annotations

import base64
from hashlib import sha256
from typing import Dict, Any

from .frame import MRPFrame, crc32_hex
from .ecc import parity_hex, xor_parity_bytes


def sidecar_from_frames(
    r: MRPFrame,
    g: MRPFrame,
    *,
    bits_per_channel: int = 1,
    ecc_scheme: str = "parity",
) -> Dict[str, Any]:
    """Build the canonical B-channel sidecar document from channel frames."""
    r_bytes = r.payload
    g_bytes = g.payload
    parity = parity_hex(r_bytes, g_bytes)
    parity_bytes = xor_parity_bytes(r_bytes, g_bytes)

    sha_b64_hex = sha256(r_bytes).hexdigest()
    try:
        message_plain = base64.b64decode(r_bytes, validate=True)
        sha_plain_hex = sha256(message_plain).hexdigest()
    except Exception:
        message_plain = b""
        sha_plain_hex = ""

    if not sha_plain_hex:
        sha_plain_hex = sha_b64_hex

    return {
        "crc_r": (f"{r.crc32:08X}" if r.crc32 is not None else crc32_hex(r_bytes)).upper(),
        "crc_g": (f"{g.crc32:08X}" if g.crc32 is not None else crc32_hex(g_bytes)).upper(),
        "parity": parity,
        "parity_len": max(len(r_bytes), len(g_bytes)),
        "sha256_msg": sha_plain_hex,
        "sha256_msg_b64": sha_b64_hex,
        "ecc_scheme": ecc_scheme,
        "bits_per_channel": bits_per_channel,
        **(
            {"parity_block_b64": base64.b64encode(parity_bytes).decode("ascii")}
            if parity_bytes
            else {}
        ),
    }


__all__ = ["sidecar_from_frames"]
