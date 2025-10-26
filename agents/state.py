"""Shared JSON-backed state store for Echo agents (monorepo wrapper)."""

from __future__ import annotations

import json
import os
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

STATE_FILE = Path("artifacts/state.json")

LEDGER_SECTIONS: Dict[str, str] = {
    "glyphs": "glyph",
    "glyph_analysis": "analysis",
    "mrp_embeds": "embed",
    "mrp_extracts": "extract",
    "lsb_covers": "lsb_cover",
    "lsb_embeds": "lsb_embed",
    "lsb_extracts": "lsb_extract",
}


def _default_state() -> Dict[str, Dict[str, Any]]:
    return {section: {} for section in LEDGER_SECTIONS}


class JsonStateStore:
    """Minimal thread-safe JSON ledger with optional on-disk persistence."""

    def __init__(
        self,
        path: Optional[str | Path] = None,
        auto_flush: bool = True,
        on_create: Optional[Callable[[str, str, Dict[str, Any]], Optional[str]]] = None,
    ) -> None:
        self.path = Path(path) if path else None
        self.auto_flush = auto_flush
        self._lock = threading.RLock()
        self._state: Dict[str, Dict[str, Any]] = _default_state()
        self._on_create = on_create
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                try:
                    data = json.loads(self.path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    data = {}
                if isinstance(data, dict):
                    for section, entries in data.items():
                        if isinstance(entries, dict):
                            self._state[section] = entries
        self._ensure_sections()

    # ------------------------------------------------------------------ #
    # Basic CRUD helpers                                                 #
    # ------------------------------------------------------------------ #

    def create_record(self, section: str, payload: Dict[str, Any], record_id: Optional[str] = None) -> str:
        """Insert payload into section, returning the assigned record id."""

        with self._lock:
            bucket = self._state.setdefault(section, {})
            if record_id is None:
                record_id = self._generate_id(section, bucket)
            entry = deepcopy(payload)
            bucket[record_id] = entry

            if self._on_create:
                cloned = deepcopy(entry)
                block_hash = self._on_create(section, record_id, cloned)
                if block_hash:
                    entry.setdefault("block_hash", block_hash)

            if self.auto_flush:
                self._write_locked()
            return record_id

    def update_record(self, section: str, record_id: str, payload: Dict[str, Any]) -> None:
        with self._lock:
            bucket = self._state.setdefault(section, {})
            bucket[record_id] = payload
            if self.auto_flush:
                self._write_locked()

    def patch_record(self, section: str, record_id: str, updates: Dict[str, Any]) -> None:
        with self._lock:
            bucket = self._state.setdefault(section, {})
            current = bucket.get(record_id, {})
            current.update(updates)
            bucket[record_id] = current
            if self.auto_flush:
                self._write_locked()

    def get_record(self, section: str, record_id: str) -> Dict[str, Any]:
        with self._lock:
            bucket = self._state.get(section, {})
            if record_id not in bucket:
                raise KeyError(f"{section}:{record_id} not found")
            return deepcopy(bucket[record_id])

    def list_section(self, section: str) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return deepcopy(self._state.get(section, {}))

    def sections(self) -> Iterable[str]:
        with self._lock:
            return tuple(self._state.keys())

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return deepcopy(self._state)

    # ------------------------------------------------------------------ #
    # Persistence                                                        #
    # ------------------------------------------------------------------ #

    def flush(self) -> None:
        with self._lock:
            self._write_locked()

    def _write_locked(self) -> None:
        if not self.path:
            return
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    # ------------------------------------------------------------------ #
    # Utilities                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _generate_id(section: str, bucket: Dict[str, Any]) -> str:
        prefix = LEDGER_SECTIONS.get(section, section.rstrip("s") or section)
        candidate = f"{prefix}_{len(bucket) + 1}"
        if candidate not in bucket:
            return candidate
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def _ensure_sections(self) -> None:
        for section in LEDGER_SECTIONS:
            self._state.setdefault(section, {})


_CREATE_LISTENERS: list[Callable[[str, str, Dict[str, Any]], Optional[str]]] = []


def register_create_listener(listener: Callable[[str, str, Dict[str, Any]], Optional[str]]) -> None:
    """Register a callback invoked whenever a new record is created."""

    _CREATE_LISTENERS.append(listener)


def _dispatch_create(section: str, record_id: str, payload: Dict[str, Any]) -> Optional[str]:
    block_hash: Optional[str] = None
    for listener in _CREATE_LISTENERS:
        result = listener(section, record_id, deepcopy(payload))
        if result:
            block_hash = result
    return block_hash


_STORE = JsonStateStore(path=STATE_FILE, auto_flush=True, on_create=_dispatch_create)


def store() -> JsonStateStore:
    """Return the process-wide JSON state store."""

    return _STORE


def _utc_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def add_entry(section: str, payload: Dict[str, Any], record_id: Optional[str] = None) -> str:
    """Generic helper to insert an entry into a ledger section."""

    if "created" not in payload:
        payload = {**payload, "created": _utc_timestamp()}
    return _STORE.create_record(section, payload, record_id=record_id)


def log_glyph(token: str, size: int, file_path: str, **extras: Any) -> str:
    payload = {"token": token, "size": size, "file": file_path, **extras}
    return add_entry("glyphs", payload)


def log_glyph_analysis(source: str, mse: float, fft_mean: float, **extras: Any) -> str:
    payload = {"source": source, "mse": mse, "fft_mean": fft_mean, **extras}
    return add_entry("glyph_analysis", payload)


def log_mrp_embed(
    cover: str,
    output: str,
    payload_hash: str,
    *,
    channel: Optional[str] = None,
    **extras: Any,
) -> str:
    record = {
        "cover": cover,
        "output": output,
        "payload_hash": payload_hash,
        **extras,
    }
    if channel:
        record["channel"] = channel
    return add_entry("mrp_embeds", record)


def log_mrp_extract(path: str, payload_hash: str, *, channel: Optional[str] = None, **extras: Any) -> str:
    record = {"source": path, "payload_hash": payload_hash, **extras}
    if channel:
        record["channel"] = channel
    return add_entry("mrp_extracts", record)


def log_lsb_cover(path: str, *, checksum: Optional[str] = None, **extras: Any) -> str:
    record = {"path": path, **extras}
    if checksum:
        record["checksum"] = checksum
    return add_entry("lsb_covers", record)


def log_lsb_embed(path: str, *, payload_hash: Optional[str] = None, **extras: Any) -> str:
    record = {"path": path, **extras}
    if payload_hash:
        record["payload_hash"] = payload_hash
    return add_entry("lsb_embeds", record)


def log_lsb_extract(path: str, payload_hash: str, *, channel: Optional[str] = None, **extras: Any) -> str:
    record = {"path": path, "payload_hash": payload_hash, **extras}
    if channel:
        record["channel"] = channel
    return add_entry("lsb_extracts", record)
