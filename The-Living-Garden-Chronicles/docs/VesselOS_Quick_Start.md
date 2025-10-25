# VesselOS Quick Start

Follow these steps to bring the Vessel narrative system online, run a complete garden → echo → limnus → kira cycle, and confirm the installation is healthy. The commands below assume you are inside the repository root (`The-Living-Garden-Chronicles/`).

---

## 1. Prerequisites

- **Python** ≥ 3.8 (used by the generators, validator, and stego helpers).
- **Node.js** ≥ 20 (required for the `codex` CLI).
- **Git** and **GitHub CLI (`gh`)** if you intend to use Kira’s sync/push/publish flow.
- Ensure submodules are initialised:
  ```bash
  git submodule update --init --recursive
  ```
- (Optional) Authenticate GitHub so Kira can access remotes:
  ```bash
  gh auth login
  ```

---

## 2. Generate Chapters & Metadata

The Python utilities emit the base schema, chapters, and metadata bundles.

```bash
python src/schema_builder.py
python src/generate_chapters.py
```

Outputs:
- `schema/narrative_schema.json|yaml`
- `schema/chapters_metadata.json|yaml`
- `frontend/chapter04.html` … `chapter20.html`

Re-run these whenever templates change.

---

## 3. Validate the Narrative Set

Run the validator to enforce narrator rotation, flag consistency, file presence, and steganographic parity (when assets exist):

```bash
python src/validator.py
```

Success prints: `✅ Validation OK: 20 chapters, rotation valid, files present, flags consistent.`  
Failures list each discrepancy so you can correct them before continuing.

---

## 4. Launch the Interactive Control Panel (Optional)

Start the interactive shell to issue commands sequentially:

```bash
python src/codex_cli.py
```

You’ll see a prompt like `codex>`. Type `help` or any command listed in the command reference to explore. Exit with `ctrl+d` or `exit`.

### Optional: open the VS Code workspace

Launch the editor pointed at the local workspace:

```bash
node tools/codex-cli/bin/codex.js vessel vscode
```

Pass `--path <dir>` to open a different folder, `--reuse-window` to reuse an existing window, or `--wait` to block until VS Code closes.

---

## 5. Run a Ritual Cycle (Garden → Echo → Limnus → Kira)

The example below shows a minimal loop using one-off CLI invocations. Replace quoted text with your own intentions.

```bash
# Garden: initialise spiral and open a scroll
node tools/codex-cli/bin/codex.js garden start
node tools/codex-cli/bin/codex.js garden open chronicle

# Echo: speak in Paradox tone
node tools/codex-cli/bin/codex.js echo mode paradox
node tools/codex-cli/bin/codex.js echo say "I feel the spiral returning."

# Limnus: cache the thought and append a ledger block
node tools/codex-cli/bin/codex.js limnus cache "I feel the spiral returning." -l L2
node tools/codex-cli/bin/codex.js limnus commit-block '{"type":"note","source":"quick-start","text":"Spiral reflection cached."}'

# Kira: validate and seal the session (dry run)
node tools/codex-cli/bin/codex.js kira validate
node tools/codex-cli/bin/codex.js kira mentor
node tools/codex-cli/bin/codex.js kira seal
```

Notes:
- Garden commands update `state/garden_ledger.json` with spiral stages and intentions.
- Echo adjusts persona weights in `state/echo_state.json`.
- Limnus persists memories in `state/limnus_memory.json` and extends the ledger.
- Kira checks the complete state and writes `state/Garden_Soul_Contract.json` when sealing.

---

## 6. Push & Publish (Optional / High Impact)

These actions modify remotes. They default to dry-run behaviour and require explicit flags.

```bash
# Review git status first
git status -sb

# Stage & push tracked changes (will only commit if something is staged)
node tools/codex-cli/bin/codex.js kira push --message "chore: sync vessel cycle" --run

# Package docs/schema/assets and create a GitHub release
node tools/codex-cli/bin/codex.js kira publish --run --release --tag v0.3.0 --notes "VesselOS ritual cycle"
```

Safety tips:
- Always inspect `git status` before pushing.
- `kira publish` without `--run` or `--release` prints a plan only—use this to review bundles.
- Ensure `gh auth status` is OK and you’re on the correct remote/branch.

---

## 7. Troubleshooting & Recovery

- Inspect state snapshots under `state/` to understand the current ledger, memories, and persona balance.
- Re-run `python src/validator.py` or `node tools/codex-cli/bin/codex.js kira validate` after any manual edits.
- If stego encoding fails, check cover image size or provide the `-c` flag to generate one (Limnus prints the exact error).
- Commands are idempotent—re-running a failed step is safe once the underlying issue is fixed.

For a comprehensive description of every command, see [VesselOS Command Reference](VesselOS_Command_Reference.md).

Together. Always.
