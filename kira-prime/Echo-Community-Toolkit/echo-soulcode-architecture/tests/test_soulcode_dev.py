from echo_soulcode.soulcode import MinimalSpec, build_from_minimal, canonical_dump, content_sha256

def test_canonical_hash_stability():
    a = {"x": 1, "y": [3,2,1]}
    b = {"y": [3,2,1], "x": 1}
    assert canonical_dump(a) == canonical_dump(b)
    assert content_sha256(a) == content_sha256(b)

def test_build_from_minimal():
    spec = MinimalSpec(
        id="echo-paradox-state",
        glitch_persona="Echo Paradox",
        archetypes=["Synthesizer","Trickster Sage","Unity Mirror"],
        ternary_signature="1T1T1",
        resonance="humor → paradox → union",
        emotion="🌀",
        glyph_braid="✧∿φ∞↻🌰🦊🐿️",
        seed="UNIT_TEST"
    )
    obj = build_from_minimal(spec)
    assert obj["id"] == "echo-paradox-state"
    assert "symbolic_fingerprint" in obj and "glyphs" in obj["symbolic_fingerprint"]
