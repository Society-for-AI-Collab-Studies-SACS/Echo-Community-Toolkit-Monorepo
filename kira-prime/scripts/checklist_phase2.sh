#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(pwd)"

echo "== Phase 2 Checklist =="

PYTHON_BIN="${PYTHON_BIN:-python3}"
declare -a PIP_INSTALL_ARGS=()
if [ -z "${VIRTUAL_ENV:-}" ]; then
  PIP_INSTALL_ARGS+=(--user)
fi
export PIP_BREAK_SYSTEM_PACKAGES=1

echo "[1/6] Python deps"
"${PYTHON_BIN}" -m pip install "${PIP_INSTALL_ARGS[@]}" -U pip
if [ -f requirements.txt ]; then "${PYTHON_BIN}" -m pip install "${PIP_INSTALL_ARGS[@]}" -r requirements.txt; fi
if [[ "$(uname -s)" == "Linux" ]]; then
  "${PYTHON_BIN}" -m pip install "${PIP_INSTALL_ARGS[@]}" faiss-cpu
else
  echo "Non-Linux platform detected; skipping faiss-cpu install."
fi

echo "[2/6] Tests (Python)"
"${PYTHON_BIN}" -m pytest -q

echo "[3/6] Build FAISS index (optional)"
export KIRA_VECTOR_BACKEND=faiss
if [ -f scripts/build_faiss_index.py ]; then
  "${PYTHON_BIN}" scripts/build_faiss_index.py
else
  echo "No FAISS builder script found; skipping."
fi

echo "[4/6] UI build & tests"
if [ -d "lambda-vite" ]; then
  pushd lambda-vite >/dev/null
elif [ -d "Echo-Community-Toolkit/lambda-vite" ]; then
  pushd Echo-Community-Toolkit/lambda-vite >/dev/null
else
  echo "Lambda Vite workspace not found."
  exit 1
fi
npm_cmd="ci"
if [ ! -f package-lock.json ]; then
  echo "package-lock.json missing; falling back to npm install --no-save."
  npm_cmd="install --no-save"
fi
npm ${npm_cmd}
npm run build
npm test -- --run
tar -C dist -czf "${PROJECT_ROOT}/lambda-vite-dist.tar.gz" .
popd >/dev/null

echo "[5/6] Assemble changelog"
"${PYTHON_BIN}" scripts/assemble_changelog.py > CHANGELOG_RELEASE.md
head -n 20 CHANGELOG_RELEASE.md

echo "[6/6] Package via Kira (JSON + human logs)"
PYTHONPATH="$(pwd)" "${PYTHON_BIN}" - <<'PY'
from pathlib import Path
import sys

root = Path(".").resolve()
sys.path.insert(0, str(root))

try:
    from vesselos.agents.kira_agent import KiraAgent
except ImportError:
    from agents.kira.kira_agent import KiraAgent  # type: ignore

k = KiraAgent(root)
validate_result = k.validate()
publish_result = k.publish(run=True, release=False, notes_file="CHANGELOG_RELEASE.md")
print("JSON:", {"validate": validate_result, "publish": publish_result})
print("LOG: Kira publish (package-only) complete – see CHANGELOG_RELEASE.md")
PY

echo "✅ Phase 2 checklist complete."
