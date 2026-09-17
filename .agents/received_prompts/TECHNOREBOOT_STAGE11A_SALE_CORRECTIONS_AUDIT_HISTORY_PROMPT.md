# TECHNOREBOOT — Stage 11A LOCAL
## Safe correction of completed sales with immutable audit history

Project: ТехноРебут
Workspace: C:\tbootit
Environment: LOCAL ONLY
Canonical production VDS: 144.31.15.88 — DO NOT DEPLOY IN THIS STAGE

# 0. GOAL

Implement a safe correction workflow for already completed sales.

Owner requirement:
- change sale amount / sold price;
- change payment method;
- remove a sold product;
- add another product;
- replace one product with another;
- correct the composition of the sale.

Corrections must NOT silently overwrite history.

The system must make it immediately visible that a sale was edited and preserve:

when / who / what changed / old value -> new value.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:
C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE11A_SALE_CORRECTIONS_AUDIT_HISTORY_PROMPT.md

to:
C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE11A_SALE_CORRECTIONS_AUDIT_HISTORY_PROMPT.md

# 2. LOCAL-ONLY SAFETY

Before work:
- git status
- git branch --show-current
- git rev-parse HEAD
- docker compose ps

Preserve uncommitted work.

Do NOT:
- mutate production;
- deploy to 144.31.15.88;
- copy LOCAL business data to production;
- resurrect Dry-Run / Armed / automatic Avito deactivation.

Use current LOCAL production-synced business data only.

# 3. ARCHITECTURE PREFLIGHT

Inspect current implementation before coding:
- Core sales models/APIs;
- sale item model;
- sale statuses;
- inventory quantity/status transitions;
- payment-method model;
- Today/Week/Year reports;
- receipt generation;
- authenticated actor identity;
- post-sale Avito task logic;
- sales list/detail UI.

Respect current module boundaries.
Core remains owner of canonical sales/inventory data.

# 4. EDITABLE SALES

Primary editable state: completed sale.

Do not allow direct correction of canceled sales.
Preserve current canceled/superseded/reissued semantics.

Correction keeps the same sale ID.
Do NOT delete the old sale and create an unrelated replacement.

# 5. IMMUTABLE REVISION MODEL

Implement append-only sale revision history using project naming conventions.

Conceptually store:
- id
- sale_id
- revision_no
- changed_at
- changed_by
- optional reason/comment
- before_snapshot
- after_snapshot
- structured_diff

Requirements:
- revisions never updated/deleted by normal UI;
- every successful correction creates exactly one revision;
- failed correction creates none;
- revision_no increases per sale;
- actor comes from existing authenticated identity where possible;
- normal UI must show readable changes, not raw JSON.

# 6. ATOMIC CORRECTION

Correction must be one DB/business transaction:

read current sale
-> validate editable
-> capture before snapshot
-> validate new state
-> reconcile inventory delta
-> update sale/items/payment
-> append revision
-> commit

Any failure => rollback everything.

# 7. INVENTORY RECONCILIATION

Product removed from completed sale:
- return to stock;
- restore quantity/status using canonical existing cancellation/return rules;
- never duplicate stock.

Product added:
- require sufficient current stock;
- deduct stock exactly once;
- use normal sale stock transition rules.

Product replaced:
- restore old;
- deduct new.

Price/payment-only changes:
- no stock effect.

Do not assume quantity is always 1 if current model supports quantities.

# 8. FINANCIAL CONSISTENCY

Owner must be able to correct sale amount.

If total is derived from line prices:
- edit line sale prices;
- recompute total canonically.

If explicit total/final amount exists:
- preserve current accounting invariant;
- prevent inconsistent totals.

Reports must use corrected current state and must NOT count revision history as new revenue.

# 9. PAYMENT METHOD

Allow changing payment method using current canonical payment methods.

Correction must update:
- sale detail;
- payment-method reports;
- Today/Week/Year totals where applicable.

History example:
Способ оплаты: Наличные -> Перевод

# 10. UI — SALES LIST MARKER

Corrected sales must be visibly marked in the sales list.

Use a compact marker such as:
✎ Изменена
or equivalent.

Requirements:
- visible without opening the sale;
- tooltip/title explains correction history;
- display revision count if clean, e.g. Изменена ×2;
- do not style as a fatal error.

# 11. UI — SALE DETAIL / EDIT

Add:
[Изменить продажу]

Prefill current sale.

Allow:
- remove item;
- add item using current product search/barcode flow where practical;
- replace item;
- edit sold price/amount;
- edit payment method.

After save:
- current sale detail reflects corrected state;
- edited marker appears;
- history appears below.

# 12. UI — HISTORY

Add:
История изменений

Each revision should show:
- date/time;
- actor;
- revision number;
- human-readable changes.

Example:
16.09.2026 18:42 — OWNER
Ревизия №2
• Способ оплаты: Наличные -> Перевод
• Итог: 18 000 ₽ -> 17 500 ₽
• Удалён товар: SSD Kingston 480 GB
• Добавлен товар: SSD Samsung 500 GB

# 13. CORRECTION COMMENT

If clean, add:
Комментарий / причина корректировки

It may be optional unless existing audit conventions make a mandatory reason clearly preferable.
Do not invent approval workflows.

# 14. RECEIPT / REPRINT

Existing receipt/reprint must use corrected current sale state.

If clean, add a small note:
Продажа скорректирована — ревизия №N

Do not print full history.

# 15. AVITO CONSISTENCY

Automatic Avito deactivation remains forbidden.

If correction adds a sold product with active linked Avito listing:
- create/ensure canonical manual post-sale task idempotently.

If correction removes a product:
- never auto-reactivate/publish listing;
- if pending/manual_required task can safely be canceled/superseded, use current semantics;
- if already manually confirmed removed, preserve history and record the correction.

No remote automatic Avito mutation.

# 16. DOUBLE-SUBMIT / CONCURRENCY

Prevent double application:
- retry/double-click must not decrement inventory twice;
- reject stale/invalid state cleanly where practical.

# 17. MIGRATION / SCHEMA GUARD

If DB change is required:
- explicit migration;
- preserve existing sales;
- existing sales must not appear edited without revisions;
- run Schema Guard before and after.

# 18. TESTS

Add tests for at least:
1. payment method only;
2. amount only;
3. remove item -> stock restored;
4. add item -> stock deducted;
5. replace item -> both reconciled;
6. insufficient stock -> full rollback;
7. one edit -> one revision;
8. two edits -> revisions 1 and 2;
9. failed edit -> no revision;
10. reports use corrected amount/payment without duplicate revenue;
11. receipt uses corrected state;
12. canceled sale cannot be directly corrected;
13. automatic Avito deactivation still disabled;
14. manual Avito task handling remains canonical;
15. production-synced existing sales remain readable.

Run official project tests.

# 19. LOCAL OWNER BROWSER CHECK

Leave LOCAL running at https://localhost:8443

Owner browser workflow:
1. Open Sales.
2. Use a safe LOCAL test sale.
3. Open it.
4. Click Изменить продажу.
5. Change payment method and amount.
6. Replace/add/remove an item.
7. Save.
8. Verify edited marker in sales list.
9. Reopen and inspect readable history.
10. Verify inventory delta.

Do not ask Owner for CMD/PowerShell.

# 20. DOCUMENTATION

Create:
reports/stage11a_sale_corrections_audit_history_report.md

Update relevant docs and logs/<current-date>.md.

# 21. GIT

Commit tracked code/tests/docs only.
Never commit LOCAL DB/media/backups/secrets/private keys.
Push main after tests pass.

# 22. FINAL REPORT CONTRACT

Return:

# Stage 11A — Sale Corrections + Audit History

## Implementation
SALE_CORRECTION_API:
SALE_REVISION_STORAGE:
ACTOR_SOURCE:
ATOMIC_TRANSACTION:
SCHEMA_GUARD:

## Editable Fields
ITEM_ADD:
ITEM_REMOVE:
ITEM_REPLACE:
PRICE_AMOUNT_EDIT:
PAYMENT_METHOD_EDIT:

## Inventory
REMOVED_ITEM_RESTORES_STOCK:
ADDED_ITEM_DEDUCTS_STOCK:
REPLACEMENT_RECONCILES_BOTH:
ROLLBACK_ON_FAILURE:

## Audit
EDITED_MARKER_IN_LIST:
REVISION_COUNT_VISIBLE:
DETAIL_HISTORY_VISIBLE:
TIMESTAMP_RECORDED:
ACTOR_RECORDED:
BEFORE_AFTER_DIFF_VISIBLE:

## Reports / Receipt
REPORTS_USE_CORRECTED_STATE:
NO_DOUBLE_REVENUE:
RECEIPT_USES_CORRECTED_STATE:

## Avito
AUTO_DEACTIVATION_DISABLED:
MANUAL_POST_SALE_TASKS_RECONCILED:

## Tests
AUTOMATED_TESTS:
LOCAL_6_SERVICES_HEALTHY:
LOCAL_SMOKE:

## Production
PRODUCTION_TOUCHED: false
DEPLOYED_TO_144_31_15_88: false

FINAL_STATUS:
TECHNOREBOOT_STAGE11A_LOCAL_READY_FOR_OWNER_ACCEPTANCE

# 23. STOP

STOP after LOCAL implementation + tests + smoke.
Do NOT deploy to production.
Wait for Owner browser acceptance.
