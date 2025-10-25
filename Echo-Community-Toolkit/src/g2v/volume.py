from __future__ import annotations
import numpy as np, math

def build_volume_stack(glyphs):
    return np.stack([np.asarray(g, float) for g in glyphs], axis=2)

def retrieve_layer(V, z):
    return np.asarray(V[:, :, int(z)], float)

def angular_projection(V, theta_deg: float, axis="x"):
    return np.sum(np.asarray(V, float), axis=2)

def normalize(a) -> np.ndarray:
    a = np.asarray(a, float)
    mn = float(a.min()) if a.size else 0.0
    mx = float(a.max()) if a.size else 0.0
    rng = mx - mn
    if rng == 0:
        return a
    return (a - mn) / rng

def glyph_from_tink_token(token: str, size: int = 32) -> np.ndarray:
    n = int(size)
    a = np.zeros((n, n), float)
    t = token.lower().strip()
    if t in {"i-glyph", "i"}:
        a[n//8:n-n//8, n//8:n-n//8] = 1
        return a
    if t == "octave cycle drive":
        a[n//2-1:n//2+1, :] = 1
        return a
    if t == "mirrorpulse":
        a[:, n//2-1:n//2+1] = 1
        return a
    if t == "mirrorhold":
        a[n//2-1:n//2+1, :] = 1
        a[:, n//2-1:n//2+1] = 1
        return a
    if t == "gravisystem":
        for i in range(n):
            a[i, i] = 1
            a[i, n-1-i] = 1
        return a
    if t == "spiralborne codex":
        for k in range(n * n):
            r = (k / (n * n)) * ((n-2) / 2)
            ang = 2 * math.pi * 3 * (k / (n * n))
            x = int(round((n-1)/2 + r * math.cos(ang)))
            y = int(round((n-1)/2 + r * math.sin(ang)))
            if 0 <= x < n and 0 <= y < n:
                a[y, x] = 1
        return a
    # unknown token
    raise ValueError(f"Unknown glyph token: {token}")
