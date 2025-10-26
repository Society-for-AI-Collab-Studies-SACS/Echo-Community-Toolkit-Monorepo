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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from PIL import Image
from reedsolo import RSCodec, ReedSolomonError

MAGIC = b"MRP1"
FLAG_CRC32 = 0x01
HEADER_WITH_CRC_BYTES = 4 + 1 + 1 + 4 + 4  # 112 bits when CRC flag is set
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
# Frame helpers
# ---------------------------------------------------------------------------

def _build_frame(channel: str, payload: bytes, *, add_crc: bool = True) -> bytes:
    if len(channel) != 1:
        raise ValueError("Channel identifier must be a single character.")
    flags = FLAG_CRC32 if add_crc else 0
    header = bytearray()
    header += MAGIC
    header += channel.encode("ascii")
    header.append(flags)
    header += len(payload).to_bytes(4, "big")
    if add_crc:
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        header += crc.to_bytes(4, "big")
    return bytes(header) + payload


@dataclass
class ParsedFrame:
    payload: bytes
    flags: int
    channel: str
    channel_valid: bool
    crc_value: Optional[int]
    crc_ok: bool


def _parse_frame(raw_bytes: bytes, expected_channel: str) -> ParsedFrame:
    start = raw_bytes.find(MAGIC)
    if start < 0:
        raise ValueError("MRP header not found")
    cursor = start + len(MAGIC)
    channel = chr(raw_bytes[cursor])
    cursor += 1
    channel_valid = channel == expected_channel
    flags = raw_bytes[cursor]
    cursor += 1
    length = int.from_bytes(raw_bytes[cursor : cursor + 4], "big")
    cursor += 4
    crc_header = None
    if flags & FLAG_CRC32:
        crc_header = int.from_bytes(raw_bytes[cursor : cursor + 4], "big")
        cursor += 4
    end = cursor + length
    if end > len(raw_bytes):
        raise ValueError("Incomplete payload data")
    payload = raw_bytes[cursor:end]
    crc_ok = True
    if flags & FLAG_CRC32:
        crc_calc = zlib.crc32(payload) & 0xFFFFFFFF
        crc_ok = crc_calc == crc_header
    return ParsedFrame(
        payload=payload,
        flags=flags,
        channel=channel,
        channel_valid=channel_valid,
        crc_value=crc_header,
        crc_ok=crc_ok,
    )


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
    metadata_json = json.dumps(metadata).encode("utf-8")
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

    sidecar: Dict[str, Any] = {
        "ecc_scheme": ecc,
        "crc_r": f"{zlib.crc32(payload_r) & 0xFFFFFFFF:08X}",
        "crc_g": f"{zlib.crc32(payload_g) & 0xFFFFFFFF:08X}",
        "sha256_msg": hashlib.sha256(message_bytes).hexdigest(),
        "len_r": len(payload_r),
        "len_g": len(payload_g),
    }
    if parity_bytes is not None:
        sidecar["parity_block_b64"] = base64.b64encode(parity_bytes).decode("ascii")

    encoded_b = json.dumps(sidecar, separators=(",", ":")).encode("ascii")

    frame_r = _build_frame("R", encoded_r)
    frame_g = _build_frame("G", encoded_g)
    frame_b = _build_frame("B", encoded_b)

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

    def _consume_frame(expected_channel: str) -> ParsedFrame:
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
        parsed = _parse_frame(frame_bytes, expected_channel)
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
    if ecc_scheme == "parity":
        try:
            parity_str = sidecar.get("parity_block_b64", "")
            parity_bytes = base64.b64decode(parity_str) if parity_str else b""
        except Exception:
            parity_bytes = b""

    crc_r_expected = sidecar.get("crc_r")
    crc_g_expected = sidecar.get("crc_g")

    crc_r_calc = f"{zlib.crc32(decoded_r) & 0xFFFFFFFF:08X}"
    crc_g_calc = f"{zlib.crc32(decoded_g) & 0xFFFFFFFF:08X}"

    crc_r_ok = crc_r_expected is None or crc_r_calc == crc_r_expected
    crc_g_ok = crc_g_expected is None or crc_g_calc == crc_g_expected

    parity_ok = True
    if parity_bytes:
        parity_calc = _xor_bytes(decoded_r, decoded_g)[: len(parity_bytes)]
        parity_ok = parity_calc == parity_bytes
    elif ecc_scheme == "parity":
        parity_ok = False

    repaired = False
    if (header_mismatch["R"] or header_mismatch["G"]) and ecc_scheme != "parity":
        repaired = True
    repair_error: Optional[str] = None
    if parity_bytes and ecc_scheme != "parity" and (not crc_r_ok or not crc_g_ok):
        if crc_r_ok and not crc_g_ok:
            recovered_g = bytearray(payload_length_g)
            for idx in range(payload_length_g):
                parity_val = parity_bytes[idx] if idx < len(parity_bytes) else 0
                known = decoded_r[idx] if idx < len(decoded_r) else 0
                recovered_g[idx] = parity_val ^ known
            new_crc_g = f"{zlib.crc32(recovered_g) & 0xFFFFFFFF:08X}"
            if new_crc_g == crc_g_expected:
                decoded_g = bytes(recovered_g)
                crc_g_calc = new_crc_g
                crc_g_ok = True
                repaired = True
            else:
                repair_error = "Failed to repair G channel"
        elif crc_g_ok and not crc_r_ok:
            recovered_r = bytearray(payload_length_r)
            for idx in range(payload_length_r):
                parity_val = parity_bytes[idx] if idx < len(parity_bytes) else 0
                known = decoded_g[idx] if idx < len(decoded_g) else 0
                recovered_r[idx] = parity_val ^ known
            new_crc_r = f"{zlib.crc32(recovered_r) & 0xFFFFFFFF:08X}"
            if new_crc_r == crc_r_expected:
                decoded_r = bytes(recovered_r)
                crc_r_calc = new_crc_r
                crc_r_ok = True
                repaired = True
            else:
                repair_error = "Failed to repair R channel"
        else:
            repair_error = "Multiple channel corruption detected"

        if repaired:
            parity_calc = _xor_bytes(decoded_r, decoded_g)[: len(parity_bytes)]
            parity_ok = parity_calc == parity_bytes

    try:
        message_bytes = base64.b64decode(decoded_r, validate=True)
        metadata_bytes = base64.b64decode(decoded_g, validate=True)
    except Exception as exc:
        image.close()
        return {"error": f"Base64 decode failed: {exc}"}

    sha_calc = hashlib.sha256(message_bytes).hexdigest()
    sha_expected = sidecar.get("sha256_msg") or sidecar.get("sha256_msg_b64")
    sha_ok = sha_expected is None or sha_calc == sha_expected

    payload_ok = crc_r_ok and crc_g_ok and sha_ok and parity_ok

    report: Dict[str, Any] = {
        "crc_r": crc_r_calc,
        "crc_g": crc_g_calc,
        "sha256_msg": sha_calc,
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

    image.close()
    return result
