from __future__ import annotations
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class HilbertState:
    alpha: float
    beta: float
    gamma: float

    @property
    def norm(self) -> float:
        return math.sqrt(self.alpha**2 + self.beta**2 + self.gamma**2)

    def normalized(self) -> "HilbertState":
        n = self.norm or 1.0
        return HilbertState(self.alpha/n, self.beta/n, self.gamma/n)

def normalize(alpha: float, beta: float, gamma: float) -> tuple[float,float,float]:
    h = HilbertState(alpha, beta, gamma).normalized()
    return (h.alpha, h.beta, h.gamma)

def phase_shift(alpha: float, beta: float, gamma: float) -> float:
    # simple synthetic "phase" using atan2 of paradox vs (squirrel+fox)
    return math.atan2(gamma, (alpha + beta))

def dominant_frequency(beta: float, gamma: float, f0: float = 13.0) -> float:
    # baseline resonance near 13 Hz; shift by fox/paradox delta
    return f0 + 2.0 * (beta - gamma)


def to_complex(alpha: float, beta: float, gamma: float,
               pha: float=0.0, phb: float=0.0, phg: float=0.0) -> tuple[complex,complex,complex]:
    """Return complex amplitudes from magnitudes and phases (radians)."""
    return (alpha*complex(math.cos(pha), math.sin(pha)),
            beta*complex(math.cos(phb), math.sin(phb)),
            gamma*complex(math.cos(phg), math.sin(phg)))
