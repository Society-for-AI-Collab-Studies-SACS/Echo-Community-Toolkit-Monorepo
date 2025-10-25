#!/usr/bin/env python3
"""Journal logging service with HTTP endpoints and ZMQ PUB broadcast."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import zmq
import zmq.asyncio
from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

from shared.utils import setup_logging


logger = setup_logging("journal")

# Prometheus metrics
JOURNAL_COMMITS_TOTAL = Counter("journal_commits_total", "Journal commits written")
JOURNAL_ERRORS_TOTAL = Counter("journal_errors_total", "Errors during commit")
JOURNAL_LAST_TS = Gauge("journal_last_commit_timestamp", "Unix ts of last commit")
JOURNAL_LEDGER_SIZE = Gauge("journal_ledger_bytes", "Approx size of JSONL ledger file")

# Environment configuration
PUB_PORT = int(os.getenv("JOURNAL_PUB_PORT", "5557"))
PUB_BIND = os.getenv("JOURNAL_PUB_ENDPOINT", f"tcp://0.0.0.0:{PUB_PORT}")
HTTP_PORT = int(os.getenv("JOURNAL_HTTP_PORT", "8082"))
LEDGER_PATH = Path(os.getenv("JOURNAL_LEDGER_PATH", "data/journals/ledger.jsonl"))
LATEST_CAP = int(os.getenv("JOURNAL_LATEST_CAP", "1000"))

# ZMQ publisher
_zctx = zmq.asyncio.Context.instance()
_pub = _zctx.socket(zmq.PUB)
_pub.setsockopt(zmq.LINGER, 0)
try:
    _pub.bind(PUB_BIND)
    logger.info("Journal PUB socket bound to %s", PUB_BIND)
except zmq.ZMQError as exc:  # pragma: no cover
    logger.error("Failed to bind PUB socket on %s: %s", PUB_BIND, exc)
    raise

_write_lock = threading.Lock()
_latest_ring: List[Dict[str, Any]] = []
_next_index = 0
_bootstrapped = False


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )


def _ensure_dirs() -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)


def _write_jsonl(entry: Dict[str, Any]) -> None:
    body = json.dumps(entry, separators=(",", ":"))
    with _write_lock:
        _ensure_dirs()
        with LEDGER_PATH.open("a", encoding="utf-8") as handle:
            handle.write(body + "\n")
        try:
            JOURNAL_LEDGER_SIZE.set(LEDGER_PATH.stat().st_size)
        except Exception:  # pragma: no cover
            pass


def _read_all_entries() -> List[Dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("Skipping malformed ledger line")
    return entries


def _append_latest(entry: Dict[str, Any]) -> None:
    _latest_ring.append(entry)
    if len(_latest_ring) > LATEST_CAP:
        del _latest_ring[: len(_latest_ring) - LATEST_CAP]


def _bootstrap_from_disk() -> None:
    global _bootstrapped, _next_index
    if _bootstrapped:
        return
    entries = _read_all_entries()
    if entries:
        _latest_ring.extend(entries[-LATEST_CAP:])
        last = entries[-1]
        if isinstance(last.get("index"), int):
            _next_index = int(last["index"]) + 1
        else:
            _next_index = len(entries)
        try:
            last_ts = last.get("time")
            if last_ts:
                JOURNAL_LAST_TS.set(datetime.fromisoformat(last_ts.replace("Z", "+00:00")).timestamp())
        except Exception:  # pragma: no cover
            pass
        try:
            JOURNAL_COMMITS_TOTAL.inc(len(entries))
        except Exception:  # pragma: no cover
            pass
    _bootstrapped = True


async def publish_update(payload: Dict[str, Any]) -> None:
    try:
        await _pub.send_json({"type": "narrative_update", "time": time.time(), **payload})
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to publish update: %s", exc)


async def health(_: web.Request) -> web.Response:
    return web.json_response(
        {
            "status": "ok",
            "service": "journal_logger",
            "pub_endpoint": PUB_BIND,
            "ledger_path": str(LEDGER_PATH),
            "latest_cached": len(_latest_ring),
        }
    )


async def metrics(_: web.Request) -> web.Response:
    data = generate_latest()
    return web.Response(body=data, headers={"Content-Type": CONTENT_TYPE_LATEST})


async def post_entry(request: web.Request) -> web.Response:
    global _next_index
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)

    content = (body.get("content") or "").strip()
    if not content:
        return web.json_response({"error": "content required"}, status=400)

    tags = body.get("tags") or []
    narrator = body.get("narrator")
    event_type = body.get("event_type")
    sigprint = body.get("sigprint")
    features = body.get("features") or {}

    now_iso = _utc_now_iso()
    entry = {
        "index": _next_index,
        "time": now_iso,
        "entry": content,
        "tags": tags,
        "narrator": narrator,
        "event_type": event_type,
        "sigprint": sigprint,
        "features": features,
    }
    _next_index += 1

    try:
        _write_jsonl(entry)
        _append_latest(entry)
        JOURNAL_COMMITS_TOTAL.inc()
        JOURNAL_LAST_TS.set(time.time())
    except Exception as exc:
        JOURNAL_ERRORS_TOTAL.inc()
        logger.exception("Failed to persist entry")
        return web.json_response({"error": str(exc)}, status=500)

    await publish_update(
        {
            "tags": tags,
            "sigprint": sigprint,
            "entry_len": len(content),
            "narrator": narrator,
            "event_type": event_type,
        }
    )

    return web.json_response({"ok": True, "index": entry["index"], "time": now_iso})


async def get_latest(request: web.Request) -> web.Response:
    try:
        n = int(request.query.get("n", "10"))
    except ValueError:
        return web.json_response({"error": "n must be an integer"}, status=400)

    n = max(1, min(n, LATEST_CAP))
    if len(_latest_ring) >= n:
        result = _latest_ring[-n:]
    else:
        result = _read_all_entries()[-n:]
    return web.json_response(result)


def _in_window(ts_iso: str, since: Optional[datetime], until: Optional[datetime]) -> bool:
    try:
        ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    except Exception:
        return False
    if since and ts < since:
        return False
    if until and ts > until:
        return False
    return True


def _rollup(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_narrator: Dict[str, int] = {}
    by_event: Dict[str, int] = {}
    by_tag: Dict[str, int] = {}
    earliest: Optional[str] = None
    latest: Optional[str] = None

    for entry in entries:
        ts = entry.get("time")
        if ts:
            earliest = ts if earliest is None or ts < earliest else earliest
            latest = ts if latest is None or ts > latest else latest

        narrator = entry.get("narrator") or "—"
        event_type = entry.get("event_type") or "—"
        by_narrator[narrator] = by_narrator.get(narrator, 0) + 1
        by_event[event_type] = by_event.get(event_type, 0) + 1

        for tag in entry.get("tags") or []:
            by_tag[tag] = by_tag.get(tag, 0) + 1

    return {
        "count": len(entries),
        "earliest": earliest,
        "latest": latest,
        "by_narrator": by_narrator,
        "by_event_type": by_event,
        "by_tag": by_tag,
    }


async def get_stats(request: web.Request) -> web.Response:
    try:
        last = request.query.get("last")
        since_q = request.query.get("since")
        until_q = request.query.get("until")

        entries = _read_all_entries()
        if last:
            try:
                n = max(1, int(last))
            except ValueError:
                return web.json_response({"error": "last must be an integer"}, status=400)
            entries = entries[-n:]
        else:
            since = datetime.fromisoformat(since_q.replace("Z", "+00:00")) if since_q else None
            until = datetime.fromisoformat(until_q.replace("Z", "+00:00")) if until_q else None
            if since or until:
                entries = [entry for entry in entries if _in_window(entry.get("time", ""), since, until)]

        return web.json_response(_rollup(entries))
    except ValueError:
        return web.json_response({"error": "Invalid ISO timestamp"}, status=400)
    except Exception as exc:
        JOURNAL_ERRORS_TOTAL.inc()
        return web.json_response({"error": str(exc)}, status=500)


def _create_app() -> web.Application:
    _bootstrap_from_disk()
    app = web.Application()
    app.add_routes(
        [
            web.get("/health", health),
            web.get("/metrics", metrics),
            web.post("/entry", post_entry),
            web.get("/latest", get_latest),
            web.get("/stats", get_stats),
        ]
    )

    async def _close_pub(_: web.Application) -> None:
        _pub.close(0)

    app.on_cleanup.append(_close_pub)
    return app


def main() -> None:
    web.run_app(_create_app(), port=HTTP_PORT, handle_signals=False)


if __name__ == "__main__":
    main()
