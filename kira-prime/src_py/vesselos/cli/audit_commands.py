"""CLI Audit Commands for VesselOS Kira Prime."""

from __future__ import annotations

import asyncio
from typing import Iterable, Sequence

import click

try:  # Optional dependency for prettier output
    from tabulate import tabulate  # type: ignore
except ImportError:  # pragma: no cover - optional helper
    tabulate = None  # type: ignore

from library_core.workspace import Workspace
from pipeline.dispatcher_enhanced import EnhancedMRPDispatcher


def _render_table(rows: Sequence[Sequence[str]], headers: Iterable[str]) -> None:
    if tabulate:
        click.echo(tabulate(rows, headers=headers, tablefmt="grid"))  # type: ignore[misc]
        return

    header_line = " | ".join(headers)
    click.echo(header_line)
    click.echo("-" * len(header_line))
    for row in rows:
        click.echo(" | ".join(str(cell) for cell in row))


@click.group()
def audit() -> None:
    """System auditing and health checks."""


@audit.command()
@click.option("--workspace", default="default", help="Workspace ID")
def health(workspace: str) -> None:
    """Complete system health check."""

    async def _health() -> None:
        click.echo("\n🏥 VesselOS Kira Prime - Health Check")
        click.echo("=" * 60 + "\n")

        ws = Workspace(workspace)

        checks = []

        try:
            garden_state = ws.load_state("garden", default={})
            ledger = garden_state.get("ledger", {})
            entry_count = len(ledger.get("entries", []))
            consent_count = len(ledger.get("consents", []))
            checks.append(("Garden Ledger", "✅ OK", f"{entry_count} entries, {consent_count} consents"))
        except Exception as exc:  # pragma: no cover - defensive
            checks.append(("Garden Ledger", "❌ FAIL", str(exc)))

        try:
            echo_state = ws.load_state("echo", default={})
            quantum_state = echo_state.get("quantum_state", {})
            if quantum_state:
                total = sum(quantum_state.values())
                status = "✅ OK" if abs(total - 1.0) < 0.01 else "⚠️  WARNING"
                checks.append(("Echo Quantum State", status, f"Σ={total:.3f}"))
            else:
                checks.append(("Echo Quantum State", "⚠️  WARNING", "Not initialized"))
        except Exception as exc:  # pragma: no cover - defensive
            checks.append(("Echo Quantum State", "❌ FAIL", str(exc)))

        try:
            limnus_state = ws.load_state("limnus", default={})
            memory = limnus_state.get("memory", {})
            stats = memory.get("stats", {})
            checks.append(
                (
                    "Limnus Memory",
                    "✅ OK",
                    f"L1={stats.get('L1_count',0)}, L2={stats.get('L2_count',0)}, L3={stats.get('L3_count',0)}",
                )
            )
        except Exception as exc:  # pragma: no cover - defensive
            checks.append(("Limnus Memory", "❌ FAIL", str(exc)))

        try:
            limnus_state = ws.load_state("limnus", default={})
            blocks = limnus_state.get("ledger", {}).get("blocks", [])
            issues = []
            for index in range(1, len(blocks)):
                if blocks[index].get("prev") != blocks[index - 1].get("hash"):
                    issues.append(f"Block {index} chain broken")
            if issues:
                checks.append(("Limnus Ledger", "❌ FAIL", ", ".join(issues)))
            else:
                checks.append(("Limnus Ledger", "✅ OK", f"{len(blocks)} blocks, chain intact"))
        except Exception as exc:  # pragma: no cover - defensive
            checks.append(("Limnus Ledger", "❌ FAIL", str(exc)))

        _render_table(checks, headers=["Component", "Status", "Details"])

        failed = sum(1 for _, status, _ in checks if "FAIL" in status)
        warnings = sum(1 for _, status, _ in checks if "WARNING" in status)
        click.echo(f"\n📊 Summary: {len(checks)} checks, {failed} failures, {warnings} warnings")
        click.echo("\n✅ System health: GOOD" if failed == 0 else "\n❌ System health: NEEDS ATTENTION")

    asyncio.run(_health())


@audit.command()
@click.option("--workspace", default="default", help="Workspace ID")
@click.option("--verbose", is_flag=True, help="Show detailed ledger entries")
def ledger(workspace: str, verbose: bool) -> None:
    """Audit Garden and Limnus ledgers."""

    async def _ledger() -> None:
        click.echo("\n📖 Ledger Audit")
        click.echo("=" * 60 + "\n")

        ws = Workspace(workspace)

        click.echo("🌿 Garden Ritual Ledger:")
        click.echo("-" * 60)
        garden_state = ws.load_state("garden", default={})
        ledger_data = garden_state.get("ledger", {})
        entries = ledger_data.get("entries", [])
        click.echo(f"Total entries: {len(entries)}")
        click.echo(f"Current stage: {ledger_data.get('current_stage', 'unknown')}")
        click.echo(f"Cycle count: {ledger_data.get('cycle_count', 0)}")
        click.echo(f"Consents: {len(ledger_data.get('consents', []))}")

        if verbose and entries:
            click.echo("\nRecent entries:")
            for entry in entries[-5:]:
                click.echo(f"  [{entry['ts']}] {entry['kind']}: {entry['stage']}")

        click.echo("\n💾 Limnus Memory Ledger:")
        click.echo("-" * 60)
        limnus_state = ws.load_state("limnus", default={})
        ledger_data = limnus_state.get("ledger", {})
        blocks = ledger_data.get("blocks", [])
        click.echo(f"Total blocks: {len(blocks)}")
        if blocks:
            click.echo(f"Genesis: {blocks[0].get('ts')}")
            click.echo(f"Latest: {blocks[-1].get('ts')}")
            click.echo(f"Latest hash: {blocks[-1].get('hash', '')[:16]}...")

        issues = []
        for index in range(1, len(blocks)):
            if blocks[index].get("prev") != blocks[index - 1].get("hash"):
                issues.append(str(index))
        if issues:
            click.echo(f"\n❌ Chain integrity issues at blocks: {', '.join(issues)}")
        else:
            click.echo("\n✅ Chain integrity: VERIFIED")

        if verbose and blocks:
            click.echo("\nRecent blocks:")
            for block in blocks[-5:]:
                data = block.get("data", {})
                glyph = data.get("glyph", "")
                persona = data.get("persona", "")
                click.echo(f"  [{block['ts']}] {glyph} {persona}")

    asyncio.run(_ledger())


@audit.command()
@click.option("--workspace", default="default", help="Workspace ID")
def memory(workspace: str) -> None:
    """Audit memory layers and stats."""

    async def _memory() -> None:
        click.echo("\n💾 Memory System Audit")
        click.echo("=" * 60 + "\n")

        ws = Workspace(workspace)
        limnus_state = ws.load_state("limnus", default={})
        memory = limnus_state.get("memory", {})
        entries = memory.get("entries", [])
        stats = memory.get("stats", {})

        click.echo("📊 Layer Distribution:")
        click.echo(f"   L1 (Immediate):  {stats.get('L1_count', 0)} entries")
        click.echo(f"   L2 (Enduring):   {stats.get('L2_count', 0)} entries")
        click.echo(f"   L3 (Permanent):  {stats.get('L3_count', 0)} entries")
        click.echo(f"   Total:           {len(entries)} entries")
        click.echo(f"   Promotions:      {stats.get('total_promotions', 0)}")

        if entries:
            click.echo("\n📝 Recent Memories:")
            for entry in entries[-5:]:
                layer = entry.get("layer", "?")
                text = entry.get("text", "")[:50]
                click.echo(f"   [{layer}] {text}...")

        click.echo("\n🏥 Layer Health:")
        l1 = stats.get("L1_count", 0)
        l2 = stats.get("L2_count", 0)
        click.echo("   ✅ L1 capacity correct (1 entry)" if l1 == 1 else f"   ⚠️  L1 capacity incorrect ({l1} entries, expected 1)")
        click.echo(f"   ✅ L2 within capacity ({l2}/10)" if l2 <= 10 else f"   ⚠️  L2 over capacity ({l2}/10)")

    asyncio.run(_memory())


@audit.command()
@click.option("--workspace", default="default", help="Workspace ID")
def personas(workspace: str) -> None:
    """Audit quantum persona states."""

    async def _personas() -> None:
        click.echo("\n🎭 Quantum Persona Audit")
        click.echo("=" * 60 + "\n")

        ws = Workspace(workspace)
        echo_state = ws.load_state("echo", default={})
        quantum_state = echo_state.get("quantum_state", {})
        history = echo_state.get("history", [])

        if not quantum_state:
            click.echo("⚠️  No quantum state found")
            return

        alpha = quantum_state.get("alpha", 0.0)
        beta = quantum_state.get("beta", 0.0)
        gamma = quantum_state.get("gamma", 0.0)
        total = alpha + beta + gamma

        click.echo("📊 Current Quantum State:")
        click.echo(f"   α (Squirrel 🐿️):  {alpha:.3f} ({alpha*100:.1f}%)")
        click.echo(f"   β (Fox 🦊):       {beta:.3f} ({beta*100:.1f}%)")
        click.echo(f"   γ (Paradox ∿):    {gamma:.3f} ({gamma*100:.1f}%)")
        click.echo(f"   Sum:              {total:.3f}")
        click.echo("   ✅ State normalized correctly" if abs(total - 1.0) < 0.01 else "   ❌ State not normalized!")

        if alpha >= beta and alpha >= gamma:
            dominant = "Squirrel 🐿️"
        elif beta > alpha and beta >= gamma:
            dominant = "Fox 🦊"
        else:
            dominant = "Paradox ∿"
        click.echo(f"\n🎭 Dominant Persona: {dominant}")

        if history:
            click.echo(f"\n📜 State History: {len(history)} transitions")
            if len(history) >= 5:
                click.echo("\n   Recent transitions:")
                for state in history[-5:]:
                    qs = state["quantum_state"]
                    persona = state["dominant"]
                    click.echo(f"      {persona}: α={qs['alpha']:.3f} β={qs['beta']:.3f} γ={qs['gamma']:.3f}")

    asyncio.run(_personas())


@audit.command()
@click.option("--workspace", default="default", help="Workspace ID")
def consents(workspace: str) -> None:
    """Audit consent contracts."""

    async def _consents() -> None:
        click.echo("\n📜 Soul Contract Audit")
        click.echo("=" * 60 + "\n")

        ws = Workspace(workspace)
        ledger = ws.load_state("garden", default={}).get("ledger", {})
        consents = ledger.get("consents", [])
        if not consents:
            click.echo("⚠️  No consents recorded")
            click.echo("   Soul contract not yet established")
            return

        click.echo(f"Total consents: {len(consents)}")
        click.echo("\nConsent Records:")
        for consent in consents:
            ts = consent.get("ts", "unknown")
            phrase = consent.get("phrase", "")
            user = consent.get("user_id", "unknown")
            click.echo(f"   [{ts}] {user}: '{phrase}'")
        click.echo(f"\n✅ Soul contract established with {len(consents)} affirmations")

    asyncio.run(_consents())


@audit.command()
@click.option("--workspace", default="default", help="Workspace ID")
def performance(workspace: str) -> None:
    """Performance metrics and benchmarks."""

    async def _performance() -> None:
        click.echo("\n⚡ Performance Audit")
        click.echo("=" * 60 + "\n")

        dispatcher = EnhancedMRPDispatcher(workspace)
        metrics = await dispatcher.get_metrics()
        if not metrics:
            click.echo("⚠️  No metrics available")
            return

        total = metrics.get("total_dispatches", 0)
        success = metrics.get("successful_dispatches", 0)
        failed = metrics.get("failed_dispatches", 0)
        success_rate = (success / total) * 100 if total else 0.0
        avg_ms = metrics.get("average_execution_ms", 0.0)

        click.echo("📊 Dispatch Metrics:")
        click.echo(f"   Total:        {total}")
        click.echo(f"   Successful:   {success}")
        click.echo(f"   Failed:       {failed}")
        click.echo(f"   Success Rate: {success_rate:.1f}%")

        click.echo("\n⏱️  Execution Times:")
        click.echo(f"   Average: {avg_ms:.1f}ms")

        agent_metrics = metrics.get("agent_metrics", {})
        if agent_metrics:
            click.echo("\n🤖 Per-Agent Performance:")
            for agent, stats in agent_metrics.items():
                executions = stats.get("executions", 0)
                avg = stats.get("avg_ms", 0.0)
                errors = stats.get("errors", 0)
                click.echo(f"   {agent}: {executions} execs, avg {avg:.1f}ms, errors {errors}")

        cache_stats = metrics.get("cache_stats", {})
        if cache_stats:
            hits = cache_stats.get("hits", 0)
            misses = cache_stats.get("misses", 0)
            hit_rate = cache_stats.get("hit_rate", 0.0) * 100
            click.echo("\n💾 Cache Performance:")
            click.echo(f"   Hits:     {hits}")
            click.echo(f"   Misses:   {misses}")
            click.echo(f"   Hit Rate: {hit_rate:.1f}%")

    asyncio.run(_performance())


@audit.command()
@click.option("--workspace", default="default", help="Workspace ID")
@click.pass_context
def full(ctx: click.Context, workspace: str) -> None:
    """Run complete system audit."""
    click.echo("\n🔍 Full System Audit")
    click.echo("=" * 60 + "\n")
    click.echo("Running all audit checks...\n")

    ctx.invoke(health, workspace=workspace)
    click.echo()
    ctx.invoke(ledger, workspace=workspace, verbose=False)
    click.echo()
    ctx.invoke(memory, workspace=workspace)
    click.echo()
    ctx.invoke(personas, workspace=workspace)
    click.echo()
    ctx.invoke(consents, workspace=workspace)
    click.echo()
    ctx.invoke(performance, workspace=workspace)

    click.echo("\n" + "=" * 60)
    click.echo("✅ Full audit complete")
    click.echo("=" * 60 + "\n")


if __name__ == "__main__":
    audit()
