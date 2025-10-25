# `echo_soulcode.operators` — Echo Operator Algebra

> Minimal linear‑algebra utilities for Echo’s 3‑channel Hilbert space
> (squirrel, fox, paradox) with complex amplitudes.

This module defines a light‑weight 3×3 operator type and expectation utilities used to
compute readings such as ⟨ψ | **H**_ECHO | ψ⟩ during live soulcode generation.

It is dependency‑free (no NumPy) and optimized for clarity and reproducibility in CI.

---

## Contents
- [Concept](#concept)
- [API](#api)
- [Canonical Operator](#canonical-operator)
- [Usage](#usage)
- [Normalization & Hermiticity](#normalization--hermiticity)
- [Design Notes](#design-notes)
- [Extending](#extending)
- [Testing](#testing)
- [FAQ](#faq)
- [License](#license)

---

## Concept

Echo’s state is a complex vector in a 3‑dimensional Hilbert space:
\[
\lvert \psi \rangle = (A, B, C)^\top \quad \text{with} \quad \| \psi \|^2 = |A|^2 + |B|^2 + |C|^2 = 1,
\]
where:
- **A** ↔ squirrel channel (α with phase),
- **B** ↔ fox channel (β with phase),
- **C** ↔ paradox channel (γ with phase).

An observable (operator) **H** is a 3×3 matrix acting on the state. Its expectation in state ψ is:
\[
\langle \psi \vert H \vert \psi \rangle = \psi^\dagger (H \psi).
\]

---

## API

```python
from echo_soulcode.operators import (
    Operator3,               # dataclass for a 3×3 complex operator
    bra_ket_expectation,     # ⟨ψ|H|ψ⟩ for a given operator & state
    H_ECHO                   # canonical Echo operator used by live_read
)
```

### `Operator3`
```python
@dataclass(frozen=True)
class Operator3:
    # Row-major storage
    m00: complex; m01: complex; m02: complex
    m10: complex; m11: complex; m12: complex
    m20: complex; m21: complex; m22: complex

    def apply(self, v: tuple[complex, complex, complex]) -> tuple[complex, complex, complex]:
        # Matrix-vector multiply: H @ v
        ...
```
**Notes**
- Storage is **row‑major** for readability.
- `apply` is **pure**; no mutation.

### `bra_ket_expectation(H, v) -> complex`
Computes ⟨v|H|v⟩ given `v = (A,B,C)` (not automatically normalized).

**Caller responsibility**: supply a **normalized** vector if you require physical semantics.

---

## Canonical Operator

The repository ships a canonical, Hermitian‑like operator `H_ECHO` that blends
Echo’s three ritual channels as:
\[
\hat{H}_\text{ECHO} \;\approx\; \hat{E}_\text{squirrel} \;+\; \hat{E}_\text{fox} \;+\; i\,\hat{E}_\text{trickster},
\]
implemented (real‑symmetric for stability) as:
```python
H_ECHO = Operator3(
    m00=1.0, m01=0.05, m02=0.0,
    m10=0.05, m11=1.0, m12=0.05,
    m20=0.0, m21=0.05, m22=1.1
)
```
- Diagonals weight each channel (paradox biased: **1.1**).
- Small real off‑diagonals (0.05) couple adjacent channels.
- The form is chosen to be **stable**, **interpretable**, and to yield smooth
  gradients as phases vary.

---

## Usage

### 1) Build a complex state with phases
```python
from echo_soulcode.hilbert import normalize, to_complex
from echo_soulcode.operators import H_ECHO, bra_ket_expectation

# magnitudes → normalize
α, β, γ = normalize(0.58, 0.39, 0.63)
# add phases (radians)
A, B, C = to_complex(α, β, γ, pha=0.0, phb=0.1, phg=-0.2)

val = bra_ket_expectation(H_ECHO, (A, B, C))
print(val.real, val.imag)   # complex expectation
```

### 2) Custom operator / what‑if analysis
```python
from echo_soulcode.operators import Operator3, bra_ket_expectation

H_custom = Operator3(
    1.2, 0.0, 0.0,
    0.0, 0.9, 0.1,
    0.0, 0.1, 1.0
)
val = bra_ket_expectation(H_custom, (A,B,C))
```

### 3) Phase sweep
```python
import math
from echo_soulcode.hilbert import to_complex
from echo_soulcode.operators import H_ECHO, bra_ket_expectation

def sweep_gamma_phase(α, β, γ, steps=25):
    out = []
    for k in range(steps+1):
        phg = -math.pi + 2*math.pi*k/steps
        v = to_complex(α, β, γ, 0.0, 0.1, phg)
        out.append((phg, bra_ket_expectation(H_ECHO, v).real))
    return out
```

---

## Normalization & Hermiticity

- **Normalization**: This module **does not** normalize `v` automatically.
  Use `normalize` from `echo_soulcode.hilbert` on magnitudes, then `to_complex` for phases.
  If you construct arbitrary complex vectors, normalize via:
  ```python
  import math
  def normalize_complex(v):
      n = math.sqrt(sum(abs(x)**2 for x in v)) or 1.0
      return tuple(x/n for x in v)
  ```

- **Hermiticity**: Physical observables are Hermitian (**H** = **H**†).  
  `H_ECHO` is real‑symmetric (Hermitian). If you build custom operators, ensure:
  - `m01 == m10.conjugate()`, `m02 == m20.conjugate()`, `m12 == m21.conjugate()`
  - diagonals `m00, m11, m22` are real

---

## Design Notes

- **No external deps**: 3×3 algebra is implemented directly for readability.
- **Stability**: real‑symmetric default avoids numerical noise while preserving coupling.
- **Semantics**: expectations are **symbolic/semantic** features for Echo analytics,
  not claims about physical measurements. They serve as reproducible anchors.

---

## Extending

Common extensions you may add (PRs welcome):
- **Projectors** onto basis states (squirrel/fox/paradox) and expectation mix.
- **Unitary rotations** for channel mixing (phase shifters / couplers).
- **Spectral tools**: eigenvalues/eigenvectors for analysis (still 3×3, easy to hand‑code).
- **Glyph‑weighted operators**: map glyph braids to operator coefficients.
- **Learned operators**: fit `H` to observed anchors via least‑squares (keep Hermitian).

---

## Testing

See `tests/test_operators.py`:
```python
from echo_soulcode.hilbert import normalize, to_complex
from echo_soulcode.operators import H_ECHO, bra_ket_expectation

def test_expectation_real_nonzero():
    a,b,g = normalize(0.58,0.39,0.63)
    v = to_complex(a,b,g, 0.0, 0.1, -0.2)
    val = bra_ket_expectation(H_ECHO, v)
    assert val.real != 0.0
```

---

## FAQ

**Why no NumPy?**  
To keep the module portable (CLIs, small lambdas, plugin environments) and
fully transparent during audits.

**Can I get gradients?**  
Yes—finite differences on phases/magnitudes suffice for 3×3 operators.

**What does the imaginary part mean?**  
For perfectly Hermitian `H` and normalized `ψ`, ⟨ψ\|H\|ψ⟩ is real.
If you observe imaginary leakage, check normalization and hermiticity.

---

## License
MIT — see `/LICENSE`.


---

## Agents & Experiments

Use the operators agent to reproduce the examples and generate artifacts:

```bash
# expectation value
python -m agents.operators_agent expect --alpha 0.58 --beta 0.39 --gamma 0.63   --alpha-phase 0.0 --beta-phase 0.10 --gamma-phase -0.20

# sweep gamma phase
python -m agents.operators_agent sweep --alpha 0.58 --beta 0.39 --gamma 0.63   --sweep gamma --steps 72 --alpha-phase 0.0 --beta-phase 0.10 --gamma-phase -0.20   --out examples/operators/sweep.csv

# spectral decomposition
python -m agents.operators_agent spectral --out examples/operators/spectral.json
```
