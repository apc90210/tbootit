# TECHNOREBOOT — Stage 08B-R1
## Production Debian Docker configuration and security baseline

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 08B-R1 — Production Debian Docker Configuration and Security Baseline`

# 0. EXECUTION CONTRACT

Stage08A full Owner workflow audit is accepted.

Owner has manually verified the main browser workflows. The local system is functionally ready for production preparation.

This stage prepares a safe production configuration for a Debian VDS.

IMPORTANT:

- Do NOT deploy to the real VDS yet.
- Do NOT change DNS.
- Do NOT expose the local workstation to the Internet.
- Do NOT modify live business data.
- Do NOT reset certificates/auth.
- Do NOT redesign modules.
- Do NOT add unrelated features.
- Keep normal Owner workflows browser-only.

The purpose is:

> From a clean Git checkout on Debian, provide a deterministic production Docker configuration that requires explicit secrets, persists all mutable data, exposes only the Gateway publicly, supports the existing mTLS OWNER/USER model, and is compatible with backup/disaster recovery.

First copy this prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08B_R1_PRODUCTION_DEBIAN_DOCKER_CONFIGURATION_AND_SECURITY_BASELINE_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08B_R1_PRODUCTION_DEBIAN_DOCKER_CONFIGURATION_AND_SECURITY_BASELINE_PROMPT.md`

# 1. PREFLIGHT

Record:

```text
BRANCH:
HEAD:
GIT_STATUS:
DOCKER_STATUS:
CURRENT_COMPOSE_FILES:
CURRENT_GATEWAY_PORT:
CURRENT_EXTENSION_VERSION:
CURRENT_BACKUP_FORMAT_VERSION:
```

Capture current live data identity/count baseline:

```text
PRODUCT_IDS
SALE_IDS
REPAIR_IDS
PHOTO_IDS
EXTERNAL_LISTING_IDS
```

These must remain unchanged.

# 2. PRODUCTION LAYOUT

Create a clear production layout, preferably:

```text
deploy/
  production/
    docker-compose.prod.yml
    nginx/
    env.production.example
    README.md
```

or another equally simple structure.

Do NOT create a second application architecture.

The production Compose configuration must reuse the existing modules:

- gateway/nginx;
- core;
- admin-shell;
- inventory-sales-module;
- repairs-module;
- avito-module.

# 3. PUBLIC NETWORK EXPOSURE POLICY

Production rule:

> Only the Gateway may publish host ports.

Internal services must NOT publish public host ports.

Expected:

```text
gateway:
  80/tcp   optional for redirect only
  443/tcp  public HTTPS/mTLS

core:
  Docker network only

admin-shell:
  Docker network only

inventory-sales-module:
  Docker network only

repairs-module:
  Docker network only

avito-module:
  Docker network only
```

If Avito extension pairing technically requires a distinct endpoint, route it through Gateway rather than exposing the module directly unless there is a proven hard requirement.

Add an automated test that fails if an internal service publishes a production host port.

# 4. PRODUCTION HOSTNAME

Do not hardcode:

```text
localhost
127.0.0.1
```

in production routing.

Use an explicit required environment value such as:

```text
TECHNOREBOOT_HOSTNAME=
```

The final production hostname/domain will be supplied at deployment time.

Local development configuration must remain unchanged.

# 5. SERVER TLS + CLIENT MTLS

Production must preserve current security model:

- HTTPS server certificate;
- client mTLS required;
- OWNER/USER authorization remains in admin-shell;
- revoked certificates remain rejected;
- `/backups` OWNER-only;
- `/certificates` OWNER-only.

Do NOT generate a new client CA if restored `data/auth` exists.

Keep `data/auth` as persistent mutable state.

Production server TLS certificate/key must be configurable separately from the client certificate CA.

Preferred environment/file contract:

```text
SERVER_TLS_CERT_PATH=
SERVER_TLS_KEY_PATH=
CLIENT_CA_CERT_PATH=
```

Do not commit real private keys.

# 6. HTTP TO HTTPS

Production Gateway should support:

```text
http://HOST -> https://HOST
```

with a permanent redirect if port 80 is enabled.

No application content over plain HTTP.

# 7. REMOVE DEVELOPMENT DEFAULTS FROM PRODUCTION

Audit all production environment values.

Production must fail fast if critical secret/config values are absent.

Do not allow insecure defaults such as:

```text
dev-token
change-me
admin
password
```

for production.

Identify every current token/secret.

Create a safe `env.production.example` containing variable names and explanations only.

Do NOT include real secrets.

Required report:

```text
CRITICAL_ENV_VARS:
INSECURE_DEFAULTS_FOUND:
INSECURE_DEFAULTS_ALLOWED_IN_PROD: 0
```

Development mode may retain its existing defaults if needed for local work.

# 8. PERSISTENT DATA CONTRACT

Production must persist all mutable data outside container layers.

At minimum:

```text
DB
storage/product photos
auth
Avito mutable state
backups
```

Choose one simple server root, preferably:

```text
/srv/technoreboot/data
```

or configurable:

```text
TECHNOREBOOT_DATA_ROOT=/srv/technoreboot/data
```

Production compose bind mounts must use that root.

It must remain compatible with existing:
- web backup;
- fresh-server bootstrap restore;
- disaster recovery scripts.

Do not duplicate the same mutable state in multiple host locations.

# 9. CONTAINER RESTART / HEALTH POLICY

Production services must have an appropriate restart policy such as:

```text
restart: unless-stopped
```

All important services must have useful health checks.

Report health checks by service.

# 10. SMALL-VDS BASELINE

Target server class:

```text
1 vCPU
2 GB RAM
~20 GB disk initially
```

Do NOT introduce memory-heavy auxiliary services.

Audit:
- image sizes;
- container count;
- obvious memory-heavy debug processes;
- development reloaders.

Production must not use:
- `--reload`;
- debug servers;
- unnecessary test containers.

# 11. LOGGING / ROTATION

Prevent unlimited Docker logs from filling a 20 GB disk.

Production Compose should use a bounded logging policy, for example:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "5"
```

or equivalent.

Apply consistently to application containers.

# 12. DATABASE SAFETY

Current DB is SQLite.

For this stage:
- do NOT migrate databases;
- do NOT switch PostgreSQL;
- do NOT redesign persistence.

Production must:
- use persistent DB path;
- never place SQLite only inside container writable layer;
- preserve safe backup behavior;
- verify only Core writes the business DB.

Document concurrency assumptions.

# 13. FILE PERMISSIONS

Define production permissions for:

```text
data/db
data/storage
data/auth
data/backups
data/avito-module
server TLS private key
client CA private key
```

Private keys must not be world-readable.

Do not require privileged containers.

# 14. DOCKER SECURITY BASELINE

Audit production Compose for:

- no Docker socket mount;
- no host root mount;
- no privileged containers;
- no unnecessary capabilities;
- no `network_mode: host`;
- no public internal-service ports;
- no embedded secrets in image/build args;
- no source-code bind mounts required in production.

Where practical, use `no-new-privileges`.

Do not break runtime merely to satisfy theoretical hardening.

# 15. PRODUCTION BUILD

Production configuration must build from repository source or deterministic images created from repository source.

No dependency on the developer machine’s existing images.

Prove in an isolated production simulation:

```text
fresh clone
production env fixture
production compose build
production compose config validation
```

Do NOT use real secrets in tests.

# 16. PRODUCTION SIMULATION

Create an isolated production-like test stack with:

- fresh Git checkout;
- temporary data root;
- generated test-only server TLS material;
- generated test-only client CA/cert;
- separate Compose project;
- alternate host ports to avoid collision with 8443.

Do not use live mutable data.

Prove:

- only Gateway host ports are published;
- Gateway HTTPS works;
- no-cert rejected;
- OWNER-like cert works;
- internal modules are not publicly exposed;
- products page loads;
- repairs page loads;
- sales page loads;
- Avito extension page loads;
- backup page access policy still works.

Tear down test stack cleanly.

# 17. FIREWALL / DEBIAN RUNBOOK

Create documentation for the future real VDS.

Do NOT modify a real server now.

Document recommended Debian firewall rules:

```text
22/tcp   SSH
80/tcp   HTTP redirect
443/tcp  HTTPS/mTLS
```

Everything else closed publicly.

Do not assume a specific cloud firewall provider.

# 18. PRODUCTION DEPLOYMENT RUNBOOK

Create:

`docs/production_debian_deployment.md`

It must cover:

1. fresh Debian prerequisites;
2. Docker installation expectations;
3. clone Git repository;
4. create `/srv/technoreboot`;
5. configure production environment;
6. place/restore mutable data;
7. configure server TLS;
8. build/start production Compose;
9. verify mTLS;
10. verify routes;
11. rollback procedure.

Do not actually perform these steps on the real VDS yet.

# 19. ROLLBACK PLAN

Document a simple rollback:

```text
backup before release
record previous Git commit
deploy new commit
health check
if failed:
  stop new stack
  checkout previous commit
  rebuild/start
  restore backup only if data migration changed data
```

Since this stage must not introduce schema migration, normal rollback should not require DB restore.

# 20. REQUIRED TESTS

A. production Compose parses successfully.
B. only Gateway publishes host ports.
C. internal services have zero production published ports.
D. production hostname is configurable.
E. no localhost/127.0.0.1 production dependency.
F. HTTP redirects to HTTPS.
G. mTLS remains required.
H. OWNER-like cert accepted.
I. no-cert rejected.
J. `/backups` remains OWNER-only.
K. `/certificates` remains OWNER-only.
L. no insecure production secret defaults.
M. no secrets committed.
N. DB persists under configurable production data root.
O. storage persists.
P. auth persists.
Q. Avito mutable state persists.
R. backups persist.
S. restart policies set.
T. health checks defined.
U. bounded Docker log rotation configured.
V. no privileged containers.
W. no Docker socket mount.
X. no host networking.
Y. fresh-clone production build succeeds.
Z. isolated production simulation passes and tears down cleanly.

Run relevant existing regression suites if shared production code/config changes.

# 21. LIVE DATA SAFETY

Before and after:

```text
PRODUCT_IDS
SALE_IDS
REPAIR_IDS
PHOTO_IDS
EXTERNAL_LISTING_IDS
```

must be exactly unchanged.

Required:

```text
PRODUCT_IDS_UNCHANGED: true
SALE_IDS_UNCHANGED: true
REPAIR_IDS_UNCHANGED: true
PHOTO_IDS_UNCHANGED: true
EXTERNAL_LISTING_IDS_UNCHANGED: true
REAL_PRODUCTS_DELETED: 0
```

# 22. DOCUMENTATION / RECORDS

Create:

`docs/stage08b_r1_production_debian_security_baseline.md`

`docs/production_debian_deployment.md`

`reports/stage08b_r1_production_debian_security_baseline_report.md`

Update:

`logs/2026-09-11.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE08B_R1_PRODUCTION_DEBIAN_DOCKER_CONFIGURATION_AND_SECURITY_BASELINE_PROMPT.md`

# 23. GIT / SAFETY

Do not commit:

- `.env` with real values;
- server private keys;
- CA private keys;
- client private keys;
- runtime DB;
- backup ZIPs;
- real media;
- cookies/session;
- generated production secrets.

Commit only:
- production templates;
- source/config;
- tests;
- docs/reports.

Push `origin/main`.
Verify clean worktree.

# 24. FINAL REPORT CONTRACT

Return:

```text
# Stage 08B-R1 — Production Debian Docker Configuration and Security Baseline

## Preflight
HEAD:
GIT_STATUS:
LIVE_COUNTS:

## Production Compose
FILE:
SERVICES:
PUBLIC_SERVICES:
PUBLIC_PORTS:
INTERNAL_PUBLISHED_PORTS:
DATA_ROOT:
HOSTNAME_VARIABLE:

## TLS / mTLS
SERVER_TLS_CONFIG:
CLIENT_CA_CONFIG:
MTLS_REQUIRED:
OWNER_POLICY:
USER_POLICY:
REVOCATION_POLICY:

## Secrets
CRITICAL_ENV_VARS:
INSECURE_DEFAULTS_FOUND:
INSECURE_DEFAULTS_ALLOWED_IN_PROD:
REAL_SECRETS_COMMITTED:

## Persistence
DB:
STORAGE:
AUTH:
AVITO_STATE:
BACKUPS:

## Container Security
PRIVILEGED_CONTAINERS:
HOST_NETWORK:
DOCKER_SOCKET_MOUNTS:
HOST_ROOT_MOUNTS:
SOURCE_BIND_MOUNTS:
LOG_ROTATION:
RESTART_POLICIES:
HEALTHCHECKS:

## Fresh Build Proof
FRESH_CLONE:
FRESH_CLONE_HEAD:
PREBUILT_IMAGES_REQUIRED:
BUILD_RESULT:

## Isolated Production Simulation
PROJECT:
GATEWAY_URL:
GATEWAY_HTTPS:
NO_CERT_REJECTED:
OWNER_CERT_ACCEPTED:
PRODUCTS:
SALES:
REPAIRS:
AVITO_EXTENSION:
BACKUPS:
INTERNAL_SERVICES_PUBLICLY_EXPOSED:
TEARDOWN:

## Live Data Safety
PRODUCT_IDS_UNCHANGED:
SALE_IDS_UNCHANGED:
REPAIR_IDS_UNCHANGED:
PHOTO_IDS_UNCHANGED:
EXTERNAL_LISTING_IDS_UNCHANGED:
REAL_PRODUCTS_DELETED: 0

## Deployment Runbook
PATH: docs/production_debian_deployment.md
REAL_VDS_TOUCHED: false
DNS_CHANGED: false

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08B_R1_PRODUCTION_BASELINE_READY_FOR_OWNER_CHECK

PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If any internal service remains publicly exposed in the production configuration, return BLOCKED.

If production can start with known development/default secrets, return BLOCKED.

If live business data changes, return BLOCKED.

# 25. STOP

After production configuration, isolated simulation, tests, docs, commit/push and report:

STOP.

Do not deploy to the real VDS.
Wait for Owner acceptance.
