import numpy as np
import pytest

from src.g2v.volume import (
    angular_projection,
    build_volume_stack,
    glyph_from_tink_token,
    normalize,
    retrieve_layer,
)


def test_stack_and_slice() -> None:
    square = np.zeros((8, 8))
    square[2:6, 2:6] = 1
    bar = np.zeros((8, 8))
    bar[3:5, :] = 1

    volume = build_volume_stack([square, bar])
    assert volume.shape == (8, 8, 2)

    layer0 = retrieve_layer(volume, 0)
    layer1 = retrieve_layer(volume, 1)
    assert np.allclose(layer0, square)
    assert np.allclose(layer1, bar)


def test_projection_has_signal() -> None:
    square = np.zeros((16, 16))
    square[4:12, 4:12] = 1
    bar = np.zeros((16, 16))
    bar[7:9, :] = 1

    volume = build_volume_stack([normalize(square), normalize(bar)])
    projection = angular_projection(volume, theta_deg=30, axis="x")
    assert projection.shape == (16, 16)
    assert float(np.abs(projection).sum()) > 0.0


def test_glyph_from_tink_token_shapes() -> None:
    tokens = [
        "I-Glyph",
        "Octave Cycle Drive",
        "MirrorPulse",
        "MirrorHold",
        "GraviSystem",
        "Spiralborne Codex",
    ]
    glyphs = [glyph_from_tink_token(token) for token in tokens]
    shapes = {glyph.shape for glyph in glyphs}
    assert len(shapes) == 1


def test_glyph_from_tink_token_unknown() -> None:
    with pytest.raises(ValueError):
        glyph_from_tink_token("unknown token")
