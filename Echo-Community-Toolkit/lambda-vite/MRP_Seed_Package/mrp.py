
"""
MRP — Multi-Channel Resonance Protocol
R channel: primary message (UTF-8, base64-encoded)
G channel: metadata (UTF-8 JSON, base64-encoded)
B channel: ECC / integrity (JSON with CRCs, SHA256, and parity bytes; base64-encoded)

Each channel payload is wrapped in a compact header:
    magic: 4 bytes = b"MRP1"
    channel_id: 1 byte = ord('R'|'G'|'B')
    flags: 1 byte   = bit0: CRC32 present over payload bytes
    length: 4 bytes = big-endian payload length (bytes)
    [crc32]: 4 bytes if flags & 0x01
    payload: <length> bytes (ASCII base64)

Bits are embedded/extracted from the LSB of a single color channel, MSB-first packing.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Any, Optional
import base64, zlib, json, hashlib, argparse, sys, os
import numpy as np
from PIL import Image

MAGIC = b"MRP1"
FLAG_CRC32 = 0x01

@dataclass
class ChannelPacket:
    channel_id: int   # 0=R,1=G,2=B
    payload: bytes    # raw payload (not base64 yet)
    as_text: bool = True  # whether to base64-decode as UTF-8 text on decode

def _bytes_to_bits(b: bytes):
    for byte in b:
        for s in range(7, -1, -1):
            yield (byte >> s) & 1

def _bits_to_bytes(bits: np.ndarray) -> bytes:
    # bits is 1D array of {0,1}
    n = (len(bits) // 8) * 8
    bits = bits[:n].reshape(-1, 8)
    weights = (1 << np.arange(7, -1, -1, dtype=np.uint8)).astype(np.uint16)
    packed = (bits * weights).sum(axis=1).astype(np.uint8)
    return bytes(packed)

def _build_header_payload(channel_char: str, payload_ascii: bytes, add_crc=True) -> bytes:
    flags = FLAG_CRC32 if add_crc else 0
    hdr = bytearray()
    hdr += MAGIC
    hdr += channel_char.encode('ascii')
    hdr.append(flags)
    hdr += len(payload_ascii).to_bytes(4, 'big')
    if add_crc:
        crc = zlib.crc32(payload_ascii) & 0xFFFFFFFF
        hdr += crc.to_bytes(4, 'big')
    return bytes(hdr) + payload_ascii

def _parse_header(data: bytes, expected_channel: str):
    # Find MAGIC
    idx = data.find(MAGIC)
    if idx == -1:
        raise ValueError("MRP header not found")
    p = idx + 4
    ch = chr(data[p]); p += 1
    if ch != expected_channel:
        raise ValueError(f"Unexpected channel {ch}, expected {expected_channel}")
    flags = data[p]; p += 1
    length = int.from_bytes(data[p:p+4], 'big'); p += 4
    crc_header = None
    if flags & FLAG_CRC32:
        crc_header = int.from_bytes(data[p:p+4], 'big')
        p += 4
    payload = data[p:p+length]
    if len(payload) != length:
        raise ValueError("Payload length mismatch")
    if flags & FLAG_CRC32:
        crc_calc = zlib.crc32(payload) & 0xFFFFFFFF
        if crc_calc != crc_header:
            raise ValueError(f"CRC mismatch: header={crc_header:08X} calc={crc_calc:08X}")
    return payload, flags

def _ensure_capacity(arr: np.ndarray, per_channel_bits_needed: Dict[int,int]):
    h,w,_ = arr.shape
    cap_bits = h*w
    for ch, bits_needed in per_channel_bits_needed.items():
        if bits_needed > cap_bits:
            raise ValueError(f"Not enough capacity on channel {ch}: need {bits_needed}, have {cap_bits}")

def _embed_bits_into_channel(arr: np.ndarray, ch: int, bits: np.ndarray):
    plane = arr[:,:,ch].ravel()
    if len(bits) > plane.size:
        raise ValueError("Insufficient capacity for bits")
    plane[:len(bits)] = (plane[:len(bits)] & 0xFE) | bits
    arr[:,:,ch] = plane.reshape(arr.shape[0], arr.shape[1])

def _extract_all_bits(arr: np.ndarray, ch: int) -> np.ndarray:
    plane = arr[:,:,ch].ravel()
    return (plane & 1).astype(np.uint8)

def _b64(s: bytes) -> bytes:
    return base64.b64encode(s)

def _b64d(s: bytes) -> bytes:
    return base64.b64decode(s, validate=True)

def _parity_bytes(data: bytes, block: int = 8) -> bytes:
    out = bytearray()
    for i in range(0, len(data), block):
        blk = data[i:i+block]
        p = 0
        for b in blk:
            p ^= b
        out.append(p)
    return bytes(out)

def encode_mrp(cover_image_path: str, out_path: str, message_text: str, metadata: Dict[str,Any]) -> Dict[str,Any]:
    im = Image.open(cover_image_path).convert("RGB")
    arr = np.array(im, dtype=np.uint8)

    # Build channel payloads
    msg_bytes = message_text.encode("utf-8")
    meta_bytes = json.dumps(metadata, ensure_ascii=False, separators=(",",":")).encode("utf-8")

    msg_b64 = _b64(msg_bytes)
    meta_b64 = _b64(meta_bytes)

    # ECC payload over base64 bodies
    # Phase‑A parity: XOR across R_b64 and G_b64 streams (length = len(G_b64))
    def phase_a_parity_b64(r_b64: bytes, g_b64: bytes) -> str:
        Lg, Lr = len(g_b64), len(r_b64)
        P = bytearray(Lg)
        for i in range(Lg):
            P[i] = (r_b64[i] ^ g_b64[i]) if i < Lr else g_b64[i]
        return base64.b64encode(bytes(P)).decode("ascii")

    ecc = {
        "crc_r": f"{(zlib.crc32(msg_b64)&0xFFFFFFFF):08X}",
        "crc_g": f"{(zlib.crc32(meta_b64)&0xFFFFFFFF):08X}",
        # Phase‑A spec variant: SHA‑256 over R_b64 (primary base64 body)
        "sha256_msg_b64": hashlib.sha256(msg_b64).hexdigest(),
        "ecc_scheme": "parity",
        "parity_block_b64": phase_a_parity_b64(msg_b64, meta_b64),
    }
    ecc_bytes = json.dumps(ecc, separators=(",",":")).encode("utf-8")
    ecc_b64 = _b64(ecc_bytes)

    # Build full channel frames
    r_frame = _build_header_payload('R', msg_b64, add_crc=True)
    g_frame = _build_header_payload('G', meta_b64, add_crc=True)
    b_frame = _build_header_payload('B', ecc_b64, add_crc=True)

    # Convert to bits
    def to_bits(b: bytes) -> np.ndarray:
        return np.fromiter(_bytes_to_bits(b), dtype=np.uint8, count=len(b)*8)

    r_bits = to_bits(r_frame)
    g_bits = to_bits(g_frame)
    b_bits = to_bits(b_frame)

    # Capacity check
    _ensure_capacity(arr, {0: len(r_bits), 1: len(g_bits), 2: len(b_bits)})

    # Embed
    _embed_bits_into_channel(arr, 0, r_bits)
    _embed_bits_into_channel(arr, 1, g_bits)
    _embed_bits_into_channel(arr, 2, b_bits)

    stego = Image.fromarray(arr, mode="RGB")
    stego.save(out_path, format="PNG", optimize=True)

    return {
        "cover": cover_image_path,
        "stego": out_path,
        "sizes_bits": {"R": int(len(r_bits)), "G": int(len(g_bits)), "B": int(len(b_bits))},
        "payload_lengths": {"R": len(msg_b64), "G": len(meta_b64), "B": len(ecc_b64)},
        "ecc": ecc,
    }

def decode_mrp(stego_image_path: str) -> Dict[str,Any]:
    im = Image.open(stego_image_path).convert("RGB")
    arr = np.array(im, dtype=np.uint8)

    # Extract per-channel bitstreams → bytes
    r_bits = _extract_all_bits(arr, 0); r_bytes = _bits_to_bytes(r_bits)
    g_bits = _extract_all_bits(arr, 1); g_bytes = _bits_to_bytes(g_bits)
    b_bits = _extract_all_bits(arr, 2); b_bytes = _bits_to_bytes(b_bits)

    # Parse headers + payloads
    r_payload_b64, _ = _parse_header(r_bytes, 'R')
    g_payload_b64, _ = _parse_header(g_bytes, 'G')
    b_payload_b64, _ = _parse_header(b_bytes, 'B')

    # Decode
    msg_bytes = base64.b64decode(r_payload_b64, validate=True)
    meta_bytes = base64.b64decode(g_payload_b64, validate=True)
    ecc_bytes  = base64.b64decode(b_payload_b64, validate=True)

    message = msg_bytes.decode("utf-8", "replace")
    metadata = json.loads(meta_bytes.decode("utf-8", "replace"))
    ecc = json.loads(ecc_bytes.decode("utf-8", "replace"))

    # Verify ECC
    crc_r_calc = f"{(zlib.crc32(r_payload_b64)&0xFFFFFFFF):08X}"
    crc_g_calc = f"{(zlib.crc32(g_payload_b64)&0xFFFFFFFF):08X}"
    sha_calc = hashlib.sha256(msg_bytes).hexdigest()

    # Phase‑A parity recompute (XOR across R_b64 and G_b64)
    def _phase_a_parity(r_b64: bytes, g_b64: bytes) -> bytes:
        Lg, Lr = len(g_b64), len(r_b64)
        P = bytearray(Lg)
        for i in range(Lg):
            P[i] = (r_b64[i] ^ g_b64[i]) if i < Lr else g_b64[i]
        return bytes(P)

    parity_rg_b64 = ecc.get("parity_block_b64", "")
    try:
        parity_rg = base64.b64decode(parity_rg_b64, validate=True)
    except Exception:
        parity_rg = b""
    parity_calc = _phase_a_parity(r_payload_b64, g_payload_b64)
    parity_match = (parity_rg == parity_calc)

    report = {
        "image": stego_image_path,
        "width": im.width,
        "height": im.height,
        # Backward compatibility: check SHA256 over decoded message bytes if present
        "message_sha256_ok": (sha_calc == ecc.get("sha256_msg")) if ("sha256_msg" in ecc) else None,
        # Phase‑A: expected SHA over R_b64
        "sha256_r_b64_ok": (hashlib.sha256(r_payload_b64).hexdigest() == ecc.get("sha256_msg_b64")),
        "crc_r_ok": (crc_r_calc == ecc.get("crc_r")),
        "crc_g_ok": (crc_g_calc == ecc.get("crc_g")),
        "parity_ok": parity_match,
        "crc_r_calc": crc_r_calc,
        "crc_g_calc": crc_g_calc,
        "sha256_calc": sha_calc,
        "ecc_header": ecc,
        "metadata": metadata,
    }
    return {"message": message, "metadata": metadata, "ecc": ecc, "report": report}


# -----------------------------
# Tiny CLI for encode/decode
# -----------------------------

def _load_metadata(meta_str: Optional[str], meta_file: Optional[str]) -> Dict[str, Any]:
    if meta_str:
        return json.loads(meta_str)
    if meta_file:
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    ap = argparse.ArgumentParser(description="MRP Phase-A encoder/decoder (LSB, RGB channels)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ep = sub.add_parser("encode", help="Embed message+metadata into cover PNG via RGB-LSB")
    ep.add_argument("--cover", required=True, help="Path to input cover PNG")
    ep.add_argument("--out", required=True, help="Path to output stego PNG")
    mg = ep.add_mutually_exclusive_group(required=True)
    mg.add_argument("--message", help="Message text (UTF-8)")
    mg.add_argument("--message-file", help="Path to a UTF-8 text file for message")
    ep.add_argument("--metadata", help="Metadata JSON string")
    ep.add_argument("--metadata-file", help="Path to metadata JSON file")
    ep.add_argument("--report", help="If set, write encode summary JSON to this path")

    dp = sub.add_parser("decode", help="Extract and verify MRP payloads from stego PNG")
    dp.add_argument("--image", required=True, help="Path to stego PNG")
    dp.add_argument("--json", help="If set, write full decode report JSON to this path")
    dp.add_argument("--message-out", help="If set, write decoded message to this file (UTF-8)")
    dp.add_argument("--metadata-out", help="If set, write decoded metadata JSON to this file")

    args = ap.parse_args()

    if args.cmd == "encode":
        if not os.path.exists(args.cover):
            ap.error(f"Cover not found: {args.cover}")
        if args.message_file:
            with open(args.message_file, "r", encoding="utf-8") as f:
                message_text = f.read()
        else:
            message_text = args.message or ""
        metadata = _load_metadata(args.metadata, args.metadata_file)
        try:
            info = encode_mrp(args.cover, args.out, message_text, metadata)
        except Exception as e:
            print(f"[ERROR] encode failed: {e}", file=sys.stderr)
            sys.exit(1)
        print("=== MRP Encode ===")
        print(f"cover: {info['cover']}")
        print(f"stego: {info['stego']}")
        print(f"sizes_bits: {info['sizes_bits']}")
        if args.report:
            try:
                with open(args.report, "w", encoding="utf-8") as f:
                    json.dump(info, f, ensure_ascii=False, indent=2)
                print(f"[saved] {args.report}")
            except Exception as e:
                print(f"[WARN] could not save report: {e}", file=sys.stderr)
        sys.exit(0)

    if args.cmd == "decode":
        if not os.path.exists(args.image):
            ap.error(f"Image not found: {args.image}")
        try:
            res = decode_mrp(args.image)
        except Exception as e:
            print(f"[ERROR] decode failed: {e}", file=sys.stderr)
            sys.exit(1)
        print("=== MRP Decode ===")
        print(f"message (preview): {res['message'][:80]}{'...' if len(res['message'])>80 else ''}")
        print(f"crc_r_ok={res['report'].get('crc_r_ok')}  crc_g_ok={res['report'].get('crc_g_ok')}  "
              f"sha256_r_b64_ok={res['report'].get('sha256_r_b64_ok')}  parity_ok={res['report'].get('parity_ok')}")
        if args.message_out:
            try:
                with open(args.message_out, "w", encoding="utf-8") as f:
                    f.write(res["message"]) 
                print(f"[saved] {args.message_out}")
            except Exception as e:
                print(f"[WARN] could not save message: {e}", file=sys.stderr)
        if args.metadata_out:
            try:
                with open(args.metadata_out, "w", encoding="utf-8") as f:
                    json.dump(res["metadata"], f, ensure_ascii=False, indent=2)
                print(f"[saved] {args.metadata_out}")
            except Exception as e:
                print(f"[WARN] could not save metadata: {e}", file=sys.stderr)
        if args.json:
            try:
                with open(args.json, "w", encoding="utf-8") as f:
                    json.dump(res, f, ensure_ascii=False, indent=2)
                print(f"[saved] {args.json}")
            except Exception as e:
                print(f"[WARN] could not save JSON: {e}", file=sys.stderr)
        # Exit 0 even if some checks failed; callers can inspect the JSON/report
        sys.exit(0)


if __name__ == "__main__":
    main()
