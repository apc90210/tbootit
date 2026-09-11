# TECHNOREBOOT — Stage 07E-R1-R1
## Prove disaster recovery on a truly isolated recovered Docker stack

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07E-R1-R1 — Real Isolated Recovered Stack Proof`

# 0. WHY THIS REVISION EXISTS

Stage07E-R1 is NOT accepted yet.

The previous report implemented useful recovery tooling, but the evidence does not yet prove that a **fresh recovered application stack** actually booted and served the restored backup.

Observed execution included:

```text
python scripts/bootstrap_restore.py ... --data-dir C:\tbootit\.tmp_test_isolated_data --skip-containers --json
```

That proves isolated extraction/validation, but explicitly skips containers.

The later `verify_stage07e_r1_disaster_recovery_live.py` checks are not sufficient unless they are proven to target a **separate recovered Docker stack** rather than the already-running normal Technoreboot stack on port 8443.

The disaster-recovery acceptance criterion is:

> A separate recovered Docker stack, using restored data/auth/media from the backup, must boot on different ports/project name and serve real application routes with the old OWNER certificate.

Do NOT modify the current live/local working stack or its data.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07E_R1_R1_REAL_ISOLATED_RECOVERED_STACK_PROOF_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07E_R1_R1_REAL_ISOLATED_RECOVERED_STACK_PROOF_PROMPT.md`

# 1. KEEP PREVIOUS IMPLEMENTATION

Keep:
- `scripts/bootstrap_restore.py`
- `scripts/bootstrap_restore.sh`
- validation / Zip Slip protection
- staging restore
- fresh-server auth restore policy
- normal web restore preserving live auth
- runbook/docs
- tests that are already valid

Do not rewrite working code unnecessarily.

# 2. CREATE A TRULY ISOLATED RECOVERY TARGET

Use a separate temporary workspace/data root AND a separate Docker Compose project name.

Example concept:

```text
workspace:
C:\tbootit\.recovery-test\<run-id>\repo

data root:
C:\tbootit\.recovery-test\<run-id>\data

compose project:
technoreboot-recovery-<run-id>
```

Use alternate host ports, for example:

```text
recovery gateway HTTPS: 9443
```

and any required internal/admin ports different from the live stack.

The current production-like local stack on 8443 must remain running and untouched.

# 3. RESTORE BACKUP INTO THAT TARGET

Use:

`TECHNOREBOOT_BACKUP_2026-09-11_103952.zip`

or the current valid backup selected for the stage.

The recovery target must get:
- restored SQLite DB;
- storage/media;
- auth/CA/cert registry;
- Avito mutable state;
- required runtime directories.

No references/bind mounts to the normal live `C:\tbootit\data` are allowed.

Prove all bind mounts point to the recovery sandbox.

# 4. ACTUALLY START THE RECOVERED STACK

Do NOT use `--skip-containers` for the acceptance proof.

Start the isolated recovered stack using a dedicated Compose project and alternate host ports.

Report exact container names and ports.

Required:

```text
RECOVERY_CORE_CONTAINER:
RECOVERY_ADMIN_CONTAINER:
RECOVERY_GATEWAY_CONTAINER:
RECOVERY_AVITO_CONTAINER:
RECOVERY_INVENTORY_CONTAINER:
RECOVERY_REPAIRS_CONTAINER:
RECOVERY_GATEWAY_URL:
```

All must be from the recovery project, not the normal live project.

# 5. PROVE REQUESTS HIT THE RECOVERED STACK

Before HTTP verification, create deterministic proof that requests to recovery gateway are served by restored data.

Use backup-specific facts that differ from current live state where possible.

For example compare:
- recovered product count from backup;
- recovered sales count;
- recovered repair count;
- recovered photo count.

The previous report states backup values:

```text
PRODUCTS: 227
SALES: 50
REPAIRS: 66
PRODUCT_PHOTOS: 490
```

Verify these values from the **recovery DB** and through application behavior where practical.

Also report current live counts separately, so it is impossible to confuse stacks.

Required:

```text
LIVE_PRODUCTS:
RECOVERY_PRODUCTS:
LIVE_SALES:
RECOVERY_SALES:
LIVE_REPAIRS:
RECOVERY_REPAIRS:
LIVE_PHOTOS:
RECOVERY_PHOTOS:
```

# 6. MTLS MUST USE RESTORED AUTH

Against the recovery gateway only:

- existing OWNER certificate must return 200;
- no certificate must be rejected;
- `/backups` OWNER-only must work;
- `/certificates` must work;
- restored CA fingerprint must equal accepted historical CA;
- restored OWNER fingerprint/serial must match historical OWNER;
- revoked-state registry must be loaded from the restored sandbox.

Do not read auth from normal live `data/auth`.

Prove certificate files used by recovery gateway are physically under recovery sandbox.

# 7. ROUTE VERIFICATION ON RECOVERY URL ONLY

Against recovery gateway URL (for example `https://127.0.0.1:9443`), verify:

- `/`
- `/inventory/products`
- one real `/inventory/products/{id}` or canonical detail route
- `/sales`
- `/reports/sales`
- `/repairs`
- `/avito/extension`
- `/backups`
- `/certificates`
- at least 3 `/media/...` files

All checks must log the recovery URL explicitly.

Do not count checks against 8443 as recovery proof.

# 8. ISOLATION PROOF

Before recovery test calculate fingerprints/hashes of live:

- DB;
- auth registry/CA;
- representative media directory state.

After recovered-stack teardown, verify those live hashes/sets are unchanged.

Also verify:
- no live container was restarted;
- no live bind mount path was written by recovery procedure;
- no live DB row count changed.

Required:

```text
LIVE_DB_SHA_BEFORE:
LIVE_DB_SHA_AFTER:
LIVE_CA_SHA_BEFORE:
LIVE_CA_SHA_AFTER:
LIVE_PRODUCT_IDS_BEFORE_EQUALS_AFTER:
LIVE_SALE_IDS_BEFORE_EQUALS_AFTER:
LIVE_CONTAINERS_RESTARTED: 0
```

# 9. TEARDOWN

After successful verification:
- stop/remove only the recovery Compose project;
- remove temporary recovery workspace/data if safe;
- never run `docker compose down` without the dedicated recovery project;
- verify normal live stack remains healthy.

# 10. AUTOMATED TEST GUARD

Add a regression/integration verification that fails if:
- recovery URL equals live URL;
- recovery data directory resolves inside live `data`;
- recovery compose project equals normal project;
- any recovery service bind-mounts normal live data.

# 11. OWNER MANUAL CHECK

No complex Owner action is required for this revision.

Antigravity must provide enough evidence from the truly isolated stack.

Owner may optionally open the recovery URL in browser while it is temporarily running, but automated proof is mandatory.

If practical, leave recovery stack running only until report completion and specify URL. Otherwise cleanly tear it down after proof.

# 12. REQUIRED TESTS

A. Recovery project name differs from live.
B. Recovery gateway port differs from 8443.
C. Recovery data root differs from live data root.
D. Full restore executes without `--skip-containers`.
E. Recovery containers start healthy.
F. Recovery DB contains backup counts.
G. Recovery media exists.
H. Existing OWNER cert authenticates to recovery gateway.
I. No-cert rejected by recovery gateway.
J. `/backups` works on recovery gateway.
K. `/certificates` works on recovery gateway.
L. inventory route uses recovery DB.
M. product detail works.
N. sales/reports use recovery DB.
O. repairs uses recovery DB.
P. Avito extension route works.
Q. three restored media files return 200.
R. restored CA fingerprint matches backup.
S. restored OWNER fingerprint/serial matches backup.
T. revoked registry preserved.
U. current live DB unchanged.
V. current live auth unchanged.
W. current live media unchanged.
X. current live containers not restarted.
Y. recovery teardown does not affect live stack.
Z. normal web restore auth-preservation regression still passes.

# 13. DOCUMENTATION

Update:

`docs/stage07e_r1_new_server_bootstrap_and_disaster_recovery.md`

`docs/disaster_recovery_new_server.md`

Create:

`reports/stage07e_r1_r1_real_isolated_recovered_stack_proof_report.md`

Update:

`logs/2026-09-11.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE07E_R1_R1_REAL_ISOLATED_RECOVERED_STACK_PROOF_PROMPT.md`

# 14. GIT / SAFETY

Do not commit:
- recovery DB;
- backup ZIP;
- recovery auth private keys;
- restored media;
- cookies;
- temporary recovery workspace;
- secrets.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

# 15. FINAL REPORT CONTRACT

Return:

```text
# Stage 07E-R1-R1 — Real Isolated Recovered Stack Proof

## Live Stack
LIVE_PROJECT:
LIVE_GATEWAY_URL:
LIVE_PRODUCTS:
LIVE_SALES:
LIVE_REPAIRS:
LIVE_PHOTOS:

## Recovery Stack
RECOVERY_PROJECT:
RECOVERY_DATA_ROOT:
RECOVERY_GATEWAY_URL:
RECOVERY_CONTAINERS:
RECOVERY_USED_SKIP_CONTAINERS: false

## Restored Backup State
RECOVERY_PRODUCTS:
RECOVERY_SALES:
RECOVERY_REPAIRS:
RECOVERY_PHOTOS:
RECOVERY_MEDIA_FILES:
RECOVERY_AVITO_STATE:

## Auth Proof
RECOVERY_CA_PATH:
RECOVERY_CA_FINGERPRINT:
RECOVERY_OWNER_CERT_PATH:
RECOVERY_OWNER_FINGERPRINT:
RECOVERY_OWNER_SERIAL:
OWNER_CERT_ACCEPTED_ON_RECOVERY_URL:
NO_CERT_REJECTED_ON_RECOVERY_URL:
REVOCATION_STATE_PRESERVED:

## Recovery Route Proof
ROOT:
INVENTORY:
PRODUCT_DETAIL:
SALES:
REPORTS:
REPAIRS:
AVITO_EXTENSION:
BACKUPS:
CERTIFICATES:
MEDIA_1:
MEDIA_2:
MEDIA_3:

## Isolation Proof
LIVE_DB_SHA_BEFORE:
LIVE_DB_SHA_AFTER:
LIVE_CA_SHA_BEFORE:
LIVE_CA_SHA_AFTER:
LIVE_PRODUCT_IDS_UNCHANGED:
LIVE_SALE_IDS_UNCHANGED:
LIVE_CONTAINERS_RESTARTED:
LIVE_STACK_HEALTH_AFTER:

## Teardown
RECOVERY_PROJECT_REMOVED:
LIVE_STACK_STILL_RUNNING:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE07E_R1_R1_REAL_ISOLATED_RECOVERY_PROVEN

OWNER_MANUAL_CHECK_REQUIRED: false
PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If application route verification is performed against the normal 8443 stack instead of the recovered stack, return BLOCKED.

If the recovery stack mounts any normal live data/auth/media directory, return BLOCKED.

If current live containers must be restarted for recovery proof, return BLOCKED.

# 16. STOP

After real isolated recovered-stack proof, teardown, tests, docs, commit/push and report:

STOP.

Do not deploy to production VDS.
Wait for Owner acceptance.
