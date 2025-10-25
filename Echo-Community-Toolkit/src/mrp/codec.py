from __future__ import annotations
import json, base64
from typing import Dict, Any, Tuple, Callable
from .headers import make_frame, parse_frame, MRPHeader
from .meta import sidecar_from_headers
from .adapters import png_lsb

def encode(cover_png: str, out_png: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    r = make_frame("R", message.encode(), True)
    g = make_frame("G", json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode(), True)
    b = make_frame("B", json.dumps(sidecar_from_headers(parse_frame(r), parse_frame(g))).encode(), True)
    png_lsb.embed_frames(cover_png, out_png, {"R": r, "G": g, "B": b})
    return {"out": out_png}

def decode(stego_png: str) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    f = png_lsb.extract_frames(stego_png)
    r, g, b = parse_frame(f["R"]), parse_frame(f["G"]), parse_frame(f["B"])
    msg = base64.b64decode(r.payload_b64).decode()
    meta = json.loads(base64.b64decode(g.payload_b64).decode())
    b_json = json.loads(base64.b64decode(b.payload_b64).decode())
    ecc = {
        "crc_match": (b_json.get("crc_r") == r.crc32 and b_json.get("crc_g") == g.crc32),
        "parity_match": bool(b_json.get("parity")),
        "ecc_scheme": b_json.get("ecc_scheme", "none")
    }
    return msg, meta, ecc


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
