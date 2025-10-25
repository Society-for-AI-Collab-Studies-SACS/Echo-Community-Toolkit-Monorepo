from __future__ import annotations
import argparse, json, numpy as np
from pathlib import Path
from .volume import build_volume_stack, retrieve_layer, angular_projection, glyph_from_tink_token
from .fft_codec import fft_encode, ifft_decode

def _save(p: Path, arr):
    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(p, arr)
    return str(p)

def main(argv=None):
    p = argparse.ArgumentParser("g2v")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("glyph")
    s.add_argument("--token", required=True)
    s.add_argument("--size", type=int, default=32)
    s.add_argument("--out", required=True)
    s = sub.add_parser("stack")
    s.add_argument("--out", required=True)
    s.add_argument("glyphs", nargs="+")
    s = sub.add_parser("slice")
    s.add_argument("volume")
    s.add_argument("--z", type=int, required=True)
    s.add_argument("--out", required=True)
    s = sub.add_parser("project")
    s.add_argument("volume")
    s.add_argument("--theta", type=float, required=True)
    s.add_argument("--axis", default="x")
    s.add_argument("--out", required=True)
    s = sub.add_parser("fft")
    s.add_argument("glyph")
    s.add_argument("--out-recon", required=True)
    s.add_argument("--out-spec", required=True)
    a = p.parse_args(argv)
    if a.cmd == "glyph":
        print(json.dumps({"op": "glyph", "out": _save(Path(a.out), glyph_from_tink_token(a.token, a.size))}))
    if a.cmd == "stack":
        print(json.dumps({"op": "stack", "out": _save(Path(a.out), build_volume_stack([np.load(g) for g in a.glyphs]))}))
    if a.cmd == "slice":
        print(json.dumps({"op": "slice", "out": _save(Path(a.out), retrieve_layer(np.load(a.volume), a.z))}))
    if a.cmd == "project":
        print(json.dumps({"op": "project", "out": _save(Path(a.out), angular_projection(np.load(a.volume), a.theta, a.axis))}))
    if a.cmd == "fft":
        g = np.load(a.glyph)
        spec = _save(Path(a.out_spec), fft_encode(g))
        rec = _save(Path(a.out_recon), ifft_decode(np.load(a.out_spec)))
        print(json.dumps({"op": "fft", "out_spec": spec, "out_recon": rec}))

if __name__ == "__main__":
    main()

