"""
Convenience exports for the Multi-Channel Resonance Protocol toolkit.

encode_mrp / decode_mrp provide the primary API used by the healing regression
tests, while MemoryBlocks is a placeholder for future multi-image stitching.
"""

from .codec import decode_mrp, encode_mrp  # noqa: F401
from .frame import MRPFrame  # noqa: F401
from .memory_blocks import MemoryBlocks  # noqa: F401

__all__ = ["encode_mrp", "decode_mrp", "MRPFrame", "MemoryBlocks"]
