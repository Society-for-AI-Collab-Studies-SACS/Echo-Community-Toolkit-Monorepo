#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

MODE="pull" # pull|push|verify
BRANCH="main"
MSG="chore(g2v): subtree sync"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull) MODE="pull"; shift;;
    --push) MODE="push"; shift;;
    --verify) MODE="verify"; shift;;
    --branch) BRANCH="$2"; shift 2;;
    --msg) MSG="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

if [[ ! -d g2v_repo ]]; then
  echo "g2v_repo/ not found in $ROOT_DIR" 1>&2
  exit 1
fi

remote_exists() {
  git remote get-url "$1" >/dev/null 2>&1
}

maybe_detect_branch() {
  # Try gh to detect default branch; fallback to BRANCH env
  if command -v gh >/dev/null 2>&1; then
    if gh auth status >/dev/null 2>&1; then
      local dbr
      if dbr=$(gh repo view Society-for-AI-Collab-Studies-SACS/g2v_repo --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null); then
        echo "$dbr"; return 0
      fi
    fi
  fi
  echo "$BRANCH"
}

install_and_test() {
  echo "[g2v] Installing editable package and running tests..."
  python3 -m pip install -q --user --break-system-packages --no-build-isolation -e ./g2v_repo || true
  if command -v pytest >/dev/null 2>&1; then
    pytest -q g2v_repo/tests || true
  fi
  python3 g2v_repo/examples/demo_stack_and_project.py || true
}

if [[ "$MODE" == "pull" ]]; then
  if ! remote_exists g2v_upstream; then
    echo "Adding g2v_upstream remote..."
    git remote add g2v_upstream https://github.com/Society-for-AI-Collab-Studies-SACS/g2v_repo.git || true
  fi
  BR="$(maybe_detect_branch)"
  echo "[g2v] Subtree pull from g2v_upstream/$BR into g2v_repo/ ..."
  # Try to fetch; ignore failures if offline
  git fetch g2v_upstream "$BR" || true
  # Perform subtree pull; ignore failure offline
  git subtree pull --prefix=g2v_repo g2v_upstream "$BR" -m "$MSG from upstream/$BR" --squash || true
  install_and_test
  exit 0
fi

if [[ "$MODE" == "push" ]]; then
  echo "[g2v] Preparing subtree split branch from g2v_repo/..."
  SPLIT_BRANCH="g2v_sync_split"
  git branch -D "$SPLIT_BRANCH" >/dev/null 2>&1 || true
  git subtree split --prefix=g2v_repo -b "$SPLIT_BRANCH" || true

  if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI not available. Install gh and rerun with --push" 1>&2
    exit 1
  fi
  if ! gh auth status >/dev/null 2>&1; then
    echo "gh not authenticated. Run: gh auth login" 1>&2
    exit 1
  fi

  # Ensure we have a fork remote for g2v_repo
  if ! remote_exists g2v_fork; then
    echo "[g2v] Creating fork remote via gh..."
    gh repo fork Society-for-AI-Collab-Studies-SACS/g2v_repo --remote=true --clone=false || true
    # gh may add 'origin' remote; rename to g2v_fork if needed
    if remote_exists origin && [[ "$(git remote get-url origin)" == *"g2v_repo"* ]]; then
      git remote rename origin g2v_fork || true
    fi
  fi

  PUSH_BRANCH="sync/mono-$(date +%Y%m%d-%H%M%S)"
  echo "[g2v] Pushing split branch to fork as $PUSH_BRANCH..."
  git push -u g2v_fork "$SPLIT_BRANCH:$PUSH_BRANCH" || true

  echo "[g2v] Opening PR to upstream..."
  gh pr create \
    --repo Society-for-AI-Collab-Studies-SACS/g2v_repo \
    --title "sync: monorepo g2v subtree" \
    --body "Automated subtree sync from monorepo. Branch: $PUSH_BRANCH" \
    --base "$(maybe_detect_branch)" \
    --head "$PUSH_BRANCH" || true
  exit 0
fi

if [[ "$MODE" == "verify" ]]; then
  install_and_test
  exit 0
fi

echo "Unknown MODE: $MODE" 1>&2
exit 2

