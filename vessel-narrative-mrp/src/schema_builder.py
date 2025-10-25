#!/usr/bin/env python3
"""
Builds narrative_schema.json (and optionally YAML) describing the metadata structure.
No third-party libs required; YAML is emitted only if PyYAML is available.
"""
from __future__ import annotations

import json
from pathlib import Path


def build_schema() -> dict:
    chapter_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "chapter",
            "narrator",
            "flags",
            "glyphs",
            "file",
            "summary",
            "timestamp",
            "provenance",
        ],
        "properties": {
            "chapter": {"type": "integer", "minimum": 1, "maximum": 20},
            "narrator": {"type": "string", "enum": ["Limnus", "Garden", "Kira"]},
            "flags": {
                "type": "object",
                "additionalProperties": False,
                "required": ["R", "G", "B"],
                "properties": {
                    "R": {"type": "string", "enum": ["active", "latent"]},
                    "G": {"type": "string", "enum": ["active", "latent"]},
                    "B": {"type": "string", "enum": ["active", "latent"]},
                },
            },
            "glyphs": {"type": "array", "items": {"type": "string"}},
            "file": {"type": "string"},
            "summary": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "stego_png": {"type": "string"},
            "provenance": {
                "type": "object",
                "additionalProperties": False,
                "required": ["scroll", "label", "paragraph_index", "excerpt", "glyph_refs"],
                "properties": {
                    "scroll": {"type": "string"},
                    "label": {"type": "string"},
                    "paragraph_index": {"type": "integer", "minimum": 0},
                    "excerpt": {"type": "string"},
                    "glyph_refs": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                },
            },
        },
    }

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.com/vessel/narrative_schema.json",
        "title": "Vessel Narrative",
        "type": "object",
        "additionalProperties": False,
        "required": ["chapters"],
        "properties": {
            "chapters": {
                "type": "array",
                "minItems": 20,
                "maxItems": 20,
                "items": {"$ref": "#/$defs/chapter"},
            }
        },
        "$defs": {
            "chapter": chapter_schema,
        },
    }
    return schema


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_yaml(path: Path, data: dict) -> bool:
    try:
        import yaml  # type: ignore
    except Exception:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    return True


def main() -> None:
    schema = build_schema()
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "schema"
    write_json(out_dir / "narrative_schema.json", schema)
    wrote_yaml = write_yaml(out_dir / "narrative_schema.yaml", schema)
    print("Wrote:", out_dir / "narrative_schema.json")
    if wrote_yaml:
        print("Wrote:", out_dir / "narrative_schema.yaml")
    else:
        print("(YAML not written; install PyYAML to enable)")


if __name__ == "__main__":
    main()
