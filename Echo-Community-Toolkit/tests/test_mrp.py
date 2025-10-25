import json, pytest
from src.mrp.headers import make_frame, parse_frame
from src.mrp.ecc import parity_hex

def test_header_roundtrip():
    f = make_frame("R", b"seed", True)
    h = parse_frame(f)
    assert h.magic == "MRP1" and h.length == 4 and h.crc32

def test_parity_hex():
    assert len(parity_hex(b"ab")) == 2

