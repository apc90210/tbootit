# TECHNOREBOOT — Stage 07E-R1-R2
## Fresh Git build + full backup integrity proof

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07E-R1-R2 — Fresh Git Build and Full Backup Integrity Proof`

# 0. WHY THIS REVISION EXISTS

Stage07E-R1-R1 proved an important part successfully:

- a separate recovery Compose project was created;
- recovery used a separate data root;
- gateway ran on 9443;
- restored DB/auth/media were isolated;
- old OWNER certificate authenticated;
- live stack on 8443 was not restarted or modified;
- recovery project was removed cleanly.

However Stage07E is still NOT accepted because two final disaster-recovery guarantees are not yet proven.

## Gap 1 — recovery stack reused existing local Docker images

The isolated proof used existing images such as:

```text
tbootit-core:latest
```

A dead-server recovery requirement is stronger:

```text
fresh Git checkout + backup ZIP
=> build application images from source
=> start recovered stack
```

A new Debian server cannot depend on Docker images already existing on the old developer machine.

## Gap 2 — restored storage was sampled, not proven byte-for-byte complete

Previous reports contain different media-file totals:

```text
Stage07E-R1:    MEDIA_FILES = 1236
Stage07E-R1-R1: RECOVERY_MEDIA_FILES = 1214
```

Three media HTTP 200 checks prove serving works, but do not prove that the entire backup storage tree was restored without missing files.

This revision must close ONLY these two gaps.

Do NOT redesign backup/restore architecture.
Do NOT change Stage07G business logic.
Do NOT deploy production VDS.
Do NOT modify live business data.
No Owner CLI.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07E_R1_R2_FRESH_GIT_BUILD_AND_FULL_BACKUP_INTEGRITY_PROOF_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07E_R1_R2_FRESH_GIT_BUILD_AND_FULL_BACKUP_INTEGRITY_PROOF_PROMPT.md`

# 1. PREFLIGHT

Record:

```text
LIVE_HEAD:
ORIGIN_MAIN_HEAD:
LIVE_GIT_STATUS:
BACKUP_ZIP:
BACKUP_SHA256:
LIVE_GATEWAY:
```

Preserve all existing live data and containers.

Capture before-test hashes/identity sets for:
- live DB;
- live CA;
- live product IDs;
- live sale IDs;
- live media relative-path set.

# 2. CREATE A TRUE FRESH SOURCE WORKSPACE

Do NOT use the current working tree as the source for recovery containers.

Create a disposable source checkout under `.recovery-test/<run-id>/repo`.

Preferred:

```text
git clone <origin-url> <recovery-repo>
git checkout <expected commit>
```

The recovery checkout must come from `origin/main`.

Required report:

```text
RECOVERY_REPO_PATH:
RECOVERY_REPO_ORIGIN:
RECOVERY_REPO_HEAD:
RECOVERY_REPO_GIT_STATUS:
RECOVERY_SOURCE_IS_FRESH_CLONE: true
```

Do not copy source files from `C:\tbootit` into the recovery repo.

# 3. BUILD UNIQUE RECOVERY IMAGES FROM THAT FRESH CHECKOUT

The recovery Compose project must build images from the fresh clone.

Do NOT use pre-existing:

```text
tbootit-core:latest
tbootit-admin-shell:latest
...
```

as the acceptance path.

Use unique recovery image tags, for example:

```text
technoreboot-recovery-<run-id>-core
technoreboot-recovery-<run-id>-admin
...
```

Run an actual build from source.

Preferred proof:

```text
docker compose -p <recovery-project> build --no-cache
```

or another deterministic fresh build that cannot resolve to the normal live application images.

Report:

```text
RECOVERY_IMAGES:
RECOVERY_IMAGE_IDS:
RECOVERY_IMAGE_CREATED_AT:
RECOVERY_BUILD_FROM_CONTEXTS:
PREEXISTING_LIVE_IMAGE_IDS_NOT_USED:
```

The recovery stack must then start from these freshly built images.

# 4. RESTORE BACKUP INTO SEPARATE DATA ROOT

Use the same valid backup ZIP:

`TECHNOREBOOT_BACKUP_2026-09-11_103952.zip`

or explicitly state if a newer valid backup is used.

Restore to:

`.recovery-test/<run-id>/data`

No bind mount may reference:

`C:\tbootit\data`

or any normal live mutable path.

# 5. FULL BACKUP TREE INTEGRITY — NO SAMPLING

Before restore, safely inspect/extract backup to staging.

For every backed-up mutable component, calculate:

- relative path set;
- regular file count;
- total bytes;
- SHA256 per file (or deterministic tree hash built from `relative_path + file_sha256`).

At minimum:

```text
database/
storage/
auth/
avito-module/
```

Then calculate the same tree hash after restore.

Required:

```text
BACKUP_STORAGE_FILE_COUNT:
RESTORED_STORAGE_FILE_COUNT:
BACKUP_STORAGE_TOTAL_BYTES:
RESTORED_STORAGE_TOTAL_BYTES:
BACKUP_STORAGE_TREE_SHA256:
RESTORED_STORAGE_TREE_SHA256:
STORAGE_MISSING_FILES:
STORAGE_EXTRA_FILES:
STORAGE_HASH_MISMATCHES:
```

Acceptance:

```text
missing = 0
hash mismatches = 0
```

Explain the previous `1236` vs `1214` discrepancy precisely.

Do NOT simply choose one count and overwrite the report.

# 6. DATABASE ↔ MEDIA REFERENTIAL CHECK

Against the restored DB:

For every `product_photos` row that references a local storage path:

- referenced file must exist;
- file must be non-empty;
- extension/content type must be supported.

Report:

```text
PRODUCT_PHOTO_ROWS:
LOCAL_PHOTO_REFERENCES:
MISSING_REFERENCED_PHOTOS:
ZERO_BYTE_REFERENCED_PHOTOS:
ORPHAN_MEDIA_FILES:
```

Orphan files may exist historically, but they must be reported and must explain any storage-count difference.

Do not delete them during this proof.

# 7. AUTH AND AVITO TREE INTEGRITY

Also prove full-tree equality for backed-up auth and Avito mutable state.

Required:

```text
BACKUP_AUTH_TREE_SHA256:
RESTORED_AUTH_TREE_SHA256:
AUTH_MISSING_FILES:
AUTH_HASH_MISMATCHES:

BACKUP_AVITO_TREE_SHA256:
RESTORED_AVITO_TREE_SHA256:
AVITO_MISSING_FILES:
AVITO_HASH_MISMATCHES:
```

Private material must NOT be printed.

Only hashes/counts/relative-path diagnostics are allowed.

# 8. START FRESH-BUILT RECOVERY STACK

Use:
- separate Compose project;
- separate ports;
- recovery data root;
- freshly built recovery images.

Gateway should use an alternate port such as 9443.

Verify:

- all recovery containers start;
- health checks pass;
- OWNER certificate from backup works;
- no-cert request is rejected;
- restored backup counts are visible.

No request to 8443 may count as recovery proof.

# 9. ROUTE AND MEDIA PROOF

Against recovery URL only:

- `/`
- `/inventory/products`
- one product detail
- `/sales`
- `/reports/sales`
- `/repairs`
- `/avito/extension`
- `/backups`
- `/certificates`

For media:
- still check at least 3 HTTP 200 files;
- additionally rely on the full storage tree hash/integrity proof.

# 10. LIVE ISOLATION

After the complete build/restore/start/verify/teardown cycle:

Required:

```text
LIVE_DB_SHA_BEFORE == LIVE_DB_SHA_AFTER
LIVE_CA_SHA_BEFORE == LIVE_CA_SHA_AFTER
LIVE_PRODUCT_IDS_BEFORE == LIVE_PRODUCT_IDS_AFTER
LIVE_SALE_IDS_BEFORE == LIVE_SALE_IDS_AFTER
LIVE_MEDIA_PATH_SET_BEFORE == LIVE_MEDIA_PATH_SET_AFTER
LIVE_CONTAINERS_RESTARTED = 0
```

The fresh build is allowed to consume CPU/disk but must not alter or restart the normal stack.

# 11. CLEANUP

Remove only:
- recovery Compose project;
- recovery containers/networks/volumes;
- uniquely tagged recovery images if practical;
- recovery clone/data/staging.

Do not remove:
- backup ZIP;
- live source;
- live images used by current system;
- live data.

# 12. BOOTSTRAP SCRIPT AUDIT FOR REAL FRESH DEBIAN

Review `scripts/bootstrap_restore.sh` and `scripts/bootstrap_restore.py`.

Confirm that the documented new-server runbook does not assume:
- prebuilt Technoreboot images;
- files outside cloned repository and backup ZIP;
- old running server.

If Python dependencies such as `cryptography` are required:
- either install them deterministically in the bootstrap path;
- or fail with an exact Debian command/instruction before any restore begins.

The Owner runbook must remain operational from a fresh Debian machine.

# 13. REQUIRED TESTS

A. Fresh clone is from origin/main.
B. Fresh clone HEAD matches expected commit.
C. Recovery images are built from fresh clone.
D. Normal live application image IDs are not used by recovery containers.
E. Full backup storage path set equals restored path set.
F. Full backup storage tree hash equals restored tree hash.
G. Missing storage files = 0.
H. Storage hash mismatches = 0.
I. Previous 1236 vs 1214 discrepancy explained.
J. All ProductPhoto local references exist.
K. No referenced photo is zero bytes.
L. Auth tree hash matches.
M. Avito mutable-state tree hash matches.
N. Recovery stack starts from freshly built images.
O. Recovery gateway uses alternate port.
P. Existing OWNER certificate works.
Q. No-cert request rejected.
R. Inventory route uses restored DB.
S. Sales/reports use restored DB.
T. Repairs uses restored DB.
U. Avito extension route works.
V. Backup/certificate routes work.
W. 3 media files return HTTP 200.
X. Live DB/auth/media/identity sets unchanged.
Y. Live containers restarted = 0.
Z. Recovery teardown leaves live stack healthy.

Run relevant backup/web-restore regressions too.

# 14. DOCUMENTATION

Update:

`docs/stage07e_r1_new_server_bootstrap_and_disaster_recovery.md`

`docs/disaster_recovery_new_server.md`

Create:

`reports/stage07e_r1_r2_fresh_git_build_and_full_backup_integrity_report.md`

Update:

`logs/2026-09-11.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE07E_R1_R2_FRESH_GIT_BUILD_AND_FULL_BACKUP_INTEGRITY_PROOF_PROMPT.md`

# 15. GIT / SAFETY

Do not commit:
- recovery clone;
- recovery DB;
- restored auth keys;
- backup ZIP;
- restored media;
- temporary images/artifacts;
- cookies;
- secrets.

Commit only source/tests/docs required for durable recovery.

Push `origin/main`.
Verify clean worktree.

# 16. FINAL REPORT CONTRACT

Return:

```text
# Stage 07E-R1-R2 — Fresh Git Build and Full Backup Integrity Proof

## Fresh Source
RECOVERY_REPO:
RECOVERY_ORIGIN:
RECOVERY_HEAD:
FRESH_CLONE:

## Fresh Images
RECOVERY_IMAGES:
RECOVERY_IMAGE_IDS:
BUILT_FROM_RECOVERY_REPO:
LIVE_IMAGE_IDS_USED:

## Backup
BACKUP_FILE:
BACKUP_SHA256:

## Storage Integrity
BACKUP_STORAGE_FILE_COUNT:
RESTORED_STORAGE_FILE_COUNT:
BACKUP_STORAGE_TOTAL_BYTES:
RESTORED_STORAGE_TOTAL_BYTES:
BACKUP_STORAGE_TREE_SHA256:
RESTORED_STORAGE_TREE_SHA256:
MISSING_FILES:
EXTRA_FILES:
HASH_MISMATCHES:
COUNT_1236_VS_1214_EXPLANATION:

## ProductPhoto Integrity
PRODUCT_PHOTO_ROWS:
LOCAL_REFERENCES:
MISSING_REFERENCED_PHOTOS:
ZERO_BYTE_REFERENCED_PHOTOS:
ORPHAN_MEDIA_FILES:

## Auth Integrity
BACKUP_AUTH_TREE_SHA256:
RESTORED_AUTH_TREE_SHA256:
AUTH_MISSING:
AUTH_MISMATCHES:

## Avito State Integrity
BACKUP_AVITO_TREE_SHA256:
RESTORED_AVITO_TREE_SHA256:
AVITO_MISSING:
AVITO_MISMATCHES:

## Recovery Runtime
RECOVERY_PROJECT:
RECOVERY_GATEWAY:
RECOVERY_PRODUCTS:
RECOVERY_SALES:
RECOVERY_REPAIRS:
RECOVERY_PHOTOS:
OWNER_CERT_ACCEPTED:
NO_CERT_REJECTED:

## Route Proof
ROOT:
INVENTORY:
PRODUCT_DETAIL:
SALES:
REPORTS:
REPAIRS:
AVITO_EXTENSION:
BACKUPS:
CERTIFICATES:
MEDIA_200:

## Live Isolation
LIVE_DB_UNCHANGED:
LIVE_AUTH_UNCHANGED:
LIVE_MEDIA_UNCHANGED:
LIVE_PRODUCT_IDS_UNCHANGED:
LIVE_SALE_IDS_UNCHANGED:
LIVE_CONTAINERS_RESTARTED:
LIVE_STACK_HEALTH_AFTER:

## Debian Bootstrap
PREBUILT_IMAGES_REQUIRED:
OLD_SERVER_REQUIRED:
EXTERNAL_MANUAL_DEPENDENCIES:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE07E_R1_R2_FRESH_SERVER_RECOVERY_FULLY_PROVEN

OWNER_MANUAL_CHECK_REQUIRED: false
PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If recovery still depends on pre-existing Technoreboot application images, return BLOCKED.

If any backed-up storage file is missing or has a hash mismatch after restore, return BLOCKED.

If the recovery stack uses live mutable data, return BLOCKED.

# 17. STOP

After proof, cleanup, tests, docs, commit/push and report:

STOP.

Do not deploy to production VDS.
Wait for Owner acceptance.
