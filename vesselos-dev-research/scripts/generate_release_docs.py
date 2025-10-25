#!/usr/bin/env python3
"""Automate release documentation for VesselOS Dev Research.

This helper script refreshes the Kira knowledge artifacts and assembles
release notes summarising commits and documentation updates since the
previous tag (or a caller-specified starting point).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTES = ROOT / "dist" / "RELEASE_NOTES.md"


def _run(cmd: List[str], *, check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess rooted at the repository."""
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {result.stderr or result.stdout}")
    return result


def _latest_tag() -> Optional[str]:
    proc = _run(["git", "describe", "--tags", "--abbrev=0"], check=False)
    if proc.returncode == 0:
        tag = proc.stdout.strip()
        return tag or None
    return None


def _previous_tag(exclude: Optional[str] = None) -> Optional[str]:
    proc = _run(["git", "tag", "--sort=-creatordate"], check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    for raw in proc.stdout.strip().splitlines():
        tag = raw.strip()
        if not tag:
            continue
        if exclude and tag == exclude:
            continue
        return tag
    return None


def _git_log(range_ref: Optional[str]) -> str:
    args = ["git", "log", "--no-merges", "--pretty=format:* %h %s"]
    if range_ref:
        args.append(range_ref)
    else:
        args.append("HEAD")
    proc = _run(args, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return "- No commits found in range."
    return proc.stdout.strip()


def _git_diff_docs(range_ref: Optional[str]) -> str:
    if not range_ref:
        return "- (no previous tag detected)"
    proc = _run(["git", "diff", "--name-status", range_ref, "--", "docs/"], check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return "- No documentation changes."
    lines = []
    for row in proc.stdout.strip().splitlines():
        status, path = row.split("\t", 1)
        lines.append(f"- {status} {path}")
    return "\n".join(lines)


def _run_kira_codegen(workspace: Optional[str], emit_types: bool) -> Optional[dict]:
    cmd = [sys.executable, "vesselos.py", "kira", "codegen", "--docs"]
    if emit_types:
        cmd.append("--types")
    if workspace:
        cmd.extend(["--workspace", workspace])
    proc = _run(cmd)
    stdout = proc.stdout.strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def _format_knowledge_section(snapshot: Optional[dict]) -> str:
    if not snapshot:
        return "- Knowledge snapshot unavailable."
    workspaces = snapshot.get("workspaces") or []
    if not workspaces:
        return "- No workspaces discovered."
    lines: List[str] = []
    for entry in workspaces:
        name = entry.get("workspace", "unknown")
        memories = entry.get("memory_count", 0)
        ledger = entry.get("ledger_count", 0)
        lines.append(f"- `{name}` workspace: {memories} memories; {ledger} ledger blocks.")
    return "\n".join(lines)


def _build_notes(
    tag: Optional[str],
    since_ref: Optional[str],
    commits: str,
    docs_changes: str,
    knowledge: str,
) -> str:
    timestamp = datetime.now(timezone.utc).isoformat()
    compare_range = f"{since_ref}..{tag or 'HEAD'}" if since_ref else "HEAD"
    sections = [
        f"# VesselOS Release Notes for {tag or 'Unreleased'}",
        "",
        f"_Generated at {timestamp}_",
        "",
        f"**Comparison Range:** {compare_range}",
        "",
        "## Commits",
        commits,
        "",
        "## Documentation Changes",
        docs_changes,
        "",
        "## Knowledge Snapshot",
        knowledge,
        "",
    ]
    return "\n".join(sections)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate release notes and knowledge docs.")
    parser.add_argument("--tag", default=None, help="Target release tag (defaults to HEAD).")
    parser.add_argument(
        "--since",
        default=None,
        help="Starting reference (e.g. previous tag). If omitted, the latest tag is used.",
    )
    parser.add_argument("--workspace", default=None, help="Limit knowledge summary to a workspace.")
    parser.add_argument("--types", action="store_true", help="Also emit TypeScript type definitions.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_NOTES),
        help="Path to write the release notes markdown.",
    )
    args = parser.parse_args(argv)

    if args.since:
        since_ref = args.since
    elif args.tag:
        since_ref = _previous_tag(exclude=args.tag)
    else:
        since_ref = _latest_tag()
    range_ref = f"{since_ref}..HEAD" if since_ref else None

    snapshot = _run_kira_codegen(args.workspace, args.types)
    commits = _git_log(range_ref)
    docs_changes = _git_diff_docs(range_ref)
    knowledge = _format_knowledge_section(snapshot)
    notes = _build_notes(args.tag, since_ref, commits, docs_changes, knowledge)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(notes, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
