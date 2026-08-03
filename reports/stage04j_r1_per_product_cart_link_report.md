# Stage04J-R1 Per-Product Cart Link Report

## STATUS
SUCCESS — Stage 04J-R1 UX enhancement implemented, verified, and ready for owner check.

## OWNER_CLARIFICATION
The overall top cart button (`Перейти в корзину (N)`) is retained. In addition, a local button `Перейти в корзину` and a label `В корзине: N` appear beside each product that is currently present in the session cart, both upon quick add (via JS) and after page reload (via server template rendering).

## PREVIOUS_BEHAVIOR
In Stage 04J, only the top header cart button (`Перейти в корзину (N)`) updated upon quick add. Individual product rows/cards on `/products` and `/products/{id}` only had the `[В корзину]` action button without local indicators or links.

## NEW_BEHAVIOR
Adjacent to every product added to the session cart, a local button `Перейти в корзину` (href="/cart") and quantity label `В корзине: N` are shown. Products not in the session cart do not display local cart links.

## TEMPLATE_CONTEXT
`inventory-sales-module/app/routers/products.py` passes `cart_quantities_by_product_id` (dict of `product_id -> quantity`) and `cart_product_ids` (set of `product_id`s in cart) into the template context for both `/products` and `/products/{id}`.

## LOCAL_CART_BUTTON
HTML templates `products.html` and `product_detail.html` include `<a href="/cart" class="btn btn-success product-go-to-cart">Перейти в корзину</a>` inside `.product-cart-actions[data-product-id="..."]`, hidden by default unless `item.id in cart_product_ids`.

## JAVASCRIPT_UPDATE
`cart_quick_add.js` handles AJAX responses from `POST /cart/add-quick`. Upon success, it updates top header cart count, finds all `[data-product-id="..."]` matching `data.product_id`, unhides `.product-go-to-cart` and `.product-cart-quantity`, and updates `.product-cart-quantity-value` to `data.product_quantity_in_cart`.

## QUANTITY_DISPLAY
Displays `В корзине: N` next to the local cart button. When quantity increases via repeated quick add, `product_quantity_in_cart` updates dynamically.

## ERROR_HANDLING
When quick add encounters errors (e.g. status reserved/sold/draft, out of stock, location mismatch, quantity limit), no local button or quantity label is revealed for non-cart items, top counter remains unchanged, and a Russian error toast is displayed.

## TESTS
- **Core Safe Unit Tests**: 122 passed (0 failures).
- **Inventory-Sales-Module Tests**: 110 passed (0 failures).
- **Avito-Module Tests**: 12 passed (0 failures).

## LIVE_DB_PRESERVATION
Live database `/data/db/technoreboot.db` was 100% preserved during unit test executions via isolated temporary test databases.

## RUNTIME_EMPTY_CART
Verified via live HTTP: on `/products` with empty cart, top cart button is hidden (`display: none;`) and per-product local cart links are hidden.

## RUNTIME_FIRST_ADD
Verified via live HTTP: quick add of Product #46 updates top cart button to 1 and reveals local cart link `Перейти в корзину` and `В корзине: 1` beside Product #46.

## RUNTIME_SECOND_ADD
Verified via live HTTP: quick add of Product #47 updates top cart button to 2 and reveals local cart link beside Product #47, while Product #46 retains its local link.

## RUNTIME_RELOAD
Verified via live HTTP: GET `/products` after reload renders server-side local cart links and quantity labels for both Product #46 and #47.

## RUNTIME_CHECKOUT
Verified via live HTTP: clearing/checking out cart removes session cart items, hiding top cart button and all per-product local cart links upon return to `/products`.

## SAFETY_SCAN
All 4 mandatory safety scans returned 0 violations. No active `drop_all`, `DROP TABLE`, mass `DELETE FROM`, direct DB access from inventory module, or leaked credentials.

## FILES_CHANGED
- `inventory-sales-module/app/routers/products.py`
- `inventory-sales-module/app/routers/cart.py`
- `inventory-sales-module/app/templates/products.html`
- `inventory-sales-module/app/templates/product_detail.html`
- `inventory-sales-module/app/static/cart_quick_add.js`
- `inventory-sales-module/tests/test_product_cart_membership_ui.py`
- `inventory-sales-module/tests/test_cart_quick_add.py`
- `docs/stage04j_r1_per_product_cart_link.md`
- `reports/stage04j_r1_per_product_cart_link_report.md`
- `logs/2026-08-03.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04J_R1_PER_PRODUCT_CART_LINK_PROMPT.md`

## COMMIT
Pending targeted git commit: `git commit -m "Show cart link beside added products"`.

## PUSH
Pending git push to `origin main`.

## FINAL_GIT_STATUS
Clean worktree expected after targeted commit.

## OWNER_CHECK_GUIDE
1. Open http://localhost:8030/products with empty cart — observe no top cart button and no local cart links.
2. Click "В корзину" on any item — notice top cart button appears (1) and local "Перейти в корзину" link + "В корзине: 1" label appears next to that item without page reload.
3. Click "В корзину" on a second item — observe top cart button updates to (2) and a local link appears next to the second item.
4. Reload the page — observe local links and quantities persist across reloads.
5. Click "Перейти в корзину", complete sales checkout — return to `/products` and observe all cart links and top button disappear.

## FINAL_STATUS
TECHNOREBOOT_STAGE04J_R1_PER_PRODUCT_CART_LINK_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
