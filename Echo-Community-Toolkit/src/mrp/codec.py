from __future__ import annotations

import base64
import json
from hashlib import sha256
from typing import Callable, Dict, Any

from .adapters import png_lsb
from .ecc import xor_parity_bytes
from .headers import MRPHeader, crc32_hex, make_frame
from .meta import sidecar_from_headers


def _load_channel(frame_bytes: bytes) -> Dict[str, Any]:
    header = MRPHeader.from_json_bytes(frame_bytes)
    payload = base64.b64decode(header.payload_b64.encode("utf-8"))
    calc_crc = crc32_hex(payload)
    expected = (header.crc32 or calc_crc).upper()
    return {
        "header": header,
        "payload": payload,
        "crc_expected": expected,
        "crc_actual": calc_crc,
        "crc_ok": expected == calc_crc,
        "recovered": False,
    }


def _parity_bytes(hex_value: str) -> bytes:
    if not hex_value:
        return b""
    try:
        return bytes.fromhex(hex_value)
    except ValueError:
        return b""


def _xor_recover(parity: bytes, other_payload: bytes, length: int) -> bytes:
    if not parity:
        return b""
    if len(other_payload) < len(parity):
        other_payload = other_payload + b"\x00" * (len(parity) - len(other_payload))
    recovered = bytes(p ^ o for p, o in zip(parity, other_payload))
    return recovered[:length]


def _recover_channel(target: Dict[str, Any], other: Dict[str, Any], parity: bytes) -> bool:
    recovered = _xor_recover(parity, other["payload"], target["header"].length)
    if not recovered:
        return False
    calc_crc = crc32_hex(recovered)
    if calc_crc != target["crc_expected"]:
        return False
    target["payload"] = recovered
    target["crc_actual"] = calc_crc
    target["crc_ok"] = True
    target["recovered"] = True
    return True


def encode(cover_png: str, out_png: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    message_bytes = message.encode("utf-8")
    metadata_bytes = json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode("utf-8")

    r_frame = make_frame("R", message_bytes, True)
    g_frame = make_frame("G", metadata_bytes, True)

    r_header = MRPHeader.from_json_bytes(r_frame)
    g_header = MRPHeader.from_json_bytes(g_frame)
    sidecar = sidecar_from_headers(r_header, g_header)

    b_frame = make_frame(
        "B",
        json.dumps(sidecar, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        True,
    )

    png_lsb.embed_frames(cover_png, out_png, {"R": r_frame, "G": g_frame, "B": b_frame})
    return {
        "out": out_png,
        "integrity": sidecar,
    }


def decode(stego_png: str) -> Dict[str, Any]:
    frames = png_lsb.extract_frames(stego_png)
    channels = {ch: _load_channel(frames[ch]) for ch in ("R", "G", "B")}

    try:
        sidecar = json.loads(channels["B"]["payload"].decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid B-channel payload: {exc}") from exc

    expected_crc_r = (sidecar.get("crc_r") or channels["R"]["crc_expected"]).upper()
    expected_crc_g = (sidecar.get("crc_g") or channels["G"]["crc_expected"]).upper()
    parity_hex_value = (sidecar.get("parity") or "").upper()
    parity_bytes = _parity_bytes(parity_hex_value)

    channels["R"]["crc_expected"] = expected_crc_r
    channels["G"]["crc_expected"] = expected_crc_g

    recovery_performed = False
    if not channels["R"]["crc_ok"] and channels["G"]["crc_ok"]:
        recovery_performed |= _recover_channel(channels["R"], channels["G"], parity_bytes)
    if not channels["G"]["crc_ok"] and channels["R"]["crc_ok"]:
        recovery_performed |= _recover_channel(channels["G"], channels["R"], parity_bytes)

    if not channels["R"]["crc_ok"] or not channels["G"]["crc_ok"]:
        raise ValueError("Unrecoverable channel corruption detected")

    try:
        message_text = channels["R"]["payload"].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Message payload is not valid UTF-8") from exc

    try:
        metadata = json.loads(channels["G"]["payload"].decode("utf-8"))
    except Exception as exc:
        raise ValueError("Metadata payload is not valid JSON") from exc

    digest = sha256(channels["R"]["payload"]).digest()
    sha_actual_hex = digest.hex()
    sha_actual_b64 = base64.b64encode(digest).decode("ascii")
    sha_expected_hex = (sidecar.get("sha256_msg") or "").lower()
    sha_expected_b64 = sidecar.get("sha256_msg_b64") or ""
    sha_ok = (
        (sha_expected_hex and sha_actual_hex == sha_expected_hex)
        or (sha_expected_b64 and sha_actual_b64 == sha_expected_b64)
        or (not sha_expected_hex and not sha_expected_b64)
    )

    parity_ok = True
    parity_actual = b""
    if parity_hex_value:
        parity_actual = xor_parity_bytes(channels["R"]["payload"], channels["G"]["payload"])
        parity_ok = parity_bytes == parity_actual

    b_crc_ok = channels["B"]["crc_ok"]

    if not sha_ok:
        status = "integrity_failed"
    elif recovery_performed:
        status = "recovered"
    elif not b_crc_ok or not parity_ok:
        status = "degraded"
    else:
        status = "ok"

    integrity = {
        "status": status,
        "sha256": {
            "expected": sha_expected_hex or sha_expected_b64 or sha_actual_hex,
            "actual": sha_actual_hex,
            "ok": sha_ok,
        },
        "parity": {
            "expected": parity_hex_value,
            "actual": parity_actual.hex().upper() if parity_actual else "",
            "ok": parity_ok,
        },
        "channels": {
            ch: {
                "crc_expected": info["crc_expected"],
                "crc_actual": info["crc_actual"],
                "crc_ok": info["crc_ok"],
                "recovered": info["recovered"],
            }
            for ch, info in channels.items()
        },
        "sidecar": sidecar,
    }

    return {
        "message": message_text,
        "metadata": metadata,
        "integrity": integrity,
    }


# --- Experimental Expansion Entry Point -------------------------------------


def _encode_phase_a(cover_png: str, out_png: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    return encode(cover_png, out_png, message, metadata)


def _encode_sigprint(cover_png: str, out_png: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    enriched_meta = {
        **metadata,
        "sigprint_id": metadata.get("sigprint_id", "SIG001"),
        "pen_pressure": metadata.get("pen_pressure", "medium"),
        "intent": metadata.get("intent", "symbolic_transfer"),
    }
    return encode(cover_png, out_png, message.upper(), enriched_meta)


def _encode_entropic(*_args, **_kwargs):
    raise NotImplementedError("Entropic mode not yet implemented")


def _encode_bloom(cover_png: str, out_png: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    bloom_meta = {
        **metadata,
        "quantum_signature": metadata.get("quantum_signature", "bloom-a"),
        "resonance_phase": metadata.get("resonance_phase", "alpha"),
    }
    return encode(cover_png, out_png, message, bloom_meta)


_MODE_HANDLERS: Dict[str, Callable[[str, str, str, Dict[str, Any]], Dict[str, Any]]] = {
    "phaseA": _encode_phase_a,
    "sigprint": _encode_sigprint,
    "entropic": _encode_entropic,
    "bloom": _encode_bloom,
}


def encode_with_mode(
    cover_png: str,
    out_png: str,
    message: str,
    metadata: Dict[str, Any],
    mode: str = "phaseA",
) -> Dict[str, Any]:
    """
    Encode with an optional alternate mode (default: 'phaseA').

    Supports standard Phase-A encoding or experimental modes such as
    sigprint synthesis, stylus-specific parity tuning, etc.
    """

    try:
        handler = _MODE_HANDLERS[mode]
    except KeyError as exc:
        raise ValueError(f"Unknown mode: {mode}") from exc
    return handler(cover_png, out_png, message, metadata)
