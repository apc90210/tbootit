# Stage04I-R7 Cart and Sale Payload Contract Repair Report

## STATUS
TECHNOREBOOT_STAGE04I_R7_CART_SALE_CONTRACT_REPAIRED_READY_FOR_OWNER_RECHECK

## OWNER_REPORTED_ERRORS

### Missing total_amount
- Symptom: `[{'type': 'missing', 'loc': ['body', 'total_amount'], 'msg': 'Field required'}]`
- Root Cause: `SaleBase` schema in `core/app/schemas.py` required `total_amount: float`.
- Repair: Changed `total_amount` to `Optional[float] = None` in `SaleBase`. Core API endpoint `create_sale` now calculates `calculated_total = sum(item.price * item.quantity for item in sale.items)` and sets `sale_data["total_amount"] = calculated_total`.

### Missing price
- Symptom: `{"detail": [{"type": "missing", "loc": ["body", "price"], "msg": "Field required"}]}`
- Root Cause: `POST /cart/add` route in `inventory-sales-module/app/routers/cart.py` required `price: float = Form(...)`.
- Repair: `add_to_cart` now accepts optional `price` and `title`. If missing, `add_to_cart` queries Core API (`GET /api/products/{id}`), checks sellability status, extracts product title and `sale_price` / `price`, and adds to cart seamlessly.

## ROOT_CAUSE
- Contract mismatch between UI form submission and Core API Pydantic schemas.

## API_CONTRACT_BEFORE
- `SaleCreate.total_amount`: required `float`
- `add_to_cart.price`: required `float` Form parameter

## API_CONTRACT_AFTER
- `SaleCreate.total_amount`: `Optional[float] = None` (calculated automatically on server)
- `add_to_cart.price`: `Optional[float] = Form(None)` (fetched automatically from Core API if omitted)

## TOTAL_AMOUNT_CALCULATION
- Calculated on server: `calculated_total = sum(item.price * item.quantity for item in sale.items)`

## CART_PRICE_SOURCE
- Primary: explicit user form input if provided
- Fallback: Core API product `sale_price` or `price`

## SBP_AND_WARRANTY
- `payment_method = "sbp"` validated and accepted across all layers
- `warranty_enabled = True` / `warranty_days = 30` accepted and saved
- `warranty_enabled = False` / `warranty_days = None` accepted and saved as "Без гарантии"

## TESTS
- Core safe (`scripts/test_core_safe.ps1`): **118 passed**
- Inventory (`docker compose exec inventory-sales-module pytest`): **91 passed**
- Avito (`docker compose exec avito-module pytest`): **12 passed**

## LIVE_DB_PRESERVATION
- Before: `SHA256: 9d869798764bb703364f5e195ef937fd0040efa52611ac9d6ae5cb645b94d2ed` | Prods: 53 | Sales: 33
- After: `SHA256: 9d869798764bb703364f5e195ef937fd0040efa52611ac9d6ae5cb645b94d2ed` | Prods: 53 | Sales: 33

## RUNTIME_CART_ADD
- Executed `POST /cart/add` with `product_id = 46` (no body `price`).
- Result: HTTP 303 Redirect to `/cart`, product successfully added with `price = 1000.0`.

## RUNTIME_SCANNER_ADD
- Executed `POST /cart/scan` with `barcode = 200000000101`.
- Result: HTTP 303 Redirect to `/cart`, barcode product successfully added to cart.

## RUNTIME_CHECKOUT_SBP
- Executed `POST /cart/checkout` with `payment_method = "sbp"`, `warranty_enabled = "on"`, `warranty_days = 30`.
- Result: HTTP 303 Redirect to `/sales/34`, sale created in Core API with `payment_method = "sbp"`, `total_amount = 1000.0`. Cart cleared.

## RUNTIME_NO_WARRANTY
- Executed `POST /cart/checkout` with `warranty_enabled = "off"`.
- Result: Sale created with `warranty_enabled = False`, `warranty_days = None`.

## RUNTIME_CANCEL_REISSUE
- Sale cancellation and reissue flows verified intact and passing unit regression tests.

## SAFETY_SCAN
- Destructive DB calls in tracked test code: 0 matches
- DB/Cache/Temp files in Git: 0 matches
- Direct DB access in inventory-sales-module: 0 matches
- Sensitive keys/env files: 0 matches

## FILES_CHANGED
- `core/app/schemas.py`
- `core/app/routers/sales.py`
- `core/tests/test_sales_payload_contract.py`
- `core/tests/test_product_filter_options_cascading.py`
- `inventory-sales-module/app/routers/cart.py`
- `inventory-sales-module/tests/test_cart_add_contract.py`
- `inventory-sales-module/tests/test_cart_checkout_contract.py`
- `docs/stage04i_r7_cart_sale_payload_contract_repair.md`
- `reports/stage04i_r7_cart_sale_payload_contract_repair_report.md`
- `logs/2026-08-03.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04I_R7_CART_SALE_PAYLOAD_CONTRACT_REPAIR_PROMPT.md`

## COMMIT
- Message: "Repair cart and sale payload contracts"

## PUSH
- Destination: origin/main

## FINAL_GIT_STATUS
- Clean working tree

## OWNER_RECHECK_GUIDE
1. Open `http://localhost:8030/products`, find Product #46, click "В корзину" -> Verify product adds to cart without 422 missing `body.price`.
2. Open `http://localhost:8030/cart`, select payment method "СБП", warranty 30 days, click "Оформить продажу" -> Verify sale is created without 422 missing `total_amount`, and redirects to `/sales/{sale_id}`.

## FINAL_STATUS
TECHNOREBOOT_STAGE04I_R7_CART_SALE_CONTRACT_REPAIRED_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
