#!/usr/bin/env bash
# Technoreboot — Safe Code-Only Production Update Script
# Stage 08D-R1R1: Canonical Production Model
#
# INVARIANTS:
# 1. Updates source code and container images only.
# 2. NEVER touches, resets, overwrites, or restores live business data.
# 3. Requires production data guard /srv/technoreboot/data/.technoreboot_production_data.
# 4. Refuses execution if any data restore or local sync operation is attempted.
# 5. Creates automatic pre-update backup of production state.
# 6. Validates business count preservation across container recreations.
# 7. Automatically rolls back code if containers fail healthchecks.

set -euo pipefail

APP_DIR="/srv/technoreboot/app"
DATA_DIR="/srv/technoreboot/data"
SECRETS_DIR="/srv/technoreboot/secrets"
DEPLOY_DIR="${APP_DIR}/deploy/production"
COMPOSE_FILE="${DEPLOY_DIR}/docker-compose.prod.yml"
ENV_FILE="${SECRETS_DIR}/production.env"
GUARD_FILE="${DATA_DIR}/.technoreboot_production_data"

TARGET_REF="${1:-origin/main}"

echo "================================================================="
echo "TECHNOREBOOT: Code-Only Production Deployment"
echo "Target Ref: ${TARGET_REF}"
echo "Started at: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "================================================================="

# 1. Production environment validation
if [ ! -d "${DATA_DIR}" ]; then
    echo "ERROR: Data directory ${DATA_DIR} does not exist. Aborting." >&2
    exit 1
fi

if [ ! -f "${GUARD_FILE}" ]; then
    echo "ERROR: Production data guard ${GUARD_FILE} is missing! Refusing to run." >&2
    exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
    echo "ERROR: Secrets environment file ${ENV_FILE} is missing! Aborting." >&2
    exit 1
fi

if [ ! -f "${COMPOSE_FILE}" ]; then
    echo "ERROR: Production compose file ${COMPOSE_FILE} is missing! Aborting." >&2
    exit 1
fi

# Hard prohibition against data restore
for forbidden_arg in "restore" "bootstrap" "wipe" "reset" "sync-from-local"; do
    for arg in "$@"; do
        if [[ "${arg}" == *"${forbidden_arg}"* ]]; then
            echo "SECURITY VIOLATION: Forbidden keyword '${forbidden_arg}' detected in deploy invocation. Aborting." >&2
            exit 1
        fi
    done
done

# 2. Record pre-update git commit
PRE_GIT_COMMIT=$(git -C "${APP_DIR}" rev-parse HEAD)
echo "[1/8] Current Git Commit: ${PRE_GIT_COMMIT}"

# 3. Record pre-update business state
echo "[2/8] Recording pre-update business invariants..."
DB_PATH="${DATA_DIR}/db/technoreboot.db"
PRE_DB_SHA256="NONE"
if [ -f "${DB_PATH}" ]; then
    PRE_DB_SHA256=$(sha256sum "${DB_PATH}" | awk '{print $1}')
fi

PRE_COUNTS=$(python3 -c "
import sqlite3
from pathlib import Path
db_p = Path('${DB_PATH}')
if not db_p.exists():
    print('PRODUCTS=0 SALES=0 REPAIRS=0 PHOTOS=0 LISTINGS=0')
else:
    conn = sqlite3.connect(str(db_p))
    cur = conn.cursor()
    counts = {}
    for tbl, key in [('products', 'PRODUCTS'), ('sales', 'SALES'), ('repair_orders', 'REPAIRS'), ('product_photos', 'PHOTOS'), ('product_external_listings', 'LISTINGS')]:
        try:
            cnt = cur.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
        except Exception:
            cnt = 0
        counts[key] = cnt
    conn.close()
    print(' '.join(f'{k}={v}' for k, v in counts.items()))
")
echo "  Pre-update counts: ${PRE_COUNTS}"
echo "  Pre-update DB SHA256: ${PRE_DB_SHA256}"

# 4. Mandatory Pre-update safety backup
echo "[3/8] Creating pre-update safety backup..."
BACKUP_NAME=$(python3 -c "
import os, sys
sys.path.insert(0, '${APP_DIR}/admin-shell')
os.environ['DATA_DIR'] = '${DATA_DIR}'
os.environ['AUTH_STORAGE_DIR'] = '${DATA_DIR}/auth'
from app.backup_service import create_backup
zip_path, _ = create_backup()
print(zip_path.name)
")
echo "  Pre-update backup created: ${BACKUP_NAME}"

# 5. Fetch & update source code
echo "[4/8] Updating source code to ${TARGET_REF}..."
git -C "${APP_DIR}" fetch origin
git -C "${APP_DIR}" checkout -f "${TARGET_REF}"
NEW_GIT_COMMIT=$(git -C "${APP_DIR}" rev-parse HEAD)
echo "  Updated to Git Commit: ${NEW_GIT_COMMIT}"

# 6. Validate compose configuration
echo "[5/8] Validating docker compose configuration..."
COMPOSE_CFG=$(cd "${DEPLOY_DIR}" && docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" config)

# Verify zero host port leaks for internal services
for forbidden_port in "8000:" "8010:" "8020:" "8030:" "8040:" "6080:"; do
    if echo "${COMPOSE_CFG}" | grep -q "${forbidden_port}"; then
        echo "SECURITY ERROR: Port ${forbidden_port} exposed on host in compose config! Rolling back code..." >&2
        git -C "${APP_DIR}" checkout -f "${PRE_GIT_COMMIT}"
        exit 1
    fi
done
echo "  Compose config OK (no internal ports exposed)."

# 7. Build containers from source
echo "[6/8] Building container images from source..."
if ! (cd "${DEPLOY_DIR}" && docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build); then
    echo "BUILD FAILURE: Docker build failed! Rolling back code..." >&2
    git -C "${APP_DIR}" checkout -f "${PRE_GIT_COMMIT}"
    exit 1
fi

# 8. Recreate containers
echo "[7/8] Recreating containers..."
if ! (cd "${DEPLOY_DIR}" && docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --remove-orphans); then
    echo "DEPLOY FAILURE: Docker up failed! Rolling back code..." >&2
    git -C "${APP_DIR}" checkout -f "${PRE_GIT_COMMIT}"
    (cd "${DEPLOY_DIR}" && docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build)
    (cd "${DEPLOY_DIR}" && docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --remove-orphans)
    exit 1
fi

# Wait for healthy services
echo "  Waiting for all 6 containers to become healthy..."
SERVICES=("core" "inventory-sales" "repairs" "avito" "admin-shell" "gateway")
ALL_HEALTHY=0
for attempt in $(seq 1 45); do
    sleep 2
    PS_OUTPUT=$(docker ps --format '{{.Names}} {{.Status}}')
    MATCH_COUNT=0
    for s in "${SERVICES[@]}"; do
        CNAME="technoreboot-prod-${s}"
        if echo "${PS_OUTPUT}" | grep -q "${CNAME}" && echo "${PS_OUTPUT}" | grep "${CNAME}" | grep -q "(healthy)"; then
            MATCH_COUNT=$((MATCH_COUNT + 1))
        fi
    done
    if [ "${MATCH_COUNT}" -eq 6 ]; then
        ALL_HEALTHY=1
        echo "  All 6 containers healthy (attempt ${attempt})!"
        break
    fi
done

if [ "${ALL_HEALTHY}" -ne 1 ]; then
    echo "HEALTHCHECK TIMEOUT: One or more containers failed health check! Rolling back code..." >&2
    git -C "${APP_DIR}" checkout -f "${PRE_GIT_COMMIT}"
    (cd "${DEPLOY_DIR}" && docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build)
    (cd "${DEPLOY_DIR}" && docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --remove-orphans)
    exit 1
fi

# 9. Invariant Verification: Business Data Preservation
echo "[8/8] Verifying business data preservation..."
POST_COUNTS=$(python3 -c "
import sqlite3
from pathlib import Path
db_p = Path('${DB_PATH}')
if not db_p.exists():
    print('PRODUCTS=0 SALES=0 REPAIRS=0 PHOTOS=0 LISTINGS=0')
else:
    conn = sqlite3.connect(str(db_p))
    cur = conn.cursor()
    counts = {}
    for tbl, key in [('products', 'PRODUCTS'), ('sales', 'SALES'), ('repair_orders', 'REPAIRS'), ('product_photos', 'PHOTOS'), ('product_external_listings', 'LISTINGS')]:
        try:
            cnt = cur.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
        except Exception:
            cnt = 0
        counts[key] = cnt
    conn.close()
    print(' '.join(f'{k}={v}' for k, v in counts.items()))
")

echo "  Pre-update counts:  ${PRE_COUNTS}"
echo "  Post-update counts: ${POST_COUNTS}"

if [ "${PRE_COUNTS}" != "${POST_COUNTS}" ]; then
    echo "CRITICAL DATA CORRUPTION ERROR: Pre and post business counts do not match!" >&2
    echo "Pre:  ${PRE_COUNTS}" >&2
    echo "Post: ${POST_COUNTS}" >&2
    exit 1
fi

echo "================================================================="
echo "CODE-ONLY DEPLOYMENT COMPLETED SUCCESSFULLY"
echo "Code Updated: ${PRE_GIT_COMMIT:0:10} -> ${NEW_GIT_COMMIT:0:10}"
echo "Business Data Preserved: TRUE"
echo "All 6 Services Healthy: TRUE"
echo "Safety Backup: ${BACKUP_NAME}"
echo "Finished at: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "================================================================="
