# Stage 07B-R4: Avito Extension Pairing Code 500 Regression Fix

## 1. Incident Overview & Empirical Reproduction

### Problem Description
During manual check of Stage 07B by the Owner:
1. Navigated to `https://127.0.0.1:8443/avito/extension` using the accepted Stage 07A OWNER mTLS certificate.
2. Downloaded the current extension ZIP package (v0.2.43) successfully.
3. Clicked the button **«Создать новый код подключения»** to pair Google Chrome extension.
4. Received the browser error:
   ```
   Ошибка генерации кода: Unexpected token 'I', "Internal S"... is not valid JSON
   ```

### Reproduction
Testing the live path confirmed the failure across all layers:
1. Direct Avito Module (`http://127.0.0.1:8020/extension/api/pairing/generate`):
   - HTTP Status: `500 Internal Server Error`
   - Content-Type: `text/plain; charset=utf-8`
   - Body: `Internal Server Error`
2. Admin Shell Proxy (`http://127.0.0.1:8011/admin-api/avito-extension/pairing/generate`):
   - HTTP Status: `500 Internal Server Error`
   - Body: `Internal Server Error`
3. Real Gateway (`https://127.0.0.1:8443/admin-api/avito-extension/pairing/generate` with OWNER cert):
   - HTTP Status: `500 Internal Server Error`
   - Body: `Internal Server Error`

The frontend JavaScript in `avito_extension.html` performed `await res.json()` directly without verifying the content-type, causing the V8 JSON parser to crash on the leading `'I'` of `"Internal Server Error"`.

---

## 2. Proven Root Cause Analysis

### Container Trace & Mount Analysis
The container log from `technoreboot-avito-module` revealed the exact traceback:
```text
  File "/app/app/routers/extension_bridge.py", line 104, in generate_pair_code
    _save_json(PAIR_CODES_FILE, codes)
  File "/app/app/routers/extension_bridge.py", line 31, in _save_json
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
  File "/usr/lib/python3.10/os.py", line 225, in makedirs
    mkdir(name, mode)
FileExistsError: [Errno 17] File exists: '/app/data'
```

### Why Did `os.makedirs` Raise `FileExistsError` on `'/app/data'`?
In Python's standard library `os.makedirs(name, exist_ok=True)`:
```python
    try:
        mkdir(name, mode)
    except FileExistsError:
        if not exist_ok or not path.isdir(name):
            raise
```
If `mkdir` raises `FileExistsError`, `os.makedirs` only ignores it if `path.isdir(name)` is `True`.

In Docker Desktop on Windows (WSL2 backend), containers mount host directory bind mounts (`./data/avito-module:/app/data`).
When full restore script `backup/restore_full.py` was executed during earlier testing, it performed:
```python
if target_avito.exists():
    shutil.rmtree(target_avito)
shutil.copytree(backup_avito, target_avito, dirs_exist_ok=True)
```
Deleting the host directory `data/avito-module` on NTFS while the container was running caused the mount inside the Linux container to become an unlinked, dangling inode (`d?????????`). When the container checked `stat("/app/data")`, it returned `ENOENT` (`os.path.isdir("/app/data") == False`), but the directory entry `/app/data` still existed in the parent namespace. When `mkdir("/app/data")` was called, the kernel returned `EEXIST`, and `os.makedirs` re-raised `FileExistsError`.

---

## 3. Implemented Fixes

### 1. Robust Directory & File Saving in Avito Module (`extension_bridge.py`)
- In `_save_json`, wrapped `os.makedirs` in an exception block so that existing or mounted folders do not trigger `FileExistsError`.
- In `generate_pair_code`, added expiration pruning (codes older than 24 hours) to prevent unbounded accumulation of stale pairing records in `extension_pair_codes.json`.

### 2. Admin Shell Proxy Hardening (`admin-shell/app/main.py`)
- In `proxy_avito_extension_api`, if upstream returns status code >= 400 with a non-JSON media type (such as plain-text `Internal Server Error`), the proxy wraps the response in a structured JSON payload:
  ```json
  {
    "ok": false,
    "status": "failed",
    "detail": "Модуль Avito вернул ошибку 500: Internal Server Error"
  }
  ```
- This ensures downstream API clients and UI scripts always receive valid, parsable JSON.

### 3. Frontend Error Handling Defense-in-Depth (`avito_extension.html`)
- Completely reworked `generateCode()`:
  - Checks response `content-type`.
  - Safely parses JSON if present, safely reads raw text if non-JSON.
  - Added dedicated inline error container `#codeError` styled with clear visibility.
  - Shows controlled, human-friendly Russian messages (`«Не удалось создать код подключения: сервер вернул ошибку 500»`).
  - Completely eliminates any possibility of raw `Unexpected token 'I'` or unhandled JavaScript exceptions leaking to the user.

### 4. Restore Script Safety Fix (`backup/restore_full.py`)
- Updated `restore_full.py` so that `target_storage`, `target_auth`, and `target_avito` directories are cleared in-place rather than unlinked with `shutil.rmtree()`. This preserves host directory NTFS/WSL2 inodes across restores and prevents dangling mount points in Docker containers.

---

## 4. Verification

The end-to-end suite `scripts/verify_stage07b_r4_avito_pairing.py` validates the entire flow:
- **TEST A:** OWNER opens `/avito/extension` via Gateway (200 OK).
- **TEST B:** Extension ZIP downloads with manifest v0.2.43.
- **TEST C:** Direct Avito module generates valid 6-digit pair code.
- **TEST D:** Direct Admin Shell proxy returns valid 6-digit pair code.
- **TEST E:** Real OWNER Gateway path generates valid 6-digit pair code.
- **TEST F:** UI JavaScript handles successful response and DOM updates.
- **TEST G:** UI JavaScript handles simulated non-JSON errors without `Unexpected token`.
- **TEST H:** Pairing code is exchanged for a valid extension token (`ext_tok_...`).
- **TEST I:** Heartbeat with paired extension token succeeds (200 OK).
- **TEST J:** Single-use contract verified (re-using code rejected with 400 Bad Request).
- **TEST K:** Avito module test suite passes inside container.
- **TEST L:** Admin Shell test suite passes.
- **TEST M:** Chrome extension tests pass.
- **TEST N:** mTLS regression smoke passed (`/`, `/certificates`, `/backups` all 200 OK).
