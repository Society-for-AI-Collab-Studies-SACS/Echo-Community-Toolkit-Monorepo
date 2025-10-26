# Auto-generated MRP Phase A stubs — 2025-10-13T05:14:22.138385Z
# SPDX-License-Identifier: MIT

import base64, json, pytest
from src.mrp.headers import make_frame, parse_frame, crc32_hex, MRPHeader
from src.mrp.codec import _parity_byte, _mk_b_json

def test_header_roundtrip():
    payload = b"seed"
    f = make_frame("R", payload, with_crc=True)
    hdr = parse_frame(f)
    assert hdr.magic == "MRP1"
    assert hdr.channel == "R"
    assert hdr.length == len(payload)
    assert hdr.crc32 is not None

def test_crc_mismatch_detects():
    payload = b"seed"
    f = make_frame("R", payload, with_crc=True)
    tampered = f.replace(b"c2VlZA==", b"c2VlZQ==")  # 'seed' -> 'seeq'
    with pytest.raises(ValueError):
        parse_frame(tampered)

def test_parity():
    r = make_frame("R", b"abc", True)
    g = make_frame("G", b"xyz", True)
    hdr_r = parse_frame(r)
    hdr_g = parse_frame(g)
    bj = _mk_b_json(hdr_r, hdr_g)
    assert isinstance(bj["parity"], str) and len(bj["parity"]) == 2
