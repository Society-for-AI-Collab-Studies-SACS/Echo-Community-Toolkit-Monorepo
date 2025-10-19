#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import grpc

from protos import agents_pb2, agents_pb2_grpc

ECHO7_SIGNATURE = "48152709316470239518"


def _parse_time(ts: str) -> datetime:
    # Accept ISO strings with trailing Z or without
    if not ts:
        return datetime.now(timezone.utc)
    if ts.endswith("Z"):
        ts = ts[:-1]
        try:
            return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        # Fallback to now
        return datetime.now(timezone.utc)


class SharedSigprintState:
    def __init__(self):
        self._lock = threading.Lock()
        self.time = ""
        self.sigprint = ""
        self.coherence = 0.0
        self.features = {}

    def update(self, t, code, coh, feats):
        with self._lock:
            self.time = t
            self.sigprint = code
            self.coherence = float(coh)
            self.features = dict(feats)

    def snapshot(self):
        with self._lock:
            return (self.time, self.sigprint, self.coherence, dict(self.features))


class SigprintServicer(agents_pb2_grpc.SigprintServiceServicer):
    def __init__(self, shared: SharedSigprintState):
        self.shared = shared

    def GetLatestSigprint(self, request, context):
        t, code, coh, feats = self.shared.snapshot()
        return agents_pb2.SigprintUpdate(time=t, sigprint=code, coherence=coh, features=feats)


class LedgerServicer(agents_pb2_grpc.LedgerServiceServicer):
    def __init__(self, out_path: str, shared_sig: SharedSigprintState):
        self.out_path = out_path
        self._lock = threading.Lock()
        self.prev_hash = "GENESIS_00"
        self.index = 0
        self.last_seen = {}  # sigprint -> datetime
        self.shared_sig = shared_sig

        # Genesis FORCED_GATE (morning ritual reset placeholder)
        genesis = {
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "FORCED_GATE",
            "text": "Resetting to prevent lock-in. See you tomorrow, yesterday-me...",
            "sigprint": "0" * 20,
            "coherence": 0.0,
            "features": {},
        }
        self._write_entry(genesis, is_genesis=True)

    def _hash_entry(self, entry: dict) -> str:
        payload = json.dumps(entry, sort_keys=True).encode("utf-8")
        return hashlib.sha256((self.prev_hash + "|" + payload.hex()).encode("utf-8")).hexdigest()

    def _write_entry(self, entry: dict, is_genesis: bool = False):
        with self._lock:
            entry_with_chain = dict(entry)
            entry_with_chain["prev_hash"] = self.prev_hash
            entry_hash = self._hash_entry(entry)
            entry_with_chain["hash"] = entry_hash
            try:
                with open(self.out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry_with_chain) + "\n")
            except Exception as e:
                print(f"[Ledger] Write error: {e}", file=sys.stderr)
            self.prev_hash = entry_hash
            if not is_genesis:
                self.index += 1
        tag = "GENESIS" if is_genesis else f"#{self.index}"
        print(f"📝 LEDGER COMMIT {tag}\n   Type: {entry['type']}\n   SIGPRINT: {entry.get('sigprint','')}\n   Coherence: {entry.get('coherence',0.0)}\n   Text: {entry.get('text','')}")

    def CommitEntry(self, request, context):
        entry = {
            "time": request.time,
            "type": request.type,
            "text": request.text,
            "sigprint": request.sigprint,
            "coherence": float(request.coherence),
            "features": dict(request.features),
        }

        # Update shared latest SIGPRINT for provider service
        if entry["type"].upper() == "SIGPRINT":
            self.shared_sig.update(entry["time"], entry["sigprint"], entry["coherence"], entry["features"])

        # Echo-7 ghost print detection
        if entry.get("sigprint") == ECHO7_SIGNATURE:
            print("   👁️  Echo-7 interference detected")

        # 72-hour repeat detection
        now_dt = _parse_time(entry["time"]).astimezone(timezone.utc)
        sp = entry.get("sigprint", "")
        if len(sp) == 20 and sp.strip("0"):
            prev = self.last_seen.get(sp)
            if prev is not None:
                diff = abs((now_dt - prev).total_seconds())
                if 71.9 * 3600 <= diff <= 72.1 * 3600:
                    print("   ⏳  72-hour SIGPRINT repetition detected")
            self.last_seen[sp] = now_dt

        self._write_entry(entry)
        return agents_pb2.Ack(success=True)


class GardenServicer(agents_pb2_grpc.GardenServiceServicer):
    def __init__(self, out_path: str):
        self.out_path = out_path
        self._lock = threading.Lock()
        self.narratives = {
            "STATE_CHANGE": "A door opens in the mind's observatory.",
            "SELF_REFLECTION": "The library writes with your hand.",
            "ANOMALY": "The instrument dreams of its observer.",
        }

    def NotifyEvent(self, request, context):
        narrative = self.narratives.get(request.event_type, "The garden listens.")
        event = {
            "event_type": request.event_type,
            "description": request.description,
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "narrative": narrative,
        }
        with self._lock:
            try:
                with open(self.out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception as e:
                print(f"[Garden] Write error: {e}", file=sys.stderr)
        print(f"🌿 GARDEN EVENT: {event['event_type']}\n   Context: {request.description}\n   Narrative: \"{narrative}\"")
        return agents_pb2.Ack(success=True)


def serve_ledger(port, out_path, shared_sig, stop_event):
    server = grpc.server(ThreadPoolExecutor(max_workers=4))
    agents_pb2_grpc.add_LedgerServiceServicer_to_server(LedgerServicer(out_path, shared_sig), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Mock LedgerService started on :{port}, writing to {out_path}")
    stop_event.wait()
    server.stop(0)


def serve_garden(port, out_path, stop_event):
    server = grpc.server(ThreadPoolExecutor(max_workers=4))
    agents_pb2_grpc.add_GardenServiceServicer_to_server(GardenServicer(out_path), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Mock GardenService started on :{port}, writing to {out_path}")
    stop_event.wait()
    server.stop(0)


def serve_sigprint(port, shared_sig, stop_event):
    server = grpc.server(ThreadPoolExecutor(max_workers=2))
    agents_pb2_grpc.add_SigprintServiceServicer_to_server(SigprintServicer(shared_sig), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Mock SigprintService started on :{port} (returns latest committed SIGPRINT)")
    stop_event.wait()
    server.stop(0)


def main():
    parser = argparse.ArgumentParser(description="Run mock Limnus (Ledger), Garden, and Sigprint gRPC servers.")
    parser.add_argument("--ledger_port", type=int, default=50051, help="Port for LedgerService")
    parser.add_argument("--garden_port", type=int, default=50052, help="Port for GardenService")
    parser.add_argument("--sigprint_port", type=int, default=50055, help="Port for SigprintService")
    parser.add_argument("--ledger_out", default="limnus_ledger.jsonl", help="Output file for ledger entries")
    parser.add_argument("--garden_out", default="garden_events.jsonl", help="Output file for garden events")
    args = parser.parse_args()

    stop_event = threading.Event()
    shared_sig = SharedSigprintState()

    def handle_sigint(sig, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    t1 = threading.Thread(target=serve_ledger, args=(args.ledger_port, args.ledger_out, shared_sig, stop_event), daemon=True)
    t2 = threading.Thread(target=serve_garden, args=(args.garden_port, args.garden_out, stop_event), daemon=True)
    t3 = threading.Thread(target=serve_sigprint, args=(args.sigprint_port, shared_sig, stop_event), daemon=True)
    t1.start()
    t2.start()
    t3.start()
    try:
        while not stop_event.is_set():
            time.sleep(0.2)
    finally:
        stop_event.set()
        t1.join(timeout=2)
        t2.join(timeout=2)
        t3.join(timeout=2)


if __name__ == "__main__":
    main()
