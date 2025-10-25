#!/usr/bin/env bash
set -euo pipefail

# Placeholder bootstrap script for The Living Library.
# Installs submodule dependencies and prepares workspace directories.

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "${SCRIPT_ROOT}")"

cd "${REPO_ROOT}"

echo "[bootstrap] Initialising submodules"
git submodule update --init --recursive

echo "[bootstrap] Creating default workspace"
python3 - <<'PY'
from workspace.manager import WorkspaceManager

manager = WorkspaceManager()
manager.register("default")
print("Created workspace:", "default")
PY

echo "[bootstrap] Done"
