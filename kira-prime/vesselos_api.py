"""VesselOS Kira Prime - Production API Server."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline.dispatcher_enhanced import DispatcherConfig, EnhancedMRPDispatcher, PipelineContext
from pipeline.intent_parser import IntentParser
from library_core.workspace import Workspace

app = FastAPI(
    title="VesselOS Kira Prime API",
    version="2.1.0",
    description="Multi-Role Persona ritual interaction system",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production deployments.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InteractionRequest(BaseModel):
    text: str
    user_id: str
    workspace_id: str = "default"
    metadata: Optional[Dict[str, Any]] = None


class InteractionResponse(BaseModel):
    success: bool
    timestamp: str
    ritual: Dict[str, Any]
    echo: Dict[str, Any]
    memory: Dict[str, Any]
    validation: Dict[str, Any]
    execution_time_ms: float


dispatchers: Dict[str, EnhancedMRPDispatcher] = {}
dispatch_lock = asyncio.Lock()


async def get_dispatcher(workspace_id: str) -> EnhancedMRPDispatcher:
    async with dispatch_lock:
        if workspace_id not in dispatchers:
            config = DispatcherConfig(
                agent_order=["garden", "echo", "limnus", "kira"],
                retry_enabled=True,
                circuit_breaker_enabled=True,
                cache_enabled=True,
                verbose_logging=False,
            )
            dispatchers[workspace_id] = EnhancedMRPDispatcher(workspace_id, config)
        return dispatchers[workspace_id]


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "service": "VesselOS Kira Prime",
        "version": "2.1.0",
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "api": "ok",
            "dispatcher": "ok",
            "storage": "ok",
        },
    }


@app.post("/interact", response_model=InteractionResponse)
async def interact(request: InteractionRequest) -> InteractionResponse:
    try:
        dispatcher = await get_dispatcher(request.workspace_id)
        intent = IntentParser().parse(request.text)
        context = PipelineContext(
            input_text=request.text,
            user_id=request.user_id,
            workspace_id=request.workspace_id,
            intent=intent,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=request.metadata or {},
        )
        result = await dispatcher.dispatch(context)
        return InteractionResponse(
            success=result["success"],
            timestamp=result["timestamp"],
            ritual=result["agents"]["garden"],
            echo=result["agents"]["echo"],
            memory=result["agents"]["limnus"],
            validation=result["agents"]["kira"],
            execution_time_ms=result["execution_time_ms"],
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/workspace/{workspace_id}/state")
async def get_workspace_state(workspace_id: str) -> Dict[str, Any]:
    try:
        workspace = Workspace(workspace_id)
        garden_state = workspace.load_state("garden", default={})
        echo_state = workspace.load_state("echo", default={})
        limnus_state = workspace.load_state("limnus", default={})
        return {
            "workspace_id": workspace_id,
            "garden": {
                "stage": garden_state.get("ledger", {}).get("current_stage"),
                "cycle": garden_state.get("ledger", {}).get("cycle_count"),
                "entries": len(garden_state.get("ledger", {}).get("entries", [])),
                "consents": len(garden_state.get("ledger", {}).get("consents", [])),
            },
            "echo": {
                "quantum_state": echo_state.get("quantum_state"),
                "history_length": len(echo_state.get("history", [])),
            },
            "limnus": {
                "memory_stats": limnus_state.get("memory", {}).get("stats"),
                "blocks": len(limnus_state.get("ledger", {}).get("blocks", [])),
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/workspace/{workspace_id}/ledger")
async def get_ledger(workspace_id: str, ledger_type: str = "limnus") -> Dict[str, Any]:
    try:
        workspace = Workspace(workspace_id)
        if ledger_type == "garden":
            state = workspace.load_state("garden", default={})
            ledger = state.get("ledger", {})
            return {
                "type": "garden",
                "entries": ledger.get("entries", [])[-10:],
                "stage": ledger.get("current_stage"),
                "cycle": ledger.get("cycle_count"),
            }
        state = workspace.load_state("limnus", default={})
        ledger = state.get("ledger", {})
        blocks = ledger.get("blocks", [])
        return {
            "type": "limnus",
            "blocks": blocks[-10:],
            "total_blocks": len(blocks),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/workspace/{workspace_id}/memory")
async def get_memory(workspace_id: str, layer: Optional[str] = None) -> Dict[str, Any]:
    try:
        workspace = Workspace(workspace_id)
        limnus_state = workspace.load_state("limnus", default={})
        memory = limnus_state.get("memory", {})
        entries = memory.get("entries", [])
        if layer:
            entries = [entry for entry in entries if entry.get("layer") == layer]
        return {
            "workspace_id": workspace_id,
            "entries": entries[-20:],
            "stats": memory.get("stats"),
            "filtered_by": layer,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/workspace/{workspace_id}/quantum")
async def get_quantum_state(workspace_id: str) -> Dict[str, Any]:
    try:
        workspace = Workspace(workspace_id)
        echo_state = workspace.load_state("echo", default={})
        quantum_state = echo_state.get("quantum_state", {})
        history = echo_state.get("history", [])
        dominant = "unknown"
        glyph = "?"
        if quantum_state:
            alpha = quantum_state.get("alpha", 0.0)
            beta = quantum_state.get("beta", 0.0)
            gamma = quantum_state.get("gamma", 0.0)
            if alpha >= beta and alpha >= gamma:
                dominant, glyph = "squirrel", "🐿️"
            elif beta > alpha and beta >= gamma:
                dominant, glyph = "fox", "🦊"
            else:
                dominant, glyph = "paradox", "∿"
        return {
            "workspace_id": workspace_id,
            "quantum_state": quantum_state,
            "dominant_persona": dominant,
            "glyph": glyph,
            "history": history[-10:],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/workspace/{workspace_id}/validate")
async def validate_workspace(workspace_id: str) -> Dict[str, Any]:
    try:
        dispatcher = await get_dispatcher(workspace_id)
        intent = IntentParser().parse("validate system")
        context = PipelineContext(
            input_text="validate system",
            user_id="system",
            workspace_id=workspace_id,
            intent=intent,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        result = await dispatcher.dispatch(context)
        return result["agents"]["kira"]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for workspace_id, dispatcher in dispatchers.items():
        summary[workspace_id] = await dispatcher.get_metrics()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workspaces": summary,
    }


@app.on_event("startup")
async def startup_event() -> None:
    print("🚀 VesselOS Kira Prime API starting...")
    print("   Version: 2.1.0")
    print("   Agents: Garden → Echo → Limnus → Kira")
    print("   Status: Operational")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    print("👋 VesselOS Kira Prime API shutting down...")


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("vesselos_api:app", host="0.0.0.0", port=8000, reload=False)
