# TECHNOREBOOT — Stage 03B Parsed Avito Ads to Core Import Prompt V2

## Role

You are a senior backend developer and integration engineer.

Your task is to implement Stage 03B safely, with strict module boundaries and mandatory resumable execution logging.

---

## Project

```text
C:\tbootit
```

Current accepted state:

```text
Stage 03A Avito Parser Module MVP: accepted
Stage 03A Audit Closure Diff Validation: accepted with git add dot caveat
Agent execution logging rules: accepted

Latest governance status:
TECHNOREBOOT_AGENT_EXECUTION_LOGGING_RULES_PATCH_READY

Latest governance commit:
ba11410 Add mandatory agent execution logging rules
```

Stage03B must follow `.agents/AGENTS.md`.

---

## Mandatory execution logging

Before any implementation work:

1. Read:

```text
.agents/AGENTS.md
```

2. Create or append:

```text
logs/YYYY-MM-DD.md
```

3. Add a start entry containing:

```text
timestamp
prompt filename
prompt source path
copied prompt path under .agents/received_prompts
branch
HEAD
git status
task/stage
forbidden actions
```

4. After every major step, append a checkpoint:

```text
timestamp
step name
commands run
files read
files changed
tests/checks run
result: PASS / FAIL / BLOCKED / IN_PROGRESS
next intended action
```

5. If interrupted, the next agent must be able to continue from the last checkpoint.

6. Do not rely only on final `reports/`. The `logs/` file is the resumable execution journal.

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

Do not continue if the prompt cannot be found/copied.

---

## Stage 03B Goal

Implement controlled import of parsed Avito ads into Core through Core API.

Stage03B must convert a parsed Avito ad into Core `ProductCardImport` JSON and send it to the Core import endpoint.

Expected final status:

```text
TECHNOREBOOT_STAGE03B_PARSED_AVITO_ADS_TO_CORE_IMPORT_READY_FOR_AUDIT
```

Do not start Stage04.

---

## Current accepted architecture

Core service:

```text
http://127.0.0.1:8000
```

Avito module service:

```text
http://127.0.0.1:8020
```

Accepted Stage03A facts:

```text
Core pytest: PASS
Avito module pytest: PASS
Core health: PASS
Avito health: PASS
Sample parse: PASS

Avito module:
- separate service
- no direct Core DB access
- no direct SQLite/ORM access to technoreboot.db
- parsed ads stored under data/avito-module
- data/avito-module must remain ignored/uncommitted
- no Selenium/Playwright/browser automation/captcha bypass
```

User requirement:

```text
After Avito parsing, parsed ads must be added to the Core database through Core API only.
The Avito module must never write directly to Core DB.
```

---

## Critical boundaries

Allowed:

```text
Avito module may call Core HTTP API.
Avito module may keep its own local runtime metadata under data/avito-module.
Avito module may provide preview before import.
Avito module may import one selected parsed ad to Core by ID.
Avito module may record local import result/status under data/avito-module.
Core may expose/keep an import endpoint for product-card JSON.
Tests may use sample:// data and local Docker services.
```

Forbidden:

```text
Avito module direct DB writes
Avito module direct DB reads from Core DB
Import by touching technoreboot.db
Import by using Core ORM/session classes from Avito module
Import by importing Core Python internals instead of HTTP API
Live Avito crawling in tests
Browser automation
Selenium
Playwright
Captcha bypass
Autologin
Production external calls
Commit runtime files from data/avito-module
Commit *.db / *.sqlite / __pycache__ / downloaded HTML
Stage04 or future work
```

---

## Hard Git Rules

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

Stage exact files only.

If a command produces dirty runtime data, do not commit it.

---

## Step 1 — Preflight and logging checkpoint

Run:

```powershell
cd C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10
git show --name-status --oneline --stat HEAD

Test-Path reports\stage03a_audit_closure_diff_validation_report.md
Select-String -Path reports\stage03a_audit_closure_diff_validation_report.md -Pattern "TECHNOREBOOT_STAGE03A_AUDIT_ACCEPTED_WITH_GIT_ADD_DOT_CAVEAT_READY_FOR_STAGE03B"

Test-Path reports\agent_execution_logging_rules_patch_report.md
Select-String -Path reports\agent_execution_logging_rules_patch_report.md -Pattern "TECHNOREBOOT_AGENT_EXECUTION_LOGGING_RULES_PATCH_READY"
```

Verify the closure reports are committed:

```powershell
git ls-files reports/stage03a_audit_closure_diff_validation_report.md
git log --oneline -- reports/stage03a_audit_closure_diff_validation_report.md

git ls-files reports/agent_execution_logging_rules_patch_report.md
git log --oneline -- reports/agent_execution_logging_rules_patch_report.md
```

If Stage03A closure or logging rules report is missing/uncommitted, stop:

```text
TECHNOREBOOT_STAGE03B_BLOCKED_REQUIRED_GOVERNANCE_REPORT_MISSING
```

If worktree is dirty before starting, stop and report exact files.

Append checkpoint to log:

```text
CHECKPOINT: preflight
RESULT: PASS / FAIL / BLOCKED
```

---

## Step 2 — Inspect current API contracts

Inspect Core and Avito module code:

```powershell
Get-ChildItem -Path core,admin-shell,avito-module -Recurse -File -Include *.py,*.html,*.js,*.md,requirements.txt |
Select-String -Pattern "product-card|ProductCard|import-json|parsed-ads|core-import-preview|avito" -CaseSensitive:$false
```

Identify and log:

```text
Core import endpoint path
Expected ProductCardImport schema
Avito parsed ad storage format
Existing parsed ad endpoints
Existing preview endpoint
Existing tests
```

Append checkpoint:

```text
CHECKPOINT: API contract inspection
```

---

## Step 3 — Required Stage03B behavior

### 3.1 Import preview must remain available

Existing preview endpoint must keep working:

```text
POST /api/avito/parsed-ads/{ad_id}/core-import-preview
```

It must:

```text
convert parsed Avito ad to Core ProductCardImport JSON
not call Core import endpoint
not write Core DB
return preview JSON
```

### 3.2 Add real import endpoint

Add:

```text
POST /api/avito/parsed-ads/{ad_id}/core-import
```

It must:

```text
1. Load parsed ad by ad_id from Avito module local storage.
2. Convert parsed ad to ProductCardImport JSON using the same mapping as preview.
3. Call Core HTTP API import endpoint.
4. Return Core response plus local import metadata.
5. Store local import result/status in Avito module runtime storage under data/avito-module.
6. Be idempotent:
   - repeated import of same parsed ad should not create uncontrolled duplicates;
   - if already imported and force=false, return already_imported;
   - force=true allows retry/reimport.
```

Suggested request body:

```json
{
  "force": false
}
```

### 3.3 Add import status endpoint

Add:

```text
GET /api/avito/parsed-ads/{ad_id}/core-import-status
```

It must return:

```text
not_imported / imported / failed
last_attempt_at
core_response summary
error if failed
```

### 3.4 Optional list enrichment

If safe, enrich:

```text
GET /api/avito/parsed-ads
```

with import status per parsed ad.

Do not break existing fields.

Append checkpoints after each endpoint/mapping change.

---

## Step 4 — Core API constraints

Use Core API only.

If Core already has import endpoint:

```text
Use existing endpoint.
Do not create duplicate endpoint unless necessary.
```

If Core import endpoint does not exist or is incomplete, add a minimal Core endpoint with tests:

```text
POST /api/product-cards/import-json
```

It must:

```text
accept ProductCardImport JSON
validate fields
create/update product card in Core DB through Core service's own normal DB layer
return stable response with product/card ID
support idempotency if possible using source fields:
  source="avito"
  external_id or source_url or parsed_ad_id
```

Important:

```text
Only Core service may write Core DB.
Avito module must call this through HTTP.
```

Append checkpoint:

```text
CHECKPOINT: Core API import contract
```

---

## Step 5 — Mapping rules

Use deterministic mapping from parsed Avito ad to Core product card.

At minimum include:

```text
source: avito
source_url
external_id or parsed_ad_id
title
price
currency if available
description if available
images if available
seller/profile info if available
raw parsed fields for traceability
created/imported timestamp
```

Do not invent unknown values as facts. Use null/empty where unknown.

Keep mapping in a dedicated function/module so preview and import use the same mapping.

Append checkpoint:

```text
CHECKPOINT: mapping implemented
```

---

## Step 6 — Tests

Add/extend tests for:

```text
1. Preview still does not call Core import.
2. Import endpoint calls Core HTTP API.
3. Import uses ProductCardImport JSON generated by same mapper as preview.
4. Already-imported ad returns already_imported when force=false.
5. force=true allows retry/reimport.
6. Import status endpoint returns correct state.
7. Avito module has no direct Core DB access.
8. No Selenium/Playwright/browser/captcha dependencies.
9. data/avito-module runtime files are not committed.
10. Existing Stage03A parser tests still pass.
```

Use mocks where appropriate for HTTP Core import call.

Append checkpoint after test implementation and after every test run.

---

## Step 7 — Commands to run

Run local tests:

```powershell
docker compose ps

docker compose exec core pytest
docker compose exec avito-module pytest
```

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

Then get parsed ads and test preview/import/status:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads | ConvertTo-Json -Depth 10

# Replace AD_ID with a real parsed ad id from previous response:
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import-preview | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import -ContentType "application/json" -Body (@{ force = $false } | ConvertTo-Json) | ConvertTo-Json -Depth 10

Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import-status | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8020/api/avito/parsed-ads/AD_ID/core-import -ContentType "application/json" -Body (@{ force = $false } | ConvertTo-Json) | ConvertTo-Json -Depth 10
```

Expected second import with `force=false`:

```text
already_imported
```

Append checkpoints for each group.

---

## Step 8 — Safety scans

Run:

```powershell
git grep -n -I "technoreboot.db\|SessionLocal\|create_engine\|SELECT .* FROM products\|INSERT INTO products" -- avito-module

git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module

git status --ignored --short --untracked-files=all -- data/avito-module
git diff --name-status
```

Allowed in Avito module:

```text
HTTP client calls to Core API
ProductCardImport mapping code
local runtime import metadata under data/avito-module, uncommitted/ignored
```

Forbidden:

```text
Avito module importing Core DB/session modules
Avito module direct DB path access
Browser automation dependencies
Runtime data staged/committed
```

Append checkpoint:

```text
CHECKPOINT: safety scans
```

---

## Step 9 — Documentation/report

Create:

```text
reports/stage03b_parsed_avito_ads_to_core_import_report.md
```

Include:

```text
FINAL_STATUS:
PROJECT:
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

FILES_CHANGED:
- ...

BLOCKERS:
- ...

NEXT_STEP:
- Stage03B audit / acceptance.
```

Append checkpoint:

```text
CHECKPOINT: report created
```

---

## Step 10 — Commit exact files only

Before staging:

```powershell
git diff --name-status
git status --short --untracked-files=all
```

Do not stage runtime data.

Do not use `git add .`.

Stage exact changed source/test/report/log files only, for example:

```powershell
git add avito-module/app/<exact_changed_file>.py
git add avito-module/tests/<exact_changed_test_file>.py
git add core/<exact_changed_file_if_needed>.py
git add core/<exact_changed_test_file_if_needed>.py
git add reports/stage03b_parsed_avito_ads_to_core_import_report.md
git add logs/YYYY-MM-DD.md
```

Then verify staged files:

```powershell
git diff --cached --name-status
git diff --cached --check
```

Commit:

```powershell
git commit -m "Implement Stage 03B parsed Avito ads to Core import"
```

Append final log entry after commit.

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

REPORT:
- reports/stage03b_parsed_avito_ads_to_core_import_report.md

BLOCKERS:
- None

NEXT_STEP:
- Stage03B audit / acceptance. Do not start Stage04.
```
