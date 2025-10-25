"""Glyph agent for generating and analysing G2V glyphs."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

import numpy as np

from agents.bloom_chain import BloomChainAdapter
from agents.state import JsonStateStore
from src.g2v.fft_codec import fft_encode, ifft_decode
from src.g2v.volume import glyph_from_tink_token


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class GlyphAgent:
    """Wraps G2V glyph generation and FFT analysis with shared-state logging."""

    def __init__(self, state_store: JsonStateStore, artifact_dir: str | Path = "artifacts/glyphs") -> None:
        self.state = state_store
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Core operations                                                    #
    # ------------------------------------------------------------------ #

    def generate_glyph(self, token: str, size: int = 32) -> Tuple[str, np.ndarray]:
        """Create a glyph matrix from token and register it in state."""
        matrix = glyph_from_tink_token(token, size)
        matrix = np.asarray(matrix, dtype=float)

        glyph_id = self._new_glyph_id()
        file_path = self.artifact_dir / f"{glyph_id}.npy"
        np.save(file_path, matrix)

        record = {
            "token": token,
            "size": size,
            "file": str(file_path),
            "created": _utc_now(),
        }
        self.state.create_record("glyphs", record, record_id=glyph_id)
        return glyph_id, matrix

    def analyze_glyph_fft(self, glyph_id: str) -> Tuple[str, dict]:
        """Perform FFT round-trip and log spectral metrics."""
        glyph_record = self.state.get_record("glyphs", glyph_id)
        file_path = Path(glyph_record["file"])
        if not file_path.exists():
            raise FileNotFoundError(f"glyph matrix missing: {file_path}")

        matrix = np.load(file_path)
        spectrum = fft_encode(matrix)
        recon = ifft_decode(spectrum)

        mse = float(np.mean((matrix - recon) ** 2))
        fft_mean = float(np.abs(np.fft.fftshift(np.fft.fft2(matrix))).mean())

        analysis = {
            "source": glyph_id,
            "mse": mse,
            "fft_mean": fft_mean,
            "created": _utc_now(),
        }
        analysis_id = self.state.create_record("glyph_analysis", analysis)
        return analysis_id, analysis

    def list_glyphs(self) -> dict:
        """Return snapshot of registered glyphs."""
        return self.state.list_section("glyphs")

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _new_glyph_id() -> str:
        return f"glyph_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------- #
# CLI interface                                                          #
# ---------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="glyph-agent", description="Glyph generation and FFT analysis agent")
    parser.add_argument(
        "--state",
        default="artifacts/state.json",
        help="Path to shared state ledger (default: artifacts/state.json)",
    )
    parser.add_argument(
        "--artifacts",
        default="artifacts/glyphs",
        help="Directory for glyph .npy outputs (default: artifacts/glyphs)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("gen", help="Generate glyph matrix from token")
    gen.add_argument("--token", required=True, help="Glyph token, e.g. 'I-Glyph'")
    gen.add_argument("--size", type=int, default=32, help="Glyph resolution (default: 32)")

    fft = sub.add_parser("fft", help="Analyse glyph FFT metrics")
    fft.add_argument("--glyph-id", required=True, help="Glyph identifier returned from gen")

    sub.add_parser("list", help="List glyph entries in state")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    adapter = BloomChainAdapter(state_path.parent / "chain.log")
    state = JsonStateStore(state_path, on_create=adapter.record_event)
    agent = GlyphAgent(state, artifact_dir=args.artifacts)

    if args.command == "gen":
        glyph_id, _ = agent.generate_glyph(args.token, size=args.size)
        print(json.dumps({"glyph_id": glyph_id, "token": args.token, "size": args.size}))
    elif args.command == "fft":
        analysis_id, metrics = agent.analyze_glyph_fft(args.glyph_id)
        metrics = {"analysis_id": analysis_id, **metrics}
        print(json.dumps(metrics))
    elif args.command == "list":
        print(json.dumps(agent.list_glyphs(), indent=2))
    else:
        parser.error("unknown command")


if __name__ == "__main__":
    main()
