# TECHNOREBOOT — Stage 07B-R2
## Web Backup / Restore — Owner UI only

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Stage:** `Stage 07B-R2 — Web Backup / Restore`

---

# 0. EXECUTION CONTRACT

Stage 07B-R1 is NOT accepted in its current owner workflow.

Reason:
the backup/restore mechanism was implemented around CMD scripts and manual console usage.

The owner explicitly rejects that workflow.

The required workflow must be ONLINE / WEB-BASED through the existing Technoreboot admin interface.

Do NOT ask the owner to run CMD, PowerShell, Python, shell scripts, docker commands or terminal commands for normal backup/restore operation.

First copy this exact downloaded file:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07B_R2_WEB_BACKUP_RESTORE_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07B_R2_WEB_BACKUP_RESTORE_PROMPT.md`

Create the destination directory if needed.

Treat the copied file as the authoritative prompt for this corrective stage.

Do not start Internet deployment.

---

# 1. ACCEPTED BASELINE

Stage 07A certificate access is accepted.

Stage 07B-R1 already created useful low-level backup/restore logic and proved that:
- SQLite backup can be created/restored;
- product photos/media can be preserved;
- auth/CA/OWNER state can be preserved;
- Avito persistent state can be preserved;
- restore can return data to the backup point;
- OWNER and CA identities survive restore.

Reuse reliable internal logic where useful.

Do NOT rewrite working low-level backup code unnecessarily.

But remove the CMD-based OWNER workflow.

---

# 2. OWNER REQUIREMENT

The owner wants this:

```text
Technoreboot web admin
        ↓
Backup page
        ↓
[ Скачать резервную копию ]
```

Browser downloads one backup file to the owner's computer.

Restore:

```text
Technoreboot web admin
        ↓
Backup page
        ↓
[ Выбрать файл резервной копии ]
[ Восстановить ]
        ↓
confirmation
        ↓
server restores mutable data
```

No console.

No CMD.

No PowerShell.

No manual file collection.

No separate desktop utility.

---

# 3. WHAT MUST BE BACKED UP

Do NOT back up the source code / Git repository as the main backup payload.

The project/source can be redeployed from Git/local source.

The backup must focus on mutable, business-critical, non-recreatable data.

At minimum include:

1. **Main database**
   - `data/db/technoreboot.db`
   - use a safe SQLite snapshot mechanism, not unsafe raw copy of an actively written database.

2. **Product photos / media**
   - actual mutable storage under `data/storage/...`

3. **Auth / mTLS persistent state**
   - CA identity;
   - OWNER certificate/key/bundle;
   - certificate registry;
   - revoke state;
   - required server/auth persistent secrets.
   This is necessary so the same OWNER certificate continues working after restore.

4. **Avito persistent runtime state**
   - only real mutable state under `data/avito-module/...` that is not trivially regenerated and is needed for continuity.

5. Any other CURRENT persistent runtime data discovered in the actual project that is mutable and not safely recoverable from Git.

Do NOT include:
- source tree;
- Docker images;
- caches;
- build artifacts;
- logs unless required for recovery;
- tests;
- documentation;
- temporary files;
- existing backup files.

The backup should remain small and focused on DATA.

---

# 4. WEB UI

Add a very simple OWNER-only page in the existing Admin Shell.

Preferred route:

`/backups`

Add a navigation item such as:

`Резервные копии`

Access:
- OWNER certificate only;
- normal USER certificate -> `403`.

Keep the page minimal.

Required UI:

```text
ТЕХНОРЕБУТ — РЕЗЕРВНОЕ КОПИРОВАНИЕ

Резервная копия содержит:
- База данных
- Фото и файлы
- Данные доступа / сертификаты
- Другие изменяемые данные системы

[ Скачать резервную копию ]

--------------------------------

ВОССТАНОВЛЕНИЕ

[ Выбрать файл резервной копии ]

[ Восстановить ]

Внимание: восстановление заменит текущие данные данными из выбранной копии.
```

No dashboard.
No charts.
No backup history table unless technically necessary.
No scheduler.
No retention UI.

---

# 5. WEB BACKUP DOWNLOAD

Implement OWNER-only web endpoint.

Example:

`POST /admin-api/backups/create`

or equivalent.

Expected behavior:

1. Create a consistent backup package.
2. Validate creation.
3. Return/download one file to the browser.

Preferred filename:

`TECHNOREBOOT_BACKUP_YYYY-MM-DD_HHMMSS.zip`

The browser should receive the ZIP directly.

Avoid leaving permanent copies on the server after successful download.

Temporary server-side file is acceptable only if:
- created in a dedicated temp location;
- cleaned automatically after response / shortly after;
- not accumulated forever.

The ZIP must contain a manifest.

Example logical structure:

```text
manifest.json
database/technoreboot.db
storage/...
auth/...
avito-module/...
```

Include SQL dump only if it materially improves recovery and does not complicate the design.

Primary requirement is a reliable restore.

---

# 6. MANIFEST

Include a small `manifest.json`.

At minimum:

- format_version;
- created_at;
- git_commit;
- database info;
- included components;
- CA fingerprint;
- OWNER fingerprint;
- certificate registry counts;
- backup application version/stage if available.

Never put passwords or private key contents in manifest.

---

# 7. WEB RESTORE UPLOAD

Implement OWNER-only restore through browser upload.

Recommended flow:

1. OWNER chooses `.zip`.
2. Backend receives upload to a temporary location.
3. Backend validates archive BEFORE touching live data:
   - ZIP integrity;
   - manifest present;
   - supported format version;
   - database present;
   - auth/CA/OWNER state present;
   - required paths present.
4. UI shows explicit confirmation:
   `Восстановление заменит текущие данные. Продолжить?`
5. Only after explicit confirmation perform restore.
6. Restore mutable persistent state.
7. Restart/reload only what is technically necessary.
8. Verify application health.
9. Return a clear success/failure result to the OWNER web page.
10. Remove uploaded temporary archive after completion/failure where safe.

Do not require shell access from the owner.

Internal backend code may invoke Docker/service operations if technically necessary, but this must be fully encapsulated behind the web action.

---

# 8. IMPORTANT RESTORE UX

Because restore may briefly restart services, design the browser flow so the owner understands what is happening.

Minimal acceptable behavior:

After clicking restore:

```text
Восстановление выполняется...
```

Then one of:

```text
Резервная копия успешно восстановлена.
Система перезапущена.
```

or:

```text
Ошибка восстановления:
<safe concise error>
```

Do not dump stack traces or secrets into the browser.

If the current request cannot survive service restart, use a simple job/status mechanism or equivalent minimal approach so the browser can poll status.

Do NOT build a complex queue system.

---

# 9. OWNER / USER ACCESS

Backup page and backup API must be OWNER-only.

Required:

- OWNER -> allowed;
- USER -> 403;
- no client certificate -> denied by mTLS gateway.

Do not create a second login.

Reuse the existing Stage 07A OWNER authorization.

---

# 10. DELETE CMD OWNER WORKFLOW

The owner explicitly rejects CMD-based operation.

Remove the user-facing CMD workflow from the project.

At minimum:

DELETE:
- `backup/backup_full.cmd`
- `backup/restore_full.cmd`

Update/remove README sections that instruct the owner to use CMD.

Do not leave documentation saying normal backup/restore requires terminal commands.

If low-level Python code is still useful internally:
- refactor/reuse it as importable backend functions/modules;
- it must not be the documented OWNER workflow.

The only documented normal workflow after this stage must be WEB UI.

---

# 11. BACKUP SECURITY

This backup contains sensitive auth state.

Do not expose the backup endpoint to ordinary users.

Do not log:
- OWNER password;
- private keys;
- P12 password;
- certificate private material.

Do not commit generated backup archives to Git.

Keep `backups/` or temp backup output ignored.

No cloud upload in this stage.

---

# 12. REAL RUNTIME VERIFICATION

Perform live browser/API-equivalent verification through the actual running stack.

Required scenario:

## TEST A — OWNER page
OWNER can open `/backups`.

## TEST B — USER denied
USER gets 403 on `/backups` and backup/restore endpoints.

## TEST C — download
OWNER creates backup through web endpoint.
Response downloads a valid ZIP.

## TEST D — contents
ZIP contains:
- database;
- mutable storage/media;
- auth state;
- manifest;
- other required mutable state.

## TEST E — no source tree
ZIP does NOT contain the whole repository/application source.

## TEST F — invalid restore
Upload invalid ZIP.
Restore rejected before touching live data.

## TEST G — controlled restore
Create a valid web backup.
Make a disposable controlled mutable-data change AFTER the backup.
Upload the backup via web restore flow.
Confirm restore.

Expected:
post-backup disposable change is reverted.

## TEST H — database
Database returns to backup state.

## TEST I — media
Media baseline survives.

## TEST J — auth
Same OWNER/CA identity survives.

## TEST K — revoked state
A revoked USER remains revoked.

## TEST L — application
System returns healthy after web restore.

## TEST M — mTLS
OWNER still enters through the existing certificate after restore.

## TEST N — UI
Web page shows understandable success/failure status.

No CMD commands may be required from OWNER for these checks.

Automation may use internal test code/API requests to prove behavior.

---

# 13. TESTS

Add focused automated tests.

At minimum verify:

- OWNER-only page;
- USER denied;
- backup download response;
- filename/content-type;
- manifest;
- database inclusion;
- media inclusion;
- auth inclusion;
- source exclusion;
- invalid archive rejection;
- restore confirmation contract;
- successful restore;
- persistence of OWNER/CA/revoked state;
- temp archive cleanup where applicable.

Run relevant admin-shell and backup tests.

Do not rerun every unrelated module unless the implementation changes shared behavior.

Report exact real totals.

---

# 14. OWNER MANUAL CHECK

The final manual check must require ONLY browser actions.

Expected final guide must look like:

```text
1. Open:
   https://127.0.0.1:8443/backups

2. Click:
   Скачать резервную копию

3. Confirm that the browser downloaded:
   TECHNOREBOOT_BACKUP_....zip

4. On the same page select that ZIP in the restore field.

5. Click:
   Восстановить

6. Confirm the warning.

7. Wait for:
   Резервная копия успешно восстановлена.
```

No terminal commands in Owner Manual Check.

---

# 15. PROJECT RECORDS

Preserve this prompt:

`.agents\received_prompts\TECHNOREBOOT_STAGE07B_R2_WEB_BACKUP_RESTORE_PROMPT.md`

Create/update:

`docs\stage07b_r2_web_backup_restore.md`

`reports\stage07b_r2_web_backup_restore_report.md`

`logs\2026-09-08.md`

Update/remove Stage07B documentation that currently presents CMD scripts as the normal owner workflow.

---

# 16. GIT

Before commit:
- inspect diff;
- ensure no actual backup ZIP is staged;
- ensure no DB dump with owner data is staged;
- ensure no auth secret is staged;
- ensure runtime temp backup files are ignored.

Then:
- commit;
- push `origin/main`;
- report commit hash;
- verify clean tracked worktree.

---

# 17. FINAL REPORT CONTRACT

Return:

```text
# Stage 07B-R2 — Web Backup / Restore

## Defect Corrected
CMD_OWNER_WORKFLOW_REMOVED: true/false
WEB_ONLY_OWNER_WORKFLOW: true/false

## Mutable Data Included
DATABASE:
MEDIA:
AUTH:
AVITO_STATE:
OTHER:

## Web UI
BACKUP_PAGE:
OWNER_ACCESS:
USER_DENIED:
BACKUP_BUTTON:
RESTORE_UPLOAD:
CONFIRMATION:
STATUS_FEEDBACK:

## Backup Download
TEST:
FILENAME:
CONTENT_TYPE:
MANIFEST:
SIZE:
TEMP_FILE_CLEANUP:

## Web Restore
INVALID_ARCHIVE_REJECTED:
CONTROLLED_RESTORE:
DATABASE_RESTORED:
MEDIA_RESTORED:
OWNER_IDENTITY_PRESERVED:
CA_IDENTITY_PRESERVED:
REVOKED_STATE_PRESERVED:
SYSTEM_HEALTHY_AFTER_RESTORE:

## Tests
- exact commands
- exact passed/failed totals

## Files Changed / Removed

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R2_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If any critical web backup/restore behavior fails, return a truthful BLOCKED status.

---

# 18. STOP

After implementation, verification, documentation, commit/push and final report:

STOP.

Do not start Internet deployment.
Do not add scheduled backups.
Do not add cloud storage.
Do not expand backup UI.
Wait for owner acceptance.
