# TECHNOREBOOT — Stage 08C-R1-R2
## Full real VDS pre-cutover deployment with SSH access provided separately

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Stage:** `Stage 08C-R1-R2 — Real VDS Full Pre-Cutover Deployment With Provided SSH Access`

# 0. OWNER INTENT

Owner will provide all VDS access data separately to the installer/operator.

The installer may already receive:
- VDS public IP or hostname;
- SSH port;
- SSH username;
- SSH private key or a secure local path to it;
- if absolutely necessary, an initial password for one-time access bootstrap.

Do NOT require the Owner to create `vds_deploy.env` manually if access data has already been supplied directly to the installer.

Do NOT ask for SSH credentials again if they are already available in the execution environment or have been provided out-of-band.

Do NOT print, persist, commit, or log secret access material.

This stage IS ALLOWED to touch the real VDS.

Goal:

> Fully prepare the real Debian VDS, deploy the exact current `origin/main`, transfer and restore a fresh Technoreboot backup, build and start the production Docker stack, verify mTLS/RBAC and all key routes through the real VDS, create a remote backup smoke-test, then STOP the VDS application stack so no split-brain occurs before final cutover.

This is still PRE-CUTOVER.

STRICTLY FORBIDDEN:
- changing DNS;
- performing final cutover;
- stopping the current local Technoreboot;
- leaving both local and VDS application stacks active and writable after the proof;
- regenerating the Technoreboot client CA;
- exposing internal application ports publicly;
- committing secrets;
- logging passwords/private keys;
- deleting unrelated VDS data.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08C_R1_R2_REAL_VDS_FULL_PRECUTOVER_DEPLOY_WITH_PROVIDED_SSH_ACCESS_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08C_R1_R2_REAL_VDS_FULL_PRECUTOVER_DEPLOY_WITH_PROVIDED_SSH_ACCESS_PROMPT.md`

---

# 1. ACCESS CONTRACT — CREDENTIALS PROVIDED OUT-OF-BAND

Use VDS credentials already provided to the installer/operator.

Accepted access sources:
- secure installer input;
- environment variables;
- secure local secret store;
- explicit SSH key path;
- existing loaded SSH agent;
- one-time interactive password for initial key bootstrap only.

Required logical values:

```text
VDS_HOST
VDS_SSH_PORT
VDS_SSH_USER
SSH_AUTH_METHOD
```

Preferred:
- key-based SSH.

If key authentication is already working, use it.

If only password login is initially available:
1. use the password only interactively;
2. generate or reuse a local Ed25519 key;
3. install only the public key on the VDS;
4. verify key-based SSH in a second session;
5. continue with key-based SSH only;
6. never save the password to Git, files, logs, reports, shell scripts, or command history.

Do not echo:
- private key contents;
- passwords;
- production secrets.

If actual connection details are truly absent, return:

`BLOCKED_MISSING_VDS_ACCESS_DATA`

If the data exists but authentication fails, return:

`BLOCKED_VDS_SSH_AUTH_FAILED`

---

# 2. LOCAL GIT PREFLIGHT

Before touching VDS:

```text
LOCAL_BRANCH = main
LOCAL_HEAD
ORIGIN_MAIN_HEAD
LOCAL_GIT_STATUS
```

Required:

```text
LOCAL_HEAD == ORIGIN_MAIN_HEAD
LOCAL_GIT_STATUS = clean
```

If not equal, STOP and report.

Do not deploy a local unpushed worktree.

---

# 3. LOCAL LIVE BUSINESS SAFETY BASELINE

Capture exact current local state before deployment:

```text
PRODUCT_IDS
SALE_IDS
REPAIR_IDS
PHOTO_IDS
EXTERNAL_LISTING_IDS

LOCAL_DB_SHA256
LOCAL_CA_SHA256

LOCAL_CONTAINER_START_TIMES
LOCAL_CONTAINER_RESTART_COUNTS
LOCAL_GATEWAY_HEALTH
```

Also record counts:

```text
LOCAL_PRODUCTS
LOCAL_SALES
LOCAL_REPAIRS
LOCAL_PHOTOS
LOCAL_EXTERNAL_LISTINGS
```

This state must remain unchanged throughout this stage.

The local Technoreboot stack must stay running.

---

# 4. CREATE A FRESH LOCAL BACKUP

Create a NEW backup from the current local system using the accepted Technoreboot backup mechanism.

Do NOT use an old backup unless fresh backup creation is impossible.

Required backup contents:
- SQLite DB;
- storage/media;
- `data/auth`;
- Avito mutable state;
- manifest;
- backup metadata required by disaster recovery.

Record only safe metadata:

```text
BACKUP_FILENAME
BACKUP_CREATED_AT
BACKUP_SHA256
BACKUP_SIZE_BYTES
BACKUP_FORMAT_VERSION

BACKUP_PRODUCTS
BACKUP_SALES
BACKUP_REPAIRS
BACKUP_PHOTO_ROWS
BACKUP_EXTERNAL_LISTINGS
BACKUP_STORAGE_FILES
```

Do not print certificate private keys or secret file contents.

---

# 5. REAL VDS SSH PREFLIGHT

Connect to the real VDS.

Record:

```text
VDS_HOST
SSH_PORT
SSH_USER
SSH_KEY_AUTH_WORKS

OS_ID
OS_VERSION
KERNEL
ARCH
CPU_COUNT
RAM_MB
DISK_TOTAL_GB
DISK_FREE_GB
TIMEZONE
SYSTEM_TIME
```

Supported target:
- Debian 12 x64;
- Debian 13 x64.

Minimum target:
- 1 vCPU;
- >= 1.5 GB RAM;
- >= 12 GB free disk before build.

If another OS is detected, return BLOCKED unless compatibility is already explicitly proven.

Do not erase unrelated files.

---

# 6. CHECK EXISTING VDS STATE

Before installation:

Check:
- existing Docker installation;
- existing containers;
- existing `/srv/technoreboot`;
- current listeners on ports 22/80/443;
- firewall state;
- disk usage.

If an existing Technoreboot installation is found:
- do not overwrite blindly;
- inspect its state;
- return `BLOCKED_EXISTING_TECHNOREBOOT_DEPLOYMENT` unless it is clearly this same authorized staging deployment.

Do not delete unrelated services.

---

# 7. SSH LOCKOUT PROTECTION

Before firewall changes:

1. confirm current SSH works;
2. confirm key authentication works;
3. open a SECOND simultaneous SSH key-authenticated session;
4. only then modify firewall.

Do NOT change SSH port unless Owner explicitly requested it.

Do NOT disable current SSH user/root access in this stage.

The goal is safe deployment, not aggressive SSH hardening.

---

# 8. INSTALL / VERIFY DOCKER

If already installed and healthy, reuse existing Docker Engine + Compose plugin.

Otherwise install supported Debian Docker Engine + Docker Compose plugin.

Verify:

```text
docker --version
docker compose version
docker info
```

Do not install:
- Kubernetes;
- Portainer;
- PostgreSQL;
- unrelated monitoring;
- GUI packages.

Keep small-VDS footprint.

---

# 9. SERVER DIRECTORY LAYOUT

Create:

```text
/srv/technoreboot/
  app/
  data/
  secrets/
  deploy/
```

Use:
- `/srv/technoreboot/app` — Git checkout;
- `/srv/technoreboot/data` — persistent mutable state;
- `/srv/technoreboot/secrets` — production env + temporary server TLS;
- `/srv/technoreboot/deploy` — transferred backup and deployment artifacts.

Permissions:
- secrets/private keys: `0600`;
- secret directory: restrictive;
- mutable data writable only as required.

Do not use `/root/tbootit` as final layout.

---

# 10. CLONE EXACT ORIGIN/MAIN ON VDS

Clone the repository directly from Git into:

`/srv/technoreboot/app`

Do NOT SCP the local source tree.

Required:

```text
REMOTE_GIT_HEAD
LOCAL_ORIGIN_MAIN_HEAD
HEAD_MATCH
```

Acceptance:

```text
REMOTE_GIT_HEAD == LOCAL_ORIGIN_MAIN_HEAD
```

---

# 11. TRANSFER FRESH BACKUP

Upload the fresh backup securely to:

`/srv/technoreboot/deploy/`

Use:
- SCP;
- SFTP;
- equivalent SSH-secured transfer.

Verify SHA256 both sides:

```text
LOCAL_BACKUP_SHA256
REMOTE_BACKUP_SHA256
SHA_MATCH
```

If hashes differ:
STOP immediately.

Do not continue with corrupted backup.

---

# 12. RESTORE MUTABLE STATE ON VDS

Restore into:

`/srv/technoreboot/data`

Use the existing accepted bootstrap/disaster-recovery tooling from the repository.

Restore:
- DB;
- media/storage;
- auth/CA/certificate registry;
- Avito mutable state;
- backup state as required by accepted recovery design.

CRITICAL:
- do NOT generate a new client CA;
- do NOT replace restored auth state;
- do NOT issue a replacement OWNER certificate;
- preserve revocation registry.

After restore verify:

```text
REMOTE_PRODUCTS == BACKUP_PRODUCTS
REMOTE_SALES == BACKUP_SALES
REMOTE_REPAIRS == BACKUP_REPAIRS
REMOTE_PHOTO_ROWS == BACKUP_PHOTO_ROWS
REMOTE_EXTERNAL_LISTINGS == BACKUP_EXTERNAL_LISTINGS
REMOTE_STORAGE_FILES == BACKUP_STORAGE_FILES
```

Also verify:

```text
REMOTE_CA_SHA256 == LOCAL_CA_SHA256
OWNER_CERT_SERIAL_MATCH = true
OWNER_CERT_FINGERPRINT_MATCH = true
REVOCATION_REGISTRY_PRESENT = true
AVITO_STATE_RESTORED = true
```

---

# 13. CREATE PRODUCTION ENV ON VDS

Create:

`/srv/technoreboot/secrets/production.env`

Required:

```text
APP_ENV=production
TECHNOREBOOT_DATA_ROOT=/srv/technoreboot/data
TECHNOREBOOT_HOSTNAME=<VDS_PUBLIC_IP_OR_TEMP_HOST>
```

Generate strong random values for:
- `CORE_API_TOKEN`;
- `CART_SESSION_SECRET`;
- any other required production secret.

Do NOT print their values.

Report only:

```text
CORE_API_TOKEN_PRESENT = true
CORE_API_TOKEN_LENGTH >= 32
CART_SESSION_SECRET_PRESENT = true
CART_SESSION_SECRET_LENGTH >= 32
DEV_DEFAULTS_USED = false
```

File mode:

`0600`

Do not commit this file.

---

# 14. TEMPORARY PRE-CUTOVER SERVER TLS

Because DNS is NOT changed in this stage:

Generate a temporary server TLS certificate for the VDS public IP.

Requirements:
- SAN includes VDS public IP;
- separate from Technoreboot client CA;
- private key stored under `/srv/technoreboot/secrets`;
- mode `0600`;
- clearly documented as PRE-CUTOVER TEMPORARY TLS.

Do NOT regenerate client CA.

The later cutover stage will configure final trusted hostname/domain TLS.

---

# 15. PRODUCTION CONFIG VALIDATION ON REAL VDS

Before build:

Run:

```text
docker compose -f deploy/production/docker-compose.prod.yml config
```

using `/srv/technoreboot/secrets/production.env`.

Verify:
- only gateway publishes host ports;
- internal published ports = 0;
- data root = `/srv/technoreboot/data`;
- no source bind mounts;
- no `network_mode: host`;
- no privileged containers;
- no Docker socket mount;
- restart policies present;
- log rotation present;
- healthchecks present.

If invalid:
STOP before build.

---

# 16. FIREWALL

After SSH key auth and second session are proven:

Allow only:
- active SSH port;
- 80/tcp;
- 443/tcp.

Deny other unsolicited inbound ports.

Use one firewall mechanism only:
- nftables;
- UFW;
- or existing provider firewall.

Do not stack competing firewall managers.

After applying:
- second SSH session still works;
- 80 reachable;
- 443 reachable when stack starts;
- internal app ports not externally reachable.

---

# 17. BUILD PRODUCTION IMAGES ON REAL VDS

From:

`/srv/technoreboot/app`

Build from source using:

`deploy/production/docker-compose.prod.yml`

Do not import developer-machine images.

Record:

```text
REMOTE_BUILD_HEAD
REMOTE_IMAGES
REMOTE_IMAGE_IDS
BUILD_RESULT
```

If build hits memory pressure:
- measure memory;
- temporary swap may be added;
- document size/location;
- do not weaken security or skip services.

---

# 18. START REAL VDS STACK — VERIFICATION WINDOW

Start all production services:

- gateway;
- core;
- admin-shell;
- inventory-sales-module;
- repairs-module;
- avito-module.

Verify:

```text
ALL_SERVICES_RUNNING = true
ALL_SERVICES_HEALTHY = true
PUBLIC_PORTS = 80,443
INTERNAL_PUBLIC_PORTS = 0
```

This is a verification-only window.

Do NOT perform real business writes on VDS:
- no sales;
- no product edits;
- no repairs edits;
- no Avito imports;
- no certificate changes.

---

# 19. REMOTE HTTPS + MTLS VERIFICATION

From the Owner PC, test the real VDS through its public IP.

Use:
- temporary server TLS trust material;
- existing OWNER client certificate/key.

Verify:

```text
HTTP_TO_HTTPS = PASS
HTTPS_GATEWAY = PASS

NO_CLIENT_CERT = REJECTED
OWNER_CERT = ACCEPTED

/ = 200
/inventory/products = 200
/inventory/sales = 200
/repairs/repairs = 200
/avito/extension = 200
/backups = 200 OWNER
/certificates = 200 OWNER
```

If USER certificate is safely available:

```text
/inventory/products = 200 USER
/backups = 403 USER
/certificates = 403 USER
```

Verify remote application counts equal restored backup counts.

---

# 20. MEDIA VERIFICATION

Select at least 3 restored media files.

Verify through the VDS gateway:

```text
MEDIA_1 = HTTP 200
MEDIA_2 = HTTP 200
MEDIA_3 = HTTP 200
```

Also verify storage tree file count matches backup.

---

# 21. REMOTE BACKUP SMOKE TEST

Create ONE fresh backup on the VDS using the supported Technoreboot backup mechanism.

Verify:
- backup succeeds;
- manifest valid;
- file stored under persistent VDS backup path;
- backup includes expected mutable state;
- auth state included per accepted contract.

Do NOT restore this backup.

Record filename + SHA256 only.

---

# 22. SPLIT-BRAIN SAFETY — STOP VDS APPLICATION

After successful verification:

STOP the VDS application stack.

Preferred:

```text
docker compose -f deploy/production/docker-compose.prod.yml stop
```

Do NOT delete:
- images;
- restored data;
- repository;
- secrets;
- backup;
- Docker volumes/network metadata unless necessary.

Required final state:

```text
LOCAL_STACK_RUNNING = true
VDS_STACK_RUNNING = false
DNS_CHANGED = false
CUTOVER_PERFORMED = false
```

Reason:
Until final cutover, there must not be two simultaneously active writable Technoreboot systems.

---

# 23. VERIFY LOCAL SYSTEM AFTER VDS WORK

Compare exact local state with preflight.

Required:

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

# 24. VDS STATUS DOCUMENT

Create:

`docs/vds_pre_cutover_status.md`

Include:
- VDS public IP/hostname;
- OS/version;
- Docker/Compose versions;
- deployed Git commit;
- backup/restore result;
- firewall state;
- public ports;
- mTLS result;
- route verification result;
- temporary TLS status;
- explicit final line:

`VDS APPLICATION STACK IS STOPPED PENDING FINAL CUTOVER`

Do not include:
- passwords;
- private key paths if sensitive;
- private keys;
- production secret values.

---

# 25. REQUIRED PROOFS

A. SSH access works.  
B. Key auth works.  
C. Debian supported.  
D. Resources adequate.  
E. Docker/Compose healthy.  
F. Remote Git HEAD equals origin/main.  
G. Fresh local backup created.  
H. Backup upload SHA matches.  
I. DB restored.  
J. media restored.  
K. auth/CA restored.  
L. OWNER identity preserved.  
M. revocation state preserved.  
N. Avito state restored.  
O. production secrets secure.  
P. no dev secret used.  
Q. only gateway publishes application ports.  
R. firewall preserves SSH and only 80/443 app exposure.  
S. production build succeeds on VDS.  
T. all services start healthy.  
U. HTTPS works.  
V. no-cert rejected.  
W. OWNER accepted.  
X. OWNER-only routes protected.  
Y. 3 media files return 200.  
Z. remote backup creation succeeds.  
AA. local business data unchanged.  
AB. local containers not restarted.  
AC. VDS application stack STOPPED after proof.  
AD. DNS unchanged.  
AE. cutover not performed.

---

# 26. DOCUMENTATION / RECORDS

Create:

`docs/stage08c_r1_real_vds_pre_cutover_deployment.md`

`docs/vds_pre_cutover_status.md`

`reports/stage08c_r1_real_vds_pre_cutover_deployment_report.md`

Update:

`logs/2026-09-12.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE08C_R1_R2_REAL_VDS_FULL_PRECUTOVER_DEPLOY_WITH_PROVIDED_SSH_ACCESS_PROMPT.md`

---

# 27. GIT SAFETY

Never commit:
- SSH credentials;
- SSH private keys;
- passwords;
- `.secrets/`;
- `production.env`;
- temporary TLS private key;
- client private keys;
- backup ZIP;
- runtime DB;
- real media.

Commit only:
- docs;
- safe scripts/tests if genuinely needed;
- reports/logs.

Push `origin/main`.

Verify clean local worktree.

---

# 28. FINAL REPORT CONTRACT

Return exactly this structure:

```text
# Stage 08C-R1-R2 — Real VDS Full Pre-Cutover Deployment With Provided SSH Access

## Access
VDS_HOST:
SSH_PORT:
SSH_USER:
SSH_AUTH_METHOD:
KEY_AUTH_WORKS:
PASSWORD_USED_ONLY_INTERACTIVELY:
PASSWORD_STORED_ANYWHERE:

## Local Preflight
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
HEAD_MATCH:
LOCAL_GIT_STATUS:
LOCAL_PRODUCTS:
LOCAL_SALES:
LOCAL_REPAIRS:
LOCAL_PHOTOS:
LOCAL_EXTERNAL_LISTINGS:
LOCAL_DB_SHA256:
LOCAL_CA_SHA256:

## VDS
OS_ID:
OS_VERSION:
ARCH:
CPU_COUNT:
RAM_MB:
DISK_TOTAL_GB:
DISK_FREE_GB:
DOCKER_VERSION:
COMPOSE_VERSION:

## Source
REMOTE_REPO_PATH:
/REMOTE_HEAD:
LOCAL_ORIGIN_MAIN_HEAD:
HEAD_MATCH:

## Fresh Backup
BACKUP_FILENAME:
BACKUP_CREATED_AT:
BACKUP_SIZE_BYTES:
BACKUP_SHA256:
BACKUP_FORMAT_VERSION:
BACKUP_PRODUCTS:
BACKUP_SALES:
BACKUP_REPAIRS:
BACKUP_PHOTO_ROWS:
BACKUP_EXTERNAL_LISTINGS:
BACKUP_STORAGE_FILES:

## Backup Transfer
LOCAL_SHA256:
REMOTE_SHA256:
SHA_MATCH:

## Restore
REMOTE_PRODUCTS:
REMOTE_SALES:
REMOTE_REPAIRS:
REMOTE_PHOTO_ROWS:
REMOTE_EXTERNAL_LISTINGS:
REMOTE_STORAGE_FILES:
CA_SHA256_MATCH:
OWNER_CERT_SERIAL_MATCH:
OWNER_CERT_FINGERPRINT_MATCH:
REVOCATION_STATE_PRESERVED:
AVITO_STATE_RESTORED:

## Production Secrets
APP_ENV:
CORE_API_TOKEN_PRESENT:
CORE_API_TOKEN_LENGTH_OK:
CART_SESSION_SECRET_PRESENT:
CART_SESSION_SECRET_LENGTH_OK:
DEV_DEFAULTS_USED:

## Network / Firewall
PUBLIC_PORTS:
INTERNAL_PUBLIC_PORTS:
FIREWALL:
SSH_SECOND_SESSION_OK:
PRIVILEGED_CONTAINERS:
HOST_NETWORK:
DOCKER_SOCKET_MOUNTS:
SOURCE_BIND_MOUNTS:

## VDS Build
BUILD_RESULT:
REMOTE_BUILD_HEAD:
REMOTE_IMAGES:
REMOTE_IMAGE_IDS:

## Runtime Proof
ALL_SERVICES_RUNNING:
ALL_SERVICES_HEALTHY:
HTTP_TO_HTTPS:
HTTPS_GATEWAY:
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
REMOTE_COUNTS_MATCH_BACKUP:
MEDIA_1:
MEDIA_2:
MEDIA_3:
REMOTE_BACKUP_CREATED:
REMOTE_BACKUP_SHA256:

## Split-Brain Safety
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

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08C_R1_R2_REAL_VDS_PRE_CUTOVER_PROVEN

REAL_VDS_TOUCHED: true
DNS_CHANGED: false
CUTOVER_PERFORMED: false
VDS_STACK_STOPPED_PENDING_CUTOVER: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- required VDS access data is truly absent;
- SSH authentication fails;
- backup hash mismatches;
- restore counts mismatch;
- CA/OWNER identity mismatch;
- mTLS fails;
- internal service ports are public;
- local business data changes;
- local containers restart;
- VDS stack remains running after proof.

---

# 29. STOP

After successful real-VDS proof and deliberate VDS stack stop:

STOP.

Do not change DNS.
Do not perform final cutover.
Wait for Owner acceptance.
