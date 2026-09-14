# TECHNOREBOOT — Stage 09A-R3 LOCAL
## Real end-to-end Avito deactivation proof — NO DRY-RUN

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**LOCAL URL:** `https://localhost:8443`  
**Production VDS:** `https://144.31.50.134`  
**Stage:** `Stage 09A-R3 LOCAL — Real Avito Deactivation E2E`

# 0. OWNER DECISION — CRITICAL

For final LOCAL acceptance of this feature, Dry-Run is NOT sufficient.

Owner explicitly authorizes a real destructive test against the current Avito listing used in Sale #1:

```text
Sale ID: 1
Product: AMD Athlon X4 950 AM4. Гарантия
Avito ID: 7353766377
```

The Owner accepts that this listing may actually be removed/deactivated from publication and can be reactivated manually later if needed.

The stage must prove the complete real workflow:

```text
LOCAL sale detail
↓
[Снять с Avito]
↓
task queued
↓
Chrome Extension fetches task
↓
opens exact Avito listing
↓
verifies exact Avito ID
↓
reaches management/deactivation control
↓
performs REAL deactivation
↓
handles confirmation/reason if needed
↓
waits for confirmed inactive state
↓
reports success
↓
server task becomes success
↓
linked listing state becomes inactive/archived
```

NO DRY-RUN for the final test.

STRICTLY LOCAL application environment.
Do NOT deploy code to VDS.
Do NOT modify VDS code or business DB/media.

---

# 1. PROMPT PRESERVATION

Copy unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE09A_R3_LOCAL_REAL_AVITO_DEACTIVATION_E2E_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE09A_R3_LOCAL_REAL_AVITO_DEACTIVATION_E2E_PROMPT.md`

---

# 2. PREFLIGHT

Record:

```text
LOCAL_HEAD:
LOCAL_GIT_STATUS:
LOCAL_STACK_HEALTHY:
EXTENSION_VERSION:
LOCAL_PAIRING_STATUS:
SALE_ID:
AVITO_ID:
TASK_ID:
TASK_STATUS_BEFORE:
LISTING_STATUS_BEFORE:
```

Verify:
- LOCAL sentinel exists;
- VDS production sentinel is absent locally;
- no VDS operation job is running;
- extension version is current;
- exact task/listing relation is correct.

Do not touch VDS.

---

# 3. DRY-RUN MUST BE DISABLED FOR THIS EXACT TEST

The test must explicitly arm real execution.

Preferred safe scope:

```text
REAL mode enabled only for this approved task / Avito ID 7353766377
```

If current extension only has a global toggle, that is acceptable for this test, but:

- show clearly that Armed mode is active;
- immediately return to Dry-Run after the test completes;
- do not auto-process unrelated pending tasks while globally Armed.

Before arming:
- ensure there is only one eligible queued deactivation task;
- ensure its Avito ID is exactly `7353766377`.

---

# 4. PERMANENT SALE DETAIL BUTTON

Verify Sale #1 page contains:

```text
[ Снять с Avito ]
```

This button must remain permanently available on the sale detail page.

If task is currently:
- `suggested`
- `failed`
- `manual_required`

reuse/requeue the same idempotent task.

If already `queued`, do not create a duplicate.

Required:

```text
DUPLICATE_TASK_CREATED = false
```

---

# 5. REAL EXTENSION EXECUTION

The Chrome Extension must perform the actual real browser flow.

Required sequence:

1. Fetch queued task.
2. Validate:
   ```text
   action == deactivate_listing
   hostname == avito.ru or *.avito.ru
   avito_listing_id == 7353766377
   listing_url belongs to same ID
   ```
3. Open/focus exact listing.
4. Verify page identity.
5. Reach owner-management UI for that exact listing.
6. Locate deactivation/removal control.
7. If submenu exists, open exact menu.
8. If confirmation dialog exists, verify semantics.
9. If Avito asks a reason:
   - choose a deterministic valid "sold/removed from sale" reason only if clearly available;
   - do not select unrelated reasons.
10. Perform final destructive click.
11. Wait for real confirmation that listing is no longer active.
12. Report success.

No coordinate clicks.
No approximate title search.
No unrelated listing.
No payment/promotion/publication action.

---

# 6. SUCCESS CONFIRMATION — MUST BE EXTERNAL AND REAL

A real `success` requires proof from Avito.

Acceptable confirmation:

```text
listing status visibly inactive/archived
OR
Avito displays successful removal message
OR
owner-management page shows republish/reactivate action
OR
the active listing disappears from active listings and is present in archived/inactive
```

Do NOT mark success just because:
- click occurred;
- modal closed;
- navigation completed.

Required:

```text
REAL_EXTERNAL_INACTIVE_CONFIRMED = true
```

---

# 7. SERVER-SIDE POST-CONDITIONS

After external confirmation:

Task:

```text
status = success
finished_at != null
last_error = null
execution_mode = extension
```

Canonical linked listing:

```text
remote_status = inactive/archived/removed
```

according to existing canonical status vocabulary.

Write audit event:

```text
avito_listing_deactivated_after_sale
```

with:
- sale_id;
- product_id;
- Avito ID;
- timestamp;
- execution mode.

---

# 8. BUSINESS INTEGRITY

The Avito action must NOT:

- delete Product;
- alter sale completion;
- restore/decrement stock again;
- create a duplicate sale;
- alter sale price/payment;
- touch unrelated products/listings.

Verify after real deactivation:

```text
SALE #1 still completed
PRODUCT still exists
PHYSICAL STOCK unchanged by this Avito action
OTHER AVITO LISTINGS unchanged
```

---

# 9. FAILURE HANDLING

If real deactivation fails at any stage:

- record actual safe error;
- do not fake success;
- preserve task for retry/manual_required;
- capture the exact Avito UI text/selector/context that failed;
- leave the browser at useful diagnostic state where safe.

Do NOT fall back to success.

---

# 10. REACTIVATION IS NOT PART OF THIS STAGE

Do NOT automatically republish/reactivate the listing after the test.

Owner has stated they can reactivate it manually later if desired.

Therefore:

```text
AUTO_REACTIVATION = false
```

No new publication feature is required in this stage.

---

# 11. EXTENSION STATE AFTER TEST

After successful real deactivation:

- restore previous browser tab/focus if possible;
- close temporary task tab if safe;
- return extension to Dry-Run mode;
- clear active-task lock/storage;
- leave no unrelated queued task accidentally armed.

Required:

```text
DRY_RUN_RESTORED_AFTER_TEST = true
ACTIVE_TASK_CLEARED = true
```

---

# 12. LOCAL UI VERIFICATION

After success verify:

## Sale detail
`https://localhost:8443/sales/1`

Should show an honest state such as:

```text
Объявление уже снято с Avito
```

and must not create a new duplicate deactivation task on repeated click.

## Post-sale queue
`https://localhost:8443/avito/post-sale`

Should show:

```text
Sale #1
Avito 7353766377
Status: Снято / success
```

---

# 13. TESTS

Run existing Stage09A tests and add/adjust coverage for Armed mode:

## Armed path
- approved exact task can execute final click;
- wrong task ID blocks;
- wrong domain blocks;
- unrelated pending task cannot be auto-executed while one-task arming is active.

## Success confirmation
- final click without external confirmation -> NOT success;
- confirmed inactive -> success.

## Post-conditions
- listing status updates;
- audit event written;
- sale unchanged;
- stock unchanged.

## Cleanup
- Dry-Run restored;
- active task cleared.

Required:

```text
FAILED = 0
```

---

# 14. REAL LIVE BROWSER PROOF — MANDATORY

This stage is not complete until the real external Avito action is performed.

Mandatory proof:

```text
SALE_ID = 1
AVITO_ID = 7353766377
REAL_FINAL_CLICK_PERFORMED = true
REAL_EXTERNAL_INACTIVE_CONFIRMED = true
SERVER_TASK_STATUS = success
LISTING_REMOTE_STATUS = inactive/archived/removed
FALSE_SUCCESS = false
```

Capture:
- exact Avito control text used;
- exact confirmation text/state observed;
- final external state;
- task ID;
- timestamps.

Screenshots/log descriptions are acceptable in the report, but do not store private session data.

---

# 15. VDS SAFETY

Strictly:

```text
VDS_DEPLOYED = false
VDS_CODE_MODIFIED = false
VDS_DATA_MODIFIED = false
UPDATE_VDS_RUN = false
```

Do not use production deployment.

---

# 16. GIT

If code changes are required to make the real test pass:
- commit locally;
- do not deploy VDS;
- report push status honestly.

Final worktree should be clean.

---

# 17. FINAL REPORT CONTRACT

Return:

```text
# Stage 09A-R3 LOCAL — Real Avito Deactivation E2E

## Environment
LOCAL_ONLY: true
VDS_DEPLOYED: false
VDS_DATA_MODIFIED: false

## Target
SALE_ID: 1
PRODUCT:
AVITO_ID: 7353766377
TASK_ID:
TASK_STATUS_BEFORE:
LISTING_STATUS_BEFORE:

## Arming
DRY_RUN_DISABLED_FOR_TEST:
ONE_TASK_ONLY:
UNRELATED_TASKS_BLOCKED:

## Real Browser Execution
TASK_FETCHED:
RECEIVED_ACTION:
EXACT_URL_OPENED:
EXACT_ID_VERIFIED:
OWNER_MANAGEMENT_CONTEXT_REACHED:
DEACTIVATION_CONTROL_TEXT:
CONFIRMATION_DIALOG_HANDLED:
FINAL_CLICK_PERFORMED: true
REAL_EXTERNAL_INACTIVE_CONFIRMED: true
EXTERNAL_CONFIRMATION_TEXT_OR_STATE:

## Server Result
TASK_STATUS_AFTER: success
LISTING_REMOTE_STATUS_AFTER:
AUDIT_EVENT_WRITTEN:
LAST_ERROR_EMPTY:
FALSE_SUCCESS: false

## Business Integrity
SALE_STILL_COMPLETED:
PRODUCT_STILL_EXISTS:
PHYSICAL_STOCK_CHANGED_BY_AVITO_ACTION: false
OTHER_LISTINGS_CHANGED: false
DUPLICATE_TASK_CREATED: false

## Extension Cleanup
DRY_RUN_RESTORED_AFTER_TEST: true
ACTIVE_TASK_CLEARED: true
TEMP_TAB_CLOSED_OR_SAFE:
PREVIOUS_TAB_FOCUS_RESTORED_OR_SAFE:

## UI
SALE_DETAIL_SHOWS_ALREADY_REMOVED:
POST_SALE_QUEUE_SHOWS_SUCCESS:

## Tests
FAILED:

## VDS Safety
VDS_DEPLOYED: false
VDS_CODE_MODIFIED: false
VDS_DATA_MODIFIED: false
UPDATE_VDS_RUN: false

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE09A_R3_LOCAL_REAL_AVITO_DEACTIVATION_E2E_PROVEN

REAL_DEACTIVATION_PROVEN: true
AUTO_REACTIVATION: false
DO_NOT_DEPLOY_TO_VDS_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- real final click was not performed;
- external inactive state was not confirmed;
- server reports success without Avito confirmation;
- wrong listing was touched;
- sale/stock changed unexpectedly;
- VDS was modified;
- tests fail.

---

# 18. STOP

After the real deactivation is confirmed end-to-end:

STOP.

Wait for Owner acceptance.

Do not deploy to VDS.
