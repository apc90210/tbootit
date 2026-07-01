# TECHNOREBOOT — Stage 04 Planning: Core Product Management Module Prompt

## Role

You are a senior product architect, backend/frontend planner, and repository governance engineer.

## Project

```text
C:\tbootit
```

## Context

Stage03B has been accepted.

Accepted final status:

```text
TECHNOREBOOT_STAGE03B_ACCEPTED_READY_FOR_STAGE04_PLANNING
```

Accepted Stage03B audit commit:

```text
c400b37
```

Stage03B confirmed:

```text
Core import endpoint: PASS
Avito preview endpoint: PASS
Avito import endpoint: PASS
Avito import status endpoint: PASS
Idempotency: PASS
Runtime data committed: NO
Avito direct Core DB access: NONE
Avito Core internal imports: NONE
Avito Core API only: YES
Browser automation/captcha bypass: NONE
Stage04 started: NO
Core pytest: 28 passed
Avito module pytest: 12 passed
```

Current project direction from owner:

```text
1. Stage03A: separate Avito parser module — done.
2. Stage03B: parsed Avito ads are imported into Core through Core API — accepted.
3. Next: module for working with the product database:
   - see products in Core;
   - manage products;
   - mark/sell products;
   - prepare printable price tags.
```

Important architecture rule:

```text
The product management module must not access the DB directly.
It must work through Core API only.
```

This prompt is planning only.

Do not implement Stage04 in this prompt.

---

## Expected final status

If planning is complete:

```text
TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_READY
```

If blocked:

```text
TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_BLOCKED
```

---

## Mandatory execution logging

Before doing anything else, read:

```text
.agents/AGENTS.md
```

Find this prompt in:

```text
C:\Users\Apc\Downloads
```

Copy it into:

```text
C:\tbootit\.agents\received_prompts\
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
HEAD
worktree clean true/false
files changed
blockers
next step
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
implement Stage04
modify Core runtime behavior
modify Avito module runtime behavior
create production code for product management
create DB migrations unless only documenting planned migration needs
touch production
run external crawling
use browser automation
write directly to DB from non-Core modules
commit runtime data
```

This prompt may only create/update planning docs, reports, and execution log.

---

## Stage04 planning scope

Plan a Product Management Module MVP.

The module must allow the owner/operator to work with products already imported into Core.

Planning must cover:

```text
1. Product list screen
2. Product detail screen
3. Product status lifecycle
4. Product editing boundaries
5. Sale/mark-as-sold flow
6. Price tag / label printing flow
7. Core API endpoints needed
8. UI pages/components needed
9. Data model gaps
10. Safety and audit logging
11. Tests required
12. Stage04 implementation breakdown
```

---

## Product management MVP requirements

The plan should define how to support these workflows:

### 1. View products

User must be able to:

```text
open product list
filter by status/source/category
search by title/serial/source URL
sort by created/imported/updated/price
open product details
see Avito source trace if imported from Avito
```

### 2. Edit product card

User must be able to edit safe fields through Core API:

```text
title
description
price
category
condition
internal notes
status
images metadata if already stored
```

Do not plan direct DB editing from UI module.

### 3. Product status lifecycle

Define statuses, for example:

```text
draft/imported
in_stock
reserved
sold
written_off
archived
```

Plan exact transitions and blockers.

### 4. Sell / mark as sold

MVP sale flow may be simple:

```text
select product
mark as sold
record sold_at
record sale_price
optional buyer/contact/comment
product no longer appears as in_stock
```

Do not plan accounting/invoicing complexity unless as future work.

### 5. Price tag / label printing

Plan printable price tags:

```text
single product price tag
bulk selected products price tags
print-friendly HTML page
fields:
  title
  price
  short specs/condition
  internal SKU/product ID
  barcode/QR optional as future
```

MVP can use browser print from HTML.

No external paid print services.

### 6. Core API only

All operations must go through Core API:

```text
GET /api/products
GET /api/products/{id}
PATCH /api/products/{id}
POST /api/products/{id}/mark-sold
POST /api/products/{id}/status
POST /api/price-tags/preview
```

Endpoint names may be adjusted to current project conventions after inspection.

---

## Step 1 — Preflight

Run:

```powershell
cd C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -15
git show --name-status --oneline --stat HEAD

Test-Path reports\stage03b_audit_acceptance_report.md
Select-String -Path reports\stage03b_audit_acceptance_report.md -Pattern "TECHNOREBOOT_STAGE03B_ACCEPTED_READY_FOR_STAGE04_PLANNING"
```

If Stage03B acceptance report is missing/uncommitted, stop:

```text
TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_BLOCKED_STAGE03B_NOT_ACCEPTED
```

If worktree is dirty before planning, stop and report exact files.

Append checkpoint.

---

## Step 2 — Inspect current Core/Admin architecture

Read current code and docs:

```powershell
Get-ChildItem -Path core,admin-shell,avito-module,docs,reports -Recurse -File -Include *.py,*.html,*.js,*.md |
Select-String -Pattern "product|Product|card|status|sold|price|print|label|tag|admin|import-json|avito" -CaseSensitive:$false
```

Inspect relevant files fully as needed:

```powershell
Get-ChildItem core -Recurse -File -Include *.py
Get-ChildItem admin-shell -Recurse -File
Get-ChildItem docs -Recurse -File -Include *.md
```

Identify:

```text
Current Core product model/schema
Current Core product endpoints
Current Admin UI pages
Current import endpoint behavior
Current test structure
Current Docker service boundaries
```

Append checkpoint.

---

## Step 3 — Create Stage04 planning document

Create:

```text
docs/stage04_product_management_module_plan.md
```

The plan must contain:

```text
# Stage04 Product Management Module Plan

## 1. Goal

## 2. Non-goals

## 3. Current baseline after Stage03B

## 4. Architecture decision
- product management UI/module uses Core API only
- Core owns DB writes
- no direct DB access outside Core

## 5. Product lifecycle/status model

## 6. Required Core API endpoints

## 7. Required UI screens/components

## 8. Product editing rules

## 9. Sale / mark-as-sold flow

## 10. Price tag printing flow

## 11. Data model gaps

## 12. Security/safety constraints

## 13. Logging/audit events

## 14. Test plan

## 15. Implementation stages
- Stage04A: Core product list/detail/status API gaps
- Stage04B: Admin UI product list/detail MVP
- Stage04C: sale/mark-sold flow
- Stage04D: price tag print MVP
- Stage04E: integration audit/acceptance

## 16. Acceptance criteria

## 17. Risks/blockers
```

Do not implement any code.

Append checkpoint.

---

## Step 4 — Create Stage04 API/UI checklist

Create:

```text
docs/stage04_product_management_api_ui_checklist.md
```

Include a concise checklist:

```text
Core APIs
Admin UI
Tests
Safety scans
Reports
Acceptance gates
```

Append checkpoint.

---

## Step 5 — Create planning report

Create:

```text
reports/stage04_product_management_module_planning_report.md
```

Report must include:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_READY
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

PLANNING:
- docs_created:
- implementation_started:
- core_code_modified:
- admin_code_modified:
- avito_code_modified:
- direct_db_access_allowed:
- core_api_only_confirmed:

SCOPE:
- product_list:
- product_detail:
- edit_product:
- status_lifecycle:
- mark_sold:
- price_tags:
- audit_logging:
- tests_planned:

NEXT_STAGE_BREAKDOWN:
- Stage04A:
- Stage04B:
- Stage04C:
- Stage04D:
- Stage04E:

BLOCKERS:
- ...

NEXT_STEP:
- Owner review of Stage04 plan, then Stage04A implementation prompt.
```

Append checkpoint.

---

## Step 6 — Validate planning-only diff

Run:

```powershell
git diff --name-status
git status --short --untracked-files=all
```

Allowed changed files only:

```text
docs/stage04_product_management_module_plan.md
docs/stage04_product_management_api_ui_checklist.md
reports/stage04_product_management_module_planning_report.md
logs/YYYY-MM-DD.md
.agents/received_prompts/TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_PROMPT.md
```

Forbidden changed files:

```text
core/*
admin-shell/*
avito-module/*
data/*
*.db
*.sqlite
__pycache__/*
```

If forbidden changed files exist, stop:

```text
TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_BLOCKED_SCOPE_VIOLATION
```

Append checkpoint.

---

## Step 7 — Commit exact planning files only

Stage exact files only:

```powershell
git add docs\stage04_product_management_module_plan.md
git add docs\stage04_product_management_api_ui_checklist.md
git add reports\stage04_product_management_module_planning_report.md
git add logs\YYYY-MM-DD.md
git add .agents\received_prompts\TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_PROMPT.md
```

Use the real date log path.

Do not use `git add .`.

Verify:

```powershell
git diff --cached --name-status
git diff --cached --check
```

Commit:

```powershell
git commit -m "Plan Stage 04 product management module"
```

Append final log entry after commit.

---

## Final response

Return exactly:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_READY
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

PLANNING:
- docs_created:
- implementation_started:
- core_code_modified:
- admin_code_modified:
- avito_code_modified:
- direct_db_access_allowed:
- core_api_only_confirmed:

SCOPE:
- product_list:
- product_detail:
- edit_product:
- status_lifecycle:
- mark_sold:
- price_tags:
- audit_logging:
- tests_planned:

NEXT_STAGE_BREAKDOWN:
- Stage04A:
- Stage04B:
- Stage04C:
- Stage04D:
- Stage04E:

LOGGING:
- execution_log:
- checkpoints_present:
- final_entry_present:

REPORT:
- reports/stage04_product_management_module_planning_report.md

BLOCKERS:
- None

NEXT_STEP:
- Owner review of Stage04 plan, then Stage04A implementation prompt. Do not start Stage04A automatically.
```
