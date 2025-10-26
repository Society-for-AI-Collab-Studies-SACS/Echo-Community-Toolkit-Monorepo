# Auto-generated MRP Phase A stubs — 2025-10-13T05:14:22.138385Z
# SPDX-License-Identifier: MIT

"""Channel utilities for MRP (stubs for Phase A).
Reuses LSB1 carrier rules (row-major, RGB, MSB-first) via adapters.
"""
from typing import Literal

Channel = Literal["R","G","B"]

CHANNEL_INDEX = {
    "R": 0,
    "G": 1,
    "B": 2,
}

def ensure_channel(ch: str) -> Channel:
    if ch not in CHANNEL_INDEX:
        raise ValueError(f"Unsupported channel {ch}")
    return ch  # type: ignore[return-value]
