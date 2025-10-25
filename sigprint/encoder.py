from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional

import numpy as np


@dataclass
class SigprintConfig:
    sample_rate: int = 250
    lockin_freq: float = 8.0


class SigprintEncoder:
    """Compute a 20-digit SIGPRINT code for 8 Hz alpha activity.

    The encoder performs a simple software lock-in at 8 Hz per channel and encodes
    features (phase pattern, amplitude distribution, coherence, reserved, checksum)
    into a compact 20-digit decimal string.
    """

    def __init__(self, channel_names: Iterable[str], sample_rate: int = 250, lockin_freq: float = 8.0) -> None:
        self.channel_names: List[str] = list(channel_names)
        self.sample_rate = int(sample_rate)
        self.lockin_freq = float(lockin_freq)

        # Precompute one second of reference sin/cos at the lock-in frequency
        t = np.arange(0, self.sample_rate, dtype=float) / float(self.sample_rate)
        self.ref_sin = np.sin(2 * np.pi * self.lockin_freq * t)
        self.ref_cos = np.cos(2 * np.pi * self.lockin_freq * t)

        self.prev_signature: str | None = None

    def process_epoch(self, eeg_epoch: Mapping[str, np.ndarray], reserved_digits: Iterable[int] | None = None) -> str:
        """Process ~1s epoch per channel and return a 20-digit signature.

        eeg_epoch maps channel name to a 1D numpy array of samples. Signals are
        trimmed or zero-padded to 1 second at the configured sample rate.
        """
        # 1) Per-channel lock-in to get I/Q, amplitude, and phase
        features: Dict[str, Dict[str, float]] = {}
        N = len(self.ref_sin)
        for ch in self.channel_names:
            sig = np.asarray(eeg_epoch.get(ch, np.zeros(N, dtype=float)), dtype=float)
            if sig.ndim != 1:
                sig = sig.ravel()
            if len(sig) != N:
                if len(sig) > N:
                    sig = sig[:N]
                else:
                    sig = np.pad(sig, (0, N - len(sig)))

            # Lock-in via correlation with sin/cos references; mean acts as a low-pass
            I = float(np.dot(sig, self.ref_cos) / N)
            Q = float(np.dot(sig, self.ref_sin) / N)
            amp = float(np.hypot(I, Q))
            phase_deg = float(np.degrees(np.arctan2(Q, I)))
            features[ch] = {"amp": amp, "phase": phase_deg}

        # 2) Global coherence and amplitude distribution
        phases = [features[ch]["phase"] for ch in self.channel_names if ch in features]
        coherence = compute_global_coherence(phases)
        distribution = compute_amplitude_distribution({ch: features[ch]["amp"] for ch in self.channel_names if ch in features})

        # 3) Encode into digits (4 + 4 + 4 + 6 + 2 = 20)
        code_digits: List[int] = []
        code_digits += encode_phase_pattern(features)
        code_digits += encode_amplitude_distribution(distribution)
        code_digits += encode_coherence(coherence)
        code_digits += encode_reserved(features, reserved_digits)
        code_digits += compute_checksum(code_digits)

        sig_code = "".join(str(int(d) % 10) for d in code_digits)

        # 4) Loop/Gate detection (compare to previous signature)
        if self.prev_signature:
            dist = signature_distance(self.prev_signature, sig_code)
            if dist > GATE_THRESHOLD:
                # In an integrated system, signal this event to the journaling/agent layer
                # print("**Gate detected**: significant change in brain state signature")
                pass
        self.prev_signature = sig_code
        return sig_code

    def process_epoch_result(
        self, eeg_epoch: Mapping[str, np.ndarray], reserved_digits: Iterable[int] | None = None
    ) -> "SigprintResult":
        """Like process_epoch but returns a rich result object with fields."""
        # Recompute features and coherence using the same path
        N = len(self.ref_sin)
        features: Dict[str, Dict[str, float]] = {}
        for ch in self.channel_names:
            sig = np.asarray(eeg_epoch.get(ch, np.zeros(N, dtype=float)), dtype=float)
            if sig.ndim != 1:
                sig = sig.ravel()
            if len(sig) != N:
                if len(sig) > N:
                    sig = sig[:N]
                else:
                    sig = np.pad(sig, (0, N - len(sig)))
            I = float(np.dot(sig, self.ref_cos) / N)
            Q = float(np.dot(sig, self.ref_sin) / N)
            amp = float(np.hypot(I, Q))
            phase_deg = float(np.degrees(np.arctan2(Q, I)))
            features[ch] = {"amp": amp, "phase": phase_deg}

        phases = [features[ch]["phase"] for ch in self.channel_names if ch in features]
        coherence = compute_global_coherence(phases)
        distribution = compute_amplitude_distribution({ch: features[ch]["amp"] for ch in self.channel_names if ch in features})

        code_digits: List[int] = []
        code_digits += encode_phase_pattern(features)
        code_digits += encode_amplitude_distribution(distribution)
        code_digits += encode_coherence(coherence)
        code_digits += encode_reserved(features, reserved_digits)
        code_digits += compute_checksum(code_digits)
        code = "".join(str(int(d) % 10) for d in code_digits)

        if self.prev_signature:
            dist = signature_distance(self.prev_signature, code)
            if dist > GATE_THRESHOLD:
                pass
        self.prev_signature = code
        return SigprintResult(code=code, coherence_score=coherence, features=features)


def compute_global_coherence(phases_deg: Iterable[float]) -> int:
    """Return 0–100 coherence from phase angles (degrees) via vector strength."""
    ph = list(phases_deg)
    if not ph:
        return 0
    radians = np.deg2rad(ph)
    vec = np.exp(1j * radians)
    resultant = np.sum(vec) / len(vec)
    return int(np.clip(np.abs(resultant) * 100.0, 0.0, 100.0))


def compute_amplitude_distribution(amplitudes: Mapping[str, float]) -> Dict[str, float]:
    """Return simple regional distribution as percentages (frontal/occipital)."""
    regions = {"frontal": 0.0, "occipital": 0.0}
    for ch, amp in amplitudes.items():
        a = float(max(0.0, amp))
        if ch.upper().startswith("F"):
            regions["frontal"] += a
        elif ch.upper().startswith("O"):
            regions["occipital"] += a
    total = float(sum(amplitudes.values())) if amplitudes else 1.0
    if total <= 0:
        total = 1.0
    return {k: (v / total) * 100.0 for k, v in regions.items()}


def encode_phase_pattern(features: Mapping[str, Mapping[str, float]]) -> List[int]:
    """Encode basic inter-hemispheric phase relation into 4 digits.

    Uses F3 vs F4 phase difference if present; remaining digits are zero for now.
    """
    d = [0, 0, 0, 0]
    if "F3" in features and "F4" in features:
        diff = (features["F3"]["phase"] - features["F4"]["phase"]) % 360.0
        val = int(min(max(diff, 0.0), 99.0))
        d[0] = val // 10
        d[1] = val % 10
    return d


def encode_amplitude_distribution(dist: Mapping[str, float]) -> List[int]:
    """Encode frontal and occipital percentages into 4 digits (two each)."""
    f = int(min(max(dist.get("frontal", 0.0), 0.0), 99.0))
    o = int(min(max(dist.get("occipital", 0.0), 0.0), 99.0))
    return [f // 10, f % 10, o // 10, o % 10]


def encode_coherence(coherence: int) -> List[int]:
    """Encode 0–100 (or up to 9999) coherence value into 4 digits."""
    val = int(np.clip(int(coherence), 0, 9999))
    return [(val // 1000) % 10, (val // 100) % 10, (val // 10) % 10, val % 10]


def encode_reserved(_features: Mapping[str, Mapping[str, float]], reserved_digits: Iterable[int] | None = None) -> List[int]:
    """Six reserved digits (future metrics, markers, tags).

    If `reserved_digits` is provided, the first six integers (0-9) are used; values
    outside 0-9 are reduced modulo 10. If fewer than six are provided, remaining
    positions are filled with zeros.
    """
    if reserved_digits is None:
        return [0, 0, 0, 0, 0, 0]
    out: List[int] = []
    for i, d in enumerate(reserved_digits):
        if i >= 6:
            break
        out.append(int(d) % 10)
    while len(out) < 6:
        out.append(0)
    return out

def reserved_from_stylus(stage: int | None = None) -> List[int]:
    """Helper to encode Stylus context into reserved digits.

    Encodes `stage` (1-6) into two digits (positions 13-14), remaining zeros.
    If stage is None or out of range, returns zeros.
    """
    if stage is None or stage < 0:
        return [0, 0, 0, 0, 0, 0]
    stage = int(stage) % 100
    return [stage // 10, stage % 10, 0, 0, 0, 0]


@dataclass
class SigprintResult:
    code: str
    coherence_score: int
    features: Dict[str, Dict[str, float]]


class SIGPRINTEncoder(SigprintEncoder):
    """Alias class with a higher-level API matching docs.

    Overrides process_epoch to return a SigprintResult to support
    examples that access `.code` or `.coherence_score`.
    """

    def process_epoch(
        self, eeg_epoch: Mapping[str, np.ndarray], reserved_digits: Optional[Iterable[int]] = None
    ) -> SigprintResult:  # type: ignore[override]
        return super().process_epoch_result(eeg_epoch, reserved_digits)


def compute_checksum(code_digits: Iterable[int]) -> List[int]:
    """Two-digit checksum: sum(first 18 digits) mod 97."""
    first18 = list(code_digits)[:18]
    s = int(sum(int(x) for x in first18) % 97)
    return [s // 10, s % 10]


def signature_distance(code1: str, code2: str) -> int:
    """Hamming distance between two numeric strings."""
    n = min(len(code1), len(code2))
    return sum(1 for i in range(n) if code1[i] != code2[i]) + abs(len(code1) - len(code2))


# Threshold for gate detection (number of differing digits)
GATE_THRESHOLD = 5


# ----------------------------- CLI helpers ---------------------------------- #
def _simulate_epoch(channels: Iterable[str], sr: int, freq: float, noise_amp: float = 0.2) -> Dict[str, np.ndarray]:
    """Generate a simple synthetic epoch with mild phase/amp differences."""
    t = np.arange(sr) / float(sr)
    epoch: Dict[str, np.ndarray] = {}
    for ch in channels:
        ch_u = ch.upper()
        # Basic per-region phase/amp profile (tweak as needed)
        if ch_u.startswith("F"):
            phase = np.deg2rad(0.0); amp = 0.7
        elif ch_u.startswith("O"):
            phase = np.deg2rad(10.0); amp = 1.0
        else:
            phase = np.deg2rad(5.0); amp = 0.8
        sig = amp * np.sin(2 * np.pi * freq * t + phase)
        if noise_amp > 0:
            sig = sig + noise_amp * np.random.randn(sr)
        epoch[ch] = sig.astype(float)
    return epoch


def _cli_main(argv: list[str] | None = None) -> int:
    import argparse, json, sys
    from datetime import datetime, timezone

    ap = argparse.ArgumentParser(prog="python -m sigprint.encoder", description="SIGPRINT encoder CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_demo = sub.add_parser("demo", help="simulate epochs and print signatures")
    p_demo.add_argument("--channels", default="F3,F4,Pz,Oz")
    p_demo.add_argument("--sample-rate", type=int, default=250)
    p_demo.add_argument("--lockin-freq", type=float, default=8.0)
    p_demo.add_argument("--epochs", type=int, default=5)
    p_demo.add_argument("--noise", type=float, default=0.2)
    p_demo.add_argument("--stage", type=int, default=None)
    p_demo.add_argument("--json", action="store_true", help="emit JSON objects instead of plain codes")

    p_stdin = sub.add_parser("stdin", help="read JSON epochs from stdin, one per line; print codes")
    p_stdin.add_argument("--channels", required=True, help="Comma-separated channel list to expect")
    p_stdin.add_argument("--sample-rate", type=int, default=250)
    p_stdin.add_argument("--lockin-freq", type=float, default=8.0)
    p_stdin.add_argument("--json", action="store_true", help="emit JSON objects instead of plain codes")

    ns = ap.parse_args(argv)

    if ns.cmd == "demo":
        chans = [c.strip() for c in ns.channels.split(",") if c.strip()]
        enc = SigprintEncoder(chans, sample_rate=ns.sample_rate, lockin_freq=ns.lockin_freq)
        reserved = reserved_from_stylus(ns.stage) if ns.stage is not None else None
        for _ in range(ns.epochs):
            epoch = _simulate_epoch(chans, ns.sample_rate, ns.lockin_freq, noise_amp=ns.noise)
            code = enc.process_epoch(epoch, reserved_digits=reserved)
            ts = datetime.now(timezone.utc).isoformat()
            if ns.json:
                print(json.dumps({"time": ts, "sigprint": code}, ensure_ascii=False))
            else:
                print(code)
        return 0

    if ns.cmd == "stdin":
        chans = [c.strip() for c in ns.channels.split(",") if c.strip()]
        enc = SigprintEncoder(chans, sample_rate=ns.sample_rate, lockin_freq=ns.lockin_freq)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Map to expected channels; missing channels get zeros
            epoch: Dict[str, np.ndarray] = {}
            N = enc.sample_rate
            for ch in chans:
                arr = obj.get(ch)
                if isinstance(arr, list):
                    sig = np.asarray(arr, dtype=float)
                else:
                    sig = np.zeros(N, dtype=float)
                if sig.ndim != 1:
                    sig = sig.ravel()
                if len(sig) != N:
                    if len(sig) > N:
                        sig = sig[:N]
                    else:
                        sig = np.pad(sig, (0, N - len(sig)))
                epoch[ch] = sig
            code = enc.process_epoch(epoch)
            if ns.json:
                print(json.dumps({"sigprint": code}, ensure_ascii=False))
            else:
                print(code)
        return 0

    ap.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli_main())
