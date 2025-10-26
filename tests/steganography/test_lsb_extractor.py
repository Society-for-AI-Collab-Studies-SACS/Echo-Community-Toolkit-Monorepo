from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path

import pytest
from PIL import Image

import lsb_extractor
from lsb_extractor import LSBExtractor
from lsb_encoder_decoder import LSBCodec, _bytes_to_bits_msb


def _dummy_image(path: Path) -> None:
    Image.new("RGB", (8, 8), "black").save(path, "PNG")


def test_lsb1_header_parsing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    codec = LSBCodec()
    packet = codec._build_lsb1_packet("hello stego", use_crc=True)
    bits = _bytes_to_bits_msb(packet)

    monkeypatch.setattr(lsb_extractor, "_extract_bits_rgb_lsb", lambda img: bits)

    target = tmp_path / "carrier.png"
    _dummy_image(target)

    result = LSBExtractor().extract_from_image(target)
    payload = base64.b64encode(b"hello stego")
    expected_crc = f"{zlib.crc32(payload) & 0xFFFFFFFF:08X}"

    assert result["decoded_text"] == "hello stego"
    assert result["magic"] == "LSB1"
    assert result["version"] == 1
    assert result["flags"] == 1
    assert result["payload_length"] == len(payload)
    assert result["crc32"] == expected_crc


def test_crc_mismatch_reports_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    codec = LSBCodec()
    packet = codec._build_lsb1_packet("hello crc", use_crc=True)
    bits = _bytes_to_bits_msb(packet)

    corrupted = bits.copy()
    corrupted[112] ^= 1  # flip first payload bit (header=14 bytes)

    monkeypatch.setattr(lsb_extractor, "_extract_bits_rgb_lsb", lambda img: corrupted)

    target = tmp_path / "carrier.png"
    _dummy_image(target)

    result = LSBExtractor().extract_from_image(target)
    assert "error" in result
    assert "CRC mismatch" in result["error"]


def test_base64_decode_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = b"!!!!"
    header = (
        b"LSB1"
        + bytes([1])  # version
        + bytes([0])  # flags (no CRC)
        + len(payload).to_bytes(4, "big")
    )
    packet = header + payload
    bits = _bytes_to_bits_msb(packet)

    monkeypatch.setattr(lsb_extractor, "_extract_bits_rgb_lsb", lambda img: bits)

    target = tmp_path / "carrier.png"
    _dummy_image(target)

    result = LSBExtractor().extract_from_image(target)
    assert "error" in result
    assert "Base64 decode failed" in result["error"]


def test_golden_sample_regression() -> None:
    extractor = LSBExtractor()
    image_path = Path("Echo-Community-Toolkit/assets/images/echo_key.png")
    result = extractor.extract_from_image(image_path)

    expected = json.loads(
        Path("Echo-Community-Toolkit/assets/data/echo_key_decoded.json").read_text(encoding="utf-8")
    )

    assert result["decoded_text"] == expected["decoded_text"]
    assert result["base64_payload"] == expected["base64_payload"]
    assert result["magic"] == expected["magic"]
    assert result["version"] == expected["version"]
    assert result["flags"] == expected["flags"]
    assert result["payload_length"] == expected["payload_length"]
    assert result["crc32"] == expected["crc32"]
