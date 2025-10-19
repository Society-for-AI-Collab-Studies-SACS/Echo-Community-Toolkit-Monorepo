from __future__ import annotations

"""
Lock-in Amplification Module for 8 Hz Alpha Band Processing
==========================================================
Software lock-in detection to extract amplitude and phase at a target
frequency (default 8 Hz). Uses SciPy when available; otherwise falls back
to a lightweight exponential low-pass for real-time usage without SciPy.
"""

import logging
from typing import Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:  # optional SciPy path
    from scipy import signal as _sp_signal  # type: ignore

    _HAS_SCIPY = True
except Exception:  # pragma: no cover - environment without SciPy
    _sp_signal = None
    _HAS_SCIPY = False


class LockInAmplifier:
    """Software lock-in amplifier at a configurable target frequency.

    When SciPy is available, uses Butterworth low-pass with stateful lfilter.
    Otherwise, applies a simple exponential low-pass per-channel as fallback.
    """

    def __init__(
        self,
        sample_rate: float = 250.0,
        target_freq: float = 8.0,
        lowpass_cutoff: float = 2.0,
        filter_order: int = 4,
    ) -> None:
        self.fs = float(sample_rate)
        self.f0 = float(target_freq)
        self.cutoff = float(lowpass_cutoff)
        self.order = int(filter_order)

        # One-second reference for demodulation window
        self.t = np.arange(0, int(sample_rate)) / float(sample_rate)
        self.ref_sin = np.sin(2 * np.pi * self.f0 * self.t)
        self.ref_cos = np.cos(2 * np.pi * self.f0 * self.t)

        self.filter_states: Dict[str, Dict[str, np.ndarray]] = {}

        if _HAS_SCIPY:
            nyq = self.fs / 2.0
            normal_cutoff = max(1e-6, min(0.99, self.cutoff / nyq))
            self._b, self._a = _sp_signal.butter(self.order, normal_cutoff, btype="low")
            logger.info(
                "Lock-in(SciPy) init: f0=%.3fHz fs=%.1fHz cutoff=%.2fHz order=%d",
                self.f0,
                self.fs,
                self.cutoff,
                self.order,
            )
        else:
            # Fallback: EMA alpha derived from cutoff (~-3 dB)
            # alpha = 1 - exp(-2*pi*fc/fs)
            self._alpha = float(1.0 - np.exp(-2.0 * np.pi * self.cutoff / self.fs))
            self._ema_state: Dict[str, Dict[str, float]] = {}
            logger.info(
                "Lock-in(EMA) init: f0=%.3fHz fs=%.1fHz cutoff=%.2fHz (alpha=%.5f)",
                self.f0,
                self.fs,
                self.cutoff,
                self._alpha,
            )

    def _resize_signal(self, x: np.ndarray) -> np.ndarray:
        N = len(self.ref_sin)
        if len(x) == N:
            return x
        return x[:N] if len(x) > N else np.pad(x, (0, N - len(x)))

    def _lp_stateful(self, ch: str, x: np.ndarray, key: str) -> np.ndarray:
        if _HAS_SCIPY:
            if ch in self.filter_states:
                zi = self.filter_states[ch][key]
            else:
                zi = _sp_signal.lfilter_zi(self._b, self._a) * x[0]
            y, zf = _sp_signal.lfilter(self._b, self._a, x, zi=zi)
            self.filter_states.setdefault(ch, {})[key] = zf
            return y
        # EMA fallback
        st = self._ema_state.setdefault(ch, {}).setdefault(key, float(x[0]))
        y = np.empty_like(x)
        a = self._alpha
        prev = st
        for i, v in enumerate(x):
            prev = prev + a * (float(v) - prev)
            y[i] = prev
        self._ema_state[ch][key] = float(prev)
        return y

    def process(self, signal_data: np.ndarray, channel_name: Optional[str] = None) -> Tuple[float, float, float, float]:
        x = np.asarray(signal_data, dtype=float)
        x = self._resize_signal(x)
        i_raw = x * self.ref_cos
        q_raw = x * self.ref_sin

        if channel_name:
            i_filt = self._lp_stateful(channel_name, i_raw, "i")
            q_filt = self._lp_stateful(channel_name, q_raw, "q")
        else:
            if _HAS_SCIPY:
                i_filt = _sp_signal.filtfilt(self._b, self._a, i_raw)
                q_filt = _sp_signal.filtfilt(self._b, self._a, q_raw)
            else:
                # EMA fallback without state
                i_filt = self._lp_stateful("__tmp_i__", i_raw, "i")
                q_filt = self._lp_stateful("__tmp_q__", q_raw, "q")

        I = float(np.mean(i_filt) * 2.0)
        Q = float(np.mean(q_filt) * 2.0)
        amp = float(np.hypot(I, Q))
        phase_deg = float(np.degrees(np.arctan2(Q, I)))
        return I, Q, amp, phase_deg

    def process_multichannel(self, epoch_data: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for ch, x in epoch_data.items():
            I, Q, amp, phase = self.process(x, ch)
            out[ch] = {"I": I, "Q": Q, "amplitude": amp, "phase": phase, "snr": self._estimate_snr(np.asarray(x, dtype=float), amp)}
        return out

    def reset_filters(self, channel: Optional[str] = None) -> None:
        if _HAS_SCIPY:
            if channel is None:
                self.filter_states.clear()
            else:
                self.filter_states.pop(channel, None)
        else:
            if channel is None:
                self._ema_state.clear()
            else:
                self._ema_state.pop(channel, None)

    def update_target_frequency(self, new_freq: float) -> None:
        self.f0 = float(new_freq)
        self.ref_sin = np.sin(2 * np.pi * self.f0 * self.t)
        self.ref_cos = np.cos(2 * np.pi * self.f0 * self.t)
        self.reset_filters()
        logger.info("Lock-in updated target frequency to %.3f Hz", self.f0)

    def get_reference_signals(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.ref_sin.copy(), self.ref_cos.copy()

    def _estimate_snr(self, signal_data: np.ndarray, amplitude: float) -> float:
        t = np.arange(len(signal_data)) / self.fs
        reconstructed = amplitude * np.cos(2 * np.pi * self.f0 * t)
        residual = signal_data - reconstructed
        noise_power = float(np.var(residual))
        signal_power = float(amplitude ** 2)
        if noise_power > 0.0:
            return float(10.0 * np.log10(signal_power / noise_power))
        return float("inf")


class MultiFrequencyLockIn:
    """Multiple-band lock-in over standard EEG bands (center frequencies)."""

    def __init__(self, sample_rate: float = 250.0) -> None:
        self.sample_rate = float(sample_rate)
        self.bands = {
            "delta": (0.5, 4.0),
            "theta": (4.0, 8.0),
            "alpha": (8.0, 12.0),
            "beta": (12.0, 30.0),
            "gamma": (30.0, 100.0),
        }
        self.amplifiers: Dict[str, LockInAmplifier] = {}
        for name, (f_low, f_high) in self.bands.items():
            center = 0.5 * (f_low + f_high)
            cutoff = min(2.0, 0.25 * (f_high - f_low))
            self.amplifiers[name] = LockInAmplifier(sample_rate=sample_rate, target_freq=center, lowpass_cutoff=cutoff)

    def process_all_bands(self, signal_data: np.ndarray) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for name, amp in self.amplifiers.items():
            I, Q, A, phase = amp.process(np.asarray(signal_data, dtype=float))
            out[name] = {"amplitude": A, "phase": phase, "I": I, "Q": Q}
        return out

