# Core API Contract & Identified Gaps

## 1. Current Capabilities
- GET /api/products: Full pagination, sort, filtering by source, status, brand, etc.
- GET /api/products/{id} & .../details: Full product data including events and movements.
- PATCH /api/products/{id}: Safe updates (rejects status changes, empty title, negative prices).
- POST /api/products/{id}/status: Strict lifecycle transitions (Draft -> In Stock -> Reserved -> Sold).
- GET /api/customers & POST /api/customers: Customer management.

## 2. Identified Gaps (Stage 04C) & Resolution (Stage 04E)
The Core implementation was hardened in Stage 04C. In Stage 04E, the inventory-sales-module uses these APIs for the UI.

### POST /api/sales
**Current State:**
- Validates that the product status is `in_stock` or `reserved`.
- Rejects the sale if the product is sold, written_off, draft, etc.
- Executes the status transition to `sold` and logs a `sale_completed` event.
- Payment method validation (cash, card, transfer, mixed, other).

**Stage 04E Client Usage:**
- Used by `POST /sales/create` in `inventory-sales-module`.

### GET /api/sales & GET /api/sales/today
**Current State:**
- Implements pagination (limit, offset).
- Supports filtering.

**Stage 04E Client Usage:**
- Used by `GET /sales` in `inventory-sales-module` for the UI list.

### Cancel Sale (POST /api/sales/{id}/cancel)
**Current State:**
- Reverses a sale, returns products to `in_stock`, and logs `sale_cancelled` events.
- **Stage 04E Client Usage:** Out of scope for MVP UI. Will be added in future stages.

## 3. Data Requirements for Modules
The inventory-sales-module relies on:
- **Products:** `/api/products` for lists, `/api/products/{id}/details` for single view.
- **Sales:** `/api/sales` for creating checkout tickets and viewing sales history.
- **Customers:** Out of scope for Stage 04E UI, placeholder implementation used.
