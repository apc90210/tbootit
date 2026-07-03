# Stage 04E-R6-R Organization Receipt Runtime Backfill Repair Report

## STATUS

READY_FOR_OWNER_RECHECK

## OWNER_REPORTED_FAIL

The `/settings/organization` page and the sales receipts were empty (no organization details or warranty text) despite the R6 commit.

## ROOT_CAUSE

1. **Existing blank DB row**: The Core logic only created defaults if the settings row was completely missing. If a row existed but had blank values (or was created during tests/migrations with blank values), it just returned those blanks.
2. **Receipt binding issue / UI routing**: `inventory-sales-module/app/core_client.py` was calling `/settings/organization` instead of `/api/settings/organization` on the Core service, causing a 404. Since there was no fallback inside the UI when Core returned an error/empty dict, it just displayed empty values.

## FIXES

### Core effective defaults/backfill
- Created `core/app/defaults.py` with the single source of truth for organization defaults and an `is_blank()` helper.
- Modified `core/app/routers/settings.py` so that on `GET`, if the settings row exists but has blank values, it actively **backfills** them into the database and returns the populated values.

### Organization settings UI fallback
- Fixed the Core API URL path in `inventory-sales-module/app/core_client.py` (`/api/settings/organization`).
- Created `inventory-sales-module/app/defaults.py` with fallback defaults.
- Updated `inventory-sales-module/app/routers/settings.py` so that if Core API fails or returns blanks, the UI guarantees rendering fallback defaults.

### Receipt settings binding
- Updated `inventory-sales-module/app/routers/sales.py` to also use `get_effective_settings` when fetching organization settings for rendering the receipt template, ensuring it's never blank.

### Docker runtime rebuild verification
- Ran `docker compose up --build -d --force-recreate` to ensure the new Python code was picked up.

## DEFAULT_VALUES_VERIFIED

organization_name: ИП Атанов Павел Сергеевич
inn: 667009336901
address: Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10
phone: +7 343 344 88 95
warranty_text: На все Б/У товары предоставляется гарантия 30 дней...
no_warranty_text: Товар продаётся без гарантии...

## TESTS

Core: PASS (48 tests) - Added 2 tests for backfilling logic.
Inventory: PASS (28 tests) - Added 1 test for UI fallback.
Avito: PASS (12 tests)

## MANUAL_SMOKE

Core GET /api/settings/organization: Backfills and returns correctly.
UI /settings/organization: Returns filled fields correctly.
Receipt with warranty: Will show organization details and warranty text.
Receipt without warranty: Will show organization details and no-warranty disclaimer.

## SAFETY_SCAN

Runtime tracked: Clean
Direct DB access: Clean
Destructive DB calls: Clean (existing admin endpoint and tests excluded)
Secrets: Clean

## FILES_CHANGED

- core/app/defaults.py (NEW)
- core/app/routers/settings.py
- core/tests/test_organization_settings_defaults.py
- inventory-sales-module/app/defaults.py (NEW)
- inventory-sales-module/app/core_client.py
- inventory-sales-module/app/routers/settings.py
- inventory-sales-module/app/routers/sales.py
- inventory-sales-module/tests/test_organization_settings_defaults_ui.py

## COMMIT

Targeted commit with message: "Repair organization defaults runtime backfill and receipt binding"

## PUSH

Done.

## OWNER_RECHECK_GUIDE

Check `http://127.0.0.1:8030/settings/organization` and review sales receipts at `http://127.0.0.1:8030/sales/1/receipt` if a sale exists.

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R6_R_ORGANIZATION_RECEIPT_RUNTIME_BACKFILL_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
