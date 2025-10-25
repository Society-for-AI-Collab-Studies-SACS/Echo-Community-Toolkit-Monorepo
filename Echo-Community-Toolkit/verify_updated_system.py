#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, numpy as np
from src.lsb_extractor import LSBExtractor
from src.mrp.codec import encode, decode, encode_with_mode
from src.g2v.volume import glyph_from_tink_token
from src.g2v.fft_codec import fft_encode, ifft_decode

ROOT = Path(__file__).resolve().parent

def main():
    lsb = LSBExtractor().extract_from_image(ROOT / "assets/images/echo_key.png")
    msg, meta, ecc = encode_and_decode()
    g = glyph_from_tink_token("I-Glyph", 32)
    mse = float(np.mean((g - ifft_decode(fft_encode(g)))**2))
    mode_results = verify_mrp_modes()
    print(json.dumps({"lsb": lsb, "mrp": {"ecc": ecc, "modes": mode_results}, "g2v": {"mse": mse}}, indent=2))

def encode_and_decode():
    cover = ROOT / "assets/images/mrp_cover_stub.png"
    out = ROOT / "artifacts/mrp_stego_out.png"
    out.parent.mkdir(exist_ok=True)
    info = encode(str(cover), str(out), "Hello, Garden.", {"tool": "echo-mrp", "phase": "A"})
    d = decode(str(out))
    return d


def verify_mrp_modes():
    """Run experimental encoding modes through encode/decode cycle."""
    modes = ["phaseA", "sigprint", "entropic"]
    test_msg = "Echo-Community-Toolkit integration test"
    cover = ROOT / "assets/images/echo_key.png"
    tmp_dir = ROOT / "artifacts" / "mode_tests"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for mode in modes:
        entry = {"mode": mode}
        try:
            out_path = tmp_dir / f"mrp_test_{mode}.png"
            meta = {"tool": "verify", "phase": "test", "mode": mode}
            encode_with_mode(str(cover), str(out_path), test_msg, dict(meta), mode=mode)
            decoded_msg, decoded_meta, ecc = decode(str(out_path))
            entry.update({
                "crc_match": bool(ecc.get("crc_match")),
                "length_match": len(decoded_msg) == len(test_msg),
                "ecc_scheme": ecc.get("ecc_scheme"),
                "decoded_snippet": decoded_msg[:50],
            })
        except NotImplementedError:
            entry["status"] = "skipped (not implemented)"
        except Exception as exc:
            entry["error"] = str(exc)
        results.append(entry)
    return results

if __name__ == "__main__":
    main()
