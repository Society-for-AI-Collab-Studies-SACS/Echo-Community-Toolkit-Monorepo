#!/usr/bin/env python3
"""Enhanced VesselOS entry point that keeps Prime CLI compatibility and adds audit commands."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Optional

import click

from cli.prime import main as prime_main

ROOT = Path(__file__).resolve().parent
SRC_PY = ROOT / "src_py"
for path in (ROOT, SRC_PY):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from src_py.vesselos.cli.audit_commands import audit as audit_group  # noqa: E402


@click.group()
def cli() -> None:
    """VesselOS command interface."""


cli.add_command(audit_group, name="audit")


def _run_click(args: Iterable[str]) -> int:
    """Invoke the click CLI while capturing its exit code."""
    try:
        cli.main(args=args, prog_name="vesselos", standalone_mode=False)
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Entry point compatible with both the Prime CLI and the new audit commands."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in cli.commands:
        return _run_click(args)
    return prime_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
