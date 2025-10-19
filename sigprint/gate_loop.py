from __future__ import annotations

"""
Gate/Loop Detection Module
===========================
Detects consciousness state transitions (Gates) and recurring patterns (Loops)
by analyzing SIGPRINT code sequences over time.

Gates represent novel state transitions, while Loops indicate cyclic patterns.
"""

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StateTransition:
    """Container for state transition events."""

    timestamp: datetime
    transition_type: str  # 'gate' or 'loop'
    from_code: str
    to_code: str
    distance: float
    confidence: float
    metadata: Dict


class GateLoopDetector:
    """Detect Gates (large transitions) and Loops (recurring patterns) in SIGPRINT sequences."""

    def __init__(
        self,
        gate_threshold: float = 0.3,
        loop_threshold: float = 0.85,
        history_size: int = 60,
        min_loop_period: int = 3,
        max_loop_period: int = 20,
    ) -> None:
        self.gate_threshold = float(gate_threshold)
        self.loop_threshold = float(loop_threshold)
        self.min_loop_period = int(min_loop_period)
        self.max_loop_period = int(max_loop_period)

        # History
        self.history: Deque[str] = deque(maxlen=int(history_size))
        self.timestamps: Deque[datetime] = deque(maxlen=int(history_size))
        self.transitions: List[StateTransition] = []

        # Adaptive stats for distances
        self.distance_history: Deque[float] = deque(maxlen=100)
        self.baseline_distance: float = 0.1
        self.baseline_std: float = 0.05

        logger.info("Gate detector init: gate=%.2f loop=%.2f", self.gate_threshold, self.loop_threshold)

    def add_code(self, code: str, timestamp: Optional[datetime] = None) -> Dict[str, object]:
        """Add a 20-digit SIGPRINT code and analyze for gates/loops."""
        if timestamp is None:
            timestamp = datetime.now()

        out: Dict[str, object] = {
            "gate_detected": False,
            "loop_detected": False,
            "gate_info": None,
            "loop_info": None,
            "current_state": "stable",
        }

        if not self.history:
            self.history.append(code)
            self.timestamps.append(timestamp)
            return out

        gate_info = self._detect_gate(code, timestamp)
        if gate_info:
            out["gate_detected"] = True
            out["gate_info"] = gate_info
            out["current_state"] = "transition"

        loop_info = self._detect_loop(code)
        if loop_info:
            out["loop_detected"] = True
            out["loop_info"] = loop_info
            out["current_state"] = "cycling"

        self.history.append(code)
        self.timestamps.append(timestamp)
        self._update_baseline()
        return out

    def _detect_gate(self, new_code: str, timestamp: datetime) -> Optional[Dict[str, object]]:
        prev = self.history[-1]
        distance = self.calculate_distance(prev, new_code)
        self.distance_history.append(distance)

        if len(self.distance_history) > 10:
            z_score = (distance - self.baseline_distance) / (self.baseline_std + 1e-6)
            adaptive = self.gate_threshold
            if self.baseline_std > 0.1:
                adaptive *= 1.2
            elif self.baseline_std < 0.05:
                adaptive *= 0.8
        else:
            adaptive = self.gate_threshold
            z_score = 0.0

        if distance > adaptive:
            confidence = float(min(1.0, (distance - adaptive) / max(adaptive, 1e-6)))
            transition = StateTransition(
                timestamp=timestamp,
                transition_type="gate",
                from_code=prev,
                to_code=new_code,
                distance=distance,
                confidence=confidence,
                metadata={
                    "z_score": z_score,
                    "adaptive_threshold": adaptive,
                    "changed_digits": self._get_changed_digits(prev, new_code),
                },
            )
            self.transitions.append(transition)
            logger.info("Gate: distance=%.3f conf=%.2f", distance, confidence)
            return {
                "distance": distance,
                "confidence": confidence,
                "from_code": prev,
                "to_code": new_code,
                "timestamp": timestamp,
                "z_score": z_score,
                "adaptive_threshold": adaptive,
            }
        return None

    def _detect_loop(self, new_code: str) -> Optional[Dict[str, object]]:
        if len(self.history) < self.min_loop_period * 2:
            return None

        best = {"period": 0, "strength": 0.0, "phase_matches": 0}

        max_p = min(self.max_loop_period, len(self.history) // 2)
        for period in range(self.min_loop_period, max_p + 1):
            matches = 0
            total = 0
            for phase in range(period):
                sims: List[float] = []
                for cycle in range(1, len(self.history) // period):
                    i1 = -(phase + 1)
                    i2 = -(phase + 1 + cycle * period)
                    if abs(i2) <= len(self.history):
                        sims.append(self.calculate_similarity(self.history[i1], self.history[i2]))
                if sims:
                    mean_sim = float(np.mean(sims))
                    if mean_sim > self.loop_threshold:
                        matches += 1
                    total += 1
            if total > 0:
                strength = matches / total
                if strength > best["strength"]:
                    best = {"period": period, "strength": strength, "phase_matches": matches}

        if best["strength"] > 0.5:
            loop_codes = list(self.history)[-best["period"] :]
            logger.info("Loop: period=%d strength=%.3f", best["period"], best["strength"])
            return {
                **best,
                "loop_codes": loop_codes,
                "timestamp": self.timestamps[-1],
            }
        return None

    @staticmethod
    def calculate_distance(code1: str, code2: str) -> float:
        if len(code1) != len(code2):
            return 1.0
        return float(sum(c1 != c2 for c1, c2 in zip(code1, code2)) / len(code1))

    def calculate_similarity(self, code1: str, code2: str) -> float:
        return 1.0 - self.calculate_distance(code1, code2)

    @staticmethod
    def _get_changed_digits(code1: str, code2: str) -> List[int]:
        return [i for i, (a, b) in enumerate(zip(code1, code2)) if a != b]

    def _update_baseline(self) -> None:
        if len(self.distance_history) > 5:
            arr = np.asarray(self.distance_history, dtype=float)
            med = float(np.median(arr))
            mad = float(np.median(np.abs(arr - med)))
            self.baseline_distance = med
            self.baseline_std = 1.4826 * mad

    def get_state_summary(self) -> Dict[str, object]:
        if not self.history:
            return {"state": "no_data"}
        recent_gates = sum(1 for t in self.transitions[-10:] if t.transition_type == "gate")
        loop_info = self._detect_loop(self.history[-1]) if self.history else None
        if recent_gates > 2:
            state = "volatile"
        elif loop_info and loop_info["strength"] > 0.7:
            state = "looping"
        elif recent_gates == 1:
            state = "transitioning"
        else:
            state = "stable"
        return {
            "state": state,
            "recent_gates": recent_gates,
            "active_loop": loop_info is not None,
            "loop_period": loop_info["period"] if loop_info else None,
            "baseline_distance": self.baseline_distance,
            "baseline_std": self.baseline_std,
            "history_length": len(self.history),
        }

    def predict_next_code(self) -> Optional[str]:
        loop_info = self._detect_loop(self.history[-1]) if self.history else None
        if loop_info and loop_info["strength"] > 0.8:
            p = int(loop_info["period"])
            if len(self.history) >= p:
                return self.history[-p]
        return None

    def reset(self) -> None:
        self.history.clear()
        self.timestamps.clear()
        self.transitions.clear()
        self.distance_history.clear()
        logger.info("Gate/Loop detector reset")


class PatternAnalyzer:
    """Summary analyzer over sequences of SIGPRINT codes."""

    def __init__(self) -> None:
        self.detector = GateLoopDetector()

    def analyze_sequence(self, codes: List[str]) -> Dict[str, object]:
        res: Dict[str, object] = {
            "total_codes": len(codes),
            "unique_codes": len(set(codes)),
            "gates_detected": 0,
            "loops_detected": 0,
            "dominant_pattern": None,
            "entropy": 0.0,
            "complexity": 0.0,
        }
        for c in codes:
            det = self.detector.add_code(c)
            if det["gate_detected"]:
                res["gates_detected"] += 1
            if det["loop_detected"]:
                res["loops_detected"] += 1
        res["entropy"] = self._entropy(codes)
        res["complexity"] = self._complexity(codes)
        res["dominant_pattern"] = self.detector.get_state_summary().get("state")
        return res

    @staticmethod
    def _entropy(codes: List[str]) -> float:
        if not codes:
            return 0.0
        _, counts = np.unique(codes, return_counts=True)
        p = counts / float(len(codes))
        ent = float(-np.sum(p * np.log2(p + 1e-10)))
        max_ent = float(np.log2(len(codes))) if codes else 0.0
        return float(ent / max_ent) if max_ent > 0 else 0.0

    @staticmethod
    def _complexity(codes: List[str]) -> float:
        if not codes:
            return 0.0
        transitions = sum(1 for i in range(1, len(codes)) if codes[i] != codes[i - 1])
        denom = max(1, len(codes) - 1)
        return float(transitions / denom)

