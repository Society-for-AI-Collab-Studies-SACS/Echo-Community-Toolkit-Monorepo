"""Metrics collection helpers for the enhanced dispatcher."""

from __future__ import annotations

import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, MutableMapping

import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricsSummary:
    total_dispatches: int = 0
    successful_dispatches: int = 0
    failed_dispatches: int = 0
    average_execution_ms: float = 0.0
    agent_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    cache_stats: Dict[str, Any] = field(default_factory=dict)
    uptime_seconds: float = 0.0


class MetricsCollector:
    """Collects runtime metrics for the enhanced dispatcher."""

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        self.start_time = time.time()

        self.dispatch_total = 0
        self.dispatch_success = 0
        self.execution_times: List[float] = []

        self.agent_times: MutableMapping[str, List[float]] = defaultdict(list)
        self.agent_errors: MutableMapping[str, int] = defaultdict(int)
        self.error_counts: MutableMapping[str, int] = defaultdict(int)

        self.cache_hits = 0
        self.cache_misses = 0

    async def record_dispatch(self, success: bool, execution_time: float, agent_count: int) -> None:
        self.dispatch_total += 1
        if success:
            self.dispatch_success += 1
        self.execution_times.append(execution_time)
        logger.debug(
            "Recorded dispatch success=%s time=%.2fms agents=%s",
            success,
            execution_time * 1000,
            agent_count,
        )

    async def record_agent_execution(self, agent_name: str, success: bool, execution_time: float) -> None:
        self.agent_times[agent_name].append(execution_time)
        if not success:
            self.agent_errors[agent_name] += 1

    async def record_error(self, source: str, message: str) -> None:
        logger.debug("Recorded error source=%s message=%s", source, message)
        self.error_counts[source] += 1

    async def record_cache_hit(self) -> None:
        self.cache_hits += 1

    async def record_cache_miss(self) -> None:
        self.cache_misses += 1

    async def get_summary(self) -> MetricsSummary:
        uptime = time.time() - self.start_time

        if self.execution_times:
            avg_ms = statistics.mean(self.execution_times) * 1000
            max_ms = max(self.execution_times) * 1000
            min_ms = min(self.execution_times) * 1000
        else:
            avg_ms = max_ms = min_ms = 0.0

        agent_metrics: Dict[str, Dict[str, Any]] = {}
        for agent, times in self.agent_times.items():
            if times:
                agent_metrics[agent] = {
                    "executions": len(times),
                    "avg_ms": statistics.mean(times) * 1000,
                    "max_ms": max(times) * 1000,
                    "min_ms": min(times) * 1000,
                    "errors": self.agent_errors.get(agent, 0),
                }

        cache_total = self.cache_hits + self.cache_misses
        cache_stats = {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": self.cache_hits / cache_total if cache_total else 0.0,
        }

        return MetricsSummary(
            total_dispatches=self.dispatch_total,
            successful_dispatches=self.dispatch_success,
            failed_dispatches=self.dispatch_total - self.dispatch_success,
            average_execution_ms=avg_ms,
            agent_metrics=agent_metrics,
            error_counts=dict(self.error_counts),
            cache_stats=cache_stats,
            uptime_seconds=uptime,
        )
