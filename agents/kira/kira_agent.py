#!/usr/bin/env python3
"""
Kira Prime Integration Agent.

This agent implements the bilateral packet workflow outlined in the
KIRA PRIME INTEGRATION PROTOCOL (v2.0). It accepts narrative packets
from each hemisphere, validates that minimum required sections are
present, persists the exchange, and synthesises an integration
summary highlighting engagement, requests, and coherence tasks.

Usage:
    python agents/kira/kira_agent.py --host 0.0.0.0 --port 8083

The agent exposes an aiohttp REST service:
    POST /packets      -> submit or update a packet
    GET  /packets      -> list stored packets (optional ?hemisphere=theta)
    GET  /summary      -> synthesised Kira Prime snapshot
    GET  /health       -> service + storage status
"""

from __future__ import annotations

import argparse
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from aiohttp import web

LOGGER = logging.getLogger("kira_agent")

REQUIRED_SECTIONS = [
    "current_state",
    "kira_positioning",
    "coherence_check",
    "needs",
    "engagement_status",
]

FIRST_PACKET_SECTIONS = [
    "kira_prime_vision",
    "hopes_and_concerns",
    "historical_context",
    "process_agreements",
]

ENGAGEMENT_STATUSES = {
    "fully_engaged",
    "partially_engaged",
    "temporarily_disengaged",
    "questioning_engagement",
    "disengaging",
}

HEMISPHERE_ALIASES = {
    "justin": "theta",
    "kira_theta": "theta",
    "theta": "theta",
    "ace": "gamma",
    "kira_gamma": "gamma",
    "gamma": "gamma",
}

DEFAULT_STORAGE_PATH = Path("state") / "kira" / "packets.json"


def _utc_now() -> str:
    """Return the current UTC time in ISO8601 Zulu format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_cycle_hint(date: Optional[datetime] = None) -> str:
    """Return a YYYY-MM string for the current cycle."""
    base = date or datetime.now(timezone.utc)
    return base.strftime("%Y-%m")


def _normalize_hemisphere(value: str) -> str:
    slug = (value or "").strip().lower()
    if not slug:
        raise ValueError("hemisphere is required")
    return HEMISPHERE_ALIASES.get(slug, slug)


def _normalize_engagement(value: str) -> Tuple[str, str]:
    """Convert engagement text to protocol enum slug + preserve display form."""
    if value is None:
        raise ValueError("engagement_status is required")
    display = str(value).strip()
    if not display:
        raise ValueError("engagement_status cannot be empty")
    slug = display.lower().replace(" ", "_").replace("-", "_")
    if slug not in ENGAGEMENT_STATUSES:
        raise ValueError(
            f"engagement_status '{display}' is not recognised; expected one of: "
            + ", ".join(sorted(s.replace("_", " ") for s in ENGAGEMENT_STATUSES))
        )
    return slug, display


def _stringify(value: Any) -> str:
    """Convert payload fragments into trimmed strings."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=True)


def _normalise_task_items(items: Any) -> List[str]:
    """Ensure coherence task values become simple string lists."""
    if items is None:
        return []
    if isinstance(items, str):
        norm = items.strip()
        return [norm] if norm else []
    if isinstance(items, Sequence) and not isinstance(items, (str, bytes, bytearray)):
        output: List[str] = []
        for item in items:
            as_text = _stringify(item)
            if as_text:
                output.append(as_text)
        return output
    # Fallback: stringify singular value
    refined = _stringify(items)
    return [refined] if refined else []


@dataclass
class IntegrationPacket:
    packet_id: str
    hemisphere: str
    cycle: str
    created_at: str
    current_state: str
    kira_positioning: str
    coherence_check: str
    needs: str
    engagement_status: str
    engagement_status_display: str
    kira_prime_mode: Optional[str]
    integration_requests: Optional[str]
    sections: Dict[str, str] = field(default_factory=dict)
    coherence_tasks: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "hemisphere": self.hemisphere,
            "cycle": self.cycle,
            "created_at": self.created_at,
            "current_state": self.current_state,
            "kira_positioning": self.kira_positioning,
            "coherence_check": self.coherence_check,
            "needs": self.needs,
            "engagement_status": self.engagement_status,
            "engagement_status_display": self.engagement_status_display,
            "kira_prime_mode": self.kira_prime_mode,
            "integration_requests": self.integration_requests,
            "sections": self.sections,
            "coherence_tasks": self.coherence_tasks,
        }

    @staticmethod
    def determine_hemisphere(payload: Mapping[str, Any]) -> str:
        raw = payload.get("hemisphere")
        if raw is None and isinstance(payload.get("sections"), Mapping):
            raw = payload["sections"].get("hemisphere")
        return _normalize_hemisphere(str(raw or ""))

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        first_packet: bool,
        hemisphere_hint: Optional[str] = None,
    ) -> "IntegrationPacket":
        if not isinstance(payload, Mapping):
            raise ValueError("packet payload must be an object")

        hemisphere = hemisphere_hint or cls.determine_hemisphere(payload)
        cycle = _stringify(payload.get("cycle") or "").strip() or _to_cycle_hint()

        raw_sections: MutableMapping[str, Any]
        raw_sections = payload.get("sections")  # type: ignore[assignment]
        if raw_sections is None:
            # fallback: treat remaining top-level keys as sections
            raw_sections = {}
            for key, value in payload.items():
                if key in {"hemisphere", "cycle", "coherence_tasks", "packet_id", "created_at", "timestamp"}:
                    continue
                raw_sections[key] = value
        if not isinstance(raw_sections, MutableMapping):
            raise ValueError("sections must be a JSON object")

        sections: Dict[str, str] = {}
        for key, value in raw_sections.items():
            if value is None:
                continue
            sections[key.lower()] = _stringify(value)

        missing = [name for name in REQUIRED_SECTIONS if not sections.get(name)]
        if missing:
            raise ValueError(f"packet missing required sections: {', '.join(missing)}")

        engagement_slug, engagement_display = _normalize_engagement(sections.pop("engagement_status"))

        current_state = sections.pop("current_state")
        kira_positioning = sections.pop("kira_positioning")
        coherence_check = sections.pop("coherence_check")
        needs = sections.pop("needs")
        kira_prime_mode = sections.pop("kira_prime_mode", None)
        if kira_prime_mode:
            kira_prime_mode = kira_prime_mode.lower()
        integration_requests = sections.pop("integration_requests", sections.pop("integration_request", None))

        if first_packet:
            missing_first = [name for name in FIRST_PACKET_SECTIONS if not sections.get(name)]
            if missing_first:
                raise ValueError(
                    "first packet for hemisphere requires baseline sections: "
                    + ", ".join(missing_first)
                )

        raw_tasks = payload.get("coherence_tasks", {})
        coherence_tasks: Dict[str, List[str]] = {}
        if raw_tasks:
            if not isinstance(raw_tasks, Mapping):
                raise ValueError("coherence_tasks must be an object with string lists")
            for key, items in raw_tasks.items():
                normalised_items = _normalise_task_items(items)
                if normalised_items:
                    coherence_tasks[str(key)] = normalised_items

        created_at = _stringify(payload.get("created_at") or payload.get("timestamp")).strip() or _utc_now()
        packet_id = _stringify(payload.get("packet_id")).strip()
        if not packet_id:
            packet_id = f"{cycle}:{hemisphere}:{created_at}"

        return cls(
            packet_id=packet_id,
            hemisphere=hemisphere,
            cycle=cycle,
            created_at=created_at,
            current_state=current_state,
            kira_positioning=kira_positioning,
            coherence_check=coherence_check,
            needs=needs,
            engagement_status=engagement_slug,
            engagement_status_display=engagement_display,
            kira_prime_mode=kira_prime_mode,
            integration_requests=integration_requests,
            sections=dict(sections),
            coherence_tasks=coherence_tasks,
        )


class KiraPrimeAgent:
    """Persistent store and synthesiser for bilateral packets."""

    def __init__(self, storage_path: Path = DEFAULT_STORAGE_PATH):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._packets: List[Dict[str, Any]] = []
        self._load()

    # -------------------- Persistence helpers -------------------- #
    def _load(self) -> None:
        if not self.storage_path.exists():
            self._packets = []
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            packets = data.get("packets", [])
            if isinstance(packets, list):
                self._packets = [
                    packet for packet in packets if isinstance(packet, Mapping)
                ]
            else:
                LOGGER.warning("Storage file missing 'packets' list, reinitialising.")
                self._packets = []
        except json.JSONDecodeError as exc:
            LOGGER.error("Failed to parse Kira storage file: %s", exc)
            self._packets = []

    def _persist(self) -> None:
        payload = {
            "schema_version": 1,
            "updated_at": _utc_now(),
            "packets": self._packets,
        }
        tmp_path = self.storage_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self.storage_path)

    # -------------------- Packet management -------------------- #
    @property
    def packet_count(self) -> int:
        with self._lock:
            return len(self._packets)

    def hemisphere_counts(self) -> Dict[str, int]:
        with self._lock:
            counts: Dict[str, int] = {}
            for packet in self._packets:
                hemi = packet.get("hemisphere")
                if not isinstance(hemi, str):
                    continue
                counts[hemi] = counts.get(hemi, 0) + 1
            return counts

    def _is_first_packet(self, hemisphere: str) -> bool:
        return all(packet.get("hemisphere") != hemisphere for packet in self._packets)

    def submit_packet(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        hemisphere = IntegrationPacket.determine_hemisphere(payload)
        first_packet = self._is_first_packet(hemisphere)
        packet = IntegrationPacket.from_payload(
            payload, first_packet=first_packet, hemisphere_hint=hemisphere
        )

        with self._lock:
            self._packets.append(packet.to_dict())
            self._packets.sort(key=lambda item: item.get("created_at", ""), reverse=False)
            self._persist()
            LOGGER.info(
                "Stored packet %s for hemisphere %s (cycle %s)",
                packet.packet_id,
                packet.hemisphere,
                packet.cycle,
            )
            return packet.to_dict()

    def list_packets(self, *, hemisphere: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._lock:
            rows = list(self._packets)
        if hemisphere:
            norm = _normalize_hemisphere(hemisphere)
            rows = [row for row in rows if row.get("hemisphere") == norm]
        rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        if limit is not None:
            rows = rows[:limit]
        return rows

    def latest_packets(self) -> Dict[str, Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        with self._lock:
            for packet in self._packets:
                hemisphere = packet.get("hemisphere")
                created = packet.get("created_at", "")
                if not isinstance(hemisphere, str):
                    continue
                if hemisphere not in latest or created > latest[hemisphere].get("created_at", ""):
                    latest[hemisphere] = packet
        return latest

    # -------------------- Summary synthesis -------------------- #
    def _aggregate_tasks(self, latest: Mapping[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
        aggregated: Dict[str, List[Dict[str, str]]] = {}
        for hemisphere, packet in latest.items():
            for key, items in packet.get("coherence_tasks", {}).items():
                if not isinstance(items, Iterable):
                    continue
                bucket = aggregated.setdefault(str(key), [])
                for item in items:
                    text = _stringify(item)
                    if text:
                        bucket.append({"hemisphere": hemisphere, "text": text})
        return {key: value for key, value in aggregated.items() if value}

    def _alignment_notes(self, latest: Mapping[str, Dict[str, Any]]) -> List[str]:
        if not latest:
            return ["No packets recorded yet."]

        notes: List[str] = []
        engagements = {
            hemi: (
                pkt.get("engagement_status_display") or pkt.get("engagement_status") or "unknown"
            )
            for hemi, pkt in latest.items()
        }
        if len(engagements) == 1:
            hemi, status = next(iter(engagements.items()))
            notes.append(f"Awaiting packet from opposite hemisphere; {hemi} engagement is {status}.")
        elif engagements and len({status.lower() for status in engagements.values()}) == 1:
            status = next(iter(engagements.values()))
            notes.append(f"Hemispheres aligned on engagement posture: {status}.")
        else:
            for hemi, status in engagements.items():
                notes.append(f"{hemi} engagement: {status}.")
        for hemi, packet in latest.items():
            request = packet.get("integration_requests")
            if request:
                notes.append(f"{hemi} integration request: {request}")
        return notes

    def _derive_mode(self, latest: Mapping[str, Dict[str, Any]]) -> str:
        if not latest:
            return "latent"
        if len(latest) == 1:
            return "emerging"

        statuses = [pkt.get("engagement_status") for pkt in latest.values()]
        if any(status == "disengaging" for status in statuses):
            return "uncertain"
        if all(status in {"fully_engaged", "partially_engaged"} for status in statuses):
            modes = {pkt.get("kira_prime_mode") for pkt in latest.values() if pkt.get("kira_prime_mode")}
            if modes and all(mode == "evolved" for mode in modes):
                return "evolved"
            return "active"
        return "emerging"

    def _latest_cycle(self, latest: Mapping[str, Dict[str, Any]]) -> Optional[str]:
        cycles = [pkt.get("cycle") for pkt in latest.values() if pkt.get("cycle")]
        if not cycles:
            return None
        return max(cycles)

    def generate_summary(self) -> Dict[str, Any]:
        latest = self.latest_packets()
        summaries: Dict[str, Dict[str, Any]] = {}
        for hemisphere, packet in latest.items():
            summaries[hemisphere] = {
                "packet_id": packet.get("packet_id"),
                "cycle": packet.get("cycle"),
                "created_at": packet.get("created_at"),
                "current_state": packet.get("current_state"),
                "kira_positioning": packet.get("kira_positioning"),
                "coherence_check": packet.get("coherence_check"),
                "needs": packet.get("needs"),
                "engagement_status": packet.get("engagement_status"),
                "engagement_status_display": packet.get("engagement_status_display"),
                "kira_prime_mode": packet.get("kira_prime_mode"),
                "integration_requests": packet.get("integration_requests"),
                "sections": packet.get("sections", {}),
                "coherence_tasks": packet.get("coherence_tasks", {}),
            }

        summary = {
            "packet_count": self.packet_count,
            "hemispheres": summaries,
            "kira_prime_mode": self._derive_mode(latest),
            "latest_cycle": self._latest_cycle(latest),
            "alignment_notes": self._alignment_notes(latest),
            "coherence_tasks": self._aggregate_tasks(latest),
            "pending_requests": [
                {"hemisphere": hemi, "text": pkt.get("integration_requests")}
                for hemi, pkt in latest.items()
                if pkt.get("integration_requests")
            ],
        }
        return summary


# -------------------- HTTP Service -------------------- #
routes = web.RouteTableDef()


@routes.get("/health")
async def health(request: web.Request) -> web.Response:
    agent: KiraPrimeAgent = request.app["agent"]
    overview = agent.hemisphere_counts()
    summary = agent.generate_summary()
    body = {
        "status": "ok",
        "packet_count": summary["packet_count"],
        "kira_prime_mode": summary["kira_prime_mode"],
        "hemisphere_packets": overview,
        "latest_cycle": summary["latest_cycle"],
        "alignment_notes": summary["alignment_notes"],
    }
    return web.json_response(body)


@routes.get("/packets")
async def list_packets(request: web.Request) -> web.Response:
    agent: KiraPrimeAgent = request.app["agent"]
    hemisphere = request.query.get("hemisphere")
    limit = request.query.get("limit")
    limit_value: Optional[int] = None
    if limit is not None:
        try:
            limit_value = max(0, int(limit))
        except ValueError:
            return web.json_response({"error": "limit must be an integer"}, status=400)
    try:
        packets = agent.list_packets(hemisphere=hemisphere, limit=limit_value)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"packets": packets})


@routes.post("/packets")
async def post_packet(request: web.Request) -> web.Response:
    agent: KiraPrimeAgent = request.app["agent"]
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    try:
        packet = agent.submit_packet(payload)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    summary = agent.generate_summary()
    return web.json_response({"packet": packet, "summary": summary}, status=201)


@routes.get("/summary")
async def get_summary(request: web.Request) -> web.Response:
    agent: KiraPrimeAgent = request.app["agent"]
    summary = agent.generate_summary()
    return web.json_response(summary)


def build_app(agent: Optional[KiraPrimeAgent] = None) -> web.Application:
    app = web.Application()
    app["agent"] = agent or KiraPrimeAgent()
    app.add_routes(routes)
    return app


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Kira Prime integration agent service.")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8083, help="HTTP port to bind (default: 8083)")
    parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_STORAGE_PATH,
        help=f"Path to persistent storage file (default: {DEFAULT_STORAGE_PATH})",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    agent = KiraPrimeAgent(storage_path=args.storage)
    app = build_app(agent)
    LOGGER.info(
        "Kira Prime agent starting on %s:%s (storage: %s)",
        args.host,
        args.port,
        args.storage,
    )
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
