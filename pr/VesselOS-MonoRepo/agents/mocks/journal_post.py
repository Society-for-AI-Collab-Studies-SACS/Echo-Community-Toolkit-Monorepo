#!/usr/bin/env python3
"""CLI helper to post a single entry to the Journal service."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

import requests


def _parse_features(raw: str | None) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    print("Invalid --features JSON; using {}", file=sys.stderr)
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a journal entry over HTTP.")
    parser.add_argument(
        "--url",
        default=os.getenv("JOURNAL_URL", "http://localhost:8082"),
        help="Journal base URL (default: http://localhost:8082)",
    )
    parser.add_argument("--content", required=True, help="Journal text content")
    parser.add_argument(
        "--tags",
        default="",
        help="Comma-separated tags (e.g., insight,gate)",
    )
    parser.add_argument("--narrator", default=None, help="Narrator label (e.g., Kira)")
    parser.add_argument("--event-type", default=None, help="Event type (e.g., narrative)")
    parser.add_argument("--sigprint", default=None, help="Optional 20-digit marker")
    parser.add_argument(
        "--features",
        default=None,
        help="JSON string for arbitrary structured metadata",
    )

    args = parser.parse_args()

    tags: List[str] = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    features = _parse_features(args.features)

    payload = {
        "content": args.content,
        "tags": tags,
        "narrator": args.narrator,
        "event_type": args.event_type,
        "sigprint": args.sigprint,
        "features": features,
    }

    response = requests.post(
        f"{args.url.rstrip('/')}/entry",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
