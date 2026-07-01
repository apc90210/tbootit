# TECHNOREBOOT — Stage 03B Audit / Acceptance Prompt

## Role

You are a senior backend auditor, integration QA engineer, and repository safety reviewer.

## Project

```text
C:\tbootit
```

## Context

Stage03B recovery/closure reported:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_READY_FOR_AUDIT
```

Reported commit:

```text
HEAD:
feb21fc

Commit message:
Implement Stage 03B parsed Avito ads to Core import
```

Reported implementation:

```text
Core import endpoint:
POST /api/product-cards/import-json

Avito import endpoint:
POST /api/avito/parsed-ads/{ad_id}/core-import

Avito import status endpoint:
GET /api/avito/parsed-ads/{ad_id}/core-import-status

Preview endpoint unchanged:
POST /api/avito/parsed-ads/{ad_id}/core-import-preview
```

Reported tests:

```text
core_pytest: 28 passed
avito_module_pytest: 12 passed
smoke_core_health: PASS
smoke_avito_health: PASS
sample_parse: PASS
preview: PASS
import: PASS
repeat_import_without_force: PASS (already_imported)
import_status: PASS
```

Reported safety:

```text
runtime_data_committed: NO
git_add_dot_used: NO
direct_core_db_access_from_avito: NO
live_avito_crawling: NO
browser_automation: NO
captcha_bypass: NO
stage04_started: NO
```

Important audit caveats to verify:

```text
1. Commit includes deletion of:
   avito-module/run_test.py

   This is acceptable only if it was a tracked scratch/test helper file and no runtime/user data was deleted.

2. Commit includes received prompts under:
   .agents/received_prompts/

   This is acceptable only if these are governance/prompt record files and not secrets/runtime data.

3. The implementation must import parsed Avito ads through Core HTTP API only.
   Avito module must not import Core DB/session/ORM internals.

4. Runtime import records must remain under ignored data/avito-module and must not be committed.

5. Stage04 must not be started.
```

---

## Expected final status

If safe:

```text
TECHNOREBOOT_STAGE03B_ACCEPTED_READY_FOR_STAGE04_PLANNING
```

If issues found:

```text
TECHNOREBOOT_STAGE03B_AUDIT_BLOCKED
```

Do not start Stage04 in this prompt.

---

## Hard rules

Do not use:

```text
git reset
git clean
git push --force
git commit --amend
git rebase
git cherry-pick
git add .
git add -u
```

Do not modify implementation source unless explicitly creating the audit report.

Do not run live Avito crawling.

Do not use browser automation.

Do not bypass captcha.

Do not write directly to Core DB from Avito module.

Do not commit runtime data.

---

## Mandatory execution logging

Read:

```text
.agents/AGENTS.md
```

Append to:

```text
logs/YYYY-MM-DD.md
```

Start entry must include:

```text
timestamp
prompt filename
prompt source path
copied prompt path under .agents/received_prompts
branch
HEAD
git status
task/stage
audit caveats
forbidden actions
```

Checkpoint after each major step.

Final log entry must include:

```text
FINAL_STATUS
branch
HEAD
worktree clean true/false
audit result
tests run and results
blockers
next step
```

---

## Prompt handling

Find this prompt in:

```text
C:\Users\Apc\Downloads
```

Copy it into:

```text
C:\tbootit\.agents\received_prompts\
```

Record both paths in the execution log.

---

## Step 1 — Preflight

Run:

```powershell
cd C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10
git show --name-status --oneline --stat HEAD
git show --name-only --pretty=format: HEAD
```

Required:

```text
HEAD commit message == Implement Stage 03B parsed Avito ads to Core import
Worktree has no tracked dirty source/report/log files before audit
```

If worktree dirty, report exact files. Do not clean broadly.

Checkpoint:

```text
CHECKPOINT: preflight
```

---

## Step 2 — Commit content audit

Run:

```powershell
git show --name-status --pretty=format: HEAD
git show --stat HEAD
```

Expected committed files:

```text
.agents/received_prompts/TECHNOREBOOT_AGENT_EXECUTION_LOGGING_RULES_PATCH_PROMPT.md
.agents/received_prompts/TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_PROMPT_V2.md
.agents/received_prompts/TECHNOREBOOT_STAGE03B_RECOVERY_AND_CLOSURE_PROMPT.md
avito-module/app/core_client.py
avito-module/app/routers/exports.py
avito-module/app/schemas.py
avito-module/app/storage.py
avito-module/run_test.py (deleted)
avito-module/tests/test_contract_no_core_write.py
avito-module/tests/test_core_import.py
logs/2026-07-01.md
reports/stage03b_parsed_avito_ads_to_core_import_report.md
```

Classify:

```text
source_changes_expected:
test_changes_expected:
report_created:
log_created_or_updated:
received_prompts_committed:
run_test_deleted:
unexpected_files:
```

For `avito-module/run_test.py`, verify from git history:

```powershell
git show HEAD^:avito-module/run_test.py
git log --oneline -- avito-module/run_test.py
```

Accept deletion only if:

```text
file was a scratch/test helper,
not runtime data,
not required by application,
not referenced by Docker or tests after commit.
```

Verify no references remain:

```powershell
git grep -n -I "run_test.py\|run_test" -- .
```

If unexpected files or unsafe deletion:

```text
TECHNOREBOOT_STAGE03B_AUDIT_BLOCKED
```

Checkpoint.

---

## Step 3 — Architecture boundary audit

Run:

```powershell
git grep -n -I "technoreboot.db\|SessionLocal\|create_engine\|SELECT .* FROM products\|INSERT INTO products" -- avito-module

git grep -n -I "from core\|import core\|core.app\|ProductCard.*from core" -- avito-module

git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module

git status --ignored --short --untracked-files=all -- data/avito-module
git ls-files data/avito-module
```

Expected:

```text
No direct Core DB access from avito-module.
No Core internal Python imports from avito-module.
Only HTTP client calls to Core API.
No browser automation/captcha bypass.
data/avito-module runtime files ignored/uncommitted.
```

Checkpoint.

---

## Step 4 — Endpoint contract audit

Inspect:

```powershell
Get-Content avito-module\app\core_client.py
Get-Content avito-module\app\storage.py
Get-Content avito-module\app\schemas.py
Get-Content avito-module\app\routers\exports.py
Get-Content avito-module\tests\test_core_import.py
Get-Content avito-module\tests\test_contract_no_core_write.py
Get-Content reports\stage03b_parsed_avito_ads_to_core_import_report.md
```

Verify:

```text
core-import-preview still exists.
core-import-preview does not call Core import.
core-import endpoint exists.
core-import calls Core through HTTP client only.
core-import-status endpoint exists.
preview/import share deterministic mapping.
idempotency exists: already_imported if force=false and record exists.
force=true permits retry/reimport.
local import status path is under data/avito-module.
```

Checkpoint.

---

## Step 5 — Test suite

Run:

```powershell
docker compose ps
docker compose exec core pytest
docker compose exec avito-module pytest
```

Required:

```text
core_pytest: PASS
avito_module_pytest: PASS
```

Checkpoint.

---

## Step 6 — Smoke / endpoint E2E checks

Run:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8020/health | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8020/api/core/health | ConvertTo-Json
```

Run sample parse:

```powershell
$body = @{ profile_url = "sample://avito_profile_sample"; max_pages = 1; save_html = $true } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8020/api/avito/profiles/parse -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 10
```

Get parsed ad:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads | ConvertTo-Json -Depth 10
```

Use a real `AD_ID` from the response:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import-preview" | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import" -ContentType "application/json" -Body (@{ force = $false } | ConvertTo-Json) | ConvertTo-Json -Depth 10

Invoke-RestMethod "http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import-status" | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import" -ContentType "application/json" -Body (@{ force = $false } | ConvertTo-Json) | ConvertTo-Json -Depth 10
```

Required:

```text
preview: PASS
import: PASS
import_status: PASS
repeat_import_without_force: already_imported
```

Do not live crawl Avito.

Checkpoint.

---

## Step 7 — Runtime artifact check

Run:

```powershell
git status --short --untracked-files=all
git status --ignored --short --untracked-files=all -- data/avito-module
git ls-files data/avito-module
```

Required:

```text
runtime_data_committed: false
data/avito-module ignored or untracked only
no tracked dirty runtime files
```

Checkpoint.

---

## Step 8 — Create audit report

Create exactly:

```text
reports/stage03b_audit_acceptance_report.md
```

Report content:

```text
FINAL_STATUS:
PROJECT:
BRANCH:
HEAD:
WORKTREE_CLEAN:

COMMIT_AUDIT:
- stage03b_commit:
- committed_files_expected_only:
- received_prompts_committed:
- run_test_deleted:
- run_test_deletion_safe:
- unexpected_files:

ARCHITECTURE:
- avito_direct_core_db_access:
- avito_core_internal_imports:
- avito_core_api_only:
- browser_automation_or_captcha_bypass:
- runtime_data_committed:
- stage04_started:

ENDPOINTS:
- core_import_endpoint:
- avito_preview_endpoint:
- avito_import_endpoint:
- avito_import_status_endpoint:
- idempotency_behavior:
- local_import_record_storage:

TESTS:
- core_pytest:
- avito_module_pytest:
- smoke_core_health:
- smoke_avito_health:
- avito_core_health:
- sample_parse:
- preview:
- import:
- import_status:
- repeat_import_without_force:

LOGGING:
- execution_log:
- checkpoints_present:
- final_entry_present:

BLOCKERS:
- ...

NEXT_STEP:
- Stage04 planning only after owner acceptance.
```

Append final log entry.

---

## Step 9 — Commit audit report only

Stage exact files only:

```powershell
git add reports\stage03b_audit_acceptance_report.md
git add logs\2026-07-01.md
git add .agents\received_prompts\TECHNOREBOOT_STAGE03B_AUDIT_ACCEPTANCE_PROMPT.md
```

Only add the received prompt if it exists and was copied.

Do not use `git add .`.

Verify:

```powershell
git diff --cached --name-status
git diff --cached --check
```

Commit:

```powershell
git commit -m "Audit Stage 03B parsed Avito ads Core import"
```

---

## Final response

Return exactly:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE03B_ACCEPTED_READY_FOR_STAGE04_PLANNING
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

COMMIT_AUDIT:
- stage03b_commit:
- committed_files_expected_only:
- received_prompts_committed:
- run_test_deleted:
- run_test_deletion_safe:
- unexpected_files:

ARCHITECTURE:
- avito_direct_core_db_access:
- avito_core_internal_imports:
- avito_core_api_only:
- browser_automation_or_captcha_bypass:
- runtime_data_committed:
- stage04_started:

ENDPOINTS:
- core_import_endpoint:
- avito_preview_endpoint:
- avito_import_endpoint:
- avito_import_status_endpoint:
- idempotency_behavior:
- local_import_record_storage:

TESTS:
- core_pytest:
- avito_module_pytest:
- smoke_core_health:
- smoke_avito_health:
- avito_core_health:
- sample_parse:
- preview:
- import:
- import_status:
- repeat_import_without_force:

LOGGING:
- execution_log:
- checkpoints_present:
- final_entry_present:

REPORT:
- reports/stage03b_audit_acceptance_report.md

BLOCKERS:
- None

NEXT_STEP:
- Stage04 planning only after owner acceptance. Do not start Stage04 automatically.
```
