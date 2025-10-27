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


def _mutate_b_channel(frame_bytes: bytes) -> bytes:
    frame, _ = MRPFrame.parse_from(frame_bytes, expected_channel="B")
    sidecar = json.loads(frame.payload.decode("utf-8"))
    sidecar["parity"] = "00"
    payload = json.dumps(sidecar, separators=(",", ":"), sort_keys=True).encode("utf-8")
    mutated = bytearray(make_frame("B", payload, True))
    crc_offset = 4 + 1 + 1 + 4  # magic + channel + flags + length
    mutated[crc_offset] ^= 0xFF
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
    assert integrity["status"] in {"recovered", "recovered_with_parity"}
    assert integrity["parity"]["used"] is True
    assert integrity["parity"]["recovered_bytes"] == 1

    channels = integrity["channels"]
    assert channels["R"]["recovered"] is True
    assert channels["R"]["corrected_bytes"] == 1
    assert channels["G"]["recovered"] is False


def test_mrp_parity_recovers_corrupted_g_channel(tmp_path: Path):
    cover_path, stego_path, metadata = _prep_mrp_image(tmp_path)
    frames = png_lsb.extract_frames(str(stego_path), bits_per_channel=1)
    frames["G"] = _flip_first_payload_byte(frames["G"], "G")

    corrupted = tmp_path / "stego_corrupt_g.png"
    png_lsb.embed_frames(str(cover_path), str(corrupted), frames, bits_per_channel=1)

    out = LSBExtractor().extract_from_image(corrupted)
    assert out["mode"] == "MRP"
    assert out["message"] == "garden"
    assert out["metadata"] == metadata

    integrity = out["integrity"]
    assert integrity["status"] in {"recovered", "recovered_with_parity"}
    assert integrity["parity"]["used"] is True
    assert integrity["parity"]["recovered_bytes"] == 1

    channels = integrity["channels"]
    assert channels["G"]["recovered"] is True
    assert channels["G"]["corrected_bytes"] == 1
    assert channels["R"]["recovered"] is False


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


def test_mrp_reports_degraded_when_b_channel_corrupted(tmp_path: Path):
    cover_path, stego_path, metadata = _prep_mrp_image(tmp_path)
    frames = png_lsb.extract_frames(str(stego_path), bits_per_channel=1)
    frames["B"] = _mutate_b_channel(frames["B"])

    corrupted = tmp_path / "stego_corrupt_b.png"
    png_lsb.embed_frames(str(cover_path), str(corrupted), frames, bits_per_channel=1)

    out = LSBExtractor().extract_from_image(corrupted)
    assert out["mode"] == "MRP"
    assert out["message"] == "garden"
    assert out["metadata"] == metadata

    integrity = out["integrity"]
    assert integrity["status"] == "degraded"
    assert integrity["parity"]["used"] is False
    assert integrity["parity"]["recovered_bytes"] == 0
    assert integrity["channels"]["B"]["crc_ok"] is False


def test_mrp_integrity_ok_path_marks_parity_unused(tmp_path: Path):
    _, stego_path, metadata = _prep_mrp_image(tmp_path)
    out = LSBExtractor().extract_from_image(stego_path)

    integrity = out["integrity"]
    assert integrity["status"] == "ok"
    assert integrity["parity"]["used"] is False
    assert integrity["parity"]["recovered_bytes"] == 0
    assert out["metadata"] == metadata
