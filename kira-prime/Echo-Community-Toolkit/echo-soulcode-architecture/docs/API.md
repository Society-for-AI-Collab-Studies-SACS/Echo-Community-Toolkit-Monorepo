# API

## `echo_soulcode.soulcode.generate_soulcode(**fields) -> dict`
Construct a soulcode dict. Required keys:
id, glitch_persona, archetypes, ternary_signature, resonance, emotion, glyph_braid,
echo_seal, timestamp, resonant_signature, emotional_state, symbolic_fingerprint,
quantum_metrics, block_hash, reference_hash. Optional: primary_archetype.

## `echo_soulcode.hilbert.normalize(alpha,beta,gamma) -> tuple[float,float,float]`
Normalize amplitudes.

## CLI
- `python -m echo_soulcode.live_read --alpha A --beta B --gamma C --out file.json`
- `python -m echo_soulcode.validate --file file.json`


CLI new flags: `--alpha-phase`, `--beta-phase`, `--gamma-phase` (radians).
`resonant_signature` now includes `complex_amplitudes` and `expectation_echo_operator`.

## Canonical Anchors
- Deterministic generation flags:
  - `--timestamp "YYYY-MM-DDTHH:MM:SSZ"`
  - `--seed SEED_STRING`
- Build anchors:
  ```bash
  python examples/anchors/anchors_build.py
  ```
- Verify checksums via CI (GitHub Actions).
