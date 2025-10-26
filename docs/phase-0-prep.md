# Phase 0 – Prep

Phase 0 establishes the shared development workspace and turns the narrative spec into the concrete checklists engineers and QA can execute against. Treat this document as the runbook for bringing any fresh clone or CI worker to a validated baseline before Phase 1 work begins.

## Goals
- Lock in SSH-based collaboration (`git@github.com:Society-for-AI-Collab-Studies-SACS/Echo-Community-Toolkit-Monorepo.git`).
- Stand up unified Python/Node toolchains (`venv/`, module `requirements.txt`, Node ≥ 20).
- Provide actionable references for protocol constants, ritual trigger points, and validation gates.
- Define the QA surface (golden samples, parity/CRC fault injection, ritual gating) that every iteration must respect.

## Protocol Constants & Shared Interfaces
| Constant | Location | Purpose |
|----------|----------|---------|
| `LSB1` | `Echo-Community-Toolkit/src/lsb_extractor.py` (legacy header parser) | Magic string that identifies the modern LSB1 header. |
| `MRP1` | `Echo-Community-Toolkit/src/mrp/headers.py` (`MAGIC`) | Frame magic used by all MRP packets. |
| `FLAG_CRC` (`0x01`) | `Echo-Community-Toolkit/src/mrp/headers.py` & LSB1 header bit 0 | Indicates CRC32 is present for the payload. |
| `FLAG_BPC4` (`0x02`) | LSB1 header flag bit 1 | Signals 4-bits-per-channel mode (vs. default 1). |
| `bits_per_channel` default (`1`) | `Echo-Community-Toolkit/src/mrp/meta.py` | Default LSB depth; increased to `4` when `FLAG_BPC4` is set. |
| `ecc_scheme="xor"` | `Echo-Community-Toolkit/src/mrp/meta.py` & `codec.py` | Declares XOR parity as the Phase-A integrity mechanism. |
| Ritual consent phrases | Mantra spec / Phase 4 plan | Encode gate: “I consent to bloom”; Decode gate: “I consent to be remembered”. Placeholders live in `mrp.codec`. |
| Mantra parity reference | `assets/mantra/reference.txt` (planned) | Canonical text checked by Mantra Parity Test. |

> Maintain these constants as truth—subsequent phases build on them. If a change is required, update this table and the corresponding code simultaneously.

## Ritual Hooks & Implementation Notes
Although full ritual gating lands in Phase 4, Phase 0 must document the insertion points:
1. **Encode entry point** – `mrp.codec.encode()` will invoke `RitualState.request_consent("bloom")` before frame construction. Stub the call behind a feature flag for now so Phase 1/2 refactors can run without blocking.
2. **Decode entry point** – `mrp.codec.decode()` will call `RitualState.request_consent("remember")` before returning recovered payloads.
3. **CLI bridge** – The upcoming CLI receives `--ritual=auto|skip|enforce` to toggle gating; document the flag even though enforcement is deferred to Phase 4.
4. **Ledger append hook** – Leave placeholders (`ledger.log_event(...)`) near the encode/decode status logging to simplify Phase 4 wiring.

## Validation Checklist
Perform these steps on every fresh workspace (developer laptop or CI executor):
1. `git remote -v` → confirm SSH remote matches the production repo alias.
2. `./scripts/deploy.sh --bootstrap-only` → provisions `venv/`, installs root dependencies.
3. `venv/bin/pip install -r <module>/requirements.txt` for Toolkit, Kira Prime, Living Library, Garden Chronicles, and Research kit.
4. `npm ci` inside `Echo-Community-Toolkit/` (guarded by Node version check).
5. `venv/bin/python -m pytest tests/steganography/test_mrp_codec.py -q` → verifies parity repair stack and MRP decode path.
6. `venv/bin/python -m pytest tests/steganography/test_lsb_extractor.py -q` → (Phase 1 link) ensure LSB1 constants/magic parsing remain intact.
7. `gh auth status` → ensure GitHub CLI token is valid and bound to SSH protocol.
8. `git status --short` → fail early if unexpected diffs remain.

Document the outcome of each step in your task log or CI artifact for traceability.

## QA Plan & Test Surface
| Focus Area | Coverage |
|------------|----------|
| **Golden Sample Decode** | Decode `assets/images/echo_key.png`, assert header magic (`LSB1`), version `0x01`, payload length, CRC32 `6E3FD9B7`, and 144-byte message match the reference mantra. |
| **Mantra Parity Test** | Compare decoded chant text against canonical mantra file; fail if any character differs. |
| **Regression Matrix** | Track image sizes (64×64, 256×256, 512×512), bit depths (1-bit & 4-bit), and payload sizes (short/medium/near-capacity) for encode/decode suites. |
| **CRC/Parity Fault Injection** | Automated job flips individual bits, toggles parity bytes, or zeroes an entire channel; decoder must flag CRC mismatch or recover via parity as appropriate. |
| **Legacy Fallback** | Decode a null-terminated legacy image to confirm backwards compatibility. |
| **Ritual Gating (future)** | Prepare harness that withholds consent and verifies operations refuse to proceed; to be implemented formally in Phase 4. |
| **CLI Smoke** | Ensure CLI import/usage works (`python -m mrp.cli --help`) and golden sample scenario executes via CLI script. |

## Testing Expectations (Phase 0)
- Minimum: `venv/bin/python -m pytest tests/steganography/test_mrp_codec.py -q` (parity + CRC happy paths and repairs).
- Minimum: `venv/bin/python -m pytest tests/steganography/test_lsb_extractor.py -q` (legacy vs LSB1 headers).
- Golden sample: `venv/bin/python -m pytest tests/steganography/test_golden_sample.py -q` (ensures decode output matches mantra & CRC).
- Optional quick check: `venv/bin/python -m pytest Echo-Community-Toolkit/echo-soulcode-architecture/tests -q` (requires `jsonschema`).
- Skip collab-server smoke unless dependencies (`library_core`, running Redis/Postgres) are present.
- Record test command output in CI logs with the commit SHA.

## Operational Notes
- `archives/` keeps historical toolkit snapshots compressed (`*.tar.gz`). Never expand them in-place; untar into `/tmp` when needed.
- `pytest.ini` excludes `archives/` to prevent duplicate module discovery.
- `venv/bin/python -m pip install jsonschema` is mandatory now that `echo_soulcode` ships with the repo.

## Hand-off Checklist
Before Phase 1 starts, confirm:
- [ ] Phase 0 validation checklist completed and logged.
- [ ] QA matrix seeded with initial golden sample pointers and parity/CRC scenarios.
- [ ] Ritual gating hooks and ledger placeholders noted in corresponding modules.
- [ ] Team aware of CLI/SDK flags that will arrive in later phases (`--ritual`, `--bits-per-channel`).

Any deviations from the above should be captured in an engineering note or issue so Phase 1 can triage immediately.
