#!/usr/bin/env bash
set -euo pipefail

# Local mirror of the Python CI job.
# Run from g2v_repo after moving code here.

PYTHON_VERSION=${PYTHON_VERSION:-"3.10"}
VENV_DIR=${VENV_DIR:-".venv"}

echo "[python-ci] Using Python ${PYTHON_VERSION} (system default will be used if not installed)"

if [ ! -d "$VENV_DIR" ]; then
  echo "[python-ci] Creating virtual environment in ${VENV_DIR}"
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

if [ -f requirements.txt ]; then
  echo "[python-ci] Installing requirements.txt"
  pip install -r requirements.txt
else
  echo "[python-ci] No requirements.txt found; continuing"
fi

echo "[python-ci] Installing dev/test tools"
pip install grpcio grpcio-tools websockets flake8 pytest

echo "[python-ci] Protobuf generation (if present)"
if [ -f protos/agents.proto ]; then
  python -m grpc_tools.protoc -Iprotos --python_out=protos --grpc_python_out=protos protos/agents.proto
  python - <<'PY'
from pathlib import Path
p = Path('protos/agents_pb2_grpc.py')
if p.exists():
    t = p.read_text()
    t2 = t.replace('import agents_pb2 as agents__pb2', 'from . import agents_pb2 as agents__pb2')
    if t2 != t:
        p.write_text(t2)
print('protos OK')
PY
else
  echo "[python-ci] No protos/agents.proto found; skipping"
fi

if [ -d agents ]; then
  echo "[python-ci] Linting agents with flake8"
  flake8 agents
else
  echo "[python-ci] No agents directory; skipping flake8"
fi

echo "[python-ci] Running pytest if tests detected"
if [ -d tests ] || ls -1 test_*.py tests/test_*.py >/dev/null 2>&1; then
  pytest -q
else
  echo "[python-ci] No tests detected; skipping pytest"
fi

echo "[python-ci] Done"

