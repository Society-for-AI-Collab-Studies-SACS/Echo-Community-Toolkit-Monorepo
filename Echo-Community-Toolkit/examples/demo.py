#!/usr/bin/env python3
from pathlib import Path
from src.lsb_encoder_decoder import LSBCodec
from src.lsb_extractor import LSBExtractor

codec = LSBCodec(1)
cover = codec.create_cover_image(300, 200, "texture")
cover_p = Path("demo_cover.png")
cover.save(cover_p, "PNG")
res = codec.encode_message(cover_p, "Welcome to Echo-Limnus!", "demo_stego.png", True)
decoded = LSBExtractor().extract_from_image("demo_stego.png")
print("Encoded:", res)
print("Decoded:", decoded)

