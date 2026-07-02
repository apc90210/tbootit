# Inventory/Sales Module UI Map

This defines the mapping of UI views for the inventory and sales operations.

## UI Endpoints

- **`GET /`**
  - **Template:** `index.html`
  - **Purpose:** Primary hub showing status and quick links.
  
- **`GET /products`**
  - **Template:** `products.html`
  - **Purpose:** Interactive catalog index with native HTML forms supporting `?q=` and `?status=` passing query parameters upstream to Core.
  - **Features:** "Продать" button active for `in_stock`/`reserved` products.

- **`GET /products/{id}`**
  - **Template:** `product_detail.html`
  - **Purpose:** Singular inspection view detailing events, statuses, and links.
  - **Features:** "Продать" button active for sellable products.

- **`GET /sales`** (Added in Stage04E)
  - **Template:** `sales_list.html`
  - **Purpose:** List of recent sales with pagination and status labels.

- **`GET /sales/new`** (Added in Stage04E)
  - **Template:** `sales_new.html`
  - **Purpose:** Sale checkout form. Pre-fills price, allows selecting payment method and adding notes. Prevents selling non-sellable products.

- **`GET /sales/{id}`** (Added in Stage04E)
  - **Template:** `sales_detail.html`
  - **Purpose:** Success page / Sale detail page showing the completed transaction.

- **Error States**
  - **Template:** `error.html`
  - **Purpose:** Shown transparently to users for 404s, 500s, and business logic errors (e.g. "Товар нельзя продать").
