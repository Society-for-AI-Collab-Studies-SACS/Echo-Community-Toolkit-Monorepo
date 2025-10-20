#!/usr/bin/env python3
"""
SIGPRINT Agent Service (LSB Steganography)
-----------------------------------------

Autonomous service for LSB steganography encoding using the Echo-Community-Toolkit.

Features
- ZeroMQ REP socket API (JSON messages)
- Optional cover image support or on-the-fly noise cover generation
- CRC-enabled payload encoding and verification
- Lightweight HTTP health endpoint on port 8080

Request schema (JSON)
{
  "message": "...",                  # string (required)
  "cover_image_path": "/path.png",   # optional string
  "output_path": "output.png",       # optional string (default: output.png)
  "use_crc": true,                   # optional bool (default: true)
  "image_size": [512, 512]           # optional [w, h] when generating cover
}

Response schema (JSON)
{
  "success": true/false,
  "output_path": "output.png",
  "payload_size": 1234,
  "crc32": "abcd1234",
  "capacity_used": "N/CAP",
  "error": "...optional message..."
}
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from aiohttp import web
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import zmq.asyncio


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sigprint_lsb_agent")

# Prometheus metrics (minimal)
SIGPRINT_REQUESTS_TOTAL = Counter("sigprint_requests_total", "Total SIGPRINT requests")
SIGPRINT_ERRORS_TOTAL = Counter("sigprint_errors_total", "SIGPRINT request errors")


@dataclass
class SigprintRequest:
    message: str
    cover_image_path: Optional[str] = None
    output_path: str = "output.png"
    use_crc: bool = True
    image_size: Tuple[int, int] = (512, 512)


@dataclass
class SigprintResponse:
    success: bool
    output_path: str
    payload_size: int
    crc32: str
    capacity_used: str
    error: Optional[str] = None


def _maybe_add_toolkit_to_sys_path() -> None:
    """Add Echo-Community-Toolkit source path to sys.path if present.

    Tries common locations used across the repo:
    - tools/echo-toolkit/src
    - Echo-Community-Toolkit/src
    - <repo_root>/tools/echo-toolkit/src (relative walk)
    """

    candidates = []
    here = Path(__file__).resolve()
    repo_root = here
    for _ in range(5):  # climb a few levels to find repo root heuristically
        if (repo_root / ".git").exists() or (repo_root / "agents").exists():
            break
        repo_root = repo_root.parent

    candidates.extend(
        [
            repo_root / "tools" / "echo-toolkit" / "src",
            repo_root / "Echo-Community-Toolkit" / "src",
        ]
    )

    for p in candidates:
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))


class SigprintAgent:
    """SIGPRINT encoding agent using LSB steganography."""

    def __init__(self, port: int = 5555):
        self.port = port
        self.context = zmq.asyncio.Context()
        self.socket: Optional[zmq.asyncio.Socket] = None
        self.running = False

        # Import LSB modules
        try:
            _maybe_add_toolkit_to_sys_path()
            from lsb_encoder_decoder import LSBCodec  # type: ignore
            from lsb_extractor import LSBExtractor  # type: ignore

            self.codec = LSBCodec(bpc=1)
            self.extractor = LSBExtractor()
            logger.info("LSB modules loaded successfully")
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to import LSB modules: %s", exc)
            raise

    async def start(self) -> None:
        """Start the agent service (ZeroMQ REP)."""
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.port}")
        self.running = True
        logger.info("SIGPRINT Agent listening on port %s", self.port)

        try:
            while self.running:
                try:
                    message = await self.socket.recv_json()
                except Exception as exc:  # pragma: no cover
                    logger.error("Invalid request: %s", exc)
                    await self._safe_send(
                        SigprintResponse(
                            success=False,
                            output_path="",
                            payload_size=0,
                            crc32="",
                            capacity_used="",
                            error="invalid JSON",
                        )
                    )
                    continue

                response = await self.process_request(message)
                await self._safe_send(response)
        except asyncio.CancelledError:  # pragma: no cover
            pass
        except Exception as exc:
            logger.error("Agent error: %s", exc)
        finally:
            self.cleanup()

    async def _safe_send(self, resp: SigprintResponse) -> None:
        if self.socket is not None:
            try:
                await self.socket.send_json(asdict(resp))
            except Exception as exc:  # pragma: no cover
                logger.error("Failed sending response: %s", exc)

    async def process_request(self, message: Dict[str, Any]) -> SigprintResponse:
        """Process encoding request."""
        try:
            request = SigprintRequest(**message)
            try:
                SIGPRINT_REQUESTS_TOTAL.inc()
            except Exception:
                pass
            logger.info("Processing request → %s", request.output_path)

            # Create or load cover image
            if request.cover_image_path and Path(request.cover_image_path).exists():
                cover_path = Path(request.cover_image_path)
                width, height = request.image_size
            else:
                # Generate noise cover
                width, height = request.image_size
                cover = self.codec.create_cover_image(width, height, "noise")
                cover_path = Path("/tmp/temp_cover.png")
                cover.save(str(cover_path), "PNG")

            # Compute capacity for requested size
            capacity = self.codec.calculate_capacity(width, height)

            encoded_message = base64.b64encode(request.message.encode("utf-8"))
            needed = len(encoded_message) + 14  # reserve header bytes
            if needed > capacity:
                return SigprintResponse(
                    success=False,
                    output_path="",
                    payload_size=0,
                    crc32="",
                    capacity_used=f"{needed}/{capacity}",
                    error=f"Message too large: needs {needed}, capacity {capacity}",
                )

            # Encode message
            result = self.codec.encode_message(
                cover_path,
                request.message,
                Path(request.output_path),
                use_crc=request.use_crc,
            )

            # Verify encoding
            verification = self.extractor.extract_from_image(Path(request.output_path))
            if isinstance(verification, dict) and "error" in verification:
                return SigprintResponse(
                    success=False,
                    output_path=request.output_path,
                    payload_size=int(result.get("payload_length", 0)),
                    crc32=str(result.get("crc32", "")),
                    capacity_used=f"{result.get('total_embedded', 0)}/{capacity}",
                    error=f"Verification failed: {verification['error']}",
                )

            return SigprintResponse(
                success=True,
                output_path=request.output_path,
                payload_size=int(result.get("payload_length", 0)),
                crc32=str(result.get("crc32", "")),
                capacity_used=f"{result.get('total_embedded', 0)}/{capacity}",
            )

        except Exception as exc:
            logger.error("Processing error: %s", exc)
            try:
                SIGPRINT_ERRORS_TOTAL.inc()
            except Exception:
                pass
            return SigprintResponse(
                success=False,
                output_path="",
                payload_size=0,
                crc32="",
                capacity_used="",
                error=str(exc),
            )

    def cleanup(self) -> None:
        if self.socket:
            try:
                self.socket.close()
            except Exception:  # pragma: no cover
                pass
        self.context.term()
        logger.info("SIGPRINT Agent shutdown complete")

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "service": "sigprint-agent",
            "port": self.port,
            "codec_version": "LSB1",
            "running": self.running,
        }


async def main() -> None:
    agent = SigprintAgent()

    async def health_handler(request):  # type: ignore[no-redef]
        health = await agent.health_check()
        return web.json_response(health)

    async def metrics_handler(_: web.Request) -> web.Response:
        data = generate_latest()
        return web.Response(body=data, headers={"Content-Type": CONTENT_TYPE_LATEST})

    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/metrics", metrics_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)

    await asyncio.gather(site.start(), agent.start())


if __name__ == "__main__":
    asyncio.run(main())
