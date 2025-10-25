#!/usr/bin/env bash
# Automates submodule sync, Echo-Community-Toolkit setup, soulcode bundle generation,
# and final validator run for the Vessel Narrative MRP repository.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLKIT_DIR="${ROOT_DIR}/Echo-Community-Toolkit"

log() {
  printf '\n==> %s\n' "$1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is required but not installed." >&2
    exit 1
  fi
}

require_cmd git
require_cmd npm

PYTHON_BIN="python"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "Error: 'python' or 'python3' is required but not installed." >&2
    exit 1
  fi
fi

NODE_BIN="node"
NODE_VERSION=""
NODE_MAJOR=""
if command -v "$NODE_BIN" >/dev/null 2>&1; then
  NODE_VERSION="$($NODE_BIN -v 2>/dev/null || echo '')"
  if [ -n "$NODE_VERSION" ]; then
    NODE_MAJOR="${NODE_VERSION#v}"
    NODE_MAJOR="${NODE_MAJOR%%.*}"
  fi
fi

if [ ! -d "${TOOLKIT_DIR}" ]; then
  echo "Error: Echo-Community-Toolkit submodule not found at ${TOOLKIT_DIR}" >&2
  echo "Run from repository root after cloning with --recurse-submodules." >&2
  exit 1
fi

log "Synchronizing git submodules"
git -C "${ROOT_DIR}" submodule update --init --recursive

log "Updating Echo-Community-Toolkit to latest main"
git -C "${TOOLKIT_DIR}" fetch origin --tags
git -C "${TOOLKIT_DIR}" checkout main
git -C "${TOOLKIT_DIR}" pull --ff-only origin main

log "Installing toolkit dependencies"
if ! (cd "${TOOLKIT_DIR}" && npm ci); then
  echo "npm ci failed; falling back to npm install" >&2
  (cd "${TOOLKIT_DIR}" && npm install)
fi

log "Generating soulcode artifacts"
(cd "${TOOLKIT_DIR}" && npm run soulcode:emit-schema)
(cd "${TOOLKIT_DIR}" && npm run soulcode:bundle)
(cd "${TOOLKIT_DIR}" && npm run soulcode:validate)

SKIP_INTEGRATE=0
if [ -n "${NODE_MAJOR}" ] && [ "${NODE_MAJOR}" -lt 20 ]; then
  SKIP_INTEGRATE=1
  echo "Warning: Node ${NODE_VERSION} detected (<20). Skipping integrate/verify steps that require Node >=20." >&2
fi

if [ "${SKIP_INTEGRATE}" -eq 0 ]; then
  log "Embedding soulcode bundle into narrative (optional HyperFollow integration)"
  SOULCODE_BUNDLE_PATH="${TOOLKIT_DIR}/integration/outputs/echo_live.json"
  if [ -f "${SOULCODE_BUNDLE_PATH}" ]; then
    (cd "${TOOLKIT_DIR}" && SOULCODE_BUNDLE="${SOULCODE_BUNDLE_PATH}" npm run integrate)
  else
    echo "Warning: Soulcode bundle not found at ${SOULCODE_BUNDLE_PATH}. Skipping integrate step." >&2
  fi

  log "Verifying toolkit integration"
  (cd "${TOOLKIT_DIR}" && npm run verify || echo "HyperFollow verification reported issues.")
else
  log "Skipping integrate/verify due to Node version requirements"
fi

log "Running Vessel Narrative validator"
(cd "${ROOT_DIR}" && "$PYTHON_BIN" src/validator.py)

log "Completed toolkit setup and validation."
