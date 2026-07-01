# TECHNOREBOOT — Stage04 Planning Closure Log Verification Prompt

## Role

You are a senior repository auditor and governance reviewer.

## Project

```text
C:\tbootit
```

## Context

Stage04 planning reported:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_READY
```

Reported commit:

```text
HEAD:
197ceec
```

Reported changed files:

```text
docs/stage04_product_management_module_plan.md
docs/stage04_product_management_api_ui_checklist.md
reports/stage04_product_management_module_planning_report.md
logs/2026-07-01.md
.agents/received_prompts/TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_PROMPT.md
```

Reported result:

```text
WORKTREE_CLEAN: true
implementation_started: no
core_code_modified: no
admin_code_modified: no
avito_code_modified: no
Stage04A not started
```

Process caveat to verify:

The transcript shows the final log entry was appended after `git commit`:

```powershell
git commit -m "Plan Stage 04 product management module"
Add-Content -Path logs\2026-07-01.md -Value $finalLog
git status --porcelain
```

If the final log entry was appended after the commit, then `logs/2026-07-01.md` may be dirty and the final log entry may not be committed.

This prompt verifies and, if needed, commits only the missing final log entry.

Do not start Stage04A.

---

## Expected final status

If everything is already clean and committed:

```text
TECHNOREBOOT_STAGE04_PLANNING_ACCEPTED_READY_FOR_STAGE04A_PROMPT
```

If only the final log entry is dirty and safely committed by this prompt:

```text
TECHNOREBOOT_STAGE04_PLANNING_LOG_CLOSURE_COMMITTED_READY_FOR_STAGE04A_PROMPT
```

If unexpected dirty files exist:

```text
TECHNOREBOOT_STAGE04_PLANNING_CLOSURE_BLOCKED_UNEXPECTED_DIRTY_FILES
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
start Stage04A
modify Core code
modify Admin code
modify Avito code
modify product implementation
touch runtime data
commit data/*
commit *.db or *.sqlite
```

This is closure verification only.

---

## Mandatory execution logging

Read:

```text
.agents/AGENTS.md
```

Append a checkpoint to:

```text
logs/YYYY-MM-DD.md
```

Only if the log is already dirty with the missing final entry, commit that exact log file.

---

## Step 1 — Preflight

Run:

```powershell
cd C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10
git show --name-status --oneline --stat HEAD
```

Required latest planning commit should be:

```text
Plan Stage 04 product management module
```

If latest commit is not Stage04 planning, inspect:

```powershell
git log --oneline -- docs/stage04_product_management_module_plan.md
git log --oneline -- reports/stage04_product_management_module_planning_report.md
```

---

## Step 2 — Verify planning files are committed

Run:

```powershell
git ls-files docs/stage04_product_management_module_plan.md
git ls-files docs/stage04_product_management_api_ui_checklist.md
git ls-files reports/stage04_product_management_module_planning_report.md
git ls-files .agents/received_prompts/TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_PROMPT.md

Select-String -Path reports\stage04_product_management_module_planning_report.md -Pattern "TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_READY"
```

Expected:

```text
All files tracked.
Planning report contains final status.
```

If missing, stop:

```text
TECHNOREBOOT_STAGE04_PLANNING_CLOSURE_BLOCKED_REQUIRED_FILE_MISSING
```

---

## Step 3 — Verify final log entry

Run:

```powershell
Select-String -Path logs\2026-07-01.md -Pattern "TECHNOREBOOT_STAGE04_PRODUCT_MANAGEMENT_MODULE_PLANNING_READY"
git diff --name-status
git diff -- logs\2026-07-01.md
```

Classify:

```text
final_log_entry_present:
log_dirty:
dirty_files:
```

Allowed dirty file:

```text
logs/2026-07-01.md
```

Allowed dirty content only:

```text
Final Stage04 planning closure entry/checkpoint written after commit.
```

If any other dirty file exists, stop:

```text
TECHNOREBOOT_STAGE04_PLANNING_CLOSURE_BLOCKED_UNEXPECTED_DIRTY_FILES
```

---

## Step 4 — If log is dirty, commit exact log file only

If and only if `logs/2026-07-01.md` is the only dirty file and the diff is the missing final closure entry:

```powershell
git add logs\2026-07-01.md
git diff --cached --name-status
git diff --cached --check
git commit -m "Close Stage 04 planning execution log"
```

Do not use `git add .`.

If there is nothing to commit, do not create an empty commit.

---

## Step 5 — Final verification

Run:

```powershell
git status --short --untracked-files=all
git log --oneline -5
git show --name-status --oneline --stat HEAD
```

Required:

```text
worktree clean
planning files committed
final log entry committed or already clean
Stage04A not started
```

---

## Final response

Return exactly one of the final statuses.

If already clean:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE04_PLANNING_ACCEPTED_READY_FOR_STAGE04A_PROMPT
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

CLOSURE:
- planning_commit:
- planning_files_committed:
- final_log_entry_present:
- final_log_entry_committed:
- extra_closure_commit_created:
- unexpected_dirty_files:

SCOPE:
- implementation_started:
- core_code_modified:
- admin_code_modified:
- avito_code_modified:
- stage04a_started:

REPORT:
- reports/stage04_product_management_module_planning_report.md

BLOCKERS:
- None

NEXT_STEP:
- Prepare Stage04A implementation prompt only after owner approval.
```

If closure commit was created:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE04_PLANNING_LOG_CLOSURE_COMMITTED_READY_FOR_STAGE04A_PROMPT
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

CLOSURE:
- planning_commit:
- closure_commit:
- planning_files_committed:
- final_log_entry_present:
- final_log_entry_committed:
- extra_closure_commit_created:
- unexpected_dirty_files:

SCOPE:
- implementation_started:
- core_code_modified:
- admin_code_modified:
- avito_code_modified:
- stage04a_started:

REPORT:
- reports/stage04_product_management_module_planning_report.md

BLOCKERS:
- None

NEXT_STEP:
- Prepare Stage04A implementation prompt only after owner approval.
```
