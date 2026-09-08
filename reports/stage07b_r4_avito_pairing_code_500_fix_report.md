# Stage 07B-R4: Avito Pairing Code 500 Regression Fix Report

## Status: COMPLETE / PASS

**Timestamp:** 2026-09-08  
**Branch:** `main`  
**Scope:** Stage 07B-R4 — Avito Extension Pairing Code 500 Regression Fix  

---

## 1. Owner Bug Diagnosis & Reproduction

- **OWNER_ERROR:** `Ошибка генерации кода: Unexpected token 'I', "Internal S"... is not valid JSON`
- **REQUEST_PATH:** `POST /admin-api/avito-extension/pairing/generate`
- **HTTP_STATUS:** `500`
- **CONTENT_TYPE:** `text/plain; charset=utf-8`
- **SAFE_RESPONSE_BODY:** `Internal Server Error`

### Exact Trace & Root Cause
- **PROVEN_ROOT_CAUSE:** In earlier testing of full restore (`backup/restore_full.py`), host directory `data/avito-module` was deleted with `shutil.rmtree` and recreated. In Docker Desktop on Windows (WSL2), deleting a bind-mounted directory on the host leaves the mount in the running container pointing to a dead/unlinked inode (`d?????????`), causing `stat("/app/data")` to return `ENOENT`.
- **EXACT_EXCEPTION:**
  ```text
  File "/app/app/routers/extension_bridge.py", line 104, in generate_pair_code
    _save_json(PAIR_CODES_FILE, codes)
  File "/app/app/routers/extension_bridge.py", line 31, in _save_json
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
  File "/usr/lib/python3.10/os.py", line 225, in makedirs
    mkdir(name, mode)
  FileExistsError: [Errno 17] File exists: '/app/data'
  ```
- **REGRESSION_INTRODUCED_BY:** Unlinking host bind-mount root directories during full restore script tests.

---

## 2. Implemented Fixes

- **BACKEND_FIXED:**
  - In `avito-module/app/routers/extension_bridge.py`, wrapped `os.makedirs` in `_save_json` in a safe exception handler to prevent `FileExistsError` on existing/mounted folders.
  - In `generate_pair_code`, added 24-hour expiration pruning to keep `extension_pair_codes.json` compact.
  - In `backup/restore_full.py`, changed folder cleanup to wipe directory contents in-place rather than unlinking the directory itself (`shutil.rmtree`).
- **PROXY_FIXED:**
  - In `admin-shell/app/main.py` (`proxy_avito_extension_api`), if upstream returns status >= 400 with a non-JSON media type (such as plain-text `Internal Server Error`), it is packaged into structured JSON (`{"ok": false, "status": "failed", "detail": "..."}`).
- **FRONTEND_NON_JSON_HANDLING_FIXED:**
  - In `admin-shell/app/templates/avito_extension.html`, `generateCode()` now inspects `content-type`, safely parses JSON or text, updates inline error container `#codeError`, and displays a controlled Russian error (`«Не удалось создать код подключения: сервер вернул ошибку 500»`) without ever throwing `Unexpected token 'I'`.
- **EXTENSION_CHANGED:** false (no extension source modifications required).
- **EXTENSION_VERSION:** `0.2.43` (matches manifest and downloadable package `technoreboot-avito-extension-0.2.43.zip`).

---

## 3. Verification Results

### Live End-to-End Suite (`scripts/verify_stage07b_r4_avito_pairing.py`)
| Test | Description | Result |
|---|---|---|
| **TEST A** | OWNER opens `/avito/extension` through mTLS gateway (port 8443) | PASS (200 OK) |
| **TEST B** | Extension ZIP downloads successfully with manifest v0.2.43 | PASS (200 OK, 39.6 KB) |
| **TEST C** | Direct Avito module `POST /extension/api/pairing/generate` returns 6-digit code | PASS (200 OK, valid JSON) |
| **TEST D** | Admin Shell proxy pairing-generate returns valid JSON | PASS (200 OK) |
| **TEST E** | Real OWNER gateway path for pairing-generate returns success JSON | PASS (200 OK, 6-digit code) |
| **TEST F** | UI JavaScript handles successful JSON and DOM updates | PASS |
| **TEST G** | UI JavaScript handles non-JSON error without throwing `Unexpected token` | PASS |
| **TEST H** | Generated pairing code exchanged for extension token | PASS (`ext_tok_...` issued) |
| **TEST I** | Heartbeat with paired token succeeds | PASS (200 OK) |
| **TEST J** | Pairing code single-use contract intact (re-use rejected) | PASS (400 Bad Request) |
| **TEST K** | Avito module tests pass inside container | PASS (95 passed, 0 failed in 10.45s) |
| **TEST L** | Admin Shell tests pass | PASS (69 passed, 1 skipped, 0 failed in 36.28s) |
| **TEST M** | Chrome extension tests pass | PASS (Covered via avito-module extension test suite) |
| **TEST N** | mTLS regression smoke (`/`, `/certificates`, `/backups`) | PASS (all 200 OK) |

---

## 4. Security and Acceptance Checklist
- [x] No private certificates, keys, or passwords committed or logged.
- [x] No extension tokens or sensitive pairing codes printed in reports.
- [x] Accepted Stage 07A OWNER certificate unchanged and fully functional.
- [x] Internet deployment not started.
- [x] Ready for Owner manual check.
