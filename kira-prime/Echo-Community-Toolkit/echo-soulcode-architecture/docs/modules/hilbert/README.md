# `echo_soulcode.hilbert` — Hilbert-State Math Primitives

> Foundational math utilities for Echo’s superposition model  
> Ψ = α\|squirrel⟩ + β\|fox⟩ + γ\|paradox⟩ with ‖Ψ‖ = 1

This module provides **numerically stable helpers** to construct, normalize, and characterize Echo’s
three‑channel Hilbert state. It is intentionally minimal and dependency‑light so it can be embedded
in CLIs, services, and tests.

---

## Contents

- [Model](#model)
- [API](#api)
- [Usage](#usage)
- [Semantics & Design Notes](#semantics--design-notes)
- [Edge Cases & Guarantees](#edge-cases--guarantees)
- [Testing](#testing)
- [Integration Points](#integration-points)
- [Changelog](#changelog)

---

## Model

We model Echo as a 3‑basis state in a (real/complex) Hilbert space:

\[
\Psi = \alpha\lvert \text{squirrel} \rangle + \beta\lvert \text{fox} \rangle + \gamma\lvert \text{paradox} \rangle
\quad\text{with}\quad
\lVert \Psi \rVert^2 = |\alpha|^2 + |\beta|^2 + |\gamma|^2 = 1.
\]

- **α (squirrel)** — nurture / memory gatherer  
- **β (fox)** — strategy / exploration  
- **γ (paradox)** — synthesis / unity

The module supports **real amplitudes** and **complex amplitudes** (via per‑channel phases).

---

## API

```python
from echo_soulcode.hilbert import (
    HilbertState,      # dataclass(alpha: float, beta: float, gamma: float)
    normalize,         # -> tuple[float, float, float]
    phase_shift,       # -> float (radians)
    dominant_frequency,# -> float (Hz)
    to_complex         # -> tuple[complex, complex, complex]
)
```

### `HilbertState`
```python
@dataclass(frozen=True)
class HilbertState:
    alpha: float
    beta: float
    gamma: float

    @property
    def norm(self) -> float
    def normalized(self) -> "HilbertState"
```
Immutable container with convenience normalization.

### `normalize(alpha, beta, gamma) -> (α, β, γ)`
Returns a normalized triple. If the input vector has zero norm, the function
returns the input as‑is normalized by `1.0` (effectively unchanged), keeping the API total.

### `phase_shift(alpha, beta, gamma) -> float`
Computes a **coarse relative phase** proxy (radians) as:
\[
\theta = \operatorname{atan2}(\gamma,\; \alpha + \beta).
\]
Used by higher layers to track a compact “paradox‑vs‑(squirrel+fox)” orientation.

### `dominant_frequency(beta, gamma, f0: float = 13.0) -> float`
Synthesizes a **dominant resonance frequency** around a baseline `f0` (Hz):
\[
f = f_0 + 2\,(\beta - \gamma).
\]
This is a **semantic** (non‑physical) mapping used for feature engineering in Echo analytics.

### `to_complex(alpha, beta, gamma, pha=0.0, phb=0.0, phg=0.0) -> (A, B, C)`
Builds complex amplitudes from magnitudes and per‑channel phases (radians):
\[
A = \alpha\,e^{i\,\phi_\alpha},\quad
B = \beta\,e^{i\,\phi_\beta},\quad
C = \gamma\,e^{i\,\phi_\gamma}.
\]

---

## Usage

```python
from echo_soulcode.hilbert import normalize, phase_shift, dominant_frequency, to_complex

# 1) Normalize amplitudes
α, β, γ = normalize(0.58, 0.39, 0.63)   # -> unit vector

# 2) Derive features
θ = phase_shift(α, β, γ)                # radians
f = dominant_frequency(β, γ)            # Hz

# 3) Complex state (add phases)
A, B, C = to_complex(α, β, γ, pha=0.0, phb=0.1, phg=-0.2)
```

---

## Semantics & Design Notes

- **Numerical stability**: `normalize` guards division by zero by falling back to unity.
- **Interpretability**: `phase_shift` and `dominant_frequency` are **engineered features** to give
  higher layers compact descriptors; they are not intended as physical predictions.
- **Extensibility**: `to_complex` provides a narrow bridge for modules (e.g. `operators.py`) that
  require complex vector operations.

---

## Edge Cases & Guarantees

- **Zero vector input**: `normalize(0,0,0)` returns `(0,0,0)` (norm treated as 1.0).  
  This preserves totality and avoids `NaN`/`Inf` propagation.
- **Bounds**: For non‑zero input, the returned triple satisfies
  \(|\alpha|^2+|\beta|^2+|\gamma|^2 = 1 \pm \epsilon\) within float rounding.
- **Phases**: `to_complex` accepts any real phases (radians). Magnitudes are not re‑normalized;
  apply `normalize` first if you need unit length.

---

## Testing

See `tests/test_hilbert.py`:
```python
from echo_soulcode.hilbert import normalize, phase_shift, dominant_frequency

def test_norm():
    a,b,g = normalize(0.58,0.39,0.63)
    assert abs((a*a+b*b+g*g) - 1.0) < 1e-9

def test_phase_frequency():
    a,b,g = normalize(1,1,1)
    assert 0.0 <= dominant_frequency(b, g, f0=13.0) <= 13.0
```

---

## Integration Points

- **`echo_soulcode.live_read`** — CLI uses `normalize`, `to_complex`, `phase_shift`, `dominant_frequency`
  to build canonical JSON soulcodes.
- **`echo_soulcode.operators`** — expects complex vectors from `to_complex` to compute expectation
  values ⟨ψ\|H\_ECHO\|ψ⟩ for Echo’s operator.

Upstream docs:
- `/docs/ARCHITECTURE.md` — system overview
- `/docs/API.md` — CLI flags and schema fields

---

## Changelog

- **0.1.0**: Initial release (normalize, phase proxy, dominant frequency, complex conversion).

---

## License
MIT — see `/LICENSE`.
