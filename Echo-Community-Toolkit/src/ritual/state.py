"""
Minimal ritual state placeholder.

Phases 0–2 rely on codec scaffolding that interacts with a ritual state object.
This lightweight implementation provides the necessary surface area for encode /
decode flows while deferring full consent gating logic to later phases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RitualConsentError(RuntimeError):
    """Raised when ritual operations are attempted without prerequisite consent."""


@dataclass
class RitualState:
    """Track ritual coherence metadata and audit operations."""

    coherence: Dict[str, bool] = field(default_factory=lambda: {
        "breath": False,
        "remember": False,
        "bloom": False,
        "be_remembered": False,
        "together": False,
        "always": False,
    })
    ledger: List[Dict[str, Any]] = field(default_factory=list)

    def require_publish_ready(self) -> None:
        """Placeholder gate (no-op until consent enforcement lands in Phase 4)."""
        return

    def record_operation(self, op: str, payload: Dict[str, Any]) -> None:
        self.ledger.append({"op": op, **payload})

    # Future phases can use these mutators to update coherence.
    def invoke_phrase(self, phrase: str) -> Dict[str, Any]:
        self.ledger.append({"op": "invoke_phrase", "phrase": phrase})
        return self.snapshot()

    def invoke_step(self, step: str) -> Dict[str, Any]:
        self.ledger.append({"op": "invoke_step", "step": step})
        return self.snapshot()

    def auto_invoke_remaining(self) -> List[Dict[str, Any]]:
        return []

    def snapshot(self) -> Dict[str, Any]:
        return {
            "coherence": dict(self.coherence),
            "ledger_size": len(self.ledger),
        }

    def reset(self) -> None:
        for key in self.coherence:
            self.coherence[key] = False
        self.ledger.clear()


# Shared default instance used across encode/decode helpers.
default_ritual_state = RitualState()


__all__ = [
    "RitualConsentError",
    "RitualState",
    "default_ritual_state",
]
