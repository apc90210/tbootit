# Stage 07B-R5-R1 — Persistent Photo Storage Safety Fix Report

## Unsafe Behavior Removed
- **TMP_PHOTO_FALLBACK_REMOVED:** YES (`/tmp/product_photos` fallback completely eliminated from codebase)
- **REMOTE_URL_ONLY_REPORTED_AS_LOCAL_SUCCESS:** NO (remote-only references leave `photos_imported=0` and `storage_path=None`)
- **PERSISTENT_STORAGE_REQUIRED_FOR_LOCAL_PHOTO_SUCCESS:** YES (`photos_imported` increment strictly guarded by physical file existence and non-zero size verification in `/data/storage/product_photos`)

## Failure Contract
- **STORAGE_UNAVAILABLE_BEHAVIOR:** Safe partial success allowed by existing contract; product import succeeds without HTTP 500/raw traceback.
- **STRUCTURED_ERROR_OR_WARNING:** Structured warning returned in `AvitoItemImportResponse.warnings`, and extension bridge reports `status="partial"` with message `Товар {ext_id} импортирован с предупреждением: фото не сохранены (ID: {product_id}).`

## Runtime Verification
- **TEST A (Normal persistent storage):** PASS (Photos saved under `/data/storage/product_photos`, survived container restart, served via `/media/...`)
- **TEST B (Simulated storage outage):** PASS (No `/tmp` fallback, no false `storage_path`, explicit partial warning, no HTTP 500)
- **TEST C (Backup verification):** PASS (Backup created contains the imported photo file and matches bytes)
- **TEST D (Web restore safety):** PASS (Storage mount inodes `/data/storage` and `/data/storage/product_photos` preserved, photo remains available)
- **TEST E (Extension import):** PASS (Real extension-equivalent import succeeded with photos persisted)
- **TEST F (Owner access):** PASS (`/` 200, `/certificates` 200, `/backups` 200)
- **TEST G (Avito pairing/heartbeat):** PASS (Pairing code, handshake, and heartbeat succeeded)
- **TEST H (Core tests):** PASS (209 passed, 0 failed in 20.30s)
- **TEST I (Avito module tests):** PASS (95 passed, 0 failed in 12.99s)

## Exact Test Results
- `core/tests/test_persistent_photo_storage_safety.py`: 5 passed
- `docker compose exec -T core pytest`: 209 passed, 21 warnings in 20.30s
- `docker compose exec -T avito-module pytest`: 95 passed, 1 warning in 12.99s
- `pytest admin-shell/tests`: 69 passed, 1 skipped, 4216 warnings in 40.72s
- `python scripts/verify_stage07b_r5_r1_storage.py`: All 9 steps (TEST A through TEST I) PASSED 100%

## Git
- **COMMIT:** `f7a1cd1ab36df28748fac82c30ab3a3dd3302857`
- **PUSH:** `origin/main` (synced)
- **HEAD_AFTER:** `f7a1cd1ab36df28748fac82c30ab3a3dd3302857`
- **FINAL_GIT_STATUS:** clean

## Owner Manual Check Instructions
Browser/extension only (no CMD / terminal commands for Owner):
1. Open one Avito listing containing photos.
2. Press `Передать в Техноребут`.
3. Confirm import succeeds in extension popup.
4. Open the imported product in Technoreboot.
5. Confirm photos display properly.
6. Refresh/reopen the product and confirm photos still display.

## Stage Status
- **FINAL_STATUS:** TECHNOREBOOT_STAGE07B_R5_R1_READY_FOR_OWNER_CHECK
- **OWNER_MANUAL_CHECK_REQUIRED:** true
- **INTERNET_DEPLOYMENT_NOT_STARTED:** true
- **DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE:** true
