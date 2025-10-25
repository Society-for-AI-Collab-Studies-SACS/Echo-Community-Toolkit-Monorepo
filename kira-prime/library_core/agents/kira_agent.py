"""Kira agent validates ledger integrity and ritual compliance."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List

from library_core.agents.base import BaseAgent


class KiraAgent(BaseAgent):
    """Validates ledger integrity and ritual compliance."""

    async def process(self, context) -> Dict[str, Any]:  # noqa: ANN001
        issues: List[str] = []
        ledger_path = self.record.path / "state" / "ledger.json"

        try:
            ledger_blocks: List[Dict[str, Any]] = json.loads(ledger_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive
            issues.append(f"Ledger read error: {exc}")
            ledger_blocks = []

        if not ledger_blocks:
            issues.append("Ledger missing or empty")
        else:
            first_block = ledger_blocks[0]
            if first_block.get("prev"):
                issues.append("Genesis block prev field should be empty")

            for index, block in enumerate(ledger_blocks):
                block_copy = {k: block[k] for k in block if k != "hash"}
                calc_hash = hashlib.sha256(
                    json.dumps(block_copy, sort_keys=True).encode("utf-8")
                ).hexdigest()
                if block.get("hash") != calc_hash:
                    issues.append(f"Hash mismatch at block {index}")

                if index > 0:
                    expected_prev = ledger_blocks[index - 1].get("hash")
                    if block.get("prev") != expected_prev:
                        issues.append(f"Broken prev link at block {index}")
                    try:
                        prev_ts = datetime.fromisoformat(
                            ledger_blocks[index - 1]["ts"].replace("Z", "+00:00")
                        )
                        curr_ts = datetime.fromisoformat(block["ts"].replace("Z", "+00:00"))
                        if curr_ts < prev_ts:
                            issues.append(f"Timestamp out of order at block {index}")
                    except Exception:  # pragma: no cover - defensive
                        pass

        garden_state = await self.get_state("garden")
        ledger = garden_state.get("ledger", {})
        entries = ledger.get("entries", [])
        if not any(entry.get("kind") == "consent" for entry in entries):
            issues.append("No consent recorded in ritual ledger")

        # Coherence check: ensure glyph is present in styled text
        echo_state = context.agent_results.get("echo", {})
        styled = echo_state.get("styled_text", "")
        glyph = echo_state.get("glyph", "")
        coherence_ok = bool(glyph and glyph in styled)

        passed = not issues and coherence_ok
        context.metadata["validation_passed"] = passed
        context.metadata["issue_count"] = len(issues)

        # Summarise checks (coarse): ledger integrity, chain continuity, consent present
        total_checks = 3
        passed_checks = total_checks if passed else max(0, total_checks - min(len(issues), total_checks))

        await self.append_log("kira", {"passed": passed, "issues": len(issues)})
        checks = {
            "ledger_chain": not any("hash" in i.lower() or "prev" in i.lower() or "chain" in i.lower() for i in issues),
            "coherence": coherence_ok,
        }
        return {
            "passed": passed,
            "issues": issues,
            "summary": {"passed_checks": passed_checks, "total_checks": total_checks},
            "checks": checks,
        }
