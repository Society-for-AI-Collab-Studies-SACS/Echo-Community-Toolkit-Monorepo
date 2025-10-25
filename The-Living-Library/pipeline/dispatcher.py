"""Simple sequential dispatcher used for integration tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .intent_parser import IntentParser, ParsedIntent
from .logger import PipelineLogger


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class PipelineContext:
    input_text: str
    user_id: str
    workspace_id: str
    intent: ParsedIntent
    timestamp: str
    garden_result: Optional[Dict[str, Any]] = None
    echo_result: Optional[Dict[str, Any]] = None
    limnus_result: Optional[Dict[str, Any]] = None
    kira_result: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)


class _GardenAgent:
    def __init__(self, parser: IntentParser) -> None:
        self.parser = parser
        self.cycle = 0

    async def process(self, context: PipelineContext) -> Dict[str, Any]:
        stage = context.intent.args.get("stage") if context.intent.intent_type == "ritual" else None
        if not stage:
            stage = self.parser._detect_stage(context.input_text.lower()) or "scatter"
        self.cycle += 1
        mantra = next((m for m in self.parser.MANTRAS if m in context.input_text.lower()), None)
        result = {"stage": stage, "cycle": self.cycle, "mantra_detected": bool(mantra)}
        context.garden_result = result
        return result


class _EchoAgent:
    PERSONA_KEYWORDS = {
        "squirrel": ("brainstorm", "idea", "explore"),
        "fox": ("debug", "analyze", "solve"),
        "paradox": ("meaning", "mystery", "why"),
    }

    async def process(self, context: PipelineContext) -> Dict[str, Any]:
        persona = "balanced"
        lowered = context.input_text.lower()
        for name, keywords in self.PERSONA_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                persona = name
                break
        result = {
            "styled_text": context.input_text,
            "persona": persona,
            "style": {"tone": "playful" if persona == "squirrel" else "neutral"},
        }
        context.echo_result = result
        return result


class _LimnusAgent:
    def __init__(self) -> None:
        self.counter = 0

    async def process(self, context: PipelineContext) -> Dict[str, Any]:
        self.counter += 1
        result = {
            "cached": True,
            "memory_id": f"memory-{self.counter}",
            "layer": "L1" if context.garden_result and context.garden_result.get("stage") == "scatter" else "L2",
        }
        context.limnus_result = result
        return result


class _KiraAgent:
    async def process(self, context: PipelineContext) -> Dict[str, Any]:
        issues: List[str] = []
        if not context.echo_result:
            issues.append("echo_missing")
        result = {"valid": not issues, "issues": issues, "passed": not issues}
        context.kira_result = result
        return result


class MRPDispatcher:
    """Sequential dispatcher emulating Garden → Echo → Limnus → Kira."""

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        self.parser = IntentParser()
        self.logger = PipelineLogger(workspace_id)
        self.garden = _GardenAgent(self.parser)
        self.echo = _EchoAgent()
        self.limnus = _LimnusAgent()
        self.kira = _KiraAgent()
        self.sequence = [
            ("garden", self.garden),
            ("echo", self.echo),
            ("limnus", self.limnus),
            ("kira", self.kira),
        ]

    async def dispatch(self, context: PipelineContext) -> Dict[str, Any]:
        await self.logger.log_start(context)
        for name, agent in self.sequence:
            try:
                result = await agent.process(context)
                await self.logger.log_agent_step(name, context, result)
            except Exception as exc:  # pragma: no cover - defensive
                context.errors.append(f"{name}: {exc}")
        response = self._synthesise_response(context)
        await self.logger.log_complete(context, response)
        return response

    async def dispatch_text(self, text: str, user_id: str) -> Dict[str, Any]:
        intent = self.parser.parse(text)
        context = PipelineContext(
            input_text=text,
            user_id=user_id,
            workspace_id=self.workspace_id,
            intent=intent,
            timestamp=_timestamp(),
        )
        return await self.dispatch(context)

    def _synthesise_response(self, context: PipelineContext) -> Dict[str, Any]:
        return {
            "success": not context.errors,
            "timestamp": context.timestamp,
            "input": context.input_text,
            "intent": context.intent.intent_type,
            "ritual": context.garden_result or {},
            "echo": context.echo_result or {},
            "memory": context.limnus_result or {},
            "validation": context.kira_result or {"valid": False, "issues": context.errors, "passed": False},
            "errors": context.errors,
        }
