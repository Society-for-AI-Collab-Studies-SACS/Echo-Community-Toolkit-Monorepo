#!/usr/bin/env python3
"""
Repo Sentinel — a watcher that snapshots file hashes and reports drift.

Usage:
    python scripts/repo_sentinel.py
    python scripts/repo_sentinel.py --root Echo-Community-Toolkit --state .cache/sentinel.json

On each run the sentinel compares the current manifest against the stored state file
and prints added, removed, or modified paths. It then refreshes the state unless
--no-update is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "node_modules",
    "venv",
}

DEFAULT_STATE_PATH = Path("scripts/.repo_sentinel_state.json")


@dataclass(frozen=True)
class FileRecord:
    path: str
    digest: str
    size: int
    mtime: float


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Snapshot repository state and report drift.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Root directory to watch (defaults to repository root).",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help=f"State file to store manifest (defaults to {DEFAULT_STATE_PATH}).",
    )
    parser.add_argument(
        "--ignore-dir",
        action="append",
        default=[],
        help="Directory name to ignore (can be supplied multiple times).",
    )
    parser.add_argument(
        "--ignore-glob",
        action="append",
        default=[],
        help="Glob pattern (relative to root) to ignore.",
    )
    parser.add_argument(
        "--algorithm",
        default="sha256",
        choices=hashlib.algorithms_available,
        help="Hash algorithm to use (defaults to sha256).",
    )
    parser.add_argument(
        "--no-update",
        action="store_true",
        help="Do not update the stored state file after reporting.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit drift report as JSON for downstream tooling.",
    )
    return parser.parse_args(argv)


def should_skip_dir(relative_dir: Path, skip_dirs: Set[str], ignore_globs: Sequence[str]) -> bool:
    for part in relative_dir.parts:
        if part in skip_dirs:
            return True
    rel_str = str(relative_dir).replace("\\", "/")
    return any(Path(rel_str).match(pattern) for pattern in ignore_globs)


def should_skip_file(relative_file: Path, ignore_globs: Sequence[str]) -> bool:
    rel_str = str(relative_file).replace("\\", "/")
    return any(Path(rel_str).match(pattern) for pattern in ignore_globs)


def walk_files(root: Path, skip_dirs: Set[str], ignore_globs: Sequence[str]) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).resolve().relative_to(root.resolve())
        dirnames[:] = [
            d for d in dirnames if not should_skip_dir(rel_dir / d, skip_dirs, ignore_globs)
        ]
        for name in filenames:
            candidate = Path(dirpath, name)
            rel_path = candidate.resolve().relative_to(root.resolve())
            if should_skip_file(rel_path, ignore_globs):
                continue
            yield candidate


def hash_file(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_manifest(root: Path, algorithm: str, skip_dirs: Set[str], ignore_globs: Sequence[str]) -> Dict[str, FileRecord]:
    manifest: Dict[str, FileRecord] = {}
    for file_path in walk_files(root, skip_dirs, ignore_globs):
        rel_path = file_path.resolve().relative_to(root.resolve())
        digest = hash_file(file_path, algorithm)
        stat = file_path.stat()
        manifest[str(rel_path).replace("\\", "/")] = FileRecord(
            path=str(rel_path).replace("\\", "/"),
            digest=digest,
            size=stat.st_size,
            mtime=stat.st_mtime,
        )
    return manifest


def load_state(path: Path) -> Optional[Dict[str, Dict[str, object]]]:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"[repo-sentinel] Warning: could not parse state file {path}: {exc}", file=sys.stderr)
        return None


def store_state(path: Path, manifest: Dict[str, FileRecord], root: Path, algorithm: str) -> None:
    payload = {
        "version": 1,
        "algorithm": algorithm,
        "root": str(root),
        "created_at": time.time(),
        "files": {record.path: record.__dict__ for record in manifest.values()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def diff_manifests(
    previous: Optional[Dict[str, Dict[str, object]]],
    current: Dict[str, FileRecord],
) -> Tuple[List[str], List[str], List[str]]:
    if not previous or "files" not in previous:
        return sorted(current.keys()), [], []

    prev_files = previous["files"]
    prev_set = set(prev_files.keys())
    curr_set = set(current.keys())

    added = sorted(curr_set - prev_set)
    removed = sorted(prev_set - curr_set)
    modified = sorted(
        path
        for path in curr_set & prev_set
        if prev_files[path].get("digest") != current[path].digest
    )

    return added, removed, modified


def emit_report(
    added: Sequence[str],
    removed: Sequence[str],
    modified: Sequence[str],
    json_mode: bool,
) -> None:
    if json_mode:
        payload = {
            "added": list(added),
            "removed": list(removed),
            "modified": list(modified),
        }
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return

    if not added and not removed and not modified:
        print("[repo-sentinel] No drift detected.")
        return

    if added:
        print("[repo-sentinel] Added:")
        for path in added:
            print(f"  + {path}")
    if removed:
        print("[repo-sentinel] Removed:")
        for path in removed:
            print(f"  - {path}")
    if modified:
        print("[repo-sentinel] Modified:")
        for path in modified:
            print(f"  * {path}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    root = args.root.resolve()
    if not root.exists():
        print(f"[repo-sentinel] Root does not exist: {root}", file=sys.stderr)
        return 2

    skip_dirs = DEFAULT_SKIP_DIRS | set(args.ignore_dir)
    ignore_globs = tuple(args.ignore_glob)

    previous = load_state(args.state)
    manifest = build_manifest(root, args.algorithm, skip_dirs, ignore_globs)
    added, removed, modified = diff_manifests(previous, manifest)
    emit_report(added, removed, modified, args.json)

    if not args.no_update:
        store_state(args.state, manifest, root, args.algorithm)

    return 0


if __name__ == "__main__":
    sys.exit(main())

