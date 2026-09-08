# TECHNOREBOOT — Stage 07A-R1
## Minimal Certificate Access Gateway

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Stage:** `Stage 07A-R1 — Minimal Certificate Access Gateway`

---

# 0. EXECUTION CONTRACT

This file is the owner-approved execution prompt for this stage.

Execute THIS prompt against the existing project in:

`C:\tbootit`

Do not create a replacement prompt.

Before implementation:

1. Locate this exact downloaded file:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07A_R1_MINIMAL_CERTIFICATE_ACCESS_PROMPT.md`

2. Copy it unchanged into:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07A_R1_MINIMAL_CERTIFICATE_ACCESS_PROMPT.md`

3. Verify the copied file exists.

4. Treat the copied file as the authoritative received prompt for Stage 07A-R1.

Do not start any later stage.

---

# 1. CURRENT PROJECT STATE / ACCEPTED BASELINE

The current `main` state of ТехноРебут is the accepted baseline.

The system is modular and Docker-based.

Existing business modules and already accepted functionality must remain intact.

This stage is NOT a refactor of Core, Inventory/Sales, Repairs, Avito or the current business logic.

The purpose of this stage is only to add a very small external access barrier before the existing system so the current project can later be exposed on an Internet test server.

The owner explicitly requires a SIMPLE implementation.

Do not turn this into a large authentication platform.

---

# 2. PREFLIGHT — REQUIRED BEFORE ANY CHANGE

From `C:\tbootit`:

1. Run and record:
   - `git status --short`
   - current branch
   - current HEAD
   - `git log -1 --oneline`
   - `docker compose ps`

2. Confirm the repository is on the expected working branch / `main` according to the current project workflow.

3. Synchronize safely with `origin/main` if required by the current repository state.

4. Do NOT destroy uncommitted owner changes.

5. Inspect the existing:
   - `docker-compose.yml` / compose files;
   - reverse proxy or ingress implementation, if already present;
   - Admin Shell;
   - exposed host ports;
   - internal Docker networks;
   - existing healthchecks;
   - current local URLs.

6. Read the latest relevant project reports/docs/logs necessary to understand the accepted architecture.

7. Reuse the existing project stack and conventions where practical.

Do not perform unrelated cleanup or refactoring.

---

# 3. GOAL

Implement a minimal certificate-based access system for the current ТехноРебут installation using standard X.509 client certificates / mTLS.

Required behavior:

```text
No valid Technoreboot client certificate
        -> access denied

ACTIVE user certificate
        -> normal Technoreboot UI allowed

REVOKED / unknown certificate
        -> access denied

OWNER certificate
        -> normal Technoreboot UI allowed
        -> certificate admin page allowed
```

This is a TEST-STAGE access barrier.

It does not need enterprise IAM complexity.

---

# 4. REQUIRED MINIMAL FUNCTIONALITY

## 4.1 Certificate Authority

Create one persistent local Technoreboot CA.

The CA must:

- be generated only if it does not already exist;
- survive container restart / compose restart / PC reboot;
- not be regenerated during normal startup;
- be stored in persistent runtime auth storage;
- never be committed to Git.

Do not introduce Vault, HSM, cloud PKI or other infrastructure.

---

## 4.2 OWNER certificate

Create one persistent OWNER client certificate in `.p12` / `.pfx` form.

It must:

- be generated only if no OWNER certificate already exists;
- give access to the ordinary Technoreboot application;
- give access to the certificate admin page;
- survive restart;
- not be automatically replaced;
- not be revocable through normal UI/API.

The backend must explicitly reject an attempt to revoke OWNER.

The final report must tell the owner exactly:

- where the generated OWNER `.p12/.pfx` file is located;
- how to obtain it;
- what password is used or where that generated password is shown/stored.

Do not print private key material in chat/report/logs.

---

## 4.3 USER certificates

OWNER must be able to create a normal user certificate.

Minimal input:

`Название`

Example:

`Ноутбук магазин`

After creation:

- create client certificate;
- sign it with the Technoreboot CA;
- register it as `ACTIVE`;
- make a `.p12/.pfx` download available to OWNER.

A normal USER certificate gives access only to the normal Technoreboot application.

It must NOT give access to the certificate administration page.

---

## 4.4 Revoke

OWNER can revoke an ACTIVE USER certificate.

After revoke:

`ACTIVE -> REVOKED`

The revoked certificate must no longer allow access on subsequent requests.

Do not implement restore/unrevoke in this stage.

Do not implement certificate renewal in this stage.

---

# 5. MINIMAL ADMIN UI

Add one very simple certificate management page.

Prefer integration into the existing Admin Shell unless the existing architecture shows a significantly simpler safe option.

Do not create a large standalone frontend.

Required page content only:

```text
ТЕХНОРЕБУТ — ДОСТУП

[ Выпустить сертификат ]

Название | Создан | Статус | Действие
```

Statuses:

- `ACTIVE`
- `REVOKED`

Actions:

- ACTIVE ordinary certificate -> `Отозвать`
- OWNER -> no revoke action
- REVOKED -> no action required

Certificate creation requires only:

`Название`

No roles UI.
No profile UI.
No audit dashboard.
No statistics.

Use the existing visual conventions where easy, but do not spend time on design polish.

---

# 6. STORAGE

Keep this simple.

A small persistent file registry is acceptable and preferred unless the current architecture makes another already-existing storage mechanism clearly simpler.

For example:

```text
auth-data/
  ca/
  certificates/
  registry.json
```

The exact location may be adjusted to fit the current compose/project layout.

The important requirements are:

- persistent;
- one obvious auth runtime storage location;
- survives restart;
- not tracked by Git;
- suitable for inclusion in a future full-system backup.

Minimal registry information is sufficient:

- id;
- name;
- serial/fingerprint;
- status;
- owner flag;
- created_at.

Do not add a new PostgreSQL database or Redis only for this feature.

---

# 7. REQUEST VALIDATION

Use the simplest implementation that fits the CURRENT architecture.

Preferred principle:

1. reverse proxy performs TLS client certificate validation against the Technoreboot CA;
2. trusted certificate identity is passed internally;
3. a minimal auth check verifies that the certificate exists in the registry and is `ACTIVE`;
4. unknown/revoked -> deny;
5. OWNER-only path additionally requires OWNER identity.

IMPORTANT:

A client-supplied HTTP header must never be trusted as proof of certificate identity.

Any internal trusted certificate header must be overwritten/created by the trusted proxy layer after successful client-certificate verification.

The auth service/check must not be exposed as an unrestricted public endpoint.

Do not force internal Docker-to-Docker service calls to use client certificates.

The certificate barrier is for EXTERNAL access.

---

# 8. DEVELOPMENT / LOCAL STAGE

This stage is LOCAL implementation and verification in `C:\tbootit`.

Do NOT deploy to the Internet server yet.

Do NOT request server credentials.

Do NOT implement production DNS/domain setup.

Do NOT implement Let's Encrypt production deployment now.

A local/dev TLS configuration may be used as needed to prove mTLS behavior.

The result must be prepared so a later deployment stage can reuse it.

---

# 9. EXPLICITLY OUT OF SCOPE

Do NOT add unless strictly required for the minimal implementation:

- username/password authentication;
- JWT;
- OAuth;
- email login;
- SMS;
- SSO;
- LDAP;
- RBAC;
- ADMIN/MANAGER/SALES/SERVICE roles;
- device fingerprinting;
- hardware binding;
- IP allowlists;
- user-agent tracking;
- activity dashboards;
- login statistics;
- complex audit subsystem;
- automatic certificate renewal;
- certificate lifecycle portal;
- Redis;
- separate auth PostgreSQL database;
- Vault;
- Kubernetes;
- cloud PKI.

Do NOT implement backup/restore in this stage.

Backup/restore is a separate owner-approved next stage AFTER certificate access is accepted.

---

# 10. GIT / SECRET SAFETY

Verify `.gitignore` protects generated runtime security material.

Generated private/security files must not be committed, including as applicable:

- private keys;
- CA private key;
- `.p12`;
- `.pfx`;
- generated certificate passwords;
- runtime certificate registry if it contains runtime security state;
- runtime auth-data.

Do commit:

- implementation code;
- safe configuration;
- tests;
- documentation;
- reports;
- received prompt copy;
- safe example configuration where needed.

Before commit, inspect the staged diff for secrets.

---

# 11. REQUIRED TEST / VALIDATION CONTRACT

Implement and actually verify the following.

## TEST A — Existing project baseline

Existing primary services start and remain healthy.

Result:
`PASS / FAIL`

## TEST B — No client certificate

Attempt external/protected access without a Technoreboot client certificate.

Expected:
access denied.

## TEST C — OWNER normal access

Use OWNER certificate.

Expected:
normal Technoreboot application accessible.

## TEST D — OWNER admin access

Use OWNER certificate.

Expected:
certificate admin page accessible.

## TEST E — Create USER certificate

Create a USER certificate through the implemented owner flow.

Expected:
certificate created, registered ACTIVE, `.p12/.pfx` available.

## TEST F — USER normal access

Use created USER certificate.

Expected:
normal Technoreboot application accessible.

## TEST G — USER admin denied

Use normal USER certificate against certificate admin page.

Expected:
403 / access denied.

## TEST H — Revoke USER

OWNER revokes the created USER certificate.

Expected:
registry status `REVOKED`.

## TEST I — Revoked USER denied

Repeat protected request using revoked certificate.

Expected:
access denied.

## TEST J — OWNER revoke protection

Attempt to revoke OWNER via backend/API, not only through hidden UI.

Expected:
operation rejected.

## TEST K — Persistence

Restart the relevant auth/proxy services.

Expected:

- same CA;
- same OWNER certificate identity;
- same registry;
- revoked state preserved.

## TEST L — Regression

Run the appropriate existing project regression test suites / health checks required by the current repository.

Record exact totals.

Do not claim PASS without executing the check.

---

# 12. DOCUMENTATION / PROJECT RECORD

Follow the established Technoreboot project workflow.

Create/update an implementation document appropriate for the stage, for example:

`docs/stage07a_r1_minimal_certificate_access.md`

Create the stage report:

`reports/stage07a_r1_minimal_certificate_access_report.md`

Update the current daily log:

`logs/2026-09-08.md`

Keep the exact received prompt in:

`.agents/received_prompts/TECHNOREBOOT_STAGE07A_R1_MINIMAL_CERTIFICATE_ACCESS_PROMPT.md`

Document:

- actual architecture chosen after preflight;
- actual auth-data location;
- local URLs;
- OWNER retrieval procedure;
- USER issue/revoke procedure;
- validation results;
- known limitations.

Do not invent results.

---

# 13. COMMIT / PUSH

When and only when implementation and required validation are complete:

1. inspect `git status`;
2. inspect staged files;
3. ensure no secrets/private certificates are staged;
4. commit the Stage 07A-R1 implementation;
5. push to `origin/main` following the current project workflow;
6. verify final HEAD;
7. verify remote push;
8. verify final worktree state.

Do not start another stage after push.

---

# 14. FINAL CHAT REPORT CONTRACT

Return a concise but complete report.

Required structure:

```text
# Stage 07A-R1 — Minimal Certificate Access Gateway

## Executive Summary

## Preflight / Baseline
- branch
- HEAD before
- relevant current architecture
- containers before

## Implementation
- actual solution used
- access flow
- admin page
- persistent auth storage
- OWNER handling
- USER issue/revoke handling

## Files Changed / Created

## Runtime Verification
TEST A:
TEST B:
TEST C:
TEST D:
TEST E:
TEST F:
TEST G:
TEST H:
TEST I:
TEST J:
TEST K:
TEST L:

## Test Summary
- exact executed suites
- passed
- failed

## Docker / Runtime
- docker compose ps
- relevant URLs

## Git
- commit
- push
- final status

## Owner Manual Check Guide
Exact numbered steps the owner should perform locally.

## Known Limitations
Only real current limitations.

FINAL_STATUS:
TECHNOREBOOT_STAGE07A_R1_MINIMAL_CERTIFICATE_ACCESS_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
BACKUP_STAGE_NOT_STARTED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_STAGE07A_R2_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_BACKUP_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_INTERNET_DEPLOYMENT_WITHOUT_OWNER_ACCEPTANCE: true
```

If a required test actually fails, do not falsely return READY_FOR_OWNER_CHECK.

Return a truthful blocker-oriented `FINAL_STATUS` instead and explain the exact blocker.

---

# 15. STOP CONDITION

After:

- implementation;
- verification;
- documentation;
- report;
- commit/push;
- final chat report;

STOP.

Do not:

- start R2;
- implement backup;
- deploy to Internet;
- add extra authentication features.

Wait for the owner's next prompt.

---

READY_TO_RUN_IN_ANTIGRAVITY
