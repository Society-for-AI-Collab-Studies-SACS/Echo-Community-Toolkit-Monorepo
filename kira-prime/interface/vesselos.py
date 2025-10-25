#!/usr/bin/env python3
"""
Wrapper CLI entry under interface/ to align with alternate scaffolds.
Delegates to the root-level vesselos.main.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    import vesselos as _root_cli  # type: ignore

    return _root_cli.main(sys.argv if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())

