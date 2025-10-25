#!/usr/bin/env bash
set -euo pipefail

echo "🔄 Syncing submodules..."
git submodule sync --recursive
git submodule update --init --recursive
echo "✅ Submodules are up to date."

