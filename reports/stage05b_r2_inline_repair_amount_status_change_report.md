# Stage05B-R2 Inline Repair Amount in Status Change Report

## STATUS
Stage05B-R2 completed successfully. The repair amount input (`Стоимость ремонта, ₽`) is now embedded directly inside the status change form on `/repairs/{id}`. Transitioning out of `diagnostics` to any next status atomically validates/saves the amount and changes status in a single operation. All unit tests, empirical live HTTP runtime scenarios, stock/sales isolation, and live DB test isolation checks passed 100%.

## OWNER_REQUIREMENT
Staff must be able to enter the repair amount directly in the status change block on `/repairs/{id}` without navigating to `/edit` or filling out diagnosis/works/parts text fields. Submitting the form must save the amount and update status in one single atomic operation.

## PROMPT_DISCOVERY
- PROMPT_SEARCH_DONE: true
- PROMPT_USED: TECHNOREBOOT_STAGE05B_R2_REPAIR_AMOUNT_INSIDE_STATUS_CHANGE_FORM_PROMPT.md
- PROMPT_SOURCE: C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE05B_R2_REPAIR_AMOUNT_INSIDE_STATUS_CHANGE_FORM_PROMPT.md
- PROMPT_LOCAL_COPY: C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE05B_R2_REPAIR_AMOUNT_INSIDE_STATUS_CHANGE_FORM_PROMPT.md
- PROMPT_SHA256: 9DAE9AB6821D3A4A336E8F07FBDE0B32EDB4CFE77F0C747E7FAAD95CBF2DDD3A

## PREFLIGHT
- Initial HEAD: dc0d3b4e1829878d885bea275042a172a211f990 (dc0d3b4)
- Branch: main
- Worktree status: clean

## PREVIOUS_FLOW
- Staff previously had to open `/repairs/{id}/edit` to enter `estimated_repair_amount`, save edit form, and then navigate back to `/repairs/{id}` to execute status change.

## NEW_INLINE_FLOW
- Input field `Стоимость ремонта, ₽` (`step="1" min="0"`) is embedded directly in the status update card when repair status is `diagnostics`. Staff enters amount and selects new status in a single form submit.

## CORE_REQUEST_CONTRACT
- `schemas.RepairOrderStatusUpdate` expanded to include `estimated_repair_amount: Optional[int] = None` with integer money validator.
- `POST /api/repairs/{repair_id}/status` receives `estimated_repair_amount` in request body.

## ATOMIC_TRANSACTION
- `core/app/routers/repairs.py` performs validation, updates `estimated_repair_amount`, updates `status`, creates `RepairStatusHistory`, and creates `AuditLog` in a single atomic DB transaction. No partial updates occur.

## ZERO_HANDLING
- `0` is a valid integer amount (`0 ₽`). It is displayed as `value="0"` in the HTML form and is correctly processed via explicit `is not None` checks.

## EMPTY_AMOUNT_HANDLING
- If `estimated_repair_amount` is `None` in both request and DB when exiting `diagnostics`, transition is blocked with HTTP 400 and detail message:
  `"Для выхода из статуса «Диагностика» укажите стоимость ремонта. Можно указать 0 ₽."`

## ALL_DIAGNOSTICS_TRANSITIONS
- Applies equally to all 6 allowed target statuses out of `diagnostics`: `waiting_customer`, `waiting_parts`, `in_repair`, `ready`, `unrepairable`, `canceled`.

## OPTIONAL_TEXT_FIELDS
- `diagnosis_text`, `planned_works_text`, `planned_parts_text` remain 100% optional.

## OPTIONAL_COMMENT
- `comment` field remains optional. Saved in status history if provided, `None` if empty.

## UI
- Embedded `<input type="number" name="estimated_repair_amount" step="1" min="0">` in `/repairs/{id}` status form for `diagnostics` status. Preserves pre-saved amounts (`0`, `2800`), displays empty field when unsaved (`null`).

## AUDIT
- Single `repair.status_changed` (or `repair.canceled`, `repair.issued`) audit entry created containing old/new status and old/new `estimated_repair_amount`.

## TESTS
- `core/tests/test_diagnostics_exit_amount_inline.py` (3 tests covering all exit target statuses, fallback to saved amount, explicit 0 override, negative/decimal validation).
- `core/tests/test_diagnostics_ready_amount_rule.py` (Updated detail string match).
- `core/tests/test_repairs_status_flow.py` (Updated status transition tests for inline amount).
- `core/tests/test_repairs_status_matrix_complete.py` (Updated for inline amount rule).
- `repairs-module/tests/test_diagnostics_exit_amount_inline_ui.py` (3 tests covering UI rendering with null/0/2800, single form submission, empty field blocking).
- `repairs-module/tests/test_diagnostics_ready_amount_rule_ui.py` & `test_repair_diagnostics_ready_ui.py` (Updated for inline amount detail string).
- All 4 test suites passed:
  - Core safe tests: 158/158 PASS
  - Inventory-sales-module: 110/110 PASS
  - Avito-module: 12/12 PASS
  - Repairs-module: 28/28 PASS
  - Total: 308/308 PASS (100% Green)

## RUNTIME_READY_2800
- Repair `ТЕСТ Stage05B-R2 READY 2800`: Submitted `status: ready`, `estimated_repair_amount: 2800` -> **HTTP 200**, `status=ready`, `estimated_repair_amount=2800`, `closed_at=null`, `issued_at=null`.

## RUNTIME_CANCELED_ZERO
- Repair `ТЕСТ Stage05B-R2 CANCELED ZERO`: Submitted `status: canceled`, `estimated_repair_amount: 0` -> **HTTP 200**, `status=canceled`, `estimated_repair_amount=0`.

## RUNTIME_WAITING_PARTS
- Repair `ТЕСТ Stage05B-R2 WAITING PARTS`: Submitted `status: waiting_parts`, `estimated_repair_amount: 1500` -> **HTTP 200**, `status=waiting_parts`, `estimated_repair_amount=1500`.

## RUNTIME_EMPTY
- Repair `ТЕСТ Stage05B-R2 EMPTY`: Submitted `status: ready`, `estimated_repair_amount: null` -> **Blocked (HTTP 400)**, detail `"Для выхода из статуса «Диагностика» укажите стоимость ремонта. Можно указать 0 ₽."`. Status remained `diagnostics`.

## LIVE_DB_TEST_ISOLATION
- LIVE_DB_SHA256_BEFORE_TESTS: `5b207b5bd7e0c6c69f3cdaab100b5431f74a86ba3481a4808ca668528fa4da9e`
- LIVE_DB_SHA256_AFTER_TESTS: `5b207b5bd7e0c6c69f3cdaab100b5431f74a86ba3481a4808ca668528fa4da9e`
- Record counts (products: 56, sales: 43, customers: 25, repairs: 46, history: 95, audit: 275) remained 100% identical before and after test suites.

## SAFETY_SCANS
- Scan 1 (destructive queries): Clean (0 production matches)
- Scan 2 (direct DB access in repairs-module): Clean (0 matches)
- Scan 3 (tracked DB/cache files): Clean (0 matches)

## FILES_CHANGED
- `core/app/schemas.py`
- `core/app/routers/repairs.py`
- `core/tests/test_diagnostics_exit_amount_inline.py`
- `core/tests/test_diagnostics_ready_amount_rule.py`
- `core/tests/test_repairs_status_flow.py`
- `core/tests/test_repairs_status_matrix_complete.py`
- `repairs-module/app/core_client.py`
- `repairs-module/app/routers/repairs.py`
- `repairs-module/app/templates/repair_detail.html`
- `repairs-module/tests/test_diagnostics_exit_amount_inline_ui.py`
- `repairs-module/tests/test_diagnostics_ready_amount_rule_ui.py`
- `repairs-module/tests/test_repair_diagnostics_ready_ui.py`
- `docs/stage05b_r2_inline_repair_amount_status_change.md`
- `reports/stage05b_r2_inline_repair_amount_status_change_report.md`
- `logs/2026-08-05.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE05B_R2_REPAIR_AMOUNT_INSIDE_STATUS_CHANGE_FORM_PROMPT.md`

## COMMIT
- Targeted commit: `Add repair amount to status change flow`

## PUSH
- Pushed to `origin main`

## FINAL_GIT_STATUS
- Clean working directory ready for audit.

## OWNER_CHECK_GUIDE
1. Open a repair in status «Диагностика» (e.g. `http://localhost:8040/repairs/46`).
2. Observe the status change form on the right panel. Notice input field **«Стоимость ремонта, ₽»**.
3. Select status **«Готов»**, enter amount `2800`, leave comment empty, click **«Сохранить новый статус»**.
4. Verify repair status becomes «Готов» and card displays `2800 ₽`.
5. Open another repair in status «Диагностика», select **«Отменён»**, enter amount `0`, submit. Verify status becomes «Отменён» and amount shows `0 ₽`.
6. Open another repair in «Диагностика», select **«Ожидает запчасти»**, enter amount `1500`, submit. Verify status becomes «Ожидает запчасти» with `1500 ₽`.
7. Leave amount field empty, attempt status change -> verify Russian error block.

## FINAL_STATUS
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_R2_INLINE_REPAIR_AMOUNT_STATUS_CHANGE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05C_WITHOUT_OWNER_ACCEPTANCE: true
