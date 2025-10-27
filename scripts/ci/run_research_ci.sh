#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_DIR="${ROOT_DIR}/vesselos-dev-research"
VENV_DIR="${PROJECT_DIR}/.ci_venv"

npm_bootstrap() {
  if [[ -f package-lock.json ]]; then
    npm ci --no-audit --no-fund
  else
    npm install --no-audit --no-fund
  fi
}

if [[ -f "${PROJECT_DIR}/package.json" ]]; then
  pushd "${PROJECT_DIR}" >/dev/null
  npm_bootstrap
  npm run lint
  npm run build
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
pushd "${PROJECT_DIR}" >/dev/null
python3 -m pytest -q
popd >/dev/null
deactivate
rm -rf "${VENV_DIR}"
