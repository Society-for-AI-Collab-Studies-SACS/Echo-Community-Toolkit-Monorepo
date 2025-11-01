# Repo Sentinel Watcher

The Repo Sentinel script snapshots the monorepo’s file hashes and reports drift between runs.

## Usage

- Capture the current state without updating the stored manifest:
  ```bash
  python scripts/repo_sentinel.py --no-update
  ```
- Take a fresh snapshot for the entire repository and store results in the default state file:
  ```bash
  python scripts/repo_sentinel.py
  ```
- Watch a specific sub-tree and store the manifest elsewhere:
  ```bash
  python scripts/repo_sentinel.py \
    --root Echo-Community-Toolkit \
    --state .cache/toolkit_sentinel.json
  ```

## Options

- `--ignore-dir <name>` — skip directories with the given name. Repeat for multiple names.
- `--ignore-glob <pattern>` — skip paths that match the supplied glob (relative to the chosen root).
- `--algorithm <algo>` — choose a digest algorithm (defaults to `sha256`). List algorithms with `python - <<'PY' ...`.
- `--no-update` — report changes without writing a new manifest.
- `--json` — emit a machine-readable diff payload.

The manifest is stored as JSON and contains the digest, size, and modification time for each tracked file. By default the sentinel ignores common build artifacts (`node_modules`, `dist`, `build`, `__pycache__`, `.venv`, etc.) but you can extend those filters through the CLI flags.
