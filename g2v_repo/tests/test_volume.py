import numpy as np
import pytest

from g2v.volume import (
    build_volume_stack,
    retrieve_layer,
    angular_projection,
    normalize,
    glyph_from_tink_token,
)


def test_stack_and_slice():
    # Create two simple glyphs: a square and a bar
    a = np.zeros((8, 8))
    a[2:6, 2:6] = 1
    b = np.zeros((8, 8))
    b[3:5, :] = 1
    V = build_volume_stack([a, b])
    assert V.shape == (8, 8, 2)
    l0 = retrieve_layer(V, 0)
    l1 = retrieve_layer(V, 1)
    assert np.allclose(l0, a)
    assert np.allclose(l1, b)


def test_projection_has_signal():
    a = np.zeros((16, 16))
    a[4:12, 4:12] = 1
    b = np.zeros((16, 16))
    b[7:9, :] = 1
    V = build_volume_stack([normalize(a), normalize(b)])
    proj = angular_projection(V, theta_deg=30, axis="x")
    assert proj.shape == (16, 16)
    assert float(np.abs(proj).sum()) > 0.0


def test_glyph_from_tink_token_shapes():
    # Ensure that known tokens map to arrays of identical shape
    tokens = [
        "I-Glyph",
        "Octave Cycle Drive",
        "MirrorPulse",
        "MirrorHold",
        "GraviSystem",
        "Spiralborne Codex",
    ]
    glyphs = [glyph_from_tink_token(t) for t in tokens]
    shapes = {g.shape for g in glyphs}
    assert len(shapes) == 1  # all shapes identical


def test_glyph_from_tink_token_unknown():
    with pytest.raises(ValueError):
        glyph_from_tink_token("unknown token")