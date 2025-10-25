#!/usr/bin/env python3
import numpy as np
from pathlib import Path
try:
    from src.g2v.volume import build_volume_stack, retrieve_layer, angular_projection, glyph_from_tink_token
except ModuleNotFoundError:
    from g2v.volume import build_volume_stack, retrieve_layer, angular_projection, glyph_from_tink_token

data = Path(__file__).resolve().parents[1] / "examples" / "data"
data.mkdir(parents=True, exist_ok=True)
V = build_volume_stack([glyph_from_tink_token("I-Glyph"), glyph_from_tink_token("Octave Cycle Drive")])
np.save(data / "volume.npy", V)
np.save(data / "layer0.npy", retrieve_layer(V, 0))
np.save(data / "projection_30deg.npy", angular_projection(V, 30, "x"))
print("Saved to", data)
