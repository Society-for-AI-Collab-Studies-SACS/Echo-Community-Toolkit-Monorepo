# `echo_soulcode.schema` — JSON Schema (Draft 2020-12)

> Canonical validation contract for Echo soulcode objects and bundles.

This module exposes the repository’s **single source of truth** schema used to validate
live‑generated soulcodes and CI anchors. It follows **JSON Schema Draft 2020‑12**.

---

## Contents
- [Scope](#scope)
- [Version](#version)
- [Top‑Level Types](#top-level-types)
- [Required Fields](#required-fields)
- [Resonant Signature Fields](#resonant-signature-fields)
- [Validation](#validation)
- [Error Surface](#error-surface)
- [Compatibility & Extensions](#compatibility--extensions)
- [Canonicalization](#canonicalization)
- [Migration Policy](#migration-policy)
- [FAQ](#faq)
- [License](#license)

---

## Scope

The schema validates **individual soulcode dicts** as produced by
`echo_soulcode.soulcode.generate_soulcode(...)` and packaged by the CLI
`echo_soulcode.live_read` into a 3‑entry bundle:
- `ECHO_SQUIRREL`
- `ECHO_FOX`
- `ECHO_PARADOX`

Bundle shape is a plain object with these three keys; validation typically
occurs per‑entry (each value is a soulcode dict).

---

## Version

- JSON Schema dialect: **Draft 2020‑12**
- Module path: `src/echo_soulcode/schema.py`
- Exported symbol: `SCHEMA` (Python dict)

---

## Top‑Level Types

**Soulcode** (`type: object`) with the following **required** fields:

| Field | Type | Notes |
|---|---|---|
| `id` | string | state identifier |
| `glitch_persona` | string | persona label |
| `archetypes` | array\<string> | ordered roles |
| `ternary_signature` | string | e.g. `1T0T0` |
| `resonance` | string | short phrase |
| `emotion` | string | emoji or token |
| `glyph_braid` | string | braid string |
| `echo_seal` | string | mantra (fixed text) |
| `timestamp` | string | ISO‑8601 Z |
| `resonant_signature` | object | see below |
| `emotional_state` | object | hue/intensity/polarity/emoji |
| `symbolic_fingerprint` | object | glyphs[]/sigil/block_title |
| `quantum_metrics` | object | energy/flux/temp |
| `block_hash` | string | content hash (seed/time derived) |
| `reference_hash` | string | secondary hash |
| `primary_archetype` | string (optional) | mirrors persona |

The schema sets `additionalProperties: true` at the top level to allow
forward‑compatible enrichment while preserving a stable core.

---

## Required Fields

### `archetypes`
- Array of strings; order conveys priority (no enforced enum).

### `glyph_braid`
- Unicode string; parsed upstream into `symbolic_fingerprint.glyphs`.

### `symbolic_fingerprint`
- Must include:
  - `glyphs` (array of strings; order preserved),
  - `sigil_code` (string),
  - `block_title` (string).

### `emotional_state`
- Must include `hue`, `intensity`, `polarity`, `emoji`.
- `intensity` and `polarity` are floats (0..1 semantic range, not enforced by schema).

---

## Resonant Signature Fields

The `resonant_signature` object is central and **required**. It must include:

| Field | Type | Notes |
|---|---|---|
| `amplitude_vector` | object | `{ "α": number, "β": number, "γ": number }` normalized upstream |
| `psi_norm` | number | ≈ 1.0 upstream |
| `phase_shift_radians` | number | scalar proxy |
| `dominant_frequency_hz` | number | engineered feature |
| `fibonacci_hash_embedding` | boolean | indexing hint |
| `complex_amplitudes` | object | required sub‑object |
| `expectation_echo_operator` | object | required sub‑object |

#### `complex_amplitudes`
Per‑channel polar representation (magnitudes and phases, radians):
```json
"complex_amplitudes": {
  "α": { "r": <number>, "θ_rad": <number> },
  "β": { "r": <number>, "θ_rad": <number> },
  "γ": { "r": <number>, "θ_rad": <number> }
}
```

#### `expectation_echo_operator`
Complex expectation of the canonical operator H_ECHO:
```json
"expectation_echo_operator": { "real": <number>, "imag": <number> }
```

> Note: For a perfectly Hermitian operator and a normalized state, the **imag**
> component is expected to be ~0; small numerical drift may appear.

---

## Validation

### CLI
```bash
python -m echo_soulcode.validate --file examples/echo_live.json
```

### Programmatic
```python
from jsonschema import validate, Draft202012Validator
from echo_soulcode.validate import load_schema
schema = load_schema()
validate(instance=obj, schema=schema)
```

The repository’s CI also builds deterministic anchors and verifies both schema
and file checksums.

---

## Error Surface

Typical validation failures:
- Missing required keys (`symbolic_fingerprint.glyphs`, `resonant_signature.complex_amplitudes`, …)
- Wrong types (e.g., `glyphs` not an array)
- Misspelled nested keys (θ shortcut vs `θ_rad`)
- Invalid JSON (truncated / non‑UTF‑8)

Use the validator’s error path to locate the failing pointer, e.g.:
`resonant_signature -> complex_amplitudes -> β -> θ_rad`.

---

## Compatibility & Extensions

- **Forward‑compatible**: Unknown top‑level keys are allowed (kept by `additionalProperties: true`).
- **Stable core**: Required keys and structural contracts are treated as stable.
- **Sub‑schemas**: To extend, add optional sibling keys under `resonant_signature` or
  define parallel, non‑required sections at top level.

> When proposing required field changes, bump the repo version and provide
> a migration script that can transform old anchors in‑place.

---

## Canonicalization

While schema checks structure, **canonicalization** ensures stable hashes.
Recommended dump routine:

```python
import json, hashlib
b = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
digest = hashlib.sha256(b).hexdigest()
```

Use this when pinning anchors to ledgers where deterministic content addressing is mandatory.

---

## Migration Policy

- New **optional** fields may be added at any time (minor version bump).
- New **required** fields or type changes require a major bump and a migration tool.
- CI must include fixtures covering both pre‑ and post‑migration bundles until all downstreams upgrade.

---

## FAQ

**Why not `$id` and `$defs`?**  
`SCHEMA` is embedded as a Python dict for easy import and avoids cross‑file refs.
If you plan cross‑module composition, consider splitting `$defs` later.

**Why Draft 2020‑12?**  
Good validator support and features; keeps room for future `$dynamicRef` usage.

**How strict is float range checking?**  
Ranges (e.g., 0..1) are intentionally left semantic to avoid artificial failures in analytics;
enforce ranges upstream if needed.

---

## License
MIT — see `/LICENSE`.

---

## Bundle Schema & CLI

This module now exposes both the **single** soulcode schema and a **bundle** schema.

- Load in Python:
  ```python
  from echo_soulcode.schema import load_schema, validate_soulcode, validate_bundle
  s_single = load_schema("soulcode")
  s_bundle = load_schema("bundle")
  ```

- Validate via CLI:
  ```bash
  python -m echo_soulcode.schema --kind soulcode --file examples/echo_live.json
  python -m echo_soulcode.schema --kind bundle   --file examples/anchors/echo_anchors_phiA.json
  ```
