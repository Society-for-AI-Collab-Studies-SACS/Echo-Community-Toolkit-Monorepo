#!/usr/bin/env python3
"""
SIGPRINT Monitor Agent - Autonomous Consciousness Observer

Bridges firmware binary streams into The Living Library agent fabric:
- Connects to SIGPRINT hardware (serial or WiFi WebSocket)
- Decodes binary protocol packets
- Detects gates/loops and higher-order patterns
- Publishes updates to the ledger & Garden agents
- Serves GetLatestSigprint via gRPC
"""

import argparse
import asyncio
import json
import logging
import struct
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

import grpc
import numpy as np

try:  # Optional serial transport
    import serial
except ImportError:  # pragma: no cover
    serial = None

try:  # Optional websocket transport
    import websockets
except ImportError:  # pragma: no cover
    websockets = None

from google.protobuf import empty_pb2

from protos import agents_pb2, agents_pb2_grpc

# Firmware protocol constants
HEADER_FMT = "<HBBIHH"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
MAGIC = 0x5347
NUM_CHANNELS = 8
NUM_BANDS = 5
PACKET_MIN_SIZE = HEADER_SIZE + 376  # conservative guard (header + payload)
FFT_BANDS = ["delta", "theta", "alpha", "beta", "gamma"]


@dataclass
class AgentConfig:
    """Runtime configuration for the monitor agent."""

    serial_port: str = "/dev/ttyUSB0"
    baudrate: int = 921_600
    wifi_url: str = "ws://192.168.4.1/sigprint"
    mode: str = "serial"  # "serial" or "wifi"
    use_binary_protocol: bool = True
    packet_rate_hz: int = 25
    enabled_bands: List[str] = field(default_factory=lambda: FFT_BANDS.copy())
    gate_sensitivity: float = 0.30
    loop_window_seconds: int = 60
    agent_name: str = "sigprint_monitor"
    grpc_port: int = 50055
    publish_rate_hz: int = 1
    memory_size_samples: int = 10_000
    pattern_library_size: int = 100
    ledger_address: Optional[str] = "localhost:50051"
    garden_address: Optional[str] = "localhost:50052"
    enable_ledger: bool = True
    enable_garden: bool = True

    @classmethod
    def from_file(cls, path: str) -> "AgentConfig":
        data: Dict[str, Any] = {}
        if path.endswith(".yaml"):
            try:
                import yaml  # optional dependency

                with open(path, "r", encoding="utf-8") as fh:
                    parsed = yaml.safe_load(fh) or {}
                    if isinstance(parsed, dict):
                        data = parsed
            except Exception:
                pass
        return cls(**data)


class SIGPRINTMonitorAgent(agents_pb2_grpc.SigprintServiceServicer):
    """Stateful monitor that decodes firmware packets and fans updates out to other agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.connection: Optional[Any] = None
        self.connected = False

        # Rolling memories
        self.sigprint_history: Deque[Dict[str, Any]] = deque(maxlen=config.memory_size_samples)
        self.event_history: Deque[Dict[str, Any]] = deque(maxlen=1_000)
        self.pattern_matches: Deque[str] = deque(maxlen=100)
        self.known_patterns: Dict[str, str] = {}

        # Runtime stats
        self.total_packets = 0
        self.total_events = 0
        self.gate_counts = {band: 0 for band in FFT_BANDS}
        self.loop_counts = {band: 0 for band in FFT_BANDS}
        self.state = "INITIALIZING"
        self.state_history: Deque[Dict[str, Any]] = deque(maxlen=100)

        # Current reading cache
        self.current_packet: Optional[Dict[str, Any]] = None
        self.last_update_msg: Optional[agents_pb2.SigprintUpdate] = None
        self.prev_sigprint: Optional[str] = None

        # gRPC services
        self.grpc_server: Optional[grpc.aio.Server] = None
        self.ledger_channel = None
        self.ledger_stub = None
        self.garden_channel = None
        self.garden_stub = None
        if self.config.enable_ledger and self.config.ledger_address:
            try:
                self.ledger_channel = grpc.aio.insecure_channel(self.config.ledger_address)
                self.ledger_stub = agents_pb2_grpc.LedgerServiceStub(
                    self.ledger_channel
                )
            except Exception as exc:  # pragma: no cover
                self.logger.warning("Unable to init ledger stub: %s", exc)
        if self.config.enable_garden and self.config.garden_address:
            try:
                self.garden_channel = grpc.aio.insecure_channel(self.config.garden_address)
                self.garden_stub = agents_pb2_grpc.GardenServiceStub(
                    self.garden_channel
                )
            except Exception as exc:  # pragma: no cover
                self.logger.warning("Unable to init garden stub: %s", exc)

    # --------------------------------------------------------------------- #
    # Logging / setup
    # --------------------------------------------------------------------- #
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.config.agent_name)
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            logger.addHandler(handler)
        return logger

    # --------------------------------------------------------------------- #
    # Connections
    # --------------------------------------------------------------------- #
    async def connect(self) -> bool:
        """Connect to hardware."""
        self.logger.info("Connecting via %s...", self.config.mode)
        if self.config.mode == "serial":
            return self._connect_serial()
        return await self._connect_wifi()

    def _connect_serial(self) -> bool:
        if serial is None:  # pragma: no cover
            self.logger.error("pyserial not installed; cannot open serial port")
            return False
        try:
            self.connection = serial.Serial(
                self.config.serial_port,
                self.config.baudrate,
                timeout=0.05,
            )
            self.connected = True
            self.logger.info("Serial connected: %s", self.config.serial_port)
            return True
        except Exception as exc:
            self.logger.error("Serial connection failed: %s", exc)
            return False

    async def _connect_wifi(self) -> bool:
        if websockets is None:  # pragma: no cover
            self.logger.error("websockets package not installed; cannot connect via WiFi")
            return False
        try:
            self.connection = await websockets.connect(self.config.wifi_url, max_size=None)
            self.connected = True
            self.logger.info("WebSocket connected: %s", self.config.wifi_url)
            return True
        except Exception as exc:
            self.logger.error("WiFi connection failed: %s", exc)
            return False

    # --------------------------------------------------------------------- #
    # Packet decoding
    # --------------------------------------------------------------------- #
    def process_packet(self, packet: bytes) -> Optional[Dict[str, Any]]:
        """Decode a binary packet into structured data."""
        if len(packet) < HEADER_SIZE:
            return None
        magic, version, packet_type, ts_ms, payload_len, checksum = struct.unpack_from(
            HEADER_FMT, packet, 0
        )
        if magic != MAGIC or payload_len + HEADER_SIZE > len(packet):
            return None

        payload = memoryview(packet)[HEADER_SIZE : HEADER_SIZE + payload_len]
        try:
            parsed = self._parse_payload(payload)
        except Exception as exc:
            self.logger.debug("Failed to parse packet: %s", exc)
            return None

        parsed["timestamp_ms"] = ts_ms
        parsed["version"] = version
        parsed["packet_type"] = packet_type
        parsed["checksum"] = checksum
        self.total_packets += 1
        return parsed

    def _parse_payload(self, payload: memoryview) -> Dict[str, Any]:
        """Parse firmware payload (see README_ENHANCED.md for layout)."""
        offset = 0
        channel_count = payload[offset]
        offset += 1

        raw_samples: List[int] = []
        for _ in range(channel_count):
            sample_bytes = payload[offset : offset + 3]
            offset += 3
            value = int.from_bytes(sample_bytes, "little", signed=False)
            if value & 0x800000:
                value -= 1 << 24
            raw_samples.append(value)

        band_power = np.zeros((channel_count, NUM_BANDS), dtype=float)
        for ch in range(channel_count):
            for band in range(NUM_BANDS):
                band_power[ch, band] = struct.unpack_from("<f", payload, offset)[0]
                offset += 4

        band_phase = np.zeros((channel_count, NUM_BANDS), dtype=float)
        for ch in range(channel_count):
            for band in range(NUM_BANDS):
                band_phase[ch, band] = struct.unpack_from("<f", payload, offset)[0]
                offset += 4

        # SIGPRINT code (10 BCD bytes -> 20 digits)
        code_digits = []
        for _ in range(10):
            bcd = payload[offset]
            offset += 1
            code_digits.append(str((bcd >> 4) & 0x0F))
            code_digits.append(str(bcd & 0x0F))
        sigprint_code = "".join(code_digits)

        coherence = struct.unpack_from("<f", payload, offset)[0]
        offset += 4
        gate_flags = payload[offset]
        offset += 1
        loop_flags = payload[offset]
        offset += 1
        entropy = struct.unpack_from("<f", payload, offset)[0]
        offset += 4

        # reserved 4 bytes
        offset += 4

        stage = payload[offset]
        offset += 1
        zipper_freq = struct.unpack_from("<H", payload, offset)[0]

        return {
            "sigprint": sigprint_code,
            "coherence": float(coherence),
            "gate_flags": int(gate_flags),
            "loop_flags": int(loop_flags),
            "entropy": float(entropy),
            "stage": int(stage),
            "zipper_freq": int(zipper_freq),
            "raw_samples": raw_samples,
            "band_power": band_power.tolist(),
            "band_phase": band_phase.tolist(),
        }

    # --------------------------------------------------------------------- #
    # Pattern recognition / state
    # --------------------------------------------------------------------- #
    def detect_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Basic pattern detection over recent history."""
        discoveries: List[Dict[str, Any]] = []

        signature = self._signature_for(data)
        for pattern_id, stored_sig in self.known_patterns.items():
            similarity = self._similarity(signature, stored_sig)
            if similarity > 0.8:
                discoveries.append(
                    {
                        "type": "known_pattern",
                        "pattern_id": pattern_id,
                        "similarity": similarity,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                self.pattern_matches.append(pattern_id)

        emergence = self._detect_emergence()
        if emergence:
            discoveries.append(emergence)

        if data["coherence"] > 0.7:
            discoveries.append(
                {
                    "type": "high_coherence",
                    "value": data["coherence"],
                    "bands": self._coherent_bands(data),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        return discoveries

    def _signature_for(self, data: Dict[str, Any]) -> str:
        features = {
            "sigprint_prefix": data["sigprint"][:8],
            "coherence_bin": int(max(0.0, min(1.0, data["coherence"])) * 10),
            "dominant_band": self._dominant_band(data),
            "entropy_bin": int(max(0.0, data["entropy"]) * 10),
        }
        return json.dumps(features, sort_keys=True)

    @staticmethod
    def _similarity(sig_a: str, sig_b: str) -> float:
        max_len = max(len(sig_a), len(sig_b))
        if max_len == 0:
            return 1.0
        dist = sum(a != b for a, b in zip(sig_a, sig_b))
        dist += abs(len(sig_a) - len(sig_b))
        return 1.0 - dist / max_len

    def _detect_emergence(self) -> Optional[Dict[str, Any]]:
        if len(self.sigprint_history) < 20:
            return None
        recent = list(self.sigprint_history)[-20:]
        for window in range(3, 10):
            for idx in range(len(recent) - window * 2):
                chunk1 = recent[idx : idx + window]
                chunk2 = recent[idx + window : idx + window * 2]
                if self._windows_similar(chunk1, chunk2):
                    return {
                        "type": "emergence",
                        "pattern_length": window,
                        "confidence": min(0.95, 0.6 + window * 0.05),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
        return None

    @staticmethod
    def _windows_similar(window_a: List[Dict[str, Any]], window_b: List[Dict[str, Any]]) -> bool:
        similars = []
        for a, b in zip(window_a, window_b):
            code_a = a.get("sigprint")
            code_b = b.get("sigprint")
            if code_a and code_b:
                similars.append(sum(x == y for x, y in zip(code_a, code_b)) / 20.0)
        return bool(similars) and float(np.mean(similars)) > 0.7

    def _dominant_band(self, data: Dict[str, Any]) -> str:
        arr = np.array(data["band_power"], dtype=float)
        avg = np.mean(arr, axis=0)
        return FFT_BANDS[int(np.argmax(avg))]

    def _coherent_bands(self, data: Dict[str, Any]) -> List[str]:
        phases = np.array(data["band_phase"], dtype=float)
        coherent = []
        for idx, band in enumerate(FFT_BANDS):
            plv = abs(np.mean(np.exp(1j * phases[:, idx])))
            if plv > 0.5:
                coherent.append(band)
        return coherent

    def update_state(self, data: Dict[str, Any], patterns: List[Dict[str, Any]]) -> None:
        previous = self.state
        if not self.connected:
            self.state = "DISCONNECTED"
        elif self.total_packets < 5:
            self.state = "INITIALIZING"
        elif any(p["type"] == "emergence" for p in patterns):
            self.state = "EMERGENCE_DETECTED"
        elif data["coherence"] > 0.8:
            self.state = "HIGH_COHERENCE"
        elif data["entropy"] > 0.7:
            self.state = "HIGH_COMPLEXITY"
        elif data["gate_flags"]:
            self.state = "TRANSITION"
        else:
            self.state = "MONITORING"

        if self.state != previous:
            self.logger.info("State transition: %s → %s", previous, self.state)
            self.state_history.append(
                {
                    "from": previous,
                    "to": self.state,
                    "timestamp": datetime.utcnow().isoformat(),
                    "trigger": patterns[0] if patterns else None,
                }
            )

    # --------------------------------------------------------------------- #
    # gRPC (SigprintService)
    # --------------------------------------------------------------------- #
    def GetLatestSigprint(self, request, context):  # noqa: N802 (proto naming)
        if self.last_update_msg:
            return self.last_update_msg
        return agents_pb2.SigprintUpdate(
            time="", sigprint="", coherence=0.0, features={}
        )

    async def start_grpc_server(self) -> None:
        self.grpc_server = grpc.aio.server()
        agents_pb2_grpc.add_SigprintServiceServicer_to_server(self, self.grpc_server)
        bind_addr = f"[::]:{self.config.grpc_port}"
        self.grpc_server.add_insecure_port(bind_addr)
        await self.grpc_server.start()
        self.logger.info("gRPC SigprintService listening on %s", bind_addr)

    # --------------------------------------------------------------------- #
    # Publishing
    # --------------------------------------------------------------------- #
    def _build_update_message(self, data: Dict[str, Any], patterns: List[Dict[str, Any]]) -> agents_pb2.SigprintUpdate:
        ts_iso = datetime.utcnow().isoformat() + "Z"
        features: Dict[str, float] = {
            "entropy": data["entropy"],
            "stage": float(data["stage"]),
            "zipper_freq": float(data["zipper_freq"]),
            "gate_flags": float(data["gate_flags"]),
            "loop_flags": float(data["loop_flags"]),
        }
        avg_power = np.mean(np.array(data["band_power"], dtype=float), axis=0)
        for idx, band in enumerate(FFT_BANDS):
            features[f"{band}_power"] = float(avg_power[idx])
        return agents_pb2.SigprintUpdate(
            time=ts_iso,
            sigprint=data["sigprint"],
            coherence=max(0.0, min(100.0, data["coherence"] * 100.0)),
            features=features,
        )

    async def publish(self, data: Dict[str, Any], patterns: List[Dict[str, Any]]) -> None:
        update_msg = self._build_update_message(data, patterns)
        self.last_update_msg = update_msg

        # Ledger commit (best-effort)
        if self.ledger_stub:
            entry = agents_pb2.LedgerEntry(
                time=update_msg.time,
                type="SIGPRINT",
                text="",
                sigprint=update_msg.sigprint,
                coherence=update_msg.coherence,
                features=update_msg.features,
            )
            try:
                await self.ledger_stub.CommitEntry(entry)
            except Exception as exc:  # pragma: no cover
                self.logger.debug("Ledger commit failed: %s", exc)

        # Garden notifications on transitions
        if self.garden_stub and (data["gate_flags"] or self._sigprint_delta(data["sigprint"]) > 5):
            description = {
                "sigprint": data["sigprint"],
                "coherence": update_msg.coherence,
                "gate_flags": data["gate_flags"],
                "state": self.state,
            }
            try:
                await self.garden_stub.NotifyEvent(
                    agents_pb2.GardenEvent(
                        event_type="STATE_CHANGE",
                        description=json.dumps(description),
                    )
                )
            except Exception as exc:  # pragma: no cover
                self.logger.debug("Garden notify failed: %s", exc)

    def _sigprint_delta(self, new_code: str) -> int:
        if self.prev_sigprint is None:
            self.prev_sigprint = new_code
            return 0
        diff = sum(a != b for a, b in zip(new_code, self.prev_sigprint))
        self.prev_sigprint = new_code
        return diff

    # --------------------------------------------------------------------- #
    # Main loop
    # --------------------------------------------------------------------- #
    async def run(self) -> None:
        self.logger.info("Starting SIGPRINT monitor agent")
        if not await self.connect():
            self.logger.error("Connection failed; exiting.")
            return

        await self.start_grpc_server()

        buffer = bytearray()
        publish_interval = 1.0 / max(0.1, self.config.publish_rate_hz)
        last_publish = 0.0

        try:
            while True:
                await self._pump_transport(buffer)
                packet = self._extract_packet(buffer)
                if packet is None:
                    await asyncio.sleep(0.001)
                    continue

                data = self.process_packet(packet)
                if not data:
                    continue

                self.sigprint_history.append(data)
                self.current_packet = data

                # Counts
                for idx, band in enumerate(FFT_BANDS):
                    if data["gate_flags"] & (1 << idx):
                        self.gate_counts[band] += 1
                    if data["loop_flags"] & (1 << idx):
                        self.loop_counts[band] += 1

                patterns = self.detect_patterns(data)
                if patterns:
                    self.total_events += len(patterns)
                    self.event_history.extend(patterns)

                self.update_state(data, patterns)

                now = asyncio.get_event_loop().time()
                if now - last_publish >= publish_interval:
                    await self.publish(data, patterns)
                    last_publish = now
        except asyncio.CancelledError:  # pragma: no cover
            pass
        except KeyboardInterrupt:
            self.logger.info("Received interrupt, shutting down.")
        finally:
            await self.shutdown()

    async def _pump_transport(self, buffer: bytearray) -> None:
        if self.config.mode == "serial":
            if serial and self.connection and self.connection.in_waiting:
                buffer.extend(self.connection.read(self.connection.in_waiting))
        else:
            if self.connection is None:
                return
            try:
                msg = await asyncio.wait_for(self.connection.recv(), timeout=0.05)
                if isinstance(msg, (bytes, bytearray)):
                    buffer.extend(msg)
            except asyncio.TimeoutError:
                pass

    def _extract_packet(self, buffer: bytearray) -> Optional[bytes]:
        if len(buffer) < HEADER_SIZE:
            return None
        magic_index = buffer.find(b"\x47\x53")  # 0x5347 little-endian
        if magic_index == -1:
            buffer.clear()
            return None
        if magic_index > 0:
            del buffer[:magic_index]
        if len(buffer) < HEADER_SIZE:
            return None
        payload_len = struct.unpack_from("<H", buffer, 8)[0]
        total_len = HEADER_SIZE + payload_len
        if len(buffer) < total_len:
            return None
        packet = bytes(buffer[:total_len])
        del buffer[:total_len]
        return packet

    async def shutdown(self) -> None:
        if self.connection:
            if self.config.mode == "serial":
                try:
                    self.connection.close()
                except Exception:  # pragma: no cover
                    pass
            else:
                try:
                    await self.connection.close()
                except Exception:  # pragma: no cover
                    pass
            self.connection = None

        if self.grpc_server:
            await self.grpc_server.stop(grace=5)
            self.grpc_server = None

        if self.ledger_channel:
            await self.ledger_channel.close()
            self.ledger_channel = None
        if self.garden_channel:
            await self.garden_channel.close()
            self.garden_channel = None

        self._save_patterns()
        self.logger.info("Monitor agent shutdown complete")

    def _save_patterns(self) -> None:
        path = f"{self.config.agent_name}_patterns.json"
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "patterns": self.known_patterns,
                        "statistics": {
                            "total_packets": self.total_packets,
                            "total_events": self.total_events,
                            "gate_counts": self.gate_counts,
                            "loop_counts": self.loop_counts,
                        },
                        "state_history": list(self.state_history),
                    },
                    fh,
                    indent=2,
                )
            self.logger.info("Pattern library saved to %s", path)
        except Exception as exc:  # pragma: no cover
            self.logger.debug("Failed to save pattern library: %s", exc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SIGPRINT Monitor Agent")
    parser.add_argument("--config", default=None, help="YAML config path")
    parser.add_argument("--port", help="Serial port override")
    parser.add_argument("--mode", choices=["serial", "wifi"], help="Connection mode")
    parser.add_argument("--wifi-url", help="WebSocket URL override")
    parser.add_argument("--grpc-port", type=int, help="gRPC listen port")
    parser.add_argument("--ledger-address", help="Ledger gRPC address")
    parser.add_argument("--garden-address", help="Garden gRPC address")
    parser.add_argument("--publish-rate", type=float, help="Publish rate in Hz")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> AgentConfig:
    cfg = AgentConfig.from_file(args.config) if args.config else AgentConfig()
    overrides: Dict[str, Any] = {}
    if args.port:
        overrides["serial_port"] = args.port
    if args.mode:
        overrides["mode"] = args.mode
    if args.wifi_url:
        overrides["wifi_url"] = args.wifi_url
    if args.grpc_port:
        overrides["grpc_port"] = args.grpc_port
    if args.ledger_address:
        overrides["ledger_address"] = args.ledger_address
    if args.garden_address:
        overrides["garden_address"] = args.garden_address
    if args.publish_rate:
        overrides["publish_rate_hz"] = args.publish_rate
    if overrides:
        cfg = AgentConfig(**{**cfg.__dict__, **overrides})
    return cfg


def main() -> None:
    args = parse_args()
    config = build_config(args)
    agent = SIGPRINTMonitorAgent(config)
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
