#!/usr/bin/env bash
# ==============================================================================
# TECHNOREBOOT — Deterministic Disaster Recovery and Bootstrap Entrypoint
# Stage 07E-R1: New Server Bootstrap and Disaster Recovery
#
# Target Scenario:
# - Fresh Debian 12 (Bookworm) or Ubuntu server / VM
# - Git repository cloned to /tbootit (or current directory)
# - One valid Technoreboot backup ZIP (e.g. in ./backups/ or specified as $1)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=============================================================================="
echo "  TECHNOREBOOT — NEW SERVER BOOTSTRAP & DISASTER RECOVERY"
echo "  Repository Root: ${REPO_ROOT}"
echo "=============================================================================="

# 1. Preflight OS environment
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    echo "[PREFLIGHT] Operating System: ${NAME:-Linux} ${VERSION_ID:-}"
else
    echo "[PREFLIGHT] Operating System: Generic Linux / Unix"
fi

# 2. Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 is required but not installed." >&2
    echo "        Run: sudo apt-get update && sudo apt-get install -y python3 python3-pip" >&2
    exit 1
fi
echo "[PREFLIGHT] Python: $(python3 --version)"

# 3. Check Python cryptography package
if ! python3 -c "import cryptography" &>/dev/null; then
    echo "[INFO] Python cryptography package not found. Attempting automatic installation..."
    if command -v apt-get &>/dev/null && [[ $EUID -eq 0 ]]; then
        apt-get update -qq && apt-get install -y -qq python3-cryptography || pip3 install cryptography
    else
        pip3 install --quiet cryptography || true
    fi
    if ! python3 -c "import cryptography" &>/dev/null; then
        echo "[ERROR] 'cryptography' library could not be imported." >&2
        echo "        Install it with: sudo apt-get install -y python3-cryptography" >&2
        exit 1
    fi
fi
echo "[PREFLIGHT] Python cryptography library: OK"

# 4. Check Docker & Docker Compose
if ! command -v docker &>/dev/null; then
    echo "[WARN] docker command not found on PATH. If this is a dry-run/testing harness,"
    echo "       use --skip-containers flag. Otherwise, install Docker Engine."
fi

# 5. Check repository structure
if [[ ! -f "${REPO_ROOT}/docker-compose.yml" ]]; then
    echo "[ERROR] docker-compose.yml not found in ${REPO_ROOT}." >&2
    echo "        Make sure you run this script from within a cloned Technoreboot repository." >&2
    exit 1
fi
echo "[PREFLIGHT] Repository structure: OK"

# 6. Execute disaster recovery engine
echo "[BOOTSTRAP] Handing off to deterministic bootstrap engine..."
exec python3 "${REPO_ROOT}/scripts/bootstrap_restore.py" "$@"
