# Stage 08D-R1R4-SYNC: Security Hardening + VDS→LOCAL Business Parity
**Architectural Specification and Implementation Record**

---

## 1. Overview & Architectural Principles

Stage 08D-R1R4-SYNC establishes the permanent operational boundary and security guarantees between Local Development and Production VDS:

1. **Code Direction:** `LOCAL DEV -> Git -> Production VDS`
   Deployments are strictly code-only via `/srv/technoreboot/app/deploy/production/update_code_only.sh origin/main`.
2. **Data Direction:** `Production VDS -> LOCAL DEV Replica`
   Production VDS is the single canonical source of truth for business data (products, sales, repairs, media, external listings).
3. **Data Protection:** `LOCAL -> VDS` business data sync is strictly prohibited. Production data guard file `/srv/technoreboot/data/.technoreboot_production_data` and deploy script invariants prevent data overwrites.

---

## 2. Implemented Capabilities & Security Hardening

### 2.1 Draft Lifecycle Hardening
- **Strict Transition Rules:**
  - Allowed: `in_stock -> draft`
  - Allowed: `draft -> in_stock`
  - Allowed: `draft -> archived`
  - Forbidden: `reserved -> draft` (HTTP 400)
  - Forbidden: `written_off -> draft` (HTTP 400)
  - Forbidden: `sold -> draft` (HTTP 400)
  - Forbidden: `archived -> draft` (HTTP 400)
  - Forbidden: `imported -> draft` (HTTP 400)
- **Direct Update & Batch Enforcement:**
  `full_update_product` (PUT `/api/products/{id}`) and `batch_update_products` (POST `/api/products/batch`) enforce `VALID_TRANSITIONS` directly, preventing update bypasses.
- **Contextual UI Actions:**
  - `in_stock`: Action button "Убрать в черновик"
  - `draft`: Action button "Вернуть в наличие"
  - Status dropdown excludes `draft` for non-in_stock items.

### 2.2 Seller RBAC Hardening
- **Route Authorization:**
  - `POST /admin-api/dev-reset`: USER -> 403 Forbidden; Production OWNER -> 403 Forbidden
  - `POST /admin-api/seed`: USER -> 403 Forbidden
  - `GET /certificates`: USER -> 403 Forbidden
  - `GET /backups`: USER -> 403 Forbidden
  - `DELETE /admin-api/avito/profiles/{key}`: USER -> 403 Forbidden
- **UI Visibility:**
  - Navigation tabs (Certificates, Backups, Avito Profiles management) hidden for USER role.

### 2.3 Hard-Delete Audit
- AST traversal across all route handlers in `core`, `admin-shell`, `inventory-sales-module`, `repairs-module`, and `avito-module`.
- Confirms `USER_ACCESSIBLE_HARD_DELETE_ROUTES = 0`.
- All deletions use soft-deletion / archiving (`archived`, `written_off`).

### 2.4 Avito Extension Permissions & Manifest (v0.2.56)
- Removed broad `https://*/*` from `manifest.json`.
- Specific explicit origins:
  - `https://144.31.50.134/*`
  - `https://localhost:8443/*`, `http://localhost:8011/*`, `http://localhost:8020/*`
  - `https://*.avito.ru/*`, `https://avito.ru/*`
  - Optional permissions declared via `optional_host_permissions: ["https://*/*", "http://*/*"]`.
- Version bumped to `0.2.56` across all extension files.
- Built zip archives:
  - `dist/technoreboot-avito-extension-0.2.56.zip`
  - `admin-shell/app/technoreboot-avito-extension-0.2.56.zip`

### 2.5 Permanent One-Way Sync Tool (`scripts/sync_vds_business_to_local.py`)
- Strictly enforces `VDS -> LOCAL`.
- Rejects `--push`, `--upload`, `--to-vds`, `--reverse`.
- Automatic local safety backup in `.local-recovery/pre_sync_*.zip`.
- Downloads and verifies SHA256 of VDS snapshot.
- Restores strictly business scope: `technoreboot.db`, `data/storage/` (photos), `data/avito-module/`.
- Local mTLS certificates, private keys, and secrets remain untouched.
- Verifies exact table count and DB hash parity.

---

## 3. Verification & Deployment Metrics

| Metric | Target | Result |
|---|---|---|
| Automated Tests | 100% Pass | PASS (106 tests across 4 suites) |
| VDS Deployment Commit | `1c7792db72` | PASS (`1c7792db7267bb3fd5e7b75b04a90edb73d37960`) |
| VDS Containers Healthy | 6/6 | PASS (core, admin-shell, avito, inventory-sales, repairs, gateway) |
| VDS Business Counts | Preserved | PRODUCTS=149 SALES=0 REPAIRS=0 PHOTOS=149 LISTINGS=149 |
| USER Security Proof | 403 on restricted | PASS (dev-reset, seed, certs, backups, avito delete) |
| OWNER Production Guard | 403 on dev-reset | PASS |
| Local Business Parity | Exact Match | PRODUCTS=149 SALES=0 REPAIRS=0 PHOTOS=149 LISTINGS=149 |
| Storage Parity | Exact Match | 149 photo files matching VDS |
