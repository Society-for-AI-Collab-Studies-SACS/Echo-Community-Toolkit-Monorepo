#!/usr/bin/env python3
"""
Limnus Ledger Agent — cryptographic consciousness recorder.

Receives SIGPRINT updates and journal entries, writes an append-only ledger,
chains entries by hash, optionally signs them, and emits Merkle checkpoints for
verification. Exposes the LedgerService (CommitEntry) defined in protos/agents.proto.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import grpc
import numpy as np
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from protos import agents_pb2, agents_pb2_grpc

FFT_BANDS = ["delta", "theta", "alpha", "beta", "gamma"]

# --------------------------------------------------------------------------- #
# Merkle tree utilities
# --------------------------------------------------------------------------- #


class MerkleNode:
    def __init__(self, left: "MerkleNode | None" = None, right: "MerkleNode | None" = None, data: str | None = None):
        if data is not None:
            self.hash = hashlib.sha256(data.encode("utf-8")).hexdigest()
        else:
            combined = (left.hash + right.hash).encode("utf-8")
            self.hash = hashlib.sha256(combined).hexdigest()
        self.left = left
        self.right = right
        self.data = data


class MerkleTree:
    def __init__(self, leaves: List[str]):
        self.leaves = [MerkleNode(data=leaf) for leaf in leaves]
        self.root = self._build(self.leaves)

    def _build(self, nodes: List[MerkleNode]) -> Optional[MerkleNode]:
        if not nodes:
            return None
        if len(nodes) == 1:
            return nodes[0]
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        next_level: List[MerkleNode] = []
        for idx in range(0, len(nodes), 2):
            next_level.append(MerkleNode(left=nodes[idx], right=nodes[idx + 1]))
        return self._build(next_level)

    def root_hash(self) -> str:
        return self.root.hash if self.root else ""


# --------------------------------------------------------------------------- #
# Persistent storage
# --------------------------------------------------------------------------- #


class LedgerDatabase:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_entries (
                entry_id TEXT PRIMARY KEY,
                sigprint_code TEXT,
                coherence REAL,
                entropy REAL,
                previous_hash TEXT,
                entry_type TEXT,
                text_payload TEXT,
                timestamp TEXT,
                signature BLOB,
                metadata TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS merkle_checkpoints (
                checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_hash TEXT,
                entry_count INTEGER,
                timestamp TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_associations (
                association_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT,
                transcript TEXT,
                audio_hash TEXT,
                timestamp TEXT,
                FOREIGN KEY(entry_id) REFERENCES ledger_entries(entry_id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_data TEXT,
                frequency INTEGER,
                first_seen TEXT,
                last_seen TEXT
            )
            """
        )
        self.conn.commit()

    def add_entry(self, entry: Dict[str, Any]) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO ledger_entries
            (entry_id, sigprint_code, coherence, entropy, previous_hash, entry_type,
             text_payload, timestamp, signature, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry["entry_id"],
                entry["sigprint_code"],
                entry["coherence"],
                entry["entropy"],
                entry["previous_hash"],
                entry.get("entry_type", ""),
                entry.get("text_payload", ""),
                entry["timestamp"],
                entry.get("signature", b""),
                json.dumps(entry.get("metadata", {})),
            ),
        )
        self.conn.commit()

    def latest_entry(self) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT entry_id, timestamp FROM ledger_entries ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return {"entry_id": row["entry_id"], "timestamp": row["timestamp"]}

    def fetch_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute("SELECT * FROM ledger_entries WHERE entry_id = ?", (entry_id,)).fetchone()
        if not row:
            return None
        return {
            "entry_id": row["entry_id"],
            "sigprint_code": row["sigprint_code"],
            "coherence": row["coherence"],
            "entropy": row["entropy"],
            "previous_hash": row["previous_hash"],
            "entry_type": row["entry_type"],
            "text_payload": row["text_payload"],
            "timestamp": row["timestamp"],
            "signature": row["signature"],
            "metadata": json.loads(row["metadata"]),
        }

    def recent_entries(self, limit: int = 10) -> List[str]:
        rows = self.conn.execute(
            "SELECT entry_id FROM ledger_entries ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [row["entry_id"] for row in rows]

    def add_merkle_checkpoint(self, root_hash: str, entry_count: int) -> None:
        self.conn.execute(
            "INSERT INTO merkle_checkpoints (root_hash, entry_count, timestamp) VALUES (?, ?, ?)",
            (root_hash, entry_count, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


# --------------------------------------------------------------------------- #
# Configuration and agent implementation
# --------------------------------------------------------------------------- #


@dataclass
class LedgerConfig:
    ledger_path: str = "limnus_ledger.db"
    checkpoint_interval: int = 100
    enable_encryption: bool = True
    signing_key_path: str = "limnus_key.pem"
    grpc_port: int = 50051

    @classmethod
    def from_file(cls, path: str) -> "LedgerConfig":
        data: Dict[str, Any] = {}
        if path and path.endswith(".yaml"):
            try:
                import yaml

                with open(path, "r", encoding="utf-8") as fh:
                    parsed = yaml.safe_load(fh) or {}
                    if isinstance(parsed, dict):
                        data = parsed
            except Exception:
                pass
        return cls(**data)


class LimnusLedgerAgent(agents_pb2_grpc.LedgerServiceServicer):
    def __init__(self, config: LedgerConfig):
        self.config = config
        self.logger = logging.getLogger("limnus_ledger")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(handler)

        self.db = LedgerDatabase(self.config.ledger_path)
        self.private_key = None
        self.public_key = None
        if self.config.enable_encryption:
            self._load_or_generate_keys()

        self.entry_count = 0
        self.current_merkle_root = ""
        self.pattern_cache: Dict[str, Dict[str, Any]] = {}
        self.grpc_server: Optional[grpc.aio.Server] = None

    # ------------------------------------------------------------------ #
    # Crypto helpers
    # ------------------------------------------------------------------ #
    def _load_or_generate_keys(self) -> None:
        key_path = Path(self.config.signing_key_path)
        if key_path.exists():
            with open(key_path, "rb") as fh:
                self.private_key = serialization.load_pem_private_key(
                    fh.read(), password=None, backend=default_backend()
                )
        else:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )
            pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
            with open(key_path, "wb") as fh:
                fh.write(pem)
            self.logger.info("Generated signing key at %s", key_path)
        self.public_key = self.private_key.public_key() if self.private_key else None

    # ------------------------------------------------------------------ #
    # Core storage
    # ------------------------------------------------------------------ #
    def _store_entry(self, request: agents_pb2.LedgerEntry) -> Dict[str, Any]:
        timestamp = request.time or datetime.utcnow().isoformat()
        features = dict(request.features)

        sigprint_data = {
            "sigprint": request.sigprint,
            "coherence": request.coherence,
            "entropy": features.get("entropy", 0.0),
            "features": features,
        }

        previous = self.db.latest_entry()
        previous_hash = previous["entry_id"] if previous else "genesis"

        entry_payload = {
            "sigprint_code": request.sigprint,
            "coherence": request.coherence,
            "entropy": sigprint_data["entropy"],
            "previous_hash": previous_hash,
            "entry_type": request.type,
            "text_payload": request.text,
            "timestamp": timestamp,
            "metadata": {
                "features": features,
                "type": request.type,
            },
        }

        entry_json = json.dumps(entry_payload, sort_keys=True)
        entry_id = hashlib.sha256(entry_json.encode("utf-8")).hexdigest()
        entry_payload["entry_id"] = entry_id

        if self.private_key:
            signature = self.private_key.sign(
                entry_json.encode("utf-8"),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
            entry_payload["signature"] = signature

        self.db.add_entry(entry_payload)
        self.entry_count += 1

        self._update_patterns(sigprint_data)

        if self.entry_count % self.config.checkpoint_interval == 0:
            self._create_merkle_checkpoint()

        self.logger.info(
            "Ledger entry stored type=%s sigprint=%s… coherence=%.2f",
            request.type or "SIGPRINT",
            request.sigprint[:8],
            request.coherence,
        )
        return entry_payload

    def _create_merkle_checkpoint(self) -> None:
        recent_ids = self.db.recent_entries(self.config.checkpoint_interval)
        if not recent_ids:
            return
        tree = MerkleTree(recent_ids)
        root_hash = tree.root_hash()
        self.db.add_merkle_checkpoint(root_hash, len(recent_ids))
        self.current_merkle_root = root_hash
        self.logger.info("Merkle checkpoint created root=%s…", root_hash[:8])

    # ------------------------------------------------------------------ #
    # Pattern tracking
    # ------------------------------------------------------------------ #
    def _update_patterns(self, data: Dict[str, Any]) -> None:
        key = data["sigprint"][:8]
        if key in self.pattern_cache:
            entry = self.pattern_cache[key]
            entry["count"] += 1
            entry["last_seen"] = datetime.utcnow()
        else:
            self.pattern_cache[key] = {
                "count": 1,
                "first_seen": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "data": data,
            }

    # ------------------------------------------------------------------ #
    # Verification helpers
    # ------------------------------------------------------------------ #
    def verify_entry(self, entry_id: str) -> bool:
        entry = self.db.fetch_entry(entry_id)
        if not entry:
            return False

        payload = entry.copy()
        signature = payload.pop("signature", None)
        payload_json = json.dumps(
            {
                k: v
                for k, v in payload.items()
                if k not in {"metadata"} or isinstance(v, (str, float, int, list, dict))
            },
            sort_keys=True,
        )
        if signature and self.public_key:
            try:
                self.public_key.verify(
                    signature,
                    payload_json.encode("utf-8"),
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256(),
                )
            except InvalidSignature:
                return False
        prev_hash = entry.get("previous_hash")
        if prev_hash and prev_hash != "genesis":
            return self.db.fetch_entry(prev_hash) is not None
        return True

    # ------------------------------------------------------------------ #
    # gRPC service implementation
    # ------------------------------------------------------------------ #
    async def CommitEntry(
        self, request: agents_pb2.LedgerEntry, context: grpc.aio.ServicerContext
    ) -> agents_pb2.Ack:  # noqa: N802
        try:
            self._store_entry(request)
            return agents_pb2.Ack(success=True)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("CommitEntry failure: %s", exc)
            return agents_pb2.Ack(success=False)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def serve(self) -> None:
        self.grpc_server = grpc.aio.server()
        agents_pb2_grpc.add_LedgerServiceServicer_to_server(self, self.grpc_server)
        address = f"[::]:{self.config.grpc_port}"
        self.grpc_server.add_insecure_port(address)
        await self.grpc_server.start()
        self.logger.info("Limnus Ledger listening on %s", address)
        try:
            await self.grpc_server.wait_for_termination()
        finally:
            if self.grpc_server:
                await self.grpc_server.stop(grace=5)
            self.db.close()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Limnus Ledger Agent")
    parser.add_argument("--config", default=None, help="Path to YAML config")
    parser.add_argument("--ledger-path", help="Override ledger DB path")
    parser.add_argument("--grpc-port", type=int, help="Override gRPC port")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> LedgerConfig:
    cfg = LedgerConfig.from_file(args.config) if args.config else LedgerConfig()
    overrides: Dict[str, Any] = {}
    if args.ledger_path:
        overrides["ledger_path"] = args.ledger_path
    if args.grpc_port:
        overrides["grpc_port"] = args.grpc_port
    if overrides:
        cfg = LedgerConfig(**{**cfg.__dict__, **overrides})
    return cfg


def main() -> None:
    args = parse_args()
    config = build_config(args)
    agent = LimnusLedgerAgent(config)
    asyncio.run(agent.serve())


if __name__ == "__main__":
    main()

