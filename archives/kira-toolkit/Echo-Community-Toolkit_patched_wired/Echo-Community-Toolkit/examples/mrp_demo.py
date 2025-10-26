# Auto-generated MRP Phase A stubs — 2025-10-13T05:14:22.138385Z
# SPDX-License-Identifier: MIT

#!/usr/bin/env python3
"""Minimal MRP Phase A demo (codec only; adapter is stubbed).
"""
import json, sys
from src.mrp.codec import encode, decode

def main():
    if len(sys.argv) < 3:
        print("Usage: python examples/mrp_demo.py <cover.png> <out.png>")
        print("NOTE: Adapter is a stub; this will raise NotImplementedError until implemented.")
        sys.exit(2)
    cover, outp = sys.argv[1], sys.argv[2]
    meta = {"tool": "echo-mrp", "phase": "A", "ts": "now"}
    try:
        info = encode(cover, outp, "Hello, Garden.", meta)
        print("Encoded:", json.dumps(info, indent=2))
    except NotImplementedError as e:
        print("Adapter not implemented:", e)
        sys.exit(3)

if __name__ == "__main__":
    main()
