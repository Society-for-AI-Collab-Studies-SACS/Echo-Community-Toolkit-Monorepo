"""
Core encode/decode routines for the Multi-Channel Resonance Protocol (MRP).

The encoder writes three framed payloads into the RGB channels of a cover PNG:
    R channel → primary message (base64 bytes)
    G channel → metadata JSON (base64 bytes)
    B channel → integrity/ECC sidecar JSON (base64 bytes)

Each channel is wrapped with a compact header:
    magic (4 bytes)  : b"MRP1"
    channel (1 byte) : ordinal of 'R', 'G', or 'B'
    flags (1 byte)   : bit 0 = CRC32 present
    length (4 bytes) : payload byte length
    [crc32] (4 bytes): optional CRC32 over payload when flag set

The header is followed by the payload bytes. Frames are embedded MSB-first into
the least-significant bit of the corresponding channel. Only 1 bit per channel
is currently supported; this keeps the implementation compact and matches the
expectations of the healing regression tests.
"""

from __future__ import annotations

import base64
import hashlib
import json
import zlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from PIL import Image
from reedsolo import RSCodec, ReedSolomonError

from .frame import (
    FLAG_CRC32,
    HEADER_WITH_CRC_BYTES,
    MRPFrame,
    crc32_hex as frame_crc32_hex,
)

RS_PARITY_BYTES = 16  # RS parity symbols (t = 8 byte corrections)

_rs_codec = RSCodec(RS_PARITY_BYTES)


# ---------------------------------------------------------------------------
# Bit helpers
# ---------------------------------------------------------------------------

def _bytes_to_bits(buf: bytes) -> List[int]:
    return [(byte >> shift) & 1 for byte in buf for shift in range(7, -1, -1)]


def _bits_to_bytes(bits: Iterable[int]) -> bytes:
    out = bytearray()
    bucket: List[int] = []
    for bit in bits:
        bucket.append(bit & 1)
        if len(bucket) == 8:
            value = 0
            for idx, b in enumerate(bucket):
                value |= b << (7 - idx)
            out.append(value)
            bucket.clear()
    if bucket:
        while len(bucket) < 8:
            bucket.append(0)
        value = 0
        for idx, b in enumerate(bucket):
            value |= b << (7 - idx)
        out.append(value)
    return bytes(out)


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    if len(left) < len(right):
        left = left.ljust(len(right), b"\x00")
    elif len(right) < len(left):
        right = right.ljust(len(left), b"\x00")
    return bytes(a ^ b for a, b in zip(left, right))


# ---------------------------------------------------------------------------
# Hamming (7,4) utilities
# ---------------------------------------------------------------------------

def _hamming_encode_bits(data_bits: List[int]) -> List[int]:
    encoded: List[int] = []
    for i in range(0, len(data_bits), 4):
        nibble = data_bits[i : i + 4]
        while len(nibble) < 4:
            nibble.append(0)
        d1, d2, d3, d4 = nibble
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p3 = d2 ^ d3 ^ d4
        encoded.extend([p1, p2, d1, p3, d2, d3, d4])
    return encoded


def _hamming_decode_bits(code_bits: List[int]) -> Tuple[List[int], bool]:
    decoded: List[int] = []
    had_error = False
    for i in range(0, len(code_bits), 7):
        block = code_bits[i : i + 7]
        if len(block) < 7:
            block.extend([0] * (7 - len(block)))
        p1, p2, d1, p3, d2, d3, d4 = block
        s1 = p1 ^ d1 ^ d2 ^ d4
        s2 = p2 ^ d1 ^ d3 ^ d4
        s3 = p3 ^ d2 ^ d3 ^ d4
        syndrome = (s3 << 2) | (s2 << 1) | s1
        if syndrome:
            had_error = True
            idx = syndrome - 1
            if 0 <= idx < 7:
                block[idx] ^= 1
                p1, p2, d1, p3, d2, d3, d4 = block
        decoded.extend([d1, d2, d3, d4])
    return decoded, had_error


# ---------------------------------------------------------------------------
# Image bit plane helpers
# ---------------------------------------------------------------------------

def _embed_bits_into_image(data: bytearray, offset: int, bits: List[int]) -> None:
    for idx, bit in enumerate(bits):
        pos = offset + idx
        data[pos] = (data[pos] & 0xFE) | (bit & 1)


def _extract_bits(raw: bytes, offset: int, count: int) -> List[int]:
    return [(raw[offset + idx] & 1) for idx in range(count) if (offset + idx) < len(raw)]


# ---------------------------------------------------------------------------
# ECC application helpers
# ---------------------------------------------------------------------------

def _apply_ecc_encode(payload: bytes, scheme: str) -> Tuple[bytes, Dict[str, Any]]:
    if scheme == "parity":
        return payload, {}
    if scheme == "hamming":
        bits = _bytes_to_bits(payload)
        encoded_bits = _hamming_encode_bits(bits)
        return _bits_to_bytes(encoded_bits), {}
    if scheme == "rs":
        return bytes(_rs_codec.encode(payload)), {}
    raise ValueError(f"Unsupported ECC scheme {scheme!r}")


def _apply_ecc_decode(encoded: bytes, scheme: str, expected_length: int) -> Tuple[Optional[bytes], Dict[str, Any]]:
    if scheme == "parity":
        return encoded[:expected_length], {}
    if scheme == "hamming":
        bits = _bytes_to_bits(encoded)
        decoded_bits, corrected = _hamming_decode_bits(bits)
        decoded_bytes = _bits_to_bytes(decoded_bits)[:expected_length]
        return decoded_bytes, {"hamming_corrected": corrected}
    if scheme == "rs":
        try:
            decoded, _, _ = _rs_codec.decode(encoded)  # type: ignore[misc]
        except ReedSolomonError as exc:
            return None, {"rs_error": str(exc)}
        return bytes(decoded[:expected_length]), {}
    raise ValueError(f"Unsupported ECC scheme {scheme!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encode_mrp(
    cover_path: str,
    out_path: str,
    message: str,
    metadata: Dict[str, Any],
    *,
    ecc: str = "parity",
) -> Dict[str, Any]:
    """Embed message + metadata into cover image using the requested ECC scheme."""
    cover = Image.open(cover_path).convert("RGB")
    width, height = cover.size
    stride = 3  # RGB
    raw = bytearray(cover.tobytes())

    message_bytes = message.encode("utf-8")
    metadata_json = json.dumps(metadata, ensure_ascii=False).encode("utf-8")
    payload_r = base64.b64encode(message_bytes)
    payload_g = base64.b64encode(metadata_json)

    encoded_r, _ = _apply_ecc_encode(payload_r, ecc)
    encoded_g, _ = _apply_ecc_encode(payload_g, ecc)

    parity_bytes: Optional[bytes] = None
    if ecc == "parity":
        length_g = len(payload_g)
        buf = bytearray(length_g)
        for idx in range(length_g):
            if idx < len(payload_r):
                buf[idx] = payload_r[idx] ^ payload_g[idx]
            else:
                buf[idx] = payload_g[idx]
        parity_bytes = bytes(buf)

    sha_msg_b64 = hashlib.sha256(payload_r).hexdigest()
    sha_msg_plain = hashlib.sha256(message_bytes).hexdigest()

    sidecar: Dict[str, Any] = {
        "ecc_scheme": ecc,
        "crc_r": frame_crc32_hex(payload_r),
        "crc_g": frame_crc32_hex(payload_g),
        "sha256_msg_b64": sha_msg_b64,
        "len_r": len(payload_r),
        "len_g": len(payload_g),
    }
    # Retain legacy digest for tooling that still inspects raw message bytes.
    sidecar["sha256_msg"] = sha_msg_plain
    if parity_bytes is not None:
        sidecar["parity_block_b64"] = base64.b64encode(parity_bytes).decode("ascii")

    sidecar_bytes = json.dumps(sidecar, separators=(",", ":")).encode("utf-8")
    payload_b = base64.b64encode(sidecar_bytes)

    frame_r = MRPFrame.build("R", encoded_r).to_bytes()
    frame_g = MRPFrame.build("G", encoded_g).to_bytes()
    frame_b = MRPFrame.build("B", payload_b).to_bytes()

    bits_r = _bytes_to_bits(frame_r)
    bits_g = _bytes_to_bits(frame_g)
    bits_b = _bytes_to_bits(frame_b)

    total_bits_needed = len(bits_r) + len(bits_g) + len(bits_b)
    if total_bits_needed > len(raw):
        raise ValueError("Not enough capacity in cover image for MRP payloads")

    offset_r = 0
    offset_g = offset_r + len(bits_r)
    offset_b = offset_g + len(bits_g)

    _embed_bits_into_image(raw, offset_r, bits_r)
    _embed_bits_into_image(raw, offset_g, bits_g)
    _embed_bits_into_image(raw, offset_b, bits_b)

    stego = Image.frombytes("RGB", cover.size, bytes(raw))
    stego.save(out_path, format="PNG")

    cover.close()
    stego.close()

    return {
        "cover": cover_path,
        "stego": out_path,
        "ecc": ecc,
        "payload_lengths": {
            "r": len(payload_r),
            "g": len(payload_g),
        },
    }


def decode_mrp(stego_path: str) -> Dict[str, Any]:
    """Decode an MRP stego PNG, applying ECC corrections when possible."""
    image = Image.open(stego_path).convert("RGB")
    raw = image.tobytes()
    raw_bits = [byte & 1 for byte in raw]
    cursor = 0

    def _consume_frame(expected_channel: str) -> MRPFrame:
        nonlocal cursor
        header_bits = HEADER_WITH_CRC_BYTES * 8
        if cursor + header_bits > len(raw_bits):
            raise ValueError("Incomplete frame header")
        header_bytes = _bits_to_bytes(raw_bits[cursor : cursor + header_bits])
        length = int.from_bytes(header_bytes[6:10], "big")
        total_bits = header_bits + length * 8
        if cursor + total_bits > len(raw_bits):
            raise ValueError("Incomplete payload data")
        frame_bits = raw_bits[cursor : cursor + total_bits]
        frame_bytes = _bits_to_bytes(frame_bits)
        parsed, _consumed = MRPFrame.parse_from(frame_bytes, expected_channel=expected_channel)
        cursor += total_bits
        return parsed

    try:
        parsed_r = _consume_frame("R")
        parsed_g = _consume_frame("G")
        parsed_b = _consume_frame("B")
    except ValueError as exc:
        image.close()
        return {"error": str(exc)}

    def _load_sidecar(payload: bytes) -> Dict[str, Any]:
        try:
            return json.loads(payload.decode("utf-8"))
        except Exception:
            decoded = base64.b64decode(payload, validate=True)
            return json.loads(decoded.decode("utf-8"))

    try:
        sidecar = _load_sidecar(parsed_b.payload)
    except Exception as exc:
        image.close()
        return {"error": f"Invalid B-channel payload: {exc}"}

    ecc_scheme = sidecar.get("ecc_scheme", "parity")
    header_mismatch = {
        "R": not parsed_r.channel_valid,
        "G": not parsed_g.channel_valid,
        "B": not parsed_b.channel_valid,
    }
    if header_mismatch["B"]:
        image.close()
        return {"error": "Channel header mismatch detected"}
    if (header_mismatch["R"] or header_mismatch["G"]) and ecc_scheme == "parity":
        image.close()
        return {"error": "Channel header mismatch detected"}

    payload_length_r = int(sidecar.get("len_r") or sidecar.get("payload_length_r") or 0)
    payload_length_g = int(sidecar.get("len_g") or sidecar.get("payload_length_g") or 0)
    if payload_length_r <= 0:
        payload_length_r = len(parsed_r.payload)
    if payload_length_g <= 0:
        payload_length_g = len(parsed_g.payload)

    decoded_r, ecc_report_r = _apply_ecc_decode(parsed_r.payload, ecc_scheme, payload_length_r)
    decoded_g, ecc_report_g = _apply_ecc_decode(parsed_g.payload, ecc_scheme, payload_length_g)

    if decoded_r is None or decoded_g is None:
        image.close()
        error_reason = "Reed-Solomon decode failed" if ecc_scheme == "rs" else "ECC decode failed"
        if ecc_scheme == "rs" and ecc_report_r.get("rs_error"):
            error_reason = ecc_report_r["rs_error"]
        return {"error": error_reason}

    parity_bytes = b""
    parity_str = sidecar.get("parity_block_b64")
    if parity_str:
        try:
            parity_bytes = base64.b64decode(parity_str)
        except Exception:
            parity_bytes = b""

    def _parity_from_payloads(r_bytes: bytes, g_bytes: bytes, length: int) -> bytes:
        block = bytearray(length)
        for idx in range(length):
            r_val = r_bytes[idx] if idx < len(r_bytes) else 0
            g_val = g_bytes[idx] if idx < len(g_bytes) else 0
            block[idx] = r_val ^ g_val
        return bytes(block)

    def _recover_with_fallback(
        parity: bytes, known: bytes, fallback: bytes, target_length: int
    ) -> bytes:
        recovered = bytearray(target_length)
        for idx in range(target_length):
            if idx < len(parity):
                parity_val = parity[idx]
                known_val = known[idx] if idx < len(known) else 0
                recovered[idx] = parity_val ^ known_val
            elif idx < len(fallback):
                recovered[idx] = fallback[idx]
            else:
                recovered[idx] = 0
        return bytes(recovered)

    crc_r_expected = sidecar.get("crc_r")
    crc_g_expected = sidecar.get("crc_g")

    crc_r_calc = f"{zlib.crc32(decoded_r) & 0xFFFFFFFF:08X}"
    crc_g_calc = f"{zlib.crc32(decoded_g) & 0xFFFFFFFF:08X}"

    crc_r_ok = crc_r_expected is None or crc_r_calc == crc_r_expected
    crc_g_ok = crc_g_expected is None or crc_g_calc == crc_g_expected

    parity_ok = True
    if parity_bytes:
        parity_calc = _parity_from_payloads(decoded_r, decoded_g, len(parity_bytes))
        parity_ok = parity_calc == parity_bytes
    elif ecc_scheme == "parity":
        parity_ok = False

    original_r = decoded_r
    original_g = decoded_g
    repaired = False
    if (header_mismatch["R"] or header_mismatch["G"]) and ecc_scheme != "parity":
        repaired = True
    repair_error: Optional[str] = None
    if parity_bytes and ecc_scheme != "parity" and ((not crc_r_ok) ^ (not crc_g_ok)):
        if not crc_r_ok and crc_g_ok:
            recovered_r = _recover_with_fallback(parity_bytes, decoded_g, original_r, payload_length_r)
            new_crc_r = f"{zlib.crc32(recovered_r) & 0xFFFFFFFF:08X}"
            sha_expected_b64 = sidecar.get("sha256_msg_b64")
            sha_match = True
            if sha_expected_b64:
                sha_match = hashlib.sha256(recovered_r).hexdigest() == sha_expected_b64
            if (crc_r_expected is None or new_crc_r == crc_r_expected) and sha_match:
                decoded_r = recovered_r[:payload_length_r]
                crc_r_calc = new_crc_r
                crc_r_ok = True
                repaired = True
            else:
                repair_error = "Failed to repair R channel - data unrecoverable"
        elif not crc_g_ok and crc_r_ok:
            recovered_g = _recover_with_fallback(parity_bytes, decoded_r, original_g, payload_length_g)
            new_crc_g = f"{zlib.crc32(recovered_g) & 0xFFFFFFFF:08X}"
            if crc_g_expected is None or new_crc_g == crc_g_expected:
                decoded_g = recovered_g[:payload_length_g]
                crc_g_calc = new_crc_g
                crc_g_ok = True
                repaired = True
            else:
                repair_error = "Failed to repair G channel - data unrecoverable"
    elif parity_bytes and not crc_r_ok and not crc_g_ok:
        repair_error = "Multiple channel corruption detected - cannot repair"

    if parity_bytes:
        parity_calc = _parity_from_payloads(decoded_r, decoded_g, len(parity_bytes))
        parity_ok = parity_calc == parity_bytes

    try:
        message_bytes = base64.b64decode(decoded_r, validate=True)
        metadata_bytes = base64.b64decode(decoded_g, validate=True)
    except Exception as exc:
        image.close()
        return {"error": f"Base64 decode failed: {exc}"}

    sha_calc_b64 = hashlib.sha256(decoded_r).hexdigest()
    sha_calc_plain = hashlib.sha256(message_bytes).hexdigest()
    sha_expected_b64 = sidecar.get("sha256_msg_b64")
    sha_expected_plain = sidecar.get("sha256_msg")
    sha_ok = True
    if sha_expected_b64:
        sha_ok = sha_ok and (sha_calc_b64 == sha_expected_b64)
    if sha_expected_plain:
        sha_ok = sha_ok and (sha_calc_plain == sha_expected_plain)

    payload_ok = crc_r_ok and crc_g_ok and sha_ok and parity_ok

    report: Dict[str, Any] = {
        "crc_r": crc_r_calc,
        "crc_g": crc_g_calc,
        "sha256_msg_b64": sha_calc_b64,
        "sha256_msg": sha_calc_plain,
        "payload_length_r": payload_length_r,
        "payload_length_g": payload_length_g,
        "ecc_scheme": ecc_scheme,
        "parity_ok": parity_ok,
        "crc_r_ok": crc_r_ok,
        "crc_g_ok": crc_g_ok,
        "sha_ok": sha_ok,
        "repaired": repaired,
        "header_mismatch": header_mismatch,
    }
    report.update({f"r_{key}": value for key, value in ecc_report_r.items()})
    report.update({f"g_{key}": value for key, value in ecc_report_g.items()})

    result: Dict[str, Any] = {
        "message": message_bytes.decode("utf-8", "replace"),
        "metadata": json.loads(metadata_bytes.decode("utf-8", "replace")),
        "report": report,
    }

    if not payload_ok:
        result["error"] = repair_error or "Integrity check failed"
    elif report.get("ecc_scheme") == "parity" and report.get("repaired"):
        result["error"] = repair_error or "Parity integrity check failed"

    image.close()
    return result
