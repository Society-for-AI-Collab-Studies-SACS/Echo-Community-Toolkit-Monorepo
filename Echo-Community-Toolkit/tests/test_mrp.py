import json, pytest
from src.mrp.headers import make_frame, parse_frame
from src.mrp.ecc import parity_hex, xor_parity_bytes

def test_header_roundtrip():
    f = make_frame("R", b"seed", True)
    h = parse_frame(f)
    assert h.magic == "MRP1" and h.length == 4 and h.crc32

def test_parity_hex():
    # XOR parity between two payloads should match manual calculation
    left = b"hello"
    right = b"world"
    expected = xor_parity_bytes(left, right).hex().upper()
    assert parity_hex(left, right) == expected
