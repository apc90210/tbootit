# Stage 04J Quick Add and Conditional Cart Button Documentation

## Overview
This document records the design, implementation, test coverage, and release verification for Stage 04J (`TECHNOREBOOT_STAGE04J_QUICK_ADD_CONDITIONAL_CART_BUTTON`).

---

## 1. Owner Decision & Requirements

- **Problem:**
  - Previously, clicking "В корзину" on the `/products` list page performed a full form submission and redirected the user to `/cart`.
  - This interrupted item selection, lost page scroll position, and required users to navigate back to `/products` to add additional items.

- **Stage 04J UX Requirements:**
  1. Clicking "В корзину" adds the item to the session cart **without reloading the page or redirecting to `/cart`**.
  2. The page URL, active filters, search query, pagination, and scroll position remain completely preserved.
  3. A conditional **"Перейти в корзину (N)"** button appears next to the page header when `cart_items_count > 0`.
  4. When the cart is empty (`cart_items_count == 0`), the button is hidden (`display: none;`).
  5. Error conditions (reserved, sold, draft, out of stock, wrong location, non-existent product) show clear Russian error messages without altering cart state or counter.
  6. Non-JavaScript progressive enhancement fallback redirects back to the current `/products` page with active filters instead of `/cart`.

---

## 2. Technical Architecture & Endpoints

### A. Core API Contract & Session Cart
- `inventory-sales-module` remains 100% session cart based and delegates product validation and details retrieval to `Core API`.
- No direct database access or ORM calls from `inventory-sales-module`.

### B. Endpoint `POST /cart/add-quick` & `POST /cart/add`
- Location: `inventory-sales-module/app/routers/cart.py`
- Accepts AJAX/Fetch request (`X-Requested-With: XMLHttpRequest` or `/cart/add-quick`).
- JSON Response Schema:
  ```json
  {
    "ok": true,
    "message": "Товар '...' добавлен в корзину",
    "cart_items_count": 3,
    "cart_lines_count": 2,
    "product_id": 55,
    "product_quantity_in_cart": 1
  }
  ```
- Error Response Schema (`HTTP 400/404/409/502`):
  ```json
  {
    "ok": false,
    "message": "Товар зарезервирован и недоступен для продажи.",
    "cart_items_count": 2
  }
  ```

### C. Client Script & Accessibility (`inventory-sales-module/app/static/cart_quick_add.js`)
- Intercepts submit events on form element `.quick-add-form`.
- Temporarily disables submit button and updates text to `"Добавляем..."` to prevent double-click double increments.
- On success:
  - Updates `#go-to-cart-button` span counter and reveals button if hidden.
  - Temporarily sets button text to `"✓ Добавлено"`.
  - Shows Toast notification (`aria-live="polite"`).
- On failure:
  - Displays error toast notification.
  - Restores button state without changing cart counter.

---

## 3. Test Coverage

- **Core API Safe Tests:** `122 passed`
- **Inventory Sales Unit Tests (`test_cart_quick_add.py`, `test_products_quick_cart_ui.py`):** `106 passed`
- **Avito Module Tests:** `12 passed`
- **Live DB Preservation:** Live DB SHA256 (`54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`) remained 100% identical before & after unit tests.

---

## 4. Live Runtime Scenarios Verified

1. **Scenario A (Empty Cart):** `go-to-cart-button` is hidden (`display: none;`).
2. **Scenario B (First Quick Add):** Adding Product #55 updates button counter to `Перейти в корзину (1)` and reveals it without page reload.
3. **Scenario C (Second Quick Add & Filter Preservation):** Adding Product #56 updates button counter to `Перейти в корзину (2)`. Search query `?location=store&q=...` preserved intact.
4. **Scenario D (Error Handling):** Invalid product ID returns HTTP 404 with Russian error message. Cart counter remains 2.
5. **Scenario E (Checkout Regression):** Completing checkout creates Sale #43, clears cart, and hides `go-to-cart-button` on `/products`.
