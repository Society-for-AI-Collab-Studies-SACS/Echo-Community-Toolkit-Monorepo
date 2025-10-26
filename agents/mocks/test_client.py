#!/usr/bin/env python3
"""
Test Client for SIGPRINT Integration
Simulates both a SIGPRINT agent and a journal logger against the mock services.

Usage:
  1) Start mocks in one terminal:
     bazel run //agents/mocks:mock_services
  2) Run this client in another terminal:
     bazel run //agents/mocks:test_client
"""

import argparse
import random
import string
import threading
import time
from datetime import datetime

try:
    import grpc
except ModuleNotFoundError:  # CI image lacks native grpc; fall back to stub
    from tests._stubs import grpc as grpc
from google.protobuf import empty_pb2

from protos import agents_pb2, agents_pb2_grpc

class TestSigprintAgent(threading.Thread):
    """Simulates the SIGPRINT agent behavior (no EEG, synthetic signatures)."""

    def __init__(self, ledger_addr, garden_addr, interval=1.0, stop_event=None):
        super().__init__(daemon=True)
        self.ledger_stub = agents_pb2_grpc.LedgerServiceStub(grpc.insecure_channel(ledger_addr))
        self.garden_stub = agents_pb2_grpc.GardenServiceStub(grpc.insecure_channel(garden_addr))
        self.interval = interval
        self.last_sigprint = None
        self.stop_event = stop_event or threading.Event()

    def run(self):
        print("[TestSigprintAgent] starting...")
        while not self.stop_event.is_set():
            coherence = max(0.0, min(100.0, 65.0 + random.gauss(0, 10)))

            if random.random() < 0.1:
                sigprint = "48152709316470239518"  # fun pattern
                coherence = 87.3
                print("[TestSigprintAgent] Echo-7 interference detected")
            else:
                sigprint = "".join(str(random.randint(0, 9)) for _ in range(20))

            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            features = {
                "frontal_pct": random.uniform(30, 50),
                "occipital_pct": random.uniform(40, 60),
                "phase_diff_F3_F4": random.uniform(0, 30),
            }

            # Commit to ledger
            entry = agents_pb2.LedgerEntry(
                time=now,
                type="SIGPRINT",
                text="",
                sigprint=sigprint,
                coherence=float(coherence),
                features=features,
            )
            try:
                self.ledger_stub.CommitEntry(entry)
            except Exception as e:
                print(f"[TestSigprintAgent] Ledger commit failed: {e}")

            # Gate detection via Hamming distance
            if self.last_sigprint:
                changes = sum(1 for a, b in zip(sigprint, self.last_sigprint) if a != b)
                if changes >= 5:
                    print(f"[TestSigprintAgent] GATE DETECTED! ({changes} digit changes)")
                    event = agents_pb2.GardenEvent(
                        event_type="STATE_CHANGE",
                        description=f"Gate transition: {changes} digits changed, coherence={coherence:.1f}",
                    )
                    try:
                        self.garden_stub.NotifyEvent(event)
                    except Exception as e:
                        print(f"[TestSigprintAgent] Garden notify failed: {e}")

            self.last_sigprint = sigprint

            # High coherence alert
            if coherence > 90:
                event = agents_pb2.GardenEvent(
                    event_type="ANOMALY",
                    description=f"coherence>{coherence:.1f} - Approaching singularity",
                )
                try:
                    self.garden_stub.NotifyEvent(event)
                except Exception as e:
                    print(f"[TestSigprintAgent] Garden notify failed: {e}")

            self.stop_event.wait(self.interval)


class TestJournalLogger(threading.Thread):
    """Simulates journal entries with SIGPRINT tagging."""

    def __init__(self, sigprint_addr, ledger_addr, garden_addr, interval=5.0, stop_event=None):
        super().__init__(daemon=True)
        self.sig_stub = agents_pb2_grpc.SigprintServiceStub(grpc.insecure_channel(sigprint_addr))
        self.ledger_stub = agents_pb2_grpc.LedgerServiceStub(grpc.insecure_channel(ledger_addr))
        self.garden_stub = agents_pb2_grpc.GardenServiceStub(grpc.insecure_channel(garden_addr))
        self.interval = interval
        self.stop_event = stop_event or threading.Event()
        self.counter = 0

    def _random_text(self):
        self.counter += 1
        blob = "".join(random.choice(string.ascii_lowercase + "     ") for _ in range(40)).strip()
        return f"test-entry-{self.counter}: {blob}"

    def run(self):
        print("[TestJournalLogger] starting...")
        while not self.stop_event.is_set():
            entry_text = self._random_text()
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            sigprint = ""
            coherence = 0.0
            features = {}
            try:
                update = self.sig_stub.GetLatestSigprint(empty_pb2.Empty())
                sigprint = update.sigprint
                coherence = update.coherence
                features = dict(update.features)
            except Exception as e:
                print(f"[TestJournalLogger] GetLatestSigprint failed: {e}")

            entry = agents_pb2.LedgerEntry(
                time=now,
                type="JOURNAL",
                text=entry_text,
                sigprint=sigprint,
                coherence=coherence,
                features=features,
            )
            try:
                self.ledger_stub.CommitEntry(entry)
                print(f"[TestJournalLogger] Logged entry with sig={sigprint}")
            except Exception as e:
                print(f"[TestJournalLogger] Ledger commit failed: {e}")

            try:
                event = agents_pb2.GardenEvent(event_type="SELF_REFLECTION", description="Automated journal test entry")
                self.garden_stub.NotifyEvent(event)
            except Exception as e:
                print(f"[TestJournalLogger] Garden notify failed: {e}")

            self.stop_event.wait(self.interval)


def main():
    parser = argparse.ArgumentParser(description="Run a test client simulating SIGPRINT + Journal against mocks.")
    parser.add_argument("--ledger_addr", default="localhost:50051", help="LedgerService host:port")
    parser.add_argument("--garden_addr", default="localhost:50052", help="GardenService host:port")
    parser.add_argument("--sigprint_addr", default="localhost:50055", help="SigprintService host:port to query")
    parser.add_argument("--sigprint_interval", type=float, default=1.0, help="Seconds between SIGPRINT updates")
    parser.add_argument("--journal_interval", type=float, default=5.0, help="Seconds between journal entries")
    parser.add_argument("--run_for", type=float, default=0.0, help="Stop after N seconds (0 = until Ctrl+C)")
    args = parser.parse_args()

    stop_event = threading.Event()
    sig_thread = TestSigprintAgent(args.ledger_addr, args.garden_addr, interval=args.sigprint_interval, stop_event=stop_event)
    jnl_thread = TestJournalLogger(args.sigprint_addr, args.ledger_addr, args.garden_addr, interval=args.journal_interval, stop_event=stop_event)
    sig_thread.start()
    jnl_thread.start()

    try:
        if args.run_for > 0:
            time.sleep(args.run_for)
        else:
            while True:
                time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        print("[TestClient] stopping...")
        stop_event.set()
        sig_thread.join(timeout=2)
        jnl_thread.join(timeout=2)


if __name__ == "__main__":
    main()
