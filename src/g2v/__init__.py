"""Glyph‑to‑Volume (g2v) core package.

Minimal, self‑contained implementation to support:
- Volume stack/slice/project helpers
- Simple FFT encode/decode
- CLI entry point (see g2v.cli)

Only depends on NumPy for offline, deterministic execution.
"""

from .volume import (  # noqa: F401
    build_volume_stack,
    retrieve_layer,
    angular_projection,
    normalize,
    glyph_from_tink_token,
)
from .fft_codec import fft_encode, ifft_decode  # noqa: F401

__all__ = [
    "build_volume_stack",
    "retrieve_layer",
    "angular_projection",
    "normalize",
    "glyph_from_tink_token",
    "fft_encode",
    "ifft_decode",
]

