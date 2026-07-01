# Inventory/Sales Module UI Map

This defines the initial skeleton mappings and intended progression.

## UI Endpoints

- **`GET /`**
  - **Template:** `index.html`
  - **Purpose:** Primary hub showing status and quick links.
  
- **`GET /products`**
  - **Template:** `products.html`
  - **Purpose:** Interactive catalog index with native HTML forms supporting `?q=` and `?status=` passing query parameters upstream to Core.
  - **Pending Hooks:** *Sale action (Stage04E)*, *Price tag generation (Stage04F)*.

- **`GET /products/{id}`**
  - **Template:** `product_detail.html`
  - **Purpose:** Singular inspection view detailing events, statuses, and links.
  - **Pending Hooks:** *Sale action (Stage04E)*, *Price tag generation (Stage04F)*.

- **Error States**
  - **Template:** `error.html`
  - **Purpose:** Shown transparently to users for 404s and 500s.
