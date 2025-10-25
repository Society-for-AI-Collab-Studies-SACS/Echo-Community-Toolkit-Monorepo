#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script for VesselOS development environments.
# Run from the repository root: ./scripts/bootstrap.sh

PYTHON_VERSION=${PYTHON_VERSION:-"3.10"}
NODE_VERSION=${NODE_VERSION:-"20"}

echo ">>> Creating Python virtual environment (python${PYTHON_VERSION} required)..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ -f requirements-dev.txt ]; then
  echo ">>> Installing dev requirements..."
  pip install -r requirements-dev.txt
fi

echo ">>> Installing Node.js dependencies (requires Node ${NODE_VERSION}+)."
if command -v npm >/dev/null 2>&1; then
  npm install
else
  echo "npm not found. Install Node.js ${NODE_VERSION}+ before continuing." >&2
fi

echo ">>> Bootstrap complete."
echo "Activate the environment with: source .venv/bin/activate"
echo "Then run VesselOS commands via: python3 vesselos.py <agent> <command>"
