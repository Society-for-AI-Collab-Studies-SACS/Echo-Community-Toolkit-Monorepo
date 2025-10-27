from __future__ import annotations

"""Phase-A ECC utilities with XOR parity helpers."""

from typing import Union

BytesLike = Union[bytes, bytearray, memoryview]


def _coerce_bytes(value: Union[BytesLike, str, None]) -> bytes:
    if value is None:
        return b""
    if isinstance(value, str):
        return value.encode("utf-8")
    return bytes(value)


def xor_parity_bytes(*payloads: Union[BytesLike, str, None]) -> bytes:
    """Compute XOR parity across the provided payloads.

    Shorter payloads are zero-padded so the parity length matches the longest input.
    """
    buffers = [_coerce_bytes(p) for p in payloads if p]
    if not buffers:
        return b""

    max_len = max(len(buf) for buf in buffers)
    parity = bytearray(max_len)
    for buf in buffers:
        for index, value in enumerate(buf):
            parity[index] ^= value
    return bytes(parity)


def parity_hex(*payloads: Union[BytesLike, str, None]) -> str:
    """Return uppercase hex representation of the XOR parity for payloads."""
    return xor_parity_bytes(*payloads).hex().upper()


def encode_ecc(payload: bytes) -> bytes:
    """Hook for future ECC; Phase-A returns payload unchanged."""
    return payload


def decode_ecc(payload: bytes) -> tuple[bytes, dict]:
    return payload, {"ecc_scheme": "none"}
