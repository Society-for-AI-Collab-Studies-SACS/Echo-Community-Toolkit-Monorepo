"""
MRP encoding and decoding coordination layer.

This package bridges dictation collected via Echo into the
vessel-narrative-MRP encoders so the Living Library can store and
retrieve structured lessons.
"""

from .pipeline import decode_lesson, encode_lesson

__all__ = ["encode_lesson", "decode_lesson"]
