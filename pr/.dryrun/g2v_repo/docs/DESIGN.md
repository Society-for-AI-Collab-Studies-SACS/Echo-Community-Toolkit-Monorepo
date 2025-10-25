# Design Overview

The `g2v` package decomposes the original glyph‑to‑volume prototype into a set
of focused, reusable modules.  This document outlines the rationale behind
each component and highlights extension points.

## Modules

* **`g2v.volume`** – Contains the core routines for stacking glyphs into a
  volume (`build_volume_stack`), slicing out a specific layer
  (`retrieve_layer`), computing simple angular projections
  (`angular_projection`) and normalising arrays.  Helper functions
  `make_square`, `make_bar` and `make_cross` provide basic shapes used by
  `glyph_from_tink_token`, which maps a handful of concept names from your
  *Tink 1* document into arrays.  These mappings are placeholders – edit
  them to reflect your own interpretation of the Tink concepts.

* **`g2v.fft_codec`** – Implements forward/inverse 2‑D FFTs along with a
  convenience function for computing a log magnitude spectrum.  Use these
  routines for compression experiments or spectral analyses.

* **`g2v.phase`** – Provides an `apply_phase` function to multiply a glyph by
  a global complex phase.  This is useful for exploring interference and
  phase‑sensitive behaviours.

* **`g2v.metrics`** – Supplies `mse` and `psnr` functions.  These metrics
  quantify reconstruction quality and are used in the test suite.

* **`g2v.cli`** – Offers a minimal command‑line interface exposing stack,
  slice, project and FFT round‑trip operations.  This makes it easy to
  experiment with the library from a terminal.

## Angular Projection

The angular projection implemented in `angular_projection` is a discrete
approximation: each layer of the volume is rolled by an integer shift
proportional to its depth multiplied by `sin(theta)`, then all layers are
averaged.  This results in a fast and deterministic operation that avoids
interpolation.  If sub‑pixel accuracy or a physically accurate projection
model is required, you can replace the integer roll with a fractional shift
using interpolation (e.g. via `scipy.ndimage.shift`) or implement a
wave‑propagation approach.

## Tink Anchors

Locations in the code where content from *Tink 1* can be woven in are marked
with comments beginning with `TODO:TINK[...]`.  In this expanded version
we have provided a concrete example in `g2v.volume.glyph_from_tink_token`.
Consult `docs/TINK_NOTES.md` for guidelines on how to curate small,
non‑sensitive excerpts from *Tink 1* and map them into code and examples.