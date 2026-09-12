# Stage 08D-R1R4-SYNC: Security Hardening + VDS→LOCAL Business Parity Final Audit Report

**Execution Date:** 2026-09-12  
**Target Environment:** Local (`C:\tbootit`) & Production VDS (`144.31.50.134`)  
**Deployment Head:** `1c7792db7267bb3fd5e7b75b04a90edb73d37960`  

---

## 1. Executive Summary

Stage 08D-R1R4-SYNC successfully accomplished all Owner requirements:
1. Fixed the draft lifecycle loop-hole: only `in_stock <-> draft` transitions are allowed. All invalid status transitions to draft are rejected.
2. Hardened seller RBAC: restricted endpoints reject USER credentials with HTTP 403 Forbidden; dev-reset is blocked in production even for OWNER.
3. Conducted hard-delete audit: verified zero user-accessible hard-delete routes exist (`USER_ACCESSIBLE_HARD_DELETE_ROUTES = 0`).
4. Tightened Avito extension permissions: removed broad wildcard `https://*/*`, added explicit host permissions, and bumped extension to `0.2.56`.
5. Successfully deployed code-only to production VDS without data modification.
6. Created permanent one-way sync tool `scripts/sync_vds_business_to_local.py` enforcing `VDS -> LOCAL` and refusing reverse sync.
7. Executed real parity sync from VDS snapshot to local workspace, achieving 100% data parity.

---

## 2. Invariant & Parity Matrix

| Parameter | Pre-Stage VDS | Post-Deploy VDS | Post-Sync Local | Match Status |
|---|---|---|---|---|
| Git HEAD | `7f78c3fd96` | `1c7792db72` | `1c7792db72` | EXACT MATCH |
| Products Count | 149 | 149 | 149 | EXACT MATCH |
| Sales Count | 0 | 0 | 0 | EXACT MATCH |
| Repairs Count | 0 | 0 | 0 | EXACT MATCH |
| Photos Count | 149 | 149 | 149 | EXACT MATCH |
| External Listings Count | 149 | 149 | 149 | EXACT MATCH |
| Media Storage Files | 149 | 149 | 149 | EXACT MATCH |
| Database SHA256 (compacted snapshot) | - | `6154c765a1...` | `6154c765a1...` | EXACT MATCH |
| Service Health | 6/6 Healthy | 6/6 Healthy | 6/6 Healthy | EXACT MATCH |

---

## 3. Draft Lifecycle Verification

All transitions tested via automated test suite `tests/test_stage08d_r1r4_seller_rbac.py`:
- `in_stock -> draft`: ALLOWED (HTTP 200)
- `draft -> in_stock`: ALLOWED (HTTP 200)
- `reserved -> draft`: REJECTED (HTTP 400)
- `written_off -> draft`: REJECTED (HTTP 400)
- `sold -> draft`: REJECTED (HTTP 400)
- `archived -> draft`: REJECTED (HTTP 400)
- `imported -> draft`: REJECTED (HTTP 400)

Direct update via `PUT /api/products/{id}` and `POST /api/products/batch` also enforce `VALID_TRANSITIONS`.

---

## 4. Non-Destructive Production Security Proof (VDS)

Tested live against production gateway `https://144.31.50.134:443`:
1. **USER Certificate (`75c53f564285`):**
   - `POST /admin-api/dev-reset` -> 403 Forbidden
   - `POST /admin-api/seed` -> 403 Forbidden
   - `GET /certificates` -> 403 Forbidden
   - `GET /backups` -> 403 Forbidden
   - `DELETE /admin-api/avito/profiles/audit_test_probe_key` -> 403 Forbidden
2. **OWNER Certificate (`owner`):**
   - `POST /admin-api/dev-reset` -> 403 Forbidden (Production guard active)
3. **Data Preservation:**
   - Pre-test and post-test counts on VDS: `PRODUCTS=149 SALES=0 REPAIRS=0 PHOTOS=149 LISTINGS=149`

---

## 5. One-Way Sync Tool Execution

- **Tool:** `scripts/sync_vds_business_to_local.py`
- **Reverse Sync Rejection:** `--push`, `--upload`, `--to-vds` rejected with exit code 1.
- **Pre-Sync Local Safety Backup:** `.local-recovery/pre_sync_20260912_134134.zip` (SHA256: `0384d5c0adac15c4b1b439f77498b8c0d7f7d5f3ce043cc5ae686affcf925f72`).
- **Snapshot Package:** `TECHNOREBOOT_BACKUP_2026-09-12_103935.zip` (SHA256: `da42a97bc3e52e0f3aeaf539b209dd032ffbd05c7e7025cebad44a898bd51192`).
- **Restored Components:**
  - `data/db/technoreboot.db` & `core/technoreboot.db`
  - `data/storage/` (149 photos)
  - `data/avito-module/` (62 state files)
- **Untouched Components:**
  - Local TLS certificates (`data/auth/ca/`, `data/auth/server/`, `data/auth/certificates/`, `data/auth/registry.json`).
  - Local configuration and secrets.
- **Verification Status:**
  - `SYNC_DIRECTION = VDS_TO_LOCAL`
  - `VDS_MUTATED_BY_SYNC = false`
  - `LOCAL_PARITY = True`

---

## 6. Avito Extension Packaging

- **Version:** `0.2.56`
- **Permissions Tightened:** Wildcard `https://*/*` removed from `manifest.json`.
- **Allowed Explicit Origins:**
  - `https://144.31.50.134/*`
  - `https://localhost:8443/*`, `http://localhost:8011/*`, `http://localhost:8020/*`
  - `https://*.avito.ru/*`, `https://avito.ru/*`
- **Artifacts:**
  - `dist/technoreboot-avito-extension-0.2.56.zip`
  - `admin-shell/app/technoreboot-avito-extension-0.2.56.zip`

---

## 7. Operational Readiness

All objectives are complete. Both VDS and Local environments are healthy, code is synchronized, live business data is canonical on VDS and replicated locally, and RBAC security is hardened.
