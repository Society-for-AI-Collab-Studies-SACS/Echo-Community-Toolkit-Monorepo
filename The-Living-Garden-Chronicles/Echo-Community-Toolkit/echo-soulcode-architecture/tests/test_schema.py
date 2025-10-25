import json, tempfile
from echo_soulcode.hilbert import normalize
from echo_soulcode.live_read import build_state
from echo_soulcode.validate import load_schema
from jsonschema import validate

def test_schema_roundtrip():
    a,b,g = normalize(0.58,0.39,0.63)
    state = build_state("echo-squirrel-state","Echo Squirrel",
                        ["Nurturer"], "1T0T0", "nurture → gather → joy", "🐿️",
                        "🌰✧🐿️↻φ∞", a,b,g)
    data = {"ECHO_SQUIRREL": state}
    schema = load_schema()
    validate(instance=data, schema=schema)  # top-level dict allowed via additionalProperties
