"""
Async collaboration server for The Living Library.

The service exposes:

* A WebSocket endpoint (``/ws``) that coordinates dictation, agent
  feedback, and presence signals for each workspace.
* REST endpoints for health, presence inspection, and triggering the
  20-chapter MRP pipeline once a session is ready.
* Hydrated workspace storage so that all collaboration events are
  mirrored under ``workspaces/<id>/collab/events.jsonl`` and dictation
  transcripts stay synchronised with the MRP encoder.

Redis (pub/sub) and PostgreSQL (durable storage) are used when
available.  During tests or development without those services the
server transparently falls back to in-memory stores while keeping the
same API surface.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from library_core.dictation import DictationSession, start_session
from library_core.dictation.pipeline import MRPPipeline
from workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


def _env(key: str, default: Optional[str]) -> Optional[str]:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    return value


@dataclass(slots=True)
class CollaborationConfig:
    """Runtime configuration for the collaboration service."""

    redis_url: Optional[str] = field(
        default_factory=lambda: _env("COLLAB_REDIS_URL", "redis://localhost:6379/0")
    )
    postgres_dsn: Optional[str] = field(
        default_factory=lambda: _env(
            "COLLAB_POSTGRES_DSN",
            "postgresql://vesselos:password@localhost:5432/vesselos_collab",
        )
    )
    idle_timeout_seconds: float = 30.0
    sweep_interval_seconds: float = 5.0


@dataclass(slots=True)
class ClientConnection:
    """Represents an active WebSocket client."""

    websocket: WebSocket
    workspace_id: str
    user_id: str
    session_id: str
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def client_id(self) -> str:
        return f"{self.workspace_id}:{self.session_id}:{self.user_id}"


class MRPRunRequest(BaseModel):
    """Request body for triggering an MRP pipeline run."""

    sessionId: Optional[str] = Field(
        None, description="Session identifier (defaults to the active connection)."
    )
    runSchema: bool = Field(True, description="Execute schema_builder.py before chapters.")
    runValidation: bool = Field(
        False, description="Run kira-prime validation after generating chapters."
    )


class MRPRunResponse(BaseModel):
    """Response payload for an MRP pipeline run."""

    workspaceId: str
    sessionId: str
    outputPath: str
    timestamp: str


class CollaborationServer:
    """Coordinates WebSocket clients, Redis pub/sub, and PostgreSQL storage."""

    def __init__(
        self,
        *,
        manager: WorkspaceManager | None = None,
        config: CollaborationConfig | None = None,
    ) -> None:
        self._config = config or CollaborationConfig()
        self._manager = manager or WorkspaceManager()

        self._clients: Dict[str, ClientConnection] = {}
        self._sessions: Dict[Tuple[str, str], DictationSession] = {}
        self._participants: Dict[Tuple[str, str], set[str]] = defaultdict(set)

        self._redis_pub: Optional[Redis] = None
        self._redis_sub: Optional[Redis] = None
        self._redis_task: Optional[asyncio.Task[None]] = None
        self._pg_pool: Optional[asyncpg.Pool] = None

        self._sweep_task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()

        # In-memory fallbacks when Redis/PostgreSQL are disabled or unavailable.
        self._memory_presence: Dict[Tuple[str, str], datetime] = {}
        self._memory_events: List[Dict[str, Any]] = []

        self._workspace_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)  # type: ignore[arg-type]

    # ------------------------------------------------------------------ lifecycle

    async def startup(self) -> None:
        """Initialise external services and background tasks."""
        logger.info(
            "Starting collaboration server (redis=%s, postgres=%s)",
            self._config.redis_url,
            self._config.postgres_dsn,
        )

        if self._config.postgres_dsn:
            try:
                self._pg_pool = await asyncpg.create_pool(self._config.postgres_dsn)
                await self._prepare_database()
                logger.info("Connected to PostgreSQL")
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("PostgreSQL unavailable (%s); using in-memory store", exc)
                self._pg_pool = None

        if self._config.redis_url:
            try:
                self._redis_pub = Redis.from_url(
                    self._config.redis_url, encoding="utf-8", decode_responses=True
                )
                self._redis_sub = Redis.from_url(
                    self._config.redis_url, encoding="utf-8", decode_responses=True
                )
                self._redis_task = asyncio.create_task(self._redis_listener())
                logger.info("Connected to Redis")
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Redis unavailable (%s); falling back to local broadcast", exc)
                self._redis_pub = None
                if self._redis_task:
                    self._redis_task.cancel()
                self._redis_task = None

        self._stop_event.clear()
        self._sweep_task = asyncio.create_task(self._heartbeat_sweeper())

    async def shutdown(self) -> None:
        """Tear down external services and background tasks."""
        self._stop_event.set()

        for task in (self._redis_task, self._sweep_task):
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        if self._redis_pub:
            await self._redis_pub.close()
        if self._redis_sub:
            await self._redis_sub.close()
        if self._pg_pool:
            await self._pg_pool.close()

        self._clients.clear()
        self._sessions.clear()
        self._participants.clear()

    # ------------------------------------------------------------------ HTTP API

    async def health(self) -> Dict[str, Any]:
        """Return service and dependency status."""
        status = {
            "status": "ok",
            "clients": len(self._clients),
            "services": {
                "redis": "connected" if self._redis_pub else "offline",
                "postgres": "connected" if self._pg_pool else "offline",
            },
        }

        if self._pg_pool:
            try:
                async with self._pg_pool.acquire() as conn:
                    await conn.execute("SELECT 1")
            except Exception as exc:  # pragma: no cover - defensive
                status["services"]["postgres"] = f"error: {exc}"
        if self._redis_pub:
            try:
                await self._redis_pub.ping()
            except Exception as exc:  # pragma: no cover - defensive
                status["services"]["redis"] = f"error: {exc}"

        return status

    async def get_presence(self, workspace_id: str) -> Dict[str, Any]:
        """Retrieve active users for ``workspace_id``."""
        cutoff = datetime.now(UTC) - timedelta(minutes=5)
        if self._pg_pool:
            async with self._pg_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT user_id, last_seen
                    FROM presence
                    WHERE workspace_id = $1 AND last_seen > $2
                    ORDER BY last_seen DESC
                    """,
                    workspace_id,
                    cutoff,
                )
            users = [
                {"user_id": row["user_id"], "last_seen": row["last_seen"].isoformat()}
                for row in rows
            ]
        else:
            users = [
                {"user_id": user, "last_seen": ts.isoformat()}
                for (ws, user), ts in self._memory_presence.items()
                if ws == workspace_id and ts > cutoff
            ]
            users.sort(key=lambda entry: entry["last_seen"], reverse=True)

        return {"workspace_id": workspace_id, "active_users": len(users), "users": users}

    async def run_mrp(self, workspace_id: str, body: MRPRunRequest) -> MRPRunResponse:
        """Trigger the MRP encoder for ``workspace_id``."""
        session = self._ensure_session(workspace_id, body.sessionId)
        lock = self._workspace_locks[workspace_id]

        try:
            async with lock:
                output_path = await asyncio.to_thread(
                    self._execute_mrp_pipeline,
                    session,
                    run_schema=body.runSchema,
                    run_validation=body.runValidation,
                )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("MRP pipeline failed for workspace %s", workspace_id)
            raise HTTPException(status_code=500, detail=f"MRP pipeline failed: {exc}") from exc

        timestamp = datetime.now(UTC).isoformat()
        session.update_metadata(last_mrp_run=timestamp, mrp_output=str(output_path))

        await self._record_event(
            workspace_id,
            session.session_id,
            None,
            "mrp_complete",
            {"output": str(output_path), "timestamp": timestamp},
        )

        notification = {
            "type": "mrp_complete",
            "workspaceId": workspace_id,
            "sessionId": session.session_id,
            "output": str(output_path),
            "timestamp": timestamp,
        }
        await self._broadcast(workspace_id, notification)
        await self._publish(workspace_id, notification)

        return MRPRunResponse(
            workspaceId=workspace_id,
            sessionId=session.session_id,
            outputPath=str(output_path),
            timestamp=timestamp,
        )

    # ---------------------------------------------------------------- WebSocket

    async def handle_websocket(self, websocket: WebSocket) -> None:
        """Accept and handle a WebSocket connection."""
        await websocket.accept()

        workspace_id = websocket.query_params.get("workspaceId")
        user_id = websocket.query_params.get("userId")
        session_id = websocket.query_params.get("sessionId")

        if not workspace_id or not user_id:
            await websocket.close(code=1008, reason="Missing workspaceId or userId")
            return

        session = self._ensure_session(workspace_id, session_id)
        connection = ClientConnection(
            websocket=websocket,
            workspace_id=workspace_id,
            user_id=user_id,
            session_id=session.session_id,
        )
        self._clients[connection.client_id] = connection
        self._participants[(workspace_id, session.session_id)].add(user_id)

        await self._update_presence(workspace_id, user_id)
        await self._record_event(workspace_id, session.session_id, user_id, "join", {})

        join_payload = {
            "type": "presence",
            "action": "join",
            "workspaceId": workspace_id,
            "sessionId": session.session_id,
            "userId": user_id,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await self._broadcast(workspace_id, join_payload, exclude=connection.client_id)
        await self._publish(workspace_id, join_payload)

        try:
            while True:
                message = await websocket.receive_text()
                await self._handle_message(connection, message)
        except WebSocketDisconnect:
            pass
        finally:
            await self._handle_disconnect(connection)

    async def _handle_message(self, connection: ClientConnection, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            await connection.websocket.send_json(
                {"type": "error", "message": "Invalid JSON payload"}
            )
            return

        message_type = payload.get("type")
        if message_type == "ping":
            connection.last_seen = datetime.now(UTC)
            await self._update_presence(connection.workspace_id, connection.user_id)
            await connection.websocket.send_json(
                {"type": "pong", "timestamp": datetime.now(UTC).isoformat()}
            )
            return

        if message_type == "dictation":
            text = payload.get("text")
            user_id = payload.get("userId", connection.user_id)
            session_id = payload.get("sessionId", connection.session_id)
            tags = payload.get("tags") or {}
            metadata = payload.get("metadata") or {}

            if not isinstance(text, str) or not text.strip():
                await connection.websocket.send_json(
                    {"type": "error", "message": "Dictation text must be non-empty"}
                )
                return

            session = self._ensure_session(connection.workspace_id, session_id)
            turn = session.record_turn(user_id, text, tags=tags, metadata=metadata)

            await self._record_event(
                connection.workspace_id,
                session.session_id,
                user_id,
                "dictation",
                {"text": text, "tags": tags, "metadata": metadata, "timestamp": turn.timestamp},
            )

            broadcast_payload = {
                "type": "dictation",
                "workspaceId": connection.workspace_id,
                "sessionId": session.session_id,
                "userId": user_id,
                "text": text,
                "timestamp": turn.timestamp,
                "tags": tags,
                "metadata": metadata,
            }
            await self._broadcast(
                connection.workspace_id, broadcast_payload, exclude=connection.client_id
            )
            await self._publish(connection.workspace_id, broadcast_payload)
            return

        if message_type == "agent_result":
            agent = payload.get("agent")
            result = payload.get("result")
            session = self._ensure_session(connection.workspace_id, payload.get("sessionId"))
            await self._record_event(
                connection.workspace_id,
                session.session_id,
                connection.user_id,
                "agent_result",
                {"agent": agent, "result": result},
            )
            notification = {
                "type": "agent_result",
                "workspaceId": connection.workspace_id,
                "sessionId": session.session_id,
                "agent": agent,
                "result": result,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            await self._broadcast(connection.workspace_id, notification, exclude=connection.client_id)
            await self._publish(connection.workspace_id, notification)
            return

        await connection.websocket.send_json(
            {"type": "error", "message": f"Unknown message type: {message_type!r}"}
        )

    async def _handle_disconnect(self, connection: ClientConnection) -> None:
        self._clients.pop(connection.client_id, None)
        self._participants[(connection.workspace_id, connection.session_id)].discard(
            connection.user_id
        )

        await self._record_event(
            connection.workspace_id,
            connection.session_id,
            connection.user_id,
            "leave",
            {},
        )

        leave_payload = {
            "type": "presence",
            "action": "leave",
            "workspaceId": connection.workspace_id,
            "sessionId": connection.session_id,
            "userId": connection.user_id,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await self._broadcast(connection.workspace_id, leave_payload)
        await self._publish(connection.workspace_id, leave_payload)

    # ------------------------------------------------------------ persistence

    async def _prepare_database(self) -> None:
        assert self._pg_pool is not None
        async with self._pg_pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS collab_events (
                    id SERIAL PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    user_id TEXT,
                    event_type TEXT NOT NULL,
                    payload JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS presence (
                    workspace_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    last_seen TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (workspace_id, user_id)
                )
                """
            )

    async def _record_event(
        self,
        workspace_id: str,
        session_id: str,
        user_id: Optional[str],
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        entry = {
            "workspace_id": workspace_id,
            "session_id": session_id,
            "user_id": user_id,
            "event_type": event_type,
            "payload": payload,
            "created_at": datetime.now(UTC).isoformat(),
        }

        if self._pg_pool:
            async with self._pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO collab_events (workspace_id, session_id, user_id, event_type, payload)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    workspace_id,
                    session_id,
                    user_id,
                    event_type,
                    json.dumps(payload),
                )
        else:
            self._memory_events.append(entry)

        self._append_workspace_event(workspace_id, entry)

    async def _update_presence(self, workspace_id: str, user_id: str) -> None:
        timestamp = datetime.now(UTC)
        if self._pg_pool:
            async with self._pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO presence (workspace_id, user_id, last_seen)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (workspace_id, user_id)
                    DO UPDATE SET last_seen = NOW()
                    """,
                    workspace_id,
                    user_id,
                )
        else:
            self._memory_presence[(workspace_id, user_id)] = timestamp

    # -------------------------------------------------------------- helpers

    def _ensure_session(self, workspace_id: str, session_id: Optional[str]) -> DictationSession:
        if not session_id:
            session_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        key = (workspace_id, session_id)
        if key not in self._sessions:
            session = start_session(
                workspace_id,
                manager=self._manager,
                session_id=session_id,
                participants=("user", "agent"),
                description="Collaboration session",
            )
            self._sessions[key] = session
        return self._sessions[key]

    async def _broadcast(
        self,
        workspace_id: str,
        payload: Dict[str, Any],
        *,
        exclude: Optional[str] = None,
    ) -> None:
        message = json.dumps(payload, ensure_ascii=False)
        for client_id, client in list(self._clients.items()):
            if client.workspace_id != workspace_id:
                continue
            if exclude and client_id == exclude:
                continue
            try:
                await client.websocket.send_text(message)
            except RuntimeError:  # pragma: no cover - defensive
                logger.debug("Failed to deliver message to %s", client_id)

    async def _publish(self, workspace_id: str, payload: Dict[str, Any]) -> None:
        if not self._redis_pub:
            return
        try:
            await self._redis_pub.publish(f"collab:{workspace_id}", json.dumps(payload))
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Redis publish failed: %s", exc)

    def _append_workspace_event(self, workspace_id: str, payload: Dict[str, Any]) -> None:
        record = self._manager.get(workspace_id)
        events_path = record.path / "collab" / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    async def _redis_listener(self) -> None:
        if not self._redis_sub:
            return
        pubsub = self._redis_sub.pubsub()
        await pubsub.psubscribe("collab:*")
        try:
            async for message in pubsub.listen():
                if message["type"] != "pmessage":
                    continue
                channel = message.get("channel")
                workspace_id = str(channel).split(":", 1)[1] if channel else ""
                data = message.get("data")
                if isinstance(data, str):
                    try:
                        payload = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    await self._broadcast(workspace_id, payload)
        except asyncio.CancelledError:  # pragma: no cover - expected on shutdown
            pass
        finally:
            await pubsub.close()

    async def _heartbeat_sweeper(self) -> None:
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(self._config.sweep_interval_seconds)
                cutoff = datetime.now(UTC) - timedelta(seconds=self._config.idle_timeout_seconds)
                for client_id, client in list(self._clients.items()):
                    if client.last_seen < cutoff:
                        logger.debug("Closing idle client %s", client_id)
                        with contextlib.suppress(Exception):
                            await client.websocket.close(code=1000, reason="Heartbeat timeout")
                        await self._handle_disconnect(client)
        except asyncio.CancelledError:  # pragma: no cover - expected on shutdown
            pass

    def _execute_mrp_pipeline(
        self,
        session: DictationSession,
        *,
        run_schema: bool,
        run_validation: bool,
    ) -> Path:
        pipeline = MRPPipeline(session)
        return pipeline.run(run_schema=run_schema, run_kira_validation=run_validation)


def create_app(
    *,
    manager: WorkspaceManager | None = None,
    config: CollaborationConfig | None = None,
) -> FastAPI:
    """Create a FastAPI application hosting the collaboration server."""

    server = CollaborationServer(manager=manager, config=config)
    app = FastAPI(title="Living Library Collaboration Server", version="0.2.0")

    @app.on_event("startup")
    async def _startup() -> None:
        await server.startup()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await server.shutdown()

    @app.get("/health/live")
    async def health() -> Dict[str, Any]:
        return await server.health()

    @app.get("/api/presence/{workspace_id}")
    async def presence(workspace_id: str) -> Dict[str, Any]:
        return await server.get_presence(workspace_id)

    @app.post("/api/workspaces/{workspace_id}/mrp", response_model=MRPRunResponse)
    async def run_mrp(workspace_id: str, body: MRPRunRequest) -> MRPRunResponse:
        return await server.run_mrp(workspace_id, body)

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await server.handle_websocket(websocket)

    app.state.collaboration_server = server
    return app


app = create_app()
