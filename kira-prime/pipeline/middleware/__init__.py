"""Middleware primitives for the enhanced dispatcher."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from pipeline.dispatcher_enhanced import PipelineContext

logger = logging.getLogger(__name__)


class Middleware:
    async def pre_dispatch(self, context: "PipelineContext") -> "PipelineContext":
        return context

    async def post_dispatch(
        self,
        context: "PipelineContext",
        response: Dict[str, Any],
    ) -> Dict[str, Any]:
        return response

    async def pre_agent(self, agent_name: str, context: "PipelineContext") -> "PipelineContext":
        return context

    async def post_agent(
        self,
        agent_name: str,
        context: "PipelineContext",
        result: Any,
    ) -> Any:
        return result

    async def on_error(self, agent_name: str, context: "PipelineContext", error: Exception) -> None:
        return None


class LoggingMiddleware(Middleware):
    async def pre_dispatch(self, context: "PipelineContext") -> "PipelineContext":
        logger.info(
            "[DISPATCH START] user=%s workspace=%s text=%s",
            context.user_id,
            context.workspace_id,
            context.input_text[:80],
        )
        return context

    async def post_dispatch(
        self,
        context: "PipelineContext",
        response: Dict[str, Any],
    ) -> Dict[str, Any]:
        status = "✅" if response.get("success") else "❌"
        logger.info("[DISPATCH END] %s errors=%s", status, len(response.get("errors", [])))
        return response

    async def pre_agent(self, agent_name: str, context: "PipelineContext") -> "PipelineContext":
        logger.debug("[AGENT START] %s", agent_name)
        return context

    async def post_agent(
        self,
        agent_name: str,
        context: "PipelineContext",
        result: Any,
    ) -> Any:
        logger.debug("[AGENT END] %s", agent_name)
        return result

    async def on_error(self, agent_name: str, context: "PipelineContext", error: Exception) -> None:
        logger.error("[AGENT ERROR] %s -> %s", agent_name, error)


class RateLimitMiddleware(Middleware):
    def __init__(self, max_requests_per_minute: int = 60) -> None:
        self.max_requests = max_requests_per_minute
        self._requests: Dict[str, List[float]] = {}

    async def pre_dispatch(self, context: "PipelineContext") -> "PipelineContext":
        now = time.time()
        user = context.user_id
        history = self._requests.setdefault(user, [])
        history[:] = [ts for ts in history if now - ts < 60]
        if len(history) >= self.max_requests:
            raise RuntimeError(f"Rate limit exceeded for {user}")
        history.append(now)
        context.metadata["rate_limit_remaining"] = self.max_requests - len(history)
        return context


class MetricsMiddleware(Middleware):
    def __init__(self) -> None:
        self._timers: Dict[str, float] = {}

    async def pre_agent(self, agent_name: str, context: "PipelineContext") -> "PipelineContext":
        self._timers[agent_name] = time.time()
        return context

    async def post_agent(
        self,
        agent_name: str,
        context: "PipelineContext",
        result: Any,
    ) -> Any:
        start = self._timers.get(agent_name)
        if start is not None:
            elapsed_ms = (time.time() - start) * 1000
            context.metrics.setdefault("agent_timings", {})[agent_name] = elapsed_ms
        return result


class ValidationMiddleware(Middleware):
    def __init__(self, max_length: int = 10_000) -> None:
        self.max_length = max_length

    async def pre_dispatch(self, context: "PipelineContext") -> "PipelineContext":
        if not context.input_text:
            raise ValueError("Input text cannot be empty")
        if len(context.input_text) > self.max_length:
            raise ValueError(f"Input text too long (max {self.max_length} characters)")
        return context

    async def post_dispatch(
        self,
        context: "PipelineContext",
        response: Dict[str, Any],
    ) -> Dict[str, Any]:
        for key in ("success", "timestamp", "agents"):
            if key not in response:
                logger.warning("Dispatcher response missing key '%s'", key)
        return response

