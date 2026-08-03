# Stage05A-R5 Editable Diagnostic Fee Report

## STATUS
Stage05A-R5 completed successfully. All unit tests, UI features, print document formatting, and live database migrations verified.

## OWNER_REQUIREMENT
- Added diagnostic fee field to repair intake form (`http://localhost:8040/repairs/new`), defaulting to 500 ₽.
- Allowed employee to edit diagnostic fee amount during intake or when editing active repairs.
- Persisted repair-specific diagnostic fee in Core database (`repair_orders.diagnostic_fee`).
- Rendered exact stored diagnostic fee across Core API, intake form, edit form, repair detail card, printable work order, detachable ticket, and detailed terms.

## PROMPT_DISCOVERY
- PROMPT_SEARCH_DONE: true
- PROMPT_USED: TECHNOREBOOT_STAGE05A_R5_EDITABLE_DIAGNOSTIC_FEE_ACROSS_DOCUMENTS_PROMPT.md
- PROMPT_SOURCE: C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE05A_R5_EDITABLE_DIAGNOSTIC_FEE_ACROSS_DOCUMENTS_PROMPT.md
- PROMPT_LOCAL_COPY: C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE05A_R5_EDITABLE_DIAGNOSTIC_FEE_ACROSS_DOCUMENTS_PROMPT.md
- PROMPT_SHA256: b197b8c9168073fbdd81f49f172752b3d09c9b56d8d6433b07fc7cf57b67f461

## PREFLIGHT
- Initial HEAD: 277e6801474931c1f181f71a976a15c2bc1a3e94
- Branch: main
- Worktree clean: true (before edits)

## MONEY_CONVENTION
- Used Float / integer-ruble representation matching project convention for `Product.price` and `Sale.total_amount`.
- Input field uses `step="1" min="0"`.

## FIELD_NAME
- Database & API field name: `diagnostic_fee`

## DATABASE_MIGRATION
- Additive SQLite column `diagnostic_fee` added to `repair_orders` table (Float, NOT NULL, DEFAULT 500.0).
- Idempotent startup migration in `core/app/services/repair_migration.py`.
- Pre-migration backup created at `C:\tbootit-data-backups\stage05a-r5\20260803_124821\technoreboot.db` (SHA256: `8c8b99c4f1b9c4c7949e1cbbbffe6ae3d9a672e242ebf302361e23445387b9df`).

## EXISTING_REPAIR_BACKFILL
- All 26 existing repair orders in live DB backfilled with `diagnostic_fee = 500.0`.
- 0 NULL values remain.

## DEFAULT_SOURCE
- Centralized in `GET /api/repairs/options` returning `"default_diagnostic_fee": 500`.
- `repairs-module` fetches default from Core options API.

## CORE_API
- `POST /api/repairs/`: Accepts `diagnostic_fee`, defaults to 500.0 if omitted.
- `GET /api/repairs/`: Returns `diagnostic_fee` for each repair item.
- `GET /api/repairs/{id}` & `/by-number/{number}`: Includes `diagnostic_fee`.
- `PATCH /api/repairs/{id}`: Allows updating `diagnostic_fee` for active repairs (blocks terminal `issued`/`canceled` repairs with HTTP 409 Conflict).
- `GET /api/repairs/options`: Includes `default_diagnostic_fee: 500`.

## CREATE_FORM
- Form at `/repairs/new` contains "Стоимость диагностики, ₽" with value default `500`.
- Custom values (e.g. 750, 800) and zero (0) are correctly passed and saved.
- Russian validation error displayed on negative inputs: "Стоимость диагностики не может быть отрицательной".

## EDIT_FORM
- Form at `/repairs/{id}/edit` displays saved diagnostic fee (e.g. 800 or 0) without resetting to default 500.
- Terminal repairs (`issued`/`canceled`) block editing.

## REPAIR_DETAIL
- Page at `/repairs/{id}` displays "Стоимость диагностики: N ₽" formatted with integer rubles.

## PRINT_DOCUMENT
- Jinja2 template `repair_print_order.html` dynamically renders `repair.diagnostic_fee`.
- Replaced static "500 рублей" hardcode with `{{ repair.diagnostic_fee | int }} рублей`.

## DETACHABLE_TICKET
- Detachable ticket on Page 1 renders the exact same `repair.diagnostic_fee` as the main agreement block.

## DETAILED_TERMS
- Page 2 terms render the repair-specific diagnostic fee.

## HARDCODE_SCAN
- FORBIDDEN_PRODUCTION_DIAGNOSTIC_FEE_HARDCODE_MATCHES: 0

## AUDIT_EVENTS
- `repair.created` captures `diagnostic_fee`.
- `repair.updated` captures `old_value` and `new_value` with `diagnostic_fee` changes.

## CORE_TESTS
- `core/tests/test_repair_diagnostic_fee.py` (7 tests covering default, custom, 0, negative validation, reads, patch, terminal protection, audit, options).
- Result: 147/147 PASS.

## REPAIRS_TESTS
- `repairs-module/tests/test_repair_diagnostic_fee_ui.py` (covers UI new form defaults, submission, validation error, edit form, detail display, terminal block).
- Result: 15/15 PASS.

## PRINT_TESTS
- `repairs-module/tests/test_repair_print_order.py` (covers Repair A 500 fee, Repair B 800 fee, absence of 500 text in Repair B).
- Result: PASS.

## RUNTIME_DEFAULT_500
- Verified repair created without diagnostic fee receives 500 ₽.

## RUNTIME_CUSTOM_800
- Verified repair created with 800 ₽ renders 800 in API, detail, print main block, and detachable ticket.

## RUNTIME_EDIT_650
- Verified editing active repair from 800 to 650 updates API, card, and print view, while audit event `repair.updated` is created.

## RUNTIME_ZERO
- Verified diagnostic fee 0 ₽ is preserved across creation, edit, card, and print document without reverting to 500.

## LIVE_DB_TEST_ISOLATION
- Verified live DB SHA256 (`895497a9c3ef29bfcc06d4ec6e03f565285b4a4f32037fef38270e190b7370f2`) and record counts (products: 56, sales: 43, customers: 13, repairs: 26) remained untouched by test execution.

## SAFETY_SCANS
- Scan 1 (drop_all/DROP TABLE/mass DELETE): Clean (0 production matches)
- Scan 2 (Direct DB access in repairs-module): Clean (0 matches)
- Scan 3 (Tracked DB/cache files): Clean (0 matches)
- Scan 4 (Production diagnostic 500 hardcode): Clean (0 forbidden matches)

## FILES_CHANGED
- `core/app/models.py`
- `core/app/schemas.py`
- `core/app/routers/repairs.py`
- `core/app/services/repair_migration.py`
- `core/tests/test_repair_diagnostic_fee.py`
- `repairs-module/app/routers/repairs.py`
- `repairs-module/app/templates/repair_new.html`
- `repairs-module/app/templates/repair_edit.html`
- `repairs-module/app/templates/repair_detail.html`
- `repairs-module/app/templates/repair_print_order.html`
- `repairs-module/tests/test_repair_diagnostic_fee_ui.py`
- `repairs-module/tests/test_repair_print_order.py`
- `docs/stage05a_r5_editable_diagnostic_fee.md`
- `reports/stage05a_r5_editable_diagnostic_fee_report.md`
- `logs/2026-08-03.md`

## COMMIT
- Pending targeted git commit: `Add editable repair diagnostic fee`

## PUSH
- Pending push to `origin main`

## FINAL_GIT_STATUS
- Clean targeted files ready for commit.

## LEGAL_TEXT_CHANGE:
ONLY_DIAGNOSTIC_FEE_VALUE_BECAME_REPAIR_SPECIFIC

## OWNER_CHECK_GUIDE
1. Open http://localhost:8040/repairs/new
2. Check field "Стоимость диагностики, ₽" pre-filled with 500.
3. Submit repair without changing amount -> verify 500 ₽ on card and print document.
4. Create second repair with diagnostic fee set to 800 -> verify 800 ₽ on card, print document, and detachable ticket.
5. Edit active repair from 800 to 650 -> verify 650 ₽ on card and newly opened print document.
6. Verify first repair remains 500 ₽.
7. Verify fee value 0 ₽ is preserved.
8. Verify negative fee raises Russian error message.

## FINAL_STATUS
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R5_EDITABLE_DIAGNOSTIC_FEE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05B_WITHOUT_OWNER_ACCEPTANCE: true
