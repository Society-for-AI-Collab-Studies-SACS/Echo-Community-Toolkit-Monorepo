#!/bin/bash
# Setup Git/GitHub for VesselOS

set -e

echo "[INFO] Setting up Git/GitHub integration..."

# Initialize repository if needed
if [ ! -d ".git" ]; then
    echo "[INFO] Initializing git repository..."
    git init
    git add .
    git commit -m "chore: initial commit"
fi

# Ensure GitHub CLI is available
if ! command -v gh >/dev/null 2>&1; then
    echo "[WARN] GitHub CLI (gh) not found"
    echo "Install from https://cli.github.com/ or use 'sudo apt install gh' on Ubuntu."
    exit 1
fi

echo "[INFO] Checking GitHub authentication..."
if ! gh auth status >/dev/null 2>&1; then
    echo "[ACTION] Authenticate with GitHub via 'gh auth login'"
    gh auth login
fi

REPO_NAME="kira-prime"
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "[INFO] Creating GitHub repository ${REPO_NAME}..."
    gh repo create "${REPO_NAME}" --private --source=. --remote=origin --push
    echo "[INFO] Repository created and pushed."
else
    echo "[INFO] Remote repository already configured."
fi

cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/

# Node
node_modules/
dist/

# IDE
.vscode/
.idea/

# Logs
logs/*.log

# OS artifacts
.DS_Store
Thumbs.db

# State artifacts
state/*.png
state/semantic_index.json
EOF

git add .gitignore
git commit -m "chore: add .gitignore" || echo "[INFO] No changes to commit for .gitignore"

echo "[INFO] Git/GitHub setup complete."
echo "Try: prime kira push --run --message 'Initial commit'"
echo "     prime kira publish --run --release"
