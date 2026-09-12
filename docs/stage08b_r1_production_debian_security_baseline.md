# ТехноРебут — Stage 08B-R1: Production Debian Docker Security Baseline

## 1. Overview & Objectives

This document establishes the architecture, network exposure policy, authorization model, container security baseline, and persistence contracts for deploying ТехноРебут on a dedicated Debian 12 (Bookworm) Virtual Dedicated Server (VDS).

The target machine profile is a small VDS:
- **CPU:** 1 vCPU
- **RAM:** 2 GB
- **Storage:** 20 GB SSD
- **OS:** Debian 12 (Bookworm) minimal

The primary principle is:
> From a clean Git checkout on Debian, provide a deterministic production Docker Compose configuration that requires explicit secrets, persists all mutable data, exposes only the Gateway publicly, supports the existing mTLS OWNER/USER model, and is fully compatible with backup and disaster recovery.

---

## 2. Public Network Exposure Policy

### 2.1 Edge Gateway Isolation
In production, only the Gateway (`nginx:alpine`) container publishes ports to the host:
- **Port 80/tcp**: Plain HTTP, strictly for permanent redirection (`301 Moved Permanently`) to HTTPS. No business or static application content is served over HTTP.
- **Port 443/tcp**: Encrypted HTTPS with mandatory client mTLS authentication.

### 2.2 Internal Services Isolation
All internal services operate strictly on the internal Docker bridge network (`technoreboot-network`) with **zero** host ports published:
- `core`: port 8000 on container network only.
- `admin-shell`: port 8010 on container network only.
- `inventory-sales-module`: port 8030 on container network only.
- `repairs-module`: port 8040 on container network only.
- `avito-module`: port 8020 (API) and port 6080 (noVNC) on container network only.

Host socket checks verify that ports `8000`, `8010`, `8020`, `8030`, and `8040` are closed and unreachable from the public internet and external networks.

---

## 3. Hostname & Domain Configuration

Production routing decouples from development identifiers (`localhost`, `127.0.0.1`).
The production hostname is specified via the required environment variable:
```bash
TECHNOREBOOT_HOSTNAME=crm.technoreboot.ru
```
Nginx evaluates this variable via `envsubst` upon container startup using `NGINX_ENVSUBST_FILTER=TECHNOREBOOT_HOSTNAME`, ensuring all internal Nginx variables (`$host`, `$request_uri`, `$ssl_client_serial`, etc.) remain protected and untampered.

If `TECHNOREBOOT_HOSTNAME` is missing, production Compose validation fails fast.

---

## 4. Cryptographic Identity & mTLS Authentication Model

The production deployment preserves the cryptographic access model established in earlier stages:

### 4.1 Server TLS vs Client CA Decoupling
- **Server TLS Certificate & Key**:
  - `SERVER_TLS_CERT_PATH`: Public certificate chain (e.g. issued by Let's Encrypt or custom authority).
  - `SERVER_TLS_KEY_PATH`: Private key for the HTTPS server (permissions `0600`).
- **Client mTLS CA Certificate**:
  - `CLIENT_CA_CERT_PATH`: Technoreboot Root CA public certificate (`data/auth/ca/ca.crt`), used by Nginx (`ssl_client_certificate`) to verify incoming client certificates.

### 4.2 Subrequest Verification Architecture
1. Client connects to Gateway on port 443 presenting an X.509 client certificate.
2. Nginx verifies the certificate signature against `CLIENT_CA_CERT_PATH`.
3. Nginx initiates an internal subrequest to `admin-shell:8010/internal-auth/verify` forwarding client certificate metadata (`X-Client-Cert-Serial`, `X-Client-Cert-Fingerprint`, `X-Client-Cert-Verify`).
4. `admin-shell` validates the certificate against `data/auth/registry.json`:
   - If not signed by CA or not `SUCCESS`: HTTP 403 Forbidden.
   - If revoked: HTTP 403 Forbidden.
   - If active: returns HTTP 200 with headers `X-Auth-Subject` and `X-Auth-Is-Owner`.
5. Nginx forwards verified identity headers to internal services.

### 4.3 Role-Based Access Control (RBAC)
- **OWNER Certificates**: Full access to all routes:
  - Dashboard (`/`)
  - Inventory & Sales (`/inventory/products`, `/inventory/sales`)
  - Repairs (`/repairs/repairs`)
  - Avito Extension (`/avito/extension`)
  - Backup Management (`/backups`, `/admin-api/backups`)
  - Certificate Management (`/certificates`, `/admin-api/certificates`)
- **USER Certificates**: Access to operational workflows (Inventory, Sales, Repairs, Avito); access to `/backups` and `/certificates` is strictly blocked with HTTP 403 Forbidden.

---

## 5. Secrets Management & Fail-Fast Validation

Production containers disallow insecure and development default secrets:
- Insecure tokens: `dev-token`, `technoreboot_secret_cart_key_mvp`, `change-me`, `admin`, `password`, or empty strings.
- When `APP_ENV=production`, `core` and `inventory-sales-module` run Pydantic validators on startup:
  - `CORE_API_TOKEN`: Must be strong; startup aborts if default or missing.
  - `CART_SESSION_SECRET`: Must be strong; startup aborts if default or missing.
- Configuration template: `deploy/production/env.production.example` documents all required variables with zero real secrets.
- Real `.env` files are ignored by Git.

---

## 6. Persistent Data Contract

All mutable business state lives outside container layers under a single persistent data root:
```text
${TECHNOREBOOT_DATA_ROOT:-/srv/technoreboot/data}/
  ├── db/              # SQLite database (technoreboot.db)
  ├── storage/         # Product photos and uploaded media (/product_photos)
  ├── auth/            # PKI CA, certificates, and registry.json
  ├── avito-module/    # Avito pairing state, session data, and cookies
  └── backups/         # Full backup archives (ZIP)
```

No source code is bind-mounted in production (`docker-compose.prod.yml`). Containers run immutable application code copied during the Docker build stage.

---

## 7. Small-VDS Resource & Container Security Hardening

To guarantee reliable operation on a 1 vCPU / 2 GB RAM server:
1. **Bounded Docker Log Rotation**:
   Every service defines bounded JSON log rotation:
   ```yaml
   logging:
     driver: json-file
     options:
       max-size: "10m"
       max-file: "5"
   ```
   Maximum log disk usage per service is capped at 50 MB (total 300 MB across all 6 services).
2. **Container Security Flags**:
   - `no-new-privileges:true` enabled on all containers.
   - Zero privileged containers (`privileged: true` forbidden).
   - Zero Docker socket mounts (`/var/run/docker.sock` forbidden).
   - Zero host networking (`network_mode: host` forbidden).
3. **Health Checks & Automatic Restart**:
   - Every service defines an explicit healthcheck with intervals and retries.
   - All services define `restart: unless-stopped`.
4. **Development Tools Disabled**:
   - Uvicorn `--reload` flag is completely disabled in production.
   - Memory-heavy debugging processes are omitted.
