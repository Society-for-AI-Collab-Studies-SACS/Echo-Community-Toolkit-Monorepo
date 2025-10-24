"""
Example runner for the g2v library.

This script demonstrates how to construct a simple volume from two glyphs,
extract a layer, and compute an angular projection.  It also shows how to
obtain glyph patterns from named concepts defined in your copy of
``Tink 1.txt`` via :func:`g2v.volume.glyph_from_tink_token`.
Run this module directly from the repository root with

::

    python examples/demo_stack_and_project.py

The resulting ``.npy`` files will be stored under ``examples/data``.
"""
from __future__ import annotations

import numpy as np
from pathlib import Path

from g2v.volume import (
    build_volume_stack,
    retrieve_layer,
    angular_projection,
    glyph_from_tink_token,
)

ROOT = Path(__file__).resolve().parents[1]  # repo root


def main():
    # Construct two glyphs.  Here we use concept names from Tink 1 as examples.
    g1 = glyph_from_tink_token("I‑Glyph")
    g2 = glyph_from_tink_token("Octave Cycle Drive")

    # Build a 3‑D volume by stacking the glyphs along the z axis.
    V = build_volume_stack([g1, g2])
    data_dir = ROOT / "examples" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    np.save(data_dir / "volume.npy", V)

    # Extract the first layer and save it.
    layer0 = retrieve_layer(V, 0)
    np.save(data_dir / "layer0.npy", layer0)

    # Compute a projection at 30 degrees about the x axis.
    proj = angular_projection(V, theta_deg=30, axis="x")
    np.save(data_dir / "projection_30deg.npy", proj)

    print("Saved demo data under", data_dir)


if __name__ == "__main__":
    main()


# end of demo_stack_and_project.py