#!/usr/bin/env python3
from src.mrp.codec import encode, decode

info = encode("assets/images/mrp_cover_stub.png", "assets/images/mrp_stego_out.png", "Hello", {"phase": "A"})
print("Encoded:", info)
print("Decoded:", decode("assets/images/mrp_stego_out.png"))

