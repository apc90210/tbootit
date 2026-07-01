# Core API Contract & Identified Gaps

## 1. Current Capabilities
- GET /api/products: Full pagination, sort, filtering by source, status, brand, etc.
- GET /api/products/{id} & .../details: Full product data including events and movements.
- PATCH /api/products/{id}: Safe updates (rejects status changes, empty title, negative prices).
- POST /api/products/{id}/status: Strict lifecycle transitions (Draft -> In Stock -> Reserved -> Sold).
- GET /api/customers & POST /api/customers: Customer management.

## 2. Identified Gaps (Stage 04C)
The current Core implementation lacks robust sales logic required by the inventory-sales module.

### POST /api/sales
**Current State:**
- Creates a sale and hardcodes product.status = "sold".
- Does not check if the product is already sold, written off, or in repair.
- Does not trigger a ProductEvent for the status change (only an AuditLog).

**Required Updates:**
- Must validate that the product status is in_stock or eserved.
- Must reject the sale if the product is sold, written_off, draft, etc.
- Must execute the status transition through the central lifecycle logic (creating a ProductEvent).
- Payment method validation (cash, card, transfer, mixed, other).

### GET /api/sales
**Current State:** Returns .all() without pagination.
**Required Updates:**
- Implement pagination (limit, offset).
- Add filtering (e.g., date_from, date_to or GET /api/sales/today).

### Cancel Sale
**Current State:** Missing.
**Required Updates:**
- Need POST /api/sales/{id}/cancel to reverse a sale, returning products back to in_stock and logging events.

## 3. Data Requirements for Modules
The inventory-sales-module will rely heavily on:
- **Products:** /api/products for lists, /api/products/{id}/details for single view.
- **Sales:** Updated /api/sales for creating checkout tickets.
- **Customers:** /api/customers for assigning sales.
