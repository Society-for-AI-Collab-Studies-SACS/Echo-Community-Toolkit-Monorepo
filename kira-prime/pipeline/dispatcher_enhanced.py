"""Production-style dispatcher with middleware, retries, and metrics."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from library_core.agents import EchoAgent, GardenAgent, KiraAgent, LimnusAgent, VesselIndexAgent
from library_core.agents.base import BaseAgent
from library_core.storage import StorageManager
from pipeline.circuit_breaker import CircuitBreaker
from pipeline.intent_parser import ParsedIntent
from pipeline.metrics import MetricsCollector
from pipeline.middleware import Middleware
from pipeline.logger import PipelineLogger
from workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineContext:
    input_text: str
    user_id: str
    workspace_id: str
    intent: ParsedIntent
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    trace: List[Dict[str, Any]] = field(default_factory=list)

    def add_result(self, agent: str, result: Any) -> None:
        self.agent_results[agent] = result

    def add_error(self, agent: str, error: Exception) -> None:
        self.errors.append(
            {
                "agent": agent,
                "error": str(error),
                "type": type(error).__name__,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def add_trace(self, event: str, data: Dict[str, Any]) -> None:
        entry = {"event": event, "ts": datetime.now(timezone.utc).isoformat()}
        entry.update(data)
        self.trace.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DispatcherConfig:
    agent_order: List[str] = field(
        default_factory=lambda: ["garden", "echo", "limnus", "kira", "vessel_index"]
    )
    parallel_execution: bool = False
    timeout_seconds: int = 30
    retry_enabled: bool = True
    retry_attempts: int = 3
    retry_delay: float = 1.0
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    cache_enabled: bool = True
    cache_ttl: int = 300
    verbose_logging: bool = True


class EnhancedMRPDispatcher:
    """Coordinator that executes the Garden→Echo→Limnus→Kira chain with extras."""

    def __init__(self, workspace_id: str, config: Optional[DispatcherConfig] = None) -> None:
        self.workspace_id = workspace_id
        self.config = config or DispatcherConfig()

        self.manager = WorkspaceManager()
        self.record = self.manager.get(workspace_id)
        self.storage = StorageManager(self.record.path)

        self.logger = PipelineLogger(workspace_id, self.manager)
        self.metrics = MetricsCollector(workspace_id)

        self.middleware: List[Middleware] = []
        self.event_hooks: Dict[str, List[Callable[..., Awaitable[None] | None]]] = {
            "pre_dispatch": [],
            "post_dispatch": [],
            "pre_agent": [],
            "post_agent": [],
            "error": [],
            "retry": [],
        }

        self.cache: Dict[str, tuple[Any, float]] = {}

        self.agents: Dict[str, BaseAgent] = {
            "garden": GardenAgent(workspace_id, self.storage, self.manager),
            "echo": EchoAgent(workspace_id, self.storage, self.manager),
            "limnus": LimnusAgent(workspace_id, self.storage, self.manager),
            "kira": KiraAgent(workspace_id, self.storage, self.manager),
            "vessel_index": VesselIndexAgent(workspace_id, self.storage, self.manager),
        }

        self.breakers: Dict[str, CircuitBreaker] = {}
        if self.config.circuit_breaker_enabled:
            for name in self.config.agent_order:
                self.breakers[name] = CircuitBreaker(
                    failure_threshold=self.config.circuit_breaker_threshold,
                    timeout=self.config.circuit_breaker_timeout,
                )

    # ------------------------------------------------------------------ middleware/events
    def add_middleware(self, middleware: Middleware) -> None:
        self.middleware.append(middleware)

    def on(self, event: str, handler: Callable[..., Awaitable[None] | None]) -> None:
        self.event_hooks.setdefault(event, []).append(handler)

    async def _emit(self, event: str, **kwargs) -> None:
        for handler in self.event_hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(**kwargs)
                else:
                    handler(**kwargs)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Event hook error (%s): %s", event, exc)

    # ------------------------------------------------------------------ caching helpers
    def _cache_key(self, context: PipelineContext) -> str:
        cache_data = f"{context.user_id}:{context.workspace_id}:{context.input_text}"
        return hashlib.sha256(cache_data.encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        if not self.config.cache_enabled:
            return None
        entry = self.cache.get(key)
        if not entry:
            return None
        result, ts = entry
        if time.time() - ts > self.config.cache_ttl:
            self.cache.pop(key, None)
            return None
        logger.debug("Cache hit for %s", key[:12])
        return result

    def _set_cached(self, key: str, result: Dict[str, Any]) -> None:
        if self.config.cache_enabled:
            self.cache[key] = (result, time.time())

    # ------------------------------------------------------------------ main dispatch
    async def dispatch(self, context: PipelineContext) -> Dict[str, Any]:
        start = time.time()
        cache_key = self._cache_key(context)
        cached = self._get_cached(cache_key)
        if cached:
            await self.metrics.record_cache_hit()
            cached["cached"] = True
            return cached
        await self.metrics.record_cache_miss()

        await self._emit("pre_dispatch", context=context)
        for middleware in self.middleware:
            context = await middleware.pre_dispatch(context)

        if self.config.parallel_execution:
            await self._dispatch_parallel(context)
        else:
            await self._dispatch_sequential(context)

        response = self._synthesise(context)
        response["execution_time_ms"] = (time.time() - start) * 1000
        response["cached"] = False

        for middleware in reversed(self.middleware):
            response = await middleware.post_dispatch(context, response)
        await self._emit("post_dispatch", context=context, response=response)

        await self.metrics.record_dispatch(response["success"], response["execution_time_ms"] / 1000, len(self.config.agent_order))
        self._set_cached(cache_key, response)
        return response

    async def _dispatch_sequential(self, context: PipelineContext) -> None:
        for agent_name in self.config.agent_order:
            await self._execute_agent(agent_name, context)

    async def _dispatch_parallel(self, context: PipelineContext) -> None:
        tasks = [self._execute_agent(name, context) for name in self.config.agent_order]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_agent(self, agent_name: str, context: PipelineContext) -> None:
        agent = self.agents.get(agent_name)
        if not agent:
            logger.warning("Agent not found: %s", agent_name)
            return

        breaker = self.breakers.get(agent_name)
        if breaker and breaker.is_open():
            context.add_error(agent_name, RuntimeError("circuit_open"))
            return

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt < (self.config.retry_attempts if self.config.retry_enabled else 1):
            try:
                await self._emit("pre_agent", agent_name=agent_name, context=context)
                for middleware in self.middleware:
                    context = await middleware.pre_agent(agent_name, context)
                context.add_trace("agent_start", {"agent": agent_name, "attempt": attempt})
                start = time.time()
                result = await asyncio.wait_for(
                    agent.process(context),
                    timeout=self.config.timeout_seconds,
                )
                context.add_trace("agent_complete", {"agent": agent_name, "elapsed_ms": (time.time() - start) * 1000})
                context.add_result(agent_name, result)

                for middleware in reversed(self.middleware):
                    result = await middleware.post_agent(agent_name, context, result)
                await self._emit("post_agent", agent_name=agent_name, context=context, result=result)

                if breaker:
                    breaker.record_success()
                await self.metrics.record_agent_execution(agent_name, True, time.time() - start)
                return

            except Exception as exc:  # pragma: no cover - defensive
                last_error = exc
                context.add_trace("agent_failure", {"agent": agent_name, "error": str(exc)})
                for middleware in self.middleware:
                    await middleware.on_error(agent_name, context, exc)
                await self.metrics.record_agent_execution(agent_name, False, 0)
                await self._emit("error", agent_name=agent_name, context=context, error=exc)
                if breaker:
                    breaker.record_failure()

            attempt += 1
            if attempt < self.config.retry_attempts and self.config.retry_enabled:
                delay = self.config.retry_delay * (2 ** (attempt - 1))
                context.add_trace("agent_retry", {"agent": agent_name, "delay": delay})
                await self._emit("retry", agent_name=agent_name, attempt=attempt)
                await asyncio.sleep(delay)

        if last_error is not None:
            context.add_error(agent_name, last_error)

    def _synthesise(self, context: PipelineContext) -> Dict[str, Any]:
        response = {
            "success": not context.errors,
            "timestamp": context.timestamp,
            "input": context.input_text,
            "intent": context.intent.intent_type,
            "agents": {name: context.agent_results.get(name) for name in self.config.agent_order},
            "errors": context.errors,
            "metadata": context.metadata,
            "trace": context.trace if self.config.verbose_logging else [],
            "metrics": context.metrics,
        }
        response["ritual"] = context.agent_results.get("garden", {})
        response["echo"] = context.agent_results.get("echo", {})
        response["memory"] = context.agent_results.get("limnus", {})
        response["validation"] = context.agent_results.get("kira", {})
        response["index"] = context.agent_results.get("vessel_index", {})
        return response

    async def get_metrics(self) -> Dict[str, Any]:
        summary = await self.metrics.get_summary()
        return summary.__dict__

    async def reset_circuit_breakers(self) -> None:
        for breaker in self.breakers.values():
            breaker.reset()

