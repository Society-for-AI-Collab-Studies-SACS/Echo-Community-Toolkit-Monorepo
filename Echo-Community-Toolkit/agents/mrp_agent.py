"""MRP Phase-A steganography agent."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from agents.bloom_chain import BloomChainAdapter
from agents.state import JsonStateStore
from src.mrp.codec import decode, encode


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MRPAgent:
    """Handles multi-channel embed/extract operations with shared ledger logging."""

    def __init__(self, state_store: JsonStateStore, artifact_dir: str | Path = "artifacts/mrp") -> None:
        self.state = state_store
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def embed_message(
        self,
        cover_path: str,
        message: str,
        metadata: Dict[str, object] | None = None,
        out_path: str | None = None,
    ) -> Tuple[str, str]:
        metadata = metadata or {}
        cover = Path(cover_path)
        if not cover.exists():
            raise FileNotFoundError(f"cover image not found: {cover}")

        if out_path is None:
            out_path = self.artifact_dir / f"stego_{uuid.uuid4().hex[:8]}.png"
        else:
            out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        encode(str(cover), str(out_path), message, metadata)

        record = {
            "cover": str(cover),
            "output": str(out_path),
            "message": message,
            "metadata": metadata,
            "created": _utc_now(),
        }
        embed_id = self.state.create_record("mrp_embeds", record)
        return embed_id, str(out_path)

    def extract_message(self, stego_path: str) -> Tuple[str, Dict[str, object], Dict[str, object]]:
        stego = Path(stego_path)
        if not stego.exists():
            raise FileNotFoundError(f"stego image not found: {stego}")

        message, metadata, ecc = decode(str(stego))
        record = {
            "stego": str(stego),
            "message": message,
            "metadata": metadata,
            "ecc": ecc,
            "created": _utc_now(),
        }
        extract_id = self.state.create_record("mrp_extracts", record)
        return extract_id, record, ecc

    def list_embeds(self) -> Dict[str, Dict[str, object]]:
        return self.state.list_section("mrp_embeds")

    def list_extracts(self) -> Dict[str, Dict[str, object]]:
        return self.state.list_section("mrp_extracts")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mrp-agent", description="MRP Phase-A steganography agent")
    parser.add_argument(
        "--state",
        default="artifacts/state.json",
        help="Path to shared state ledger (default: artifacts/state.json)",
    )
    parser.add_argument(
        "--artifacts",
        default="artifacts/mrp",
        help="Directory for generated stego outputs (default: artifacts/mrp)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    embed = sub.add_parser("embed", help="Embed message into cover image")
    embed.add_argument("--cover", required=True, help="Input cover PNG")
    embed.add_argument("--message", required=True, help="Message text to embed")
    embed.add_argument("--metadata", default="{}", help="Optional JSON metadata string")
    embed.add_argument("--out", help="Output stego path (default: auto)")

    extract = sub.add_parser("extract", help="Extract message from stego image")
    extract.add_argument("--stego", required=True, help="Stego PNG path")

    sub.add_parser("list-embeds", help="List embed operations")
    sub.add_parser("list-extracts", help="List extraction operations")

    return parser


def _load_metadata(raw: str) -> Dict[str, object]:
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid metadata JSON: {exc}") from exc


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    adapter = BloomChainAdapter(state_path.parent / "chain.log")
    state = JsonStateStore(state_path, on_create=adapter.record_event)
    agent = MRPAgent(state, artifact_dir=args.artifacts)

    if args.command == "embed":
        metadata = _load_metadata(args.metadata)
        embed_id, out_path = agent.embed_message(args.cover, args.message, metadata, args.out)
        print(json.dumps({"embed_id": embed_id, "output": out_path}))
    elif args.command == "extract":
        extract_id, record, ecc = agent.extract_message(args.stego)
        payload = {"extract_id": extract_id, "message": record["message"], "metadata": record["metadata"], "ecc": ecc}
        print(json.dumps(payload))
    elif args.command == "list-embeds":
        print(json.dumps(agent.list_embeds(), indent=2))
    elif args.command == "list-extracts":
        print(json.dumps(agent.list_extracts(), indent=2))
    else:
        parser.error("unknown command")


if __name__ == "__main__":
    main()
