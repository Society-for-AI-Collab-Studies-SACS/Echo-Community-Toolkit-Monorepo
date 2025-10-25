#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, json, sys
from pathlib import Path
from typing import Tuple


def _ensure_on_sys_path(root: Path) -> None:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _ensure_cover(cover: Path) -> None:
    if cover.exists():
        return
    from PIL import Image, ImageDraw

    cover.parent.mkdir(parents=True, exist_ok=True)
    w = h = 256
    img = Image.new("RGB", (w, h))
    for y in range(h):
        for x in range(w):
            img.putpixel((x, y), (x % 256, y % 256, (x ^ y) % 256))
    ImageDraw.Draw(img).rectangle([0, 0, w - 1, h - 1], outline=(0, 0, 0))
    img.save(cover, "PNG")


def _load_message(root: Path, source: str) -> Tuple[str, str]:
    # Returns (message_text, source_used)
    data_dir = root / "assets" / "data"
    if source in {"auto", "json"}:
        js_p = data_dir / "echo_key_decoded.json"
        if js_p.exists():
            js = json.loads(js_p.read_text())
            b64 = js.get("base64_payload", "")
            if b64:
                try:
                    text = base64.b64decode(b64.encode()).decode("utf-8")
                    return text, "json"
                except Exception:
                    pass
    # fallback to text file
    txt_p = data_dir / "LSB1_Mantra.txt"
    text = txt_p.read_text() if txt_p.exists() else ""
    return text, "text"


def main(argv=None) -> None:
    here = Path(__file__).resolve()
    root = here.parents[1]
    _ensure_on_sys_path(root)

    from src.lsb_encoder_decoder import LSBCodec

    ap = argparse.ArgumentParser("embed_golden_echo_key")
    ap.add_argument("--cover", default=str(root / "assets" / "images" / "echo_key.png"))
    ap.add_argument("--out", default=str(root / "assets" / "images" / "echo_key.png"))
    ap.add_argument("--message-source", choices=["auto", "json", "text"], default="auto")
    args = ap.parse_args(argv)

    cover = Path(args.cover)
    out = Path(args.out)
    _ensure_cover(cover)
    message, source_used = _load_message(root, args.message_source)
    if not message:
        raise SystemExit("No message text available")

    info = LSBCodec().encode_message(str(cover), message, str(out), use_crc=True)
    print(json.dumps({
        "op": "embed_golden_echo_key",
        "cover": str(cover),
        "out": str(out),
        "message_source": source_used,
        **info,
    }, indent=2))


if __name__ == "__main__":
    main()

