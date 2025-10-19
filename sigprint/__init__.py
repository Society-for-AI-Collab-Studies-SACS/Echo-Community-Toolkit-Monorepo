"""SIGPRINT package exports.

Convenience exports for encoder, lock-in, coherence, and gate/loop detection.
"""
from .encoder import SIGPRINTEncoder, SigprintEncoder, SigprintResult, reserved_from_stylus
from .lockin import LockInAmplifier, MultiFrequencyLockIn
from .coherence import PhaseCoherence, SpatialCoherence
from .gate_loop import GateLoopDetector, PatternAnalyzer

__all__ = [
    "SIGPRINTEncoder",
    "SigprintEncoder",
    "SigprintResult",
    "reserved_from_stylus",
    "LockInAmplifier",
    "MultiFrequencyLockIn",
    "PhaseCoherence",
    "SpatialCoherence",
    "GateLoopDetector",
    "PatternAnalyzer",
]

