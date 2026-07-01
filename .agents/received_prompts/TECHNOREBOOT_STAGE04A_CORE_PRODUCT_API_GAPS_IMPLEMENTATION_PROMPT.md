# TECHNOREBOOT — Stage04A Core Product API Gaps Implementation Prompt

## Role

You are a senior backend developer and repository-safe implementation engineer.

## Project

```text
C:\tbootit
```

## Context

Stage04 planning has been completed and log closure verified.

Accepted planning closure status:

```text
TECHNOREBOOT_STAGE04_PLANNING_LOG_CLOSURE_COMMITTED_READY_FOR_STAGE04A_PROMPT
```

Current accepted HEAD:

```text
0e160d1
```

Planning commit:

```text
197ceec
```

Closure commit:

```text
0e160d1
```

Stage03B accepted status:

```text
TECHNOREBOOT_STAGE03B_ACCEPTED_READY_FOR_STAGE04_PLANNING
```

Stage03B accepted behavior:

```text
Avito parsed ads can be imported into Core through Core HTTP API.
Avito module does not access Core DB directly.
Core owns product DB writes.
```

Stage04 planning scope:

```text
Stage04A: Core product list/detail/status API gaps
Stage04B: Admin UI product list/detail MVP
Stage04C: sale/mark-sold flow
Stage04D: price tag print MVP
Stage04E: integration audit/acceptance
```

This prompt implements Stage04A only.

Do not start Stage04B, Stage04C, Stage04D, or Stage04E.

---

## Expected final status

If successful:

```text
TECHNOREBOOT_STAGE04A_CORE_PRODUCT_API_GAPS_READY_FOR_AUDIT
```

If blocked:

```text
TECHNOREBOOT_STAGE04A_CORE_PRODUCT_API_GAPS_BLOCKED
```

---

## Mandatory execution logging

Before doing anything else:

1. Read:

```text
.agents/AGENTS.md
```

2. Find this prompt in:

```text
C:\Users\Apc\Downloads
```

3. Copy it into:

```text
C:\tbootit\.agents\received_prompts\
```

4. Append a start entry to:

```text
logs/YYYY-MM-DD.md
```

Start entry must include:

```text
timestamp
prompt filename
prompt source path
copied prompt path
branch
HEAD
git status
task/stage
forbidden actions
```

Checkpoint after every major step.

Final log entry must include:

```text
FINAL_STATUS
branch
HEAD before commit
worktree clean before staging
committed files
tests run and results
blockers
next step
whether ready for audit
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
start Stage04B UI
start Stage04C mark-sold/sale flow
start Stage04D price tag printing
modify avito-module unless a test-only contract check is absolutely necessary
modify admin-shell
touch production
run external crawling
use browser automation
write directly to DB outside Core
commit runtime data
commit *.db / *.sqlite / __pycache__ / downloaded HTML
```

Allowed implementation scope:

```text
core/*
core tests
docs/report/logs
received prompt copy
```

---

## Stage04A goal

Implement/complete Core API gaps needed for product management MVP.

Core must expose stable API for:

```text
1. Product list
2. Product detail
3. Product update of safe editable fields
4. Product status update
5. Product status lifecycle validation
6. Product filters/search/sort basics
```

Stage04A must not implement:

```text
Admin UI screens
Mark-as-sold sale flow
Price tag printing
Bulk print
Accounting/invoice logic
External integrations
```

---

## Product status model

Use the statuses planned in Stage04:

```text
imported
in_stock
reserved
sold
written_off
archived
```

If existing project uses different current statuses, preserve backward compatibility and add a mapping or compatibility layer.

Recommended transitions for Stage04A:

```text
imported -> in_stock
imported -> archived
in_stock -> reserved
in_stock -> archived
reserved -> in_stock
reserved -> archived
sold -> archived
written_off -> archived
archived -> imported only if explicitly allowed by force/admin field
```

Stage04A should not implement full sale data capture. If status `sold` already exists, allow setting status only if the existing model supports it safely, but do not create sale_price/sold_at workflow unless already present. The mark-sold flow belongs to Stage04C.

---

## Core API target

Inspect current conventions first. Prefer existing endpoint style.

Required or equivalent endpoints:

```text
GET /api/products
GET /api/products/{product_id}
PATCH /api/products/{product_id}
POST /api/products/{product_id}/status
```

If current project uses `product-cards` naming, either:

```text
1. keep existing product-card endpoints and add compatibility aliases under /api/products, or
2. document that product-cards are the product API and add missing list/detail/update/status behavior there.
```

Do not break Stage03B import endpoint:

```text
POST /api/product-cards/import-json
```

---

## Safe editable fields

PATCH should allow only safe fields, for example:

```text
title
description
price
category
condition
internal_notes
status if already safe, otherwise use status endpoint
image metadata if current model supports it
```

Do not allow unsafe writes such as:

```text
id
created_at
source/import provenance fields unless explicitly designed
raw import blob deletion
```

Preserve Avito import traceability:

```text
source
source_url
external_id / parsed_ad_id
raw parsed fields
```

---

## Step 1 — Preflight

Run:

```powershell
cd C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -15
git show --name-status --oneline --stat HEAD

Test-Path reports\stage04_product_management_module_planning_report.md
Select-String -Path reports\stage04_product_management_module_planning_report.md -Pattern "TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_READY"

Test-Path reports\stage03b_audit_acceptance_report.md
Select-String -Path reports\stage03b_audit_acceptance_report.md -Pattern "TECHNOREBOOT_STAGE03B_ACCEPTED_READY_FOR_STAGE04_PLANNING"
```

If required reports are missing/uncommitted, stop:

```text
TECHNOREBOOT_STAGE04A_CORE_PRODUCT_API_GAPS_BLOCKED_MISSING_PRIOR_ACCEPTANCE
```

If worktree is dirty before starting, stop and report exact files.

Append checkpoint.

---

## Step 2 — Inspect current Core product model/API/tests

Read current Core code:

```powershell
Get-ChildItem core -Recurse -File -Include *.py | Select-Object FullName

Get-Content core\app\models.py
Get-ChildItem core\app\routers -Recurse -File -Include *.py | Select-Object FullName
Get-ChildItem core\tests -Recurse -File -Include *.py | Select-Object FullName
```

Search relevant symbols:

```powershell
Get-ChildItem -Path core -Recurse -File -Include *.py |
Select-String -Pattern "Product|product|ProductCard|product-card|import-json|status|price|category|condition|sold|archived" -CaseSensitive:$false
```

Identify:

```text
current product/product-card model
current schemas
current routers/endpoints
current DB/session pattern inside Core
current tests
current import-json behavior
```

Append checkpoint.

---

## Step 3 — Design minimal Stage04A implementation

Before editing, write a short implementation note into the execution log:

```text
chosen endpoint paths
model/schema changes needed
whether DB migration is needed
backward compatibility plan for Stage03B import-json
tests to add/modify
```

Do not create a separate `implementation_plan.md` at repo root.

Append checkpoint.

---

## Step 4 — Implement Core API gaps

Implement in Core only.

Expected capabilities:

### 4.1 Product list

Support:

```text
GET /api/products
```

Minimum query parameters:

```text
status
source
q
sort
limit
offset
```

Recommended response:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

### 4.2 Product detail

Support:

```text
GET /api/products/{product_id}
```

Return complete product/product-card data, including source/import provenance.

### 4.3 Product update

Support:

```text
PATCH /api/products/{product_id}
```

Allow safe editable fields only.

Validate:

```text
price >= 0 if present
title non-empty if present
status valid if included or route through status endpoint
unknown fields rejected
```

### 4.4 Product status update

Support:

```text
POST /api/products/{product_id}/status
```

Request example:

```json
{
  "status": "in_stock",
  "reason": "checked and ready"
}
```

Validate status and transition.

Return updated product.

### 4.5 Backward compatibility

Keep existing:

```text
POST /api/product-cards/import-json
```

working exactly as Stage03B expects.

If adding product aliases, tests must prove import-json still passes.

Append checkpoints after each implementation group.

---

## Step 5 — Tests

Add/extend Core tests for:

```text
1. GET /api/products returns list.
2. GET /api/products supports status filter.
3. GET /api/products supports source filter if source exists.
4. GET /api/products supports q search by title/source URL if fields exist.
5. GET /api/products/{id} returns detail.
6. PATCH /api/products/{id} updates safe fields.
7. PATCH rejects unknown/unsafe fields.
8. POST /api/products/{id}/status accepts valid transition.
9. POST /api/products/{id}/status rejects invalid status.
10. POST /api/products/{id}/status rejects invalid transition if transition validation implemented.
11. Stage03B import-json still works.
```

If current model does not support all fields, tests should reflect actual supported fields and document gaps in report.

Run:

```powershell
docker compose exec core pytest
```

Append checkpoint.

---

## Step 6 — Cross-service regression tests

Run:

```powershell
docker compose exec avito-module pytest
```

Required:

```text
Avito module tests still PASS
Stage03B import behavior still compatible
```

Append checkpoint.

---

## Step 7 — Smoke checks

Run:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/version | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/products | ConvertTo-Json -Depth 10
```

If there are products, test detail/update/status with a safe sample or create a test product through existing import-json endpoint using sample JSON.

Do not live crawl Avito.

Append checkpoint.

---

## Step 8 — Safety scans

Run:

```powershell
git diff --name-status

git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module

git status --ignored --short --untracked-files=all -- data/avito-module
```

Expected:

```text
No browser automation/captcha additions.
No avito-module DB direct access changes.
No runtime data staged/committed.
No admin UI implementation.
```

Append checkpoint.

---

## Step 9 — Create report

Create:

```text
reports/stage04a_core_product_api_gaps_report.md
```

Report must include:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE04A_CORE_PRODUCT_API_GAPS_READY_FOR_AUDIT
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

IMPLEMENTATION:
- product_list_endpoint:
- product_detail_endpoint:
- product_patch_endpoint:
- product_status_endpoint:
- status_lifecycle_validation:
- import_json_backward_compatible:
- admin_ui_started:
- mark_sold_started:
- price_tags_started:

TESTS:
- core_pytest:
- avito_module_pytest:
- product_list:
- product_filter_status:
- product_detail:
- product_patch_safe_fields:
- product_patch_rejects_unsafe:
- product_status_valid:
- product_status_invalid:
- import_json_regression:

SAFETY:
- runtime_data_committed:
- git_add_dot_used:
- browser_automation:
- captcha_bypass:
- avito_module_modified:
- admin_shell_modified:
- stage04b_started:
- stage04c_started:
- stage04d_started:

LOGGING:
- execution_log:
- checkpoints_present:
- final_entry_present:

FILES_CHANGED:
- ...

BLOCKERS:
- None

NEXT_STEP:
- Stage04A audit / acceptance. Do not start Stage04B.
```

Append checkpoint.

---

## Step 10 — Final log entry before commit

Append final execution entry to `logs/YYYY-MM-DD.md`:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE04A_CORE_PRODUCT_API_GAPS_READY_FOR_AUDIT
branch
HEAD before commit
worktree clean before staging
files intended for commit
tests run and results
blockers
next step
audit/acceptance ready true
```

---

## Step 11 — Stage exact files only

Run:

```powershell
git diff --name-status
git status --short --untracked-files=all
```

Stage exact changed files only.

Likely examples:

```powershell
git add core\app\<exact_changed_file>.py
git add core\app\routers\<exact_changed_file>.py
git add core\tests\<exact_changed_test_file>.py
git add reports\stage04a_core_product_api_gaps_report.md
git add logs\YYYY-MM-DD.md
git add .agents\received_prompts\TECHNOREBOOT_STAGE04A_CORE_PRODUCT_API_GAPS_IMPLEMENTATION_PROMPT.md
```

Do not stage:

```text
admin-shell/*
avito-module/*
data/*
*.db
*.sqlite
__pycache__
task.md
implementation_plan.md
walkthrough.md
```

unless a file is intentionally modified and allowed by this prompt. In normal Stage04A, admin-shell and avito-module should not be staged.

Verify:

```powershell
git diff --cached --name-status
git diff --cached --check
```

Commit:

```powershell
git commit -m "Implement Stage 04A Core product API gaps"
```

---

## Step 12 — Final verification

Run:

```powershell
git status --short --untracked-files=all
git log --oneline -5
git show --name-status --oneline --stat HEAD
```

Worktree must be clean except ignored runtime data.

---

## Final response

Return exactly:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE04A_CORE_PRODUCT_API_GAPS_READY_FOR_AUDIT
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

IMPLEMENTATION:
- product_list_endpoint:
- product_detail_endpoint:
- product_patch_endpoint:
- product_status_endpoint:
- status_lifecycle_validation:
- import_json_backward_compatible:
- admin_ui_started:
- mark_sold_started:
- price_tags_started:

TESTS:
- core_pytest:
- avito_module_pytest:
- product_list:
- product_filter_status:
- product_detail:
- product_patch_safe_fields:
- product_patch_rejects_unsafe:
- product_status_valid:
- product_status_invalid:
- import_json_regression:

SAFETY:
- runtime_data_committed:
- git_add_dot_used:
- browser_automation:
- captcha_bypass:
- avito_module_modified:
- admin_shell_modified:
- stage04b_started:
- stage04c_started:
- stage04d_started:

LOGGING:
- execution_log:
- checkpoints_present:
- final_entry_present:

COMMIT:
- committed:
- commit_message:
- committed_files:
- forbidden_files_committed:

REPORT:
- reports/stage04a_core_product_api_gaps_report.md

BLOCKERS:
- None

NEXT_STEP:
- Stage04A audit / acceptance. Do not start Stage04B automatically.
```
