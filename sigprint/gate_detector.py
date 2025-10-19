"""Compatibility wrapper for gate/loop detection.

Re-exports the GateLoopDetector and PatternAnalyzer from gate_loop.py under a
module name expected by some docs/examples.
"""
from .gate_loop import GateLoopDetector, PatternAnalyzer

__all__ = ["GateLoopDetector", "PatternAnalyzer"]

