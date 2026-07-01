# TECHNOREBOOT — Agent Execution Logging Rules Patch Prompt

## Role

You are a senior repository governance engineer.

## Project

```text
C:\tbootit
```

## Problem

Current agent prompts produce final reports under `reports/`, but this is not enough.

If an agent run is interrupted, the next agent must be able to continue from the exact last safe point.

Therefore the project needs mandatory append-only execution logs for every agent run.

---

## Goal

Patch `.agents` project rules so every future agent must maintain a durable execution log.

Expected final status:

```text
TECHNOREBOOT_AGENT_EXECUTION_LOGGING_RULES_PATCH_READY
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

Do not modify application source code.

Do not start Stage03B or any product stage in this prompt.

This is governance-only.

---

## Step 1 — Inspect current agent rules

Run:

```powershell
cd C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10

Get-ChildItem .agents -Recurse -File | Select-Object FullName
Get-Content .agents\AGENTS.md
```

Also inspect any rules files related to prompts/logging:

```powershell
Get-ChildItem .agents -Recurse -File -Include *.md |
Select-String -Pattern "log|logging|journal|checkpoint|continue|interrupted|received_prompts|prompt" -CaseSensitive:$false
```

---

## Step 2 — Add mandatory execution logging rule

Patch the relevant `.agents` rule file, preferably:

```text
.agents/AGENTS.md
```

If the project has a better dedicated rules file, use that instead, but document it.

Add a section like this:

```markdown
## Mandatory execution logging

Every agent run must maintain an append-only execution log.

### Log location

Use:

`logs/YYYY-MM-DD.md`

If the date log does not exist, create it.

### Start entry

At the beginning of every run, before source edits, append:

- timestamp
- prompt filename
- prompt source path
- current branch
- current HEAD
- worktree status
- intended task/stage
- forbidden actions relevant to the task

### Checkpoint entries

After every major step, append a short checkpoint:

- timestamp
- what was done
- commands run, summarized
- files read
- files created/edited
- tests/checks run
- result: PASS / FAIL / BLOCKED / IN_PROGRESS
- next intended action

Major steps include:

- preflight
- architecture inspection
- implementation start
- each endpoint/API change
- each test run
- every blocker
- every restore/cleanup action
- before commit
- after commit
- final verification

### Interruption recovery

The log must be sufficient for the next agent to continue.

If interrupted, the next agent must:

1. read the latest `logs/YYYY-MM-DD.md`;
2. find the last checkpoint for the active prompt/stage;
3. verify branch, HEAD, and worktree;
4. continue from the last safe unfinished step;
5. never assume final success if final status is missing.

### Final entry

At the end of every run, append:

- FINAL_STATUS
- branch
- HEAD
- worktree clean true/false
- committed files
- tests run and results
- blockers
- next step
- whether the current stage is ready for audit/acceptance

### Logging discipline

- Logs are append-only.
- Do not rewrite older log entries.
- Do not delete logs.
- Do not replace detailed logs with only final reports.
- `reports/` are for final summaries; `logs/` are for resumable execution history.
```

---

## Step 3 — Add/patch prompt search rule if needed

Ensure `.agents` also states:

```markdown
## Prompt search rule

At the beginning of every run, the agent must search for the current prompt in:

1. `C:\Users\Apc\Downloads`
2. `.agents\received_prompts`
3. project-local prompt/log locations, if any

If found in Downloads, copy it into `.agents\received_prompts\` before execution.

The execution log must record both the original prompt path and the copied prompt path.
```

Do not duplicate if this already exists. If it exists, only add the missing logging connection.

---

## Step 4 — Add continuation rule

Add:

```markdown
## Continuation after interruption

If the previous agent stopped without a final status, the next agent must treat the stage as incomplete.

The next agent must not restart blindly.

The next agent must:

- inspect the latest log;
- inspect `git status`;
- inspect changed files;
- inspect last successful checkpoint;
- continue from the last safe checkpoint;
- avoid repeating destructive operations;
- preserve uncommitted user/agent work unless explicitly proven safe.
```

---

## Step 5 — Create report

Create:

```text
reports/agent_execution_logging_rules_patch_report.md
```

Include:

```text
FINAL_STATUS:
PROJECT:
BRANCH:
HEAD:
WORKTREE_CLEAN:

PATCH:
- files_changed:
- mandatory_execution_logging_added:
- prompt_search_logging_added:
- interruption_continuation_rule_added:
- append_only_log_policy_added:

VALIDATION:
- .agents rules readable:
- logs directory exists or will be created:
- no app source modified:
- no product stage started:

NEXT_STEP:
- Future stage prompts must rely on logs/YYYY-MM-DD.md as resumable execution journal.
```

---

## Step 6 — Commit exact files only

Stage exact files only.

Example:

```powershell
git add .agents\AGENTS.md
git add reports\agent_execution_logging_rules_patch_report.md
git diff --cached --name-status
git diff --cached --check
git commit -m "Add mandatory agent execution logging rules"
```

Do not use `git add .`.

---

## Final response

Return exactly:

```text
FINAL_STATUS: TECHNOREBOOT_AGENT_EXECUTION_LOGGING_RULES_PATCH_READY
PROJECT: C:\tbootit
BRANCH:
HEAD:
WORKTREE_CLEAN:

PATCH:
- files_changed:
- mandatory_execution_logging_added:
- prompt_search_logging_added:
- interruption_continuation_rule_added:
- append_only_log_policy_added:

VALIDATION:
- app_source_modified:
- product_stage_started:
- git_add_dot_used:
- report_created:

REPORT:
- reports/agent_execution_logging_rules_patch_report.md

NEXT_STEP:
- Re-run/continue Stage03B only after this logging rule is accepted.
```
