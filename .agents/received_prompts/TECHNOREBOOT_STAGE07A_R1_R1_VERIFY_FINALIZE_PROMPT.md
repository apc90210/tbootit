# TECHNOREBOOT — Stage 07A-R1-R1
## Verify, correct and finalize Minimal Certificate Access

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Parent stage:** `Stage 07A-R1 — Minimal Certificate Access Gateway`
**Purpose:** verification/finalization only

---

# 0. EXECUTION CONTRACT

This is a corrective verification/finalization prompt for the already implemented Stage 07A-R1.

Do NOT redesign the certificate system.
Do NOT add new authentication features.
Do NOT start backup.
Do NOT deploy to the Internet.

First copy this exact downloaded file:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07A_R1_R1_VERIFY_FINALIZE_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07A_R1_R1_VERIFY_FINALIZE_PROMPT.md`

Create the destination directory if needed.

Treat the copied file as the authoritative prompt for this corrective stage.

---

# 1. CURRENT STATE

Stage 07A-R1 has already implemented:

- Nginx `gateway` on HTTPS/mTLS;
- persistent Technoreboot CA;
- persistent OWNER certificate;
- USER certificate issue/download/revoke;
- `/certificates` owner-only UI;
- runtime registry in `data/auth`;
- auth verification through the gateway;
- tests for owner/user/revocation/persistence.

Do NOT rewrite this implementation unless a verification step proves a real defect.

---

# 2. WHY THIS CORRECTIVE PASS IS REQUIRED

The previous final chat report is not yet accepted because its reporting/finalization contract contains inconsistencies.

Specifically:

1. The final report did not provide a commit hash and push result.
2. The final report did not clearly confirm the required stage docs/report files and received-prompt copy.
3. Test totals must be re-read from ACTUAL command output and reported exactly. Do not reuse remembered totals.
4. During the previous execution, the OWNER PKCS#12 password was exposed in an executed command/transcript. Before the OWNER file becomes the permanent owner access file, rotate ONLY the PKCS#12 bundle password without changing the OWNER certificate identity.

Do not echo the old password.
Do not echo the new password in chat, logs, command text, documentation, or git.

---

# 3. PREFLIGHT

From `C:\tbootit` record:

- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git log -1 --oneline`
- `docker compose ps`

Do not destroy current work.

Inspect the current Stage 07A-R1 diff/state before changing anything.

---

# 4. OWNER P12 PASSWORD ROTATION

The existing OWNER certificate identity must remain the same.

Required:

1. Read the current OWNER certificate fingerprint/serial internally.
2. Generate a NEW strong random PKCS#12 password.
3. Re-export/replace:

`data\auth\certificates\owner.p12`

using the EXISTING OWNER private key and EXISTING OWNER certificate.

4. Update:

`data\auth\owner_password.txt`

with the new password.

5. Verify the OWNER certificate fingerprint/serial before and after is identical.
6. Verify the new `.p12` imports/works with the new password.
7. Do not print either password anywhere.
8. Do not create a second OWNER identity.
9. Do not regenerate the CA.

The final report may state only:

`OWNER_P12_PASSWORD_ROTATED: true`

and where the password file is located.

Never include the password itself.

---

# 5. VERIFY SECURITY GATE

Re-run the real live verification of the existing implementation.

At minimum prove:

- no certificate -> denied;
- OWNER -> normal app allowed;
- OWNER -> `/certificates` allowed;
- USER ACTIVE -> normal app allowed;
- USER -> `/certificates` denied;
- USER revoke -> status REVOKED;
- revoked USER -> denied;
- OWNER revoke API attempt -> denied;
- restart gateway/admin-shell -> CA/OWNER/registry persist;
- direct client headers cannot bypass certificate validation;
- external/raw module ports do not provide an mTLS bypass according to the existing project access contract.

Use the existing verification script where correct.
Fix the verification script only if it has a real defect.

---

# 6. RE-RUN TESTS AND REPORT EXACT COUNTS

Run the actual relevant test suites.

At minimum:

- `pytest admin-shell/tests`
- Core tests in the way currently supported by the project/container
- inventory-sales-module tests
- repairs-module tests
- avito-module tests

IMPORTANT:

Report exactly what each executed command actually says.

Do NOT infer totals.
Do NOT copy totals from the previous report.
Do NOT claim `95 passed` if the actual Avito command says another number.

For each suite report:

`command -> X passed, Y failed`

If a suite cannot be run, state the exact reason.

---

# 7. REQUIRED PROJECT RECORDS

Ensure the standard project records exist and accurately reflect the final implementation.

Required received prompt:

`.agents\received_prompts\TECHNOREBOOT_STAGE07A_R1_R1_VERIFY_FINALIZE_PROMPT.md`

Ensure the original Stage07A-R1 received prompt is also preserved if it exists.

Create/update:

`docs\stage07a_r1_minimal_certificate_access.md`

`reports\stage07a_r1_minimal_certificate_access_report.md`

`logs\2026-09-08.md`

The report must contain only verified facts and exact test totals.

Do not put passwords, private keys, P12 contents or other secret values in these files.

---

# 8. SECRET CHECK

Before commit:

1. Run appropriate git searches/status checks.
2. Confirm `data/auth/` and generated secrets are ignored.
3. Inspect staged diff.
4. Search tracked/staged project files for accidental OWNER password/private-key material.
5. If any secret from Stage07A was accidentally written into a TRACKED project file, remove it before commit.
6. Do not attempt destructive cleanup of Antigravity's own internal transcript/history; just ensure project/git artifacts are clean.

---

# 9. GIT FINALIZATION

After all checks pass:

1. `git status`
2. stage only correct project files
3. inspect staged diff
4. commit Stage 07A-R1 / R1-R1 finalization
5. push to `origin/main`
6. verify push succeeded
7. record final commit hash
8. verify final `git status`

Do not commit runtime auth secrets.

---

# 10. FINAL REPORT

Return exactly this structure:

```text
# Stage 07A-R1-R1 — Verification & Finalization

## Preflight
BRANCH:
HEAD_BEFORE:
GIT_STATUS_BEFORE:
DOCKER_STATUS:

## Existing Implementation
- concise confirmed architecture

## OWNER Bundle
OWNER_CERT_IDENTITY_UNCHANGED: true/false
OWNER_P12_PASSWORD_ROTATED: true/false
OWNER_P12_PATH:
OWNER_PASSWORD_FILE_PATH:
CA_UNCHANGED: true/false

Do not print any password.

## Runtime Verification
NO_CERT_DENIED:
OWNER_APP_ALLOWED:
OWNER_ADMIN_ALLOWED:
USER_APP_ALLOWED:
USER_ADMIN_DENIED:
USER_REVOKE_WORKS:
REVOKED_USER_DENIED:
OWNER_REVOKE_BLOCKED:
PERSISTENCE_AFTER_RESTART:
HEADER_BYPASS_BLOCKED:
RAW_PORT_BYPASS_BLOCKED:

## Exact Test Results
admin-shell:
core:
inventory-sales-module:
repairs-module:
avito-module:

## Project Records
RECEIVED_PROMPT:
DOC:
REPORT:
DAILY_LOG:

## Secret Safety
RUNTIME_AUTH_IGNORED:
TRACKED_SECRET_SCAN:
STAGED_SECRET_SCAN:

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
1.
2.
3.
4.
5.

FINAL_STATUS:
TECHNOREBOOT_STAGE07A_R1_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
BACKUP_STAGE_NOT_STARTED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If any required verification fails, return a truthful BLOCKED status instead of READY.

---

# 11. STOP

After report/commit/push, STOP.

Do not start backup.
Do not start Internet deployment.
Do not extend authentication.
Wait for owner acceptance.
