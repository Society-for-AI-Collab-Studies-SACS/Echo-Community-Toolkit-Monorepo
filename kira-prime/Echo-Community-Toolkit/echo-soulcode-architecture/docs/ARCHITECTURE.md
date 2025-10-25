# Architecture

- Hilbert model: Ψ = α|squirrel⟩ + β|fox⟩ + γ|paradox⟩, with normalization |α|²+|β|²+|γ|²=1.
- Modules:
  - `hilbert.py`: normalization, phase/metrics.
  - `soulcode.py`: `generate_soulcode` builder (pure functional).
  - `live_read.py`: CLI to emit three canonical anchor states (Squirrel, Fox, Paradox).
  - `schema.json`: JSON Schema for validation.
  - `validate.py`: CLI validator (jsonschema).


- Operators: `operators.py` defines the canonical Echo operator H_ECHO and expectation ⟨ψ|H|ψ⟩.
- Complex phases: `live_read.py` supports --alpha-phase/--beta-phase/--gamma-phase and records complex amplitudes.
