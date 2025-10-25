"""Shared JSON-backed state store for Echo agents."""

from __future__ import annotations

import json
import os
import threading
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional


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
        self._state: Dict[str, Dict[str, Any]] = {}
        self._on_create = on_create
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                self._state = json.loads(self.path.read_text(encoding="utf-8"))

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
        base = f"{section}_{len(bucket) + 1:04d}"
        if base not in bucket:
            return base
        return f"{section}_{uuid.uuid4().hex[:8]}"
