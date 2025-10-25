# Phase‑A ECC scaffold (no-op parity)
def parity_hex(b: bytes) -> str:
    x = 0
    for v in b:
        x ^= v
    return f"{x:02X}"

def encode_ecc(payload: bytes) -> bytes:
    # Hook for future ECC; Phase‑A returns payload unchanged
    return payload

def decode_ecc(payload: bytes) -> tuple[bytes, dict]:
    return payload, {"ecc_scheme": "none"}

