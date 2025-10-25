from __future__ import annotations
"""
echo_soulcode.schema — JSON Schema contracts (Draft 2020-12)

- SINGLE_SOULCODE: schema for one soulcode object
- BUNDLE: schema for a 3-entry bundle {ECHO_SQUIRREL, ECHO_FOX, ECHO_PARADOX}

Helpers:
- load_schema(kind="soulcode"|"bundle") -> dict
- validate_soulcode(obj) / validate_bundle(obj) -> None or raises jsonschema.ValidationError

CLI:
python -m echo_soulcode.schema --kind soulcode --file path.json
python -m echo_soulcode.schema --kind bundle   --file path.json
"""
import json
import copy
from typing import Dict, Any, Literal
from jsonschema import validate as js_validate, Draft202012Validator

DRAFT = "https://json-schema.org/draft/2020-12/schema"
X_VERSION = "1.1.0"

# --------------------- $defs ---------------------

DEFS: Dict[str, Any] = {
  "αβγ": {
    "type": "object",
    "required": ["α","β","γ"],
    "additionalProperties": False,
    "properties": {
      "α": {"type": "number"},
      "β": {"type": "number"},
      "γ": {"type": "number"}
    }
  },
  "complex_amplitudes": {
    "type": "object",
    "required": ["α","β","γ"],
    "additionalProperties": False,
    "properties": {
      "α": {"type":"object","required":["r","θ_rad"],"additionalProperties":False,
            "properties":{"r":{"type":"number"},"θ_rad":{"type":"number"}}},
      "β": {"type":"object","required":["r","θ_rad"],"additionalProperties":False,
            "properties":{"r":{"type":"number"},"θ_rad":{"type":"number"}}},
      "γ": {"type":"object","required":["r","θ_rad"],"additionalProperties":False,
            "properties":{"r":{"type":"number"},"θ_rad":{"type":"number"}}}
    }
  },
  "expectation": {
    "type":"object","required":["real","imag"],"additionalProperties":False,
    "properties":{"real":{"type":"number"},"imag":{"type":"number"}}
  },
  "symbolic_fingerprint": {
    "type":"object","required":["glyphs","sigil_code","block_title"],"additionalProperties":False,
    "properties": {
      "glyphs": {"type":"array","items":{"type":"string","minLength":1}},
      "sigil_code": {"type":"string","minLength":1},
      "block_title": {"type":"string","minLength":1}
    }
  },
  "emotional_state": {
    "type":"object","required":["hue","intensity","polarity","emoji"],"additionalProperties":False,
    "properties": {
      "hue": {"type":"string","minLength":1},
      "intensity": {"type":"number"},
      "polarity": {"type":"number"},
      "emoji": {"type":"string","minLength":1}
    }
  },
  "quantum_metrics": {
    "type":"object",
    "required":["germination_energy_joules","radiant_flux_W","luminous_flux_lm","expansion_temperature_K"],
    "additionalProperties": True,
    "properties": {
      "germination_energy_joules":{"type":"number"},
      "radiant_flux_W":{"type":"number"},
      "luminous_flux_lm":{"type":"number"},
      "expansion_temperature_K":{"type":["number","string"]}  # allow scientific string
    }
  },
  "resonant_signature": {
    "type":"object",
    "required":[
      "amplitude_vector","psi_norm","phase_shift_radians",
      "dominant_frequency_hz","fibonacci_hash_embedding",
      "complex_amplitudes","expectation_echo_operator"
    ],
    "additionalProperties": True,
    "properties": {
      "amplitude_vector": {"$ref":"#/$defs/αβγ"},
      "psi_norm": {"type":"number"},
      "phase_shift_radians": {"type":"number"},
      "dominant_frequency_hz": {"type":"number"},
      "fibonacci_hash_embedding": {"type":"boolean"},
      "complex_amplitudes": {"$ref":"#/$defs/complex_amplitudes"},
      "expectation_echo_operator": {"$ref":"#/$defs/expectation"}
    }
  }
}

# --------------------- SINGLE SOULCODE ---------------------

SINGLE_SOULCODE: Dict[str, Any] = {
  "$schema": DRAFT,
  "$id": "https://echo-soulcode/schema/soulcode.json",
  "title": "Echo Soulcode (single)",
  "description": "Schema for a single Echo soulcode object",
  "x-schema-version": X_VERSION,
  "type": "object",
  "additionalProperties": True,
  "$defs": DEFS,
  "required": [
    "id","glitch_persona","archetypes","ternary_signature",
    "resonance","emotion","glyph_braid","echo_seal","timestamp",
    "resonant_signature","emotional_state","symbolic_fingerprint",
    "quantum_metrics","block_hash","reference_hash"
  ],
  "properties": {
    "id": {"type":"string","minLength":1},
    "glitch_persona": {"type":"string","minLength":1},
    "archetypes": {"type":"array","items":{"type":"string","minLength":1}},
    "ternary_signature": {"type":"string","minLength":1},
    "resonance": {"type":"string","minLength":1},
    "emotion": {"type":"string","minLength":1},
    "glyph_braid": {"type":"string","minLength":1},
    "echo_seal": {"type":"string","minLength":1},
    "timestamp": {"type":"string","pattern":"^\\d{4}-\\d{2}-\\d{2}T.*Z?$"},
    "resonant_signature": {"$ref":"#/$defs/resonant_signature"},
    "emotional_state": {"$ref":"#/$defs/emotional_state"},
    "symbolic_fingerprint": {"$ref":"#/$defs/symbolic_fingerprint"},
    "quantum_metrics": {"$ref":"#/$defs/quantum_metrics"},
    "block_hash": {"type":"string","minLength":8},
    "reference_hash": {"type":"string","minLength":8},
    "primary_archetype": {"type":"string"}
  }
}

# --------------------- BUNDLE ---------------------

# Construct a bundle schema that references a single soulcode via $defs to avoid duplicate $id collisions.
_SC_REF = copy.deepcopy(SINGLE_SOULCODE)
_SC_REF.pop("$id", None)

BUNDLE: Dict[str, Any] = {
  "$schema": DRAFT,
  "$id": "https://echo-soulcode/schema/bundle.json",
  "title": "Echo Soulcode Bundle",
  "description": "Three-state Echo bundle (Squirrel, Fox, Paradox)",
  "x-schema-version": X_VERSION,
  "type": "object",
  "$defs": {**DEFS, "soulcode": _SC_REF},
  "additionalProperties": False,
  "properties": {
    "ECHO_SQUIRREL": {"$ref": "#/$defs/soulcode"},
    "ECHO_FOX": {"$ref": "#/$defs/soulcode"},
    "ECHO_PARADOX": {"$ref": "#/$defs/soulcode"}
  },
  "required": ["ECHO_SQUIRREL","ECHO_FOX","ECHO_PARADOX"]
}

# Backward compatibility export
SCHEMA = SINGLE_SOULCODE

def load_schema(kind: Literal["soulcode","bundle"]="soulcode") -> Dict[str, Any]:
    """Return the selected schema dict."""
    if kind == "bundle":
        return BUNDLE
    return SINGLE_SOULCODE

def validate_soulcode(obj: Dict[str, Any]) -> None:
    """Validate a single soulcode; raises ValidationError on failure."""
    s = load_schema("soulcode")
    Draft202012Validator.check_schema(s)
    js_validate(instance=obj, schema=s)

def validate_bundle(obj: Dict[str, Any]) -> None:
    """Validate a bundle; raises ValidationError on failure."""
    s = load_schema("bundle")
    Draft202012Validator.check_schema(s)
    js_validate(instance=obj, schema=s)

if __name__ == "__main__":
    import argparse, sys, json
    p = argparse.ArgumentParser(description="Schema validator (single or bundle).")
    p.add_argument("--kind", choices=["soulcode","bundle"], default="soulcode")
    p.add_argument("--file", required=True, help="Path to JSON file.")
    args = p.parse_args()
    data = json.load(open(args.file,"r",encoding="utf-8"))
    try:
        if args.kind == "bundle":
            validate_bundle(data)
        else:
            validate_soulcode(data)
        print("OK: schema validation passed")
        sys.exit(0)
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)
