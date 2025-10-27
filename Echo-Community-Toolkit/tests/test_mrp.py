import base64
import json

import pytest

from src.mrp.frame import make_frame, parse_frame
from src.mrp.ecc import parity_hex, xor_parity_bytes

def test_header_roundtrip():
    payload = base64.b64encode(b"seed")
    f = make_frame("R", payload, True)
    h = parse_frame(f)
    assert h.magic == "MRP1"
    assert h.length == len(payload)
    assert h.crc32 and h.crc_ok

def test_parity_hex():
    # XOR parity between two payloads should match manual calculation
    left = b"hello"
    right = b"world"
    expected = xor_parity_bytes(left, right).hex().upper()
    assert parity_hex(left, right) == expected
