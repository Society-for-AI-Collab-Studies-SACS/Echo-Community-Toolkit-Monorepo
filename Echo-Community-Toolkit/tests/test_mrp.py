import base64
import json
from pathlib import Path

import pytest

from src.lsb_encoder_decoder import LSBCodec
from src.lsb_extractor import LSBExtractor
from src.mrp.adapters import png_lsb
from src.mrp.frame import MRPFrame, make_frame, parse_frame
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


def _prep_mrp_image(tmp_path: Path):
    codec = LSBCodec()
    cover_path = tmp_path / "cover.png"
    codec.create_cover_image(64, 64).save(cover_path, "PNG")
    stego_path = tmp_path / "stego.png"
    metadata = {"purpose": "mrp", "sequence": 7}
    codec.encode_message(
        cover_path,
        "garden",
        stego_path,
        mode="mrp",
        metadata=metadata,
    )
    return cover_path, stego_path, metadata


def _flip_first_payload_byte(frame_bytes: bytes, channel: str) -> bytes:
    frame, consumed = MRPFrame.parse_from(frame_bytes, expected_channel=channel)
    payload_start = consumed - frame.length
    mutated = bytearray(frame_bytes)
    mutated[payload_start] ^= 0x01
    return bytes(mutated)


def test_mrp_parity_recovers_corrupted_r_channel(tmp_path: Path):
    cover_path, stego_path, metadata = _prep_mrp_image(tmp_path)
    frames = png_lsb.extract_frames(str(stego_path), bits_per_channel=1)
    frames["R"] = _flip_first_payload_byte(frames["R"], "R")

    corrupted = tmp_path / "stego_corrupt_r.png"
    png_lsb.embed_frames(str(cover_path), str(corrupted), frames, bits_per_channel=1)

    out = LSBExtractor().extract_from_image(corrupted)
    assert out["mode"] == "MRP"
    assert out["message"] == "garden"
    assert out["metadata"] == metadata

    integrity = out["integrity"]
    assert integrity["status"] == "recovered_with_parity"
    assert integrity["parity"]["used"] is True
    assert integrity["parity"]["recovered_bytes"] > 0

    channels = integrity["channels"]
    assert channels["R"]["recovered"] is True
    assert channels["R"]["corrected_bytes"] > 0
    assert channels["G"]["recovered"] is False


def test_mrp_parity_cannot_recover_when_multiple_channels_corrupt(tmp_path: Path):
    cover_path, stego_path, _ = _prep_mrp_image(tmp_path)
    frames = png_lsb.extract_frames(str(stego_path), bits_per_channel=1)
    frames["R"] = _flip_first_payload_byte(frames["R"], "R")
    frames["G"] = _flip_first_payload_byte(frames["G"], "G")

    corrupted = tmp_path / "stego_corrupt_rg.png"
    png_lsb.embed_frames(str(cover_path), str(corrupted), frames, bits_per_channel=1)

    out = LSBExtractor().extract_from_image(corrupted)
    assert out["mode"] == "MRP"
    assert "error" in out
    assert "Unrecoverable channel corruption" in out["error"]
