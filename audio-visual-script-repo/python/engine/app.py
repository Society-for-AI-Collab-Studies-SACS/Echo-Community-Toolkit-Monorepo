"""ZeroMQ-based narrative engine service scaffold."""

from __future__ import annotations

import json
import signal
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict

import zmq


@dataclass
class EngineConfig:
    endpoint: str = "tcp://127.0.0.1:5559"


def handle_message(message: Dict[str, Any]) -> Dict[str, Any]:
    action = message.get("action")
    if action == "ping":
        return {"status": "ok", "pong": True}
    return {"status": "error", "error": f"Unknown action: {action}"}


def serve(config: EngineConfig) -> None:
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(config.endpoint)

    print(f"[python-engine] Listening on {config.endpoint}")

    def shutdown(_signum, _frame) -> None:
        print("[python-engine] Shutting down…")
        socket.close(0)
        context.term()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        raw = socket.recv()
        payload = json.loads(raw.decode("utf-8"))
        response = handle_message(payload)
        socket.send_json(response)
        time.sleep(0.01)


if __name__ == "__main__":
    serve(EngineConfig())
