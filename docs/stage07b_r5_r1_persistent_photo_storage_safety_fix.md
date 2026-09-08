# Stage 07B-R5-R1 — Persistent Photo Storage Safety Fix

## 1. Overview and Architecture

During Stage 07B-R5, an issue where Docker bind-mounted directories severed host-container synchronization was resolved. However, the temporary fallback mechanism introduced in R5 allowed product photos to fall back to `/tmp/product_photos` or to report `photos_imported > 0` even when photos were only stored as remote URL references.

Stage 07B-R5-R1 eliminates all unsafe fallback behavior and enforces strict canonical photo persistence:
- Canonical persistent product photo directory: `/data/storage/product_photos`, mapped to host `./data/storage/product_photos`.
- `/tmp/product_photos` is never used as a successful persistence fallback.
- `photos_imported` is incremented **only** when physical bytes are successfully written to persistent storage and verified on disk (`os.path.isfile(path) and os.path.getsize(path) > 0`).
- If persistent storage is unavailable:
  - Product import safely completes without HTTP 500 error.
  - Photo rows record `storage_path = None` and `media_url = source_url`.
  - `photos_imported` remains `0`.
  - Structured warnings are included in `AvitoItemImportResponse.warnings`.
  - Avito extension bridge returns `status: "partial"` with user-friendly warning `Товар ... импортирован с предупреждением: фото не сохранены`.
- Startup and import-time health validation via `check_persistent_photo_storage()` with automated write/delete probe.
- Retains all bind-mount safety fixes from Stage 07B-R5 (in-place directory synchronization without deleting mount roots).

---

## 2. Key Code Modifications

### 2.1. Core Storage Module (`core/app/storage.py`)
- Added `get_product_photos_dir()` returning canonical path `/data/storage/product_photos`.
- Added `check_persistent_photo_storage() -> Tuple[bool, str]`:
  - Verifies target directory exists or creates it.
  - Verifies target is a directory.
  - Performs safe write/delete probe file (`.probe_<uuid>.tmp`).
  - Returns `(is_available, error_message)`.

### 2.2. Core Startup Validation (`core/app/main.py`)
- Runs `check_persistent_photo_storage()` on container startup.
- Logs explicit diagnostic message:
  - `[STORAGE] Canonical persistent photo storage verified: /data/storage/product_photos`
  - Or `[STORAGE ERROR] Canonical persistent photo storage check failed: ...`

### 2.3. Core Schemas (`core/app/schemas.py`)
- Added `warnings: List[str] = []` to `AvitoItemImportResponse`.

### 2.4. Core Integrations Router (`core/app/routers/integrations.py`)
- Removed all fallback references to `/tmp/product_photos`.
- Evaluates `check_persistent_photo_storage()` before photo processing.
- Strictly guards `photos_imported += 1` behind verified persistent file writes.
- When storage is unavailable or photos lack bytes, sets `storage_path = None`, `media_url = source_url`, appends to `warnings`, and keeps `photos_imported = 0`.
- Supports idempotent photo healing: if a product was previously imported during a storage outage and is re-imported when storage is restored, existing rows without `storage_path` are written to disk and healed.

### 2.5. Avito Module Extension Bridge (`avito-module/app/routers/extension_bridge.py`)
- When `result_status == "partial"` (photos were received but Core persisted 0 photos), user message explicitly states:
  `Товар {ext_id} импортирован с предупреждением: фото не сохранены (ID: {product_id}).`

---

## 3. Verification and Testing

Automated verification script `scripts/verify_stage07b_r5_r1_storage.py` validated:
1. **TEST A:** Persistent storage normal operation: photo saved to persistent storage, survived Core container restart, served via Core `/media/...` mount (200 OK).
2. **TEST B:** Simulated storage outage: temporary directory block caused Core to return `photos_imported=0` with warning, `storage_path=None`, no `/tmp` fallback, no raw 500 error; Avito bridge returned `status="partial"`.
3. **TEST C:** Backup creation: full system backup archive contains the imported photo file.
4. **TEST D:** Web restore: in-place restore preserved container mount inodes for `/data/storage` and `/data/storage/product_photos`, and photo remained readable.
5. **TEST E:** Real extension proxy import: succeeded with photo persistence.
6. **TEST F:** Owner access: `/`, `/certificates`, `/backups` all returned 200 OK via Gateway mTLS.
7. **TEST G:** Avito pairing code generation, pairing handshake, and heartbeat passed.
8. **TEST H:** Core pytest suite: 209 passed.
9. **TEST I:** Avito module pytest suite: 95 passed.
