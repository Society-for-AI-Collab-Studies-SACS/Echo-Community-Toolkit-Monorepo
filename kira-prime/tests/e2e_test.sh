#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -n "${PRIME_CLI:-}" ]]; then
  # shellcheck disable=SC2206
  CLI=(${PRIME_CLI})
elif command -v prime >/dev/null 2>&1; then
  CLI=(prime)
else
  CLI=(python3 "$REPO_ROOT/vesselos.py")
fi

run_cli() {
  "${CLI[@]}" "$@"
}

log() {
  printf '%s\n' "$@"
}

log "[TEST] End-to-end integration test"

log "[STEP] Semantic memory"
run_cli limnus cache "I love programming"
run_cli limnus cache "Coding is my passion"
run_cli limnus cache "The weather is nice"
results="$(run_cli limnus recall "software development" || true)"
log "[INFO] Semantic recall output: ${results}"

log "[STEP] Git automation"
if ! run_cli kira push --run --message "Test commit"; then
  log "[WARN] Git push command reported an error"
fi

log "[STEP] Validation"
if ! run_cli kira validate; then
  log "[WARN] Validation command reported issues"
fi

log "[STEP] VSCode extension"
if command -v code >/dev/null 2>&1 && code --list-extensions | grep -q "kira-prime"; then
  log "[INFO] VSCode extension detected"
else
  log "[INFO] VSCode extension not installed"
fi

log "[RESULT] Integration script completed"
