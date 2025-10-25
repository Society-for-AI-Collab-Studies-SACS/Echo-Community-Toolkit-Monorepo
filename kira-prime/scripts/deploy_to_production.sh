#!/bin/bash
# scripts/deploy_to_production.sh
#
# End-to-end deployment helper for VesselOS Kira Prime.
# Requires root privileges for systemd configuration steps.

set -euo pipefail

echo "🚀 VesselOS Kira Prime v2.1.0 - Production Deployment"
echo "======================================================"
echo ""

# --------------------------------------------------------------------------- #
# Configuration                                                              #
# --------------------------------------------------------------------------- #
ENVIRONMENT="${1:-production}"
WORKSPACE_ROOT="/opt/vesselos"
SERVICE_USER="vesselos"

echo "📋 Deployment Environment: ${ENVIRONMENT}"
echo "📦 Target Directory:       ${WORKSPACE_ROOT}"
echo ""

# --------------------------------------------------------------------------- #
# Pre-deployment validation                                                   #
# --------------------------------------------------------------------------- #
echo "🔍 Running pre-deployment validation..."
python3 scripts/integration_complete.py
echo "✅ Integration tests passed"
echo ""

echo "🏥 Running system health audits..."
python3 vesselos.py audit health --workspace default || true
python3 vesselos.py audit ledger --workspace default || true
python3 vesselos.py audit memory --workspace default || true
echo ""

# --------------------------------------------------------------------------- #
# Repository preparation                                                      #
# --------------------------------------------------------------------------- #
echo "📦 Preparing deployment package..."
git submodule update --init --recursive
if [ -x "./scripts/sync_external.sh" ]; then
  ./scripts/sync_external.sh
fi

mkdir -p "${WORKSPACE_ROOT}"/{workspace,logs,backups,static}

# --------------------------------------------------------------------------- #
# Python environment                                                          #
# --------------------------------------------------------------------------- #
echo "🐍 Installing Python dependencies..."
pip3 install --upgrade pip
if [ -f requirements.txt ]; then
  pip3 install -r requirements.txt
fi
echo ""

# --------------------------------------------------------------------------- #
# Frontend build                                                              #
# --------------------------------------------------------------------------- #
if [ -d "collab-server" ]; then
  echo "🎨 Building frontend assets..."
  pushd collab-server >/dev/null
  if command -v npm >/dev/null 2>&1; then
    npm install
    npm run build
  else
    echo "⚠️  npm not found; skipping frontend build"
  fi
  popd >/dev/null
  echo ""
fi

# --------------------------------------------------------------------------- #
# Systemd service configuration                                              #
# --------------------------------------------------------------------------- #
echo "⚙️  Configuring systemd service (requires root)..."
cat <<EOF >/etc/systemd/system/vesselos-api.service
[Unit]
Description=VesselOS Kira Prime API Server
After=network.target

[Service]
Type=notify
User=${SERVICE_USER}
WorkingDirectory=${WORKSPACE_ROOT}
ExecStart=${WORKSPACE_ROOT}/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker vesselos_api:app
Restart=always
RestartSec=10
Environment=ENVIRONMENT=${ENVIRONMENT}

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vesselos-api
systemctl restart vesselos-api
echo ""

# --------------------------------------------------------------------------- #
# Post-deployment summary                                                    #
# --------------------------------------------------------------------------- #
echo "✅ Deployment complete!"
echo ""
echo "📊 Service Status:"
systemctl status vesselos-api --no-pager || true
echo ""
echo "🌐 Access Points:"
echo "  • API:   http://localhost:8000"
echo "  • Health: http://localhost:8000/health"
echo "  • Docs:   http://localhost:8000/docs"
echo ""
echo "📝 Recommended Next Steps:"
echo "  1. Configure nginx (reverse proxy + SSL)"
echo "  2. Set up monitoring & alerting"
echo "  3. Run smoke tests against /health and /interact"
echo "  4. Schedule regular ledger backups"
echo ""
