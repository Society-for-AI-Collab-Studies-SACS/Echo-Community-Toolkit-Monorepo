"""
Therapeutic journaling scenario built on VesselOS Kira Prime.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from pipeline.dispatcher_enhanced import EnhancedMRPDispatcher, PipelineContext
from pipeline.intent_parser import IntentParser
from library_core.workspace import Workspace


@dataclass
class TherapeuticJournal:
    """Guided journaling helper using the ESFG pipeline."""

    user_id: str

    def __post_init__(self) -> None:
        self.workspace_id = f"journal-{self.user_id}"
        self.dispatcher = EnhancedMRPDispatcher(self.workspace_id)
        self.parser = IntentParser()

    async def journal_entry(self, text: str, tags: List[str] | None = None) -> Dict[str, Any]:
        intent = self.parser.parse(text)
        context = PipelineContext(
            input_text=text,
            user_id=self.user_id,
            workspace_id=self.workspace_id,
            intent=intent,
            timestamp=datetime.now().isoformat(),
            metadata={"tags": tags or [], "type": "journal"},
        )
        return await self.dispatcher.dispatch(context)

    async def get_emotional_trajectory(self) -> List[Dict[str, Any]]:
        ws = Workspace(self.workspace_id)
        echo_state = ws.load_state("echo", default={})
        history = echo_state.get("history", [])
        trajectory: List[Dict[str, Any]] = []
        for entry in history:
            state = entry["quantum_state"]
            trajectory.append(
                {
                    "timestamp": entry["ts"],
                    "persona": entry["dominant"],
                    "emotional_balance": {
                        "playful": state["alpha"],
                        "analytical": state["beta"],
                        "reflective": state["gamma"],
                    },
                }
            )
        return trajectory

    async def get_growth_summary(self) -> Dict[str, Any]:
        ws = Workspace(self.workspace_id)
        garden_state = ws.load_state("garden", default={})
        limnus_state = ws.load_state("limnus", default={})
        ledger = garden_state.get("ledger", {})
        stats = limnus_state.get("memory", {}).get("stats", {})

        return {
            "journal_sessions": len(ledger.get("entries", [])),
            "ritual_cycles": ledger.get("cycle_count", 0),
            "consents_affirmed": len(ledger.get("consents", [])),
            "memory_depth": {
                "immediate": stats.get("L1_count", 0),
                "integrated": stats.get("L2_count", 0),
                "permanent": stats.get("L3_count", 0),
            },
            "emotional_trajectory": await self.get_emotional_trajectory(),
        }


async def demo_therapeutic_journal() -> None:
    journal = TherapeuticJournal("user-alice")
    await journal.journal_entry(
        "I consent to this process. I'm feeling overwhelmed by work stress.",
        tags=["stress", "work"],
    )
    await journal.journal_entry(
        "Let me debug this situation. What are the actual problems here?",
        tags=["analysis", "work"],
    )
    await journal.journal_entry(
        "Why am I resisting change? Maybe the chaos has meaning.",
        tags=["acceptance", "growth"],
    )

    summary = await journal.get_growth_summary()
    print("\n📊 Growth Summary")
    print(f"   Sessions: {summary['journal_sessions']}")
    depth = summary["memory_depth"]
    print(f"   Memory Layers: L1={depth['immediate']} L2={depth['integrated']} L3={depth['permanent']}")


if __name__ == "__main__":
    asyncio.run(demo_therapeutic_journal())
