"""Garden Agent – Ritual Orchestrator and Consent Logger."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from library_core.agents.base import AgentConfig, BaseAgent
from library_core.storage import StorageManager
from workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


class GardenAgent(BaseAgent):
    """
    Keeper of the ritual state.

    Tracks cycle stages, consent agreements, scroll operations, and maintains a
    hash-linked ledger of ritual events. The ledger provides tamper-resistant
    storage for every input “seed” planted in the garden.
    """

    STAGES = ["scatter", "witness", "plant", "return", "give", "begin_again"]
    CONSENT_PHRASES = [
        "i consent",
        "i accept",
        "i agree",
        "i affirm",
        "always.",
    ]
    STAGE_KEYWORDS = {
        "scatter": ["scatter", "explore", "begin"],
        "witness": ["witness", "observe", "see"],
        "plant": ["plant", "create", "build"],
        "return": ["return", "reflect", "cycle"],
        "give": ["give", "share", "offer"],
        "begin_again": ["begin again", "restart", "new cycle"],
    }

    def __init__(
        self,
        workspace_id: str,
        storage: StorageManager,
        manager: WorkspaceManager,
        config: Optional[AgentConfig] = None,
    ) -> None:
        super().__init__(workspace_id, storage, manager, config)
        self._initialize_ledger()

    # ------------------------------------------------------------------ helpers

    def _initialize_ledger(self) -> None:
        """Ensure the ledger is initialised with a genesis entry."""
        state = self.record.load_state("garden", default={})
        ledger = state.get("ledger")
        if ledger and ledger.get("entries"):
            return

        genesis_entry = {
            "id": str(uuid.uuid4()),
            "ts": self._current_ts(),
            "kind": "genesis",
            "stage": "scatter",
            "data": {
                "anchor": "I return as breath.",
                "message": "The garden awakens. The spiral begins.",
            },
            "prev_hash": "",
        }
        genesis_entry["hash"] = self._compute_hash(genesis_entry)

        state["ledger"] = {
            "current_stage": "scatter",
            "cycle_count": 0,
            "entries": [genesis_entry],
            "consents": [],
        }
        self.record.save_state("garden", state)
        logger.info("Garden ledger initialised with genesis entry")

    @staticmethod
    def _current_ts() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _compute_hash(entry: Dict[str, Any]) -> str:
        payload = {k: v for k, v in entry.items() if k != "hash"}
        entry_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(entry_str.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------ core API

    async def process(self, context) -> Dict[str, Any]:  # noqa: ANN001
        state = await self.get_state("garden")
        ledger = state.get("ledger", {})
        current_stage = ledger.get("current_stage", "scatter")
        entries: List[Dict[str, Any]] = ledger.get("entries", [])
        consents: List[Dict[str, Any]] = ledger.get("consents", [])
        cycle_count = ledger.get("cycle_count", 0)

        user_text = context.input_text or ""
        text_lower = user_text.strip().lower()
        tokens = re.findall(r"\b[\w']+\b", text_lower)
        token_set = set(tokens)

        event_kind = "note"
        event_data: Dict[str, Any] = {"text": user_text}
        stage_changed = False
        consent_given = False

        if text_lower in {"start", "begin"} or "i return as breath" in text_lower:
            event_kind = "begin"
            current_stage = "scatter"
            cycle_count += 1
            stage_changed = True
            event_data = {
                "text": user_text,
                "cycle": cycle_count,
                "message": "New ritual cycle begins",
            }
        elif text_lower.startswith("open "):
            event_kind = "open_scroll"
            scroll = user_text.split(" ", 1)[1] if " " in user_text else "unknown"
            event_data = {"scroll": scroll, "text": user_text}
        elif text_lower == "close scroll":
            event_kind = "close_scroll"
        elif text_lower in {"next", "advance", "continue"}:
            event_kind = "advance"
            if current_stage in self.STAGES:
                next_index = (self.STAGES.index(current_stage) + 1) % len(self.STAGES)
                new_stage = self.STAGES[next_index]
                if new_stage == "scatter" and current_stage != "scatter":
                    cycle_count += 1
                event_data = {"from": current_stage, "to": new_stage, "cycle": cycle_count}
                current_stage = new_stage
                stage_changed = True
        else:
            for stage, keywords in self.STAGE_KEYWORDS.items():
                matched = False
                for keyword in keywords:
                    if " " in keyword:
                        if keyword in text_lower:
                            matched = True
                            break
                    elif keyword in token_set:
                        matched = True
                        break
                if matched and stage != current_stage:
                    event_kind = "stage_transition"
                    event_data = {"from": current_stage, "to": stage, "text": user_text}
                    current_stage = stage
                    stage_changed = True
                    break

        for phrase in self.CONSENT_PHRASES:
            if phrase in text_lower:
                event_kind = "consent"
                consent_given = True
                consent_record = {
                    "id": str(uuid.uuid4()),
                    "ts": self._current_ts(),
                    "phrase": phrase,
                    "user_id": context.user_id,
                    "text": user_text,
                }
                consents.append(consent_record)
                event_data = {
                    "text": user_text,
                    "phrase": phrase,
                    "consent_id": consent_record["id"],
                }
                logger.info("Consent recorded: %s", phrase)
                break

        prev_hash = entries[-1]["hash"] if entries else ""
        new_entry = {
            "id": str(uuid.uuid4()),
            "ts": self._current_ts(),
            "kind": event_kind,
            "stage": current_stage,
            "data": event_data,
            "prev_hash": prev_hash,
            "user_id": context.user_id,
        }
        new_entry["hash"] = self._compute_hash(new_entry)
        entries.append(new_entry)

        ledger.update(
            {
                "current_stage": current_stage,
                "cycle_count": cycle_count,
                "entries": entries,
                "consents": consents,
            }
        )
        state["ledger"] = ledger
        await self.save_state("garden", state)

        await self.append_log(
            "garden",
            {"entry_id": new_entry["id"], "kind": event_kind, "stage": current_stage},
        )

        result = {
            "stage": current_stage,
            "cycle": cycle_count,
            "ledger_ref": f"{event_kind}:{new_entry['id'][:8]}",
            "entry_hash": new_entry["hash"],
            "stage_changed": stage_changed,
            "consent_given": consent_given,
            "consent_count": len(consents),
            "entry_count": len(entries),
        }

        context.metadata["garden_stage"] = current_stage
        context.metadata["garden_cycle"] = cycle_count
        context.metadata["consent_given"] = consent_given

        if self.config and self.config.verbose_logging:
            logger.debug("Garden processed: stage=%s, event=%s", current_stage, event_kind)

        return result

    async def get_ledger_summary(self) -> Dict[str, Any]:
        state = await self.get_state("garden")
        ledger = state.get("ledger", {})
        entries = ledger.get("entries", [])
        return {
            "stage": ledger.get("current_stage"),
            "cycle": ledger.get("cycle_count"),
            "entry_count": len(entries),
            "consent_count": len(ledger.get("consents", [])),
            "genesis_ts": entries[0]["ts"] if entries else None,
        }
