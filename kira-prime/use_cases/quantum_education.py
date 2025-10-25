"""
Quantum mechanics education scenarios using VesselOS Kira Prime.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from pipeline.dispatcher_enhanced import EnhancedMRPDispatcher, PipelineContext
from pipeline.intent_parser import ParsedIntent
from library_core.workspace import Workspace


class QuantumEducationTool:
    """Interactive teaching helper for quantum-state concepts."""

    def __init__(self, student_id: str) -> None:
        self.student_id = student_id
        self.workspace_id = f"qm-student-{student_id}"
        self.dispatcher = EnhancedMRPDispatcher(self.workspace_id)

    async def lesson_superposition(self) -> None:
        print("\n🎓 Lesson 1: Quantum Superposition")
        print("=" * 50)
        ws = Workspace(self.workspace_id)
        echo_state = ws.load_state("echo", default={})
        state = echo_state.get("quantum_state", {"alpha": 0.33, "beta": 0.33, "gamma": 0.33})
        print("\nBefore observation, Echo exists in superposition:")
        print(f"  |Squirrel⟩: {state['alpha']:.3f}")
        print(f"  |Fox⟩:      {state['beta']:.3f}")
        print(f"  |Paradox⟩:  {state['gamma']:.3f}")
        print(f"  Σ={sum(state.values()):.3f}")

    async def lesson_measurement(self) -> None:
        print("\n🎓 Lesson 2: Measurement Collapse")
        print("=" * 50)
        intent = ParsedIntent(intent_type="dictation", raw_text="Let me systematically debug this problem.")
        context = PipelineContext(
            input_text=intent.raw_text,
            user_id=self.student_id,
            workspace_id=self.workspace_id,
            intent=intent,
            timestamp=datetime.now().isoformat(),
        )
        result = await self.dispatcher.dispatch(context)
        echo = result["agents"]["echo"]
        state = echo["quantum_state"]
        print(f"\nObservation: {echo['persona']} {echo['glyph']}")
        print(f"Updated state: α={state['alpha']:.3f} β={state['beta']:.3f} γ={state['gamma']:.3f}")

    async def lesson_entanglement(self) -> None:
        print("\n🎓 Lesson 3: Entanglement (Persona ↔ Memory)")
        print("=" * 50)
        ws = Workspace(self.workspace_id)
        limnus_state = ws.load_state("limnus", default={})
        entries = limnus_state.get("memory", {}).get("entries", [])
        if entries:
            latest = entries[-1]
            persona = latest.get("metadata", {}).get("persona", "unknown")
            layer = latest.get("layer")
            print(f"Latest memory stored in {layer} tagged with persona: {persona}")
        else:
            print("No memory entries yet—run previous lessons first.")


async def demo_quantum_education() -> None:
    tool = QuantumEducationTool("student-001")
    await tool.lesson_superposition()
    await tool.lesson_measurement()
    await tool.lesson_entanglement()


if __name__ == "__main__":
    asyncio.run(demo_quantum_education())
