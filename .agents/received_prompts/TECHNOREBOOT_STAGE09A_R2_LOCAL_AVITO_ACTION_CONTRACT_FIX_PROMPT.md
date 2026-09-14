# TECHNOREBOOT — Stage 09A-R2 LOCAL
## Fix Avito post-sale task action contract mismatch (`deactivate` vs `deactivate_listing`)

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**LOCAL URL:** `https://localhost:8443`  
**Production VDS:** `https://144.31.50.134`  
**Stage:** `Stage 09A-R2 LOCAL — Avito Task Action Contract Fix`

# 0. OBSERVED REAL OWNER FAILURE

Owner performed the real LOCAL browser workflow.

The task was created and reached the post-sale queue, but ended as:

```text
Avito ID: 7353766377
Status: manual_required
Attempts: 1 / 3
Error: Unsupported action: deactivate
```

This proves:
- sale hook works;
- task creation works;
- queue UI works;
- extension task polling/transport works far enough to reject the task;
- the current failure is a contract mismatch between backend task action and Chrome Extension executor.

Likely mismatch:

```text
DB/business action: deactivate
Extension executor expects: deactivate_listing
```

This stage must fix ONLY that contract mismatch and re-run the exact LOCAL workflow.

STRICTLY LOCAL ONLY.
Do NOT deploy to VDS.

# 1. PROMPT PRESERVATION

Copy unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE09A_R2_LOCAL_AVITO_ACTION_CONTRACT_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE09A_R2_LOCAL_AVITO_ACTION_CONTRACT_FIX_PROMPT.md`

# 2. PREFLIGHT

Record:

```text
LOCAL_HEAD:
LOCAL_GIT_STATUS:
LOCAL_STACK_HEALTHY:
EXTENSION_VERSION:
CURRENT_DB_ACTION_VALUE_FOR_TASK_1:
CURRENT_EXTENSION_EXPECTED_ACTION:
CURRENT_EXTENSION_BRIDGE_PAYLOAD_ACTION:
```

Inspect the actual task row that produced:

```text
Unsupported action: deactivate
```

Do not guess.

# 3. ROOT-CAUSE AUDIT

Inspect at minimum:

```text
core/app/models.py
core/app/routers/avito_post_sale.py
avito-module/app/routers/extension_bridge.py
chrome-extension/technoreboot-avito/service_worker.js
chrome-extension/technoreboot-avito/content.js
tests/test_avito_post_sale_deactivation.py
```

Trace the action string end-to-end:

```text
task creation
-> DB persisted action
-> Core API response
-> Avito module bridge
-> extension /tasks/next payload
-> service worker action dispatch
```

Report exactly where:

```text
deactivate
```

is emitted and where:

```text
deactivate_listing
```

is required.

# 4. CANONICAL CONTRACT DECISION

Do NOT create another schema migration solely to rename this task action unless truly required.

Preferred fix:

```text
Internal persisted business action:
deactivate

Transport/executor action:
deactivate_listing
```

Add an explicit adapter/serializer at the extension bridge boundary.

Example:

```text
DB action = deactivate
        ↓
extension bridge maps
        ↓
payload.action = deactivate_listing
```

This preserves the existing DB schema/default/idempotency model.

Define constants rather than scattering raw strings.

Suggested:

```text
BUSINESS_ACTION_DEACTIVATE = "deactivate"
EXTENSION_ACTION_DEACTIVATE_LISTING = "deactivate_listing"
```

If code architecture makes a single canonical string safer, explain why before changing DB/defaults.

# 5. BACKWARD COMPATIBILITY

Existing LOCAL tasks already persisted with:

```text
action = deactivate
```

must work after the fix.

Do not require deleting/recreating all pending tasks.

Task #1 / existing manual_required task must be retryable after reset/requeue according to normal state rules.

Do not edit production VDS data.

# 6. EXTENSION SAFETY

Keep all Stage09A-R1 protections unchanged:

- exact Avito domain validation;
- exact Avito listing ID validation;
- one task at a time;
- dry-run ON by default;
- no final destructive click in dry-run;
- no success without real external confirmation;
- publish/payment/edit controls ignored;
- ambiguous control -> manual_required.

Do not weaken the executor simply to make this task pass.


# 6A. SALE DETAIL PAGE — PERMANENT "СНЯТЬ С AVITO" BUTTON

Owner requirement:

When opening ANY already completed/existing sale in the sales section, the sale detail page currently contains controls such as:

```text
[ Товарный чек ]
[ Вернуться к продажам / Все продажи ]
```

Add another permanent action:

```text
[ Снять с Avito ]
```

Required behavior:

- the button must be visible on the sale detail page at any later time, not only immediately after sale completion;
- it must remain available even if the seller previously pressed `Не сейчас`;
- it must allow the user to re-open/retry Avito removal from an old sale;
- for multi-item sales it must operate on all eligible linked active Avito listings from that sale;
- if there is exactly one eligible listing, queue/requeue that listing;
- if there are several, show a confirmation listing the eligible products/Avito IDs and allow one-click queueing for all;
- if there is already an existing `suggested`, `failed`, or `manual_required` task, reuse/requeue the existing idempotent task instead of creating a duplicate;
- if the listing is already confirmed inactive/success, clicking the button must show an honest informational result such as:
  `Объявление уже снято с Avito`;
- if the sale has no Avito-linked product, the button may remain visible but must return:
  `Для этой продажи нет связанных объявлений Avito`;
- the button must never disappear merely because the immediate post-sale modal was dismissed.

RBAC:
- normal seller USER may use this button for a sale;
- USER does not gain Avito account administration rights;
- OWNER may use it.

Do not change the completed sale status when this button is used.

# 6B. DIRECT BROWSER NAVIGATION — MAKE THE AVITO ACTION ACTUALLY WORK

Owner requirement:

Do not stop at task transport.

Use the already logged-in Chrome/Avito browser session and follow the exact Avito link from the task.

Required preferred flow:

```text
Sale detail -> [Снять с Avito]
↓
task queued
↓
Chrome Extension receives exact Avito URL + ID
↓
extension opens a temporary Avito tab for that exact URL
↓
verifies current page contains the same listing ID
↓
finds the listing-owner management controls
↓
opens the exact management/deactivation UI for that listing
↓
deactivates/removes it from publication in Armed mode
↓
waits for confirmed inactive state
↓
reports success
↓
returns focus to the previous tab and may close the temporary Avito tab
```

Implementation guidance:

1. Prefer direct navigation to the exact canonical `listing_url` already stored for the product.
2. If the public listing page itself does not expose owner controls:
   - find the listing's own management/edit/menu control on that exact page;
   - navigate from that listing to its management context;
   - never search by title and click an approximate result.
3. If Avito uses a profile/listings page for owner actions:
   - navigate there only after retaining the exact target Avito ID;
   - locate the row/card whose listing ID exactly equals the task ID;
   - only then open its menu and deactivate.
4. The extension may create a temporary tab and operate there.
5. For reliability, it may make that tab active while executing.
6. After confirmed success:
   - restore focus to the previously active Technoreboot tab if known;
   - close the temporary Avito task tab if safe.
7. In Dry-Run mode:
   - navigate all the way to the exact final deactivation control;
   - highlight/identify it;
   - STOP before the destructive click;
   - leave enough UI visible for Owner inspection;
   - do not report success.
8. In Armed mode:
   - perform the final click only after exact ID validation and exact control validation;
   - handle the deactivation confirmation dialog;
   - require visible confirmed inactive state before reporting success.

The target is not merely "open Avito".
The target is:

```text
open exact linked listing
-> reach its own management/deactivation control
-> perform real deactivation in Armed mode
-> confirm the listing is no longer active
```

Do not claim `BROWSER_ASSISTED_AVAILABLE=true` unless this complete route exists in code.


# 7. VERSION

If only backend/bridge task serialization changes and extension source does not need modification:

```text
keep extension v0.2.58
```

Do not bump version unnecessarily.

If extension source must change:
- bump to `0.2.59`;
- update all references;
- rebuild ZIP;
- run extension regression.

Report which path was taken.

# 8. TESTS — REQUIRED CONTRACT COVERAGE

Add regression tests proving:

## Persisted task
```text
task.action == "deactivate"
```

may remain valid internally.

## Extension bridge payload
For that task:

```text
payload.action == "deactivate_listing"
```

## Executor
`deactivate_listing` is accepted.

## No unsupported-action regression
A normal post-sale task must never fail with:

```text
Unsupported action: deactivate
```

## Unknown actions
Truly unknown actions must still be rejected.

Example:

```text
delete_account
publish_listing
pay_promotion
```

must not be normalized into deactivation.

Required:

```text
FAILED = 0
```

# 9. RE-RUN THE REAL LOCAL OWNER SCENARIO

Using the existing LOCAL task/listing if safe:

```text
Sale #1
Product: AMD Athlon X4 950 AM4. Гарантия
Avito ID: 7353766377
```

Do not create another sale unnecessarily.

Preferred:

1. Use the existing `Повторить` action for the task.
2. Task becomes queued.
3. Extension automatically fetches it.
4. Confirm received action is:
   ```text
   deactivate_listing
   ```
5. Confirm no `Unsupported action` error.
6. Extension opens/focuses exact Avito listing:
   ```text
   7353766377
   ```
7. Exact listing ID validation passes.
8. In dry-run, extension searches for the deactivation control.
9. Final destructive click remains blocked.
10. Task must NOT falsely become success.

If the actual Avito DOM cannot find the control:
- report the actual observed failure;
- leave task manual_required/failed honestly;
- do not regress to the old unsupported-action error.

# 10. OWNER ACCEPTANCE TARGET

The specific acceptance goal is:

```text
OLD:
Unsupported action: deactivate

NEW:
task accepted by extension executor
-> exact Avito page opened
-> ID verified
-> dry-run reaches control discovery
```

For LOCAL acceptance, Dry-Run remains the default and may stop before the destructive click.

However, the IMPLEMENTATION itself must contain the complete Armed-mode path capable of performing the actual deactivation through the logged-in browser session once Dry-Run is explicitly disabled for an approved task.

The Owner does not need a real external deactivation yet unless a disposable listing is explicitly approved.

# 11. VDS SAFETY

Strictly:

```text
VDS_DEPLOYED = false
VDS_DATA_MODIFIED = false
UPDATE_VDS_RUN = false
REAL_PRODUCTION_LISTING_DEACTIVATED = false
```

Do not use production SSH for any write operation.

# 12. GIT

Commit LOCAL fix if consistent with current LOCAL workflow.

Do not push/deploy unless current local-development convention explicitly allows push before Owner acceptance.

Report:

```text
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:
```

# 13. FINAL REPORT CONTRACT

Return:

```text
# Stage 09A-R2 LOCAL — Avito Action Contract Fix

## Root Cause
PERSISTED_ACTION:
BRIDGE_ACTION_BEFORE:
EXTENSION_EXPECTED_ACTION:
ROOT_CAUSE:

## Fix
INTERNAL_ACTION:
EXTENSION_TRANSPORT_ACTION:
ADAPTER_LOCATION:
DB_SCHEMA_CHANGED:
EXTENSION_CHANGED:
EXTENSION_VERSION:

## Backward Compatibility
EXISTING_DEACTIVATE_TASKS_SUPPORTED:
EXISTING_TASK_RETRIED:
UNSUPPORTED_ACTION_ERROR_GONE:

## Sale Detail Permanent Action
SALE_DETAIL_AVITO_BUTTON_VISIBLE:
SALE_DETAIL_AVITO_BUTTON_ALWAYS_AVAILABLE:
OLD_SALE_SUPPORTED:
DISMISSED_POST_SALE_TASK_REUSABLE:
MULTI_ITEM_SALE_BUTTON_SUPPORTED:
NO_DUPLICATE_TASK_CREATED:
ALREADY_INACTIVE_MESSAGE:
NO_AVITO_LINK_MESSAGE:

## Browser Executor Route
DIRECT_LISTING_URL_USED:
TEMPORARY_AVITO_TAB_SUPPORTED:
EXACT_LISTING_ID_RETAINED_ACROSS_NAVIGATION:
OWNER_MANAGEMENT_CONTEXT_REACHED:
EXACT_DEACTIVATION_CONTROL_REACHED:
PREVIOUS_TAB_FOCUS_RESTORED:
TASK_TAB_CLOSE_AFTER_SUCCESS_SUPPORTED:

## Real Local Proof
SALE_ID:
PRODUCT:
AVITO_ID:
TASK_REQUEUED:
TASK_FETCHED_BY_EXTENSION:
RECEIVED_ACTION:
EXACT_LISTING_OPENED:
LISTING_ID_MATCHED:
DRY_RUN_ACTIVE:
DEACTIVATION_CONTROL_DISCOVERY_REACHED:
FINAL_CLICK_PERFORMED: false
FALSE_SUCCESS: false

## Tests
FAILED:

## VDS Safety
VDS_DEPLOYED: false
VDS_DATA_MODIFIED: false
UPDATE_VDS_RUN: false
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
TECHNOREBOOT_STAGE09A_R2_LOCAL_AVITO_ACTION_CONTRACT_FIXED_READY_FOR_OWNER_ACCEPTANCE

DO_NOT_DEPLOY_TO_VDS_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- `Unsupported action: deactivate` still occurs;
- unknown actions are broadly accepted;
- dry-run protection is weakened;
- VDS is modified;
- tests fail.

# 14. STOP

After the narrow LOCAL fix and proof:

STOP.

Wait for Owner browser acceptance.
