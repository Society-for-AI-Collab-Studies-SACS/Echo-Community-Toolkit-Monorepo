"""Legacy LSB1 steganography agent."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from agents.bloom_chain import BloomChainAdapter
from agents.state import JsonStateStore
from src.lsb_encoder_decoder import LSBCodec
from src.lsb_extractor import LSBExtractor


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class LSBAgent:
    """Thin wrapper around LSB1 encoder/decoder with state logging."""

    def __init__(self, state_store: JsonStateStore, artifact_dir: str | Path = "artifacts/lsb") -> None:
        self.state = state_store
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.codec = LSBCodec()
        self.extractor = LSBExtractor()

    def create_cover(self, width: int, height: int, out_path: str | None = None) -> str:
        if out_path is None:
            out_path = self.artifact_dir / f"cover_{uuid.uuid4().hex[:8]}.png"
        else:
            out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img = self.codec.create_cover_image(width, height)
        img.save(out_path, "PNG")
        record = {
            "output": str(out_path),
            "width": width,
            "height": height,
            "created": _utc_now(),
        }
        cover_id = self.state.create_record("lsb_covers", record)
        return cover_id

    def embed_message(
        self,
        cover_path: str,
        message: str,
        out_path: str | None = None,
        use_crc: bool = True,
    ) -> Tuple[str, str, Dict[str, object]]:
        cover = Path(cover_path)
        if not cover.exists():
            raise FileNotFoundError(f"cover image not found: {cover}")
        if out_path is None:
            out_path = self.artifact_dir / f"lsb_{uuid.uuid4().hex[:8]}.png"
        else:
            out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        info = self.codec.encode_message(str(cover), message, str(out_path), use_crc)
        record = {
            "cover": str(cover),
            "output": str(out_path),
            "message": message,
            "use_crc": use_crc,
            "encoder_info": info,
            "created": _utc_now(),
        }
        embed_id = self.state.create_record("lsb_embeds", record)
        return embed_id, str(out_path), info

    def extract_message(self, stego_path: str) -> Tuple[str, Dict[str, object]]:
        stego = Path(stego_path)
        if not stego.exists():
            raise FileNotFoundError(f"stego image not found: {stego}")
        result = self.extractor.extract_from_image(str(stego))
        record = {
            "stego": str(stego),
            "result": result,
            "created": _utc_now(),
        }
        extract_id = self.state.create_record("lsb_extracts", record)
        return extract_id, result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lsb-agent", description="LSB1 steganography agent")
    parser.add_argument(
        "--state",
        default="artifacts/state.json",
        help="Path to shared state ledger (default: artifacts/state.json)",
    )
    parser.add_argument(
        "--artifacts",
        default="artifacts/lsb",
        help="Directory for generated assets (default: artifacts/lsb)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    cover = sub.add_parser("cover", help="Create a blank cover image")
    cover.add_argument("--width", type=int, default=512, help="Cover width (default: 512)")
    cover.add_argument("--height", type=int, default=512, help="Cover height (default: 512)")
    cover.add_argument("--out", help="Output path (default: artifacts/lsb/cover_<id>.png)")

    embed = sub.add_parser("embed", help="Embed message using LSB1")
    embed.add_argument("--cover", required=True, help="Input cover PNG")
    embed.add_argument("--message", required=True, help="Message text to embed")
    embed.add_argument("--out", help="Output stego path (default: auto)")
    embed.add_argument("--no-crc", action="store_true", help="Disable CRC32 in payload header")

    extract = sub.add_parser("extract", help="Extract message from LSB stego image")
    extract.add_argument("--stego", required=True, help="Stego PNG path")

    sub.add_parser("list-covers", help="List generated covers")
    sub.add_parser("list-embeds", help="List LSB embed operations")
    sub.add_parser("list-extracts", help="List LSB extraction operations")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    adapter = BloomChainAdapter(state_path.parent / "chain.log")
    state = JsonStateStore(state_path, on_create=adapter.record_event)
    agent = LSBAgent(state, artifact_dir=args.artifacts)

    if args.command == "cover":
        cover_id = agent.create_cover(args.width, args.height, args.out)
        print(json.dumps({"cover_id": cover_id, "output": args.out or "auto"}))
    elif args.command == "embed":
        embed_id, output_path, info = agent.embed_message(args.cover, args.message, args.out, use_crc=not args.no_crc)
        payload = {"embed_id": embed_id, "output": output_path, "encoder_info": info}
        print(json.dumps(payload))
    elif args.command == "extract":
        extract_id, result = agent.extract_message(args.stego)
        print(json.dumps({"extract_id": extract_id, "result": result}, indent=2))
    elif args.command == "list-covers":
        print(json.dumps(state.list_section("lsb_covers"), indent=2))
    elif args.command == "list-embeds":
        print(json.dumps(state.list_section("lsb_embeds"), indent=2))
    elif args.command == "list-extracts":
        print(json.dumps(state.list_section("lsb_extracts"), indent=2))
    else:
        parser.error("unknown command")


if __name__ == "__main__":
    main()
