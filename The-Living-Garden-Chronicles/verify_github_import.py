#!/usr/bin/env python3
"""
Verify that the imported GitHub repository has the expected commit and files.

Usage:
  export GITHUB_TOKEN=ghp_...        # Optional: only needed for private repos or to raise rate limits
  python verify_github_import.py --owner YourUser --repo The-Living-Garden-Chronicles \
      --commit 27bfebf389ef0a6b3b3d66afce94ca324f4db14f \
      --path frontend/index.html
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

API_ROOT = "https://api.github.com"


def github_request(path: str, token: str | None) -> dict:
    req = urllib.request.Request(f"{API_ROOT}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise SystemExit(f"GitHub API call failed: {resp.status} {resp.reason}")
        return json.load(resp)


def verify_commit(owner: str, repo: str, expected_sha: str, token: str | None) -> None:
    data = github_request(f"/repos/{owner}/{repo}/commits/main", token)
    actual_sha = data["sha"]
    message = data["commit"]["message"].splitlines()[0]
    if actual_sha.startswith(expected_sha):
        print(f"✔ main head matches expected commit ({actual_sha[:7]}: {message})")
    else:
        raise SystemExit(
            f"✖ main head {actual_sha[:7]} does not match expected {expected_sha[:7]}"
        )


def verify_path(owner: str, repo: str, path: str, token: str | None) -> None:
    github_request(f"/repos/{owner}/{repo}/contents/{path}", token)
    print(f"✔ found {path} in repository")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check GitHub import status.")
    parser.add_argument("--owner", required=True, help="GitHub username or org")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--commit", required=True, help="Expected commit SHA or prefix")
    parser.add_argument("--path", required=True, help="Repository path to verify")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    verify_commit(args.owner, args.repo, args.commit, token)
    verify_path(args.owner, args.repo, args.path, token)
    print("All checks passed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
