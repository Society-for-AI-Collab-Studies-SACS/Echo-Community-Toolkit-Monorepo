#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_DIR="${ROOT_DIR}/kira-prime"
VENV_DIR="${PROJECT_DIR}/.ci_venv"
EXTRA_PATH="${ROOT_DIR}/vesselos-dev-research"

npm_bootstrap() {
  if [[ -f package-lock.json ]]; then
    npm ci --no-audit --no-fund
  else
    npm install --no-audit --no-fund
  fi
}

if [[ -d "${PROJECT_DIR}/collab-server" ]]; then
  pushd "${PROJECT_DIR}/collab-server" >/dev/null
  npm_bootstrap
  npm run build
  popd >/dev/null
fi

if [[ -d "${PROJECT_DIR}/lambda-vite" ]]; then
  pushd "${PROJECT_DIR}/lambda-vite" >/dev/null
  npm_bootstrap
  npm run build
  npm run test
  popd >/dev/null
fi

if [[ -d "${PROJECT_DIR}/vscode-extension" ]]; then
  pushd "${PROJECT_DIR}/vscode-extension" >/dev/null
  npm_bootstrap
  npm run lint
  npm run compile
  popd >/dev/null
fi

rm -rf "${VENV_DIR}"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install -r "${PROJECT_DIR}/requirements.txt"
if [[ -f "${PROJECT_DIR}/requirements-dev.txt" ]]; then
  python3 -m pip install -r "${PROJECT_DIR}/requirements-dev.txt"
fi

PYTHONPATH="${PROJECT_DIR}:${EXTRA_PATH}" python3 vesselos.py validate
PYTHONPATH="${PROJECT_DIR}:${EXTRA_PATH}" python3 -m pytest -q

deactivate
rm -rf "${VENV_DIR}"
