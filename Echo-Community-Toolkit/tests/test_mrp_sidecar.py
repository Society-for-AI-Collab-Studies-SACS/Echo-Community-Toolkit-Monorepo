from __future__ import annotations

import hashlib
import json

from src.mrp.headers import make_frame, parse_frame
from src.mrp.sidecar import generate_sidecar, validate_sidecar


def _build_headers():
    r_frame = make_frame("R", b"Hello, Garden.", True)
    g_payload = json.dumps({"tool": "echo-mrp", "phase": "A"}, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    g_frame = make_frame("G", g_payload, True)

    r_header = parse_frame(r_frame)
    g_header = parse_frame(g_frame)
    sidecar_doc = generate_sidecar(r_header, g_header, include_schema=False)
    b_frame = make_frame("B", json.dumps(sidecar_doc, separators=(",", ":"), sort_keys=True).encode("utf-8"), True)
    b_header = parse_frame(b_frame)
    return r_header, g_header, b_header, sidecar_doc


def test_generate_sidecar_produces_expected_fields():
    r_header, g_header, _, sidecar_doc = _build_headers()
    expected_sha = hashlib.sha256(b"Hello, Garden.").hexdigest()

    assert sidecar_doc["crc_r"] == r_header.crc32
    assert sidecar_doc["crc_g"] == g_header.crc32
    assert sidecar_doc["ecc_scheme"] == "parity"
    assert sidecar_doc["sha256_msg_b64"] == expected_sha
    assert len(sidecar_doc["parity"]) == 2


def test_validate_sidecar_passes_for_canonical_payload():
    r_header, g_header, b_header, sidecar_doc = _build_headers()
    validation = validate_sidecar(sidecar_doc, r_header, g_header, b_header)

    assert validation.valid
    assert all(validation.checks.get(key, False) for key in ("crc_match", "parity_match", "sha256_match"))


def test_validate_sidecar_flags_bad_crc():
    r_header, g_header, b_header, sidecar_doc = _build_headers()
    tampered = dict(sidecar_doc)
    tampered["crc_r"] = "00000000"

    validation = validate_sidecar(tampered, r_header, g_header, b_header)

    assert not validation.valid
    assert not validation.checks.get("crc_match")
    assert "crc_match" in validation.errors
