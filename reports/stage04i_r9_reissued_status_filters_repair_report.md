# Stage04I-R9 Reissued Status and Filters Repair Report

## STATUS
TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIRED_READY_FOR_OWNER_RECHECK

## WHY_R8_WAS_NOT_ACCEPTED
- R8 identified that reissued sales must have domain status `reissued` (not `completed`), so that filters, badges, receipts, and revenue reports properly handle reissued sales.

## ROOT_CAUSE
- Reissued sales need explicit `reissued` status semantics across API endpoints, startup migrations, UI filter buttons, detail badges, and receipt headers.

## DOMAIN_STATUS_RULES
- `completed`: Active regular sale (`source_sale_id is None`)
- `canceled`: Canceled sale (stock returned)
- `superseded`: Original historical sale replaced by reissue (`superseded_by_sale_id` set)
- `reissued`: Active sale created from a canceled sale (`source_sale_id` set)

## LEGACY_MISCLASSIFIED_SALES
- Query: `SELECT COUNT(*) FROM sales WHERE source_sale_id IS NOT NULL AND status = 'completed'`
- `MISCLASSIFIED_REISSUED_BEFORE`: 0
- `MISCLASSIFIED_REISSUED_AFTER`: 0

## BACKUP
- Backup created prior to migration: `C:\tbootit-data-recovery\stage04i-r9\host_data_db_technoreboot.db`

## NORMALIZATION
- Idempotent startup migration in `core/app/main.py` and `core/app/services/sale_status_repair.py`.
- SQL statement: `UPDATE sales SET status = 'reissued' WHERE source_sale_id IS NOT NULL AND status = 'completed'`
- Updated count: 0 rows (DB clean). Subsequent runs update 0 rows.

## REISSUE_FLOW_REPAIR
- `POST /api/sales/{sale_id}/reissue` sets `status = "reissued"` on new sale and `status = "superseded"` on old sale.

## FILTERS
- Filter links: `/sales?status=completed`, `/sales?status=canceled`, `/sales?status=superseded`, `/sales?status=reissued`.
- Completed filter excludes `reissued` sales.
- Reissued filter includes `reissued` sales.

## DETAIL_UI
- `reissued` status displays blue info banner "✓ Повторно оформленная продажа" with link to `№{source_sale_id}`.
- `superseded` status displays gray info banner "ⓘ Продажа заменена" with link to `№{superseded_by_sale_id}`.

## RECEIPTS
- `reissued` receipt displays header banner "ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА (НА ОСНОВЕ ПРОДАЖИ №...)".
- `superseded` receipt displays header banner "АРХИВНЫЙ ЧЕК — ПРОДАЖА №... ЗАМЕНЕНА (ПОВТОРНАЯ ПРОДАЖА №...)".

## REPORTS
- Included statuses: `completed`, `reissued`.
- Excluded statuses: `canceled`, `superseded`.
- Reissued sales counted in revenue exactly ONCE.

## TESTS
- Core safe (`scripts/test_core_safe.ps1`): **122 passed**
- Inventory (`docker compose exec inventory-sales-module pytest`): **94 passed**
- Avito (`docker compose exec avito-module pytest`): **12 passed**

## LIVE_DB_PRESERVATION
- Before tests: `SHA256: 54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- After tests: `SHA256: 54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- Result: **100% Identical SHA256 and record counts before & after unit tests.**

## RUNTIME_REISSUE
- Product #54 created, Sale #40 created, canceled, and reissued as Sale #41.
- Sale #40: `status = superseded`, `superseded_by = 41`.
- Sale #41: `status = reissued`, `source = 40`.

## RUNTIME_FILTERS
- `GET /sales?status=completed` -> Sale #41 absent.
- `GET /sales?status=reissued` -> Sale #41 present.
- `GET /sales?status=superseded` -> Sale #40 present.

## RUNTIME_REPORTS
- Revenue includes Sale #41 once (1234.0 ₽), excludes Sale #40.

## RUNTIME_RECEIPTS
- Sale #41 receipt: `ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА (НА ОСНОВЕ ПРОДАЖИ №40)`.
- Sale #40 receipt: `АРХИВНЫЙ ЧЕК — ПРОДАЖА №40 ЗАМЕНЕНА (ПОВТОРНАЯ ПРОДАЖА №41)`.

## SAFETY_SCAN
- Destructive DB calls in tracked test code: 0 matches
- DB/Cache/Temp files in Git: 0 matches
- Direct DB access in inventory-sales-module: 0 matches
- Sensitive keys/env files: 0 matches

## FILES_CHANGED
- `core/app/main.py`
- `core/app/services/sale_status_repair.py`
- `core/tests/test_sale_reissue_status_semantics.py`
- `inventory-sales-module/tests/test_reissued_status_ui.py`
- `docs/stage04i_r9_reissued_status_filters_repair.md`
- `reports/stage04i_r9_reissued_status_filters_repair_report.md`
- `logs/2026-08-03.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIR_PROMPT.md`

## COMMIT
- Message: "Repair reissued sale status and filters"

## PUSH
- Destination: origin/main

## FINAL_GIT_STATUS
- Clean working tree

## OWNER_RECHECK_GUIDE
1. Open `http://localhost:8030/sales?status=reissued` -> Verify reissued sales (e.g. #39, #41) appear with blue "Повторно оформлена" badge.
2. Open `http://localhost:8030/sales?status=completed` -> Verify reissued sales do NOT appear under completed filter.
3. Open `http://localhost:8030/sales/41` -> Verify blue info box "✓ Повторно оформленная продажа" with link to source sale №40.
4. Open `http://localhost:8030/sales/41/receipt` -> Verify header banner "ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА (НА ОСНОВЕ ПРОДАЖИ №40)".

## FINAL_STATUS
TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIRED_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
