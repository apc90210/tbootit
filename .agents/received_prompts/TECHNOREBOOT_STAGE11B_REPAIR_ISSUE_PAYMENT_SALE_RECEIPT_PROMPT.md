# TECHNOREBOOT — Stage 11B LOCAL
## Repair Ready -> Issued payment finalization, linked sale, and repair warranty receipt

Project: ТехноРебут
Workspace: C:\tbootit
Environment: LOCAL ONLY
Canonical production VDS: 144.31.15.88 — DO NOT DEPLOY IN THIS STAGE

Dependency: run after Stage 11A is accepted, or at minimum preserve compatibility with the sale-correction model introduced there.

# 0. GOAL

Implement the canonical repair completion workflow:

Ремонт выполняется
-> Готов
-> Выдан

Critical business rule:

Готов != продажа

A repair becomes revenue / a sale ONLY when it changes from:
Готов -> Выдан

At that moment operator must confirm:
- final repair amount;
- payment method;
- warranty term for completed repair work.

Only after confirmation:
- repair becomes Выдан;
- exactly one linked sale is created;
- it appears in normal sales/reports;
- printable repair receipt / warranty document becomes available.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:
C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE11B_REPAIR_ISSUE_PAYMENT_SALE_RECEIPT_PROMPT.md

to:
C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE11B_REPAIR_ISSUE_PAYMENT_SALE_RECEIPT_PROMPT.md

# 2. LOCAL-ONLY SAFETY

Before work:
- git status
- git branch --show-current
- git rev-parse HEAD
- docker compose ps

Preserve uncommitted work.

Do NOT:
- deploy production;
- mutate VDS 144.31.15.88;
- send LOCAL business DB/media to VDS;
- create automatic Avito actions.

# 3. ARCHITECTURE PREFLIGHT

Inspect:
- repair statuses/transitions;
- repair detail UI;
- customer/device/serial/problem/diagnosis/work-done/parts fields;
- repair estimated/final amount fields if present;
- payment methods;
- sales model/API from Stage11A/current branch;
- reports;
- receipt/print templates/CSS;
- actor/audit/event model.

Respect current module boundaries.
Do not make Repairs module write Sales DB directly if current architecture expects Core API ownership.

# 4. STATUS MODEL

Ensure distinct statuses:
- Готов
- Выдан

If backend uses English enums, keep UI Russian labels.

Готов:
- work finished;
- device awaits customer;
- NO sale/revenue;
- no payment required merely to mark Ready.

Выдан:
- device physically handed to customer;
- payment finalized;
- linked sale exists exactly once.

Do not merge Ready and Issued.

# 5. READY -> ISSUED UI

When operator chooses Готов -> Выдан, do NOT change status immediately.

Open completion modal/page with required fields:
- Окончательная стоимость ремонта
- Способ оплаты
- Гарантия на выполненные работы

Warranty UX:
- use existing business policy if one exists;
- if no canonical period exists, require explicit operator input instead of inventing a default;
- practical representation may be warranty_days with 0 = без гарантии, or equivalent explicit period model;
- validate clearly.

Buttons:
[Подтвердить выдачу и оплату]
[Отмена]

If canceled:
- repair remains Готов;
- no sale;
- no payment finalization.

# 6. ATOMIC ISSUE TRANSACTION

Confirmed issue must be one atomic transaction:

validate repair is Ready
-> validate amount/payment/warranty
-> capture actor/time
-> create/obtain linked sale exactly once
-> store final repair financial/warranty fields
-> set repair status Issued
-> append repair event/audit
-> commit

Any failure:
- rollback all;
- repair remains Ready;
- no orphan sale.

# 7. EXACTLY ONE LINKED SALE

Each issued repair must have exactly one canonical linked sale.

Create durable relationship using project conventions, conceptually:
repair_order_id <-> sale_id

Enforce uniqueness/idempotency.

Double click / refresh / retry must never create duplicate sales.

# 8. NO FAKE INVENTORY PRODUCT

Repair/service sale is not a physical inventory product unless current model explicitly represents parts.

Do NOT create fake inventory products just to satisfy sale-item constraints.

Use a proper service/repair sale representation:
- source/type = repair;
- linked repair order;
- service/non-stock line if architecture supports it.

Choose minimal clean model compatible with sales/reports.

# 9. SALES MODULE REPRESENTATION

Repair-generated sale must appear in ordinary sales list and reports.

Make source understandable, e.g.:
Ремонт №123

Include:
- final amount;
- payment method;
- issue/payment time;
- link back to repair detail if practical.

Revenue counted exactly once.

# 10. STAGE 11A COMPATIBILITY

Repair-generated sales must remain auditable.

If Stage11A allows amount/payment correction:
- correction of repair sale amount/payment must use canonical correction flow;
- linked repair financial snapshot must update transactionally so UIs do not disagree;
- append audit/history referencing sale correction;
- never duplicate revenue.

For repair-specific service line:
- do not allow arbitrary stock-product manipulation unless current repair model intentionally supports repair parts/products.

Document chosen behavior.

# 11. REPAIR AUDIT EVENT

Repair history must record issue event:
- date/time;
- actor;
- status Готов -> Выдан;
- final amount;
- payment method;
- warranty;
- linked sale number/ID.

Reuse existing repair event/history architecture if present.

# 12. PRINTABLE REPAIR RECEIPT / WARRANTY

Implement print-friendly document available immediately after issue and later from repair detail.

Recommended title:
Квитанция на ремонт / гарантийный талон

Reuse current sales receipt visual style/business header where practical.

Include available fields:
- store/business identity from current receipt config;
- repair number;
- acceptance date if available;
- issue date;
- customer if stored;
- device;
- model;
- serial number if stored;
- declared fault if appropriate;
- completed work/result;
- used parts only if current repair model has them;
- final amount;
- payment method;
- warranty term;
- linked sale/document number.

If warranty stored in days:
- print human-readable period;
- optionally compute warranty end date from issue date.

Do not invent legal/fiscal claims.
This is a repair receipt/warranty document, not automatically a fiscal receipt.

# 13. PRINT UX

After successful issue show:
Ремонт выдан
Продажа №...
[Распечатать квитанцию / гарантию]

Issued repair detail keeps permanent print button.

Browser printing only; no Owner command line.

# 14. REPORTS

Repair-generated sale participates in:
- Today;
- Week;
- Year;
- payment-method totals.

Use issue/payment timestamp and final amount.

Marking repair Готов alone must not affect revenue.

# 15. REVERSE / REOPEN

Do not invent a complex reverse workflow.

If current UI allows moving issued repair backward:
- prevent casual status change that would orphan/double-count linked sale;
- require existing sale cancellation/reversal semantics or block with clear message.

Document behavior.

# 16. SCHEMA / MIGRATION

If schema changes are needed:
- explicit migration;
- preserve existing repair records;
- existing non-issued repairs get no sale;
- existing issued repairs must not be blindly duplicated.

If historical issued repairs exist without linked sale:
- do NOT fabricate historical revenue automatically;
- report them and leave explicit backfill decision for Owner unless a safe mapping already exists.

Run Schema Guard before and after.

# 17. TESTS

Add tests at minimum:
1. mark Ready -> no sale;
2. open Issue flow then cancel -> remains Ready/no sale;
3. Ready -> Issued with valid amount/payment/warranty -> exactly one sale;
4. double submit/retry -> still one sale;
5. sale amount equals final repair amount;
6. sale payment method equals selected method;
7. sale appears in sales list/reports;
8. repair links to sale and sale links to repair;
9. repair history stores actor/time/amount/payment/warranty;
10. receipt route renders;
11. receipt contains amount/payment/warranty/device/order number;
12. invalid amount/payment/warranty -> no partial transition;
13. backward casual status change cannot orphan sale;
14. Stage11A correction of linked repair sale preserves financial consistency;
15. existing production-synced repair data remains readable.

Run official project tests.

# 18. LOCAL OWNER BROWSER CHECK

Leave LOCAL running at:
https://localhost:8443

Owner browser workflow:
1. Open Repairs.
2. Open/create safe LOCAL repair.
3. Move it to Готов.
4. Confirm no sale exists yet.
5. Choose Выдать.
6. Enter final amount.
7. Choose payment method.
8. Enter warranty term.
9. Confirm.
10. Verify status becomes Выдан.
11. Verify linked sale appears in Sales.
12. Verify amount/payment match.
13. Open/print repair receipt/warranty.
14. Confirm repair history shows issue details.

Do not ask Owner for CMD/PowerShell.

# 19. DOCUMENTATION

Create:
reports/stage11b_repair_issue_payment_sale_receipt_report.md

Update relevant docs and logs/<current-date>.md.

Document:
- Ready vs Issued semantics;
- sale linkage;
- idempotency;
- warranty representation;
- receipt route/template;
- Stage11A correction integration.

# 20. GIT

Commit tracked code/tests/docs only.
Never commit LOCAL DB/media/backups/secrets/private keys.
Push main after tests pass.

# 21. FINAL REPORT CONTRACT

Return:

# Stage 11B — Repair Issue -> Sale + Warranty Receipt

## Status Flow
READY_EXISTS:
ISSUED_EXISTS:
READY_CREATES_SALE: false
ISSUED_REQUIRES_PAYMENT_CONFIRMATION:

## Issue Modal
FINAL_AMOUNT_REQUIRED:
PAYMENT_METHOD_REQUIRED:
WARRANTY_TERM_REQUIRED:
CANCEL_LEAVES_READY:

## Linked Sale
SALE_CREATED_ON_ISSUE:
EXACTLY_ONE_SALE_PER_REPAIR:
REPAIR_SALE_LINK:
SALE_REPAIR_LINK:
SERVICE_NOT_FAKE_INVENTORY_PRODUCT:
REPORTS_INCLUDE_REPAIR_SALE:

## Audit
ISSUE_ACTOR_RECORDED:
ISSUE_TIMESTAMP_RECORDED:
AMOUNT_RECORDED:
PAYMENT_RECORDED:
WARRANTY_RECORDED:
SALE_ID_RECORDED:

## Receipt
REPAIR_RECEIPT_ROUTE:
PRINT_BUTTON:
DEVICE_INFO_PRESENT:
FINAL_AMOUNT_PRESENT:
PAYMENT_METHOD_PRESENT:
WARRANTY_PRESENT:

## Stage11A Compatibility
REPAIR_SALE_CORRECTION_SUPPORTED:
FINANCIAL_FIELDS_STAY_CONSISTENT:
AUDIT_PRESERVED:

## Tests
AUTOMATED_TESTS:
LOCAL_6_SERVICES_HEALTHY:
LOCAL_SMOKE:

## Production
PRODUCTION_TOUCHED: false
DEPLOYED_TO_144_31_15_88: false

FINAL_STATUS:
TECHNOREBOOT_STAGE11B_LOCAL_READY_FOR_OWNER_ACCEPTANCE

# 22. STOP

STOP after LOCAL implementation + tests + smoke.
Do NOT deploy to production.
Wait for Owner browser acceptance.
