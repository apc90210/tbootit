# TECHNOREBOOT — Stage 07E-R1
## New-server bootstrap and disaster recovery from Technoreboot backup

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07E-R1 — New Server Bootstrap and Disaster Recovery`

# 0. EXECUTION CONTRACT

Stage07G-R1 has been accepted by Owner.

Resume the previously postponed disaster-recovery stage.

Goal:

> Prove that Technoreboot can be restored onto a fresh Debian server/VM from source + one Technoreboot backup archive, including business data, media, Avito mutable state and OWNER certificate authority state, without depending on the old running server.

This stage is LOCAL/TEST only.

Do NOT deploy the production VDS yet.
Do NOT destroy or overwrite the current working installation.
No Owner CLI for acceptance.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07E_R1_NEW_SERVER_BOOTSTRAP_AND_DISASTER_RECOVERY_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07E_R1_NEW_SERVER_BOOTSTRAP_AND_DISASTER_RECOVERY_PROMPT.md`

---

# 1. EXISTING ACCEPTED BACKUP CONTRACT

Current accepted web backup behavior:

- `/backups` is OWNER-only;
- Owner downloads one ZIP;
- ZIP contains mutable DB, storage/media, auth, Avito mutable state and manifest;
- source code is NOT inside backup ZIP;
- normal in-place web restore deliberately DOES NOT overwrite live `data/auth`;
- auth is still included in ZIP specifically for dead-server/fresh-server recovery.

This stage must implement the missing fresh-server bootstrap path.

# 2. TARGET DISASTER SCENARIO

Assume:

- old server completely dead/unavailable;
- new server is fresh Debian;
- available: Git repository + one valid Technoreboot backup ZIP;
- Docker/Docker Compose can be installed;
- no DNS/VDS production cutover in this stage.

Recover:

- source;
- containers;
- DB;
- product photos/media;
- Avito mutable state;
- auth CA / OWNER trust state;
- required runtime configuration.

The recovered system must recognize the already-issued OWNER certificate when the backup contains the matching auth state.

Do NOT generate a new CA during recovery when a valid backed-up CA exists.

# 3. BOOTSTRAP ENTRYPOINT

Implement one deterministic recovery entrypoint, preferably:

`scripts/bootstrap_restore.sh`

It must:

1. preflight OS/dependencies;
2. verify repository root;
3. verify backup ZIP exists;
4. inspect/validate manifest;
5. verify required components;
6. stop target recovery stack if needed;
7. create required host directories;
8. restore mutable data to correct host paths;
9. restore `data/auth` from backup in fresh-server mode;
10. preserve permissions required by containers;
11. build/start Docker Compose stack;
12. wait for health;
13. verify HTTPS/mTLS gateway;
14. verify business data/media;
15. print concise recovery result.

Do not embed secrets in source.

# 4. TWO DISTINCT RESTORE MODES

## A. Existing running system restore

Current `/backups` behavior remains unchanged:

- business state restore;
- DO NOT overwrite live `data/auth`.

## B. Fresh/dead-server bootstrap restore

New bootstrap path:

- source from Git;
- mutable state from backup ZIP;
- `data/auth` MUST be restored;
- old CA and OWNER trust state preserved;
- no dependence on running admin-shell.

Do not merge these policies.

# 5. BACKUP VALIDATION

Before restore validate:

- ZIP readable;
- manifest present;
- supported format/version;
- DB present;
- required mutable directories identified;
- auth present for full recovery;
- reject `../`, absolute paths and traversal;
- reject partial/malformed archive before writing targets.

If checksums exist, verify them.
If absent, add forward-compatible checksum support if practical without breaking old backups.

# 6. SAFE RESTORE

Use staging:

- extract to temporary directory;
- validate staged content;
- prepare target directories;
- sync/restore;
- start stack;
- verify.

Do not extract directly over arbitrary filesystem paths.

Preserve bind-mount stability; sync contents in place where appropriate instead of replacing mounted directory inodes.

# 7. AUTH / OWNER CERTIFICATE RECOVERY

After fresh recovery:

- backed-up CA is active CA;
- backed-up OWNER certificate serial/trust state remains recognized;
- OWNER routes work with existing OWNER client certificate;
- no-cert requests remain rejected;
- revoked certificates remain revoked.

Do not expose private CA material in report.

# 8. DATA RECOVERY VERIFICATION

Use a disposable recovery target separate from current live local instance.

Verify:

- product count matches backup;
- Avito-linked count matches;
- local-only count matches;
- sales count matches;
- product photo count matches;
- several actual media files return HTTP 200;
- product detail loads;
- `/inventory/products` loads;
- sales/reports load;
- repairs loads;
- `/avito/extension` loads;
- `/backups` loads for OWNER.

Do not accept count-only recovery if files/routes are broken.

# 9. AVITO STATE RECOVERY

Restore mutable Avito-module state included by accepted backup contract.

Do NOT add browser cookies/session to backup if they were previously excluded.

Verify Avito module starts and extension page works.

# 10. CONFIG / SECRETS

Audit which runtime values are:

- committed safe defaults;
- environment variables;
- generated secrets;
- mutable auth material;
- host-specific configuration.

Fresh restore must fail clearly if an external secret/config value is required but unavailable.

Never commit real secrets.

# 11. DISPOSABLE RECOVERY ENVIRONMENT

Do NOT test by overwriting `C:\tbootit` live data.

Use one of:

- separate Docker Compose project name;
- temporary cloned workspace;
- dedicated temporary data root;
- disposable Debian VM/container where appropriate.

Ports must not collide with current local system.

Document exact isolation method.

# 12. REQUIRED TESTS

A. Valid backup accepted.  
B. Missing manifest rejected.  
C. Unsupported version rejected.  
D. Path traversal ZIP rejected.  
E. Missing DB rejected.  
F. Missing auth for full bootstrap rejected.  
G. Staging restore succeeds.  
H. Backed-up auth/CA restored.  
I. Existing OWNER certificate accepted.  
J. OWNER-only `/backups` accessible.  
K. No-cert request rejected.  
L. Product count matches.  
M. Avito-linked count matches.  
N. Local-only count matches.  
O. Sales count matches.  
P. Product photo rows match.  
Q. Sample media returns 200.  
R. Inventory page loads.  
S. Product detail loads.  
T. Sales/report routes load.  
U. Repairs route loads.  
V. Avito extension route loads.  
W. Backup route loads.  
X. Fresh recovery does not modify original live data.  
Y. Normal web restore still does NOT overwrite live auth.  
Z. Relevant regression suites pass.

Report exact totals.

# 13. OWNER-FACING RECOVERY RUNBOOK

Create:

`docs/disaster_recovery_new_server.md`

Assume:

> “Old server is dead. I have a Debian VPS, Git repository access and a Technoreboot backup ZIP.”

Include:

- prerequisites;
- clone repo;
- where to place ZIP;
- one bootstrap command;
- expected success;
- how to open recovered system;
- how to verify OWNER access;
- what NOT to do.

# 14. DO NOT DEPLOY PRODUCTION

Do NOT:

- change DNS;
- expose public production ports;
- migrate to selected VDS;
- issue production certs;
- perform final server hardening.

Those are later stages.

# 15. RECORDS

Create/update:

- `docs/stage07e_r1_new_server_bootstrap_and_disaster_recovery.md`
- `docs/disaster_recovery_new_server.md`
- `reports/stage07e_r1_new_server_bootstrap_and_disaster_recovery_report.md`
- `logs/2026-09-11.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE07E_R1_NEW_SERVER_BOOTSTRAP_AND_DISASTER_RECOVERY_PROMPT.md`

# 16. GIT / SAFETY

Do not commit:

- runtime DB;
- backup ZIPs;
- auth private keys;
- private CA files;
- real media;
- Avito cookies/session;
- env secrets.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

# 17. FINAL REPORT CONTRACT

Return:

```text
# Stage 07E-R1 — New Server Bootstrap and Disaster Recovery

## Recovery Architecture
BOOTSTRAP_ENTRYPOINT:
SOURCE_ORIGIN:
BACKUP_ORIGIN:
RESTORE_MODE:
ISOLATION_METHOD:

## Validation
MANIFEST:
FORMAT_VERSION:
PATH_TRAVERSAL_PROTECTION:
DB_REQUIRED:
AUTH_REQUIRED:
CHECKSUMS:

## Restored State
PRODUCTS:
AVITO_LINKED_PRODUCTS:
LOCAL_ONLY_PRODUCTS:
SALES:
PRODUCT_PHOTOS:
MEDIA_FILES:
AVITO_STATE:
AUTH_STATE:

## Auth Continuity
OLD_CA_RESTORED:
OWNER_CERT_ACCEPTED:
OWNER_ONLY_ROUTE:
NO_CERT_REJECTED:
REVOCATION_STATE_PRESERVED:

## Application Verification
GATEWAY:
INVENTORY:
PRODUCT_DETAIL:
SALES:
REPORTS:
REPAIRS:
AVITO_EXTENSION:
BACKUPS:
MEDIA_200:

## Isolation / Safety
ORIGINAL_LIVE_DB_UNCHANGED:
ORIGINAL_LIVE_AUTH_UNCHANGED:
ORIGINAL_LIVE_MEDIA_UNCHANGED:
WEB_RESTORE_AUTH_POLICY_UNCHANGED:

## Exact Test Results

## Files Created/Changed

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Recovery Runbook
PATH:
ONE_COMMAND_BOOTSTRAP:

FINAL_STATUS:
TECHNOREBOOT_STAGE07E_R1_NEW_SERVER_DISASTER_RECOVERY_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If recovery requires old running server, return BLOCKED.

If fresh recovery generates a new CA instead of restoring backed-up CA, return BLOCKED.

If testing modifies current live local data, return BLOCKED.

# 18. STOP

After implementation, isolated recovery test, docs, commit/push and report:

STOP.

Do not deploy to production VDS.
Wait for Owner acceptance.
