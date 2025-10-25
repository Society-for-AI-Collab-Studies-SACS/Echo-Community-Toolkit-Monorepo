# Echo-Community-Toolkit — G2V (Glyph-to-Volume) Scaffold

Copy-paste ready snippets for the refreshed G2V toolkit. The modules now expose
typed helpers, a CLI with subcommands, and richer glyph synthesis utilities.

## Modules

### `src/g2v/volume.py`
```python
from __future__ import annotations

import math
from typing import Iterable

import numpy as np

def normalize(a: np.ndarray) -> np.ndarray:
    arr = np.asarray(a, dtype=np.float64)
    maxv = float(np.max(np.abs(arr))) if arr.size else 0.0
    if maxv == 0.0 or not np.isfinite(maxv):
        return arr.copy()
    return arr / maxv

def build_volume_stack(glyphs: Iterable[np.ndarray]) -> np.ndarray:
    glyph_list = [np.asarray(g, dtype=np.float64) for g in glyphs]
    if not glyph_list:
        raise ValueError("No glyphs provided")
    shape0 = glyph_list[0].shape
    for idx, glyph in enumerate(glyph_list[1:], start=1):
        if glyph.shape != shape0:
            raise ValueError(f"Glyph {idx} shape {glyph.shape} != {shape0}")
    return np.stack(glyph_list, axis=2).astype(np.float64, copy=False)

def retrieve_layer(volume: np.ndarray, z: int) -> np.ndarray:
    arr = np.asarray(volume)
    if arr.ndim != 3:
        raise ValueError("Volume must be 3-D (H, W, Z)")
    if not (0 <= z < arr.shape[2]):
        raise IndexError("Layer index out of range")
    return np.asarray(arr[:, :, z], dtype=np.float64)

def angular_projection(volume: np.ndarray, theta_deg: float, axis: str = "x") -> np.ndarray:
    arr = np.asarray(volume, dtype=np.float64)
    if arr.ndim != 3:
        raise ValueError("Volume must be 3-D (H, W, Z)")
    if axis not in {"x", "y", "z"}:
        raise ValueError("axis must be one of 'x', 'y', 'z'")
    return np.sum(arr, axis=2)

def glyph_from_tink_token(token: str, size: int = 32) -> np.ndarray:
    token_norm = (
        token.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-").strip()
    )
    n = int(size)
    if n <= 4:
        raise ValueError("size too small for glyph synthesis")
    lowered = token_norm.lower()
    if lowered in {"i-glyph", "i glyph", "i"}:
        return _filled_square(n, pad=max(1, n // 8))
    if lowered == "octave cycle drive":
        return _horizontal_bar(n, thickness=max(1, n // 12))
    if lowered == "mirrorpulse":
        return _vertical_bar(n, thickness=max(1, n // 12))
    if lowered == "mirrorhold":
        return _diagonal_cross(n, thickness=max(1, n // 20))
    if lowered == "gravisystem":
        outer = _filled_square(n, pad=max(1, n // 6))
        inner = _filled_square(n, pad=max(1, n // 4))
        return outer - inner
    if lowered == "spiralborne codex":
        return _spiral(n, turns=3)
    raise ValueError(f"Unknown token: {token}")
```

### `src/g2v/fft_codec.py`
```python
from __future__ import annotations
import numpy as np

def fft_encode(img: np.ndarray) -> np.ndarray:
    arr = np.asarray(img, dtype=np.float64)
    return np.fft.fftshift(np.fft.fft2(arr))

def ifft_decode(spectrum: np.ndarray) -> np.ndarray:
    recon = np.fft.ifft2(np.fft.ifftshift(np.asarray(spectrum)))
    return np.real(recon)
```

### `src/g2v/cli.py`
```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="g2v", description="Glyph-to-Volume toolkit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_stack = sub.add_parser("stack", help="Stack glyphs into a volume")
    p_stack.add_argument("--out", required=True)
    p_stack.add_argument("glyphs", nargs="+")
    p_stack.set_defaults(func=cmd_stack)

    p_slice = sub.add_parser("slice", help="Extract a layer from a volume")
    p_slice.add_argument("volume")
    p_slice.add_argument("--z", required=True, type=int)
    p_slice.add_argument("--out", required=True)
    p_slice.set_defaults(func=cmd_slice)

    p_proj = sub.add_parser("project", help="Project a volume through an angle")
    p_proj.add_argument("volume")
    p_proj.add_argument("--theta", required=True, type=float)
    p_proj.add_argument("--axis", default="x", choices=["x", "y", "z"])
    p_proj.add_argument("--out", required=True)
    p_proj.set_defaults(func=cmd_project)

    p_fft = sub.add_parser("fft", help="FFT round-trip for a glyph")
    p_fft.add_argument("glyph")
    p_fft.add_argument("--out-recon", required=True, dest="out_recon")
    p_fft.add_argument("--out-spec", required=True, dest="out_spec")
    p_fft.set_defaults(func=cmd_fft)

    p_glyph = sub.add_parser("glyph", help="Generate a glyph array by token")
    p_glyph.add_argument("--token", required=True)
    p_glyph.add_argument("--size", default=32, type=int)
    p_glyph.add_argument("--out", required=True)
    p_glyph.set_defaults(func=cmd_glyph)
    return parser
```

## Demo

`examples/demo_stack_and_project.py`
```python
from pathlib import Path
import numpy as np
from src.g2v.volume import (
    angular_projection,
    build_volume_stack,
    glyph_from_tink_token,
    retrieve_layer,
)

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    glyph_a = glyph_from_tink_token("I-Glyph")
    glyph_b = glyph_from_tink_token("Octave Cycle Drive")
    volume = build_volume_stack([glyph_a, glyph_b])
    data_dir = ROOT / "examples" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    np.save(data_dir / "volume.npy", volume)
    np.save(data_dir / "layer0.npy", retrieve_layer(volume, 0))
    np.save(data_dir / "projection_30deg.npy", angular_projection(volume, theta_deg=30, axis="x"))
```

## Tests

`tests/test_fft_codec.py`
```python
import numpy as np
from src.g2v.fft_codec import fft_encode, ifft_decode

def test_fft_roundtrip() -> None:
    glyph = np.zeros((16, 16))
    glyph[4:12, 4:12] = 1.0
    spectrum = fft_encode(glyph)
    recon = ifft_decode(spectrum)
    assert np.mean((glyph - recon) ** 2) < 1e-10
```

`tests/test_volume.py`
```python
import numpy as np
import pytest
from src.g2v.volume import (
    angular_projection,
    build_volume_stack,
    glyph_from_tink_token,
    normalize,
    retrieve_layer,
)

def test_glyph_from_tink_token_unknown() -> None:
    with pytest.raises(ValueError):
        glyph_from_tink_token("unknown token")
```
