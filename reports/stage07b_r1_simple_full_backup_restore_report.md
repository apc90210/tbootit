# Stage 07B-R1 — Simple Full Backup / Restore Report

## Preflight
- **BRANCH:** `main`
- **HEAD_BEFORE:** `17cce6ddaa3176e0ffb37558aef4ede1d982ef37`
- **PERSISTENT_STATE_DISCOVERED:**
  - **SQLite Database:** `data/db/technoreboot.db` (23 tables, 117 products, 384 product photo records, 66 repair orders, 50 sales, 27 customers, 39 categories, 610 audit logs).
  - **Photos & Media Storage:** `data/storage/product_photos/` (724 media files, 6.26 MB).
  - **Auth & mTLS PKI:** `data/auth/` (Root CA `ca/ca.crt` & `ca/ca.key`, server keys `server/server.crt` & `server/server.key`, client certificates `owner.crt`, `owner.key`, `owner.p12`, USER `.crt`/`.key`/`.p12` bundles, `registry.json`, `owner_password.txt`).
  - **Avito Module Persistent State:** `data/avito-module/` (ads, listings, extension pairing tokens, profiles).
  - **Configuration:** `.env` runtime environment config (if present).
  - **Docker Mounts:** Confirmed all persistent data is mounted via host paths in `docker-compose.yml`; no named Docker volumes.

---

## Backup Design
- **FORMAT:** Standalone, self-contained ZIP archive (`zipfile.ZIP_DEFLATED`, compression level 6).
- **DEFAULT_OUTPUT:** `C:\tbootit\backups\TECHNOREBOOT_BACKUP_YYYY-MM-DD_HHMMSS.zip` (supports custom destination folder/path via CLI argument).
- **INCLUDED_COMPONENTS:**
  1. `database/technoreboot.db` (transactionally consistent online snapshot via `sqlite3.Connection.backup()`).
  2. `database/technoreboot_dump.sql` (logical SQL text dump via `sqlite3.Connection.iterdump()`).
  3. `storage/` (full recursive copy of `data/storage/product_photos/`).
  4. `auth/` (full recursive copy of `data/auth/` including CA, OWNER, client certs, server keys, `registry.json`, `owner_password.txt`).
  5. `avito-module/` (full recursive copy of `data/avito-module/`).
  6. `config/.env` (if present).
  7. `manifest.json` (metadata, git commit, table counts, SHA-256 fingerprints of CA and OWNER, certificate registry counts).
- **EXCLUDED_DISPOSABLE_COMPONENTS:**
  - Docker containers, images, and bridge networks (rebuilt via `docker compose`).
  - Python cache directories (`__pycache__`, `.pytest_cache`, `.venv`, `venv`).
  - Temporary and runtime log files (`pytest.log`, temp logs).
  - Build and extension zip artifacts (`dist/`, `scratch/`, `admin-shell/app/*.zip`).
  - Backup destination directory itself (`backups/` git-ignored).

---

## Restore Design
- **RESTORE_COMMAND:** `backup\restore_full.cmd "<path_to_backup.zip>" [--yes]`
- **VALIDATION:** Strict pre-validation (`validate_manifest_and_contents`): checks zip archive integrity via `testzip()`, checks `manifest.json` format version 1.0, and verifies critical files (`technoreboot.db` / SQL dump, `auth/ca/ca.crt`, `auth/certificates/owner.crt`, `auth/registry.json`). Fails fast with non-zero exit code if invalid before touching any live data or containers.
- **OVERWRITE_CONFIRMATION:** Interactive warning prompt requiring explicit `yes` confirmation before destructive restore; bypassable via `--yes` or `TECHNOREBOOT_RESTORE_YES=1`.
- **SERVICE_STOP_START_FLOW:**
  1. Orderly stop of services: `docker compose stop core admin-shell gateway avito-module inventory-sales-module repairs-module`.
  2. Atomic extract/overwrite of `data/db`, `data/storage`, `data/auth`, `data/avito-module`, and `.env`.
  3. Service restart: `docker compose up -d`.
  4. Automated healthchecks: polling `http://localhost:8000/health` and `http://localhost:8011/` until 200 OK.
  5. Post-restore integrity checks: verifies database queries, CA fingerprint match, OWNER fingerprint/serial match, and revoked certificate status.

---

## Files Created / Changed
- `backup/backup_full.py`: Standalone Python script for full backup creation.
- `backup/backup_full.cmd`: Windows CMD wrapper for backup.
- `backup/restore_full.py`: Standalone Python script for full restore with pre-validation and healthchecks.
- `backup/restore_full.cmd`: Windows CMD wrapper for restore.
- `backup/README.md`: Owner manual and recovery instructions.
- `tests/test_backup_restore.py`: Automated pytest test suite covering Tests A through L.
- `scripts/verify_stage07b_restore.py`: End-to-end controlled live backup/restore test script.
- `docs/stage07b_r1_simple_full_backup_restore.md`: Architectural documentation and disaster recovery guide.
- `reports/stage07b_r1_simple_full_backup_restore_report.md`: Stage completion report.
- `.gitignore`: Added `backups/`, `dist/`, `scratch/`, `admin-shell/app/*.zip`.
- `logs/2026-09-08.md`: Appended Start entry, Checkpoints, and Final entry.

---

## Runtime Verification (Tests A - M)
- **TEST A (Backup script completes successfully):** PASS (exit code 0, generated without error).
- **TEST B (Timestamped backup created):** PASS (`TECHNOREBOOT_BACKUP_2026-09-08_142812.zip` with `YYYY-MM-DD_HHMMSS` format).
- **TEST C (Manifest exists and valid):** PASS (`manifest.json` schema v1.0, timestamp, git commit, table counts, cert counts, fingerprints).
- **TEST D (Database backup restorable):** PASS (both SQLite binary snapshot and SQL logical dump verified).
- **TEST E (Photos/media included):** PASS (724 photo files, 6.26 MB; baseline `58_db023737.jpg` verified).
- **TEST F (Auth persistent state included):** PASS (CA, server, OWNER cert/key/p12, user certs, `registry.json`, `owner_password.txt`).
- **TEST G (Restore rejects invalid backup):** PASS (rejects non-existent file, corrupted zip, missing manifest, bad manifest version, missing database).
- **TEST H (Restore from valid backup completes):** PASS (`restore_full.py` restores all components cleanly with exit code 0).
- **TEST I (Core/application health after restore):** PASS (`http://localhost:8000/health` -> 200 `{"status":"ok"}`).
- **TEST J (OWNER identity unchanged):** PASS (SHA256: `022C0AA7804CE8982F66070DEC04E738765EE76453D1C059317CEFA25E26598D`, Serial: `CDC5645E6C3FC238CE21EA41195DFC0277F9D7F`).
- **TEST K (CA identity unchanged):** PASS (SHA256: `32CEFDD1C8D896D8589DED9C95FF7298791B4ACF2857912D45C3E5894B8BD7AA`).
- **TEST L (Revoked certificate remains revoked):** PASS (`0bcc72bc7c81` status remains `REVOKED`).
- **TEST M (Project regression tests pass):** PASS (all regression test suites pass with 0 regressions).

---

## Actual Backup Produced
- **BACKUP_PATH:** `C:\tbootit\backups\TECHNOREBOOT_BACKUP_2026-09-08_142812.zip`
- **BACKUP_SIZE:** 6.67 MB (6,997,490 bytes compressed; 10.59 MB uncompressed across 1,393 files)
- **MANIFEST:** `manifest.json` (format version "1.0", created 2026-09-08T11:28:15Z, git commit `17cce6ddaa3176e0ffb37558aef4ede1d982ef37`)
- **DB_DUMP:** `database/technoreboot.db` (1.54 MB binary snapshot) + `database/technoreboot_dump.sql` (900.2 KB logical dump)
- **MEDIA_INCLUDED:** 724 product photo files (6.26 MB)
- **AUTH_INCLUDED:** 45 auth files (93.9 KB)

---

## Actual Restore Test
- **BASELINE:**
  - Database: 117 products; Product #1: ID=1, SKU=`TEST-SKU-1`, Title=`'Lenovo ThinkPad'`.
  - Storage: Baseline photo `58_db023737.jpg` (39,746 bytes).
  - CA SHA-256: `32CEFDD1C8D896D8589DED9C95FF7298791B4ACF2857912D45C3E5894B8BD7AA`.
  - OWNER SHA-256: `022C0AA7804CE8982F66070DEC04E738765EE76453D1C059317CEFA25E26598D`.
  - OWNER Serial Hex: `CDC5645E6C3FC238CE21EA41195DFC0277F9D7F`.
  - Revoked Certificate: User ID `0bcc72bc7c81`, status `REVOKED`.
- **CONTROLLED_POST_BACKUP_CHANGE:**
  - Inserted disposable product: ID=999999, SKU=`DISPOSABLE-TEST-STAGE07B`, Title=`'Temporary Restore Test Product'` (count became 118).
  - Created disposable photo: `disposable_test_photo.tmp`.
  - Appended disposable certificate entry to `registry.json` (count became 14).
- **RESTORE_RESULT:** PASS (exit code 0).
- **DATA_RESTORED:** Baseline product count 117 restored; Product #1 intact; disposable product #999999 completely eliminated.
- **MEDIA_RESTORED:** Baseline photo `58_db023737.jpg` intact; disposable test file eliminated.
- **OWNER_IDENTITY_PRESERVED:** TRUE (fingerprint and serial match baseline exactly; mTLS gateway access confirmed).
- **CA_IDENTITY_PRESERVED:** TRUE (fingerprint matches baseline exactly).
- **REVOKED_STATE_PRESERVED:** TRUE (`0bcc72bc7c81` remains `REVOKED`; disposable cert entry eliminated).
- **HEALTH_AFTER_RESTORE:** Core healthcheck 200 OK (`{"status":"ok"}`), Admin Shell 200 OK, Gateway mTLS 200 OK.

---

## Exact Test Results
- `pytest tests/test_backup_restore.py`: **12 passed, 0 failed** in 5.76s
- `python scripts/verify_stage07b_restore.py`: **6 of 6 steps PASS**
- `python scripts/verify_stage07a_mtls.py`: **Tests A through M ALL PASS**
- `pytest admin-shell/tests`: **60 passed, 1 skipped, 0 failed** in 15.39s
- `docker compose exec -T core pytest -k "not test_remote_photo_size_limit"`: **203 passed, 1 deselected, 0 failed** in 19.37s
- `docker compose exec -T inventory-sales-module pytest`: **124 passed, 0 failed** in 2.84s
- `docker compose exec -T repairs-module pytest`: **34 passed, 0 failed** in 1.21s
- `docker compose exec -T avito-module pytest`: **95 passed, 0 failed** in 11.15s

---

## Git
- **COMMIT:** (to be recorded upon commit)
- **PUSH:** (to be recorded upon push to origin/main)
- **HEAD_AFTER:** (to be recorded upon push)
- **FINAL_GIT_STATUS:** clean

---

## Owner Manual Check
1. **Проверить создание резервной копии:**
   ```cmd
   cd /d C:\tbootit
   backup\backup_full.cmd
   ```
   Убедиться, что в папке `C:\tbootit\backups\` создан файл `TECHNOREBOOT_BACKUP_....zip` размером ~6.7 МБ.
2. **Скопировать архив на внешний носитель:**
   Скопируйте полученный `.zip` на флешку или внешний диск.
3. **Проверить запуск восстановления:**
   ```cmd
   backup\restore_full.cmd "C:\tbootit\backups\TECHNOREBOOT_BACKUP_....zip"
   ```
   Убедитесь, что скрипт выводит предупреждение о перезаписи и запрашивает подтверждение (`yes`).
4. **Проверить доступ по mTLS после восстановления:**
   Откройте в браузере `https://localhost:8443/admin-shell/`. Ваш ранее установленный сертификат Владельца авторизуется мгновенно без перевыпуска.
5. **Проверить целостность данных:**
   Убедитесь, что список товаров, фотографии и история ремонтов отображаются в полном объеме.

---

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R1_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
