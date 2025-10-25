from pathlib import Path
from src.lsb_encoder_decoder import LSBCodec
from src.lsb_extractor import LSBExtractor

def test_round_trip():
    c = LSBCodec()
    cover = c.create_cover_image(64, 64)
    p = Path("rt_cover.png")
    cover.save(p, "PNG")
    res = c.encode_message(p, "abc", "rt_stego.png", True)
    out = LSBExtractor().extract_from_image("rt_stego.png")
    assert out["magic"] == "LSB1" and out["payload_length"] >= 3

