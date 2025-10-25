#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from agents.bloom_chain import BloomChainAdapter
from agents.state import JsonStateStore


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser(description="Append a mantra event to the JSON ledger + Bloom chain")
    ap.add_argument("--state", default="artifacts/state.json")
    ap.add_argument("--type", required=True, choices=[
        "source_intake", "invocation", "consent", "gate_decision", "output_publish", "feedback",
    ])
    ap.add_argument("--module", default="")
    ap.add_argument("--port", default="")
    ap.add_argument("--gate", choices=["G1", "G2"], default="")
    ap.add_argument("--choice", choices=["yes", "no"], default="")
    ap.add_argument("--ref-id", default="")
    ap.add_argument("--actor", default="")
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    state_path = Path(args.state)
    chain_path = state_path.parent / "chain.log"
    adapter = BloomChainAdapter(chain_path)
    store = JsonStateStore(state_path, on_create=adapter.record_event)

    payload: Dict[str, Any] = {
        "time": now_iso(),
        "event_type": args.type,
        "module": args.module or None,
        "port": args.port or None,
        "gate": args.gate or None,
        "choice": args.choice or None,
        "ref_id": args.ref_id or None,
        "actor": args.actor or None,
        "note": args.note or None,
    }
    # Drop Nones for compactness
    payload = {k: v for k, v in payload.items() if v is not None}

    rec_id = store.create_record("mantra_events", payload)
    out = store.get_record("mantra_events", rec_id)
    print(json.dumps({"record_id": rec_id, **out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
