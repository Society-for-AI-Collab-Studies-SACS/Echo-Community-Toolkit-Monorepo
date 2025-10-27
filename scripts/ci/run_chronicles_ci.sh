#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_DIR="${ROOT_DIR}/The-Living-Garden-Chronicles"
VENV_DIR="${PROJECT_DIR}/.ci_venv"

rm -rf "${VENV_DIR}"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install pillow pyyaml >/dev/null 2>&1 || true

pushd "${PROJECT_DIR}" >/dev/null
python3 src/schema_builder.py
python3 src/generate_chapters.py
python3 src/validator.py
popd >/dev/null

deactivate
rm -rf "${VENV_DIR}"

# Prevent generated artifacts from leaving the tree dirty during local runs.
git -C "${PROJECT_DIR}" checkout -- frontend/index.html frontend/assets >/dev/null 2>&1 || true
