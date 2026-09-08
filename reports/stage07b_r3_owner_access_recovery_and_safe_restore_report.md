# Stage 07B-R3: OWNER Access Recovery and Safe Web Restore Report

## Status: COMPLETE / PASS

**Timestamp:** 2026-09-08  
**Branch:** `main`  
**Scope:** Stage 07B-R3 — OWNER Access Recovery and Safe Web Restore  

---

## 1. Incident Diagnosis and Proven Root Cause

During verification in Stage 07B-R2, the Owner attempted to access `https://127.0.0.1:8443` using the certificate installed in their browser (`Technoreboot OWNER`) and received an HTTP `403 Forbidden` error.

### Root Cause
1. **Unfiltered Auth Extraction:** In Stage 07B-R2, the web restore function `restore_backup()` in `admin-shell/app/backup_service.py` extracted all folders in the backup archive, including `auth/`, directly into the runtime `data/auth/` directory.
2. **CA Desynchronization:** An archive produced during earlier testing containing a divergent CA (fingerprint `5D24...`) was restored. This replaced `data/auth/ca.crt` on the filesystem.
3. **Nginx Client Cert Verification Failure:** The Nginx Gateway uses `data/auth/ca.crt` as `ssl_client_certificate`. When the Owner's browser presented the Stage 07A accepted certificate (Serial `CDC5645E6C3FC238CE21EA41195DFC0277F9D7F`, signed by Root CA `32CEFDD1...`), Nginx rejected the mTLS handshake with 403 Forbidden because the certificate issuer did not match the newly restored CA in `data/auth/ca.crt`.

---

## 2. Recovery of Accepted Stage 07A OWNER Identity

The exact accepted Stage 07A credentials were recovered from `TECHNOREBOOT_BACKUP_2026-09-08_142812.zip` and placed in `data/auth/`.

### Verified Cryptographic Parameters:
- **Root CA Subject:** `CN=Technoreboot Root CA, O=Technoreboot, C=RU`
- **Root CA SHA-256 Fingerprint:** `32CEFDD1C8D896D8589DED9C95FF7298791B4ACF2857912D45C3E5894B8BD7AA`
- **OWNER Subject:** `CN=Technoreboot OWNER, O=Technoreboot, C=RU`
- **OWNER Serial (Hex):** `CDC5645E6C3FC238CE21EA41195DFC0277F9D7F`
- **OWNER SHA-256 Fingerprint:** `022C0AA7804CE8982F66070DEC04E738765EE76453D1C059317CEFA25E26598D`
- **OWNER Role in Registry:** `"is_owner": true`, `"status": "ACTIVE"`
- **Total OWNERs:** Exactly 1.
- **New identities created:** 0. No new CA or OWNER certificates generated.
- **Manual re-import required by Owner:** NO. The existing browser certificate works immediately.

Live access through real Nginx Gateway (`https://127.0.0.1:8443`) using accepted OWNER client certificate:
- `GET /` -> 200 OK
- `GET /certificates` -> 200 OK
- `GET /backups` -> 200 OK

---

## 3. Safe Web Restore Policy Implementation

### Architectural Changes in `admin-shell/app/backup_service.py`
- Added `get_auth_dir()` helper to safely locate `data/auth/`.
- Updated `restore_backup(archive_path)`:
  - Validates ZIP archive and reads `manifest.json`.
  - Restores SQLite database (`technoreboot.db`) to `data/`.
  - Restores media/photos to `data/storage/`.
  - Restores Avito module persistent state if present.
  - **Explicitly skips extracting `auth/`** during online web restore, preserving live authentication intact.
  - Runs post-restore verification: verifies database queryability and ensures live CA and Owner certificates remain intact.
- Preserved disaster recovery packaging in `create_backup()`:
  - System backups continue to package `auth/` so that a fresh server bare-metal recovery can rebuild the identical cryptographic root in an emergency.

### UI Changes in `admin-shell/app/templates/backups.html`
- Updated restore warning message to explicitly state that access certificates are preserved during web restore:
  > «Восстановление заменит базу данных и изменяемые данные системы состоянием из резервной копии. Текущие сертификаты доступа при обычном онлайн-восстановлении сохраняются.»

---

## 4. Verification Results

### Live End-to-End Suite (`scripts/verify_stage07b_r3_safe_restore.py`)
Tested through real gateway on `https://127.0.0.1:8443`:
1. **TEST A — Existing OWNER identity:** PASS (Serial `CDC5645E6C3FC238CE21EA41195DFC0277F9D7F`, SHA256 `022C0AA7...`).
2. **TEST B — Live OWNER access via Gateway:** PASS (200 OK for `/`, `/certificates`, `/backups`).
3. **TEST C — No new identity:** PASS (CA `32CEFDD1...` unchanged, exactly 1 OWNER).
4. **TEST D — Create backup:** PASS (Valid ZIP created and downloaded).
5. **TEST E — Backup includes emergency auth:** PASS (`auth/` included in ZIP, source code excluded).
6. **TEST F — Normal restore preserves live auth:** PASS (User cert issued post-backup remains active and present after restore).
7. **TEST G — Business data restores:** PASS (Disposable product added post-backup is reverted on restore).
8. **TEST H — Media restores:** PASS (Disposable media file added post-backup is reverted on restore).
9. **TEST I — OWNER access works immediately after restore:** PASS (200 OK on all pages without certificate re-import).
10. **TEST J — Existing revoked state preserved:** PASS (Revoked certificate remains REVOKED after restore).
11. **TEST K — USER denied from owner pages:** PASS (403 Forbidden for `/certificates`, `/backups`, `/admin-api/backups/download`, `/admin-api/backups/restore`).
12. **TEST L — Corrupted archive rejected:** PASS (HTTP 400 Bad Request, live data untouched).

### Admin-Shell Unit Test Suite
- `pytest admin-shell/tests`: 70 passed, 0 failed (including new test `test_restore_preserves_live_auth`).

---

## 5. Security and Quality Checklist
- [x] No private keys or passwords in commit diffs, logs, or reports.
- [x] No backup ZIP archives tracked in git.
- [x] Tracked worktree clean.
- [x] Internet deployment not started.
- [x] Ready for Owner manual verification with existing browser certificate.
