#!/usr/bin/env bash
set -euo pipefail

# Open a PR for Phase‑A sidecar changes using gh and a token from:
#   1) $ACEDAD_gh, or 2) $Acead_TOKEN, or 3) token file ("Acead gh.txt" / "ACEAD_GH.txt" / "ACEDAD_gh.txt")

TOKEN="${ACEDAD_gh:-${Acead_TOKEN:-}}"
if [[ -z "$TOKEN" ]]; then
  for f in "Acead gh.txt" "ACEAD_GH.txt" "ACEDAD_gh.txt"; do
    if [[ -f "$f" ]]; then
      TOKEN=$(tr -d ' \r\n' < "$f")
      break
    fi
  done
fi
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: Token not found. Set ACEDAD_gh (or Acead_TOKEN), or create 'Acead gh.txt' with your GitHub token." >&2
  exit 1
fi

echo "Authenticating gh with provided token..."
if gh auth status >/dev/null 2>&1; then
  echo "gh is already authenticated; reconfiguring git protocol to https."
else
  : # not authenticated
fi
printf "%s" "$TOKEN" | gh auth login --hostname github.com --with-token >/dev/null
gh config set git_protocol https -h github.com >/dev/null
gh auth setup-git >/dev/null

# Push the Echo-Community-Toolkit submodule branch (contains code+docs changes)
echo "Pushing submodule branch: Echo-Community-Toolkit feat/mrp-sidecar-cli..."
(
  cd Echo-Community-Toolkit
  # Ensure the branch exists locally
  git rev-parse --verify feat/mrp-sidecar-cli >/dev/null
  git push -u origin feat/mrp-sidecar-cli
)

# Ensure monorepo remote uses https; do not overwrite custom hosts
origin_url=$(git remote get-url origin)
if [[ "$origin_url" =~ ^git@github.com: ]]; then
  https_url="https://github.com/${origin_url#git@github.com:}.git"
  echo "Rewriting origin remote to HTTPS: $https_url"
  git remote set-url origin "$https_url"
fi

echo "Pushing monorepo branch: feat/mrp-sidecar-docs..."
git rev-parse --verify feat/mrp-sidecar-docs >/dev/null
git push -u origin feat/mrp-sidecar-docs

# Determine default branch (fallback: main)
default_branch=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo main)

title='feat(mrp): Phase‑A sidecar helpers + docs; update submodule'
body_file='pr/PR_BODY_MRP_SIDECAR.md'

echo "Creating PR against $default_branch..."
gh pr create \
  --base "$default_branch" \
  --head feat/mrp-sidecar-docs \
  --title "$title" \
  --body-file "$body_file"

echo "Done."
