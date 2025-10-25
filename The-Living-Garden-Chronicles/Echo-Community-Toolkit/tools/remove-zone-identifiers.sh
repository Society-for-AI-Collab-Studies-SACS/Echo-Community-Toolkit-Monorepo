#!/usr/bin/env bash
set -euo pipefail

# Remove Zone.Identifier files (tracked and untracked) from the working tree.
# Usage: bash tools/remove-zone-identifiers.sh

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

echo "Scanning for Zone.Identifier artifacts..." >&2

# Remove untracked artifacts first (outside .git). This is safe and cleans noise.
mapfile -t untracked < <(find . -path './.git' -prune -o -type f -name '*:Zone.Identifier*' -print)
if ((${#untracked[@]})); then
  printf 'Removing %d untracked artifacts...\n' "${#untracked[@]}" >&2
  # Use rm to remove untracked files
  for f in "${untracked[@]}"; do
    rm -f -- "$f"
  done
fi

# Remove tracked artifacts and stage deletions.
mapfile -d '' -t tracked < <(git ls-files -z | perl -0ne 'print if /:Zone\.Identifier/')
if ((${#tracked[@]})); then
  printf 'Staging removal of %d tracked artifacts...\n' "${#tracked[@]}" >&2
  git rm --quiet -- "${tracked[@]}"
fi

# Optionally clean stray artifacts inside .git directory (purely cosmetic).
mapfile -t stray_git < <(find .git -type f -name '*:Zone.Identifier*' -print || true)
if ((${#stray_git[@]})); then
  printf 'Cleaning %d stray artifacts inside .git ...\n' "${#stray_git[@]}" >&2
  for f in "${stray_git[@]}"; do
    rm -f -- "$f"
  done
fi

echo "Done. Review with: git status" >&2

