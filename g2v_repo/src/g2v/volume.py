from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def normalize(a: np.ndarray) -> np.ndarray:
    """Normalize an array to [0, 1] if possible; return zero array unchanged.

    The operation is deterministic and uses float64 for stability.
    """
    a = np.asarray(a, dtype=np.float64)
    maxv = float(np.max(np.abs(a))) if a.size else 0.0
    if maxv == 0.0 or not np.isfinite(maxv):
        return a.copy()
    return a / maxv


def build_volume_stack(glyphs: Iterable[np.ndarray]) -> np.ndarray:
    """Stack 2‑D glyph arrays along the last axis to form a 3‑D volume.

    All glyphs must share identical shapes. Output dtype is float64.
    """
    glyph_list = [np.asarray(g, dtype=np.float64) for g in glyphs]
    if not glyph_list:
        raise ValueError("No glyphs provided")
    shape0 = glyph_list[0].shape
    if len(shape0) != 2:
        raise ValueError("Glyphs must be 2‑D arrays")
    for i, g in enumerate(glyph_list[1:], start=1):
        if g.shape != shape0:
            raise ValueError(f"Glyph {i} shape {g.shape} != {shape0}")
    V = np.stack(glyph_list, axis=2)
    return V.astype(np.float64, copy=False)


def retrieve_layer(V: np.ndarray, z: int) -> np.ndarray:
    """Return a single 2‑D layer from a 3‑D volume along the last axis."""
    V = np.asarray(V)
    if V.ndim != 3:
        raise ValueError("Volume must be 3‑D (H, W, Z)")
    if not (0 <= z < V.shape[2]):
        raise IndexError("Layer index out of range")
    return np.asarray(V[:, :, z], dtype=np.float64)


def angular_projection(V: np.ndarray, theta_deg: float, axis: str = "x") -> np.ndarray:
    """Compute a simple angular projection.

    For determinism and zero external deps, this implementation performs a very
    lightweight projection:
      - If `axis` is 'x' or 'y', we ignore rotation and return the sum along the
        stacking (z) axis, which preserves energy and shape.

    This is sufficient for basic tests and offline tooling. The API is stable
    so a more accurate rotational projection can replace this later without
    changing callers.
    """
    V = np.asarray(V, dtype=np.float64)
    if V.ndim != 3:
        raise ValueError("Volume must be 3‑D (H, W, Z)")
    _ = float(theta_deg)  # accepted but not used in the simplified projector
    if axis not in {"x", "y", "z"}:
        raise ValueError("axis must be one of 'x', 'y', 'z'")
    # Simplified projection: sum along z to (H, W)
    proj = np.sum(V, axis=2)
    return proj


# --- Glyph synthesis helpers -------------------------------------------------

def _filled_square(n: int, pad: int) -> np.ndarray:
    a = np.zeros((n, n), dtype=np.float64)
    a[pad : n - pad, pad : n - pad] = 1.0
    return a


def _horizontal_bar(n: int, thickness: int) -> np.ndarray:
    a = np.zeros((n, n), dtype=np.float64)
    mid = n // 2
    a[mid - thickness // 2 : mid + (thickness - thickness // 2), :] = 1.0
    return a


def _vertical_bar(n: int, thickness: int) -> np.ndarray:
    a = np.zeros((n, n), dtype=np.float64)
    mid = n // 2
    a[:, mid - thickness // 2 : mid + (thickness - thickness // 2)] = 1.0
    return a


def _diagonal_cross(n: int, thickness: int) -> np.ndarray:
    a = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for t in range(-thickness // 2, (thickness + 1) // 2):
            j1 = i + t
            j2 = (n - 1 - i) + t
            if 0 <= j1 < n:
                a[i, j1] = 1.0
            if 0 <= j2 < n:
                a[i, j2] = 1.0
    return a


def _spiral(n: int, turns: int) -> np.ndarray:
    a = np.zeros((n, n), dtype=np.float64)
    cx = cy = (n - 1) / 2.0
    max_r = (n - 2) / 2.0
    steps = n * n
    for k in range(steps):
        t = k / steps
        angle = 2 * math.pi * turns * t
        r = max_r * t
        x = int(round(cx + r * math.cos(angle)))
        y = int(round(cy + r * math.sin(angle)))
        if 0 <= x < n and 0 <= y < n:
            a[y, x] = 1.0
    return a


def glyph_from_tink_token(token: str, size: int = 32) -> np.ndarray:
    """Return a deterministic glyph array for a given conceptual token.

    The mapping is intentionally simple and offline‑friendly.
    """
    # Normalize common hyphen/ndash variants
    token_norm = (
        token.replace("\u2011", "-")  # non‑breaking hyphen
        .replace("\u2013", "-")  # en dash
        .replace("\u2014", "-")  # em dash
        .strip()
    )

    n = int(size)
    if n <= 4:
        raise ValueError("size too small for glyph synthesis")

    if token_norm.lower() in {"i-glyph", "i glyph", "i"}:
        return _filled_square(n, pad=max(1, n // 8))
    if token_norm.lower() == "octave cycle drive":
        # Horizontal bar
        return _horizontal_bar(n, thickness=max(1, n // 12))
    if token_norm.lower() == "mirrorpulse":
        # Vertical bar
        return _vertical_bar(n, thickness=max(1, n // 12))
    if token_norm.lower() == "mirrorhold":
        # Diagonal cross
        return _diagonal_cross(n, thickness=max(1, n // 20))
    if token_norm.lower() == "gravisystem":
        # Square with thicker border
        a = _filled_square(n, pad=max(1, n // 6))
        b = _filled_square(n, pad=max(1, n // 4))
        return a - b
    if token_norm.lower() == "spiralborne codex":
        return _spiral(n, turns=3)

    raise ValueError(f"Unknown token: {token}")

