"""
Echo Network Node — API Gateway for LSB/MRP/G2V operations
Uses FastAPI for async endpoints, exposing encode/decode as services.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import math
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np
from fastapi import Body, FastAPI, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.mrp.codec import decode, encode_with_mode
from .glyph_batch import GlyphBatchProcessor

app = FastAPI(title="Echo Network Node", version="2.0")

# In-memory stores (swap with Redis/DB in production)
ECHO_MANIFEST: Dict[str, Any] = {}
GLYPH_REGISTRY: List[Dict[str, Any]] = []
PEER_DISTRIBUTIONS: Dict[str, Any] = {}
_manifest_lock = asyncio.Lock()
_registry_lock = asyncio.Lock()


DEFAULT_TOKENS = ["I-Glyph", "Octave Cycle Drive", "MirrorPulse"]


class EncodeRequest(BaseModel):
    message: str
    mode: str = "phaseA"
    metadata: Dict[str, Any] = {}


class BatchDistributeRequest(BaseModel):
    tokens: List[str]
    peers: List[str] = []
    size: int = 64
    projection: bool = True
    theta: float = 30.0


class BatchRegisterRequest(BaseModel):
    tokens: List[str]
    signature: Optional[str] = None
    size: int = 64
    projection: bool = True
    theta: float = 30.0


def _ensure_artifacts_dir() -> Path:
    path = Path("artifacts")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _prepare_batch(
    tokens: Iterable[str],
    size: int,
    projection: bool,
    theta: float,
) -> tuple[List[dict], Sequence[np.ndarray], str]:
    """
    Generate glyph batch artefacts: manifest entries, raw arrays, and grid PNG (base64).
    """
    processor = GlyphBatchProcessor(size=size, projection=projection, theta_deg=theta)
    if not processor.process_tokens(tokens):
        raise HTTPException(status_code=400, detail="unable to generate glyph batch")
    processor.apply_batch_normalization()
    arrays = processor.generate_array_layout(as_base64=False)
    if not arrays:
        raise HTTPException(status_code=400, detail="no glyph data produced")
    processor.compute_fft_metadata()
    manifest = processor.create_manifest()

    grid_image = processor.generate_grid_layout(include_labels=True)
    if grid_image is None:
        raise HTTPException(status_code=400, detail="failed to compose grid layout")
    buf = io.BytesIO()
    grid_image.save(buf, format="PNG")
    b64_grid = base64.b64encode(buf.getvalue()).decode("ascii")
    return manifest, arrays, b64_grid


def _compute_similarity_metrics(arrays: Sequence[np.ndarray]) -> List[Dict[str, float]]:
    """
    Compute MSE/PSNR between successive glyph arrays.
    """
    metrics: List[Dict[str, float]] = []
    if len(arrays) < 2:
        return metrics
    for a, b in zip(arrays, arrays[1:]):
        a = np.asarray(a, float)
        b = np.asarray(b, float)
        mse = float(np.mean((a - b) ** 2))
        psnr = float("inf") if mse == 0 else 10.0 * math.log10(1.0 / mse)
        metrics.append({"mse": mse, "psnr": psnr})
    return metrics


def _hash_manifest(manifest: Iterable[Dict[str, Any]]) -> str:
    """
    Derive a reproducible signature from manifest entries.
    """
    digest = sha256()
    for entry in manifest:
        digest.update(str(entry.get("token", "")).encode("utf-8"))
        digest.update(str(entry.get("fft_mean", "")).encode("utf-8"))
        digest.update(str(entry.get("base64", "")).encode("utf-8"))
    return digest.hexdigest()


@app.post("/encode")
async def encode_endpoint(req: EncodeRequest):
    cover = Path("assets/images/echo_key.png").resolve()
    if not cover.exists():
        raise HTTPException(status_code=404, detail="cover image not found")

    out_dir = _ensure_artifacts_dir()
    out_path = out_dir / f"{req.mode}_net.png"

    try:
        result = encode_with_mode(str(cover), str(out_path), req.message, dict(req.metadata), req.mode)
    except NotImplementedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    async with _manifest_lock:
        ECHO_MANIFEST[str(out_path)] = result

    return {"status": "ok", "file": str(out_path), "details": result}


@app.post("/decode")
async def decode_endpoint(file: UploadFile):
    uploads = Path("uploads")
    uploads.mkdir(parents=True, exist_ok=True)
    tmp = uploads / file.filename
    data = await file.read()
    await asyncio.to_thread(tmp.write_bytes, data)

    try:
        msg, meta, ecc = decode(str(tmp))
    finally:
        tmp.unlink(missing_ok=True)
    return {"message": msg, "metadata": meta, "ecc": ecc}


@app.get("/manifest")
async def get_manifest():
    async with _manifest_lock:
        return dict(ECHO_MANIFEST)


@app.get("/peers")
async def get_peer_distributions():
    async with _manifest_lock:
        return {peer: list(records) for peer, records in PEER_DISTRIBUTIONS.items()}


@app.get("/registry")
async def get_registry():
    async with _registry_lock:
        return list(GLYPH_REGISTRY)


# --- /glyph Endpoint for Remote Visualization -------------------------------


@app.get("/glyph")
def generate_glyph(
    token: str = Query("I-Glyph", description="Glyph keyword (Tink token or concept)"),
    size: int = Query(64, ge=16, le=512, description="Glyph resolution"),
    projection: bool = Query(True, description="Apply angular projection"),
    theta: float = Query(30.0, description="Projection angle in degrees"),
):
    """
    Generate a glyph from the Echo G2V system and return it as a base64-encoded PNG.

    Flow:
        1. glyph_from_tink_token(token) → 2D NumPy array
        2. Optionally build a 3D stack and project through an angle
        3. Perform FFT round-trip to emphasize spectral detail
        4. Convert to base64 PNG for remote rendering
    """

    manifest, _, _ = _prepare_batch([token], size, projection, theta)
    entry = manifest[0] if manifest else {}
    payload = {
        "token": token,
        "size": size,
        "projection": projection,
        "theta": theta,
        "fft_magnitude_mean": entry.get("fft_mean"),
        "image_base64": entry.get("base64"),
    }
    return JSONResponse(content=payload)


# --- /glyph/batch Endpoint ---------------------------------------------------


@app.post("/glyph/batch")
def generate_glyph_batch(
    tokens: List[str] = Body(default=DEFAULT_TOKENS.copy(), description="List of glyph tokens or concept names."),
    size: int = Query(64, ge=16, le=256, description="Individual glyph size"),
    layout: str = Query("grid", description="Layout: 'grid' or 'array'"),
    projection: bool = Query(True, description="Apply angular projection"),
    theta: float = Query(30.0, description="Projection angle for all glyphs"),
    compare: bool = Query(False, description="Compute MSE/PSNR between successive glyphs"),
):
    """
    Generate multiple glyphs from a list of tokens and return as:
    - layout='array': JSON array of individual base64 glyphs
    - layout='grid' : Base64 PNG grid collage (default)
    """

    if not tokens:
        raise HTTPException(status_code=400, detail="token list must not be empty")

    layout = layout.lower()
    if layout not in {"grid", "array"}:
        raise HTTPException(status_code=400, detail="layout must be 'grid' or 'array'")

    manifest, arrays, grid_b64 = _prepare_batch(tokens, size, projection, theta)
    metrics = _compute_similarity_metrics(arrays) if compare else []

    if layout == "array":
        return {"layout": "array", "count": len(manifest), "glyphs": manifest, "similarity": metrics}

    count = len(manifest)
    cols = max(1, math.ceil(math.sqrt(count)))
    rows = max(1, math.ceil(count / cols))

    return {
        "layout": "grid",
        "count": count,
        "cols": cols,
        "rows": rows,
        "image_base64": grid_b64,
        "glyphs": manifest,
        "similarity": metrics,
    }


# --- /glyph/batch/distribute -----------------------------------------------


@app.post("/glyph/batch/distribute")
async def distribute_glyph_batch(req: BatchDistributeRequest):
    manifest, arrays, grid_b64 = _prepare_batch(req.tokens, req.size, req.projection, req.theta)
    metrics = _compute_similarity_metrics(arrays)
    timestamp = datetime.utcnow().isoformat() + "Z"
    record = {
        "timestamp": timestamp,
        "tokens": req.tokens,
        "size": req.size,
        "projection": req.projection,
        "theta": req.theta,
        "glyphs": manifest,
        "grid_base64": grid_b64,
        "similarity": metrics,
    }

    peers = req.peers or ["broadcast"]
    async with _manifest_lock:
        for peer in peers:
            PEER_DISTRIBUTIONS.setdefault(peer, []).append(record)

    return {"status": "ok", "peers": peers, "count": len(manifest), "timestamp": timestamp}


# --- /glyph/batch/register --------------------------------------------------


@app.post("/glyph/batch/register")
async def register_glyph_batch(req: BatchRegisterRequest):
    manifest, arrays, grid_b64 = _prepare_batch(req.tokens, req.size, req.projection, req.theta)
    signature = req.signature or _hash_manifest(manifest)
    timestamp = datetime.utcnow().isoformat() + "Z"
    metrics = _compute_similarity_metrics(arrays)
    record = {
        "signature": signature,
        "timestamp": timestamp,
        "tokens": req.tokens,
        "size": req.size,
        "projection": req.projection,
        "theta": req.theta,
        "glyphs": manifest,
        "grid_base64": grid_b64,
        "similarity": metrics,
    }

    async with _registry_lock:
        GLYPH_REGISTRY.append(record)

    return {"status": "ok", "signature": signature, "count": len(manifest), "timestamp": timestamp}


# --- /glyph/batch/ws --------------------------------------------------------


@app.websocket("/glyph/batch/ws")
async def glyph_batch_websocket(ws: WebSocket):
    await ws.accept()
    tokens = DEFAULT_TOKENS
    size = 64
    projection = True
    theta = 30.0
    try:
        manifest, arrays, grid_b64 = _prepare_batch(tokens, size, projection, theta)
        metrics = _compute_similarity_metrics(arrays)
        await ws.send_json(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "tokens": tokens,
                "size": size,
                "projection": projection,
                "theta": theta,
                "glyphs": manifest,
                "grid_base64": grid_b64,
                "similarity": metrics,
            }
        )
    except HTTPException as exc:
        await ws.send_json({"error": exc.detail, "status": exc.status_code})
    try:
        while True:
            message = await ws.receive_text()
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                data = {}

            tokens = data.get("tokens") or tokens
            size = int(data.get("size", size))
            projection = bool(data.get("projection", projection))
            theta = float(data.get("theta", theta))

            try:
                manifest, arrays, grid_b64 = _prepare_batch(tokens, size, projection, theta)
                metrics = _compute_similarity_metrics(arrays)
                await ws.send_json(
                    {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "tokens": tokens,
                        "size": size,
                        "projection": projection,
                        "theta": theta,
                        "glyphs": manifest,
                        "grid_base64": grid_b64,
                        "similarity": metrics,
                    }
                )
            except HTTPException as exc:
                await ws.send_json({"error": exc.detail, "status": exc.status_code})
    except WebSocketDisconnect:
        return
