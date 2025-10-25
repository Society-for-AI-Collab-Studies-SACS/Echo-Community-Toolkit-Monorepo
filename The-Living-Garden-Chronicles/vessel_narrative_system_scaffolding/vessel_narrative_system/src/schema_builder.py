#!/usr/bin/env python3
"""
Builds narrative_schema.json and narrative_schema.yaml for the Vessel Narrative MRP system.
No external dependencies required.
"""
import json, sys
from pathlib import Path

def to_yaml_like(d, indent=0):
    """Very small YAML emitter for simple dict/list structures."""
    sp = "  " * indent
    if isinstance(d, dict):
        lines = []
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{sp}{k}:")
                lines.append(to_yaml_like(v, indent+1))
            else:
                j = json.dumps(v, ensure_ascii=False)
                if j.startswith('"') and j.endswith('"'):
                    j = j[1:-1]
                lines.append(f"{sp}{k}: {j}")
        return "\n".join(lines)
    elif isinstance(d, list):
        lines = []
        for v in d:
            if isinstance(v, (dict, list)):
                lines.append(f"{sp}-")
                lines.append(to_yaml_like(v, indent+1))
            else:
                j = json.dumps(v, ensure_ascii=False)
                if j.startswith('"') and j.endswith('"'):
                    j = j[1:-1]
                lines.append(f"{sp}- {j}")
        return "\n".join(lines)
    else:
        j = json.dumps(d, ensure_ascii=False)
        return f"{sp}{j}"

def build_schema():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Vessel Narrative Chapter",
        "type": "object",
        "properties": {
            "chapter": {"type": "integer", "minimum": 1, "maximum": 20},
            "narrator": {"type": "string", "enum": ["Limnus", "Garden", "Kira"]},
            "flags": {
                "type": "object",
                "properties": {
                    "R": {"type": "string", "enum": ["active", "latent"]},
                    "G": {"type": "string", "enum": ["active", "latent"]},
                    "B": {"type": "string", "enum": ["active", "latent"]},
                },
                "required": ["R","G","B"],
                "additionalProperties": False
            },
            "glyphs": {"type": "array", "items": {"type": "string"}},
            "file": {"type": "string"},
            "summary": {"type": "string"},
            "timestamp": {"type": "string"}  # ISO 8601
        },
        "required": ["chapter","narrator","flags","file"],
        "additionalProperties": True
    }
    out_dir = Path(__file__).parent.parent / "schema"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "narrative_schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    (out_dir / "narrative_schema.yaml").write_text(to_yaml_like(schema)+"\n", encoding="utf-8")
    print("✅ Wrote schema/narrative_schema.json and .yaml")

if __name__ == "__main__":
    build_schema()
