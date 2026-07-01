# TECHNOREBOOT — Stage 03B Recovery, Validation, and Closure Prompt

## Role

You are a senior backend developer, integration engineer, and repository safety auditor.

## Project

```text
C:\tbootit
```

## Why this prompt exists

A Stage03B implementation attempt was executed, but it did not finish in the required closure format.

The attempt reported:

```text
Stage 03B implemented
Core pytest: 28 passed
Avito module pytest: 12 passed
Execution log updated: logs/2026-07-01.md
```

But the run is NOT accepted because:

```text
1. Required final status was not returned:
   TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_READY_FOR_AUDIT

2. Required report was not created:
   reports/stage03b_parsed_avito_ads_to_core_import_report.md

3. The log itself says:
   worktree clean: false
   committed files: none

4. The implementation was not committed.

5. The transcript shows extra edited files:
   implementation_plan.md
   task.md
   walkthrough.md

6. The prompt required exact-file staging and no runtime/scratch artifacts.

7. Smoke endpoint checks for preview/import/status were not fully shown in final required format.

8. There was an obsolete scratch file issue:
   avito-module/run_test.py existed inside Docker container and was deleted from the container.
   The repo must verify this file is not present/committed locally.
```

This prompt must recover the current work safely, validate it, create the required report, and commit exact intended files only.

Do not start Stage04.

---

## Accepted prior state

Stage03A accepted:

```text
TECHNOREBOOT_STAGE03A_AUDIT_ACCEPTED_WITH_GIT_ADD_DOT_CAVEAT_READY_FOR_STAGE03B
```

Agent logging rules accepted:

```text
TECHNOREBOOT_AGENT_EXECUTION_LOGGING_RULES_PATCH_READY
```

Current intended Stage03B goal:

```text
Parsed Avito Ads → Core Import through Core HTTP API only.
```

---

## Expected final status

If safe and complete:

```text
TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_READY_FOR_AUDIT
```

If current dirty work contains unsafe/unexpected files:

```text
TECHNOREBOOT_STAGE03B_RECOVERY_BLOCKED_UNEXPECTED_WORKTREE_CONTENT
```

If tests fail:

```text
TECHNOREBOOT_STAGE03B_RECOVERY_BLOCKED_TESTS_FAILED
```

If forbidden action used:

```text
TECHNOREBOOT_STAGE03B_RECOVERY_BLOCKED_FORBIDDEN_ACTION_USED
```

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

Do not:

```text
start Stage04
perform live Avito crawling
use browser automation
use Selenium
use Playwright
bypass captcha
write directly to Core DB from Avito module
commit runtime data from data/avito-module
commit *.db / *.sqlite / __pycache__ / downloaded HTML
commit Antigravity/Gemini walkthrough files
commit random task.md / implementation_plan.md unless they are explicitly approved project docs
```

No broad restore. If a file must be removed from the working tree, first classify it and record it in the log.

---

## Mandatory execution logging

Before doing anything else, read:

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
reason for recovery
forbidden actions
```

After each major step, append a checkpoint:

```text
timestamp
step name
commands run
files read
files changed
tests/checks run
result
next intended action
```

Final log entry must include:

```text
FINAL_STATUS
branch
HEAD
worktree clean true/false
committed files
tests run and results
blockers
next step
audit/acceptance ready true/false
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

## Step 1 — Preflight and dirty worktree inventory

Run:

```powershell
cd C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -15
git diff --name-status
git diff --stat
git status --ignored --short --untracked-files=all -- data/avito-module
```

Also inspect the execution log:

```powershell
Get-Content logs\2026-07-01.md
```

Record in the log:

```text
current branch
current HEAD
tracked modified files
untracked files
ignored runtime files
whether implementation is uncommitted
```

If there are unexpected dirty files outside intended Stage03B scope, stop and report.

Expected possible intended files include only:

```text
avito-module/app/core_client.py
avito-module/app/storage.py
avito-module/app/schemas.py
avito-module/app/routers/exports.py
avito-module/tests/test_core_import.py
avito-module/tests/test_contract_no_core_write.py
reports/stage03b_parsed_avito_ads_to_core_import_report.md
logs/2026-07-01.md
.agents/received_prompts/TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_PROMPT_V2.md
.agents/received_prompts/TECHNOREBOOT_STAGE03B_RECOVERY_AND_CLOSURE_PROMPT.md
```

Potentially unexpected/scratch files:

```text
implementation_plan.md
task.md
walkthrough.md
avito-module/run_test.py
__pycache__/*
*.pyc
data/avito-module/*
```

Rules:

```text
- Do not commit implementation_plan.md, task.md, or walkthrough.md unless they are already tracked approved project docs.
- Do not commit avito-module/run_test.py.
- Do not commit __pycache__, *.pyc, data/avito-module runtime files.
- If these are untracked scratch files, leave them uncommitted and report them, or remove only exact untracked scratch files after logging why they are safe to remove.
```

Do not use `git clean`.

---

## Step 2 — Inspect Stage03B implementation

Read the changed files:

```powershell
git diff -- avito-module/app/core_client.py
git diff -- avito-module/app/storage.py
git diff -- avito-module/app/schemas.py
git diff -- avito-module/app/routers/exports.py
git diff -- avito-module/tests/test_core_import.py
git diff -- avito-module/tests/test_contract_no_core_write.py
```

Verify:

```text
core-import-preview still exists and does not call Core import.
POST /api/avito/parsed-ads/{ad_id}/core-import exists.
GET /api/avito/parsed-ads/{ad_id}/core-import-status exists.
Preview and import use same mapping.
Import calls Core through HTTP client only.
Idempotency exists: already_imported when force=false.
force=true allows retry/reimport.
Local import status stored only under data/avito-module.
No direct Core DB access from Avito module.
No browser automation/captcha bypass.
```

If implementation is incomplete, finish it with direct edits only.

Append checkpoint.

---

## Step 3 — Core import endpoint verification

Inspect Core product card import endpoint:

```powershell
Get-Content core\app\routers\product_cards.py
Get-ChildItem core -Recurse -File -Include *.py | Select-String -Pattern "import-json|ProductCardImport|product-cards" -CaseSensitive:$false
```

Verify the Avito module calls the existing Core endpoint through HTTP, not by importing Core internals.

If Core endpoint is already sufficient, do not modify Core.

If Core endpoint is missing/incomplete, implement only the minimal required Core endpoint and tests.

Append checkpoint.

---

## Step 4 — Safety scans

Run:

```powershell
git grep -n -I "technoreboot.db\|SessionLocal\|create_engine\|SELECT .* FROM products\|INSERT INTO products" -- avito-module

git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module

git status --ignored --short --untracked-files=all -- data/avito-module
```

Expected:

```text
No direct DB access from avito-module.
No browser automation/captcha bypass.
Runtime data ignored/uncommitted.
```

Append checkpoint.

---

## Step 5 — Run tests

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

If tests fail, fix only relevant Stage03B issues. Do not create scratch patch scripts.

Append checkpoint with exact results.

---

## Step 6 — Run smoke and endpoint checks

Run health checks:

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

Get parsed ad ID:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads | ConvertTo-Json -Depth 10
```

Then run, replacing `AD_ID`:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import-preview | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import -ContentType "application/json" -Body (@{ force = $false } | ConvertTo-Json) | ConvertTo-Json -Depth 10

Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import-status | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import -ContentType "application/json" -Body (@{ force = $false } | ConvertTo-Json) | ConvertTo-Json -Depth 10
```

Required:

```text
preview: PASS
import: PASS
import_status: PASS
repeat_import_without_force: already_imported
```

Append checkpoint.

---

## Step 7 — Runtime dirt cleanup without broad clean

After tests/smoke:

```powershell
git status --short --untracked-files=all
git status --ignored --short --untracked-files=all -- data/avito-module
```

Do not commit runtime data.

If untracked scratch files exist:

```text
implementation_plan.md
task.md
walkthrough.md
avito-module/run_test.py
__pycache__/*
*.pyc
```

Classify them.

If they are untracked scratch files created by the prior interrupted run, remove exact paths only after logging:

```powershell
Remove-Item implementation_plan.md -Force
Remove-Item task.md -Force
Remove-Item avito-module\run_test.py -Force
Remove-Item avito-module\__pycache__ -Recurse -Force
Remove-Item avito-module\tests\__pycache__ -Recurse -Force
```

Only run commands for paths that actually exist and are confirmed untracked scratch/runtime.

Do not delete user data.

Do not remove `data/avito-module` if ignored runtime state is useful; just do not commit it.

Append checkpoint.

---

## Step 8 — Create required Stage03B report

Create:

```text
reports/stage03b_parsed_avito_ads_to_core_import_report.md
```

Report must include:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_READY_FOR_AUDIT
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

IMPLEMENTATION:
- core_import_endpoint:
- avito_import_endpoint:
- avito_import_status_endpoint:
- preview_unchanged:
- idempotency_behavior:
- local_import_record_storage:
- direct_core_db_access_from_avito:
- browser_automation_or_captcha_bypass:

TESTS:
- core_pytest:
- avito_module_pytest:
- smoke_core_health:
- smoke_avito_health:
- sample_parse:
- preview:
- import:
- repeat_import_without_force:
- import_status:

LOGGING:
- execution_log:
- start_entry_created:
- checkpoints_written:
- final_entry_written:

SAFETY:
- runtime_data_committed:
- git_add_dot_used:
- direct_core_db_access_from_avito:
- live_avito_crawling:
- browser_automation:
- captcha_bypass:
- stage04_started:

FILES_CHANGED:
- ...

BLOCKERS:
- None

NEXT_STEP:
- Stage03B audit / acceptance. Do not start Stage04.
```

Append checkpoint.

---

## Step 9 — Final log entry before commit

Append final execution entry to:

```text
logs/2026-07-01.md
```

Must include:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_READY_FOR_AUDIT
branch
HEAD before commit
worktree clean before staging
files intended for commit
tests run and results
smoke checks results
blockers: None
next step: Stage03B audit / acceptance
```

---

## Step 10 — Stage exact files only

Run:

```powershell
git diff --name-status
git status --short --untracked-files=all
```

Stage exact intended files only.

Likely exact files:

```powershell
git add avito-module\app\core_client.py
git add avito-module\app\storage.py
git add avito-module\app\schemas.py
git add avito-module\app\routers\exports.py
git add avito-module\tests\test_core_import.py
git add avito-module\tests\test_contract_no_core_write.py
git add reports\stage03b_parsed_avito_ads_to_core_import_report.md
git add logs\2026-07-01.md
git add .agents\received_prompts\TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_PROMPT_V2.md
git add .agents\received_prompts\TECHNOREBOOT_STAGE03B_RECOVERY_AND_CLOSURE_PROMPT.md
```

Only stage files that exist and are intentional.

Do not stage:

```text
implementation_plan.md
task.md
walkthrough.md
avito-module/run_test.py
__pycache__
data/avito-module
*.db
*.sqlite
```

Verify staged files:

```powershell
git diff --cached --name-status
git diff --cached --check
git diff --cached --name-only
```

If staged files include forbidden runtime/scratch files, unstage exact file only with:

```powershell
git restore --staged <exact file>
```

Do not use broad restore.

Commit:

```powershell
git commit -m "Implement Stage 03B parsed Avito ads to Core import"
```

---

## Step 11 — Final verification

Run:

```powershell
git status --short --untracked-files=all
git log --oneline -5
git show --name-status --oneline --stat HEAD
```

Worktree may show ignored runtime files, but should have no tracked dirty source/report/log files.

If untracked scratch files remain, report them explicitly.

---

## Final response

Return exactly:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_READY_FOR_AUDIT
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

IMPLEMENTATION:
- core_import_endpoint:
- avito_import_endpoint:
- avito_import_status_endpoint:
- preview_unchanged:
- idempotency_behavior:
- local_import_record_storage:
- direct_core_db_access_from_avito:
- browser_automation_or_captcha_bypass:

TESTS:
- core_pytest:
- avito_module_pytest:
- smoke_core_health:
- smoke_avito_health:
- sample_parse:
- preview:
- import:
- repeat_import_without_force:
- import_status:

LOGGING:
- execution_log:
- start_entry_created:
- checkpoints_written:
- final_entry_written:

SAFETY:
- runtime_data_committed:
- git_add_dot_used:
- direct_core_db_access_from_avito:
- live_avito_crawling:
- browser_automation:
- captcha_bypass:
- stage04_started:

COMMIT:
- committed:
- commit_message:
- committed_files:
- forbidden_files_committed:

REPORT:
- reports/stage03b_parsed_avito_ads_to_core_import_report.md

BLOCKERS:
- None

NEXT_STEP:
- Stage03B audit / acceptance. Do not start Stage04.
```
