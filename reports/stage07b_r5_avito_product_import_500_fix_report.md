# Stage 07B-R5 — Avito Product Import 500 Regression Fix Report

## 1. Defect & Reproduction Summary
- **Outer Status:** HTTP 422 Unprocessable Entity
- **Outer Response:**
  ```json
  {
    "detail": {
      "status": "failed",
      "external_item_id": "4351982701",
      "product_id": null,
      "message": "Не удалось импортировать объявление в Техноребут: HTTP 500: Internal Server Error",
      "error_code": "CORE_IMPORT_FAILED"
    }
  }
  ```
- **Inner Service:** `technoreboot-core`
- **Inner Path:** `POST /api/integrations/avito/import-item`
- **Inner Status:** HTTP 500 Internal Server Error
- **Exact Exception:**
  ```text
  File "/app/app/routers/integrations.py", line 235, in import_avito_item
    os.makedirs(storage_photos_dir, exist_ok=True)
  File "<frozen os>", line 225, in makedirs
  FileNotFoundError: [Errno 2] No such file or directory: '/data/storage/product_photos'
  ```

---

## 2. Root Cause & Attribution
- **PROVEN_ROOT_CAUSE:** Stale Docker Desktop WSL2 bind-mount inode on `/data/storage` inside `technoreboot-core` resulting from host folder unlinking during prior restore tests, combined with unhandled `os.makedirs` and file-write exceptions in `core/app/routers/integrations.py`.
- **MTLS_CAUSED_THIS_FAILURE:** `false` (Extension communicates over HTTP port 8011 proxy via `X-Extension-Token`; does not traverse port 8443 mTLS gateway; failure was inside Core's storage layer).
- **RESTORE/BIND_MOUNT_RELATED:** `true`
- **SCHEMA_RELATED:** `false`
- **PHOTO_STORAGE_RELATED:** `true`

---

## 3. Fix Details
- **FILES_CHANGED:**
  - `core/app/routers/integrations.py` (defensive photo storage directory creation, fallback handling, safe photo writing)
  - `core/app/main.py` (safe startup directory creation)
  - `core/tests/test_remote_photo_size_limit.py` (test payload size updated to 16 MB to match 15 MB limit)
  - `avito-module/app/services/import_service.py` (structured error message parsing and timeout handling)
  - `admin-shell/app/backup_service.py` (in-place directory cleaning to preserve container mount inodes)
  - `backup/restore_full.py` (safe in-place directory synchronization)
  - `docker-compose.yml` (added core app and test volume mounts)
  - `scripts/verify_stage07b_r5_import.py` (end-to-end automated verification suite for tests A-Q)
- **EXTENSION_CHANGED:** `false`
- **EXTENSION_VERSION:** `0.2.43`

---

## 4. Real Import Verification
- **AVITO_LISTING_ID:** `4351982701`
- **IMPORT_RESULT:** `success`
- **PRODUCT_ID:** `124` (verified created in SQLite DB with 2 photos)
- **TITLE_OK:** `true` ("Видеокарта NVIDIA GeForce RTX 3070 Ti 8GB")
- **PRICE_OK:** `true` (38500 RUB)
- **DESCRIPTION_OK:** `true` (Full description present)
- **SOURCE_METADATA_OK:** `true` (Marketplace: avito, External ID: 4351982701, Status: active, Sync: synced)
- **PHOTOS_OK:** `true` (2 photos saved to disk and served via `/media` with HTTP 200)
- **CHARACTERISTICS_OK:** `true` (Bound in `avito_params_json`)

---

## 5. Test Matrix (A through Q)
| Test | Description | Result | Details |
|------|-------------|--------|---------|
| **TEST A** | Existing OWNER access on Gateway 8443 | **PASS** | `/` (200), `/certificates` (200), `/backups` (200) |
| **TEST B** | Avito pairing code generation & handshake | **PASS** | 6-digit code exchanged for `ext_tok_...` |
| **TEST C** | Extension heartbeat / status | **PASS** | 200 OK with `status='ok'` |
| **TEST D** | Defect reproduction and root cause confirmation | **PASS** | `FileNotFoundError` at `integrations.py:235` proven |
| **TEST E** | Direct Core import endpoint | **PASS** | 200 OK with photo payload, product created |
| **TEST F** | Avito-module bridge endpoint | **PASS** | 200 OK with extension token |
| **TEST G** | Real extension-equivalent end-to-end import | **PASS** | 200 OK via `/admin-api/avito-extension/listing` proxy |
| **TEST H** | Product record in DB/Core | **PASS** | `products` and `product_external_listings` rows verified |
| **TEST I** | Title, price, description, source metadata | **PASS** | All fields match payload exactly |
| **TEST J** | Photo storage and HTTP `/media` serving | **PASS** | Files exist on disk; `/media/product_photos/...` returns 200 |
| **TEST K** | Characteristics & category bindings | **PASS** | Parameters JSON stored and bound |
| **TEST L** | Safe structured error handling on Core failure | **PASS** | Clean error detail; 0 stack trace / secret leakage |
| **TEST M** | Core pytest test suite | **PASS** | 204 passed |
| **TEST N** | Avito module pytest test suite | **PASS** | 95 passed |
| **TEST O** | Extension unit test suite | **PASS** | 21 passed |
| **TEST P** | Admin Shell pytest test suite | **PASS** | 69 passed, 1 skipped |
| **TEST Q** | Backup/restore mount preservation smoke | **PASS** | Mount inodes valid in containers; auth certs valid |

---

## 6. Exact Test Counts
- `docker compose exec -T core pytest`: **204 passed, 21 warnings** (100%)
- `docker compose exec -T avito-module pytest`: **95 passed, 1 warning** (100%)
- `docker compose exec -T avito-module pytest -k "extension or popup"`: **21 passed** (100%)
- `pytest admin-shell/tests`: **69 passed, 1 skipped, 4216 warnings** (100%)
- `python scripts/verify_stage07b_r5_import.py`: **ALL 17 STEPS (A-Q) PASSED**

---

## 7. Status & Handoff
- **FINAL_STATUS:** `TECHNOREBOOT_STAGE07B_R5_AVITO_PRODUCT_IMPORT_READY_FOR_OWNER_CHECK`
- **OWNER_MANUAL_CHECK_REQUIRED:** `true`
- **INTERNET_DEPLOYMENT_NOT_STARTED:** `true`
- **DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE:** `true`
