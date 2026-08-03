# Stage 04I-R7 Cart and Sale Payload Contract Repair Documentation

## Overview
This document records the architectural analysis, repair implementation, and verification for the two owner-reported regression defects in Stage 04I-R7 of project "Technoreboot".

---

## 1. Owner Reported Errors & Root Cause Analysis

### Error 1 — Cart Checkout (`/cart/checkout`) Missing `total_amount`
- **Symptom:**
  ```text
  Ошибка: [{'type': 'missing', 'loc': ['body', 'total_amount'], 'msg': 'Field required', 'input': {...}}]
  ```
- **Root Cause:**
  - `SaleBase` schema in `core/app/schemas.py` specified `total_amount: float` as a required field.
  - When checking out from the UI (`inventory-sales-module`), the client payload omitted `total_amount` or expected Core to compute it from items.
- **Architectural Solution:**
  - Changed `total_amount` to `Optional[float] = None` in `SaleBase` schema (`core/app/schemas.py`).
  - Updated `create_sale` endpoint in `core/app/routers/sales.py` to calculate `calculated_total = sum(item.price * item.quantity for item in sale.items)` on the server and set `sale_data["total_amount"] = calculated_total`.
  - Core API now dynamically calculates `total_amount` from sale item rows, ensuring server-side integrity and backwards payload compatibility.

### Error 2 — Add Product to Cart (`/cart/add`) Missing `price` Body
- **Symptom:**
  ```json
  {"detail": [{"type": "missing", "loc": ["body", "price"], "msg": "Field required", "input": null}]}
  ```
- **Root Cause:**
  - `POST /cart/add` route in `inventory-sales-module/app/routers/cart.py` declared `price: float = Form(...)` as a required form field.
  - When adding a product to cart from HTML forms on product list (`/products`) or product detail (`/products/{id}`), `price` was either missing or empty.
- **Architectural Solution:**
  - Updated `add_to_cart` route in `inventory-sales-module/app/routers/cart.py` to accept `product_id: Optional[int] = Form(None)`, `path_product_id: Optional[int] = None`, `title: Optional[str] = Form(None)`, and `price: Optional[float] = Form(None)`.
  - If `title` or `price` is missing, `add_to_cart` queries Core API (`GET /api/products/{id}`), validates product sellability (checking status, quantity, storage location), extracts `title` and `sale_price` / `price`, and adds the product to cart seamlessly without 422 errors.

---

## 2. Test Suites & Coverage
- **Core Unit Tests (`scripts/test_core_safe.ps1`):** Created `core/tests/test_sales_payload_contract.py` testing `SaleCreate` without `total_amount`, server total calculation, item validation, and SBP/no-warranty payload options (**118 passed**).
- **Inventory UI Tests (`inventory-sales-module`):** Created `inventory-sales-module/tests/test_cart_add_contract.py` and `inventory-sales-module/tests/test_cart_checkout_contract.py` (**91 passed**).
- **Avito Module Tests (`avito-module`):** **12 passed**.

---

## 3. Live Empirical Verification
- **Live DB Preservation Proof:**
  - `SHA256` before tests & edits: `9d869798764bb703364f5e195ef937fd0040efa52611ac9d6ae5cb645b94d2ed`
  - `SHA256` after tests & edits: `9d869798764bb703364f5e195ef937fd0040efa52611ac9d6ae5cb645b94d2ed`
  - Products: 53 | Barcodes: 53 | Sales: 33 (100% untouched and preserved).
- **Live Empirical HTTP Smoke Test:**
  - `POST /cart/add` with `product_id = 46` (no body `price`) -> HTTP 303 Redirect to `/cart`, product successfully added.
  - `POST /cart/checkout` with `payment_method = "sbp"`, `warranty_enabled = "on"`, `warranty_days = 30` -> HTTP 303 Redirect to `/sales/34`, sale created in Core with `total_amount = 1000.0`, `payment_method = "sbp"`. Cart cleared.
