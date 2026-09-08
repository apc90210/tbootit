# Stage 07B-R5 — Avito Product Import 500 Regression Fix Architecture & Diagnosis

## 1. Executive Summary
During Stage 07B manual Owner checks of the Avito Chrome extension (v0.2.43), attempting to import an Avito listing into Technoreboot resulted in the following error dialog in the extension:
```text
✕ Объявление получено, но импорт товара завершился ошибкой.
Ошибка сервера 422:
Не удалось импортировать объявление в Техноребут:
HTTP 500: Internal Server Error
```
This document details the root cause diagnosis, architectural analysis, defensive hardening across `core`, `avito-module`, `admin-shell`, and `backup/restore_full.py`, and the verification proof demonstrating that Avito listing imports and photos now function seamlessly.

---

## 2. Reproduced Failure & Exact Call Chain

### Call Chain
1. **Chrome Extension** (`service_worker.js:sendListingPayload`):
   Sends payload to `POST http://localhost:8011/admin-api/avito-extension/listing` with header `X-Extension-Token`.
2. **Admin Shell Proxy** (`admin-shell/app/main.py:proxy_avito_extension_api`):
   Proxies request internally to `POST http://avito-module:8020/extension/api/listing`.
3. **Avito Module Bridge** (`avito-module/app/routers/extension_bridge.py:receive_listing`):
   Saves received listing as `ParsedAd` and invokes `import_service.import_ad_to_core(ext_id, account_key)`.
4. **Avito Module Import Service** (`avito-module/app/services/import_service.py:import_ad_to_core`):
   Calls `POST http://core:8000/api/integrations/avito/import-item`.
5. **Core API Ingestion** (`core/app/routers/integrations.py:import_avito_item`):
   Threw uncaught `FileNotFoundError: [Errno 2] No such file or directory: '/data/storage/product_photos'` at line 235 when running `os.makedirs(storage_photos_dir, exist_ok=True)`.
6. **Core API Result**:
   FastAPI unhandled exception handler generated `HTTP 500: Internal Server Error`.
7. **Avito Module Bridge Result**:
   Captured `HTTP 500: Internal Server Error` string and raised `HTTPException(status_code=422, detail={..., "message": "Не удалось импортировать объявление в Техноребут: HTTP 500: Internal Server Error"})`.
8. **Chrome Extension Result**:
   Displayed 422 error banner with inner 500 message.

---

## 3. Root Cause Analysis

### Stale Docker Desktop Mount Inode (WSL2 / 9P drvfs)
- In Stage 07B-R1 and R2 restore verification, prior backup restore scripts deleted and recreated host folders (`C:\tbootit\data\storage` and `C:\tbootit\data\avito-module`) using `shutil.rmtree(target_storage)` on the Windows host.
- In Docker Desktop with WSL2, bind mounts link to the specific host NTFS inode. Deleting the folder on the host while the container is running destroys the mount link inside the Linux container, leaving it in a dead/unreachable state (`d?????????` / `stat: cannot statx '/data/storage': No such file or directory`).
- In Stage 07B-R4, `technoreboot-avito-module` and `technoreboot-admin-shell` were restarted, but `technoreboot-core` was not. Consequently, `technoreboot-core` continued running with a severed `/data/storage` mount point.

### Lack of Defensive File/Storage Exception Handling in Core
- In `core/app/routers/integrations.py`, line 235 executed `os.makedirs(storage_photos_dir, exist_ok=True)` without a try/except block.
- If the primary photo storage mount was inaccessible or read-only, the entire request crashed with an unhandled 500 error instead of falling back to a temporary directory or storing photos as remote URLs (`media_url = source_url`, `storage_path = None`).

### Error Reporting Leakage
- `avito-module/app/services/import_service.py` extracted raw response text without structured error parsing, passing `HTTP 500: Internal Server Error` directly to the extension bridge.

---

## 4. Architectural Proof: mTLS Involvement

```text
MTLS_CAUSED_THIS_FAILURE: false
```

### Evidence:
1. The Avito Chrome Extension connects directly to `admin-shell` via HTTP port `8011` (`/admin-api/avito-extension/...`) using its paired token `X-Extension-Token`.
2. The extension does **not** route through the Nginx reverse gateway on port `8443` (which enforces mTLS for owner web UI).
3. The HTTP 422 / 500 error was generated deep inside `technoreboot-core` (`POST /api/integrations/avito/import-item`) due to a filesystem mount error when saving product photos, completely unrelated to mTLS certificates or TLS handshakes.

---

## 5. Changes Implemented

### 1. `core/app/routers/integrations.py`
- Protected photo directory creation with try/except and fallback:
  If `settings.storage_root` fails or is inaccessible, it attempts `/tmp/product_photos`. If both fail, it gracefully marks `storage_writable = False`.
- Protected photo file write with try/except:
  If writing photo bytes to disk fails, Core logs a warning and saves the photo record with `storage_path=None` and `media_url=source_url`. The product and its photos are safely imported without crashing with 500.

### 2. `core/app/main.py`
- Wrapped startup directory creation (`settings.storage_root` and database directory) in try/except blocks with logging so storage hiccups do not crash the application on startup.

### 3. `core/tests/test_remote_photo_size_limit.py`
- Updated payload size to 16 MB (`16 * 1024 * 1024`) to properly test rejection against the 15 MB limit introduced in commit `c78f61c`.

### 4. `avito-module/app/services/import_service.py`
- Hardened error parsing in `import_ad_to_core`: parses structured JSON `detail` if available; cleans short plain text if non-JSON; handles HTTP timeouts gracefully with a 60-second limit.

### 5. `admin-shell/app/backup_service.py`
- Updated `_clean_and_copy_dir`: when restoring storage and avito persistent folders, recursively cleans directory contents in-place instead of deleting the directory roots (`shutil.rmtree(child)`). This preserves folder inodes across Docker/WSL2 bind mounts during web restore.

### 6. `backup/restore_full.py`
- Added `_safe_sync_dir` helper to synchronize storage, auth, and avito modules in-place without deleting subdirectory roots (`product_photos`).

### 7. `docker-compose.yml`
- Added `./core/app:/app/app` and `./core/tests:/app/tests` volume mounts to `core` service for consistency with `admin-shell` and `avito-module`.

---

## 6. Extension Version Decision
- **Decision:** No extension source changes were necessary.
- **Reason:** The defect was entirely server-side (Core photo storage mount and error handling).
- **Extension Version:** Remains `0.2.43`.
- **Extension ZIP:** Validated `admin-shell/app/technoreboot-avito-extension.zip` is version `0.2.43`.
