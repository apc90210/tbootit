# Stage05B-R1 Diagnostics-to-Ready Amount Rule Report

## STATUS
Stage05B-R1 completed successfully. Status transition from `diagnostics` to `ready` now requires ONLY that `estimated_repair_amount is not None`. All unit tests, empirical live HTTP runtime scenarios, stock/sales isolation, and live DB test isolation checks passed 100%.

## OWNER_REQUIREMENT
Transition from «Диагностика» -> «Готов» must NOT require status comment, diagnosis text, planned works text, or planned parts text. The ONLY mandatory condition is that `estimated_repair_amount` must be populated (`estimated_repair_amount is not None`). `0` is a valid, filled amount (`0 ₽`).

## PROMPT_DISCOVERY
- PROMPT_SEARCH_DONE: true
- PROMPT_USED: TECHNOREBOOT_STAGE05B_R1_DIAGNOSTICS_READY_REQUIRES_ONLY_AMOUNT_PROMPT.md
- PROMPT_SOURCE: C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE05B_R1_DIAGNOSTICS_READY_REQUIRES_ONLY_AMOUNT_PROMPT.md
- PROMPT_LOCAL_COPY: C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE05B_R1_DIAGNOSTICS_READY_REQUIRES_ONLY_AMOUNT_PROMPT.md
- PROMPT_SHA256: BD4F15602E1AE19925FEC156CDCB66E8092E2ED5BE37AB5BEF00BC38A0818B04

## PREFLIGHT
- Initial HEAD: bfae593198e7e0b5f5cbac5260d81ad0890afb04 (bfae593)
- Branch: main
- Worktree status: clean

## PREVIOUS_RULE
- Transition `diagnostics -> ready` previously required a non-empty status comment ("Для перехода из диагностики в статус 'Готов' требуется указать комментарий с описанием выполненных работ").

## NEW_RULE
- Transition `diagnostics -> ready` requires `estimated_repair_amount is not None`.
- Comment and text fields (`diagnosis_text`, `planned_works_text`, `planned_parts_text`) are 100% optional.
- Error message if `estimated_repair_amount is None`: `"Для перехода в статус «Готов» укажите предполагаемую стоимость ремонта. Можно указать 0 ₽."` (HTTP 400).

## ZERO_VALUE_HANDLING
- `0` is handled via explicit `is None` check. `0` is a valid integer amount (`0 ₽`) and allows the transition to `ready`.

## CORE_VALIDATION
- Updated `core/app/routers/repairs.py` (`update_repair_status`).
- Evaluates `if db_repair.estimated_repair_amount is None: raise HTTPException(400, detail=...)`.
- If blocked, status remains `diagnostics`, `closed_at` and `issued_at` remain null, no history or audit record created.

## UI_BEHAVIOR
- Option «Готов» is always visible in `diagnostics` status dropdown on `/repairs/{id}`.
- If amount is missing when user submits status change to `ready`, UI displays error message with button/link `"Указать стоимость ремонта"` leading to `/repairs/{id}/edit`.
- The old error message about mandatory comment is removed.

## OPTIONAL_TEXT_FIELDS
- `diagnosis_text`, `planned_works_text`, `planned_parts_text` remain optional and do not block status transition to `ready`.

## OPTIONAL_STATUS_COMMENT
- Comment field on status change form is optional. If provided, saved in `RepairStatusHistory.comment`. If omitted, saved as `None`.

## TESTS
- `core/tests/test_diagnostics_ready_amount_rule.py` (3 tests covering blocked null amount, zero amount success, amount 2800 success with optional comment).
- `core/tests/test_repairs_status_matrix_complete.py` (Updated to reflect Stage05B-R1 amount rule).
- `repairs-module/tests/test_diagnostics_ready_amount_rule_ui.py` (3 tests covering UI rendering, error alert with edit link, amount 0 success, amount 2800 success).
- `repairs-module/tests/test_repair_diagnostics_ready_ui.py` (Updated for Stage05B-R1 amount rule).
- All 4 test suites passed:
  - Core safe tests: 155/155 PASS
  - Inventory-sales-module: 110/110 PASS
  - Avito-module: 12/12 PASS
  - Repairs-module: 25/25 PASS
  - Total: 302/302 PASS (100% Green)

## RUNTIME_EMPTY_AMOUNT
- Repair created (`ТЕСТ Stage05B-R1 EMPTY AMOUNT`), transitioned to `diagnostics`.
- Attempted transition to `ready` with `estimated_repair_amount=null` -> Blocked with HTTP 400 and detail `"Для перехода в статус «Готов» укажите предполагаемую стоимость ремонта. Можно указать 0 ₽."`. Status remained `diagnostics`.

## RUNTIME_ZERO
- Set `estimated_repair_amount=0`, left text fields and comment empty.
- Transitioned `diagnostics -> ready` -> Success (HTTP 200, status `ready`, `closed_at=null`, `issued_at=null`).

## RUNTIME_2800
- Repair created (`ТЕСТ Stage05B-R1 AMOUNT 2800`), set `estimated_repair_amount=2800`, left text fields empty.
- Transitioned `received -> diagnostics -> ready` -> Success (HTTP 200, status `ready`).

## LIVE_DB_TEST_ISOLATION
- LIVE_DB_SHA256_BEFORE_TESTS: `f7cb04f31b7708e878b2a5cc1602667ea2d5b040b6528bef0a42364e485c9bb1`
- LIVE_DB_SHA256_AFTER_TESTS: `f7cb04f31b7708e878b2a5cc1602667ea2d5b040b6528bef0a42364e485c9bb1`
- Record counts (products: 56, sales: 43, customers: 21, repairs: 41, history: 81, audit: 261) remained 100% identical before and after test suites.

## SAFETY_SCANS
- Scan 1 (destructive queries): Clean (0 production matches)
- Scan 2 (direct DB access in repairs-module): Clean (0 matches)
- Scan 3 (tracked DB/cache files): Clean (0 matches)

## FILES_CHANGED
- `core/app/routers/repairs.py`
- `core/tests/test_diagnostics_ready_amount_rule.py`
- `core/tests/test_repairs_status_matrix_complete.py`
- `repairs-module/app/routers/repairs.py`
- `repairs-module/app/templates/repair_detail.html`
- `repairs-module/tests/test_diagnostics_ready_amount_rule_ui.py`
- `repairs-module/tests/test_repair_diagnostics_ready_ui.py`
- `docs/stage05b_r1_diagnostics_ready_amount_rule.md`
- `reports/stage05b_r1_diagnostics_ready_amount_rule_report.md`
- `logs/2026-08-05.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE05B_R1_DIAGNOSTICS_READY_REQUIRES_ONLY_AMOUNT_PROMPT.md`

## COMMIT
- Targeted commit: `Require repair amount before ready status`

## PUSH
- Pushed to `origin main`

## FINAL_GIT_STATUS
- Clean working directory ready for audit.

## OWNER_CHECK_GUIDE
1. Open a repair in status «Диагностика» (e.g. `http://localhost:8040/repairs/41`).
2. Ensure estimated repair amount is empty.
3. Attempt status change to «Готов».
4. Verify transition is blocked with message `"Для перехода в статус «Готов» укажите предполагаемую стоимость ремонта. Можно указать 0 ₽."` and button `"Указать стоимость ремонта"`.
5. Set amount to `0`.
6. Leave diagnosis, works, parts, and comment empty.
7. Transition status to «Готов».
8. Verify status becomes «Готов» successfully.
9. Repeat with amount `2800`.

## FINAL_STATUS
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_R1_DIAGNOSTICS_READY_AMOUNT_RULE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05C_WITHOUT_OWNER_ACCEPTANCE: true
