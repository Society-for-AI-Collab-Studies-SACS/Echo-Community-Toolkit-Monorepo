#!/usr/bin/env bash
#
# Living Library SIGPRINT Deployment Utility
# ------------------------------------------
# Bootstraps the Python environment, regenerates protobufs, optionally
# builds/uploads firmware, and launches the orchestrator or individual
# agents for the unified SIGPRINT runtime.
#
# Usage examples:
#   scripts/deploy.sh --full
#   scripts/deploy.sh --orchestrator
#   scripts/deploy.sh --clean
#

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
DATA_DIR="$PROJECT_ROOT/data"
LOGS_DIR="$PROJECT_ROOT/logs"
NARRATIVES_DIR="$PROJECT_ROOT/narratives"
PATTERNS_DIR="$PROJECT_ROOT/patterns"
EXPORTS_DIR="$PROJECT_ROOT/exports"
FIRMWARE_DIR="$PROJECT_ROOT/PlatformIO"
CONFIG_PATH="$PROJECT_ROOT/config/default_config.yaml"

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RESET='\033[0m'

PLATFORMIO_AVAILABLE=false
BAZEL_AVAILABLE=false
SKIP_FIRMWARE=false

print_header() {
    echo -e "${COLOR_GREEN}============================================================${COLOR_RESET}"
    echo -e "${COLOR_GREEN}      Living Library SIGPRINT Runtime Deployment             ${COLOR_RESET}"
    echo -e "${COLOR_GREEN}      Multi-Agent Consciousness Research Stack               ${COLOR_RESET}"
    echo -e "${COLOR_GREEN}============================================================${COLOR_RESET}"
    echo
}

status_line() {
    local color="$1"; shift
    printf "%b%s%b\n" "${color}" "$*" "${COLOR_RESET}"
}

check_prerequisites() {
    status_line "${COLOR_YELLOW}" "Checking prerequisites..."

    if command -v python3 >/dev/null 2>&1; then
        status_line "${COLOR_GREEN}" "✓ Python 3 detected ($(python3 --version 2>/dev/null))"
    else
        status_line "${COLOR_RED}" "✗ Python 3 not found. Please install Python 3."
        exit 1
    fi

    if command -v pio >/dev/null 2>&1; then
        PLATFORMIO_AVAILABLE=true
        status_line "${COLOR_GREEN}" "✓ PlatformIO detected"
    else
        status_line "${COLOR_YELLOW}" "! PlatformIO not found (firmware build/upload disabled)"
    fi

    if command -v bazel >/dev/null 2>&1; then
        BAZEL_AVAILABLE=true
        status_line "${COLOR_GREEN}" "✓ Bazel detected"
    else
        status_line "${COLOR_YELLOW}" "! Bazel not found (Python entrypoints will be used)"
    fi

    if [ -e /dev/ttyUSB0 ]; then
        status_line "${COLOR_GREEN}" "✓ Serial device /dev/ttyUSB0 present"
    else
        status_line "${COLOR_YELLOW}" "! Serial device not found (expect WiFi mode)"
    fi
    echo
}

create_directories() {
    status_line "${COLOR_YELLOW}" "Creating workspace directories..."
    mkdir -p "$DATA_DIR" "$LOGS_DIR" "$NARRATIVES_DIR" "$PATTERNS_DIR" "$EXPORTS_DIR"
    status_line "${COLOR_GREEN}" "✓ Directories ready"
    echo
}

activate_venv() {
    # shellcheck disable=SC1090
    source "$VENV_PATH/bin/activate"
}

setup_python_environment() {
    status_line "${COLOR_YELLOW}" "Setting up Python virtual environment..."
    if [ ! -d "$VENV_PATH" ]; then
        python3 -m venv "$VENV_PATH"
        status_line "${COLOR_GREEN}" "✓ Virtual environment created"
    else
        status_line "${COLOR_GREEN}" "✓ Virtual environment already exists"
    fi

    activate_venv
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet -r "$PROJECT_ROOT/requirements.txt"
    if [ -f "$PROJECT_ROOT/requirements-full.txt" ]; then
        python -m pip install --quiet -r "$PROJECT_ROOT/requirements-full.txt" || true
    fi
    status_line "${COLOR_GREEN}" "✓ Python dependencies installed"
    echo
}

link_monorepo_packages() {
    # Ensure local module imports (library_core from vesselos-dev-research, agents from kira-prime)
    if [ -x "$PROJECT_ROOT/scripts/link_dev_packages.sh" ]; then
        bash "$PROJECT_ROOT/scripts/link_dev_packages.sh" --venv "$VENV_PATH" || true
    fi
}

generate_protobuf() {
    status_line "${COLOR_YELLOW}" "Generating protobuf stubs..."
    activate_venv
    pushd "$PROJECT_ROOT" >/dev/null

    python -m grpc_tools.protoc \
        -Iprotos \
        --python_out=protos \
        --grpc_python_out=protos \
        protos/agents.proto

    python - <<'PY'
from pathlib import Path
path = Path("protos/agents_pb2_grpc.py")
text = path.read_text()
text = text.replace("import agents_pb2 as agents__pb2", "from . import agents_pb2 as agents__pb2")
path.write_text(text)
PY

    status_line "${COLOR_GREEN}" "✓ Protobuf modules generated (protos/agents_pb2*.py)"
    popd >/dev/null
    echo
}

build_firmware() {
    if [ "$SKIP_FIRMWARE" = true ]; then
        status_line "${COLOR_YELLOW}" "Skipping firmware build (--skip-firmware supplied)"
        echo
        return
    fi

    if [ "$PLATFORMIO_AVAILABLE" = false ]; then
        status_line "${COLOR_YELLOW}" "PlatformIO unavailable; skipping firmware build"
        echo
        return
    fi

    if [ ! -d "$FIRMWARE_DIR" ]; then
        status_line "${COLOR_YELLOW}" "Firmware directory $FIRMWARE_DIR not found; skipping"
        echo
        return
    fi

    status_line "${COLOR_YELLOW}" "Building ESP32 firmware via PlatformIO..."
    pushd "$FIRMWARE_DIR" >/dev/null
    if pio run -e esp32s3_enhanced; then
        status_line "${COLOR_GREEN}" "✓ Firmware built"
        status_line "${COLOR_YELLOW}" "  Artifact: $FIRMWARE_DIR/.pio/build/esp32s3_enhanced/firmware.bin"
    else
        status_line "${COLOR_RED}" "✗ Firmware build failed"
    fi
    popd >/dev/null
    echo
}

upload_firmware() {
    if [ "$PLATFORMIO_AVAILABLE" = false ] || [ "$SKIP_FIRMWARE" = true ]; then
        status_line "${COLOR_YELLOW}" "Firmware upload skipped"
        echo
        return
    fi

    if [ ! -e /dev/ttyUSB0 ]; then
        status_line "${COLOR_YELLOW}" "Serial device not detected; skipping firmware upload"
        echo
        return
    fi

    read -r -p "Upload firmware to ESP32-S3 now? (y/N) " reply
    if [[ "$reply" = "y" || "$reply" = "Y" ]]; then
        pushd "$FIRMWARE_DIR" >/dev/null
        if pio run -e esp32s3_enhanced -t upload; then
            status_line "${COLOR_GREEN}" "✓ Firmware uploaded successfully"
        else
            status_line "${COLOR_RED}" "✗ Firmware upload failed"
        fi
        popd >/dev/null
    fi
    echo
}

start_orchestrator() {
    status_line "${COLOR_YELLOW}" "Launching Living Library orchestrator..."
    activate_venv
    pushd "$PROJECT_ROOT" >/dev/null
    python orchestrator.py --config "$CONFIG_PATH"
    popd >/dev/null
}

start_individual_agent() {
    echo -e "${COLOR_YELLOW}Select agent to start:${COLOR_RESET}"
    cat <<'MENU'
  1) SIGPRINT Monitor Agent
  2) Limnus Ledger Agent
  3) Garden Narrative Agent
  4) All agents via orchestrator
  5) Cancel
MENU
    read -r choice
    activate_venv
    pushd "$PROJECT_ROOT" >/dev/null
    case "$choice" in
        1) python agents/sigprint/monitor_agent.py ;;
        2) python agents/limnus/ledger_agent.py ;;
        3) python agents/garden/narrative_agent.py ;;
        4) python orchestrator.py --config "$CONFIG_PATH" ;;
        *) status_line "${COLOR_YELLOW}" "Cancelled" ;;
    esac
    popd >/dev/null
}

run_tests() {
    status_line "${COLOR_YELLOW}" "Running import smoke tests..."
    activate_venv
    python - <<'PY'
from protos import agents_pb2
from protos import agents_pb2_grpc
from agents.sigprint.monitor_agent import SIGPRINTMonitorAgent
from agents.limnus.ledger_agent import LimnusLedgerAgent
from agents.garden.narrative_agent import GardenNarrativeAgent
print("Imports OK")
PY
    status_line "${COLOR_GREEN}" "✓ Module imports succeeded"
    echo
}

clean_reset() {
    read -r -p "This will delete data/logs/generated files. Continue? (y/N) " response
    if [[ "$response" != "y" && "$response" != "Y" ]]; then
        return
    fi

    rm -rf "$DATA_DIR" "$LOGS_DIR" "$NARRATIVES_DIR" "$PATTERNS_DIR" "$EXPORTS_DIR"
    rm -f "$PROJECT_ROOT"/protos/agents_pb2*.py
    rm -rf "$PROJECT_ROOT"/__pycache__ "$PROJECT_ROOT"/agents/**/__pycache__ 2>/dev/null || true
    status_line "${COLOR_GREEN}" "✓ Workspace cleaned"
    echo
}

show_menu() {
    echo -e "${COLOR_YELLOW}Choose an operation:${COLOR_RESET}"
    cat <<'MENU'
  1) Full deployment (recommended first run)
  2) Start orchestrator
  3) Start individual agent
  4) Build firmware only
  5) Upload firmware
  6) Run smoke tests
  7) Clean and reset
  8) Exit
MENU
    echo -n "Choice: "
}

full_deployment() {
    print_header
    check_prerequisites
    create_directories
    setup_python_environment
    link_monorepo_packages
    generate_protobuf
    build_firmware
    run_tests
    upload_firmware
    start_orchestrator
}

bootstrap_only() {
    print_header
    check_prerequisites
    create_directories
    setup_python_environment
}

###############################################################################
# Command-line handling
###############################################################################

while [[ $# -gt 0 ]]; do
    case "$1" in
        --bootstrap-only)
            bootstrap_only
            exit 0
            ;;
        --full)
            full_deployment
            exit 0
            ;;
        --orchestrator)
            check_prerequisites
            setup_python_environment
            link_monorepo_packages
            generate_protobuf
            start_orchestrator
            exit 0
            ;;
        --skip-firmware)
            SKIP_FIRMWARE=true
            shift
            ;;
        --clean)
            clean_reset
            exit 0
            ;;
        --help|-h)
            cat <<EOF
Living Library SIGPRINT Deployment Script

Usage:
  $0 [--full] [--orchestrator] [--skip-firmware] [--clean]

Options:
  --full           Run full deployment pipeline
  --orchestrator   Launch orchestrator directly
  --skip-firmware  Skip PlatformIO build/upload steps
  --clean          Remove generated data/logs/protobuf outputs
  --help           Show this message
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Interactive menu
print_header
check_prerequisites
create_directories

while true; do
    show_menu
    read -r menu_choice
    echo
    case "$menu_choice" in
        1)
            full_deployment
            ;;
        2)
            setup_python_environment
            link_monorepo_packages
            generate_protobuf
            start_orchestrator
            ;;
        3)
            setup_python_environment
            link_monorepo_packages
            generate_protobuf
            start_individual_agent
            ;;
        4)
            build_firmware
            ;;
        5)
            upload_firmware
            ;;
        6)
            setup_python_environment
            generate_protobuf
            run_tests
            ;;
        7)
            clean_reset
            ;;
        8)
            status_line "${COLOR_GREEN}" "Goodbye!"
            exit 0
            ;;
        *)
            status_line "${COLOR_RED}" "Invalid selection"
            ;;
    esac

    echo
    read -r -p "Press Enter to continue..." _
    echo
done
