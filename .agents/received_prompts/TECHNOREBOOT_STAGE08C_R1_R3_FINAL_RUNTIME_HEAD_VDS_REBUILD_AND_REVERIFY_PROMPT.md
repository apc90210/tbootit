# TECHNOREBOOT — Stage 08C-R1-R3
## Final runtime-head VDS rebuild and re-verification

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Stage:** `Stage 08C-R1-R3 — Final Runtime Head VDS Rebuild and Re-Verification`

# 0. WHY THIS REVISION EXISTS

Stage08C-R1-R2 is NOT accepted yet.

The real VDS deployment itself was successful, but the report shows a runtime-source mismatch:

```text
REMOTE_BUILD_HEAD: f78dad75734b4cae95cd5742677327a4d5448cd8
FINAL_REPOSITORY_HEAD: 7e19c95c8baad4b22c06173a4b64a27bc19a6d4b
```

During Stage08C-R1-R2, a real runtime source file was changed after the VDS images had already been built:

```text
admin-shell/app/backup_service.py
```

Therefore the successful VDS proof did not execute the final committed runtime code.

This revision closes only that gap.

IMPORTANT:
- real VDS is already provisioned;
- restored data already exists on VDS;
- VDS application stack is currently STOPPED;
- DNS must remain unchanged;
- no business cutover;
- local stack remains canonical and running;
- do NOT re-bootstrap SSH or reinstall Docker unless something is broken;
- do NOT restore a second backup unless required by an actual integrity problem;
- do NOT modify local business data.

First copy this prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08C_R1_R3_FINAL_RUNTIME_HEAD_VDS_REBUILD_AND_REVERIFY_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08C_R1_R3_FINAL_RUNTIME_HEAD_VDS_REBUILD_AND_REVERIFY_PROMPT.md`

---

# 1. PRE-FLIGHT

Record:

```text
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
LOCAL_GIT_STATUS:
VDS_REPO_HEAD:
VDS_STACK_RUNNING:
VDS_DATA_EXISTS:
```

Required:
- local worktree clean;
- local HEAD == origin/main;
- VDS stack stopped;
- VDS restored data present.

Capture local safety baseline:
- product IDs;
- sale IDs;
- repair IDs;
- photo IDs;
- external listing IDs;
- local DB SHA256;
- local CA SHA256;
- local container start times/restart counts.

---

# 2. DEFINE DEPLOYMENT CODE HEAD

Because this revision itself may later add only reports/logs/prompts, use an explicit immutable runtime baseline:

```text
DEPLOYMENT_CODE_HEAD = current origin/main before this revision modifies any runtime source
```

If any runtime/source/config fix is required during this revision:
1. make the fix;
2. run relevant tests;
3. commit and push it;
4. update `DEPLOYMENT_CODE_HEAD` to that new commit;
5. only then rebuild the VDS.

After the VDS runtime proof, only documentation/report/log/prompt files may be committed.

No runtime-relevant file may change after `DEPLOYMENT_CODE_HEAD` is proven.

Runtime-relevant paths include at minimum:

```text
admin-shell/
core/
inventory-sales-module/
repairs-module/
avito-module/
gateway/
deploy/
scripts/bootstrap_restore.py
scripts/bootstrap_restore.sh
docker-compose.yml
```

If any of those paths change after the runtime proof, the proof must be repeated.

---

# 3. VERIFY VDS REPOSITORY

On the VDS:

```text
cd /srv/technoreboot/app
git fetch origin
git checkout main
git reset --hard <DEPLOYMENT_CODE_HEAD>
```

Required:

```text
VDS_REPO_HEAD == DEPLOYMENT_CODE_HEAD
```

Do not delete:
- `/srv/technoreboot/data`;
- `/srv/technoreboot/secrets`;
- `/srv/technoreboot/deploy`.

Do not restore business data again unless corruption is found.

---

# 4. VERIFY RESTORED DATA BEFORE REBUILD

With the VDS stack still stopped, verify restored persistent state:

```text
PRODUCTS = 50
SALES = 52
REPAIRS = 66
PHOTO_ROWS = 50
EXTERNAL_LISTINGS = 50
CA_SHA256 = expected local CA SHA256
```

Also verify:
- media tree exists;
- OWNER identity exists in registry;
- revocation registry exists.

If any mismatch appears, STOP with BLOCKED.

---

# 5. REBUILD ALL PRODUCTION IMAGES FROM FINAL RUNTIME HEAD

On the VDS, from `/srv/technoreboot/app`:

```text
docker compose \
  --env-file /srv/technoreboot/secrets/production.env \
  -f deploy/production/docker-compose.prod.yml \
  build --no-cache
```

or equivalent.

Record:

```text
BUILD_SOURCE_PATH:
BUILD_SOURCE_HEAD:
IMAGE_NAMES:
IMAGE_IDS:
```

Required:

```text
BUILD_SOURCE_HEAD == DEPLOYMENT_CODE_HEAD
```

All six production services must be rebuilt from this source.

Do not import images from the developer workstation.

---

# 6. START VDS STACK FOR FINAL RUNTIME PROOF

Start the production stack using the existing restored data and production secrets.

Verify:
- all 6 services running;
- all healthchecks healthy;
- only Gateway publishes 80/443;
- internal host ports = 0.

Do not perform ordinary business writes.

---

# 7. FINAL MTLS / RBAC / ROUTE PROOF

From the Owner PC verify the real VDS:

```text
HTTP_TO_HTTPS = PASS
NO_CLIENT_CERT = 403
OWNER_CERT = accepted

/ = 200
/inventory/products = 200
/inventory/sales = 200
/repairs/repairs = 200
/avito/extension = 200
/backups = 200 OWNER
/certificates = 200 OWNER
```

If USER cert is available:

```text
/inventory/products = 200 USER
/backups = 403 USER
/certificates = 403 USER
```

Verify remote counts remain:
- products 50;
- sales 52;
- repairs 66;
- photos 50;
- external listings 50.

---

# 8. FINAL BACKUP-SERVICE PROOF

This is mandatory because `admin-shell/app/backup_service.py` changed after the previous image build.

Using the newly rebuilt final runtime image:

1. create one VDS backup through the supported backup API/backend;
2. verify HTTP/API success;
3. verify archive exists under persistent VDS backup path;
4. verify backup manifest;
5. inspect archive safely and verify it includes the restored VDS auth tree;
6. verify the CA certificate inside that backup has exactly the same SHA256 as the live/restored Technoreboot client CA.

Required:

```text
REMOTE_BACKUP_CREATED = true
REMOTE_BACKUP_CA_SHA256_MATCH = true
REMOTE_BACKUP_AUTH_TREE_PRESENT = true
```

Do NOT restore this backup.

---

# 9. MEDIA PROOF

Verify at least the same three known media URLs or three valid current ones through the public Gateway.

Required:

```text
MEDIA_1 = 200
MEDIA_2 = 200
MEDIA_3 = 200
```

---

# 10. SECURITY / FIREWALL RECHECK

Verify:
- SSH still works;
- firewall active;
- public application ports only 80/443;
- internal container ports not public;
- no privileged containers;
- no host networking;
- no Docker socket mount.

Do not redesign firewall if current rules work.

---

# 11. SPLIT-BRAIN SAFETY

After all checks succeed:

STOP the VDS application stack again.

Required final state:

```text
LOCAL_STACK_RUNNING = true
VDS_STACK_RUNNING_AFTER_PROOF = false
DNS_CHANGED = false
CUTOVER_PERFORMED = false
```

Do not remove:
- images;
- VDS data;
- production secrets;
- repository;
- backups.

---

# 12. LOCAL SAFETY

After proof compare exact local state with preflight:

```text
PRODUCT_IDS_UNCHANGED = true
SALE_IDS_UNCHANGED = true
REPAIR_IDS_UNCHANGED = true
PHOTO_IDS_UNCHANGED = true
EXTERNAL_LISTING_IDS_UNCHANGED = true
LOCAL_DB_SHA256_UNCHANGED = true
LOCAL_CA_SHA256_UNCHANGED = true
LOCAL_CONTAINERS_RESTARTED = 0
LOCAL_GATEWAY_HEALTH_AFTER = true
```

---

# 13. TESTS

Run at minimum:
- production baseline tests;
- backup-service tests;
- admin-shell backup/auth tests affected by the runtime fix.

If any code is changed during this revision, run its complete affected module suite.

Required:
```text
FAILED = 0
```

---

# 14. DOCUMENTATION

Create:

`reports/stage08c_r1_r3_final_runtime_head_vds_rebuild_report.md`

Update:

`reports/stage08c_r1_real_vds_pre_cutover_deployment_report.md`

`docs/vds_pre_cutover_status.md`

`docs/stage08c_r1_real_vds_pre_cutover_deployment.md`

`logs/2026-09-12.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE08C_R1_R3_FINAL_RUNTIME_HEAD_VDS_REBUILD_AND_REVERIFY_PROMPT.md`

---

# 15. FINAL REPOSITORY INVARIANT

After the VDS runtime proof, if documentation/report/log commits advance `origin/main`, verify the diff:

```text
git diff --name-only DEPLOYMENT_CODE_HEAD..FINAL_HEAD
```

Allowed after proof:
- `.agents/received_prompts/**`
- `docs/**`
- `reports/**`
- `logs/**`

No runtime-relevant path may differ.

Required:

```text
RUNTIME_FILES_CHANGED_AFTER_PROOF = 0
```

This avoids the circular requirement that a documentation-only final commit must force another runtime rebuild.

---

# 16. GIT SAFETY

Never commit:
- SSH private key;
- password;
- `.secrets/`;
- production.env;
- TLS private key;
- backup ZIP;
- runtime DB;
- real media.

Push only safe source fixes (before proof) and documentation/report/log changes (after proof).

Final worktree clean.

---

# 17. FINAL REPORT CONTRACT

Return:

```text
# Stage 08C-R1-R3 — Final Runtime Head VDS Rebuild and Re-Verification

## Git Identity
LOCAL_HEAD_AT_START:
ORIGIN_MAIN_AT_START:
DEPLOYMENT_CODE_HEAD:
VDS_REPO_HEAD_AT_BUILD:
BUILD_HEAD_MATCH:

## VDS Persistent State
PRODUCTS:
SALES:
REPAIRS:
PHOTOS:
EXTERNAL_LISTINGS:
CA_SHA256_MATCH:
OWNER_IDENTITY_PRESENT:
REVOCATION_REGISTRY_PRESENT:

## Final Runtime Build
BUILD_RESULT:
BUILD_SOURCE_PATH:
BUILD_SOURCE_HEAD:
IMAGES:
IMAGE_IDS:

## Runtime Proof
ALL_SERVICES_HEALTHY:
HTTP_TO_HTTPS:
NO_CLIENT_CERT_REJECTED:
OWNER_CERT_ACCEPTED:
USER_RBAC:
ROOT_ROUTE:
PRODUCTS_ROUTE:
SALES_ROUTE:
REPAIRS_ROUTE:
AVITO_EXTENSION_ROUTE:
BACKUPS_ROUTE:
CERTIFICATES_ROUTE:
REMOTE_COUNTS_MATCH:

## Backup-Service Proof
REMOTE_BACKUP_CREATED:
REMOTE_BACKUP_FILE:
REMOTE_BACKUP_SHA256:
REMOTE_BACKUP_AUTH_TREE_PRESENT:
REMOTE_BACKUP_CA_SHA256:
LIVE_CA_SHA256:
REMOTE_BACKUP_CA_SHA256_MATCH:

## Media
MEDIA_1:
MEDIA_2:
MEDIA_3:

## Security
SSH_OK:
FIREWALL_ACTIVE:
PUBLIC_APP_PORTS:
INTERNAL_PUBLIC_PORTS:
PRIVILEGED_CONTAINERS:
HOST_NETWORK:
DOCKER_SOCKET_MOUNTS:

## Split-Brain
LOCAL_STACK_RUNNING:
VDS_STACK_RUNNING_AFTER_PROOF:
DNS_CHANGED:
CUTOVER_PERFORMED:

## Local Safety
PRODUCT_IDS_UNCHANGED:
SALE_IDS_UNCHANGED:
REPAIR_IDS_UNCHANGED:
PHOTO_IDS_UNCHANGED:
EXTERNAL_LISTING_IDS_UNCHANGED:
LOCAL_DB_SHA256_UNCHANGED:
LOCAL_CA_SHA256_UNCHANGED:
LOCAL_CONTAINERS_RESTARTED:
LOCAL_GATEWAY_HEALTH_AFTER:

## Tests
FAILED:

## Final Repository Invariant
FINAL_HEAD:
FILES_CHANGED_AFTER_DEPLOYMENT_CODE_HEAD:
RUNTIME_FILES_CHANGED_AFTER_PROOF:

## Git
COMMIT:
PUSH:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08C_R1_R3_FINAL_RUNTIME_HEAD_VDS_PROVEN

REAL_VDS_TOUCHED: true
DNS_CHANGED: false
CUTOVER_PERFORMED: false
VDS_STACK_STOPPED_PENDING_CUTOVER: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- VDS build source head differs from DEPLOYMENT_CODE_HEAD;
- backup created by rebuilt runtime contains wrong/missing auth CA;
- local data changes;
- internal ports become public;
- VDS stack remains running after proof;
- any runtime-relevant file changes after the proven build without repeating the proof.

---

# 18. STOP

After final runtime-head rebuild, verification, remote backup proof and deliberate VDS stack stop:

STOP.

Do not change DNS.
Do not perform cutover.
Wait for Owner acceptance.
