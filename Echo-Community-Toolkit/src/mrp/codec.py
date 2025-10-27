from __future__ import annotations

import base64
import binascii
import json
from hashlib import sha256
from typing import Any, Callable, Dict, Optional

from mrp.adapters import png_lsb
from mrp.ecc import xor_parity_bytes
from mrp.frame import MRPFrame, crc32_hex, make_frame
from mrp.meta import sidecar_from_frames
from ritual.state import (
    RitualConsentError,
    RitualState,
    default_ritual_state,
)


def _load_channel(frame_bytes: bytes, expected: Optional[str] = None) -> Dict[str, Any]:
    frame, _consumed = MRPFrame.parse_from(frame_bytes, expected_channel=expected)
    payload = frame.payload
    calc_crc = crc32_hex(payload)
    expected_crc = calc_crc if frame.crc32 is None else f"{frame.crc32:08X}"
    return {
        "header": frame,
        "payload": payload,
        "crc_expected": expected_crc,
        "crc_actual": calc_crc,
        "crc_ok": expected_crc == calc_crc,
        "recovered": False,
        "corrected_bytes": 0,
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


def _recover_channel(target: Dict[str, Any], other: Dict[str, Any], parity: bytes) -> int:
    recovered = _xor_recover(parity, other["payload"], target["header"].length)
    if not recovered:
        return 0
    calc_crc = crc32_hex(recovered)
    if calc_crc != target["crc_expected"]:
        return 0
    prior_payload = target["payload"]
    target["payload"] = recovered
    target["crc_actual"] = calc_crc
    target["crc_ok"] = True
    target["recovered"] = True
    corrected = sum(
        1
        for old_byte, new_byte in zip(prior_payload, recovered)
        if old_byte != new_byte
    )
    target["corrected_bytes"] = corrected
    return corrected


def _resolve_state(state: Optional[RitualState]) -> RitualState:
    return state or default_ritual_state


def encode(
    cover_png: str,
    out_png: str,
    message: str,
    metadata: Dict[str, Any],
    *,
    ritual_state: Optional[RitualState] = None,
    bits_per_channel: int = 1,
    ecc: str = "parity",
) -> Dict[str, Any]:
    state = _resolve_state(ritual_state)
    state.require_publish_ready()

    if bits_per_channel not in png_lsb.SUPPORTED_BPC:
        raise ValueError(f"Unsupported bits_per_channel: {bits_per_channel}")

    message_bytes = message.encode("utf-8")
    metadata_json = json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode("utf-8")

    payload_r = base64.b64encode(message_bytes)
    payload_g = base64.b64encode(metadata_json)

    ecc_scheme = ecc.lower()
    if ecc_scheme not in {"parity", "xor"}:
        raise ValueError(f"Unsupported ecc scheme: {ecc}")

    r_frame_bytes = make_frame("R", payload_r, True)
    g_frame_bytes = make_frame("G", payload_g, True)

    r_frame, _ = MRPFrame.parse_from(r_frame_bytes, expected_channel="R")
    g_frame, _ = MRPFrame.parse_from(g_frame_bytes, expected_channel="G")
    sidecar = sidecar_from_frames(
        r_frame,
        g_frame,
        bits_per_channel=bits_per_channel,
        ecc_scheme="parity" if ecc_scheme == "xor" else ecc_scheme,
    )

    b_frame_bytes = make_frame(
        "B",
        json.dumps(sidecar, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        True,
    )

    png_lsb.embed_frames(
        cover_png,
        out_png,
        {"R": r_frame_bytes, "G": g_frame_bytes, "B": b_frame_bytes},
        bits_per_channel=bits_per_channel,
    )
    state.record_operation(
        "encode",
        {
            "cover": cover_png,
            "out": out_png,
            "message_length": len(message_bytes),
            "metadata_keys": sorted(metadata.keys()),
            "bits_per_channel": bits_per_channel,
        },
    )
    return {
        "out": out_png,
        "integrity": sidecar,
        "ecc": sidecar.get("ecc_scheme", ecc_scheme),
    }


def _decode_frames(frames: Dict[str, bytes], *, bits_per_channel: int) -> Dict[str, Any]:
    channels = {ch: _load_channel(frames[ch], expected=ch) for ch in ("R", "G", "B")}

    try:
        sidecar = json.loads(channels["B"]["payload"].decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid B-channel payload: {exc}") from exc

    sidecar_bpc = sidecar.get("bits_per_channel")
    if isinstance(sidecar_bpc, str):
        try:
            sidecar_bpc = int(sidecar_bpc)
        except ValueError:
            sidecar_bpc = None
    if sidecar_bpc not in (None, bits_per_channel):
        raise ValueError(
            f"Bits-per-channel mismatch (sidecar={sidecar_bpc}, requested={bits_per_channel}). "
            "Re-run decode with the correct --bpc flag."
        )

    expected_crc_r = (sidecar.get("crc_r") or channels["R"]["crc_expected"]).upper()
    expected_crc_g = (sidecar.get("crc_g") or channels["G"]["crc_expected"]).upper()
    parity_len_expected = int(
        sidecar.get("parity_len")
        or max(len(channels["R"]["payload"]), len(channels["G"]["payload"]))
    )
    parity_hex_value = (sidecar.get("parity") or "").upper()
    parity_bytes = _parity_bytes(parity_hex_value) if parity_hex_value else b""
    parity_length_valid = True
    if parity_hex_value and len(parity_hex_value) != parity_len_expected * 2:
        parity_length_valid = False
        parity_bytes = b""

    channels["R"]["crc_expected"] = expected_crc_r
    channels["G"]["crc_expected"] = expected_crc_g

    recovered_bytes_total = 0
    if not channels["R"]["crc_ok"] and channels["G"]["crc_ok"]:
        recovered_bytes_total += _recover_channel(channels["R"], channels["G"], parity_bytes)
    if not channels["G"]["crc_ok"] and channels["R"]["crc_ok"]:
        recovered_bytes_total += _recover_channel(channels["G"], channels["R"], parity_bytes)

    if not channels["R"]["crc_ok"] or not channels["G"]["crc_ok"]:
        raise ValueError("Unrecoverable channel corruption detected")

    try:
        message_bytes = base64.b64decode(channels["R"]["payload"], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Message payload is not valid base64") from exc

    try:
        metadata_bytes = base64.b64decode(channels["G"]["payload"], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Metadata payload is not valid base64") from exc

    try:
        message_text = message_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Message payload is not valid UTF-8") from exc

    try:
        metadata = json.loads(metadata_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Metadata payload is not valid JSON") from exc

    sha_calc_b64 = sha256(channels["R"]["payload"]).hexdigest()
    sha_calc_plain = sha256(message_bytes).hexdigest()
    sha_expected_plain = (sidecar.get("sha256_msg") or "").lower()
    sha_expected_b64 = (sidecar.get("sha256_msg_b64") or "").lower()

    sha_ok = True
    if sha_expected_b64:
        sha_ok = sha_ok and (sha_calc_b64.lower() == sha_expected_b64)
    if sha_expected_plain:
        sha_ok = sha_ok and (sha_calc_plain == sha_expected_plain)
    if not sha_expected_b64 and not sha_expected_plain:
        sha_ok = True

    parity_ok = True
    parity_actual = b""
    if parity_hex_value:
        parity_actual = xor_parity_bytes(channels["R"]["payload"], channels["G"]["payload"])
        parity_ok = parity_length_valid and parity_bytes == parity_actual
    elif parity_len_expected:
        parity_ok = False

    crc_r_ok = channels["R"]["crc_ok"]
    crc_g_ok = channels["G"]["crc_ok"]
    b_crc_ok = channels["B"]["crc_ok"]

    if not sha_ok:
        status = "integrity_failed"
    elif not (crc_r_ok and crc_g_ok):
        status = "failed"
    elif recovered_bytes_total > 0:
        status = "recovered"
    elif not b_crc_ok or not parity_ok or not parity_length_valid:
        status = "degraded"
    else:
        status = "ok"

    integrity = {
        "status": status,
        "sha256": {
            "expected": sha_expected_plain or sha_expected_b64 or sha_calc_plain,
            "actual": sha_calc_plain,
            "actual_base64_payload": sha_calc_b64,
            "actual_message": sha_calc_plain,
            "ok": sha_ok,
        },
        "parity": {
            "expected": parity_hex_value,
            "actual": parity_actual.hex().upper() if parity_actual else "",
            "ok": parity_ok,
            "used": recovered_bytes_total > 0,
            "recovered_bytes": recovered_bytes_total,
        },
        "channels": {
            ch: {
                "crc_expected": info["crc_expected"],
                "crc_actual": info["crc_actual"],
                "crc_ok": info["crc_ok"],
                "recovered": info["recovered"],
                "corrected_bytes": info.get("corrected_bytes", 0),
            }
            for ch, info in channels.items()
        },
        "sidecar": sidecar,
    }

    result = {
        "message": message_text,
        "metadata": metadata,
        "integrity": integrity,
        "message_length": len(message_bytes),
    }

    if status in {"failed", "integrity_failed"}:
        result["error"] = "Integrity check failed"

    return result


def decode(
    stego_png: str,
    *,
    ritual_state: Optional[RitualState] = None,
    bits_per_channel: int = 1,
) -> Dict[str, Any]:
    state = _resolve_state(ritual_state)
    state.require_publish_ready()

    if bits_per_channel not in png_lsb.SUPPORTED_BPC:
        raise ValueError(f"Unsupported bits_per_channel: {bits_per_channel}")

    try:
        frames = png_lsb.extract_frames(stego_png, bits_per_channel=bits_per_channel)
    except (ValueError, IndexError) as exc:
        raise ValueError(
            f"Unable to extract frames with bits_per_channel={bits_per_channel}. "
            "If this is a Phase-A image encoded with a different depth, rerun with the matching --bpc value."
        ) from exc

    result = _decode_frames(frames, bits_per_channel=bits_per_channel)

    if "error" in result:
        raise ValueError(result["error"])

    state.record_operation(
        "decode",
        {
            "stego": stego_png,
            "status": result["integrity"]["status"],
            "message_length": result.get("message_length", len(result["message"].encode("utf-8"))),
            "bits_per_channel": bits_per_channel,
        },
    )
    result_out = dict(result)
    result_out.pop("message_length", None)
    return result_out


# --- Experimental Expansion Entry Point -------------------------------------

def _encode_phase_a(
    cover_png: str,
    out_png: str,
    message: str,
    metadata: Dict[str, Any],
    *,
    ritual_state: Optional[RitualState] = None,
    bits_per_channel: int = 1,
) -> Dict[str, Any]:
    return encode(
        cover_png,
        out_png,
        message,
        metadata,
        ritual_state=ritual_state,
        bits_per_channel=bits_per_channel,
    )


def _encode_sigprint(
    cover_png: str,
    out_png: str,
    message: str,
    metadata: Dict[str, Any],
    *,
    ritual_state: Optional[RitualState] = None,
    bits_per_channel: int = 1,
) -> Dict[str, Any]:
    enriched_meta = {
        **metadata,
        "sigprint_id": metadata.get("sigprint_id", "SIG001"),
        "pen_pressure": metadata.get("pen_pressure", "medium"),
        "intent": metadata.get("intent", "symbolic_transfer"),
    }
    return encode(
        cover_png,
        out_png,
        message.upper(),
        enriched_meta,
        ritual_state=ritual_state,
        bits_per_channel=bits_per_channel,
    )


def _encode_entropic(*_args, **_kwargs):
    raise NotImplementedError("Entropic mode not yet implemented")


def _encode_bloom(
    cover_png: str,
    out_png: str,
    message: str,
    metadata: Dict[str, Any],
    *,
    ritual_state: Optional[RitualState] = None,
    bits_per_channel: int = 1,
) -> Dict[str, Any]:
    bloom_meta = {
        **metadata,
        "quantum_signature": metadata.get("quantum_signature", "bloom-a"),
        "resonance_phase": metadata.get("resonance_phase", "alpha"),
    }
    return encode(
        cover_png,
        out_png,
        message,
        bloom_meta,
        ritual_state=ritual_state,
        bits_per_channel=bits_per_channel,
    )


_MODE_HANDLERS: Dict[str, Callable[..., Dict[str, Any]]] = {
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
    *,
    ritual_state: Optional[RitualState] = None,
    bits_per_channel: int = 1,
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
    return handler(
        cover_png,
        out_png,
        message,
        metadata,
        ritual_state=ritual_state,
        bits_per_channel=bits_per_channel,
    )


__all__ = [
    "RitualConsentError",
    "encode",
    "encode_with_mode",
    "decode",
]
