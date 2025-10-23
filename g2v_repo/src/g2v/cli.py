from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import numpy as np

from .volume import (
    build_volume_stack,
    retrieve_layer,
    angular_projection,
    glyph_from_tink_token,
)
from .fft_codec import fft_encode, ifft_decode


def _save_npy(path: Path, arr: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, arr)
    return str(path)


def cmd_stack(args: argparse.Namespace) -> dict:
    glyphs = [np.load(p) for p in args.glyphs]
    V = build_volume_stack(glyphs)
    out = Path(args.out)
    path = _save_npy(out, V)
    return {"op": "stack", "out": path, "shape": list(V.shape)}


def cmd_slice(args: argparse.Namespace) -> dict:
    V = np.load(args.volume)
    layer = retrieve_layer(V, int(args.z))
    out = Path(args.out)
    path = _save_npy(out, layer)
    return {"op": "slice", "out": path, "z": int(args.z), "shape": list(layer.shape)}


def cmd_project(args: argparse.Namespace) -> dict:
    V = np.load(args.volume)
    proj = angular_projection(V, float(args.theta), axis=args.axis)
    out = Path(args.out)
    path = _save_npy(out, proj)
    return {
        "op": "project",
        "out": path,
        "theta": float(args.theta),
        "axis": args.axis,
        "shape": list(proj.shape),
    }


def cmd_fft(args: argparse.Namespace) -> dict:
    g = np.load(args.glyph)
    F = fft_encode(g)
    recon = ifft_decode(F)
    out_spec = Path(args.out_spec)
    out_recon = Path(args.out_recon)
    spec_path = _save_npy(out_spec, F)
    recon_path = _save_npy(out_recon, recon)
    return {
        "op": "fft",
        "out_spec": spec_path,
        "out_recon": recon_path,
        "glyph_shape": list(np.asarray(g).shape),
    }


def cmd_glyph(args: argparse.Namespace) -> dict:
    g = glyph_from_tink_token(args.token, size=int(args.size))
    out = Path(args.out)
    path = _save_npy(out, g)
    return {"op": "glyph", "token": args.token, "size": int(args.size), "out": path}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="g2v", description="Glyph‑to‑Volume toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_stack = sub.add_parser("stack", help="Stack glyphs into a volume")
    p_stack.add_argument("--out", required=True, help="Output .npy volume path")
    p_stack.add_argument("glyphs", nargs="+", help="Input glyph .npy paths")
    p_stack.set_default(func=cmd_stack)

    p_slice = sub.add_parser("slice", help="Extract a layer from a volume")
    p_slice.add_argument("volume", help="Input volume .npy path")
    p_slice.add_argument("--z", required=True, type=int, help="Layer index (0‑based)")
    p_slice.add_argument("--out", required=True, help="Output .npy path")
    p_slice.set_default(func=cmd_slice)

    p_proj = sub.add_parser("project", help="Project a volume through an angle")
    p_proj.add_argument("volume", help="Input volume .npy path")
    p_proj.add_argument("--theta", required=True, type=float, help="Angle in degrees")
    p_proj.add_argument("--axis", default="x", choices=["x", "y", "z"], help="Axis")
    p_proj.add_argument("--out", required=True, help="Output .npy path")
    p_proj.set_default(func=cmd_project)

    p_fft = sub.add_parser("fft", help="FFT round‑trip for a glyph")
    p_fft.add_argument("glyph", help="Input glyph .npy path")
    p_fft.add_argument("--out-recon", required=True, dest="out_recon", help="Reconstruction .npy")
    p_fft.add_argument("--out-spec", required=True, dest="out_spec", help="Spectrum .npy")
    p_fft.set_default(func=cmd_fft)

    p_glyph = sub.add_parser("glyph", help="Generate a glyph array by token")
    p_glyph.add_argument("--token", required=True, help="Glyph token name")
    p_glyph.add_argument("--size", default=32, type=int, help="Glyph size (pixels)")
    p_glyph.add_argument("--out", required=True, help="Output .npy path")
    p_glyph.set_default(func=cmd_glyph)

    return p


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":  # pragma: no cover
    main()
