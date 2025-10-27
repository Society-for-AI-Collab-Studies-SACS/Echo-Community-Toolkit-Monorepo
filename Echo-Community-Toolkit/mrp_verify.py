#!/usr/bin/env python3
"""
mrp_verify.py — Multi-Channel Resonance Protocol (MRP) Phase‑A verifier

Verifies an MRP Phase‑A stego payload using the provided
R/G/B payload JSONs and optional sidecar JSON. Checks:
  • CRC32 of raw R/G payload bytes against B-channel claims
  • SHA‑256 (hex + base64) of the R payload against B & sidecar
  • XOR parity (hex) between R/G payloads for Phase‑A
  • Sidecar sanity (if provided): header flags, used_bits math, capacity_bits vs PNG dims

Exit code: 0 on success, 1 on any check failing.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import struct
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

HEADER_LEN_WITH_CRC = 14  # magic(4)+channel(1)+flags(1)+length(4)+crc32(4)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def crc32_hex(data: bytes) -> str:
    # zlib.crc32 returns signed in some envs; mask to 32-bit
    import zlib

    return format(zlib.crc32(data) & 0xFFFFFFFF, "08X")


def minify_json_bytes(obj: Any) -> bytes:
    """Stable, ascii-preserving minify used for base64 body generation."""

    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_png_dims(path: str) -> Optional[Tuple[int, int]]:
    """
    Read PNG width/height from header without external deps.
    Returns (width, height) or None if not PNG / malformed.
    """

    try:
        with open(path, "rb") as f:
            sig = f.read(8)
            if sig != b"\x89PNG\r\n\x1a\n":
                return None
            # Next comes IHDR chunk: length(4) 'IHDR'(4) then data
            ihdr_len = struct.unpack(">I", f.read(4))[0]
            ihdr_type = f.read(4)
            if ihdr_type != b"IHDR":
                return None
            ihdr = f.read(ihdr_len)
            if len(ihdr) < 8:
                return None
            width = struct.unpack(">I", ihdr[0:4])[0]
            height = struct.unpack(">I", ihdr[4:8])[0]
            return width, height
    except Exception:
        return None


def compute_phase_a_parity_hex(r_payload: bytes, g_payload: bytes) -> Tuple[str, int]:
    """
    Phase‑A parity block (hex representation) and length:
      • Pad shorter payload with zeros
      • XOR byte-wise
      • Return uppercase hex string plus underlying byte length
    """

    length = max(len(r_payload), len(g_payload))
    if length == 0:
        return "", 0

    parity = bytearray(length)
    for idx in range(length):
        r_val = r_payload[idx] if idx < len(r_payload) else 0
        g_val = g_payload[idx] if idx < len(g_payload) else 0
        parity[idx] = r_val ^ g_val

    return bytes(parity).hex().upper(), length


def verify(args) -> Dict[str, Any]:
    # Load payloads
    R_obj = load_json(args.R)
    G_obj = load_json(args.G)
    B_obj = load_json(args.B)

    # Minify to canonical payload bytes
    R_min = minify_json_bytes(R_obj)
    G_min = minify_json_bytes(G_obj)
    B_min = minify_json_bytes(B_obj)

    # Recompute hashes
    crc_r = crc32_hex(R_min)
    crc_g = crc32_hex(G_min)
    sha_digest = hashlib.sha256(R_min).digest()
    sha_r_hex = sha_digest.hex()
    sha_r_b64 = base64.b64encode(sha_digest).decode("ascii")

    # Expected from B-payload
    exp_crc_r = (B_obj.get("crc_r") or "").upper()
    exp_crc_g = (B_obj.get("crc_g") or "").upper()
    exp_sha_hex = (B_obj.get("sha256_msg") or "").lower()
    exp_sha_b64 = B_obj.get("sha256_msg_b64") or ""
    exp_parity = (B_obj.get("parity") or "").upper()
    exp_parity_len = B_obj.get("parity_len")
    ecc_scheme = B_obj.get("ecc_scheme")

    # Parity recompute (Phase‑A only)
    calc_parity, calc_parity_len = compute_phase_a_parity_hex(R_min, G_min)

    checks = {
        "crc_r_ok": bool(exp_crc_r) and crc_r == exp_crc_r,
        "crc_g_ok": bool(exp_crc_g) and crc_g == exp_crc_g,
        "sha256_r_hex_ok": bool(exp_sha_hex) and sha_r_hex == exp_sha_hex,
        "sha256_r_b64_ok": bool(exp_sha_b64) and sha_r_b64 == exp_sha_b64,
        "ecc_scheme_ok": ecc_scheme in ("xor", "XOR"),
        "parity_block_ok": bool(exp_parity) and calc_parity == exp_parity,
        "parity_len_ok": isinstance(exp_parity_len, int) and exp_parity_len == calc_parity_len,
    }

    # Sidecar checks (optional)
    sidecar_info = None
    if args.sidecar and os.path.exists(args.sidecar):
        S = load_json(args.sidecar)
        sidecar_info = S

        # image dims / capacity
        dims = compute_png_dims(S.get("file") or args.image or "")
        if dims:
            w, h = dims
            cap_bits_expected = w * h  # 1 bit per pixel per channel, LSB1
        else:
            w = h = None
            cap_bits_expected = None

        ch = S.get("channels", {})
        headers = S.get("headers", {})

        # Used bits math (payload_len + 14 header) * 8 must match
        used_bits_math_ok = True
        cap_bits_ok = True
        header_magic_ok = True
        header_flags_crc_set = True

        expected_payload_lengths = {
            "R": len(R_min),
            "G": len(G_min),
            "B": len(B_min),
        }

        payload_len_ok = True

        for k in ("R", "G", "B"):
            ch_k = ch.get(k, {})
            hdr_k = headers.get(k, {})
            payload_len = ch_k.get("payload_len")
            used_bits = ch_k.get("used_bits")
            capacity_bits = ch_k.get("capacity_bits")

            # used bits math
            if isinstance(payload_len, int) and isinstance(used_bits, int):
                if used_bits != (payload_len + HEADER_LEN_WITH_CRC) * 8:
                    used_bits_math_ok = False
                if payload_len != expected_payload_lengths.get(k):
                    payload_len_ok = False
            else:
                used_bits_math_ok = False
                payload_len_ok = False

            # capacity bits
            if cap_bits_expected is not None and isinstance(capacity_bits, int):
                if capacity_bits != cap_bits_expected:
                    cap_bits_ok = False

            # headers
            if hdr_k.get("magic") != "MRP1" or hdr_k.get("channel") != k:
                header_magic_ok = False
            # bit0 of flags indicates CRC present in Phase‑A
            flags = hdr_k.get("flags")
            if not isinstance(flags, int) or (flags & 0x01) != 0x01:
                header_flags_crc_set = False

        # Sidecar sha check
        sidecar_sha_ok = (
            S.get("sha256_msg") == sha_r_hex
            or S.get("sha256_msg_b64") == sha_r_b64
        )

        checks.update(
            {
                "sidecar_sha256_ok": sidecar_sha_ok,
                "sidecar_used_bits_math_ok": used_bits_math_ok,
                "sidecar_payload_len_ok": payload_len_ok,
                "sidecar_capacity_bits_ok": cap_bits_ok,
                "sidecar_header_magic_ok": header_magic_ok,
                "sidecar_header_flags_crc_ok": header_flags_crc_set,
            }
        )

    # Overall
    ok = all(checks.values())

    report = {
        "inputs": {
            "image": args.image,
            "R": args.R,
            "G": args.G,
            "B": args.B,
            "sidecar": args.sidecar,
        },
        "image_info": {},
        "lengths": {
            "R_min_bytes": len(R_min),
            "G_min_bytes": len(G_min),
            "B_min_bytes": len(B_min),
            "parity_len_bytes": calc_parity_len,
        },
        "computed": {
            "crc_r": crc_r,
            "crc_g": crc_g,
            "sha256_r_hex": sha_r_hex,
            "sha256_r_b64": sha_r_b64,
            "parity_hex_head": calc_parity[:64] + ("..." if len(calc_parity) > 64 else ""),
        },
        "expected_from_B": {
            "crc_r": exp_crc_r,
            "crc_g": exp_crc_g,
            "sha256_msg": exp_sha_hex,
            "sha256_msg_b64": exp_sha_b64,
            "ecc_scheme": ecc_scheme,
            "parity": exp_parity,
            "parity_len": exp_parity_len,
        },
        "checks": checks,
        "mrp_ok": ok,
    }

    # Attach sidecar echo if present
    if sidecar_info is not None:
        # include just a minimal echo to avoid huge logs
        report["sidecar_echo"] = {
            "file": sidecar_info.get("file"),
            "sha256_msg": sidecar_info.get("sha256_msg"),
            "sha256_msg_b64": sidecar_info.get("sha256_msg_b64"),
            "channels": sidecar_info.get("channels"),
            "headers": sidecar_info.get("headers"),
        }

    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify MRP Phase‑A stego payloads.")
    ap.add_argument(
        "image",
        nargs="?",
        default="",
        help="Path to the MRP stego PNG (optional; used for capacity sanity).",
    )
    ap.add_argument("--R", dest="R", default="mrp_lambda_R_payload.json", help="Path to R payload JSON.")
    ap.add_argument("--G", dest="G", default="mrp_lambda_G_payload.json", help="Path to G payload JSON.")
    ap.add_argument("--B", dest="B", default="mrp_lambda_B_payload.json", help="Path to B payload JSON.")
    ap.add_argument(
        "--sidecar",
        dest="sidecar",
        default="mrp_lambda_state_sidecar.json",
        help="Path to sidecar JSON (optional).",
    )
    ap.add_argument("--json", dest="json_out", default="", help="If set, write full report JSON to this path.")
    args = ap.parse_args()

    try:
        report = verify(args)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected failure: {e}", file=sys.stderr)
        sys.exit(1)

    # Pretty print summary
    print("=== MRP Phase‑A Verify ===")
    print(f"R crc32: {report['computed']['crc_r']}  (expect {report['expected_from_B']['crc_r']})")
    print(f"G crc32: {report['computed']['crc_g']}  (expect {report['expected_from_B']['crc_g']})")
    print(
        f"SHA256(R): {report['computed']['sha256_r_hex']}  (expect {report['expected_from_B']['sha256_msg']})"
    )
    print(f"Parity OK: {report['checks']['parity_block_ok']}  ECC scheme: {report['expected_from_B']['ecc_scheme']}")
    # Sidecar summaries if present
    if any(k.startswith("sidecar_") for k in report["checks"].keys()):
        print(
            "Sidecar checks:",
            f"sha_ok={report['checks'].get('sidecar_sha256_ok')}",
            f"used_bits_math_ok={report['checks'].get('sidecar_used_bits_math_ok')}",
            f"payload_len_ok={report['checks'].get('sidecar_payload_len_ok')}",
            f"capacity_ok={report['checks'].get('sidecar_capacity_bits_ok')}",
            f"hdr_magic_ok={report['checks'].get('sidecar_header_magic_ok')}",
            f"hdr_flags_crc_ok={report['checks'].get('sidecar_header_flags_crc_ok')}",
            sep="  ",
        )

    print(f"MRP: {'PASS' if report['mrp_ok'] else 'FAIL'}")

    if args.json_out:
        try:
            Path(args.json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2))
            print(f"[saved] {args.json_out}")
        except Exception as e:
            print(f"[WARN] Could not write JSON report: {e}", file=sys.stderr)

    sys.exit(0 if report["mrp_ok"] else 1)


if __name__ == "__main__":
    main()
