#!/usr/bin/env python3
"""Trigger a full MRP chapter generation run for a dictation session."""

from __future__ import annotations

import argparse
from pathlib import Path

from library_core.dictation import start_session
from library_core.dictation.pipeline import MRPPipeline
from workspace.manager import WorkspaceManager


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 20-chapter MRP pipeline.")
    parser.add_argument("--workspace", default="default", help="Workspace identifier")
    parser.add_argument("--session", default=None, help="Optional session id (default: timestamp)")
    parser.add_argument(
        "--input", dest="input_text", default=None,
        help="Optional text to log as the first dictation turn",
    )
    parser.add_argument(
        "--from-file", dest="input_file", default=None,
        help="Path to a text file that will be logged as the first turn",
    )
    parser.add_argument(
        "--no-schema", dest="run_schema", action="store_false",
        help="Skip schema_builder.py before generating chapters",
    )
    parser.add_argument(
        "--validate", dest="run_validation", action="store_true",
        help="Run kira-prime validation after generation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manager = WorkspaceManager()

    session = start_session(
        args.workspace,
        manager=manager,
        session_id=args.session,
        description="Automated MRP cycle",
    )

    seed_text: str | None = args.input_text
    if args.input_file:
        seed_text = Path(args.input_file).read_text(encoding="utf-8")

    if seed_text:
        session.record_turn("user", seed_text, tags={"seed": "true"})

    pipeline = MRPPipeline(session)
    output_dir = pipeline.run(
        run_schema=args.run_schema,
        run_kira_validation=args.run_validation,
    )

    print("MRP cycle complete.")
    print(f"Session: {session.session_id}")
    print(f"Workspace: {args.workspace}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()
