#!/usr/bin/env python3
"""Lightweight SIGPRINT agent stub for development stacks."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict

import zmq.asyncio
from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

from shared.utils import setup_logging


logger = setup_logging("sigprint")

SIGPRINT_REQUESTS_TOTAL = Counter("sigprint_requests_total", "Total SIGPRINT requests")
SIGPRINT_ERRORS_TOTAL = Counter("sigprint_errors_total", "SIGPRINT request errors")
SIGPRINT_LAST_SIZE = Gauge("sigprint_last_payload_bytes", "Size of last encoded payload")


def _encode_payload(message: str) -> Dict[str, Any]:
    encoded = base64.b64encode(message.encode("utf-8")).decode("ascii")
    size = len(encoded)
    SIGPRINT_LAST_SIZE.set(size)
    return {
        "success": True,
        "output_path": "memory://sigprint",
        "payload_size": size,
        "crc32": f"{size:08x}",
        "capacity_used": f"{size}/8192",
        "error": None,
        "encoded": encoded,
    }


@dataclass
class SigprintRequest:
    message: str
    cover_image_path: str | None = None
    output_path: str = "output.png"
    use_crc: bool = True


class SigprintAgent:
    def __init__(self, port: int = 5555) -> None:
        self.port = port
        self.context = zmq.asyncio.Context()
        self.socket: zmq.asyncio.Socket | None = None

    async def start(self) -> None:
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.port}")
        logger.info("SIGPRINT agent listening on ZMQ port %s", self.port)
        while True:
            try:
                payload = await self.socket.recv_json()
            except Exception as exc:  # pragma: no cover
                logger.error("Malformed request: %s", exc)
                SIGPRINT_ERRORS_TOTAL.inc()
                await self.socket.send_json({"success": False, "error": "invalid JSON"})
                continue

            try:
                SIGPRINT_REQUESTS_TOTAL.inc()
                request = SigprintRequest(**payload)
                response = _encode_payload(request.message)
                await self.socket.send_json(response)
            except Exception as exc:  # pragma: no cover
                SIGPRINT_ERRORS_TOTAL.inc()
                logger.error("Encoding failed: %s", exc)
                await self.socket.send_json({"success": False, "error": str(exc)})


async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "sigprint"})


async def metrics(_: web.Request) -> web.Response:
    data = generate_latest()
    return web.Response(body=data, headers={"Content-Type": CONTENT_TYPE_LATEST})


async def run_http(agent: SigprintAgent) -> None:
    app = web.Application()
    app.add_routes([web.get("/health", health), web.get("/metrics", metrics)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    await agent.start()


async def main() -> None:
    agent = SigprintAgent()
    await run_http(agent)


if __name__ == "__main__":
    asyncio.run(main())
