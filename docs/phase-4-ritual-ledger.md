# Phase 4 – Ritual & Ledger

## Objectives
- Implement `RitualState` to manage the six-invocation mantra and consent gates.
- Enforce ritual gating on encode/decode operations.
- Persist ledger entries for every authorised action.

## Scope & Deliverables
1. **RitualState Engine**
   - Implement `mrp/ritual/state.py` with:
     - Enum `RitualStep` (α, β, γ, bloom, remember, close) mapped to mantra lines.
     - `RitualState` dataclass capturing current step, timestamps, consent flags, automation mode.
     - Methods: `advance(step)`, `consent(action)`, `reset()`, `is_ready_for(operation)`.
   - Support configuration (env/CLI) for auto consent (CI), interactive prompts, or enforced manual acknowledgement.
   - Record metrics (e.g., `state.metrics.consent_attempts`, `denials`).
2. **Gating Integration**
   - Wrap `encode_mrp` and `decode_mrp` (and legacy encode/decode) with gating middleware:
     - `encode`: require `RitualState.consent("bloom")`.
     - `decode`: require `RitualState.consent("remember")`.
   - Provide context manager `with ritual.guard("bloom"):` to make usage explicit.
   - Add CLI options:
     - `--ritual enforce|auto|skip` (default `enforce` for humans, `auto` for CI, `skip` only available in test harness).
     - `--ritual-script file` to pre-supply consent tokens.
   - Surface error `RitualGateError` with message referencing missing consent and instructions.
   - Ensure API/SDK functions accept `ritual_state` parameter for advanced integrations.
3. **Ledger Logging**
   - Create `mrp/ledger/logger.py` using JSON lines or `JsonStateStore`.
   - Define ledger entry schema: system timestamp, operation (`encode`/`decode`), glyph ID (hash/UUID), mantra step snapshot, file paths, metadata hash, integrity status.
   - Ensure atomic append (use file locking on POSIX) and guard against duplicate entries (same glyph/time).
   - Provide CLI command `ledger list`, `ledger inspect <id>` for audits.
   - Add retention/rotation plan (e.g., archive after N entries).
4. **User Experience & Prompts**
   - CLI interactive flow:
     - Display mantra line and require explicit confirmation (y/N) or typed phrase.
     - Optionally display ASCII art per step (squirrel, fox, infinity).
   - Provide TUI/curses variant (stretch) for immersive experience.
   - Log summary after operation showing ledger entry ID, ritual coherence.
5. **Testing**
   - Unit tests:
     - RitualState step sequencing, duplicate consent, timeout logic.
     - Gating functions (encode/decode fail without consent).
     - Ledger write/read, duplicate prevention.
   - CLI tests:
     - Simulate interactive input (using `pexpect`) verifying prompts and ledger entries.
     - Automation mode works (CI friendly).
   - Integration tests combining encode/decode with ledger and integrity checks.
6. **Documentation**
   - Update docs with full mantra text, mapping of steps to operations.
   - Provide configuration examples (YAML or env) for ritual settings.
   - Document ledger format, rotation policy, and compliance considerations.

## Exit Criteria
- Encode/decode blocked without proper consent, with tests proving enforcement.
- Ledger entries created for every successful operation.
- CLI/SDK documentation updated with ritual usage and override options.
