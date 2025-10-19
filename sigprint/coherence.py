from __future__ import annotations

"""
Phase Coherence Analysis Module
================================
Calculates phase synchronization between EEG channels using PLV, WPLI,
and related spatial metrics. SciPy is optional; a circular mean fallback
is used when SciPy is not available.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:  # optional SciPy deps
    from scipy import stats as _sp_stats  # type: ignore

    _HAS_SCIPY = True
except Exception:  # pragma: no cover
    _sp_stats = None
    _HAS_SCIPY = False


def _circmean(x: np.ndarray) -> float:
    """Circular mean in radians. Uses SciPy if available, else vector mean."""
    x = np.asarray(x, dtype=float)
    if _HAS_SCIPY:
        # SciPy expects range; default [-pi, pi)
        return float(_sp_stats.circmean(x))
    # Fallback: angle of mean unit phasor
    return float(np.angle(np.mean(np.exp(1j * x))))


class PhaseCoherence:
    """Calculate phase coherence between signals or channels."""

    def __init__(self, window_size: int = 250) -> None:
        self.window_size = int(window_size)

    def calculate_plv(self, phases1: np.ndarray, phases2: np.ndarray) -> float:
        """Phase Locking Value (0..1) from two phase series (radians)."""
        p1 = np.asarray(phases1, dtype=float)
        p2 = np.asarray(phases2, dtype=float)
        if p1.shape != p2.shape:
            n = min(len(p1), len(p2))
            p1 = p1[:n]
            p2 = p2[:n]
        if p1.size == 0:
            return 0.0
        phase_diff = p1 - p2
        cos_mean = float(np.mean(np.cos(phase_diff)))
        sin_mean = float(np.mean(np.sin(phase_diff)))
        return float(np.hypot(cos_mean, sin_mean))

    def calculate_wpli(self, phases1: np.ndarray, phases2: np.ndarray) -> float:
        """Weighted Phase Lag Index (0..1) from phase differences.

        Note: This approximation uses phase differences directly instead of
        cross-spectral imaginary parts; adequate for quick heuristics.
        """
        p1 = np.asarray(phases1, dtype=float)
        p2 = np.asarray(phases2, dtype=float)
        n = min(len(p1), len(p2))
        if n == 0:
            return 0.0
        phase_diff = p1[:n] - p2[:n]
        imag_part = np.sin(phase_diff)
        denom = float(np.mean(np.abs(imag_part)))
        if denom == 0.0:
            return 0.0
        numer = float(np.mean(np.abs(imag_part) * np.sign(imag_part)))
        return float(abs(numer) / denom)

    def calculate_global_coherence(self, phase_dict: Dict[str, float], method: str = "plv") -> float:
        """Global coherence from per-channel phases (radians).

        Methods:
        - 'plv': average pairwise PLV across channels
        - 'circular_mean': vector strength of phases (Kuramoto R)
        - 'kuramoto': alias of circular_mean
        """
        phases = np.asarray(list(phase_dict.values()), dtype=float)
        n = len(phases)
        if n == 0:
            return 0.0
        if method == "plv":
            if n < 2:
                return 0.0
            acc = 0.0
            cnt = 0
            for i in range(n):
                for j in range(i + 1, n):
                    acc += self.calculate_plv(np.array([phases[i]]), np.array([phases[j]]))
                    cnt += 1
            return float(acc / cnt) if cnt else 0.0
        elif method in ("circular_mean", "kuramoto"):
            r = abs(np.mean(np.exp(1j * phases)))
            return float(r)
        else:
            raise ValueError(f"Unknown method: {method}")

    def calculate_regional_coherence(self, phase_dict: Dict[str, float], region1: List[str], region2: List[str]) -> float:
        """Coherence between two channel groups via PLV of their circular means."""
        phases1 = [phase_dict[ch] for ch in region1 if ch in phase_dict]
        phases2 = [phase_dict[ch] for ch in region2 if ch in phase_dict]
        if not phases1 or not phases2:
            return 0.0
        mean1 = _circmean(np.asarray(phases1, dtype=float))
        mean2 = _circmean(np.asarray(phases2, dtype=float))
        return self.calculate_plv(np.array([mean1]), np.array([mean2]))

    def calculate_coherence_matrix(self, phase_dict: Dict[str, float]) -> np.ndarray:
        """Symmetric matrix of PLV between all pairs."""
        channels = list(phase_dict.keys())
        n = len(channels)
        M = np.zeros((n, n), dtype=float)
        for i in range(n):
            M[i, i] = 1.0
            for j in range(i + 1, n):
                plv = self.calculate_plv(np.array([phase_dict[channels[i]]]), np.array([phase_dict[channels[j]]]))
                M[i, j] = M[j, i] = plv
        return M

    def sliding_window_coherence(
        self, phase_series1: np.ndarray, phase_series2: np.ndarray, window_size: Optional[int] = None, step_size: int = 1
    ) -> np.ndarray:
        """PLV over sliding windows of two phase time series (radians)."""
        if window_size is None:
            window_size = self.window_size
        p1 = np.asarray(phase_series1, dtype=float)
        p2 = np.asarray(phase_series2, dtype=float)
        n = min(len(p1), len(p2))
        if n < window_size or window_size <= 0:
            return np.zeros(0, dtype=float)
        n_win = (n - window_size) // step_size + 1
        out = np.zeros(n_win, dtype=float)
        for i in range(n_win):
            s = i * step_size
            e = s + window_size
            out[i] = self.calculate_plv(p1[s:e], p2[s:e])
        return out


class SpatialCoherence:
    """Spatial coherence patterns over multi-channel EEG.

    Includes topographic regional metrics and gradient estimation.
    """

    BRAIN_REGIONS: Dict[str, List[str]] = {
        "frontal": ["Fp1", "Fp2", "F3", "F4", "F7", "F8", "Fz"],
        "central": ["C3", "C4", "Cz"],
        "temporal": ["T3", "T4", "T5", "T6"],
        "parietal": ["P3", "P4", "Pz"],
        "occipital": ["O1", "O2"],
    }

    def __init__(self) -> None:
        self.coherence_calc = PhaseCoherence()

    def analyze_spatial_pattern(self, phase_dict: Dict[str, float]) -> Dict[str, object]:
        res: Dict[str, object] = {
            "global_coherence": self.coherence_calc.calculate_global_coherence(phase_dict, method="kuramoto"),
            "regional_coherence": {},
            "inter_hemispheric": 0.0,
            "anterior_posterior": 0.0,
            "dominant_pattern": None,
        }
        # Regional coherence within each region
        regional: Dict[str, float] = {}
        for region, chans in self.BRAIN_REGIONS.items():
            subset = {ch: phase_dict[ch] for ch in chans if ch in phase_dict}
            if len(subset) > 1:
                regional[region] = self.coherence_calc.calculate_global_coherence(subset, method="kuramoto")
        res["regional_coherence"] = regional

        # Inter-hemispheric (left/right numeric convention)
        left = [ch for ch in phase_dict if any(x in ch for x in ["1", "3", "5", "7"])]
        right = [ch for ch in phase_dict if any(x in ch for x in ["2", "4", "6", "8"])]
        if left and right:
            res["inter_hemispheric"] = self.coherence_calc.calculate_regional_coherence(phase_dict, left, right)

        # Anterior vs posterior
        anterior = self.BRAIN_REGIONS["frontal"]
        posterior = self.BRAIN_REGIONS["parietal"] + self.BRAIN_REGIONS["occipital"]
        res["anterior_posterior"] = self.coherence_calc.calculate_regional_coherence(phase_dict, anterior, posterior)

        res["dominant_pattern"] = self._identify_pattern(res)
        return res

    def _identify_pattern(self, coherence_results: Dict[str, object]) -> str:
        g = float(coherence_results.get("global_coherence", 0.0))
        ih = float(coherence_results.get("inter_hemispheric", 0.0))
        ap = float(coherence_results.get("anterior_posterior", 0.0))
        if g > 0.7:
            return "high_global_synchrony"
        if ih > 0.6 and ap < 0.4:
            return "hemispheric_synchrony"
        if ap > 0.6 and ih < 0.4:
            return "anterior_posterior_gradient"
        if g < 0.3:
            return "desynchronized"
        return "mixed_pattern"

    def calculate_phase_gradient(self, phase_dict: Dict[str, float], channel_positions: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        chans = [ch for ch in phase_dict.keys() if ch in channel_positions]
        if len(chans) < 3:
            return {"gradient_magnitude": 0.0, "gradient_direction": 0.0}
        positions = np.array([channel_positions[ch] for ch in chans], dtype=float)
        phases = np.array([phase_dict[ch] for ch in chans], dtype=float)
        A = np.column_stack([positions, np.ones(len(positions))])
        coeffs, _, _, _ = np.linalg.lstsq(A, phases, rcond=None)
        grad_x = float(coeffs[0])
        grad_y = float(coeffs[1])
        magnitude = float(np.hypot(grad_x, grad_y))
        direction = float(np.degrees(np.arctan2(grad_y, grad_x)))
        return {
            "gradient_magnitude": magnitude,
            "gradient_direction": direction,
            "gradient_x": grad_x,
            "gradient_y": grad_y,
        }

