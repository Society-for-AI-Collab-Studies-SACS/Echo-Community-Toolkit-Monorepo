#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_DIR="${ROOT_DIR}/kira-prime"
VENV_DIR="${PROJECT_DIR}/.ci_venv"
EXTRA_PATH="${ROOT_DIR}/vesselos-dev-research"

rm -rf "${VENV_DIR}"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

PYTHONPATH="${PROJECT_DIR}:${EXTRA_PATH}" python3 vesselos.py validate
PYTHONPATH="${PROJECT_DIR}:${EXTRA_PATH}" python3 -m pytest -q

deactivate
rm -rf "${VENV_DIR}"
