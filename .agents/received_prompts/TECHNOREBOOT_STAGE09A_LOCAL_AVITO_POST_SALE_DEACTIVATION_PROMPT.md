# TECHNOREBOOT — Stage 09A LOCAL
## Avito post-sale deactivation automation — LOCAL development only

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**LOCAL URL:** `https://localhost:8443`  
**Production VDS:** `https://144.31.50.134`  
**Stage:** `Stage 09A LOCAL — Avito Post-Sale Deactivation Automation`

# 0. OWNER OPERATING MODE — CRITICAL

This stage is LOCAL DEVELOPMENT ONLY.

Do NOT deploy anything to VDS in this stage.

Do NOT run UPDATE VDS.

Do NOT modify production VDS code.

Do NOT modify production VDS database/media/business state.

Do NOT execute real destructive Avito actions against production listings unless Owner explicitly approves a disposable/test listing.

Permanent workflow:

```text
LOCAL development
↓
LOCAL automated tests
↓
LOCAL browser/manual Owner acceptance
↓
STOP

Only after Owner says "ок":
separate deployment stage
↓
Git/push if needed
↓
VDS preflight
↓
backup/checkpoint
↓
Schema Guard
↓
code-only UPDATE
↓
production verification
```

Business data direction remains:

```text
VDS -> LOCAL
```

Never:

```text
LOCAL business DB/media -> VDS
```

---

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE09A_LOCAL_AVITO_POST_SALE_DEACTIVATION_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE09A_LOCAL_AVITO_POST_SALE_DEACTIVATION_PROMPT.md`

---

# 2. PREFLIGHT

Record:

```text
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
LOCAL_GIT_STATUS:
LOCAL_STACK_HEALTHY:
LOCAL_PRODUCTS:
LOCAL_SALES:
LOCAL_REPAIRS:
LOCAL_PHOTOS:
LOCAL_EXTERNAL_LISTINGS:
```

Verify LOCAL environment sentinel:

```text
data/.technoreboot_local_dev
```

Verify VDS production sentinel is NOT present locally.

Verify no system operation job is running.

Do not touch VDS.

---

# 3. GOAL

When a sale is completed locally, if the sold product is linked to an active Avito listing, the system must offer to deactivate/remove that listing from publication.

Desired UX:

```text
Продажа оформлена.

Товар:
HP LaserJet ...

Avito №1234567890 активно.

Снять объявление с Avito?

[ Не сейчас ]
[ Снять с Avito ]
```

For multi-item sale:

```text
Продажа оформлена.

Найдено активных объявлений Avito: 3

[ Не сейчас ]
[ Снять 3 объявления с Avito ]
```

The sale itself must remain completed regardless of Avito availability.

---

# 4. AUDIT CURRENT SALE FLOW

Inspect current implementation of:
- sale completion;
- inventory decrement/write-off;
- sale status;
- product status after sale;
- sale cancellation;
- receipt generation;
- UI after successful sale.

Identify exact hook point after transaction success.

Do NOT trigger Avito logic before sale commit.

Required principle:

```text
SALE SUCCESS
then
AVITO FOLLOW-UP
```

---

# 5. AUDIT CURRENT AVITO LINK MODEL

Inspect:
- `product_external_listings`;
- current Avito ID fields;
- listing URL;
- listing status;
- Avito account/profile relation;
- extension bridge;
- extension v0.2.56;
- current browser-assisted reverse flow;
- official API capability layer.

Use existing canonical identity.

Do NOT create a second Avito-ID mapping model.

Document exact relation:

```text
Product
↔
External Listing
↔
Avito Listing ID
↔
Avito URL
↔
Current status
```

---

# 6. BUSINESS RULES

After sale completion:

## No linked Avito listing

```text
No prompt
No task
```

## Linked listing already inactive / archived / removed / closed

```text
No deactivation task
No duplicate action
```

## Linked active listing

```text
Create/surface deactivation suggestion
```

The seller may choose:

```text
Не сейчас
```

or:

```text
Снять с Avito
```

`Не сейчас` must not lose the action.
It should remain visible later as pending cleanup.

---

# 7. PERSISTENT TASK MODEL

First inspect whether an existing event/outbox/action model can safely store this workflow.

Prefer reuse if semantically correct.

Required task states:

```text
suggested
queued
processing
success
failed
manual_required
canceled
```

Required fields:

```text
id
sale_id
product_id
external_listing_id
avito_listing_id
listing_url
status
requested_by
requested_at
started_at
finished_at
attempt_count
last_error
execution_mode
result_metadata
```

Idempotency key:

```text
sale_id + product_id + avito_listing_id + action=deactivate
```

Duplicate task creation must be impossible.

---

# 8. SCHEMA GUARD RULE

If an existing persistent model cannot support the task safely and a DB schema change is required:

1. implement the schema change LOCALLY;
2. regenerate:
   `deploy/production/schema_contract.json`
3. set:
   `deploy/production/deployment_compatibility.json`

to:

```json
{
  "requires_manual_migration": true,
  "database_change": true
}
```

4. add explicit reason;
5. continue LOCAL testing;
6. DO NOT deploy to VDS in this stage.

The future VDS deployment must become a separate migration/deploy stage.

Do NOT bypass Schema Guard.

---

# 9. EXECUTION MODES

Implement capability-based execution.

Priority:

```text
1. official Avito API, if current capability supports exact deactivation operation
2. Chrome Extension browser-assisted
3. manual_required fallback
```

For LOCAL stage:
- fully implement and test task routing;
- use mocks/fixtures for official API where appropriate;
- use extension task channel locally;
- do not deactivate a real production listing.

---

# 10. OFFICIAL API MODE

If the current Avito module has credentials/capability for deactivation:

Implement:

```text
can_deactivate_listing = true/false
```

Only use the official API if:
- account capability is valid;
- exact listing ID matches;
- API supports exact operation;
- success can be confirmed by response/status.

If unavailable:

```text
OFFICIAL_API_AVAILABLE = false
```

and use extension mode.

Do not fabricate capability.

---

# 11. CHROME EXTENSION TASK CHANNEL

If browser-assisted mode is needed, add a task channel using the existing extension bridge.

Suggested endpoints:

```text
GET  /admin-api/avito-extension/tasks/next
POST /admin-api/avito-extension/tasks/{id}/started
POST /admin-api/avito-extension/tasks/{id}/success
POST /admin-api/avito-extension/tasks/{id}/failed
```

Equivalent existing route structure is acceptable.

Task payload:

```json
{
  "task_id": "...",
  "action": "deactivate_listing",
  "sale_id": 123,
  "product_id": 456,
  "avito_listing_id": "1234567890",
  "listing_url": "https://www.avito.ru/..."
}
```

Validate server-side:
- Avito domain;
- listing ID;
- task action;
- linked product/listing identity.

No arbitrary URL execution.

---

# 12. EXTENSION BEHAVIOR

For action:

```text
deactivate_listing
```

Extension must:

1. verify correct server pairing;
2. receive exact task;
3. validate listing ID;
4. open/focus exact listing management page;
5. perform only deactivate/remove/archive-from-publication action;
6. wait for visible confirmation;
7. send success only after confirmation.

Never:
- publish;
- republish;
- pay/promote;
- edit title;
- edit price;
- edit description;
- click unrelated ads/listings;
- operate on another Avito ID.

If selectors/UI are unknown:

```text
manual_required
```

Do not guess-click.

---

# 13. EXTENSION VERSION

If extension source changes:

```text
0.2.56 -> 0.2.57
```

Update:
- manifest;
- popup;
- service worker/content script refs if needed;
- backend expected version;
- admin-shell download package;
- extension ZIP.

Run existing extension regression suites.

LOCAL only.

---

# 14. POST-SALE UI

After sale success, show an Avito follow-up block.

Single item:

```text
Продажа оформлена

Avito:
Объявление №1234567890 активно

[ Не сейчас ]
[ Снять с Avito ]
```

Multi-item:

```text
Активных объявлений Avito после продажи: 3

[ Не сейчас ]
[ Снять все ]
```

After action:

```text
Снято: 2
Требует ручной проверки: 1
```

Sale receipt and success state must remain visible.

---

# 15. PENDING CLEANUP VIEW

Add a small view/page/section:

```text
Avito → После продаж
```

or equivalent inside existing Avito module UI.

Show:

```text
Дата
Sale ID
Товар
Avito ID
Статус
Попытки
Ошибка
Действие
```

Actions:

```text
[ Снять с Avito ]
[ Повторить ]
```

Only valid pending/failed/manual states.

---

# 16. RETRIES

Recommended:

```text
max automatic attempts = 3
```

Flow:

```text
queued
↓
processing
↓
failed
↓
retry
↓
manual_required after limit
```

No infinite loop.

No duplicate external action.

---

# 17. SUCCESS SEMANTICS

Only mark:

```text
success
```

after actual external confirmation.

On success:
- update canonical external listing status;
- write audit event:
  `avito_listing_deactivated_after_sale`.

Record:
- sale_id;
- product_id;
- listing ID;
- execution mode;
- timestamp.

Do NOT:
- delete Product;
- change completed sale;
- change physical inventory because of Avito state.

Stock was already handled by sale.

---

# 18. SALE CANCELLATION

If sale is later canceled after Avito listing was deactivated:

Do NOT automatically republish listing.

Show:

```text
Продажа отменена.
Объявление Avito ранее было снято.
Автоматическая повторная публикация не выполняется.
```

Republishing is a separate future feature/action.

---

# 19. RBAC

Seller USER may:
- see post-sale prompt;
- request deactivation for listing linked to sold product;
- retry pending/failed deactivation;
- view post-sale cleanup queue.

Seller USER may NOT:
- delete Avito profile;
- change credentials;
- change OAuth settings;
- change extension pairing server;
- perform arbitrary account management.

OWNER may see full operational state.

---

# 20. LOCAL TEST DATA SAFETY

Do NOT use current real VDS Avito listings for destructive external testing.

Use:
- mocked API;
- mocked browser task completion;
- LOCAL test listing;
- explicitly disposable Avito listing only if Owner later approves.

For browser-assisted flow, it is sufficient in this stage to prove:
- task reaches extension;
- exact URL/ID validation works;
- correct page/action preparation happens;
- dry-run/manual_required behavior works.

Do not actually click "deactivate" on a real production listing without Owner approval.

---

# 21. TESTS

Add tests for:

## Sale integration
- sale completed with no Avito listing -> no task;
- active linked listing -> suggested task;
- inactive linked listing -> no task;
- duplicate callback -> no duplicate task.

## Multi-item sale
- one task per active linked listing;
- unrelated products ignored;
- one failure does not block others.

## Task lifecycle
- suggested -> queued;
- queued -> processing;
- processing -> success;
- processing -> failed;
- failed -> retry;
- retry limit -> manual_required.

## Idempotency
- duplicate request returns existing task;
- no duplicate external action.

## RBAC
- USER can request post-sale deactivate;
- USER cannot admin Avito profile/account;
- OWNER works.

## Extension
- valid Avito URL accepted;
- invalid domain rejected;
- listing ID mismatch rejected;
- exact target only;
- unknown UI -> manual_required;
- no publish/payment actions.

## Data integrity
- sale remains completed if Avito fails;
- stock unchanged by Avito task;
- product remains in DB;
- listing state only changes after confirmed success.

## Sale cancellation
- no automatic republish.

Required:

```text
FAILED = 0
```

---

# 22. LOCAL FULL REGRESSION

Run at minimum:
- new Stage09A tests;
- sales tests;
- inventory tests;
- RBAC tests;
- extension pairing tests;
- extension regression;
- schema guard;
- production data guard;
- owner operations tests.

Required:

```text
FAILED = 0
```

---

# 23. LOCAL RUNTIME PROOF

On:

```text
https://localhost:8443
```

Verify with OWNER:

1. sale UI works;
2. controlled LOCAL sale can complete;
3. linked active Avito listing produces post-sale prompt;
4. `Не сейчас` preserves pending task;
5. `Снять с Avito` queues task;
6. task visible in Avito post-sale queue;
7. extension paired locally can fetch the task;
8. dry-run/mock execution can report success/failure;
9. no unrelated listing action occurs;
10. sale remains valid regardless of Avito task result.

Do NOT deploy to VDS.

---

# 24. GIT

Commit LOCAL source/tests/docs.

Push `origin/main` only if that matches current project workflow and Owner has not prohibited push before LOCAL acceptance.

However:

```text
DO NOT UPDATE VDS
```

Do not run:
- `/system/operations -> UPDATE VDS`;
- `update_code_only.sh`;
- production migration.

If Owner workflow requires commit only after manual acceptance, leave changes uncommitted but cleanly documented and report that status.

Prefer to follow the current repo convention without touching VDS.

---

# 25. DOCUMENTATION

Create/update:

```text
docs/avito_post_sale_deactivation.md
docs/production_status.md
reports/stage09a_local_avito_post_sale_deactivation_report.md
logs/2026-09-12.md
```

If schema changed, document:

```text
MIGRATION_REQUIRED = true
```

and exact diff.

---

# 26. FINAL REPORT CONTRACT

Return:

```text
# Stage 09A LOCAL — Avito Post-Sale Deactivation

## Environment
LOCAL_ONLY: true
VDS_DEPLOYED: false
VDS_DATA_MODIFIED: false

## Sale Integration
SALE_COMPLETION_HOOK:
ACTIVE_LISTING_DETECTED:
NO_LISTING_BEHAVIOR:
INACTIVE_LISTING_BEHAVIOR:
MULTI_ITEM_SUPPORTED:
SALE_BLOCKED_BY_AVITO_FAILURE: false

## Task Model
PERSISTENT_TASK_MODEL:
SCHEMA_CHANGE_REQUIRED:
MIGRATION_REQUIRED:
IDEMPOTENCY_KEY:
TASK_STATES:
RETRY_LIMIT:
MANUAL_REQUIRED_SUPPORTED:

## Execution
OFFICIAL_API_AVAILABLE:
BROWSER_ASSISTED_AVAILABLE:
MANUAL_FALLBACK_AVAILABLE:
EXACT_LISTING_VALIDATION:
UNRELATED_AVITO_ACTIONS_BLOCKED:

## Extension
EXTENSION_CHANGED:
EXTENSION_VERSION:
LOCAL_PAIRING_WORKS:
ZIP_REBUILT:

## Data Semantics
PRODUCT_DELETED: false
SALE_CHANGED_BY_AVITO_FAILURE: false
PHYSICAL_STOCK_CHANGED_BY_AVITO_STATUS: false
LISTING_STATUS_UPDATED_ONLY_AFTER_CONFIRMATION:
AUDIT_EVENT_WRITTEN:

## RBAC
USER_CAN_REQUEST_POST_SALE_DEACTIVATION:
USER_CAN_ADMINISTER_AVITO_ACCOUNT: false
OWNER_SUPPORTED:

## Local Runtime
LOCAL_SALE_FLOW_WORKS:
POST_SALE_PROMPT_WORKS:
PENDING_QUEUE_WORKS:
EXTENSION_TASK_FETCH_WORKS:
DRY_RUN_OR_MOCK_RESULT_WORKS:

## Tests
FAILED:

## Schema Guard
SCHEMA_COMPATIBILITY:
REQUIRES_MANUAL_MIGRATION:
DATABASE_CHANGE:

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE09A_LOCAL_AVITO_POST_SALE_DEACTIVATION_READY_FOR_OWNER_ACCEPTANCE

DO_NOT_DEPLOY_TO_VDS_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- any VDS deployment occurs;
- real production Avito listing is deactivated without Owner approval;
- sale can fail because Avito is unavailable;
- success can be reported without confirmation;
- schema change bypasses Schema Guard;
- tests fail.

---

# 27. STOP

After LOCAL implementation, tests and local runtime proof:

STOP.

Wait for Owner browser acceptance.

Do not prepare or execute VDS deployment until Owner says `ок`.
