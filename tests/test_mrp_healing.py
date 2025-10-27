import base64
import json
import zlib
import hashlib
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from mrp import encode_mrp, decode_mrp  # noqa: E402

TEST_MESSAGE = "hello world"
TEST_METADATA = {"purpose": "MRP test", "sequence": 1}


def _compute_crc_hex(data_bytes: bytes) -> str:
    return f"{zlib.crc32(data_bytes) & 0xFFFFFFFF:08X}"


def _flip_image_bit(png_path: Path, bit_index: int):
    img = Image.open(png_path).convert("RGB")
    w, h = img.size
    pixel_index = bit_index // 3
    channel_index = bit_index % 3
    x = pixel_index % w
    y = pixel_index // w
    r, g, b = img.getpixel((x, y))
    if channel_index == 0:
        r ^= 0x01
    elif channel_index == 1:
        g ^= 0x01
    else:
        b ^= 0x01
    img.putpixel((x, y), (r, g, b))
    img.save(png_path, "PNG")
    img.close()


def test_mrp_parity_detection():
    cover_path = Path("cover_tmp.png")
    stego_path = Path("stego_parity.png")
    Image.new("RGB", (50, 50), color=0).save(cover_path, "PNG")

    encode_mrp(str(cover_path), str(stego_path), TEST_MESSAGE, TEST_METADATA, ecc="parity")
    cover_path.unlink(missing_ok=True)

    out = decode_mrp(str(stego_path))
    assert "error" not in out
    assert out.get("message") == TEST_MESSAGE
    assert out.get("metadata") == TEST_METADATA

    base64_msg = base64.b64encode(TEST_MESSAGE.encode("utf-8"))
    base64_meta = base64.b64encode(json.dumps(TEST_METADATA).encode("utf-8"))
    expected_crc_r = _compute_crc_hex(base64_msg)
    expected_crc_g = _compute_crc_hex(base64_meta)
    expected_sha_b64 = hashlib.sha256(base64_msg).hexdigest()
    expected_sha_plain = hashlib.sha256(TEST_MESSAGE.encode("utf-8")).hexdigest()
    report = out.get("report", {})
    assert report.get("crc_r") == expected_crc_r
    assert report.get("crc_g") == expected_crc_g
    assert report.get("sha256_msg_b64") == expected_sha_b64
    assert report.get("sha256_msg") == expected_sha_plain

    _flip_image_bit(stego_path, 112)
    out_corrupt = decode_mrp(str(stego_path))
    assert "error" in out_corrupt

    encode_mrp(str(stego_path), str(stego_path), TEST_MESSAGE, TEST_METADATA, ecc="parity")
    flip_bit_index = 112 + report.get("payload_length_r", 0) * 8
    _flip_image_bit(stego_path, flip_bit_index)
    out_corrupt = decode_mrp(str(stego_path))
    assert "error" in out_corrupt
    stego_path.unlink(missing_ok=True)


def test_mrp_hamming_correction():
    cover_path = Path("cover_tmp2.png")
    stego_path = Path("stego_hamming.png")
    Image.new("RGB", (50, 50), color=0).save(cover_path, "PNG")

    encode_mrp(str(cover_path), str(stego_path), TEST_MESSAGE, TEST_METADATA, ecc="hamming")
    cover_path.unlink(missing_ok=True)

    out = decode_mrp(str(stego_path))
    assert "error" not in out

    _flip_image_bit(stego_path, 112)
    out_fixed = decode_mrp(str(stego_path))
    assert "error" not in out_fixed
    assert out_fixed.get("message") == TEST_MESSAGE

    base64_msg = base64.b64encode(TEST_MESSAGE.encode("utf-8"))
    expected_crc_r = _compute_crc_hex(base64_msg)
    assert out_fixed["report"].get("crc_r") == expected_crc_r

    _flip_image_bit(stego_path, 113)
    out_double_error = decode_mrp(str(stego_path))
    assert "error" in out_double_error
    stego_path.unlink(missing_ok=True)


def test_mrp_reed_solomon_healing():
    cover_path = Path("cover_tmp3.png")
    stego_path = Path("stego_rs.png")
    Image.new("RGB", (50, 50), color=0).save(cover_path, "PNG")

    encode_mrp(str(cover_path), str(stego_path), TEST_MESSAGE, TEST_METADATA, ecc="rs")
    cover_path.unlink(missing_ok=True)

    out = decode_mrp(str(stego_path))
    assert "error" not in out

    payload_bit_start = 112
    for offset in [3, 11, 19, 27, 35]:
        _flip_image_bit(stego_path, payload_bit_start + offset)

    out_healed = decode_mrp(str(stego_path))
    assert "error" not in out_healed
    assert out_healed.get("message") == TEST_MESSAGE

    payload_byte_count = len(base64.b64encode(TEST_MESSAGE.encode("utf-8")))
    flips = 0
    bit_index = payload_bit_start
    while flips < 18 and bit_index < payload_bit_start + payload_byte_count * 8:
        _flip_image_bit(stego_path, bit_index)
        bit_index += 8
        flips += 1

    out_overwhelmed = decode_mrp(str(stego_path))
    assert "error" in out_overwhelmed
    stego_path.unlink(missing_ok=True)


def test_mrp_B_channel_corruption():
    cover_path = Path("cover_tmp4.png")
    stego_path = Path("stego_b_corrupt.png")
    Image.new("RGB", (50, 50), color=0).save(cover_path, "PNG")

    encode_mrp(str(cover_path), str(stego_path), TEST_MESSAGE, TEST_METADATA, ecc="parity")
    cover_path.unlink(missing_ok=True)

    base64_msg = base64.b64encode(TEST_MESSAGE.encode("utf-8"))
    base64_meta = base64.b64encode(json.dumps(TEST_METADATA).encode("utf-8"))
    r_bits = 112 + len(base64_msg) * 8
    g_bits = 112 + len(base64_meta) * 8
    b_payload_start = r_bits + g_bits
    _flip_image_bit(stego_path, b_payload_start + 120)

    out = decode_mrp(str(stego_path))
    assert "error" in out
    stego_path.unlink(missing_ok=True)
