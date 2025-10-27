#!/usr/bin/env python3
from __future__ import annotations
import json
import base64
from pathlib import Path
from typing import Any, Dict
def _ensure_cover(cover: Path) -> None:
    if cover.exists():
        return
    from PIL import Image, ImageDraw
    cover.parent.mkdir(parents=True, exist_ok=True)
    w = h = 256
    img = Image.new("RGB", (w, h), "white")
    dr = ImageDraw.Draw(img)
    for y in range(0, h, 16):
        for x in range(0, w, 16):
            if (x // 16 + y // 16) % 2 == 0:
                dr.rectangle([x, y, x + 15, y + 15], fill=(200, 200, 200))
    img.save(cover, "PNG")


def _minified_json_bytes(p: Path) -> bytes:
    obj = json.loads(p.read_text())
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode()


def main() -> None:
    import sys
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    # Deferred imports (repo-local modules)
    from src.mrp.frame import make_frame, parse_frame
    from src.mrp.meta import sidecar_from_frames
    from src.mrp.adapters import png_lsb

    cover = root / "assets" / "images" / "mrp_cover_stub.png"
    _ensure_cover(cover)
    out = root / "artifacts" / "mrp_rgb_validate.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    r_payload = base64.b64encode(
        _minified_json_bytes(root / "assets" / "data" / "mrp_lambda_R_payload.json")
    )
    g_payload = base64.b64encode(
        _minified_json_bytes(root / "assets" / "data" / "mrp_lambda_G_payload.json")
    )

    r = make_frame("R", r_payload, True)
    g = make_frame("G", g_payload, True)
    sidecar = sidecar_from_frames(parse_frame(r), parse_frame(g))
    b_payload = json.dumps(sidecar, separators=(",", ":"), sort_keys=True).encode()
    b = make_frame("B", b_payload, True)

    png_lsb.embed_frames(str(cover), str(out), {"R": r, "G": g, "B": b})

    frames = png_lsb.extract_frames(str(out))
    R = parse_frame(frames["R"])
    G = parse_frame(frames["G"])
    B = parse_frame(frames["B"])

    r_ok = R.payload == r_payload
    g_ok = G.payload == g_payload
    b_obj = json.loads(B.payload.decode("utf-8"))
    ecc = {
        "crc_match": (
            b_obj.get("crc_r") == f"{R.crc32:08X}"
            and b_obj.get("crc_g") == f"{G.crc32:08X}"
        ),
        "parity_present": bool(b_obj.get("parity")),
        "ecc_scheme": b_obj.get("ecc_scheme"),
    }

    print(json.dumps({
        "op": "mrp_validate_rgb",
        "out": str(out),
        "r_ok": r_ok,
        "g_ok": g_ok,
        "ecc": ecc,
    }, indent=2))


if __name__ == "__main__":
    main()
