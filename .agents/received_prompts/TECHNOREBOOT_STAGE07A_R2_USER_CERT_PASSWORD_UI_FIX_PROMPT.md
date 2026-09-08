# TECHNOREBOOT — Stage 07A-R2
## User Certificate Password UX Fix

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07A-R2 — User Certificate Password UX Fix`

---

# 0. EXECUTION CONTRACT

This is a small corrective stage for the already implemented and verified Stage 07A-R1 certificate access system.

Do NOT redesign mTLS.
Do NOT change CA/OWNER architecture.
Do NOT start backup.
Do NOT deploy to Internet.
Do NOT add new auth features.

First copy this exact downloaded file:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07A_R2_USER_CERT_PASSWORD_UI_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07A_R2_USER_CERT_PASSWORD_UI_FIX_PROMPT.md`

Create the destination directory if needed.

Treat the copied file as the authoritative prompt for this stage.

---

# 1. ACCEPTED BASELINE

Stage 07A-R1 / R1-R1 is implemented and verified:

- mTLS gateway works;
- OWNER certificate works;
- USER certificates can be issued;
- USER certificates can be revoked;
- OWNER-only `/certificates` admin page works;
- persistence works;
- runtime tests pass;
- current implementation is already committed/pushed.

Do not refactor unrelated code.

---

# 2. OWNER-FOUND DEFECT

During manual Owner Check, a real UX defect was found.

When OWNER issues a new USER certificate:

- the generated one-time PKCS#12 password appears only momentarily;
- the UI immediately changes/refreshes/continues;
- the owner has no practical time to copy or save the password;
- after that the password is not recoverable.

This makes the downloaded `.p12` unusable unless the owner somehow captures the password instantly.

This is the only defect to fix in this stage.

---

# 3. REQUIRED BEHAVIOR

After successful USER certificate creation, the page must STOP and clearly show a persistent result dialog/modal/panel.

It must remain visible until OWNER explicitly closes it.

Required content:

```text
Сертификат выпущен

Название: <certificate name>

Пароль:
[ <generated password> ] [ Копировать ]

[ Скачать сертификат .p12 ]
[ Скачать пароль .txt ]

[ Закрыть ]
```

Exact styling may follow the existing Admin Shell conventions.

Important behavior:

1. The password must remain visible after issuance.
2. No automatic page refresh/navigation may hide it.
3. `Копировать` must copy the password to clipboard.
4. `Скачать сертификат .p12` must download the newly created `.p12`.
5. `Скачать пароль .txt` must download a simple UTF-8 text file containing the generated password.
6. The dialog/panel closes only when OWNER clicks `Закрыть`.
7. After closing, the certificate remains visible in the table as `ACTIVE`.
8. The password does NOT need to become permanently viewable later.
9. Do NOT store ordinary USER passwords in the registry just to support this UI.
10. Do NOT add a “show password later” feature.

The current one-time password model remains.

---

# 4. SECURITY / SIMPLE STORAGE RULE

Keep the current security model:

- USER certificate password is generated once;
- it may exist in request/response memory long enough to render/download immediately;
- do not persist it into `registry.json`;
- do not log it;
- do not write it into tracked project files;
- do not expose it in server logs;
- do not include it in final report.

If a temporary server-side file is required to generate the `.txt`, prefer an in-memory response or equivalent minimal implementation.

Do not create long-lived password storage.

---

# 5. EXISTING CERTIFICATES

Do NOT regenerate CA.
Do NOT regenerate OWNER.
Do NOT change OWNER password.
Do NOT alter already existing certificate identities.

Any already-issued USER certificate whose password was lost may remain as-is; Owner can revoke it manually later.

This stage only fixes the issuance UX for future certificates.

---

# 6. TESTS

Add/update focused tests for this bug.

At minimum verify:

## TEST A
Issue a USER certificate through the backend/API.

Expected:
- success response;
- generated password is returned to the OWNER issuance flow;
- `.p12` download works.

## TEST B
UI does not immediately lose the result after successful issuance.

Expected:
- persistent result modal/panel is rendered;
- generated password is visible there.

## TEST C
Copy button exists and is wired to copy the password.

## TEST D
`.p12` download button/link exists and points to the new certificate.

## TEST E
Password `.txt` download works and contains exactly the generated password (plus optional newline only).

## TEST F
Password is NOT written into certificate registry.

## TEST G
Ordinary USER still cannot access `/certificates`.

## TEST H
Revocation still works.

## TEST I
Run the full `admin-shell` test suite and ensure no regression.

If another project suite is affected by the implementation, run it too.
Do not waste time re-running every unrelated module unless needed.

---

# 7. MANUAL RUNTIME CHECK

Actually run the project and perform a live check through the existing gateway.

Use OWNER certificate and verify:

1. open `/certificates`;
2. create test certificate named:
   `TEST-PASSWORD-UI`;
3. result remains visible;
4. password can be copied;
5. `.p12` downloads;
6. password `.txt` downloads;
7. downloaded `.txt` password successfully imports the downloaded `.p12`;
8. imported USER opens normal Technoreboot;
9. imported USER gets `403` on `/certificates`;
10. OWNER can revoke `TEST-PASSWORD-UI`;
11. revoked USER gets `403`.

Do not expose the generated password in the final chat report.

After the live test, the test USER certificate may remain `REVOKED`.

---

# 8. PROJECT RECORDS

Preserve this prompt in:

`.agents\received_prompts\TECHNOREBOOT_STAGE07A_R2_USER_CERT_PASSWORD_UI_FIX_PROMPT.md`

Create/update:

`docs\stage07a_r2_user_cert_password_ui_fix.md`

`reports\stage07a_r2_user_cert_password_ui_fix_report.md`

`logs\2026-09-08.md`

Document only verified behavior.
Do not include passwords or private key material.

---

# 9. GIT

After successful implementation and verification:

1. inspect `git status`;
2. inspect diff;
3. ensure no runtime secrets are staged;
4. commit;
5. push to `origin/main`;
6. verify final HEAD;
7. verify final worktree state.

Do not start another stage.

---

# 10. FINAL REPORT

Return:

```text
# Stage 07A-R2 — User Certificate Password UX Fix

## Defect
- concise description

## Fix Implemented
- exact UI/backend behavior

## Files Changed

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

## Manual Live Check
CREATE_TEST_CERT:
PASSWORD_VISIBLE_UNTIL_CLOSE:
COPY_BUTTON:
P12_DOWNLOAD:
PASSWORD_TXT_DOWNLOAD:
P12_IMPORT_WITH_TXT_PASSWORD:
USER_APP_ACCESS:
USER_ADMIN_DENIED:
REVOKE:
REVOKED_USER_DENIED:

## Security
USER_PASSWORD_PERSISTED_IN_REGISTRY: false
USER_PASSWORD_LOGGED: false
CA_CHANGED: false
OWNER_CHANGED: false

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

FINAL_STATUS:
TECHNOREBOOT_STAGE07A_R2_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
BACKUP_STAGE_NOT_STARTED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If any required check fails, return a truthful BLOCKED status.

---

# 11. STOP

After implementation, verification, documentation, commit/push and final report:

STOP.

Do not start backup.
Do not start Internet deployment.
Do not expand certificate functionality.
Wait for owner acceptance.
