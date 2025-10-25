# Auto-generated MRP Phase A stubs — 2025-10-13T05:14:22.138385Z
# SPDX-License-Identifier: MIT

#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
from src.mrp.codec import decode

def main():
    ap = argparse.ArgumentParser(description="Verify MRP frames in a stego PNG (Phase A).")
    ap.add_argument("stego", help="Path to stego PNG")
    ap.add_argument("--json", help="Write verification JSON to path", default=None)
    args = ap.parse_args()
    try:
        msg, meta, ecc = decode(args.stego)
    except NotImplementedError as e:
        print("Adapter not implemented:", e)
        sys.exit(3)
    out = {"message": msg, "metadata": meta, "ecc_report": ecc}
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2))
        print(f"Wrote {args.json}")
    else:
        print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
