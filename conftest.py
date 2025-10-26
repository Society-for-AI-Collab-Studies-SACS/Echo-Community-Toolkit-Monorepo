"""Root-level pytest customisations for the monorepo."""

from __future__ import annotations

from pathlib import Path

SKIP_ROOTS = (
    Path("archives"),
    Path("g2v_repo"),
    Path("pr"),
)


def pytest_ignore_collect(path, config) -> bool:  # pragma: no cover
    """Skip test collection under snapshot directories that shadow active modules."""
    # Pytest passes a pathlib.Path on recent versions; fall back to str otherwise.
    candidate = Path(str(path))
    try:
        relative = candidate.relative_to(config.rootpath)
    except ValueError:
        return False

    return any(
        relative == skip_root or skip_root in relative.parents for skip_root in SKIP_ROOTS
    )
