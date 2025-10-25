#!/usr/bin/env bash
# Automates regeneration of schema, chapters, and stego PNG assets, then commits
# the results. Includes optional flags for running the toolkit/validator steps.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

FLAG_TOOLKIT=0
FLAG_PUSH=0

usage() {
  cat <<'EOF'
Usage: refresh_stego_assets.sh [options] [commit-message]

Options:
  -t, --toolkit   Run scripts/setup_toolkit_and_validate.sh after generation.
  -p, --push      Push the resulting commit to origin/main.
  -h, --help      Show this help message and exit.

If no commit message is provided, a default structured message will be used.
EOF
}

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--toolkit)
      FLAG_TOOLKIT=1
      shift
      ;;
    -p|--push)
      FLAG_PUSH=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        POSITIONAL+=("$1")
        shift
      done
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

COMMIT_MESSAGE=${POSITIONAL[0]:-"chore: refresh stego assets"}

# Dependency checks
command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 1; }

if ! python3 -c "import PIL" >/dev/null 2>&1; then
  echo "Error: Pillow not installed (pip install Pillow)." >&2
  exit 1
fi

pushd "${ROOT_DIR}" >/dev/null

echo "==> Regenerating schema"
python3 src/schema_builder.py

echo "==> Regenerating chapters and stego assets"
python3 src/generate_chapters.py

echo "==> Running validator"
python3 src/validator.py

if [[ ${FLAG_TOOLKIT} -eq 1 ]]; then
  echo "==> Running toolkit integration script"
  ./scripts/setup_toolkit_and_validate.sh
fi

CHANGES=$(git status --porcelain)
if [[ -z ${CHANGES} ]]; then
  echo "No changes detected; nothing to commit."
  popd >/dev/null
  exit 0
fi

echo "==> Staging stego assets and metadata"
git add frontend/assets schema src README.md scripts || true
# Stage submodule pointer if updated
if ! git diff --quiet Echo-Community-Toolkit; then
  git add Echo-Community-Toolkit
fi

echo "==> Committing with message: ${COMMIT_MESSAGE}"
git commit -m "${COMMIT_MESSAGE}"
SUBMODULE_STATUS=$(git status --porcelain Echo-Community-Toolkit)
if [[ -n ${SUBMODULE_STATUS} ]]; then
  echo "Submodule Echo-Community-Toolkit has pending changes. Commit/push inside the submodule separately."
fi

if [[ ${FLAG_PUSH} -eq 1 ]]; then
  echo "==> Pushing to origin/main"
  git push -u origin main
else
  echo "Commit created locally. Review with 'git log -1 --stat' before pushing."
fi

popd >/dev/null
