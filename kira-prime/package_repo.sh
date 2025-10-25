#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_NAME="vessel_narrative_system"
ZIP_OUT="${ROOT_DIR}/../${BASE_NAME}.zip"

echo "Packaging ${BASE_NAME} -> ${ZIP_OUT}"
cd "${ROOT_DIR}/.."
rm -f "${ZIP_OUT}"
zip -rq "${ZIP_OUT}" "${BASE_NAME}" -x "*/__pycache__/*"
echo "Done."

