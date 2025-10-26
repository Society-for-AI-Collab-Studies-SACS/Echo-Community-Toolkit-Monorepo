# Auto-generated MRP Phase A stubs — 2025-10-13T05:14:22.138385Z
# SPDX-License-Identifier: MIT

"""PNG LSB adapter (Phase A stub)
Bridges MRP frames into per-channel LSB1 carriers using canonical bit order.
NOTE: This is a stub. Replace with real LSB plane I/O binding to your existing LSB code.
"""
from typing import Dict
def embed_frames(cover_png: str, out_png: str, frames: Dict[str, bytes]) -> None:
    raise NotImplementedError("png_lsb.embed_frames: Phase A stub — implement LSB plane mapping")

def extract_frames(stego_png: str) -> Dict[str, bytes]:
    raise NotImplementedError("png_lsb.extract_frames: Phase A stub — implement LSB plane mapping")
