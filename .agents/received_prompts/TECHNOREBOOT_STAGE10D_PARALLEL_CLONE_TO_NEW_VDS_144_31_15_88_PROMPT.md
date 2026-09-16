# TECHNOREBOOT — Stage 10D PRODUCTION / PARALLEL CLONE
## Full clone of current production VDS to new Debian 13 VDS for parallel access testing

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`

**CURRENT production VDS (SOURCE):**
```text
IP: 144.31.50.134
Current role: authoritative production
```

**NEW VDS (TARGET):**
```text
Tariff: Xeon 2667V2-2
Opened: 2026-09-16
Hostname label: atanov822.serv.host
Public IPv4: 144.31.15.88
OS: Debian 13
```

**Stage:** `Stage 10D — Parallel full clone to new VDS`

# 0. OWNER GOAL

Create a complete, independently running copy of the current TechnoReboot production system on the NEW VDS `144.31.15.88`.

Purpose: test whether the current non-VPN connectivity problem is tied to the old IP/prefix.

Required architecture:

```text
OLD VDS 144.31.50.134
= remains current authoritative production

            ↓ safe backup/copy

NEW VDS 144.31.15.88
= exact parallel clone for Owner testing
```

The old server must remain fully operational.

There is NO cutover in this stage.

Do NOT delete, replace, or modify the old production runtime except for safe backup/read operations.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE10D_PARALLEL_CLONE_TO_NEW_VDS_144_31_15_88_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE10D_PARALLEL_CLONE_TO_NEW_VDS_144_31_15_88_PROMPT.md`

# 2. SSH ACCESS / CREDENTIAL SAFETY

Owner will provide SSH access to the NEW VDS.

Use the existing authorized SSH access for the OLD VDS.

For NEW VDS:
- accept either SSH key or password supplied by Owner;
- NEVER commit credentials;
- NEVER write passwords/private keys into repo logs/reports;
- NEVER echo secrets into terminal output unnecessarily;
- prefer key-based authentication once initial access is established.

If only a root password is supplied:
- use it only ephemerally;
- install Owner SSH public key on the target;
- verify key login;
- after that use the key for the rest of the stage.

Record only:

```text
SOURCE_SSH_OK:
TARGET_SSH_OK:
TARGET_KEY_AUTH_CONFIGURED:
```

Never record secret material.

# 3. HARD SAFETY RULES

## SOURCE / OLD VDS

Allowed:
- read-only inspection;
- existing safe backup/checkpoint creation;
- SQLite online backup;
- checksums;
- rsync/read copy of media/auth/data;
- git metadata read.

Forbidden:
- database migration;
- code deployment;
- container recreation;
- firewall modification;
- production config changes;
- business-data changes;
- downtime unless absolutely unavoidable.

## TARGET / NEW VDS

Allowed:
- full bootstrap;
- Docker installation;
- firewall configuration;
- source checkout;
- restore production clone;
- server certificate issuance for NEW IP;
- container build/start;
- smoke tests.

# 4. PHASE A — SOURCE PRODUCTION PREFLIGHT

On OLD VDS `144.31.50.134`, record:

```text
SOURCE_HOSTNAME:
SOURCE_OS:
SOURCE_VDS_HEAD:
SOURCE_GIT_STATUS:
SOURCE_6_SERVICES_HEALTHY:
SOURCE_CONTAINER_IDS:
SOURCE_IMAGE_IDS:
SOURCE_DATA_ROOT:
SOURCE_DB_PATH:
SOURCE_DB_SHA256:
SOURCE_DB_SCHEMA_SHA:
SOURCE_DB_QUICK_CHECK:
SOURCE_PRODUCTS:
SOURCE_SALES:
SOURCE_REPAIRS:
SOURCE_PRODUCT_PHOTOS:
SOURCE_EXTERNAL_LISTINGS:
SOURCE_AVITO_POST_SALE_TASKS:
SOURCE_STORAGE_FILE_COUNT:
SOURCE_AUTH_CA_SHA256:
SOURCE_TOTAL_DATA_SIZE:
```

Discover actual table names rather than assuming.

Also record current production runtime configuration:
- Docker Compose file;
- production `.env` key names;
- bind mounts;
- secrets paths;
- gateway/nginx config;
- firewall/nftables config;
- sysctl network config;
- systemd units;
- backup/checkpoint tooling;
- current extension version;
- current User Manual PDF hash.

Do NOT print secret values.

# 5. PHASE B — CREATE FRESH VERIFIED SOURCE BACKUP

Use the EXISTING TechnoReboot backup/checkpoint infrastructure if possible.

Preferred:

```text
existing production backup
+
release checkpoint
```

The backup must include current mutable production state:

```text
database
media/storage
auth / client CA / certificate issuance state
Avito mutable state
manifest
```

Source code should still come from Git, not from the backup.

Required:

```text
SOURCE_BACKUP_CREATED: true
SOURCE_BACKUP_PATH:
SOURCE_BACKUP_SHA256:
SOURCE_BACKUP_QUICK_CHECK: ok
SOURCE_BACKUP_MANIFEST_OK: true
```

If using SQLite directly, use Online Backup API / `.backup`.
Do NOT copy a live SQLite DB file naively while it is being written.

# 6. PHASE C — TARGET BASELINE / DEBIAN 13

Connect to NEW VDS `144.31.15.88`.

Record:

```text
TARGET_HOSTNAME:
TARGET_OS:
TARGET_KERNEL:
TARGET_PUBLIC_IP:
TARGET_DEFAULT_ROUTE:
TARGET_GATEWAY:
TARGET_INTERFACE:
TARGET_MTU:
TARGET_DISK_FREE:
TARGET_RAM:
TARGET_CPU:
```

Confirm the target really owns:

```text
144.31.15.88
```

Do NOT trust the provider hostname label as public DNS.

Check:

```text
atanov822.serv.host
```

but do not depend on it.

# 7. PHASE D — TARGET SYSTEM BOOTSTRAP

Install only required system packages for current TechnoReboot production.

At minimum, as applicable:

```text
ca-certificates
curl
git
gnupg
rsync
sqlite3
openssl
nftables
iproute2
iputils-ping
tcpdump
```

Install Docker Engine + Docker Compose plugin using the supported Debian 13 method.

Required:

```text
docker --version
docker compose version
systemctl is-enabled docker
systemctl is-active docker
```

Enable Docker at boot.

Do not install unnecessary services.

# 8. PHASE E — SSH HARDENING

Once Owner key login is verified:
- preserve a working emergency root/key path;
- do not lock Owner out;
- keep SSH on current port unless source intentionally differs;
- do not make unrelated security-policy changes.

Record:

```text
TARGET_SSH_KEY_LOGIN_OK:
TARGET_SSH_SERVICE_ACTIVE:
```

# 9. PHASE F — TARGET NETWORK / FIREWALL

Build the NEW VDS firewall from the CURRENT CORRECTED production policy, but do not blindly copy broken historical rules.

Requirements:

```text
22/tcp   allowed as currently required for administration
80/tcp   public
443/tcp  public
ICMP     allowed as required for PMTU
internal app/database ports NOT public
```

Preserve the Stage10C network fixes where still appropriate:

```text
ICMP acceptance
net.ipv4.tcp_mtu_probing=1
safe nftables management that DOES NOT flush Docker NAT tables
```

Important:
Do NOT use a persistent `flush ruleset` pattern that destroys Docker-managed NAT.

Inspect NEW VDS topology independently.
Do not assume old gateway/MTU values apply.

After firewall setup:

```text
SSH still works
80 reachable
443 reachable
internal ports private
```

# 10. PHASE G — CHECKOUT EXACT PRODUCTION CODE

The goal is a clone of CURRENT production runtime.

Determine exact SOURCE VDS Git HEAD:

```text
SOURCE_VDS_HEAD
```

On NEW VDS create:

```text
/srv/technoreboot/app
```

Clone/fetch repository and checkout the exact SOURCE runtime commit.

Required:

```text
TARGET_CODE_HEAD == SOURCE_VDS_HEAD
```

Do not silently deploy a newer unaccepted `origin/main` commit.

If `origin/main` has later documentation-only commits, they are not relevant to runtime cloning.

Record:

```text
TARGET_CODE_HEAD:
CODE_HEAD_MATCH:
```

# 11. PHASE H — CREATE TARGET DIRECTORY STRUCTURE

Recreate current production layout, based on the real source server.

Expected pattern may include:

```text
/srv/technoreboot/app
/srv/technoreboot/data
/srv/technoreboot/secrets
/srv/technoreboot/backups
```

Use the actual source architecture.

Set correct ownership/permissions.

Never make auth/private keys world-readable.

# 12. PHASE I — TRANSFER PRODUCTION CLONE DATA

Transfer the fresh verified source backup securely to NEW VDS.

Preferred:
- source-to-target `rsync`/`scp` over SSH;
- or controlled LOCAL relay only if direct transfer is unavailable.

Verify SHA256 after transfer.

Restore into NEW VDS data root.

Clone should include:
- current production DB;
- storage/media;
- client-auth CA and certificate issuance state;
- Avito mutable state;
- required mutable manifests/config.

Do NOT use LOCAL development DB/media.

Required post-restore invariants:

```text
TARGET_PRODUCTS == SOURCE_PRODUCTS
TARGET_SALES == SOURCE_SALES
TARGET_REPAIRS == SOURCE_REPAIRS
TARGET_PRODUCT_PHOTOS == SOURCE_PRODUCT_PHOTOS
TARGET_EXTERNAL_LISTINGS == SOURCE_EXTERNAL_LISTINGS
TARGET_AVITO_POST_SALE_TASKS == SOURCE_AVITO_POST_SALE_TASKS
TARGET_STORAGE_FILE_COUNT == SOURCE_STORAGE_FILE_COUNT
TARGET_AUTH_CA_SHA256 == SOURCE_AUTH_CA_SHA256
TARGET_DB_SCHEMA_SHA == SOURCE_DB_SCHEMA_SHA
TARGET_DB_QUICK_CHECK == ok
```

This is intentionally a real production-data clone.

# 13. PHASE J — SECRETS / ENVIRONMENT

Recreate production environment configuration on NEW VDS.

Important:
- transfer current production secrets securely;
- do not commit them;
- do not display their values in reports;
- adapt only server-specific values.

Server-specific values that may need change:
- public IP;
- public URL;
- server TLS certificate paths;
- hostname/server_name if applicable.

Do not change business configuration unnecessarily.

# 14. PHASE K — TLS / mTLS ON NEW IP

Critical.

The old server TLS certificate for `144.31.50.134` must NOT be blindly reused for `144.31.15.88` unless it is genuinely valid for the new IP.

Inspect current SOURCE certificate and issuance mechanism.

For NEW VDS:

```text
Public endpoint: https://144.31.15.88
```

Obtain/install a server certificate valid for `144.31.15.88` using the same supported mechanism currently used by TechnoReboot.

At the same time preserve the SAME TechnoReboot client CA so current OWNER/USER client certificates continue to work on the clone.

Required:

```text
NEW_SERVER_CERT_VALID_FOR_144_31_15_88: true
CLIENT_CA_SAME_AS_SOURCE: true
MTLS_REQUIRED: true
```

If a publicly trusted IP certificate cannot be issued:
STOP and report the exact blocker.
Do not disable mTLS and do not silently use an invalid server certificate as the final state.

# 15. PHASE L — AVITO DUPLICATE-ACTION SAFETY

Because OLD and NEW servers temporarily contain the same business data, prevent duplicate external side effects.

Current accepted design has automatic Avito post-sale deactivation disabled/manual-only.

Verify that remains true on TARGET.

Do not enable any automatic external mutation worker merely because data was cloned.

Required:

```text
AUTO_AVITO_DEACTIVATION_DISABLED: true
NO_DUPLICATE_EXTERNAL_MUTATION_WORKER: true
```

Normal manual/import functionality may remain available.

# 16. PHASE M — BUILD AND START TARGET STACK

Use the production Compose architecture.

Build/start the six expected services on NEW VDS:

```text
gateway
core
admin-shell
inventory-sales-module
repairs-module
avito-module
```

Required:

```text
TARGET_6_SERVICES_HEALTHY: true
```

Check restart policies and boot persistence.

# 17. PHASE N — TARGET APPLICATION SMOKE

Using valid OWNER client certificate, verify on NEW VDS:

```text
https://144.31.15.88/
https://144.31.15.88/inventory/products
https://144.31.15.88/sales
https://144.31.15.88/repairs
https://144.31.15.88/avito/extension
https://144.31.15.88/avito/post-sale
https://144.31.15.88/help
https://144.31.15.88/help/user-manual.pdf
```

Verify:
- 200 where expected with OWNER cert;
- current extension version matches source;
- extension ZIP hash matches source;
- User Manual PDF hash matches source;
- product/media pages work;
- no 500/502.

Without client certificate:
- HTTPS must remain denied by mTLS.

HTTP port 80:
- redirect to HTTPS.

# 18. PHASE O — SOURCE VS TARGET IDENTITY

Produce side-by-side comparison:

```text
SOURCE_CODE_HEAD == TARGET_CODE_HEAD
SOURCE_DB_SCHEMA_SHA == TARGET_DB_SCHEMA_SHA
SOURCE_PRODUCTS == TARGET_PRODUCTS
SOURCE_SALES == TARGET_SALES
SOURCE_REPAIRS == TARGET_REPAIRS
SOURCE_PHOTOS == TARGET_PHOTOS
SOURCE_EXTERNAL_LISTINGS == TARGET_EXTERNAL_LISTINGS
SOURCE_STORAGE_FILE_COUNT == TARGET_STORAGE_FILE_COUNT
SOURCE_AUTH_CA_SHA256 == TARGET_AUTH_CA_SHA256
SOURCE_EXTENSION_VERSION == TARGET_EXTENSION_VERSION
SOURCE_EXTENSION_ZIP_SHA256 == TARGET_EXTENSION_ZIP_SHA256
SOURCE_MANUAL_PDF_SHA256 == TARGET_MANUAL_PDF_SHA256
```

DB byte SHA does not need to remain identical after TARGET services start because target runtime may legitimately create local state.
Schema and business invariants are what matter.

# 19. PHASE P — REAL NON-VPN NETWORK TEST ON NEW IP

This is the main reason for creating the clone.

Arm packet capture/log watch on NEW VDS before Owner test.

Then ask Owner only:

```text
Отключи Amnezia и открой:
https://144.31.15.88
```

Capture:
- SYN;
- SYN-ACK;
- complete ClientHello;
- TLS server response;
- client certificate exchange;
- nginx request;
- final HTTP status.

Required report:

```text
NEW_IP_NONVPN_TEST:
NEW_IP_TCP_HANDSHAKE:
NEW_IP_FULL_CLIENTHELLO:
NEW_IP_TLS_COMPLETE:
NEW_IP_NGINX_REQUEST:
NEW_IP_HTTP_STATUS:
```

Also verify with Amnezia ON afterward.

This stage must NOT claim the new IP solved the issue until Owner's real browser test succeeds.

# 20. IF NEW IP WORKS WITHOUT VPN

Do NOT cut over automatically.

Return:

```text
NEW_IP_SOLVES_NONVPN_ACCESS = true
```

Keep both servers running.

Recommend a separate cutover stage that will:
- take a fresh final delta/backup from OLD;
- stop writes briefly;
- sync final mutable data;
- make NEW server authoritative;
- keep OLD server as rollback for a defined period.

Do not perform this cutover in Stage10D.

# 21. IF NEW IP ALSO FAILS WITHOUT VPN

Do not destroy the target.

Capture same packet evidence and compare OLD vs NEW.

Return:

```text
NEW_IP_SOLVES_NONVPN_ACCESS = false
```

Then determine whether:
- both IP prefixes are affected;
- the failure is client/provider/TSPU behavior independent of VDS IP;
- a proper domain/SNI path is still required.

# 22. SOURCE SAFETY VERIFICATION

At end verify OLD production is still healthy:

```text
SOURCE_6_SERVICES_HEALTHY_AFTER:
SOURCE_PRODUCTS_UNCHANGED:
SOURCE_SALES_UNCHANGED:
SOURCE_REPAIRS_UNCHANGED:
SOURCE_STORAGE_UNCHANGED:
SOURCE_DB_QUICK_CHECK_AFTER:
```

No source cutover.

# 23. DOCUMENTATION

Create locally:

```text
reports/stage10d_parallel_clone_new_vds_144_31_15_88_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Do NOT store:
- SSH password;
- private keys;
- API tokens;
- secret env values.

# 24. GIT

Commit only:
- deployment/diagnostic scripts;
- reports/docs;
- infrastructure code changes that are intentionally part of repo.

Never commit:
- production DB;
- production media;
- backups;
- private keys;
- `.env` secrets.

Push documentation/scripts if appropriate.

# 25. FINAL REPORT CONTRACT

Return:

```text
# Stage 10D — Parallel Full Clone to New VDS

## Source
SOURCE_IP: 144.31.50.134
SOURCE_VDS_HEAD:
SOURCE_6_SERVICES_HEALTHY_BEFORE:
SOURCE_PRODUCTS:
SOURCE_SALES:
SOURCE_REPAIRS:
SOURCE_PHOTOS:
SOURCE_EXTERNAL_LISTINGS:
SOURCE_STORAGE_FILE_COUNT:
SOURCE_DB_SCHEMA_SHA:
SOURCE_AUTH_CA_SHA256:

## Backup
SOURCE_BACKUP_CREATED:
SOURCE_BACKUP_SHA256:
SOURCE_BACKUP_QUICK_CHECK:
SOURCE_BACKUP_MANIFEST_OK:

## Target
TARGET_IP: 144.31.15.88
TARGET_OS:
TARGET_HOSTNAME:
TARGET_DOCKER_VERSION:
TARGET_COMPOSE_VERSION:
TARGET_CODE_HEAD:
CODE_HEAD_MATCH:

## Restored Data
TARGET_PRODUCTS:
TARGET_SALES:
TARGET_REPAIRS:
TARGET_PHOTOS:
TARGET_EXTERNAL_LISTINGS:
TARGET_STORAGE_FILE_COUNT:
TARGET_DB_SCHEMA_SHA:
TARGET_DB_QUICK_CHECK:
TARGET_AUTH_CA_SHA256:
SOURCE_TARGET_DATA_INVARIANTS_MATCH:

## TLS / Security
NEW_SERVER_CERT_VALID_FOR_144_31_15_88:
CLIENT_CA_SAME_AS_SOURCE:
MTLS_REQUIRED:
HTTP_80_REDIRECT:
INTERNAL_PORTS_PRIVATE:
SSH_KEY_LOGIN_OK:

## Runtime
TARGET_6_SERVICES_HEALTHY:
ROOT_OK:
PRODUCTS_OK:
SALES_OK:
REPAIRS_OK:
AVITO_EXTENSION_OK:
AVITO_POST_SALE_OK:
HELP_OK:
USER_MANUAL_OK:
EXTENSION_HASH_MATCH:
MANUAL_PDF_HASH_MATCH:
AUTO_AVITO_DEACTIVATION_DISABLED:

## New IP Owner Test
OWNER_REAL_NONVPN_TEST_PERFORMED:
NEW_IP_NONVPN_TEST:
NEW_IP_TCP_HANDSHAKE:
NEW_IP_FULL_CLIENTHELLO:
NEW_IP_TLS_COMPLETE:
NEW_IP_NGINX_REQUEST:
NEW_IP_HTTP_STATUS:
NEW_IP_VPN_TEST:

## Source After
SOURCE_6_SERVICES_HEALTHY_AFTER:
SOURCE_BUSINESS_DATA_UNCHANGED:
SOURCE_STILL_AUTHORITATIVE: true

## Conclusion
NEW_IP_SOLVES_NONVPN_ACCESS:
READY_FOR_SEPARATE_CUTOVER_STAGE:

FINAL_STATUS:
<one of>
TECHNOREBOOT_STAGE10D_NEW_VDS_CLONE_READY_NEW_IP_WORKS
TECHNOREBOOT_STAGE10D_NEW_VDS_CLONE_READY_NEW_IP_STILL_BLOCKED
BLOCKED_TARGET_BOOTSTRAP_OR_RESTORE
```

# 26. STOP

After full clone + real Owner test:

STOP.

Do NOT switch production authority.
Do NOT shut down old VDS.
Do NOT delete either server.

Wait for Owner decision.
