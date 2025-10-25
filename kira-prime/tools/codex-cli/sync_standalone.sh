#!/usr/bin/env bash
set -euo pipefail
# Sync in-repo Codex CLI to the standalone local repo at ../../tools/codex-cli
# Default: sync code only (bin/codex.js, package.json). Use --all to include README/AGENTS.

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE"
DEST="$(cd "$HERE/../../.." && pwd)/tools/codex-cli"

INCLUDE_ALL=false
while [[ ${1:-} ]]; do
  case "$1" in
    --all|-a) INCLUDE_ALL=true;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
  shift || true
done

if [[ ! -d "$DEST/.git" ]]; then
  echo "Destination $DEST is not a git repository; aborting." >&2
  exit 1
fi

echo "Syncing from $SRC to $DEST ..."

# Always sync bin/codex.js and package.json
install -d "$DEST/bin"
cp -f "$SRC/bin/codex.js" "$DEST/bin/codex.js"
cp -f "$SRC/package.json" "$DEST/package.json"

if $INCLUDE_ALL; then
  cp -f "$SRC/README.md" "$DEST/README.md"
  cp -f "$SRC/AGENTS.md" "$DEST/AGENTS.md"
fi

cd "$DEST"
if ! git diff --quiet --ignore-submodules --; then
  git add -A
  git commit -m "chore(sync): mirror in-repo Codex CLI updates"
  # Unarchive remote if needed and push
  if command -v gh >/dev/null 2>&1; then
    gh repo unarchive "$(git config --get remote.origin.url | sed -E 's#.*/([^/]+)\.git#\1#' | xargs -I{} echo "$(git config --get remote.origin.url | sed -E 's#https://github.com/([^/]+)/.*#\1#')")/$(basename -s .git "$(git config --get remote.origin.url)")" 2>/dev/null || true
  fi
  git push origin HEAD
else
  echo "No changes to sync."
fi

echo "Done."
