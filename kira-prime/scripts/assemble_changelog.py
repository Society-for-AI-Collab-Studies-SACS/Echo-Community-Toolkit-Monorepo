#!/usr/bin/env python3
"""
Assemble a simple changelog segment since the previous tag.
"""

from __future__ import annotations

import subprocess
import sys


def run(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, text=True).strip()


def main() -> None:
    try:
        last_tag = run("git describe --tags --abbrev=0")
    except subprocess.CalledProcessError:
        last_tag = ""

    if last_tag:
        log = run(f'git log {last_tag}..HEAD --pretty="* %s"')
        print(f"## Changes since {last_tag}\n\n{log}")
    else:
        log = run('git log --pretty="* %s"')
        print("## Changes\n\n" + log)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"Failed to assemble changelog: {exc}\n")
        sys.exit(exc.returncode or 1)
