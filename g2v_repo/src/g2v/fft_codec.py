from __future__ import annotations

import numpy as np


def fft_encode(img: np.ndarray) -> np.ndarray:
    """Return the centered 2‑D FFT of a real image as complex64/128.

    The input is converted to float64; output uses complex128 for precision.
    """
    a = np.asarray(img, dtype=np.float64)
    F = np.fft.fftshift(np.fft.fft2(a))
    return F


def ifft_decode(F: np.ndarray) -> np.ndarray:
    """Inverse of :func:`fft_encode`, returning the real part of the image."""
    Fc = np.asarray(F)
    a = np.fft.ifft2(np.fft.ifftshift(Fc))
    return np.real(a)

