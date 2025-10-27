from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
from PIL import Image

from mrp.adapters import png_lsb
from mrp.codec import decode, encode
from mrp.headers import MRPHeader


def _create_cover(path: Path, size: tuple[int, int] = (64, 64)) -> None:
    Image.new("RGB", size, "white").save(path, "PNG")


def _mutate_channel(path: Path, channel: str, mutator) -> None:
    frames = png_lsb.extract_frames(str(path))
    header = MRPHeader.from_json_bytes(frames[channel])
    payload = bytearray(base64.b64decode(header.payload_b64.encode("utf-8")))
    mutator(payload)
    header.payload_b64 = base64.b64encode(bytes(payload)).decode("utf-8")
    frames[channel] = header.to_json_bytes()
    png_lsb.embed_frames(str(path), str(path), frames)


def _corrupt_b_sidecar(path: Path, *, parity_value: str = "00") -> None:
    frames = png_lsb.extract_frames(str(path))
    header = MRPHeader.from_json_bytes(frames["B"])
    payload = json.loads(base64.b64decode(header.payload_b64.encode("utf-8")).decode("utf-8"))
    payload["parity"] = parity_value
    mutated = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    header.payload_b64 = base64.b64encode(mutated).decode("utf-8")
    frames["B"] = header.to_json_bytes()
    png_lsb.embed_frames(str(path), str(path), frames)


def _encode_fixture(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    cover = tmp_path / "cover.png"
    stego = tmp_path / "stego.png"
    _create_cover(cover)
    metadata = {"author": "alice", "scene": "forest"}
    encode(str(cover), str(stego), "echo", metadata)
    return stego, metadata


def test_mrp_roundtrip_integrity_ok(tmp_path: Path) -> None:
    stego, metadata = _encode_fixture(tmp_path)
    decoded = decode(str(stego))

    assert decoded["message"] == "echo"
    assert decoded["metadata"] == metadata

    integrity = decoded["integrity"]
    assert integrity["status"] == "ok"
    assert integrity["sha256"]["ok"]
    assert integrity["parity"]["ok"]
    for ch in ("R", "G", "B"):
        assert integrity["channels"][ch]["crc_ok"]


def test_mrp_parity_recovers_message(tmp_path: Path) -> None:
    stego, _ = _encode_fixture(tmp_path)

    def mutate(payload: bytearray) -> None:
        payload[0] ^= 0x01

    _mutate_channel(stego, "R", mutate)

    decoded = decode(str(stego))
    integrity = decoded["integrity"]
    assert decoded["message"] == "echo"
    assert integrity["status"] == "recovered"
    assert integrity["channels"]["R"]["recovered"]
    assert integrity["channels"]["R"]["crc_ok"]


def test_mrp_parity_recovers_metadata(tmp_path: Path) -> None:
    stego, metadata = _encode_fixture(tmp_path)

    def mutate(payload: bytearray) -> None:
        payload[-1] ^= 0x01

    _mutate_channel(stego, "G", mutate)

    decoded = decode(str(stego))
    integrity = decoded["integrity"]
    assert decoded["metadata"] == metadata
    assert integrity["status"] == "recovered"
    assert integrity["channels"]["G"]["recovered"]
    assert integrity["channels"]["G"]["crc_ok"]


def test_mrp_unrecoverable_raises(tmp_path: Path) -> None:
    stego, _ = _encode_fixture(tmp_path)

    def mutate(payload: bytearray) -> None:
        payload[0] ^= 0x01

    _mutate_channel(stego, "R", mutate)
    _mutate_channel(stego, "G", mutate)

    with pytest.raises(ValueError):
        decode(str(stego))


def test_mrp_degraded_when_b_corrupted(tmp_path: Path) -> None:
    stego, _ = _encode_fixture(tmp_path)
    _corrupt_b_sidecar(stego, parity_value="00")

    decoded = decode(str(stego))
    integrity = decoded["integrity"]
    assert integrity["status"] == "degraded"
    assert not integrity["channels"]["B"]["crc_ok"]
    assert decoded["message"] == "echo"
