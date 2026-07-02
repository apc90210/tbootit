# Stage 04E-R Sales UI Owner Check Repair Report

## STATUS

TECHNOREBOOT_STAGE04E_R_SALES_UI_OWNER_CHECK_REPAIR_READY_FOR_OWNER_RECHECK

## OWNER_REPORTED_ERROR

Text: Ошибка Core API
Likely URL: `/products`
Reproduced: yes

## ROOT_CAUSE

The `core_client.get_products()` function issued a request to `GET /api/products` without a trailing slash. FastAPI returned a 307 Temporary Redirect to `/api/products/`. Since the `httpx` client was not configured to follow redirects, it received the 307 status code and treated it as an error, which the template then surfaced as a generic "Ошибка Core API" message.

## FIX_IMPLEMENTED

Added the trailing slash to the `get_products` endpoint URL in `inventory-sales-module/app/core_client.py` (`/api/products/`), ensuring the request successfully hits the endpoint directly without triggering a redirect.

## TESTS_ADDED_OR_UPDATED

Added `test_owner_reported_core_api_error_reproduced_and_fixed` to `inventory-sales-module/tests/test_core_client.py` to ensure `get_products` explicitly requests the URL with a trailing slash, preventing 307 redirect errors from bubbling up to the UI.

## MANUAL_SMOKE

Created a test product (ID 71) via Core API.
- `/products` loaded successfully without the error.
- `/sales/new?product_id=71` loaded correctly.
- Created a sale via `POST /sales/create`.
- Product 71 status updated to `sold` in Core DB.
- Attempting to sell Product 71 again correctly blocked by the UI ("Товар нельзя продать в текущем статусе").

## REGRESSION_CHECKS

- `core` tests: 34 passed
- `inventory-sales-module` tests: 27 passed

## SAFETY_SCAN

No direct DB access found in `inventory-sales-module`.
No browser automation imports found.
Data volumes correctly ignored by Git.

## FILES_CHANGED

- `inventory-sales-module/app/core_client.py`
- `inventory-sales-module/tests/test_core_client.py`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04E_R_SALES_UI_OWNER_CHECK_REPAIR_PROMPT.md`
- `docs/stage04e_r_sales_ui_owner_check_repair.md`
- `reports/stage04e_r_sales_ui_owner_check_repair_report.md`
- `logs/2026-07-02.md`

## PROCESS_NOTES

No `git commit --amend` was used during this repair stage. Only a single new normal commit will be created for the repair.

## OWNER_RECHECK_GUIDE

1. Open `http://127.0.0.1:8030/products`
2. Verify that the list of products loads correctly and there is no "Ошибка Core API".
3. Find a product in status "В наличии" or "В резерве".
4. Click "Продать".
5. Fill the form and complete the sale.
6. Verify you are redirected to the sale detail page.

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R_SALES_UI_OWNER_CHECK_REPAIR_READY_FOR_OWNER_RECHECK
