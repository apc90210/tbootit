# TECHNOREBOOT — Stage 08C-R1
## Real VDS provisioning and first production deployment — NO cutover

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 08C-R1 — Real VDS Provisioning and First Production Deployment (No Cutover)`

# 0. EXECUTION CONTRACT

Stage08B production baseline is accepted.

This is the FIRST stage allowed to touch the real VDS.

Goal:

> Provision the real Debian VDS, clone the exact committed production code, transfer a fresh Technoreboot backup, restore all mutable state, build and start the production Docker stack on the VDS, verify it over the public VDS IP with mTLS, then STOP the application stack again so that the local workstation remains the only active production writer until the later DNS/cutover stage.

IMPORTANT:

- Do NOT change DNS.
- Do NOT perform public cutover.
- Do NOT stop the current local Technoreboot stack.
- Do NOT move the canonical business workflow away from the local machine yet.
- Do NOT issue a replacement client CA.
- Do NOT expose internal Docker services.
- Do NOT leave two simultaneously active writable Technoreboot installations after this stage.
- Do NOT commit secrets.
- Do NOT log passwords/private keys.
- If SSH access parameters are missing, return BLOCKED with the exact missing variable names. Do not guess.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08C_R1_REAL_VDS_PROVISION_AND_FIRST_DEPLOY_NO_CUTOVER_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08C_R1_REAL_VDS_PROVISION_AND_FIRST_DEPLOY_NO_CUTOVER_PROMPT.md`

---

# 1. LOCAL DEPLOYMENT ACCESS CONTRACT

Do not put SSH credentials in Git or reports.

Read VDS connection settings from a local untracked file:

`C:\tbootit\.secrets\vds_deploy.env`

Supported variables:

```text
TECHNOREBOOT_VDS_HOST=
TECHNOREBOOT_VDS_SSH_PORT=22
TECHNOREBOOT_VDS_SSH_USER=
TECHNOREBOOT_VDS_SSH_KEY_PATH=
```

Optional:

```text
TECHNOREBOOT_VDS_EXPECTED_OS=debian
```

Rules:

- SSH key path must reference a local private key outside Git.
- Do not support plaintext SSH passwords in the env file.
- Never print private key content.
- `.secrets/` must be gitignored.
- If required values are missing, STOP with `BLOCKED_MISSING_VDS_ACCESS_CONFIG`.

Before touching the VDS, confirm the local git worktree is clean and:

```text
LOCAL_HEAD == ORIGIN_MAIN_HEAD
```

---

# 2. LOCAL LIVE DATA SAFETY BASELINE

Before VDS work capture:

```text
LOCAL_PRODUCTS
LOCAL_SALES
LOCAL_REPAIRS
LOCAL_PHOTOS
LOCAL_EXTERNAL_LISTINGS
LOCAL_DB_SHA256
LOCAL_CA_SHA256
LOCAL_LIVE_CONTAINER_STARTED_AT
LOCAL_LIVE_CONTAINER_RESTART_COUNTS
```

Capture exact ID sets.

The local installation must remain running and unchanged throughout the stage.

---

# 3. CREATE A FRESH DEPLOYMENT BACKUP

Create one fresh Technoreboot backup from the current local system using the existing accepted backup mechanism.

Do NOT use an old backup unless fresh backup creation fails.

Record only safe metadata:

```text
BACKUP_FILENAME
BACKUP_CREATED_AT
BACKUP_SHA256
BACKUP_SIZE
BACKUP_FORMAT_VERSION
PRODUCT_COUNT
SALE_COUNT
REPAIR_COUNT
PHOTO_ROW_COUNT
EXTERNAL_LISTING_COUNT
```

The backup must include:
- DB;
- storage/media;
- auth/CA/registry;
- Avito mutable state;
- manifest.

Do not print private material from the archive.

---

# 4. SSH PREFLIGHT — REAL VDS

Connect using key-based SSH.

Record:

```text
VDS_HOST
SSH_USER
SSH_PORT
OS_ID
OS_VERSION
KERNEL
ARCH
CPU_COUNT
RAM_MB
DISK_TOTAL
DISK_FREE
CURRENT_TIME
TIMEZONE
```

Supported target:
- Debian 12 or Debian 13 x64.

If another OS is present, return BLOCKED unless compatibility is already proven.

Check:
- at least 1 vCPU;
- at least 1.5 GB RAM;
- at least 12 GB free disk before build;
- system clock reasonable;
- no existing conflicting Technoreboot deployment;
- ports 80/443 availability.

Do not erase unrelated server data.

---

# 5. SSH SAFETY

Before changing firewall or SSH configuration:

- confirm current SSH session works;
- confirm key authentication works;
- record current SSH port;
- never disable working access before a second key-auth test succeeds.

This stage does NOT need aggressive SSH hardening.

Do NOT change the SSH port unless already configured by Owner.
Do NOT disable root/user access in a way that risks lockout.

---

# 6. INSTALL / VERIFY DOCKER

If Docker Engine + Compose plugin are already available, use them.

Otherwise install them using the supported Debian method.

Required:

```text
docker --version
docker compose version
docker info
```

Do not install:
- GUI;
- Kubernetes;
- Portainer;
- databases not used by the project;
- unrelated monitoring stacks.

Target is the small VDS footprint.

---

# 7. SERVER DIRECTORY LAYOUT

Use:

```text
/srv/technoreboot/
  app/
  data/
  secrets/
  deploy/
```

Recommended:

```text
/srv/technoreboot/app      -> Git clone
/srv/technoreboot/data     -> persistent mutable data
/srv/technoreboot/secrets  -> production .env and temporary server TLS
```

Set restrictive permissions.

Private keys and production env:

```text
0600
```

Mutable directories must be writable only as required.

Do not use `/root/tbootit` as the permanent application layout.

---

# 8. CLONE EXACT ORIGIN/MAIN

On the VDS:

```text
git clone <repository> /srv/technoreboot/app
```

Then verify:

```text
REMOTE_GIT_HEAD == LOCAL_ORIGIN_MAIN_HEAD
```

Do not copy the local source tree via SCP.

Source must come from Git.

---

# 9. TRANSFER BACKUP SECURELY

Upload the fresh backup via SSH/SCP/SFTP to a temporary restricted path such as:

```text
/srv/technoreboot/deploy/<backup>.zip
```

Verify SHA256 on both sides:

```text
LOCAL_BACKUP_SHA256 == REMOTE_BACKUP_SHA256
```

If hashes differ, STOP.

---

# 10. RESTORE MUTABLE STATE ON VDS

Use the accepted disaster-recovery/bootstrap tooling from Git.

Restore the backup into:

`/srv/technoreboot/data`

Required:
- restore DB;
- storage/media;
- auth/CA/registry;
- Avito mutable state;
- backup state where applicable.

CRITICAL:

- restore the existing backed-up client CA;
- do NOT generate a new client CA;
- preserve OWNER certificate trust and revocation registry.

After restore compare:

```text
REMOTE_PRODUCTS == BACKUP_PRODUCTS
REMOTE_SALES == BACKUP_SALES
REMOTE_REPAIRS == BACKUP_REPAIRS
REMOTE_PHOTOS == BACKUP_PHOTOS
REMOTE_EXTERNAL_LISTINGS == BACKUP_EXTERNAL_LISTINGS
```

Also compare safe CA fingerprint and OWNER serial/fingerprint.

---

# 11. PRODUCTION SECRETS ON VDS

Create an untracked production env file under:

`/srv/technoreboot/secrets/production.env`

Generate fresh strong random application secrets for:
- Core API token;
- cart/session secret;
- any other required production-only secret.

Do NOT reuse dev defaults.

Set:

```text
APP_ENV=production
TECHNOREBOOT_DATA_ROOT=/srv/technoreboot/data
```

Do not print secret values.

Report only:

```text
SECRET_PRESENT=true
SECRET_LENGTH>=32
DEV_DEFAULT_USED=false
```

---

# 12. TEMPORARY SERVER TLS FOR PRE-CUTOVER TEST

DNS must NOT be changed in this stage.

For the pre-cutover VDS proof, generate a TEMPORARY server TLS certificate specifically for the VDS IP.

Requirements:
- SAN contains the public VDS IP;
- separate from the Technoreboot client CA;
- stored only under `/srv/technoreboot/secrets/`;
- private key mode 0600;
- explicitly marked TEMPORARY / PRE-CUTOVER.

Do NOT replace or regenerate the existing Technoreboot client CA.

This temporary server certificate is for automated pre-cutover verification only.

The next cutover stage will decide the final trusted server TLS certificate/domain strategy.

---

# 13. PRODUCTION HOSTNAME FOR PRE-CUTOVER

For this stage set:

```text
TECHNOREBOOT_HOSTNAME=<VDS_PUBLIC_IP>
```

only if supported by the Nginx template.

If hostname validation requires a DNS name, use a clearly temporary internal value and test through explicit Host header.

Do NOT invent or configure public DNS.

---

# 14. FIREWALL

Apply a minimal firewall only after SSH key access is proven.

Allow:
- active SSH port;
- 80/tcp;
- 443/tcp.

Deny other unsolicited inbound traffic.

Use either:
- nftables;
- UFW;
- provider firewall if already present;

but do not stack conflicting firewall managers unnecessarily.

After applying rules:
1. open a second SSH connection;
2. prove SSH still works;
3. prove internal application ports are not reachable externally.

Required external exposure:

```text
SSH
80
443
```

Internal services must remain Docker-network only.

---

# 15. BUILD PRODUCTION STACK ON REAL VDS

From:

`/srv/technoreboot/app`

use:

`deploy/production/docker-compose.prod.yml`

Build from source on the VDS.

Do not depend on developer-machine Docker images.

Record:

```text
REMOTE_BUILD_HEAD
REMOTE_IMAGES
REMOTE_IMAGE_IDS
```

Target memory is small; build sequentially if required to avoid OOM.

If build OOMs:
- do not weaken production safety;
- report memory usage;
- use temporary swap only if documented and safe.

---

# 16. START REAL VDS STACK — TEMPORARY PRE-CUTOVER WINDOW

Start production stack on real VDS.

Verify:
- all 6 services running/healthy;
- only gateway publishes 80/443;
- internal ports not published;
- bounded logs active;
- restart policies active.

This is a short verification window only.

Local workstation remains canonical.

Do NOT perform:
- sales;
- product edits;
- Avito imports;
- repair edits

on the VDS.

---

# 17. REMOTE MTLS VERIFICATION

From the local machine test the VDS over its public IP.

Use:
- temporary server TLS trust material;
- existing OWNER client certificate/key.

Verify:

```text
HTTPS_GATEWAY = 200
NO_CLIENT_CERT = rejected
OWNER_CERT = accepted
/backups = 200 OWNER
/certificates = 200 OWNER
/inventory/products = 200
/inventory/sales = 200
/repairs/repairs = 200
/avito/extension = 200
```

If a USER client certificate is safely available, verify:
- operational route accessible;
- `/backups` -> 403;
- `/certificates` -> 403.

Verify restored counts from the VDS application.

---

# 18. MEDIA VERIFICATION

Check at least 3 restored media files through the remote Gateway.

Required:

```text
MEDIA_1 = HTTP 200
MEDIA_2 = HTTP 200
MEDIA_3 = HTTP 200
```

Also verify file counts on the VDS match the fresh backup tree.

---

# 19. REMOTE BACKUP SMOKE

On the VDS production stack, create one new backup through the supported backend/UI path without downloading it publicly.

Verify:
- backup succeeds;
- manifest valid;
- file lands under persistent `/srv/technoreboot/data/backups`;
- VDS auth state is included according to accepted backup contract.

Do not restore it during this stage.

---

# 20. SPLIT-BRAIN SAFETY — STOP VDS APPLICATION AFTER PROOF

After all verification succeeds:

STOP the Technoreboot application stack on the VDS.

Preferred:

```text
docker compose ... stop
```

Do NOT delete:
- images;
- restored data;
- env/secrets;
- repository;
- backup.

End-state:

```text
LOCAL_STACK_RUNNING = true
VDS_STACK_RUNNING = false
DNS_CHANGED = false
```

Reason:
Until the later cutover stage, there must not be two simultaneously active writable business systems.

---

# 21. VERIFY LOCAL SYSTEM AGAIN

After all real-VDS work verify local:

```text
PRODUCT_IDS unchanged
SALE_IDS unchanged
REPAIR_IDS unchanged
PHOTO_IDS unchanged
EXTERNAL_LISTING_IDS unchanged
LOCAL_CONTAINERS_RESTARTED = 0
LOCAL_GATEWAY_HEALTH = true
```

No local business state may be changed by the deployment test.

---

# 22. OWNER-FACING VDS STATUS DOC

Create:

`docs/vds_pre_cutover_status.md`

Include:
- provider-neutral server identity (IP may be included if Owner-safe);
- OS;
- Docker version;
- deployed Git commit;
- data restore result;
- service verification;
- firewall;
- temporary TLS status;
- explicit statement: `VDS application stack is STOPPED pending cutover`.

Do not include secrets/private keys.

---

# 23. REQUIRED TESTS / PROOFS

A. SSH key access works.  
B. Debian version supported.  
C. Docker/Compose works.  
D. VDS disk/RAM adequate.  
E. remote Git HEAD equals origin/main.  
F. backup SHA matches after upload.  
G. DB restored.  
H. media restored.  
I. auth CA restored.  
J. OWNER identity preserved.  
K. Avito state restored.  
L. production env contains no dev secrets.  
M. only 80/443 + SSH public.  
N. internal container ports not public.  
O. production build succeeds on VDS.  
P. all services start.  
Q. HTTPS works.  
R. no-cert rejected.  
S. OWNER accepted.  
T. OWNER-only routes protected.  
U. products/sales/repairs/Avito routes work.  
V. 3 media files return 200.  
W. remote backup creation succeeds.  
X. local live data unchanged.  
Y. local live containers not restarted.  
Z. VDS application stack is stopped after proof.

---

# 24. DOCUMENTATION / RECORDS

Create:

`docs/stage08c_r1_real_vds_pre_cutover_deployment.md`

`docs/vds_pre_cutover_status.md`

`reports/stage08c_r1_real_vds_pre_cutover_deployment_report.md`

Update:

`logs/2026-09-12.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE08C_R1_REAL_VDS_PROVISION_AND_FIRST_DEPLOY_NO_CUTOVER_PROMPT.md`

---

# 25. GIT / SAFETY

Do not commit:
- `.secrets/`;
- SSH keys;
- production.env;
- server TLS private key;
- client private keys;
- backup ZIP;
- runtime DB;
- real media;
- remote credentials.

Commit docs/scripts/tests only if needed.

Push `origin/main`.
Verify clean local worktree.

---

# 26. FINAL REPORT CONTRACT

Return:

```text
# Stage 08C-R1 — Real VDS Provisioning and First Production Deployment (No Cutover)

## Local Preflight
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
LOCAL_GATEWAY:
LOCAL_COUNTS:

## Access
VDS_HOST:
SSH_USER:
SSH_PORT:
SSH_KEY_AUTH:
SECOND_SSH_AFTER_FIREWALL:

## VDS
OS:
VERSION:
ARCH:
CPU:
RAM_MB:
DISK_FREE_BEFORE:
DOCKER_VERSION:
COMPOSE_VERSION:

## Source
REMOTE_REPO:
/REMOTE_HEAD:
HEAD_MATCH:

## Backup Transfer
BACKUP_FILE:
BACKUP_SHA256_LOCAL:
BACKUP_SHA256_REMOTE:
SHA_MATCH:

## Restore
PRODUCTS:
SALES:
REPAIRS:
PHOTOS:
EXTERNAL_LISTINGS:
MEDIA_FILES:
CA_FINGERPRINT_MATCH:
OWNER_CERT_MATCH:
REVOCATION_STATE_PRESERVED:
AVITO_STATE_RESTORED:

## Production Secrets
APP_ENV:
CORE_TOKEN_SECURE:
CART_SECRET_SECURE:
DEV_DEFAULTS_USED:

## Network
PUBLIC_PORTS:
INTERNAL_PUBLIC_PORTS:
FIREWALL:
SSH_STILL_WORKS:

## VDS Build
BUILD_RESULT:
REMOTE_BUILD_HEAD:
IMAGES:

## Pre-Cutover Runtime Proof
GATEWAY:
NO_CERT_REJECTED:
OWNER_ACCEPTED:
USER_RBAC:
PRODUCTS_ROUTE:
SALES_ROUTE:
REPAIRS_ROUTE:
AVITO_ROUTE:
BACKUPS_ROUTE:
CERTIFICATES_ROUTE:
MEDIA_200:
REMOTE_BACKUP_CREATION:

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
LOCAL_CONTAINERS_RESTARTED:
LOCAL_GATEWAY_HEALTH_AFTER:

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08C_R1_REAL_VDS_PRE_CUTOVER_PROVEN

REAL_VDS_TOUCHED: true
DNS_CHANGED: false
CUTOVER_PERFORMED: false
VDS_STACK_STOPPED_PENDING_CUTOVER: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If access config is missing, return:

`BLOCKED_MISSING_VDS_ACCESS_CONFIG`

If SSH key authentication cannot be established safely, return BLOCKED.

If backup hashes differ, return BLOCKED.

If VDS stack cannot enforce mTLS, return BLOCKED.

If local data changes, return BLOCKED.

If VDS stack remains running after the proof, return BLOCKED.

---

# 27. STOP

After real-VDS pre-cutover proof and deliberate VDS application stop:

STOP.

Do not change DNS.
Do not perform cutover.
Wait for Owner acceptance.
