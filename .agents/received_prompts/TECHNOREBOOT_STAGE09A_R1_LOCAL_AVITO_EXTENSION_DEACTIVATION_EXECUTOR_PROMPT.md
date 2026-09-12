# TECHNOREBOOT — Stage 09A-R1 LOCAL
## Complete the real Chrome Extension executor for Avito post-sale deactivation

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**LOCAL URL:** `https://localhost:8443`  
**Production VDS:** `https://144.31.50.134`  
**Stage:** `Stage 09A-R1 LOCAL — Avito Extension Deactivation Executor`

# 0. WHY THIS REVISION EXISTS

Stage09A LOCAL successfully implemented:
- post-sale suggestion/task model;
- queue UI;
- idempotency;
- RBAC;
- retry/manual_required states;
- extension task-channel API;
- Chrome Extension v0.2.57 packaging;
- Schema Guard migration block;
- LOCAL-only operation.

However the report does NOT prove that the Chrome Extension actually executes the Avito deactivation flow.

The report explicitly states:
- `service_worker.js` added task-channel helpers:
  `fetch_next_task`, `report_task_success`, `report_task_failed`;
- `popup.html`, `popup.js`, `content.js` were only updated for version strings;
- `EXTENSION_TASK_FETCH_WORKS: true`;
- dry-run/mock result works.

That proves transport, not real browser execution.

This revision must implement and prove the missing executor:

```text
queued task
↓
extension receives task
↓
opens exact Avito listing/manage page
↓
verifies exact Avito ID
↓
finds ONLY the deactivate/remove/archive control
↓
executes safely when explicitly allowed
↓
confirms resulting inactive state
↓
reports success
```

LOCAL ONLY.
Do NOT deploy to VDS.

---

# 1. PROMPT PRESERVATION

Copy unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE09A_R1_LOCAL_AVITO_EXTENSION_DEACTIVATION_EXECUTOR_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE09A_R1_LOCAL_AVITO_EXTENSION_DEACTIVATION_EXECUTOR_PROMPT.md`

---

# 2. PREFLIGHT

Record:

```text
LOCAL_HEAD:
LOCAL_GIT_STATUS:
LOCAL_STACK_HEALTHY:
EXTENSION_VERSION:
LOCAL_PAIRING_STATUS:
CURRENT_TASK_CHANNEL_STATUS:
```

Verify:
- LOCAL sentinel exists;
- no VDS operation is invoked;
- `requires_manual_migration=true` remains set;
- current Stage09A task model remains intact.

---

# 3. INSPECT THE CURRENT EXTENSION BEFORE EDITING

Audit:

```text
chrome-extension/technoreboot-avito/service_worker.js
chrome-extension/technoreboot-avito/content.js
chrome-extension/technoreboot-avito/popup.js
chrome-extension/technoreboot-avito/manifest.json
```

Answer in report:

```text
CURRENT_TASK_POLLING_IMPLEMENTED:
CURRENT_DEACTIVATION_EXECUTOR_IMPLEMENTED:
CURRENT_DEACTIVATION_SELECTOR_LOGIC:
CURRENT_SUCCESS_CONFIRMATION_LOGIC:
```

Do not claim executor exists merely because `/tasks/next` can be fetched.

---

# 4. REQUIRED EXECUTOR ARCHITECTURE

Implement a real extension-side task executor.

Preferred flow:

```text
service worker
  -> fetch next queued task
  -> validate action == deactivate_listing
  -> validate URL/Avito ID
  -> open/focus exact listing management page
  -> hand task to content script
  -> content script validates current page/listing ID
  -> discover deactivation control
  -> execute only safe action
  -> verify post-action state
  -> report success/failure/manual_required
```

No generic remote command execution.

---

# 5. TASK POLLING

Implement bounded polling in the extension.

Requirements:
- polling runs only when extension is paired;
- reasonable interval, e.g. 5–15 seconds;
- no tight loops;
- one task at a time;
- do not process a second task while one is active;
- recover safely after browser restart/service-worker suspension;
- do not lose task ID.

Persist minimal active-task state in `chrome.storage.local`.

---

# 6. EXACT TARGET VALIDATION

Before opening/clicking anything:

Validate server-side AND extension-side:

```text
hostname is avito.ru or *.avito.ru
task.action == deactivate_listing
task.avito_listing_id is non-empty
task.listing_url contains/resolves to same listing ID
current page listing ID == task.avito_listing_id
```

If mismatch:

```text
manual_required / failed
```

Never continue.

---

# 7. NAVIGATION

The extension must navigate to the exact listing-management context.

Use the most reliable available Avito URL derived from the canonical listing relation.

If direct management URL cannot be reliably constructed:
- open exact listing page;
- navigate through the listing's own management control only;
- never search by title and click the first result;
- never use approximate matching.

---

# 8. DEACTIVATION CONTROL DISCOVERY

Implement robust but conservative DOM discovery.

Recognize only controls semantically corresponding to:

```text
Снять с публикации
Снять объявление
Деактивировать
Архивировать
Убрать с публикации
```

Avito wording may vary.

Use:
- visible text;
- ARIA labels;
- data-marker attributes if stable;
- exact local DOM context for current listing.

Reject controls related to:

```text
Опубликовать
Продать быстрее
Продвигать
Поднять
Оплатить
Купить услугу
Редактировать
Удалить аккаунт
```

Do not use screen-coordinate clicks.

Do not click ambiguous controls.

If more than one plausible destructive control remains:

```text
manual_required
```

---

# 9. CONFIRMATION DIALOG HANDLING

If Avito displays a confirmation modal:

- verify it still refers to the same listing/task;
- accept only a confirmation for deactivation/removal from publication;
- never accept payment/promotion/publication dialogs.

If reason selection is required:
- choose only a safe deterministic reason approved by current business semantics;
- if Avito requires a reason that cannot be safely inferred, use `manual_required`;
- do not invent sale reason mappings without evidence.

---

# 10. SUCCESS CONFIRMATION — MANDATORY

Never report `success` immediately after click.

Require at least one reliable confirmation:

```text
listing status visibly becomes inactive/archived
OR
deactivation success message appears
OR
management controls change from active to republish/reactivate state
OR
page/API state confirms listing is no longer active
```

Then report:

```text
POST /tasks/{id}/success
```

If confirmation does not appear before timeout:

```text
POST /tasks/{id}/failed
```

with safe error.

No fake success.

---

# 11. DRY-RUN MODE FOR OWNER ACCEPTANCE

Because we must not deactivate a real production listing accidentally, implement LOCAL development dry-run support.

Dry-run behavior:

```text
task fetched
exact listing page opened
listing ID verified
deactivation control found
NO FINAL CLICK
result shown in extension:
"Готово к снятию: кнопка найдена"
```

Server task must NOT be marked `success`.

Use a local-only flag such as:

```text
avito_deactivation_dry_run = true
```

stored in extension/local dev configuration.

Dry-run must never exist as a production bypass that falsely reports success.

---

# 12. REAL ACTION ARMING

Actual destructive click must require one of:

- explicit task created by seller/Owner via post-sale `Снять с Avito`;
AND
- extension dry-run disabled;
AND
- exact ID validation passed.

Do not create a global "auto deactivate everything" behavior.

---

# 13. POPUP / STATUS UX

Extension popup should show current task state when relevant:

```text
Задача: снять объявление Avito №...
Статус:
- получена
- открываю объявление
- проверяю ID
- кнопка найдена
- снятие выполнено
- подтверждение получено
```

For dry-run:

```text
ТЕСТОВЫЙ РЕЖИМ
Финальное снятие не выполняется.
```

For failure:
show safe reason.

---

# 14. VERSION

Because extension behavior changes:

```text
0.2.57 -> 0.2.58
```

Update all version references and rebuild ZIP.

Required package:

```text
technoreboot-avito-extension-0.2.58.zip
```

LOCAL only.

---

# 15. TASK STATE SAFETY

Preserve Stage09A task semantics.

Extension flow:

```text
queued
-> processing
-> success
```

or:

```text
queued
-> processing
-> failed/manual_required
```

Do not let extension:
- create arbitrary tasks;
- change sale;
- change stock;
- delete product.

---

# 16. REAL BROWSER LOCAL PROOF — SAFE

Perform a LOCAL browser-assisted proof with dry-run enabled.

Required:

1. Pair extension to `https://localhost:8443`.
2. Create/use a LOCAL post-sale task linked to an existing Avito listing.
3. Press `Снять с Avito` in LOCAL sale UI.
4. Verify task becomes queued.
5. Extension fetches task automatically.
6. Extension opens/focuses exact Avito listing.
7. Extension verifies exact Avito ID.
8. Extension finds the actual deactivation control.
9. Dry-run prevents final click.
10. Extension reports locally:
   `ready / control found`, NOT `success`.
11. No real Avito listing changes.

If real Avito DOM cannot expose the control without entering a management menu, it may navigate up to the final confirmation boundary, but MUST stop before destructive confirmation.

Document exact observed Avito UI text/selector.

---

# 17. OPTIONAL REAL DEACTIVATION TEST

Do NOT perform by default.

Only if Owner explicitly provides/approves a disposable active Avito listing:

- disable dry-run for that one task;
- execute actual deactivation;
- confirm external inactive state;
- verify server task becomes `success`;
- verify listing status updates;
- verify product/sale/stock remain correct.

Without Owner approval:

```text
REAL_EXTERNAL_DEACTIVATION_TEST = NOT_RUN_BY_DESIGN
```

This is acceptable for Stage09A-R1 local acceptance.

---

# 18. TESTS

Add focused tests for:

## Polling
- unpaired -> no polling execution;
- paired -> next task fetched;
- active task lock prevents concurrency.

## Navigation
- exact ID opens;
- invalid domain rejected;
- mismatched ID rejected.

## DOM executor
- one exact deactivate control -> eligible;
- ambiguous controls -> manual_required;
- publish/payment controls ignored;
- unrelated listing controls ignored.

## Confirmation
- click without confirmation -> no success;
- confirmed inactive -> success;
- timeout -> failed.

## Dry-run
- finds control;
- does not click;
- does not report success.

## Restart/recovery
- active task state survives worker restart safely.

Required:

```text
FAILED = 0
```

Run existing extension regressions too.

---

# 19. LOCAL MANUAL OWNER CHECK

At the end provide browser-only instructions:

1. Download/install extension v0.2.58 from LOCAL.
2. Pair extension to LOCAL.
3. Open a LOCAL sale with an active linked Avito listing.
4. Press `Снять с Avito`.
5. Observe extension automatically receive task.
6. Confirm it opens the exact Avito listing.
7. Confirm popup shows exact same Avito ID.
8. Confirm `ТЕСТОВЫЙ РЕЖИМ`.
9. Confirm extension identifies deactivation control but DOES NOT click it.
10. Confirm task is not falsely marked success.
11. Confirm `/avito/post-sale` reflects safe pending/manual test state.

No CLI for Owner.

---

# 20. VDS SAFETY

Strictly:

```text
VDS_DEPLOYED = false
VDS_DATA_MODIFIED = false
REAL_PRODUCTION_LISTING_DEACTIVATED = false
```

Do not use UPDATE VDS.
Do not run production migration.

---

# 21. GIT

Commit LOCAL work.

Do not push if current LOCAL-acceptance workflow keeps unaccepted changes local.

Report:

```text
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:
```

Do not deploy.

---

# 22. FINAL REPORT CONTRACT

Return:

```text
# Stage 09A-R1 LOCAL — Real Extension Deactivation Executor

## Baseline
EXTENSION_VERSION_BEFORE:
TASK_CHANNEL_ALREADY_WORKED:
REAL_EXECUTOR_BEFORE:

## Executor
TASK_POLLING_IMPLEMENTED:
ONE_TASK_AT_A_TIME:
ACTIVE_TASK_PERSISTED:
EXACT_URL_VALIDATION:
EXACT_ID_VALIDATION:
MANAGEMENT_NAVIGATION:
DEACTIVATION_CONTROL_DISCOVERY:
AMBIGUOUS_CONTROL_SAFE_FAIL:
PAYMENT_PUBLISH_CONTROLS_IGNORED:
CONFIRMATION_REQUIRED_FOR_SUCCESS:

## Dry Run
DRY_RUN_IMPLEMENTED:
FINAL_CLICK_BLOCKED_IN_DRY_RUN:
FALSE_SUCCESS_BLOCKED:
REAL_AVITO_MUTATION_DURING_TEST: false

## Extension
EXTENSION_VERSION_AFTER: 0.2.58
ZIP_REBUILT:
LOCAL_PAIRING_WORKS:

## Local Browser Proof
TASK_AUTO_FETCHED:
EXACT_LISTING_OPENED:
LISTING_ID_MATCHED:
DEACTIVATION_CONTROL_FOUND:
OBSERVED_CONTROL_TEXT:
FINAL_CLICK_PERFORMED: false
TASK_FALSE_SUCCESS: false

## Optional Real Test
REAL_EXTERNAL_DEACTIVATION_TEST:
OWNER_DISPOSABLE_LISTING_APPROVED:

## Tests
FAILED:

## VDS Safety
VDS_DEPLOYED: false
VDS_DATA_MODIFIED: false
REAL_PRODUCTION_LISTING_DEACTIVATED: false

## Schema Guard
REQUIRES_MANUAL_MIGRATION: true
DATABASE_CHANGE: true

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE09A_R1_LOCAL_REAL_EXTENSION_EXECUTOR_READY_FOR_OWNER_ACCEPTANCE

DO_NOT_DEPLOY_TO_VDS_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- task transport exists but browser executor is still absent;
- extension can report success without real confirmation;
- dry-run can perform destructive click;
- exact listing ID is not verified;
- VDS is touched;
- tests fail.

---

# 23. STOP

After implementation + safe LOCAL browser proof:

STOP.

Wait for Owner acceptance.
