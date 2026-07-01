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

## Prompt search rule

At the beginning of every run, the agent must search for the current prompt in:

1. `C:\Users\Apc\Downloads`
2. `.agents\received_prompts`
3. project-local prompt/log locations, if any

If found in Downloads, copy it into `.agents\received_prompts\` before execution.

The execution log must record both the original prompt path and the copied prompt path.

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
