#!/usr/bin/env python3
"""
Validates the generated metadata and files:
- Schema presence and basic field/type checks
- Structural rotation rules and counts
- File existence in frontend/
- Flag consistency between metadata and HTML files
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from stego import (
        decode_chapter_payload,
        extract_flags as stego_extract_flags,
        is_available as stego_is_available,
    )
except Exception:  # pragma: no cover - fallback when Pillow missing
    decode_chapter_payload = None  # type: ignore[assignment]
    stego_extract_flags = None  # type: ignore[assignment]

    def stego_is_available() -> bool:  # type: ignore[return-value]
        return False

from soulcode import BUNDLE_TYPE, verify_bundle


FLAG_RE = re.compile(r"\[\s*Flags:\s*([^\]]+)\]", re.IGNORECASE)
SOULCODE_SCRIPT_RE = re.compile(r'<script id="soulcode-state"[^>]*>(.*?)</script>', re.DOTALL)


def load_metadata(root: Path) -> dict:
    meta_path = root / "schema" / "chapters_metadata.json"
    if not meta_path.exists():
        raise SystemExit(f"Missing metadata file: {meta_path}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def load_schema(root: Path) -> dict:
    schema_path = root / "schema" / "narrative_schema.json"
    if not schema_path.exists():
        raise SystemExit(f"Missing schema file: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def basic_validate_against_schema(meta: dict, schema: dict) -> List[str]:
    errors: List[str] = []
    if not isinstance(meta, dict):
        return ["Metadata root is not an object"]
    if "chapters" not in meta or not isinstance(meta["chapters"], list):
        errors.append("Metadata must contain a 'chapters' array")
        return errors

    chapters = meta["chapters"]
    if len(chapters) != 20:
        errors.append(f"Expected 20 chapters, found {len(chapters)}")

    # Pull chapter schema from $defs for simple checks
    chapter_schema = schema.get("$defs", {}).get("chapter", {})
    required = set(chapter_schema.get("required", []))
    prop_types = {k: v.get("type") for k, v in chapter_schema.get("properties", {}).items()}

    for idx, ch in enumerate(chapters, start=1):
        if not isinstance(ch, dict):
            errors.append(f"Chapter index {idx} is not an object")
            continue
        missing = required - set(ch.keys())
        if missing:
            errors.append(f"Chapter {ch.get('chapter', idx)} missing fields: {sorted(missing)}")
        # basic type checks
        for k, t in prop_types.items():
            if k in ch and t:
                if t == "integer" and not isinstance(ch[k], int):
                    errors.append(f"Chapter {ch.get('chapter', idx)} field '{k}' not integer")
                if t == "string" and not isinstance(ch[k], str):
                    errors.append(f"Chapter {ch.get('chapter', idx)} field '{k}' not string")
                if t == "array" and not isinstance(ch[k], list):
                    errors.append(f"Chapter {ch.get('chapter', idx)} field '{k}' not array")
                if t == "object" and not isinstance(ch[k], dict):
                    errors.append(f"Chapter {ch.get('chapter', idx)} field '{k}' not object")
    return errors


def check_rotation(chapters: List[dict]) -> List[str]:
    errors: List[str] = []
    voices = [ch.get("narrator") for ch in chapters]
    for a, b in zip(voices, voices[1:]):
        if a == b:
            errors.append("Narrator repetition detected (no back-to-back allowed)")
            break
    counts = Counter(voices)
    for name in ["Limnus", "Garden", "Kira"]:
        if counts[name] < 6:
            errors.append(f"Narrator {name} appears fewer than 6 times ({counts[name]})")
    return errors


def parse_flags_text(flags_text: str) -> Dict[str, str]:
    # Expect tokens like: "R active, G latent, B latent"
    parts = [p.strip() for p in flags_text.split(",")]
    out: Dict[str, str] = {}
    for part in parts:
        tokens = part.split()
        if len(tokens) == 2:
            out[tokens[0]] = tokens[1]
    return out


def extract_flags_from_html(path: Path) -> Optional[Dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = FLAG_RE.search(text)
    if not m:
        return None
    return parse_flags_text(m.group(1))


def check_files_and_flags(root: Path, chapters: List[dict]) -> List[str]:
    errors: List[str] = []
    for ch in chapters:
        ch_no = ch.get("chapter")
        rel = ch.get("file")
        flags_meta = ch.get("flags", {})
        if not isinstance(rel, str):
            errors.append(f"Chapter {ch_no}: 'file' not string")
            continue
        path = root / rel
        if not path.exists():
            errors.append(f"Chapter {ch_no}: missing file {rel}")
            continue
        flags_in_html = extract_flags_from_html(path)
        if not flags_in_html:
            errors.append(f"Chapter {ch_no}: Flags not found in HTML")
            continue
        # compare
        for k in ("R", "G", "B"):
            if flags_in_html.get(k) != flags_meta.get(k):
                errors.append(
                    f"Chapter {ch_no}: flag mismatch for {k} (meta={flags_meta.get(k)} html={flags_in_html.get(k)})"
                )
    return errors


def check_stego_payloads(root: Path, chapters: List[dict]) -> List[str]:
    errors: List[str] = []
    for ch in chapters:
        stego_rel = ch.get("stego_png")
        if not stego_rel:
            continue
        if not isinstance(stego_rel, str):
            errors.append(f"Chapter {ch.get('chapter')}: 'stego_png' must be a string")
            continue
        path = root / stego_rel
        if not path.exists():
            errors.append(f"Chapter {ch.get('chapter')}: stego PNG missing at {stego_rel}")
            continue
        if not stego_is_available() or decode_chapter_payload is None:
            # Pillow not available; skip deep validation but record advisory.
            continue
        try:
            payload = decode_chapter_payload(path).as_dict()
        except Exception as exc:
            errors.append(f"Chapter {ch.get('chapter')}: failed to decode stego PNG ({exc})")
            continue
        if stego_extract_flags is not None:
            try:
                decoded_flags = stego_extract_flags(path)
            except Exception as exc:
                errors.append(f"Chapter {ch.get('chapter')}: failed to extract flags from stego PNG ({exc})")
            else:
                for key in ("R", "G", "B"):
                    if decoded_flags.get(key) != ch.get("flags", {}).get(key):
                        errors.append(
                            f"Chapter {ch.get('chapter')}: stego flag mismatch for {key} "
                            f"(payload={decoded_flags.get(key)} metadata={ch.get('flags', {}).get(key)})"
                        )
        expected = {k: v for k, v in ch.items() if k != "stego_png"}
        if payload != expected:
            errors.append(
                f"Chapter {ch.get('chapter')}: stego payload mismatch compared to metadata"
            )
    return errors


def check_provenance(root: Path, chapters: List[dict]) -> List[str]:
    errors: List[str] = []
    for ch in chapters:
        ch_no = ch.get("chapter")
        provenance = ch.get("provenance")
        if not isinstance(provenance, dict):
            errors.append(f"Chapter {ch_no}: provenance missing or not an object")
            continue
        required_keys = {"scroll", "label", "paragraph_index", "excerpt", "glyph_refs"}
        missing = required_keys - provenance.keys()
        if missing:
            errors.append(f"Chapter {ch_no}: provenance missing keys {sorted(missing)}")
            continue
        scroll_rel = provenance.get("scroll")
        if isinstance(scroll_rel, str):
            scroll_path = root / scroll_rel
            if not scroll_path.exists():
                errors.append(
                    f"Chapter {ch_no}: provenance scroll not found at {scroll_rel}"
                )
        else:
            errors.append(f"Chapter {ch_no}: provenance scroll path is not a string")
        if not isinstance(provenance.get("label"), str) or not provenance["label"].strip():
            errors.append(f"Chapter {ch_no}: provenance label is empty")
        if not isinstance(provenance.get("excerpt"), str) or not provenance["excerpt"].strip():
            errors.append(f"Chapter {ch_no}: provenance excerpt is empty")
        paragraph_index = provenance.get("paragraph_index")
        if not isinstance(paragraph_index, int) or paragraph_index < 0:
            errors.append(f"Chapter {ch_no}: provenance paragraph_index invalid")
        glyph_refs = provenance.get("glyph_refs")
        if not isinstance(glyph_refs, list):
            errors.append(f"Chapter {ch_no}: provenance glyph_refs not a list")
        elif list(glyph_refs) != list(ch.get("glyphs", [])):
            errors.append(f"Chapter {ch_no}: provenance glyph_refs do not match glyphs")
    return errors


def check_soulcode_bundle(root: Path, chapters: List[dict]) -> Tuple[List[str], Optional[dict]]:
    bundle_path = root / "schema" / "soulcode_bundle.json"
    if not bundle_path.exists():
        return ([f"Missing soulcode bundle: {bundle_path}"], None)
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return ([f"Soulcode bundle is not valid JSON ({exc})"], None)

    errors: List[str] = []
    if bundle.get("bundle_type") != BUNDLE_TYPE:
        errors.append("Soulcode bundle type mismatch")
    if not verify_bundle(bundle):
        errors.append("Soulcode bundle signature failed verification")

    rotation = bundle.get("rotation")
    expected_rotation = [ch.get("narrator") for ch in chapters]
    if rotation != expected_rotation:
        errors.append("Soulcode bundle rotation does not match metadata ordering")

    bundle_chapters = bundle.get("chapters")
    if not isinstance(bundle_chapters, list) or len(bundle_chapters) != len(chapters):
        errors.append("Soulcode bundle chapter count mismatch")
        return errors, bundle

    for meta, entry in zip(chapters, bundle_chapters):
        for field in ("chapter", "narrator", "flags", "glyphs", "summary"):
            if meta.get(field) != entry.get(field):
                errors.append(
                    f"Soulcode bundle mismatch for chapter {meta.get('chapter')} field '{field}'"
                )
                break
    return errors, bundle


def check_landing_bundle(root: Path, bundle: Optional[dict]) -> List[str]:
    if bundle is None:
        return []
    index_path = root / "frontend" / "index.html"
    if not index_path.exists():
        return [f"Landing page missing at {index_path}"]
    html = index_path.read_text(encoding="utf-8", errors="ignore")
    match = SOULCODE_SCRIPT_RE.search(html)
    if not match:
        return ["Soulcode bundle script not embedded in frontend/index.html"]
    script_payload = match.group(1).strip()
    try:
        embedded = json.loads(script_payload)
    except json.JSONDecodeError as exc:
        return [f"Soulcode bundle embedded in index.html is invalid JSON ({exc})"]
    if embedded != bundle:
        return ["Soulcode bundle embedded in index.html does not match schema/soulcode_bundle.json"]
    return []


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    meta = load_metadata(root)
    schema = load_schema(root)
    schema_errors = basic_validate_against_schema(meta, schema)
    rotation_errors = check_rotation(meta.get("chapters", []))
    chapters = meta.get("chapters", [])
    files_flags_errors = check_files_and_flags(root, chapters)
    stego_errors = check_stego_payloads(root, chapters)
    provenance_errors = check_provenance(root, chapters)
    soulcode_errors, soulcode_bundle = check_soulcode_bundle(root, chapters)
    landing_errors = check_landing_bundle(root, soulcode_bundle)

    errors = (
        schema_errors
        + rotation_errors
        + files_flags_errors
        + stego_errors
        + provenance_errors
        + soulcode_errors
        + landing_errors
    )
    if errors:
        print("Validation FAILED:")
        for e in errors:
            print(" -", e)
        raise SystemExit(1)
    print(
        "Validation OK: 20 chapters, rotation clean, files present, flags consistent, stego payloads match."
    )


if __name__ == "__main__":
    main()
