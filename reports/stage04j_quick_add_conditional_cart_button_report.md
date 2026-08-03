# Stage04J Quick Add and Conditional Cart Button Report

## STATUS
TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_READY_FOR_OWNER_CHECK

## OWNER_REQUIREMENT
- Add to cart button on product list `/products` adds item to session cart without redirecting to `/cart` or reloading the page.
- Conditional "Перейти в корзину (N)" button appears next to title header when cart is not empty.
- When cart is empty, "Перейти в корзину" button is hidden.

## PREVIOUS_FLOW
- Clicking "В корзину" submitted standard HTML form and performed 303 Redirect to `/cart`.
- Users lost page scroll position, pagination, and filter context.

## NEW_FLOW
- AJAX/Fetch submission to `/cart/add-quick` (or `/cart/add` with AJAX header).
- Client script (`cart_quick_add.js`) intercepts form submit, disables button temporarily ("Добавляем..."), updates cart counter button dynamically ("Перейти в корзину (N)"), shows brief confirmation ("✓ Добавлено"), and preserves scroll/filters.

## QUICK_ADD_ENDPOINT
- `POST /cart/add-quick`
- Success JSON: `{"ok": true, "message": "...", "cart_items_count": 3, "cart_lines_count": 2, "product_id": 55, "product_quantity_in_cart": 1}`
- Error JSON: `{"ok": false, "message": "...", "cart_items_count": 2}` with HTTP status 400/404/409/502.

## SESSION_CART_COUNTS
- `cart_items_count`: total item units count.
- `cart_lines_count`: total unique product lines count.

## CONDITIONAL_CART_BUTTON
- HTML element: `<a id="go-to-cart-button" href="/cart">Перейти в корзину (<span>N</span>)</a>`
- Display condition: `cart_items_count > 0`. Hidden when empty (`display: none;`).

## ERROR_HANDLING
- Reserved, sold, draft, zero quantity, wrong location, non-existent products fail with clear Russian error toast.
- Session cart state and counter remain untouched.

## ACCESSIBILITY
- Toast element contains `aria-live="polite"`.
- Double-click protection via button disabling during fetch.

## FALLBACK_WITHOUT_JS
- Standard form submission sends hidden `return_url`.
- Redirects to return_url (e.g. `/products?...`) instead of `/cart` if non-AJAX.

## TESTS
- Core safe (`scripts/test_core_safe.ps1`): **122 passed**
- Inventory (`docker compose exec inventory-sales-module pytest`): **106 passed**
- Avito (`docker compose exec avito-module pytest`): **12 passed**

## LIVE_DB_PRESERVATION
- Before tests: `SHA256: 54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- After tests: `SHA256: 54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- Result: **100% Identical SHA256 before & after unit tests.**

## RUNTIME_EMPTY_CART
- Verified `go-to-cart-button` hidden when cart is empty.

## RUNTIME_FIRST_ADD
- Product #55 added via quick add -> button updated to `Перейти в корзину (1)` and revealed.

## RUNTIME_SECOND_ADD
- Product #56 added via quick add -> button updated to `Перейти в корзину (2)`.

## RUNTIME_FILTER_PRESERVATION
- Filters `?location=store&q=Quick` preserved across quick add operations without reload.

## RUNTIME_ERROR
- Invalid product ID 999999 returns HTTP 404 with Russian message. Counter remains 2.

## RUNTIME_CHECKOUT
- Checkout creates Sale #43, clears cart, and hides `go-to-cart-button` on `/products`.

## SAFETY_SCAN
- Destructive DB calls in tracked test code: 0 matches
- DB/Cache/Temp files in Git: 0 matches
- Direct DB access in inventory-sales-module: 0 matches
- Sensitive keys/env files: 0 matches

## FILES_CHANGED
- `inventory-sales-module/app/routers/cart.py`
- `inventory-sales-module/app/routers/products.py`
- `inventory-sales-module/app/templates/base.html`
- `inventory-sales-module/app/templates/products.html`
- `inventory-sales-module/app/templates/product_detail.html`
- `inventory-sales-module/app/static/cart_quick_add.js`
- `inventory-sales-module/tests/test_cart_quick_add.py`
- `inventory-sales-module/tests/test_products_quick_cart_ui.py`
- `docs/stage04j_quick_add_conditional_cart_button.md`
- `reports/stage04j_quick_add_conditional_cart_button_report.md`
- `logs/2026-08-03.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_PROMPT.md`

## COMMIT
- Message: "Add quick cart actions to product list"

## PUSH
- Destination: origin/main

## FINAL_GIT_STATUS
- Clean working tree

## OWNER_CHECK_GUIDE
1. Open `http://localhost:8030/products` -> Verify "Перейти в корзину" button is NOT visible when cart is empty.
2. Click "В корзину" on any available product -> Page does NOT reload/redirect to `/cart`. Button "Перейти в корзину (1)" appears next to header.
3. Click "В корзину" on a second product -> Counter updates to "Перейти в корзину (2)".
4. Click "Перейти в корзину (2)" -> Navigates to `/cart` with both products present.
5. Complete checkout -> Return to `/products` -> Button "Перейти в корзину" is hidden again.

## FINAL_STATUS
TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
