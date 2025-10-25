import numpy as np

from g2v.fft_codec import fft_encode, ifft_decode


def test_fft_roundtrip():
    g = np.zeros((16, 16))
    g[4:12, 4:12] = 1.0
    F = fft_encode(g)
    r = ifft_decode(F)
    # Round‑trip tolerates tiny numeric differences
    assert np.mean((g - r) ** 2) < 1e-10