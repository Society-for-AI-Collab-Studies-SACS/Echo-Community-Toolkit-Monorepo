#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _read_chain(chain_path: Path) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    if not chain_path.exists():
        return blocks
    for line in chain_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            blocks.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return blocks


def _rehash_block(index: int, prev_hash: str, payload: Dict[str, Any]) -> str:
    content = f"{index}|{prev_hash}|{json.dumps(payload, sort_keys=True)}".encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def verify(state_path: Path, chain_path: Path) -> Dict[str, Any]:
    problems: List[str] = []
    state: Dict[str, Dict[str, Any]] = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"state.json decode error: {e}")
    else:
        problems.append("state.json missing")

    blocks = _read_chain(chain_path)

    # 1) Verify chain linkage and hashes
    link_ok = True
    for i, blk in enumerate(blocks):
        expected_prev = blocks[i - 1]["hash"] if i > 0 else "GENESIS"
        if blk.get("prev_hash") != expected_prev:
            problems.append(f"block[{i}] prev_hash mismatch")
            link_ok = False
        payload = blk.get("payload", {})
        recomputed = _rehash_block(blk.get("index", i), expected_prev, payload)
        if blk.get("hash") != recomputed:
            problems.append(f"block[{i}] hash mismatch")
            link_ok = False

    # 2) Verify state back-references
    # Build lookup by hash
    by_hash = {blk.get("hash"): blk for blk in blocks}
    backref_ok = True
    for section, bucket in state.items():
        if not isinstance(bucket, dict):
            continue
        for rec_id, rec in bucket.items():
            h = rec.get("block_hash")
            if not h:
                continue
            blk = by_hash.get(h)
            if not blk:
                problems.append(f"{section}:{rec_id} block_hash not found in chain")
                backref_ok = False
                continue
            payload = blk.get("payload", {})
            if payload.get("type") != section or payload.get("record_id") != rec_id:
                problems.append(f"{section}:{rec_id} payload type/id mismatch")
                backref_ok = False
            # Compare data ignoring block_hash (which is added after append)
            st_data = {k: v for k, v in rec.items() if k != "block_hash"}
            if payload.get("data") != st_data:
                problems.append(f"{section}:{rec_id} payload data mismatch vs state")
                backref_ok = False

    ok = link_ok and backref_ok and len(problems) == 0
    return {
        "ok": ok,
        "counts": {"blocks": len(blocks), "sections": len(state)},
        "link_ok": link_ok,
        "backref_ok": backref_ok,
        "problems": problems,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify JSON ledger against Bloom Chain append-only log")
    ap.add_argument("--state", default="artifacts/state.json")
    ap.add_argument("--chain", default="artifacts/chain.log")
    ap.add_argument("--json", default="", help="Optional output report path")
    args = ap.parse_args()
    report = verify(Path(args.state), Path(args.chain))
    out = json.dumps(report, indent=2)
    print(out)
    if args.json:
        Path(args.json).write_text(out, encoding="utf-8")
    # Non-zero exit on failure for CI-friendly usage
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()

