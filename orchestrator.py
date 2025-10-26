#!/usr/bin/env python3
"""
Living Library SIGPRINT Orchestrator
===================================

Coordinates the multi-agent consciousness stack:
  - SIGPRINT Monitor (hardware + pattern detection)
  - Limnus Ledger (cryptographic recording)
  - Garden Narrative (storytelling & meaning-making)

Responsibilities:
  * spawn / connect to agents
  * poll SIGPRINT updates
  * route events to the ledger & narrative agents
  * track basic emergence statistics
  * persist orchestration metrics on shutdown
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import signal
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import grpc
from google.protobuf import empty_pb2

from protos import agents_pb2, agents_pb2_grpc

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required for the orchestrator. Install via pip.") from exc


DEFAULT_SCRIPTS = {
    "monitor": "agents/sigprint/monitor_agent.py",
    "ledger": "agents/limnus/ledger_agent.py",
    "garden": "agents/garden/narrative_agent.py",
}

DEFAULT_FLOW_RULES: List[Dict[str, Any]] = [
    {"source": "monitor", "event": "sigprint_update", "destination": "ledger", "action": "record_entry"},
    {"source": "monitor", "event": "high_coherence", "destination": "garden", "action": "generate_narrative"},
    {"source": "monitor", "event": "gate_event", "destination": "garden", "action": "generate_narrative"},
]


@dataclass
class AgentConfig:
    name: str
    script: str
    grpc_port: int
    host: str = "127.0.0.1"
    spawn: bool = True
    args: List[str] = field(default_factory=list)


@dataclass
class OrchestratorConfig:
    monitor: AgentConfig
    ledger: AgentConfig
    garden: AgentConfig
    auto_start_agents: bool = True
    monitor_interval: float = 5.0
    enable_emergence: bool = True
    flow_rules: List[Dict[str, Any]] = field(default_factory=lambda: list(DEFAULT_FLOW_RULES))

    @classmethod
    def from_file(cls, path: str) -> "OrchestratorConfig":
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        def build_agent(section: str, defaults: Dict[str, Any]) -> AgentConfig:
            cfg = data.get(section, {})
            return AgentConfig(
                name=cfg.get("agent_name", defaults["name"]),
                script=cfg.get("script", defaults["script"]),
                grpc_port=int(cfg.get("grpc_port", defaults["grpc_port"])),
                host=cfg.get("host", defaults.get("host", "127.0.0.1")),
                spawn=cfg.get("spawn", defaults.get("spawn", True)),
                args=list(cfg.get("args", defaults.get("args", []))),
            )

        monitor_defaults = {"name": "sigprint_monitor", "script": DEFAULT_SCRIPTS["monitor"], "grpc_port": 50051}
        ledger_defaults = {"name": "limnus_ledger", "script": DEFAULT_SCRIPTS["ledger"], "grpc_port": 50052}
        garden_defaults = {"name": "garden_narrative", "script": DEFAULT_SCRIPTS["garden"], "grpc_port": 50053}

        return cls(
            monitor=build_agent("monitor", monitor_defaults),
            ledger=build_agent("ledger", ledger_defaults),
            garden=build_agent("garden", garden_defaults),
            auto_start_agents=data.get("auto_start_agents", True),
            monitor_interval=float(data.get("monitor_interval", 5.0)),
            enable_emergence=data.get("enable_emergence", True),
            flow_rules=list(data.get("flow_rules") or DEFAULT_FLOW_RULES),
        )


class AgentProcess:
    """Wrapper around an agent's subprocess and gRPC connection."""

    def __init__(self, agent_type: str, config: AgentConfig):
        self.agent_type = agent_type
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[Any] = None
        self.status = "OFFLINE"
        self.last_ready: Optional[datetime] = None

    async def start(self) -> bool:
        if self.config.spawn:
            script_path = Path(self.config.script)
            if not script_path.exists():
                logging.error("Agent script not found: %s", script_path)
                self.status = "ERROR"
                return False
            args = [sys.executable, str(script_path), "--grpc-port", str(self.config.grpc_port), *self.config.args]
            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            self.status = "STARTING"
            await asyncio.sleep(1.0)
        return await self._connect()

    async def _connect(self) -> bool:
        try:
            self.channel = grpc.aio.insecure_channel(f"{self.config.host}:{self.config.grpc_port}")
            await asyncio.wait_for(self.channel.channel_ready(), timeout=10.0)
        except (asyncio.TimeoutError, grpc.FutureTimeoutError):
            logging.error("Timed out connecting to %s agent on port %s", self.agent_type, self.config.grpc_port)
            self.status = "UNAVAILABLE"
            return False

        stub_map = {
            "monitor": agents_pb2_grpc.SigprintServiceStub,
            "ledger": agents_pb2_grpc.LedgerServiceStub,
            "garden": agents_pb2_grpc.GardenServiceStub,
        }
        stub_cls = stub_map.get(self.agent_type)
        if not stub_cls:
            logging.error("Unknown agent type: %s", self.agent_type)
            self.status = "ERROR"
            return False

        self.stub = stub_cls(self.channel)
        self.status = "READY"
        self.last_ready = datetime.utcnow()
        return True

    async def stop(self) -> None:
        if self.process and self.config.spawn:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
        if self.channel:
            await self.channel.close()
        self.status = "OFFLINE"

    def is_alive(self) -> bool:
        if self.status != "READY":
            return False
        if self.config.spawn and self.process and self.process.returncode is not None:
            return False
        return True


class DataFlowController:
    """Routes events to the appropriate agents using configured rules."""

    def __init__(self, rules: List[Dict[str, Any]], orchestrator: "LivingLibraryOrchestrator"):
        self.rules = rules
        self.orchestrator = orchestrator
        self.stats = {"events_processed": 0, "rules_triggered": 0, "errors": 0}

    async def handle_event(self, event: Dict[str, Any]) -> None:
        self.stats["events_processed"] += 1
        for rule in self.rules:
            if rule.get("source") != event.get("source"):
                continue
            if rule.get("event") and rule["event"] != event.get("type"):
                continue
            try:
                await self._execute(rule, event)
                self.stats["rules_triggered"] += 1
            except Exception as exc:  # pragma: no cover - defensive
                logging.exception("Flow rule execution failed: %s", exc)
                self.stats["errors"] += 1

    async def _execute(self, rule: Dict[str, Any], event: Dict[str, Any]) -> None:
        action = rule.get("action")
        destination = rule.get("destination")
        if action == "record_entry" and destination == "ledger":
            await self.orchestrator.commit_to_ledger(event)
        elif action == "generate_narrative" and destination == "garden":
            await self.orchestrator.send_to_garden(event)


class EmergenceDetector:
    """Very light-weight emergence detector based on repeated high-coherence cycles."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.window: Deque[float] = deque(maxlen=20)
        self.detections: List[Dict[str, Any]] = []

    def observe(self, coherence: float) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        self.window.append(coherence)
        if len(self.window) < self.window.maxlen:
            return None
        avg = sum(self.window) / len(self.window)
        if avg > 85.0:
            detection = {"type": "sustained_high_coherence", "timestamp": datetime.utcnow().isoformat()}
            self.detections.append(detection)
            self.window.clear()
            logging.info("Emergence detected: sustained high coherence")
            return detection
        return None


class LivingLibraryOrchestrator:
    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.logger = logging.getLogger("orchestrator")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(handler)

        self.agents = {
            "monitor": AgentProcess("monitor", config.monitor),
            "ledger": AgentProcess("ledger", config.ledger),
            "garden": AgentProcess("garden", config.garden),
        }
        self.flow_controller = DataFlowController(config.flow_rules, self)
        self.emergence_detector = EmergenceDetector(config.enable_emergence)
        self.running = False
        self.poll_task: Optional[asyncio.Task] = None
        self.stats = {"events": 0, "ledger_commits": 0, "garden_calls": 0}
        self.last_sigprint: Optional[str] = None
        self.committed_codes: Deque[str] = deque(maxlen=1024)
        self.start_time: Optional[datetime] = None

    async def start(self) -> None:
        self.logger.info("Starting Living Library Orchestrator…")
        self.start_time = datetime.utcnow()
        self.running = True

        if self.config.auto_start_agents:
            for name, agent in self.agents.items():
                self.logger.info("Launching %s agent…", name)
                ok = await agent.start()
                if not ok:
                    self.logger.error("Failed to initialize %s agent", name)

        else:
            # Connect to already-running agents
            for name, agent in self.agents.items():
                self.logger.info("Connecting to existing %s agent…", name)
                await agent._connect()

        self.poll_task = asyncio.create_task(self._poll_monitor())
        try:
            await self.poll_task
        except asyncio.CancelledError:
            pass

    async def _poll_monitor(self) -> None:
        interval = max(0.5, self.config.monitor_interval)
        monitor_agent = self.agents["monitor"]
        empty = empty_pb2.Empty()

        while self.running:
            if not monitor_agent.is_alive() or not monitor_agent.stub:
                self.logger.warning("Monitor agent unavailable; retrying connection…")
                await monitor_agent.start()
                await asyncio.sleep(interval)
                continue

            try:
                update = await monitor_agent.stub.GetLatestSigprint(empty)
            except grpc.aio.AioRpcError as exc:
                self.logger.error("Failed to fetch SIGPRINT update: %s", exc)
                await asyncio.sleep(interval)
                continue

            if not update.sigprint:
                await asyncio.sleep(interval)
                continue

            if update.sigprint == self.last_sigprint:
                await asyncio.sleep(interval)
                continue

            self.last_sigprint = update.sigprint
            features = dict(update.features)
            event = {
                "source": "monitor",
                "type": "sigprint_update",
                "sigprint": update.sigprint,
                "coherence": update.coherence,
                "entropy": features.get("entropy", 0.0),
                "features": features,
                "timestamp": update.time or datetime.utcnow().isoformat(),
            }

            flags = features.get("gate_flags", 0.0)
            if flags:
                event["type"] = "gate_event"
                event.setdefault("events", []).append("gate")
            elif update.coherence >= 80.0:
                event["type"] = "high_coherence"

            if features.get("loop_flags", 0.0):
                event.setdefault("events", []).append("loop")

            await self.flow_controller.handle_event(event)
            self.stats["events"] += 1
            self.emergence_detector.observe(update.coherence)
            await asyncio.sleep(interval)

    async def commit_to_ledger(self, event: Dict[str, Any]) -> None:
        ledger_agent = self.agents["ledger"]
        if not ledger_agent.is_alive() or not ledger_agent.stub:
            self.logger.warning("Ledger agent not ready; skipping entry")
            return
        code = event.get("sigprint", "")
        if not code:
            return
        if code == self.last_sigprint and code in self.committed_codes:
            return

        entry = agents_pb2.LedgerEntry(
            time=event.get("timestamp", datetime.utcnow().isoformat()),
            type="SIGPRINT",
            text="",
            sigprint=code,
            coherence=float(event.get("coherence", 0.0)),
        )
        features = event.get("features", {})
        entry.features.update({k: float(v) for k, v in features.items()})
        try:
            await ledger_agent.stub.CommitEntry(entry)
            self.stats["ledger_commits"] += 1
            self.committed_codes.append(code)
        except grpc.aio.AioRpcError as exc:
            self.logger.error("Ledger commit failed: %s", exc)

    async def send_to_garden(self, event: Dict[str, Any]) -> None:
        garden_agent = self.agents["garden"]
        if not garden_agent.is_alive() or not garden_agent.stub:
            self.logger.warning("Garden agent not ready; skipping narrative trigger")
            return

        description = json.dumps(
            {
                "sigprint": event.get("sigprint"),
                "coherence": event.get("coherence"),
                "entropy": event.get("entropy"),
                "events": event.get("events", []),
                "features": event.get("features", {}),
            }
        )
        garden_event = agents_pb2.GardenEvent(
            event_type=event.get("type", "state_change").upper(),
            description=description,
        )
        try:
            await garden_agent.stub.NotifyEvent(garden_event)
            self.stats["garden_calls"] += 1
        except grpc.aio.AioRpcError as exc:
            self.logger.error("Garden notify failed: %s", exc)

    async def shutdown(self) -> None:
        self.logger.info("Orchestrator shutting down…")
        self.running = False
        if self.poll_task:
            self.poll_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.poll_task

        for name, agent in self.agents.items():
            self.logger.info("Stopping %s agent…", name)
            await agent.stop()

        self._write_stats()

    def _write_stats(self) -> None:
        runtime = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0.0
        payload = {
            "runtime_seconds": runtime,
            "events_processed": self.stats["events"],
            "ledger_commits": self.stats["ledger_commits"],
            "garden_calls": self.stats["garden_calls"],
            "emergence_events": self.emergence_detector.detections,
            "flow_stats": self.flow_controller.stats,
        }
        with open("orchestrator_stats.json", "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        self.logger.info("Saved orchestrator statistics (events=%s)", self.stats["events"])


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="Living Library SIGPRINT Orchestrator")
    parser.add_argument("--config", default="config/default_config.yaml", help="Path to orchestrator YAML config")
    parser.add_argument("--no-auto-start", action="store_true", help="Do not spawn agents automatically")
    parser.add_argument("--disable-emergence", action="store_true", help="Disable emergence detection")
    parser.add_argument("--monitor-interval", type=float, help="Override monitor polling interval (seconds)")
    args = parser.parse_args()

    if Path(args.config).exists():
        config = OrchestratorConfig.from_file(args.config)
    else:
        config = OrchestratorConfig(
            monitor=AgentConfig("sigprint_monitor", DEFAULT_SCRIPTS["monitor"], 50051),
            ledger=AgentConfig("limnus_ledger", DEFAULT_SCRIPTS["ledger"], 50052),
            garden=AgentConfig("garden_narrative", DEFAULT_SCRIPTS["garden"], 50053),
        )

    if args.no_auto_start:
        config.auto_start_agents = False
        config.monitor.spawn = False
        config.ledger.spawn = False
        config.garden.spawn = False

    if args.disable_emergence:
        config.enable_emergence = False

    if args.monitor_interval:
        config.monitor_interval = args.monitor_interval

    orchestrator = LivingLibraryOrchestrator(config)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(orchestrator.shutdown()))

    await orchestrator.start()


if __name__ == "__main__":
    import contextlib

    asyncio.run(async_main())
