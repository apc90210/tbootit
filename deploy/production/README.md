# ТехноРебут — Production Debian Docker Configuration

## Overview

This directory (`deploy/production/`) contains the production deployment definition for ТехноРебут on a Debian 12 (Bookworm) VDS server.

## Architecture Principles

1. **Edge Gateway Isolation**:
   - Only the Nginx Gateway service publishes public ports on the host (`80/tcp` for permanent HTTPS redirect, `443/tcp` for HTTPS with mTLS).
   - All internal services (`core`, `admin-shell`, `inventory-sales-module`, `repairs-module`, `avito-module`) have **zero** host ports published. They communicate exclusively over the internal Docker bridge network (`technoreboot-network`).

2. **mTLS Authentication & Authorization**:
   - Gateway enforces client TLS verification (`ssl_verify_client optional` with subrequest authentication to `admin-shell:8010/internal-auth/verify`).
   - Certificates are checked against the active registry. Revoked certificates are rejected with `403 Forbidden`.
   - `/backups` and `/certificates` routes are strictly restricted to certificates with `OWNER` privileges. Normal `USER` certificates receive `403 Forbidden`.
   - The public server TLS certificate (`SERVER_TLS_CERT_PATH`) is decoupled from the internal client CA (`CLIENT_CA_CERT_PATH`).

3. **Persistent Data Contract**:
   - All mutable state resides outside the container writable layers under the configurable host root `TECHNOREBOOT_DATA_ROOT` (default: `/srv/technoreboot/data`):
     - `${TECHNOREBOOT_DATA_ROOT}/db` -> `/data/db` (SQLite database: `technoreboot.db`)
     - `${TECHNOREBOOT_DATA_ROOT}/storage` -> `/data/storage` (Product photos and media)
     - `${TECHNOREBOOT_DATA_ROOT}/auth` -> `/app/auth-data` (PKI CA, certificates, client registry)
     - `${TECHNOREBOOT_DATA_ROOT}/avito-module` -> `/app/data` (Avito pairing state and session data)
     - `${TECHNOREBOOT_DATA_ROOT}/backups` -> `/data/backups` (Backup archives)

4. **Fail-Fast Secret Validation**:
   - In production mode (`APP_ENV=production`), application services validate that critical tokens (`CORE_API_TOKEN`, `CART_SESSION_SECRET`) are present and not equal to development defaults (`dev-token`, `technoreboot_secret_cart_key_mvp`, `change-me`, `password`, etc.).
   - If any required variable is missing or insecure, the containers immediately fail fast on startup.

5. **Resource Boundedness (Small-VDS Profile)**:
   - Designed for 1 vCPU, 2 GB RAM, 20 GB disk.
   - Bounded Docker JSON log rotation configured on all services: `max-size: "10m"`, `max-file: "5"`.
   - Development reloaders (`--reload`) and debug tools are disabled.
   - All services define explicit health checks and `restart: unless-stopped`.

## Directory Structure

```text
deploy/
  production/
    docker-compose.prod.yml       # Production Compose definition
    env.production.example        # Environment variable template
    README.md                     # Architecture and operations documentation
    nginx/
      nginx.conf.template         # Gateway Nginx configuration template with envsubst
```

## Quick Start on Debian

Refer to [docs/production_debian_deployment.md](../../docs/production_debian_deployment.md) for the complete step-by-step deployment and rollback guide.
