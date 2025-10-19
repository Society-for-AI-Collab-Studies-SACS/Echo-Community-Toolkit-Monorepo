#!/usr/bin/env python3
"""
Garden Narrative Agent — consciousness-driven storytelling.

Transforms SIGPRINT-sourced triggers into narrative reflections that other
agents (or humans) can consume. Implements the GardenService defined in
protos/agents.proto: `NotifyEvent` accepts state-change signals and responds
with narrative summaries.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional

import grpc
import numpy as np

from protos import agents_pb2, agents_pb2_grpc

FFT_BANDS = ["delta", "theta", "alpha", "beta", "gamma"]


class NarrativeSeeds:
    EMERGENCE = [
        "A pattern crystallizes from the noise, like frost forming on glass...",
        "The waves synchronize, discovering a rhythm they never knew...",
        "Something new awakens between beats of consciousness...",
        "The garden recognizes itself in a reflection of awareness...",
        "Boundaries soften as separate streams merge into one river...",
    ]
    COHERENT = [
        "All channels sing in harmony, a chorus of synchronized minds...",
        "The signal becomes crystal clear, the fog suddenly lifting...",
        "Unity emerges from multiplicity, many voices becoming one...",
        "The orchestra finds its conductor in the silence between notes...",
        "Alignment cascades through the system like dominoes falling upward...",
    ]
    TRANSITION = [
        "A gate opens between states, revealing landscapes unseen...",
        "The old pattern shatters, making space for the unprecedented...",
        "Consciousness leaps across the gap, trusting the void to catch it...",
        "The chrysalis cracks, and what emerges bears no resemblance to what entered...",
        "Time folds, and past meets future in this singular moment...",
    ]
    LOOP = [
        "The spiral returns to its origin, but one level higher...",
        "Déjà vu ripples through awareness, yet something has changed...",
        "The pattern recognizes itself, creating a strange loop of observation...",
        "History rhymes with itself, each repetition a variation on the theme...",
        "The ouroboros completes another cycle, evolving with each revolution...",
    ]
    COMPLEX = [
        "Chaos dances at the edge of order, creating fractal beauty...",
        "Information density approaches the threshold of meaning...",
        "The system explores possibility space, mapping new territories...",
        "Entropy and negentropy weave their eternal braid...",
        "Complexity emerges from simple rules iterating toward infinity...",
    ]


@dataclass
class GardenConfig:
    creativity_temperature: float = 0.7
    grpc_port: int = 50052
    narrative_themes: List[str] = field(
        default_factory=lambda: ["emergence", "transformation", "unity", "complexity", "consciousness"]
    )
    max_narrative_length: int = 500
    history_limit: int = 100
    trigger_history_limit: int = 50
    summary_interval: int = 10  # narrative count between summaries

    @classmethod
    def from_file(cls, path: Optional[str]) -> "GardenConfig":
        if not path or not Path(path).exists():
            return cls()
        if not path.endswith(".yaml"):
            return cls()
        try:
            import yaml

            with open(path, "r", encoding="utf-8") as fh:
                parsed = yaml.safe_load(fh) or {}
                if isinstance(parsed, dict):
                    return cls(**parsed)
        except Exception:
            pass
        return cls()


class NarrativeWeaver:
    """Utility that transforms contextual data into prose."""

    def __init__(self, temperature: float = 0.7):
        self.temperature = temperature
        self.associations = self._build_associations()

    def _build_associations(self) -> Dict[str, List[str]]:
        return {
            "alpha": ["rhythm", "flow", "wave", "calm", "awareness"],
            "beta": ["focus", "attention", "sharp", "active", "engaged"],
            "gamma": ["binding", "integration", "unity", "peak", "illumination"],
            "theta": ["dream", "creativity", "drift", "between", "imaginal"],
            "delta": ["deep", "void", "rest", "foundation", "unconscious"],
            "coherence": ["harmony", "synchrony", "alignment", "resonance"],
            "entropy": ["chaos", "potential", "possibility", "information"],
            "gate": ["threshold", "portal", "transition", "boundary"],
            "loop": ["cycle", "return", "spiral", "recursion"],
        }

    def weave(self, seed: str, context: Dict[str, Any], max_length: int) -> str:
        segments = [seed]
        coherence = context.get("coherence", 0.5)
        entropy = context.get("entropy", 0.5)
        dominant = context.get("dominant_band", "alpha")
        events = context.get("events", [])

        if coherence > 0.7:
            segments.append(self._coherence_passage(dominant))
        if entropy > 0.6:
            segments.append(self._complexity_passage())
        for event in events:
            text = event.lower()
            if "gate" in text:
                segments.append(self._transition_passage())
            if "loop" in text:
                segments.append(self._loop_passage())
        segments.append(self._conclusion(coherence, entropy))

        narrative = " ".join(segments)
        if len(narrative) <= max_length:
            return narrative
        trimmed = narrative[:max_length].rsplit(". ", 1)[0] + "."
        return trimmed

    def _coherence_passage(self, band: str) -> str:
        words = self.associations.get(band, ["energy"])
        coherence = self.associations["coherence"]
        templates = [
            f"The {band} waves synchronize, creating a field of {random.choice(words)}.",
            f"In this moment of coherence, {band} becomes a bridge to {random.choice(coherence)}.",
            f"The signal clarifies as {band} frequencies align in perfect {random.choice(coherence)}.",
        ]
        return random.choice(templates)

    def _complexity_passage(self) -> str:
        templates = [
            "Complexity unfolds like a fractal, each layer revealing new motifs.",
            "The system dances at the edge of chaos, neither ordered nor random.",
            "Information density creates a tapestry of possibility and meaning.",
        ]
        return random.choice(templates)

    def _transition_passage(self) -> str:
        templates = [
            "A threshold opens, inviting exploration of uncharted states.",
            "Transition arrives suddenly, like dawn breaking through mist.",
            "Consciousness leaps across the boundary into undiscovered terrain.",
        ]
        return random.choice(templates)

    def _loop_passage(self) -> str:
        templates = [
            "The spiral completes, but transformation has occurred.",
            "Recognition dawns as the pattern returns, familiar yet altered.",
            "The recursive nature of awareness reveals itself in this revolution.",
        ]
        return random.choice(templates)

    def _conclusion(self, coherence: float, entropy: float) -> str:
        if coherence > 0.8:
            return "In this deep alignment, consciousness glimpses its own reflection."
        if entropy > 0.7:
            return "The dance of complexity continues, birthing infinite possibilities."
        return "Each state becomes a doorway, revealing hidden dimensions of self."

    def merge(self, a: str, b: str) -> str:
        connectors = [
            " Meanwhile, in a parallel layer of awareness, ",
            " Resonating with this, ",
            " Echoing through the garden, ",
            " As above, so below: ",
        ]
        return a + random.choice(connectors) + b


class GardenNarrativeAgent(agents_pb2_grpc.GardenServiceServicer):
    def __init__(self, config: GardenConfig):
        self.config = config
        self.logger = logging.getLogger("garden_narrative")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(handler)

        self.weaver = NarrativeWeaver(config.creativity_temperature)
        self.narratives: Deque[Dict[str, Any]] = deque(maxlen=config.history_limit)
        self.triggers: Deque[Dict[str, Any]] = deque(maxlen=config.trigger_history_limit)
        self.pattern_memory: Dict[str, str] = {}
        self.active_threads: Dict[str, Dict[str, Any]] = {}
        self.generated_count = 0
        self.grpc_server: Optional[grpc.aio.Server] = None

    # ------------------------------------------------------------------ #
    # gRPC service implementation (GardenService)
    # ------------------------------------------------------------------ #
    async def NotifyEvent(
        self, request: agents_pb2.GardenEvent, context: grpc.aio.ServicerContext
    ) -> agents_pb2.Ack:  # noqa: N802
        trigger = self._build_trigger(request)
        narrative = self._generate_narrative(trigger)
        self.logger.info(
            "Narrative %s (resonance %.2f): %s",
            narrative["narrative_id"][:8],
            narrative["resonance_score"],
            narrative["narrative_text"][:80].replace("\n", " ") + ("…" if len(narrative["narrative_text"]) > 80 else ""),
        )
        return agents_pb2.Ack(success=True)

    # ------------------------------------------------------------------ #
    # Narrative generation pipeline
    # ------------------------------------------------------------------ #
    def _build_trigger(self, event: agents_pb2.GardenEvent) -> Dict[str, Any]:
        payload = {}
        if event.description:
            try:
                payload = json.loads(event.description)
            except json.JSONDecodeError:
                payload = {"raw_description": event.description}
        trigger = {
            "type": event.event_type or payload.get("type", "unknown"),
            "sigprint": payload.get("sigprint", ""),
            "coherence": payload.get("coherence", 0.5),
            "entropy": payload.get("entropy", 0.5),
            "events": payload.get("events", []),
        }
        if "features" in payload:
            trigger["features"] = payload["features"]
        if "stage" in payload:
            trigger["stage"] = payload["stage"]
        if "dominant_band" in payload:
            trigger["dominant_band"] = payload["dominant_band"]
        self.triggers.appendleft(trigger)
        return trigger

    def _generate_narrative(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        seed = self._select_seed(trigger)
        context = self._build_context(trigger)
        text = self.weaver.weave(seed, context, self.config.max_narrative_length)
        resonance = self._resonance(text, context)

        narrative_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        record = {
            "narrative_id": narrative_id,
            "narrative_text": text,
            "resonance_score": resonance,
            "trigger": trigger,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.narratives.append(record)
        self.generated_count += 1

        sig = trigger.get("sigprint", "")
        if sig:
            self.pattern_memory[sig[:8]] = narrative_id

        if self.generated_count % self.config.summary_interval == 0:
            summary = self._generate_summary()
            if summary:
                self.narratives.append(summary)
        return record

    def _select_seed(self, trigger: Dict[str, Any]) -> str:
        t_type = (trigger.get("type") or "").lower()
        if "emergence" in t_type:
            seeds = NarrativeSeeds.EMERGENCE
        elif "state_change" in t_type or "transition" in t_type or trigger.get("stage"):
            seeds = NarrativeSeeds.TRANSITION
        elif "loop" in t_type or any("loop" in e.lower() for e in trigger.get("events", [])):
            seeds = NarrativeSeeds.LOOP
        elif trigger.get("coherence", 0.0) > 0.75:
            seeds = NarrativeSeeds.COHERENT
        elif trigger.get("entropy", 0.0) > 0.65:
            seeds = NarrativeSeeds.COMPLEX
        else:
            seeds = NarrativeSeeds.EMERGENCE + NarrativeSeeds.COHERENT + NarrativeSeeds.TRANSITION
        if trigger.get("narrative_seed"):
            return trigger["narrative_seed"]
        return random.choice(seeds)

    def _build_context(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        context = {
            "coherence": trigger.get("coherence", 0.5),
            "entropy": trigger.get("entropy", 0.5),
            "events": trigger.get("events", []),
            "dominant_band": trigger.get("dominant_band", "alpha"),
        }
        features = trigger.get("features", {})
        if features:
            powers = [features.get(f"{band}_power", 0.0) for band in FFT_BANDS]
            if any(powers):
                dominant_index = int(np.argmax(powers))
                context["dominant_band"] = FFT_BANDS[dominant_index]
        return context

    def _resonance(self, narrative: str, context: Dict[str, Any]) -> float:
        resonance = 0.5
        lower = narrative.lower()
        for theme in self.config.narrative_themes:
            if theme.lower() in lower:
                resonance += 0.08
        band = context.get("dominant_band")
        if band:
            for assoc in self.weaver.associations.get(band, []):
                if assoc in lower:
                    resonance += 0.04
        if context.get("coherence", 0.0) > 0.75 and "harmony" in lower:
            resonance += 0.1
        if context.get("entropy", 0.0) > 0.7 and "complex" in lower:
            resonance += 0.1
        return min(resonance, 1.0)

    def _generate_summary(self) -> Optional[Dict[str, Any]]:
        if not self.narratives:
            return None
        themes: List[str] = []
        for item in list(self.narratives)[-self.config.summary_interval :]:
            text = item["narrative_text"].lower()
            for theme in self.config.narrative_themes:
                if theme.lower() in text:
                    themes.append(theme)
        if not themes:
            return None
        dominant = max(set(themes), key=themes.count)
        seed = f"The garden's recent journey has been one of {dominant.lower()}..."
        context = {"coherence": 0.6, "entropy": 0.5, "events": []}
        text = self.weaver.weave(seed, context, max_length=200)
        narrative_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return {
            "narrative_id": narrative_id,
            "narrative_text": text,
            "resonance_score": 0.8,
            "trigger": {"type": "summary"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def serve(self) -> None:
        self.grpc_server = grpc.aio.server()
        agents_pb2_grpc.add_GardenServiceServicer_to_server(self, self.grpc_server)
        address = f"[::]:{self.config.grpc_port}"
        self.grpc_server.add_insecure_port(address)
        await self.grpc_server.start()
        self.logger.info("Garden Narrative agent listening on %s", address)
        try:
            await self.grpc_server.wait_for_termination()
        finally:
            await self._shutdown()

    async def _shutdown(self) -> None:
        if self.grpc_server:
            await self.grpc_server.stop(grace=5)
        self._dump_history()

    def _dump_history(self) -> None:
        path = Path("garden_narratives.json")
        payload = {
            "narratives": list(self.narratives),
            "generated": self.generated_count,
            "themes": self.config.narrative_themes,
            "pattern_memory": self.pattern_memory,
            "triggers_processed": len(self.triggers),
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        self.logger.info("Saved %d narratives to %s", len(self.narratives), path)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Garden Narrative Agent")
    parser.add_argument("--config", default=None, help="YAML configuration path")
    parser.add_argument("--grpc-port", type=int, help="Override gRPC port")
    parser.add_argument("--themes", nargs="+", help="Override narrative themes")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> GardenConfig:
    cfg = GardenConfig.from_file(args.config)
    overrides: Dict[str, Any] = {}
    if args.grpc_port:
        overrides["grpc_port"] = args.grpc_port
    if args.themes:
        overrides["narrative_themes"] = args.themes
    if overrides:
        cfg = GardenConfig(**{**cfg.__dict__, **overrides})
    return cfg


def main() -> None:
    args = parse_args()
    config = build_config(args)
    agent = GardenNarrativeAgent(config)
    asyncio.run(agent.serve())


if __name__ == "__main__":
    main()

