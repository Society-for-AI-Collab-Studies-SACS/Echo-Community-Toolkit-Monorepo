from __future__ import annotations

import base64
import hashlib
import json

from src.mrp.ecc import xor_parity_bytes
from src.mrp.frame import make_frame, parse_frame
from src.mrp.sidecar import generate_sidecar, validate_sidecar


def _build_headers():
    message_payload = base64.b64encode(b"Hello, Garden.")
    g_payload = base64.b64encode(
        json.dumps({"tool": "echo-mrp", "phase": "A"}, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )

    r_frame = make_frame("R", message_payload, True)
    g_frame = make_frame("G", g_payload, True)

    r_header = parse_frame(r_frame)
    g_header = parse_frame(g_frame)
    sidecar_doc = generate_sidecar(r_header, g_header, include_schema=False)
    b_frame = make_frame("B", json.dumps(sidecar_doc, separators=(",", ":"), sort_keys=True).encode("utf-8"), True)
    b_header = parse_frame(b_frame)
    return r_header, g_header, b_header, sidecar_doc


def test_generate_sidecar_produces_expected_fields():
    r_header, g_header, _, sidecar_doc = _build_headers()
    payload_bytes = b"Hello, Garden."
    expected_sha_hex = hashlib.sha256(payload_bytes).hexdigest()
    expected_sha_b64 = hashlib.sha256(base64.b64encode(payload_bytes)).hexdigest()
    expected_parity_len = max(r_header.length, g_header.length)

    assert sidecar_doc["crc_r"] == f"{r_header.crc32:08X}"
    assert sidecar_doc["crc_g"] == f"{g_header.crc32:08X}"
    assert sidecar_doc["ecc_scheme"] == "xor"
    assert sidecar_doc["sha256_msg"] == expected_sha_hex
    assert sidecar_doc["sha256_msg_b64"] == expected_sha_b64
    assert len(sidecar_doc["parity"]) == expected_parity_len * 2
    assert sidecar_doc["parity_len"] == expected_parity_len
    assert sidecar_doc["bits_per_channel"] == 1
    assert "parity_block_b64" in sidecar_doc
    assert base64.b64decode(sidecar_doc["parity_block_b64"]) == xor_parity_bytes(
        r_header.payload, g_header.payload
    )


def test_validate_sidecar_passes_for_canonical_payload():
    r_header, g_header, b_header, sidecar_doc = _build_headers()
    validation = validate_sidecar(sidecar_doc, r_header, g_header, b_header)

    assert validation.valid
    assert all(
        validation.checks.get(key, False)
        for key in ("crc_match", "parity_match", "sha256_match", "bits_per_channel_match")
    )


def test_validate_sidecar_flags_bad_crc():
    r_header, g_header, b_header, sidecar_doc = _build_headers()
    tampered = dict(sidecar_doc)
    tampered["crc_r"] = "00000000"

    validation = validate_sidecar(tampered, r_header, g_header, b_header)

    assert not validation.valid
    assert not validation.checks.get("crc_match")
    assert "crc_match" in validation.errors
