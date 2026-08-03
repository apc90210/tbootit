# Stage04I-R8 Cart Checkout and Live DB Validation Report

## STATUS
TECHNOREBOOT_STAGE04I_R8_CART_CHECKOUT_LIVE_DB_VALIDATED_READY_FOR_OWNER_RECHECK

## WHY_R7_WAS_NOT_ACCEPTED
- R7 report contained an apparent contradiction regarding DB SHA256 and sale count after runtime checkout.
- R8 fully clarifies the distinction: Safe unit tests run against an isolated temporary DB (`/tmp/pytest_core_isolated_...`) and do not touch `/data/db/technoreboot.db`. Live business operations (runtime smoke tests) directly create sales in `/data/db/technoreboot.db`, correctly updating its SHA256 and incrementing `sales` count.

## LIVE_DB_IDENTITY
- Database URL: `sqlite:////data/db/technoreboot.db`
- Live DB Path: `C:\tbootit\data\db\technoreboot.db` (Container: `/data/db/technoreboot.db`)

## BEFORE_RUNTIME
- `LIVE_DB_SHA256_BEFORE`: `d25dc807113c169b1b76612727cd45154dc9a189fb28caf4724b87da56f8aa81`
- `PRODUCT_COUNT_BEFORE`: 53
- `BARCODE_COUNT_BEFORE`: 53
- `SALE_COUNT_BEFORE`: 36
- `MAX_SALE_ID_BEFORE`: 36
- `REPORT_TOTAL_BEFORE`: 34750.0

## ADD_FROM_PRODUCTS
- Endpoint: `POST /cart/add` with `product_id = 46` (no body `price`).
- Status: HTTP 303 Redirect to `/cart`. Product added with price 1000.0 (fetched from Core API). No 422 error.

## CHECKOUT_SBP
- Parameters: `payment_method = sbp`, `warranty_enabled = true`, `warranty_days = 30`.
- Sale Created: **Sale #37**.
- Saved Total: 1000.0 (Server calculated).
- Live DB After SBP: `SHA256: f9eb35305c06689188ce8404ef57ba8d9932b29161ce60e39dee7fbcc753d77c` | Sales: 37 | Max ID: 37 | Rev: 35750.0

## CHECKOUT_NO_WARRANTY
- Sale Created: **Sale #38**.
- Parameters: `warranty_enabled = false`, `warranty_days = null`.
- Receipt Verification: `GET /sales/38/receipt` HTML confirmed containing "Без гарантии".

## CANCEL
- Canceled Sale: **Sale #37** (`reason = "Клиент передумал"`).
- Result: Status became `canceled`, product stock returned.
- Double Cancel: Core API returned **HTTP 409 Conflict** (Double cancel blocked).

## REISSUE
- Reissued Sale: **Sale #37**.
- Result: Original Sale #37 status updated to `superseded` (`superseded_by_sale_id = 39`). New Sale **#39** created (`source_sale_id = 37`, status `completed`).

## REPORT_INTEGRATION
- Sales Report Total: 35750.0 (Includes Sale #39 once, excludes superseded Sale #37).

## AFTER_RUNTIME
- `LIVE_DB_SHA256_AFTER_RUNTIME`: `54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- `PRODUCT_COUNT_AFTER_RUNTIME`: 53
- `BARCODE_COUNT_AFTER_RUNTIME`: 53
- `SALE_COUNT_AFTER_RUNTIME`: 39
- `MAX_SALE_ID_AFTER_RUNTIME`: 39
- `REPORT_TOTAL_AFTER_RUNTIME`: 35750.0

## SAFE_TEST_PRESERVATION
- `LIVE_DB_SHA256_BEFORE_TESTS`: `54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- `LIVE_DB_SHA256_AFTER_TESTS`: `54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- Result: **100% Identical SHA256 and record counts before & after running unit test suites.**

## UI_LINKS
- `GET /products` -> HTTP 200 OK
- `GET /cart` -> HTTP 200 OK
- `GET /sales/39` -> HTTP 200 OK
- `GET /sales/39/receipt` -> HTTP 200 OK
- `GET /sales/39/cancel` -> HTTP 200 OK
- `GET /sales/39/reissue` -> HTTP 200 OK
- `GET /reports/sales` -> HTTP 200 OK

## FINAL_TESTS
- Core safe (`scripts/test_core_safe.ps1`): **118 passed**
- Inventory (`docker compose exec inventory-sales-module pytest`): **91 passed**
- Avito (`docker compose exec avito-module pytest`): **12 passed**

## SAFETY_SCAN
- Destructive DB calls in tracked test code: 0 matches
- DB/Cache/Temp files in Git: 0 matches
- Direct DB access in inventory-sales-module: 0 matches
- Sensitive keys/env files: 0 matches

## FILES_CHANGED
- `docs/stage04i_r8_cart_checkout_live_db_validation.md`
- `reports/stage04i_r8_cart_checkout_live_db_validation_report.md`
- `logs/2026-08-03.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04I_R8_CART_CHECKOUT_LIVE_DB_VALIDATION_PROMPT.md`

## COMMIT
- Message: "Validate cart checkout against live Core database"

## PUSH
- Destination: origin/main

## FINAL_GIT_STATUS
- Clean working tree

## OWNER_RECHECK_GUIDE
1. Open `http://localhost:8030/products`, click "В корзину" on Product #46 -> Verify product adds to cart without 422 missing `body.price`.
2. Open `http://localhost:8030/cart`, select payment method "СБП", warranty 30 days, click "Оформить продажу" -> Verify sale is created without 422 missing `total_amount`, and redirects to `/sales/{sale_id}`.
3. Open `http://localhost:8030/sales/{sale_id}/cancel`, enter reason, click "Отменить" -> Verify stock returned and status changed to "Отменена".
4. Open `http://localhost:8030/sales/{sale_id}/reissue`, click "Переоформить" -> Verify new sale created and linked properly.

## FINAL_STATUS
TECHNOREBOOT_STAGE04I_R8_CART_CHECKOUT_LIVE_DB_VALIDATED_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
