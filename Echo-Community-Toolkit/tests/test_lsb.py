import base64
from pathlib import Path
import zlib

import pytest

from src.lsb_encoder_decoder import LSBCodec
from src.lsb_extractor import (
    FLAG_HAS_CRC32,
    LSBExtractor,
    LSBParseError,
    decode_base64_payload,
    extract_legacy_payload,
    parse_lsb1_packet,
)


def _build_lsb1_packet(payload: bytes, crc_override: int | None = None) -> bytes:
    crc_val = zlib.crc32(payload) & 0xFFFFFFFF if crc_override is None else crc_override
    parts = [
        b"LSB1",
        bytes([1]),  # version
        bytes([FLAG_HAS_CRC32]),
        len(payload).to_bytes(4, "big"),
        crc_val.to_bytes(4, "big"),
        payload,
    ]
    return b"".join(parts)


def test_parse_lsb1_packet_valid():
    payload = base64.b64encode(b"garden-ritual")
    packet = _build_lsb1_packet(payload)

    header, extracted, cursor = parse_lsb1_packet(packet)

    assert header.magic == "LSB1"
    assert header.payload_length == len(payload)
    assert header.has_crc
    assert extracted == payload
    assert cursor == len(packet)


def test_parse_lsb1_packet_crc_mismatch_raises():
    payload = base64.b64encode(b"crc-mismatch")
    tampered_packet = _build_lsb1_packet(payload, crc_override=0)

    with pytest.raises(LSBParseError, match="CRC mismatch"):
        parse_lsb1_packet(tampered_packet)


def test_extract_legacy_payload_roundtrip():
    payload = base64.b64encode(b"legacy-path")
    stream = b"\x00\x00" + payload + b"\x00trailing"

    extracted, cursor = extract_legacy_payload(stream, start=2)
    b64, decoded = decode_base64_payload(extracted)

    assert extracted == payload
    assert cursor == 2 + len(payload)
    assert decoded == "legacy-path"
    assert b64 == payload.decode("ascii")


def test_decode_base64_payload_rejects_non_ascii():
    with pytest.raises(ValueError):
        decode_base64_payload(b"\xff\xff")


def test_decode_crc_failure_blocks_plaintext(tmp_path: Path):
    codec = LSBCodec()
    cover = codec.create_cover_image(32, 32)
    cover_path = tmp_path / "cover.png"
    cover.save(cover_path, "PNG")

    payload = base64.b64encode(b"crc")
    packet = _build_lsb1_packet(payload, crc_override=0)
    bits = [(byte >> shift) & 1 for byte in packet for shift in range(7, -1, -1)]

    stego = codec._embed_bits_lsb(cover, bits)
    stego_path = tmp_path / "crc_fail.png"
    stego.save(stego_path, "PNG")
    cover.close()
    stego.close()

    out = LSBExtractor().extract_from_image(stego_path)

    assert "error" in out
    assert "CRC mismatch" in out["error"]
    assert "decoded_text" not in out


def test_golden_sample_decode_matches_mantra():
    extractor = LSBExtractor()
    out = extractor.extract_from_image(Path("assets/images/echo_key.png"))
    mantra = Path("assets/data/LSB1_Mantra.txt").read_text(encoding="utf-8").strip()

    assert out["mode"] == "LSB1"
    assert out["detected_format"] == "lsb1"
    assert out["magic"] == "LSB1"
    assert out["payload_length"] == 144
    assert out["crc32"] == "6E3FD9B7"
    assert out["decoded_text"].strip() == mantra


def test_round_trip_lsb1_mode(tmp_path: Path):
    codec = LSBCodec()
    cover_path = tmp_path / "rt_cover.png"
    codec.create_cover_image(64, 64).save(cover_path, "PNG")

    stego_path = tmp_path / "rt_stego.png"
    info = codec.encode_message(cover_path, "abc", stego_path, True)
    assert info["mode"] == "lsb1"

    out = LSBExtractor().extract_from_image(stego_path)
    assert out["mode"] == "LSB1"
    assert out["magic"] == "LSB1"
    assert out["payload_length"] >= 3


def test_round_trip_bpc4(tmp_path: Path):
    codec = LSBCodec(bpc=4)
    cover_path = tmp_path / "rt_cover4.png"
    codec.create_cover_image(32, 32).save(cover_path, "PNG")

    stego_path = tmp_path / "rt_stego4.png"
    info = codec.encode_message(cover_path, "fourbit", stego_path, True)
    assert info["mode"] == "lsb1"
    assert info["bits_per_channel"] == 4

    out = LSBExtractor(bpc=4).extract_from_image(stego_path)
    assert out["mode"] == "LSB1"
    assert out["bits_per_channel"] == 4
    assert out["decoded_text"] == "fourbit"


def test_round_trip_mrp_mode(tmp_path: Path):
    codec = LSBCodec()
    cover_path = tmp_path / "mrp_cover.png"
    codec.create_cover_image(64, 64).save(cover_path, "PNG")

    stego_path = tmp_path / "mrp_stego.png"
    metadata = {"purpose": "mrp", "sequence": 7}
    info = codec.encode_message(
        cover_path,
        "garden",
        stego_path,
        mode="mrp",
        metadata=metadata,
    )
    assert info["mode"] == "mrp"
    assert "integrity" in info

    out = LSBExtractor().extract_from_image(stego_path)
    assert out["mode"] == "MRP"
    assert out["detected_format"] == "mrp"
    assert out["message"] == "garden"
    assert out["metadata"] == metadata
    assert out["integrity"]["status"] in {"ok", "degraded", "recovered_with_parity", "recovered"}
