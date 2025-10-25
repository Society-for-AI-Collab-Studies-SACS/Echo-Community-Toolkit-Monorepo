"""Dispatcher that leverages the real Kira Prime agents."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from library_core.agents import EchoAgent, GardenAgent, KiraAgent, LimnusAgent
from library_core.storage import StorageManager
from pipeline.intent_parser import IntentParser, ParsedIntent
from pipeline.logger import PipelineLogger
from workspace.manager import WorkspaceManager


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class PrimeContext:
    input_text: str
    user_id: str
    workspace_id: str
    intent: ParsedIntent
    timestamp: str
    agent_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class PrimeDispatcher:
    """Routes dictation through the real Garden→Echo→Limnus→Kira pipeline."""

    def __init__(self, workspace_id: str, *, manager: WorkspaceManager | None = None) -> None:
        self.workspace_id = workspace_id
        self.manager = manager or WorkspaceManager()
        self.record = self.manager.get(workspace_id)
        self._ensure_state_dirs()

        storage = StorageManager(self.record.path)
        self.garden = GardenAgent(self.workspace_id, storage, self.manager)
        self.echo = EchoAgent(self.workspace_id, storage, self.manager)
        self.limnus = LimnusAgent(self.workspace_id, storage, self.manager)
        self.kira = KiraAgent(self.workspace_id, storage, self.manager)

        self.parser = IntentParser()
        self.logger = PipelineLogger(workspace_id, self.manager)

    async def dispatch_text(self, text: str, user_id: str) -> Dict[str, Any]:
        intent = self.parser.parse(text)
        context = PrimeContext(
            input_text=text,
            user_id=user_id,
            workspace_id=self.workspace_id,
            intent=intent,
            timestamp=_timestamp(),
        )
        return await asyncio.to_thread(self._dispatch_sync, context)

    # ------------------------------------------------------------------ internals

    def _dispatch_sync(self, context: PrimeContext) -> Dict[str, Any]:
        asyncio.run(self.logger.log_start(context))

        try:
            garden_result = self._process_garden(context)
            context.agent_results["garden"] = garden_result
            asyncio.run(self.logger.log_agent_step("garden", context, garden_result))
        except Exception as exc:  # pragma: no cover - defensive
            context.errors.append(f"garden: {exc}")

        try:
            echo_result = self._process_echo(context)
            context.agent_results["echo"] = echo_result
            asyncio.run(self.logger.log_agent_step("echo", context, echo_result))
        except Exception as exc:  # pragma: no cover - defensive
            context.errors.append(f"echo: {exc}")

        try:
            limnus_result = self._process_limnus(context)
            context.agent_results["limnus"] = limnus_result
            asyncio.run(self.logger.log_agent_step("limnus", context, limnus_result))
        except Exception as exc:  # pragma: no cover - defensive
            context.errors.append(f"limnus: {exc}")

        try:
            kira_result = self._process_kira(context)
            context.agent_results["kira"] = kira_result
            asyncio.run(self.logger.log_agent_step("kira", context, kira_result))
        except Exception as exc:  # pragma: no cover - defensive
            context.errors.append(f"kira: {exc}")

        response = self._synthesise(context)
        asyncio.run(self.logger.log_complete(context, response))
        return response

    # Agent adapters ---------------------------------------------------

    def _process_garden(self, context: PrimeContext) -> Dict[str, Any]:
        log_ref = self.garden.log(context.input_text)
        stage = self.garden.resume()
        return {"stage": stage, "cycle": log_ref, "mantra_detected": "always" in context.input_text.lower()}

    def _process_echo(self, context: PrimeContext) -> Dict[str, Any]:
        # Allow the agent to adapt weights then produce styled text.
        self.echo.learn(context.input_text)
        styled = self.echo.say(context.input_text)
        state_path = self.record.path / "state" / "echo_state.json"
        persona = "balanced"
        tone = "neutral"
        if state_path.exists():
            data = json.loads(state_path.read_text(encoding="utf-8"))
            persona = data.get("last_mode", "balanced")
            tone = persona
        return {"styled_text": styled, "persona": persona, "style": {"tone": tone}}

    def _process_limnus(self, context: PrimeContext) -> Dict[str, Any]:
        self.limnus.cache(context.input_text, tags=[context.user_id])
        mem_path = self.record.path / "state" / "limnus_memory.json"
        memory_id = None
        if mem_path.exists():
            entries = json.loads(mem_path.read_text(encoding="utf-8"))
            if entries:
                memory_id = entries[-1].get("id")
                layer = entries[-1].get("layer", "L2")
            else:
                layer = "L2"
        else:
            layer = "L2"
        return {"cached": True, "memory_id": memory_id, "layer": layer}

    def _process_kira(self, context: PrimeContext) -> Dict[str, Any]:
        validation = self.kira.validate()
        return {
            "valid": validation.get("passed", False),
            "issues": validation.get("issues", []),
        }

    # ------------------------------------------------------------------ helpers

    def _synthesise(self, context: PrimeContext) -> Dict[str, Any]:
        return {
            "success": context.agent_results.get("kira", {}).get("valid", False),
            "timestamp": context.timestamp,
            "input": context.input_text,
            "intent": context.intent.intent_type,
            "ritual": context.agent_results.get("garden", {}),
            "echo": context.agent_results.get("echo", {}),
            "memory": context.agent_results.get("limnus", {}),
            "validation": context.agent_results.get("kira", {}),
            "errors": context.errors,
        }

    def _ensure_state_dirs(self) -> None:
        for folder in ("state", "logs", "outputs"):
            (self.record.path / folder).mkdir(parents=True, exist_ok=True)
