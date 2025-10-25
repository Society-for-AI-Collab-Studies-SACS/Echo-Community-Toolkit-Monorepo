#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from g2v.volume import build_volume_stack, retrieve_layer, angular_projection
from g2v.fft_codec import fft_encode, ifft_decode

def main() -> None:
    square = np.zeros((16, 16)); square[4:12, 4:12] = 1
    bar = np.zeros((16, 16)); bar[7:9, :] = 1
    V = build_volume_stack([square, bar])
    assert V.shape == (16, 16, 2)
    assert np.allclose(retrieve_layer(V, 0), square)
    proj = angular_projection(V, 30, 'x')
    assert proj.shape == (16, 16)
    spec = fft_encode(square)
    rec = ifft_decode(spec)
    assert float(np.mean((square - rec)**2)) < 1e-10
    print('g2v minimal checks: OK')

if __name__ == '__main__':
    main()

