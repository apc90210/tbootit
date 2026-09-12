# Stage 08C-R1-R4 — Recursive Media Tree Integrity Report

**Stage:** `Stage 08C-R1-R4 — Recursive Media Tree Integrity Proof`  
**Execution Timestamp:** 2026-09-12T11:02:00+03:00  
**Target Server:** `144.31.50.134` (`atanov821.serv.host`)  

---

## 1. Executive Summary

This verification stage resolved the media-file discrepancy between the Stage 08C-R1-R2 report (`315` media files) and the Stage 08C-R1-R3 report (`281` media files).

A rigorous, zero-mutation, byte-for-byte recursive walk was conducted across three storage locations:
1. **Local Workstation Live Storage:** `C:\tbootit\data\storage\`
2. **Accepted Deployment Backup Archive:** `TECHNOREBOOT_BACKUP_2026-09-12_102533.zip` (`storage/`)
3. **Real VDS Restored Persistent Storage:** `/srv/technoreboot/data/storage/`

### Key Results:
- **Total Storage Files:** Exactly **1,529** regular files in all three locations.
- **Total Storage Bytes:** Exactly **11,705,968** bytes in all three locations.
- **Deterministic Tree SHA256:** `1a3ee6bf8d3d4a7f28acd49b316f24ef5b63161442a3a6c8fc89561882d253a2` (100% identical).
- **Missing / Extra / Mismatched Files:** Exactly **0**.
- **Database Photo References:** All 50 `product_photos` rows in `technoreboot.db` resolve to valid, non-zero files on the VDS.
- **Root Cause of 315 vs 281:** Conclusively proven to be a shallow vs recursive counting method difference.

---

## 2. Root Cause Analysis: 315 vs 281

In Stage 08C-R1-R3, the preflight check evaluated:
```python
len(list(Path("/srv/technoreboot/data/storage/product_photos").glob("*")))
```
This shallow `glob('*')` only inspected the immediate entries of `product_photos/`:
- **Immediate regular files:** 271
- **Immediate subdirectories:** 10 (`'163'`, `'164'`, `'165'`, `'166'`, `'167'`, `'168'`, `'169'`, `'24'`, `'51'`, `'69'`)
- **Shallow glob total:** 271 + 10 = **281 entries**.

In Stage 08C-R1-R2, the recursive count of regular files under `product_photos/` was evaluated:
- **Immediate regular files:** 271
- **Nested regular files in the 10 subdirectories:** 44
- **Recursive regular files total:** 271 + 44 = **315 files**.

In addition, the historical archive directory `storage/product_photos_archive_20260911_104018` contains 1,214 files:
- 315 active product photos + 1,214 archived photos = **1,529 total regular storage files**.

**Conclusion:** Zero files were lost, missing, or corrupted. The difference was purely due to shallow `glob('*')` counting immediate directory handles as single items without traversing into nested files.

---

## 3. Recursive Manifests & Exact Set Comparison

| Metric | Local Workstation | Backup ZIP (`storage/`) | Real Debian VDS |
| :--- | :--- | :--- | :--- |
| **File Count** | 1,529 | 1,529 | 1,529 |
| **Total Bytes** | 11,705,968 | 11,705,968 | 11,705,968 |
| **Tree SHA256** | `1a3ee6bf...` | `1a3ee6bf...` | `1a3ee6bf...` |

### Pairwise Comparison:
- `LOCAL vs BACKUP`: 0 missing, 0 extra, 0 size mismatches, 0 hash mismatches (**EXACT MATCH: True**)
- `BACKUP vs VDS`: 0 missing, 0 extra, 0 size mismatches, 0 hash mismatches (**EXACT MATCH: True**)
- `LOCAL vs VDS`: 0 missing, 0 extra, 0 size mismatches, 0 hash mismatches (**EXACT MATCH: True**)

---

## 4. Database Photo-Reference Integrity

All 50 rows in `product_photos` on the VDS database were inspected:
- Total rows: 50
- Local file references: 50
- Missing referenced files: 0
- Zero-byte referenced files: 0
- Valid references: 50 (100%)

---

## 5. Known Media Files Verification

Physical files on VDS disk compared against backup and local workstation:
- `product_photos/1_51527540.jpg`: PASS (size & SHA256 match)
- `product_photos/2_bc9bdcec.jpg`: PASS (size & SHA256 match)
- `product_photos/3_f3b61975.jpg`: PASS (size & SHA256 match)

---

## 6. Zero-Mutation Proof

- **Local DB SHA256:** `98a58f06472fe480a8031761c0d0e5b2bb43e2273c800f12ec04aab2c915dddd` (unchanged)
- **Local CA SHA256:** `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d` (unchanged)
- **VDS DB SHA256:** `fa835b6c2e737f5fa74a8808f2f04b452ee7d0960a9359dee0ae29f328ead6ae` (unchanged)
- **VDS CA SHA256:** `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d` (unchanged)
- **VDS Running Containers:** 0 (remained strictly stopped throughout the entire stage)

---

## 7. Section 13 Final Report Contract

```text
# Stage 08C-R1-R4 — Recursive Media Tree Integrity Proof

## Git
LOCAL_HEAD_AT_START: d0344b5b668dda398be1f1eb568bc5835dd2f19f
ORIGIN_MAIN_AT_START: d0344b5b668dda398be1f1eb568bc5835dd2f19f
VDS_REPO_HEAD: d0344b5b668dda398be1f1eb568bc5835dd2f19f
VDS_STACK_RUNNING_AT_START: false

## Accepted Deployment Backup
BACKUP_FILENAME: TECHNOREBOOT_BACKUP_2026-09-12_102533.zip
LOCAL_BACKUP_SHA256: d0bfd8f27b9fcddf89ea539db28c6cc5b762918d2c74599841989faa50c39090
REMOTE_BACKUP_SHA256: d0bfd8f27b9fcddf89ea539db28c6cc5b762918d2c74599841989faa50c39090
BACKUP_SHA_MATCH: true

## Recursive Storage Manifests
LOCAL_STORAGE_FILE_COUNT: 1529
LOCAL_STORAGE_TOTAL_BYTES: 11705968
LOCAL_STORAGE_TREE_SHA256: 1a3ee6bf8d3d4a7f28acd49b316f24ef5b63161442a3a6c8fc89561882d253a2

BACKUP_STORAGE_FILE_COUNT: 1529
BACKUP_STORAGE_TOTAL_BYTES: 11705968
BACKUP_STORAGE_TREE_SHA256: 1a3ee6bf8d3d4a7f28acd49b316f24ef5b63161442a3a6c8fc89561882d253a2

VDS_STORAGE_FILE_COUNT: 1529
VDS_STORAGE_TOTAL_BYTES: 11705968
VDS_STORAGE_TREE_SHA256: 1a3ee6bf8d3d4a7f28acd49b316f24ef5b63161442a3a6c8fc89561882d253a2

## Exact Comparison
LOCAL_ONLY_FILES: 0
BACKUP_ONLY_FILES: 0
VDS_ONLY_FILES: 0
SIZE_MISMATCH_FILES: 0
HASH_MISMATCH_FILES: 0

LOCAL_BACKUP_TREE_MATCH: true
BACKUP_VDS_TREE_MATCH: true
LOCAL_VDS_TREE_MATCH: true

## 315 vs 281 Explanation
IMMEDIATE_PRODUCT_PHOTO_FILES: 271
IMMEDIATE_PRODUCT_PHOTO_DIRECTORIES: 10
NESTED_PRODUCT_PHOTO_FILES: 44
RECURSIVE_PRODUCT_PHOTO_FILES: 315
MEDIA_COUNT_DISCREPANCY_ROOT_CAUSE: Shallow glob('*') on product_photos counted 271 immediate files + 10 subdirectories (=281 entries), whereas recursive file walk traversed the 10 subdirectories containing 44 nested files (271 + 44 = 315 files). Exact byte-for-byte tree hash parity proven across local, backup, and VDS storage.

## DB Photo Integrity
PRODUCT_PHOTO_ROWS: 50
LOCAL_FILE_REFERENCES: 50
MISSING_REFERENCED_FILES: 0
ZERO_BYTE_REFERENCED_FILES: 0

## Known Media
MEDIA_1_HASH_MATCH: true
MEDIA_2_HASH_MATCH: true
MEDIA_3_HASH_MATCH: true

## No Mutation
LOCAL_DB_SHA256_UNCHANGED: true
LOCAL_CA_SHA256_UNCHANGED: true
VDS_DB_SHA256_UNCHANGED: true
VDS_CA_SHA256_UNCHANGED: true
VDS_RUNNING_CONTAINERS_AFTER: 0

## Repository
RUNTIME_FILES_CHANGED: 0
COMMIT: 64f37cf9a17ee452e78fa30dfc36d1d8c865b8dd
PUSH: origin/main
FINAL_HEAD: 64f37cf9a17ee452e78fa30dfc36d1d8c865b8dd
FINAL_GIT_STATUS: clean

FINAL_STATUS:
TECHNOREBOOT_STAGE08C_R1_R4_MEDIA_TREE_EXACTLY_PROVEN

DNS_CHANGED: false
CUTOVER_PERFORMED: false
VDS_STACK_STOPPED_PENDING_CUTOVER: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```
