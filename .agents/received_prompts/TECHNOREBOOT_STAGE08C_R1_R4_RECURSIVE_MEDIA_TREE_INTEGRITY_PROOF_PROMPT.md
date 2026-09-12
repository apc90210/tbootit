# TECHNOREBOOT — Stage 08C-R1-R4
## Recursive media tree integrity proof before cutover

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 08C-R1-R4 — Recursive Media Tree Integrity Proof`

# 0. WHY THIS REVISION EXISTS

Stage08C-R1-R3 is technically strong, but pre-cutover is NOT accepted yet because the media-file evidence is inconsistent:

Previous real-VDS restore report:

```text
RESTORED_MEDIA_FILES_COUNT: 315
```

Stage08C-R1-R3 report:

```text
MEDIA_STORAGE: 281 media files
```

The R3 preflight code used:

```python
len(list(media_dir.glob('*')))
```

which is a shallow count and may not include nested files.

This revision must determine conclusively whether:

1. `315` vs `281` is only a counting-method difference, OR
2. any storage files are actually missing / extra / corrupted on the VDS.

This stage is verification only.

DO NOT:
- rebuild images;
- start the VDS application stack;
- change DNS;
- perform cutover;
- modify local business data;
- modify VDS business data unless a later explicit corrective stage is approved.

The VDS application stack must remain STOPPED throughout this stage.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08C_R1_R4_RECURSIVE_MEDIA_TREE_INTEGRITY_PROOF_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08C_R1_R4_RECURSIVE_MEDIA_TREE_INTEGRITY_PROOF_PROMPT.md`

---

# 1. PREFLIGHT

Record:

```text
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
LOCAL_GIT_STATUS:
VDS_REPO_HEAD:
VDS_RUNNING_CONTAINERS:
```

Required:

```text
LOCAL_HEAD == ORIGIN_MAIN_HEAD
LOCAL_GIT_STATUS = clean
VDS_RUNNING_CONTAINERS = 0
```

Capture local database and CA SHA256 before verification.

---

# 2. IDENTIFY THE EXACT DEPLOYMENT BACKUP

The accepted VDS restore used:

```text
TECHNOREBOOT_BACKUP_2026-09-12_102533.zip
SHA256:
d0bfd8f27b9fcddf89ea539db28c6cc5b762918d2c74599841989faa50c39090
```

Verify the local archive still exists and has this exact SHA256.

Verify the remote transferred archive under:

```text
/srv/technoreboot/deploy/
```

has the same SHA256.

If either differs, return BLOCKED.

---

# 3. DEFINE EXACT MEDIA TREE

The canonical mutable media tree for this proof is:

Local:

```text
C:\tbootit\data\storage\
```

Backup ZIP:

```text
storage/
```

VDS:

```text
/srv/technoreboot/data/storage/
```

Do NOT use shallow `glob('*')`.

Walk recursively through ALL regular files.

Normalize every relative path to forward-slash form.

For each file collect:

```text
relative_path
size_bytes
sha256
```

Ignore directories themselves.

Do NOT include:
- DB;
- auth;
- Avito state;
- backups;
- source;
- generated Docker layers.

This proof concerns `storage/` only.

---

# 4. BUILD THREE RECURSIVE MANIFESTS

Create manifests in temporary memory/files outside Git:

### A. LOCAL CURRENT STORAGE

For every regular file recursively under:

`C:\tbootit\data\storage\`

compute:
- relative path;
- byte size;
- SHA256.

Report:

```text
LOCAL_STORAGE_FILE_COUNT
LOCAL_STORAGE_TOTAL_BYTES
LOCAL_STORAGE_TREE_SHA256
```

### B. BACKUP ARCHIVE STORAGE

Read the exact accepted ZIP without extracting into live data.

For every regular ZIP member below:

`storage/`

compute:
- normalized relative path;
- uncompressed byte size;
- SHA256 of content.

Report:

```text
BACKUP_STORAGE_FILE_COUNT
BACKUP_STORAGE_TOTAL_BYTES
BACKUP_STORAGE_TREE_SHA256
```

### C. VDS RESTORED STORAGE

Over SSH recursively walk:

`/srv/technoreboot/data/storage/`

For every regular file compute:
- normalized relative path;
- byte size;
- SHA256.

Report:

```text
VDS_STORAGE_FILE_COUNT
VDS_STORAGE_TOTAL_BYTES
VDS_STORAGE_TREE_SHA256
```

Use the same deterministic tree hash algorithm for all three, e.g. SHA256 over sorted lines:

```text
<relative_path>\0<size>\0<file_sha256>\n
```

---

# 5. EXACT SET COMPARISON

Compare:

```text
LOCAL vs BACKUP
BACKUP vs VDS
LOCAL vs VDS
```

Report exact counts:

```text
LOCAL_ONLY_FILES
BACKUP_ONLY_FILES
VDS_ONLY_FILES
SIZE_MISMATCH_FILES
HASH_MISMATCH_FILES
```

If any count is non-zero, list at most the first 25 relative paths in the report and write the complete diff to a safe report artifact.

Acceptance requires:

```text
BACKUP_ONLY_FILES = 0
VDS_ONLY_FILES = 0
SIZE_MISMATCH_FILES = 0
HASH_MISMATCH_FILES = 0
```

For LOCAL vs BACKUP:
- if local business/media state has legitimately changed after the deployment backup, report it clearly;
- however previous stage states local DB/data remained unchanged, so any difference requires explanation.

---

# 6. EXPLAIN 315 VS 281

Explicitly reproduce the old shallow counting method:

```python
len(list(Path(... / "product_photos").glob("*")))
```

and compare it with recursive:

```python
sum(1 for p in Path(... / "product_photos").rglob("*") if p.is_file())
```

Also report:
- number of immediate files;
- number of immediate subdirectories;
- number of files inside nested subdirectories;
- recursive total.

Required conclusion:

```text
MEDIA_COUNT_DISCREPANCY_ROOT_CAUSE:
```

Do NOT simply state "counting issue" without showing the numbers.

---

# 7. DATABASE PHOTO-REFERENCE INTEGRITY

Using the restored VDS DB:

- inspect all `product_photos` rows;
- resolve local storage references;
- verify every local file referenced by DB exists on VDS;
- verify referenced files are non-zero bytes.

Report:

```text
PRODUCT_PHOTO_ROWS
LOCAL_FILE_REFERENCES
MISSING_REFERENCED_FILES
ZERO_BYTE_REFERENCED_FILES
```

Acceptance:

```text
MISSING_REFERENCED_FILES = 0
ZERO_BYTE_REFERENCED_FILES = 0
```

Historical orphan media is allowed, but must not be deleted in this stage.

---

# 8. THREE KNOWN MEDIA FILES

Without starting the VDS stack, verify the same three files exist physically on disk and match their backup hashes:

```text
product_photos/1_51527540.jpg
product_photos/2_bc9bdcec.jpg
product_photos/3_f3b61975.jpg
```

If their actual relative paths differ, resolve from the DB/report.

Report:

```text
MEDIA_1_HASH_MATCH
MEDIA_2_HASH_MATCH
MEDIA_3_HASH_MATCH
```

---

# 9. NO MUTATION RULE

This stage MUST NOT mutate:
- VDS storage;
- local storage;
- local DB;
- VDS DB;
- auth;
- Docker images;
- containers.

Record before/after:

```text
LOCAL_DB_SHA256
LOCAL_CA_SHA256
VDS_DB_SHA256
VDS_CA_SHA256
VDS_RUNNING_CONTAINERS
```

Required:
- all hashes unchanged;
- VDS running containers remains 0.

---

# 10. TEST / SCRIPT QUALITY

If a reusable verifier is created, it may be added under:

`scripts/verify_vds_storage_integrity.py`

Requirements:
- read-only;
- no hardcoded passwords/private keys;
- no production secrets;
- supports local path + ZIP + SSH/VDS path cleanly;
- does not mutate data.

Do not add it if a one-off safe verification is simpler.

---

# 11. DOCUMENTATION

Create:

`reports/stage08c_r1_r4_recursive_media_tree_integrity_report.md`

Update:

`reports/stage08c_r1_r3_final_runtime_head_vds_rebuild_report.md`

`docs/vds_pre_cutover_status.md`

`logs/2026-09-12.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE08C_R1_R4_RECURSIVE_MEDIA_TREE_INTEGRITY_PROOF_PROMPT.md`

---

# 12. FINAL REPOSITORY INVARIANT

Only verification/docs/report/log changes are allowed.

No runtime code changes.

After commit:

```text
RUNTIME_FILES_CHANGED = 0
```

Push `origin/main`.

Final worktree clean.

---

# 13. FINAL REPORT CONTRACT

Return:

```text
# Stage 08C-R1-R4 — Recursive Media Tree Integrity Proof

## Git
LOCAL_HEAD_AT_START:
ORIGIN_MAIN_AT_START:
VDS_REPO_HEAD:
VDS_STACK_RUNNING_AT_START:

## Accepted Deployment Backup
BACKUP_FILENAME:
LOCAL_BACKUP_SHA256:
REMOTE_BACKUP_SHA256:
BACKUP_SHA_MATCH:

## Recursive Storage Manifests
LOCAL_STORAGE_FILE_COUNT:
LOCAL_STORAGE_TOTAL_BYTES:
LOCAL_STORAGE_TREE_SHA256:

BACKUP_STORAGE_FILE_COUNT:
BACKUP_STORAGE_TOTAL_BYTES:
BACKUP_STORAGE_TREE_SHA256:

VDS_STORAGE_FILE_COUNT:
VDS_STORAGE_TOTAL_BYTES:
VDS_STORAGE_TREE_SHA256:

## Exact Comparison
LOCAL_ONLY_FILES:
BACKUP_ONLY_FILES:
VDS_ONLY_FILES:
SIZE_MISMATCH_FILES:
HASH_MISMATCH_FILES:

LOCAL_BACKUP_TREE_MATCH:
BACKUP_VDS_TREE_MATCH:
LOCAL_VDS_TREE_MATCH:

## 315 vs 281 Explanation
IMMEDIATE_PRODUCT_PHOTO_FILES:
IMMEDIATE_PRODUCT_PHOTO_DIRECTORIES:
NESTED_PRODUCT_PHOTO_FILES:
RECURSIVE_PRODUCT_PHOTO_FILES:
MEDIA_COUNT_DISCREPANCY_ROOT_CAUSE:

## DB Photo Integrity
PRODUCT_PHOTO_ROWS:
LOCAL_FILE_REFERENCES:
MISSING_REFERENCED_FILES:
ZERO_BYTE_REFERENCED_FILES:

## Known Media
MEDIA_1_HASH_MATCH:
MEDIA_2_HASH_MATCH:
MEDIA_3_HASH_MATCH:

## No Mutation
LOCAL_DB_SHA256_UNCHANGED:
LOCAL_CA_SHA256_UNCHANGED:
VDS_DB_SHA256_UNCHANGED:
VDS_CA_SHA256_UNCHANGED:
VDS_RUNNING_CONTAINERS_AFTER:

## Repository
RUNTIME_FILES_CHANGED:
COMMIT:
PUSH:
FINAL_HEAD:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08C_R1_R4_MEDIA_TREE_EXACTLY_PROVEN

DNS_CHANGED: false
CUTOVER_PERFORMED: false
VDS_STACK_STOPPED_PENDING_CUTOVER: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- backup SHA mismatches;
- any backup file is missing/corrupted on VDS;
- any DB-referenced photo is missing;
- any storage hash mismatch remains unexplained;
- VDS stack is started;
- local/VDS business state is mutated.

# 14. STOP

After read-only storage proof, report, commit/push:

STOP.

Do not start VDS.
Do not change DNS.
Do not perform cutover.
Wait for Owner acceptance.
