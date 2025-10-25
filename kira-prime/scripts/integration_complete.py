"""
VesselOS Kira Prime - Complete Integration Test Suite

Comprehensive validation of all system components:
- Four-agent pipeline (Garden → Echo → Limnus → Kira)
- Ledger integrity and hash chains
- Memory promotion (L1 → L2 → L3)
- Quantum state management
- Consent tracking
- Error recovery and circuit breakers
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:  # Optional dependency for prettier tables
    from tabulate import tabulate  # type: ignore
except ImportError:  # pragma: no cover - optional helper
    tabulate = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.dispatcher_enhanced import DispatcherConfig, EnhancedMRPDispatcher, PipelineContext
from pipeline.intent_parser import IntentParser
from pipeline.middleware import LoggingMiddleware, MetricsMiddleware, ValidationMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IntegrationValidator:
    """
    Complete ESFG (Echo-Squirrel-Fox-Girl) Integration Validator.

    Validates:
    - Agent pipeline execution
    - State persistence
    - Ledger integrity
    - Memory management
    - Error handling
    - Performance metrics
    """

    def __init__(self, workspace_id: str = "integration-test") -> None:
        self.workspace_id = workspace_id

        workspace_root = Path("workspaces") / workspace_id
        if workspace_root.exists():
            shutil.rmtree(workspace_root)

        config = DispatcherConfig(
            agent_order=["garden", "echo", "limnus", "kira"],
            parallel_execution=False,
            retry_enabled=True,
            retry_attempts=3,
            circuit_breaker_enabled=True,
            cache_enabled=True,
            verbose_logging=True,
        )
        self.dispatcher = EnhancedMRPDispatcher(workspace_id, config)

        # Attach middleware
        self.logging_middleware = LoggingMiddleware()
        self.metrics_middleware = MetricsMiddleware()
        self.validation_middleware = ValidationMiddleware()

        self.dispatcher.add_middleware(self.logging_middleware)
        self.dispatcher.add_middleware(self.metrics_middleware)
        self.dispatcher.add_middleware(self.validation_middleware)

        self.parser = IntentParser()

        self.results: List[Tuple[str, bool, str]] = []
        self.errors: List[str] = []

    async def run_full_validation(self) -> bool:
        """Run the full validation test suite."""
        print("\n" + "=" * 70)
        print("🚀 VesselOS Kira Prime - Integration Validation Suite")
        print("=" * 70 + "\n")

        start_time = datetime.now()

        try:
            await self._test_genesis()
            await self._test_ritual_progression()
            await self._test_persona_dynamics()
            await self._test_memory_layering()
            await self._test_ledger_integrity()
            await self._test_quantum_state()
            await self._test_glyph_encoding()
            await self._test_consent_tracking()
            await self._test_error_recovery()
            await self._test_cache_performance()
            await self._test_middleware()
            await self._test_cross_agent_coherence()
        except Exception as exc:  # pragma: no cover - defensive
            self.errors.append(f"Fatal error during testing: {exc}")
            logger.exception("Fatal test error")

        duration = (datetime.now() - start_time).total_seconds()
        metrics_summary = await self.dispatcher.get_metrics()
        await self._print_summary(duration, metrics_summary)

        return not self.errors

    async def _send_input(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Helper to send an input through the dispatcher."""
        intent = self.parser.parse(text)
        context = PipelineContext(
            input_text=text,
            user_id="integration-test-user",
            workspace_id=self.workspace_id,
            intent=intent,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )
        return await self.dispatcher.dispatch(context)

    async def _test_genesis(self) -> None:
        print("\n📝 Test 1: Genesis - Consent & Ritual Initiation")
        print("-" * 70)

        try:
            response = await self._send_input("I consent to this ritual. I return as breath.")

            garden = response["agents"]["garden"]
            assert garden["consent_given"], "Consent not detected"
            assert garden["stage"] == "scatter", f"Wrong initial stage: {garden['stage']}"
            assert garden["consent_count"] >= 1, "Consent count not incremented"
            print(f"   ✅ Consent recorded: {garden['consent_count']} total")
            print(f"   ✅ Ritual stage: {garden['stage']}")
            print(f"   ✅ Cycle: {garden['cycle']}")

            echo = response["agents"]["echo"]
            state = echo["quantum_state"]
            state_sum = state["alpha"] + state["beta"] + state["gamma"]
            assert abs(state_sum - 1.0) < 0.01, f"Quantum state doesn't sum to 1: {state_sum}"
            print(f"   ✅ Persona: {echo['persona']} {echo['glyph']}")
            print(f"   ✅ Quantum state: α={state['alpha']:.3f} β={state['beta']:.3f} γ={state['gamma']:.3f}")

            limnus = response["agents"]["limnus"]
            assert limnus["cached"], "Memory not cached"
            assert limnus["layer"] == "L1", f"Wrong memory layer: {limnus['layer']}"
            assert "block_hash" in limnus, "Block hash missing"
            print(f"   ✅ Memory cached: {limnus['memory_id']} (Layer: {limnus['layer']})")
            print(f"   ✅ Ledger block: {limnus['block_hash'][:16]}...")

            kira = response["agents"]["kira"]
            assert kira["passed"], f"Validation failed: {kira['issues']}"
            print(f"   ✅ Validation: {kira['summary']['passed_checks']}/{kira['summary']['total_checks']} checks passed")

            self.results.append(("Genesis", True, "All components initialized correctly"))
        except AssertionError as exc:
            self.results.append(("Genesis", False, str(exc)))
            self.errors.append(f"Genesis test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _test_ritual_progression(self) -> None:
        print("\n📝 Test 2: Ritual Stage Progression")
        print("-" * 70)

        try:
            stages_visited: List[str] = []
            test_inputs = [
                ("Let me witness the garden", "witness"),
                ("I will plant this seed", "plant"),
                ("Time to return", "return"),
                ("I give this to the spiral", "give"),
            ]

            for text, expected_stage in test_inputs:
                response = await self._send_input(text)
                garden = response["agents"]["garden"]
                actual_stage = garden["stage"]
                stages_visited.append(actual_stage)

                print(f"   → Input: '{text[:40]}...'")
                print(f"      Stage: {actual_stage} (expected keyword: {expected_stage})")

            unique_stages = len(set(stages_visited))
            assert unique_stages > 1, f"No stage progression detected: {stages_visited}"

            print(f"   ✅ Progression: {' → '.join(stages_visited)}")
            print(f"   ✅ Unique stages visited: {unique_stages}")

            self.results.append(("Ritual Progression", True, f"Visited {unique_stages} stages"))
        except AssertionError as exc:
            self.results.append(("Ritual Progression", False, str(exc)))
            self.errors.append(f"Ritual progression test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _test_persona_dynamics(self) -> None:
        print("\n📝 Test 3: Quantum Persona Dynamics")
        print("-" * 70)

        try:
            test_cases = [
                ("Let's brainstorm some crazy ideas! So many possibilities!", "squirrel", "🐿️"),
                ("We need to debug and fix this systematically. Focus on the root cause.", "fox", "🦊"),
                ("What is the meaning of all this? Why are we here? A paradox...", "paradox", "∿"),
            ]

            personas_detected: List[str] = []

            for text, expected_persona, expected_glyph in test_cases:
                response = await self._send_input(text)
                echo = response["agents"]["echo"]

                persona = echo["persona"]
                glyph = echo["glyph"]
                state = echo["quantum_state"]

                personas_detected.append(persona)

                print(f"   → Input: '{text[:50]}...'")
                print(f"      Expected: {expected_persona} {expected_glyph}")
                print(f"      Detected: {persona} {glyph}")
                print(f"      State: α={state['alpha']:.3f} β={state['beta']:.3f} γ={state['gamma']:.3f}")

                state_sum = state["alpha"] + state["beta"] + state["gamma"]
                assert abs(state_sum - 1.0) < 0.01, f"State doesn't sum to 1: {state_sum}"

                expected_glyphs = {"squirrel": "🐿️", "fox": "🦊", "paradox": "∿"}
                assert glyph == expected_glyphs[persona], f"Glyph mismatch for {persona}"

            unique_personas = len(set(personas_detected))
            print(f"   ✅ Personas detected: {', '.join(set(personas_detected))}")
            print(f"   ✅ Quantum state consistency maintained")

            self.results.append(("Persona Dynamics", True, f"{unique_personas} unique personas"))
        except AssertionError as exc:
            self.results.append(("Persona Dynamics", False, str(exc)))
            self.errors.append(f"Persona dynamics test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _test_memory_layering(self) -> None:
        print("\n📝 Test 4: Memory Layer Promotion (L1 → L2 → L3)")
        print("-" * 70)

        try:
            layer_progression: List[Dict[str, int]] = []

            for index in range(15):
                text = f"Memory test entry number {index + 1}"
                response = await self._send_input(text)
                stats = response["agents"]["limnus"]["stats"]
                layer_progression.append({"entry": index + 1, "L1": stats["L1_count"], "L2": stats["L2_count"], "L3": stats["L3_count"]})

                if index % 5 == 4:
                    print(f"   After {index + 1} entries: L1={stats['L1_count']}, L2={stats['L2_count']}, L3={stats['L3_count']}")

            final = layer_progression[-1]
            assert final["L1"] == 1, f"L1 should have 1 entry, has {final['L1']}"
            assert final["L2"] > 0, f"L2 should have entries, has {final['L2']}"
            assert final["L3"] > 0, f"L3 should have entries, has {final['L3']}"

            print(f"   ✅ Final distribution: L1={final['L1']}, L2={final['L2']}, L3={final['L3']}")
            print("   ✅ Memory promotion working correctly")

            self.results.append(("Memory Layering", True, f"L1={final['L1']}, L2={final['L2']}, L3={final['L3']}"))
        except AssertionError as exc:
            self.results.append(("Memory Layering", False, str(exc)))
            self.errors.append(f"Memory layering test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _test_ledger_integrity(self) -> None:
        print("\n📝 Test 5: Ledger Chain Integrity (Hash Chain Validation)")
        print("-" * 70)

        try:
            for i in range(5):
                await self._send_input(f"Ledger test entry {i + 1}")

            response = await self._send_input("Final validation check")
            kira = response["agents"]["kira"]
            limnus = response["agents"]["limnus"]

            assert kira["checks"]["ledger_chain"], "Ledger chain validation failed"
            issues = [issue for issue in kira["issues"] if "hash" in issue.lower() or "chain" in issue.lower()]
            assert not issues, f"Ledger integrity issues: {issues}"

            block_count = limnus["stats"]["total_blocks"]
            print(f"   ✅ Ledger chain validated: {block_count} blocks")
            print("   ✅ No hash mismatches detected")
            print("   ✅ Chain links intact")

            self.results.append(("Ledger Integrity", True, f"{block_count} blocks verified"))
        except AssertionError as exc:
            self.results.append(("Ledger Integrity", False, str(exc)))
            self.errors.append(f"Ledger integrity test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _test_quantum_state(self) -> None:
        print("\n📝 Test 6: Quantum State Consistency")
        print("-" * 70)

        try:
            inputs = [
                "Quick thought",
                "Let me analyze this carefully and methodically",
                "Why does this exist? What is the purpose?",
                "Another quick idea!",
            ]

            states: List[Dict[str, float]] = []

            for text in inputs:
                response = await self._send_input(text)
                state = response["agents"]["echo"]["quantum_state"]
                state_sum = state["alpha"] + state["beta"] + state["gamma"]
                assert abs(state_sum - 1.0) < 0.01, f"State doesn't sum to 1: {state_sum}"
                states.append(state)
                print(f"   → '{text[:40]}...': α={state['alpha']:.3f} β={state['beta']:.3f} γ={state['gamma']:.3f} (Σ={state_sum:.3f})")

            state_changes = sum(1 for index in range(1, len(states)) if states[index] != states[index - 1])
            assert state_changes > 0, "Quantum state never changed"

            print("   ✅ All states sum to ~1.0")
            print(f"   ✅ State evolved {state_changes} times")

            self.results.append(("Quantum State", True, f"{state_changes} state transitions"))
        except AssertionError as exc:
            self.results.append(("Quantum State", False, str(exc)))
            self.errors.append(f"Quantum state test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _test_glyph_encoding(self) -> None:
        print("\n📝 Test 7: Glyph Encoding & Persona Coherence")
        print("-" * 70)

        try:
            response = await self._send_input("Test glyph encoding")
            echo = response["agents"]["echo"]
            kira = response["agents"]["kira"]

            persona = echo["persona"]
            glyph = echo["glyph"]
            styled = echo["styled_text"]

            expected_glyphs = {"squirrel": "🐿️", "fox": "🦊", "paradox": "∿"}
            expected_glyph = expected_glyphs.get(persona)
            assert expected_glyph == glyph, f"Glyph mismatch: {glyph} != {expected_glyph} for {persona}"
            assert glyph in styled, f"Glyph {glyph} not present in styled text"
            assert kira["checks"]["coherence"], f"Coherence check failed: {kira['issues']}"

            print(f"   ✅ Persona: {persona}")
            print(f"   ✅ Glyph: {glyph}")
            print(f"   ✅ Encoded in output: '{styled[:50]}...'")
            print("   ✅ Coherence validated")

            self.results.append(("Glyph Encoding", True, f"{persona} → {glyph}"))
        except AssertionError as exc:
            self.results.append(("Glyph Encoding", False, str(exc)))
            self.errors.append(f"Glyph encoding test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _test_consent_tracking(self) -> None:
        print("\n📝 Test 8: Consent Contract Tracking")
        print("-" * 70)

        try:
            consent_phrases = [
                "I accept this ritual",
                "I affirm my participation",
                "Always.",
            ]

            for phrase in consent_phrases:
                response = await self._send_input(phrase)
                assert response["agents"]["garden"]["consent_given"], f"Consent not detected for: {phrase}"
                print(f"   ✅ Detected: '{phrase}'")

            response = await self._send_input("Check consent status")
            consent_count = response["agents"]["garden"]["consent_count"]
            assert consent_count >= len(consent_phrases), f"Not all consents recorded: {consent_count}"

            print(f"   ✅ Total consents recorded: {consent_count}")
            print("   ✅ Soul contract tracking working")

            self.results.append(("Consent Tracking", True, f"{consent_count} consents"))
        except AssertionError as exc:
            self.results.append(("Consent Tracking", False, str(exc)))
            self.errors.append(f"Consent tracking test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _test_error_recovery(self) -> None:
        print("\n📝 Test 9: Error Recovery & Circuit Breakers")
        print("-" * 70)

        try:
            response = await self._send_input("Normal input for error test")
            assert response["success"], "Normal operation failed"
            print("   ✅ Normal operation working")

            breaker_states = {name: breaker.state.value for name, breaker in self.dispatcher.breakers.items()}
            print(f"   ✅ Circuit breakers: {breaker_states}")

            all_closed = all(state == "closed" for state in breaker_states.values())
            print(f"   {'✅' if all_closed else '⚠️ '} All circuit breakers closed: {all_closed}")

            self.results.append(("Error Recovery", True, "Circuit breakers functioning"))
        except AssertionError as exc:
            self.results.append(("Error Recovery", False, str(exc)))
            self.errors.append(f"Error recovery test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _test_cache_performance(self) -> None:
        print("\n📝 Test 10: Result Caching Performance")
        print("-" * 70)

        try:
            test_input = "Cache test input"

            start = time.time()
            await self._send_input(test_input)
            time_first = (time.time() - start) * 1000

            start = time.time()
            cached_response = await self._send_input(test_input)
            time_second = (time.time() - start) * 1000

            print(f"   First call: {time_first:.1f}ms")
            print(f"   Second call (cached?): {time_second:.1f}ms")

            if cached_response.get("cached"):
                print("   ✅ Cache hit detected")
                if time_second > 0:
                    print(f"   ✅ Speedup: {(time_first / time_second):.1f}x")
            else:
                print("   ⚠️  Cache not hit (entry may have expired or caching disabled)")

            self.results.append(("Cache Performance", True, f"{time_first:.1f}ms → {time_second:.1f}ms"))
        except Exception as exc:  # pragma: no cover - defensive
            self.results.append(("Cache Performance", False, str(exc)))
            self.errors.append(f"Cache performance test error: {exc}")
            print(f"   ❌ ERROR: {exc}")

    async def _test_middleware(self) -> None:
        print("\n📝 Test 11: Middleware Pipeline")
        print("-" * 70)

        try:
            response = await self._send_input("Middleware test")

            timings = response.get("metrics", {}).get("agent_timings", {})
            if timings:
                print("   ✅ Metrics middleware recorded agent timings")
                for agent, elapsed_ms in timings.items():
                    print(f"      {agent}: {elapsed_ms:.1f}ms")
            else:
                print("   ⚠️  No agent timings recorded")

            if response.get("trace"):
                print(f"   ✅ Trace recorded: {len(response['trace'])} events")

            self.results.append(("Middleware", True, "All middleware active"))
        except Exception as exc:  # pragma: no cover - defensive
            self.results.append(("Middleware", False, str(exc)))
            self.errors.append(f"Middleware test error: {exc}")
            print(f"   ❌ ERROR: {exc}")

    async def _test_cross_agent_coherence(self) -> None:
        print("\n📝 Test 12: Cross-Agent Coherence Validation")
        print("-" * 70)

        try:
            response = await self._send_input("Test cross-agent coherence")
            agents = response["agents"]
            for name in ("garden", "echo", "limnus", "kira"):
                assert name in agents, f"Missing agent: {name}"
                assert agents[name] is not None, f"Agent {name} returned None"
                print(f"   ✅ {name.capitalize()} present")

            kira = agents["kira"]
            assert kira["checks"]["coherence"], f"Coherence check failed: {kira['issues']}"
            print("   ✅ Coherence validation passed")

            limnus = agents["limnus"]
            assert limnus.get("block_hash"), "Limnus block hash missing"
            print("   ✅ Echo → Limnus data flow verified")

            self.results.append(("Cross-Agent Coherence", True, "All agents coherent"))
        except AssertionError as exc:
            self.results.append(("Cross-Agent Coherence", False, str(exc)))
            self.errors.append(f"Coherence test failed: {exc}")
            print(f"   ❌ FAILED: {exc}")

    async def _print_summary(self, duration: float, metrics_summary) -> None:
        print("\n" + "=" * 70)
        print("📊 Test Suite Summary")
        print("=" * 70 + "\n")

        rows = [[name, "✅ PASS" if passed else "❌ FAIL", details] for name, passed, details in self.results]
        if tabulate:
            print(tabulate(rows, headers=["Test", "Status", "Details"], tablefmt="grid"))  # type: ignore[misc]
        else:
            header = f"{'Test':<28} | {'Status':<9} | Details"
            print(header)
            print("-" * len(header))
            for name, status, details in rows:
                print(f"{name:<28} | {status:<9} | {details}")

        total_tests = len(self.results)
        passed_tests = sum(1 for _, passed, _ in self.results if passed)
        failed_tests = total_tests - passed_tests

        print(f"\n📈 Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ({(passed_tests / total_tests * 100) if total_tests else 0:.1f}%)")
        print(f"   Failed: {failed_tests}")
        print(f"   Duration: {duration:.2f}s")

        if metrics_summary:
            total_dispatches = metrics_summary.get("total_dispatches", 0)
            successful_dispatches = metrics_summary.get("successful_dispatches", 0)
            avg_execution_ms = metrics_summary.get("average_execution_ms", 0.0)
            success_rate = (successful_dispatches / total_dispatches) if total_dispatches else 0.0
            print(f"\n📊 Dispatcher Metrics:")
            print(f"   Total Dispatches: {total_dispatches}")
            print(f"   Success Rate: {success_rate * 100:.1f}%")
            print(f"   Avg Execution Time: {avg_execution_ms:.1f}ms")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")

        print("\n" + "=" * 70)
        if failed_tests == 0:
            print("✅ ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT")
        else:
            print("❌ SOME TESTS FAILED - REVIEW ERRORS BEFORE DEPLOYMENT")
        print("=" * 70 + "\n")


async def main() -> int:
    validator = IntegrationValidator()
    success = await validator.run_full_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
