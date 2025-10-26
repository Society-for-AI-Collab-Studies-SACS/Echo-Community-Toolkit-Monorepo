#!/usr/bin/env bash
# Link local monorepo Python packages into a venv using a .pth file.
# This enables kira-prime to import `library_core` from vesselos-dev-research
# and resolve its own `agents` namespace when executed as a module.
#
# Usage:
#   bash scripts/link_dev_packages.sh [--venv PATH] [--unlink] [--verify]
#
# Default venv path is ./venv relative to repo root.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${VENV_PATH:-$REPO_ROOT/venv}"
UNLINK=false
VERIFY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --venv)
      VENV_PATH="$2"; shift 2 ;;
    --unlink)
      UNLINK=true; shift ;;
    --verify)
      VERIFY=true; shift ;;
    --help|-h)
      echo "Usage: $0 [--venv PATH] [--unlink] [--verify]"; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -x "$VENV_PATH/bin/python" ]]; then
  echo "error: venv python not found at $VENV_PATH/bin/python" >&2
  exit 1
fi

# Resolve absolute venv path for use across subshells
VENV_ABS="$(cd "$VENV_PATH" && pwd)"

SITE_PACKAGES="$($VENV_ABS/bin/python - <<'PY'
import sysconfig
print(sysconfig.get_paths()["purelib"])
PY
)"

PTH_FILE="$SITE_PACKAGES/monorepo_paths.pth"

if $UNLINK; then
  if [[ -f "$PTH_FILE" ]]; then
    rm -f "$PTH_FILE"
    echo "Unlinked: $PTH_FILE"
  else
    echo "Nothing to unlink: $PTH_FILE does not exist"
  fi
  exit 0
fi

# Write only the necessary paths to avoid shadowing top-level packages.
{
  echo "$REPO_ROOT/vesselos-dev-research"
  echo "$REPO_ROOT/kira-prime"
} > "$PTH_FILE"

echo "Linked monorepo packages via: $PTH_FILE"
echo "  - $REPO_ROOT/vesselos-dev-research"
echo "  - $REPO_ROOT/kira-prime"

if $VERIFY; then
  # Verify library_core import from vesselos-dev-research
  if ! "$VENV_ABS/bin/python" - <<'PY'
import importlib
import sys
try:
    import library_core.workspace as lc
    print("import library_core.workspace -> OK")
    raise SystemExit(0)
except Exception as e:
    print("import library_core.workspace -> FAIL:", e)
    raise SystemExit(1)
PY
  then exit 1; fi

  # Verify agents import from kira-prime with CWD set to kira-prime to avoid root package shadowing.
  if ! ( cd "$REPO_ROOT/kira-prime" && "$VENV_ABS/bin/python" - <<'PY'
try:
    import agents.echo.echo_agent as ae
    print("import agents.echo.echo_agent -> OK")
    raise SystemExit(0)
except Exception as e:
    print("import agents.echo.echo_agent -> FAIL:", e)
    raise SystemExit(1)
PY
  ); then exit 1; fi
fi

