import numpy as np
from src.g2v.fft_codec import fft_encode, ifft_decode

def test_fft_roundtrip():
    g = np.zeros((16, 16))
    g[4:12, 4:12] = 1.0
    r = ifft_decode(fft_encode(g))
    assert np.mean((g - r)**2) < 1e-10

