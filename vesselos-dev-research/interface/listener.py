"""
Thin wrapper to align with scaffolds that expect interface/listener.py.
Delegates to pipeline.listener.
"""
from __future__ import annotations

from pipeline.listener import main as _main  # type: ignore


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - thin wrapper
    import sys

    _main(sys.argv if argv is None else argv)


if __name__ == "__main__":
    main()

