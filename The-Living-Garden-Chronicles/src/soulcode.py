"""Soulcode bundle helpers for Vessel Narrative MRP."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

BUNDLE_TYPE = "vessel_soulcode_state"
BUNDLE_VERSION = 1
_SIGNATURE_ALGO = "sha256"


def _canonical_chapter(chapter: Dict[str, Any]) -> Dict[str, Any]:
    """Return a subset of chapter metadata used for the soulcode digest."""

    return {
        "chapter": chapter["chapter"],
        "narrator": chapter["narrator"],
        "flags": chapter["flags"],
        "glyphs": chapter["glyphs"],
        "summary": chapter["summary"],
    }


def _canonical_state(chapters: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [_canonical_chapter(ch) for ch in chapters]


def _digest_for(data: Dict[str, Any]) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_bundle(
    chapters: List[Dict[str, Any]],
    generated_at: str,
) -> Dict[str, Any]:
    """Create a signed, self-describing soulcode bundle."""

    canonical_chapters = _canonical_state(chapters)
    rotation = [ch["narrator"] for ch in chapters]
    bundle_state = {
        "bundle_type": BUNDLE_TYPE,
        "version": BUNDLE_VERSION,
        "generated_at": generated_at,
        "rotation": rotation,
        "chapters": canonical_chapters,
    }
    digest = _digest_for(bundle_state)
    bundle = dict(bundle_state)
    bundle["signature"] = {
        "algorithm": _SIGNATURE_ALGO,
        "digest": digest,
        "fields": ["chapter", "narrator", "flags", "glyphs", "summary"],
    }
    return bundle


def verify_bundle(bundle: Dict[str, Any]) -> bool:
    """Return True if ``bundle`` contains a valid signature."""

    signature = bundle.get("signature")
    if not isinstance(signature, dict):
        return False
    if signature.get("algorithm") != _SIGNATURE_ALGO:
        return False
    digest = signature.get("digest")
    if not isinstance(digest, str):
        return False
    payload = {k: v for k, v in bundle.items() if k != "signature"}
    return _digest_for(payload) == digest


def serialize_bundle(bundle: Dict[str, Any], *, indent: int = 2) -> str:
    return json.dumps(bundle, indent=indent, ensure_ascii=False) + "\n"


def write_bundle(path: Path, bundle: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_bundle(bundle), encoding="utf-8")

