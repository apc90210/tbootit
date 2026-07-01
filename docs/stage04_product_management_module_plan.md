# Stage04 Product Management Module Plan

## 1. Goal
Design the MVP for the Product Management Module to allow operators to manage products imported into Core, modify details, transition statuses (including marking as sold), and print price tags.

## 2. Non-goals
- Advanced accounting and invoicing.
- Integration with external paid printing services.
- Direct database editing bypassing the Core API.
- Direct creation of products via UI (only editing/managing imported/draft products).

## 3. Current baseline after Stage03B
- Avito ads can be parsed and imported into Core as draft products.
- Product model exists in Core (`products` table) with multiple fields for pricing, notes, condition, and status.
- Admin UI exists but primarily supports basic health checks and initial scaffolding (`index.html`).

## 4. Architecture decision
- product management UI/module uses Core API only
- Core owns DB writes
- no direct DB access outside Core

## 5. Product lifecycle/status model
Statuses defined for products:
- `draft` (initial state after import)
- `in_stock` (ready to be sold)
- `reserved` (on hold for a customer)
- `sold` (purchased)
- `written_off` (lost, broken, unusable)
- `archived` (hidden from active views)

Transitions:
- `draft` -> `in_stock`
- `in_stock` -> `reserved`, `sold`, `written_off`
- `reserved` -> `in_stock`, `sold`
- `sold` -> `archived` (optional)

## 6. Required Core API endpoints
- `GET /api/products`: List products with filtering (status, source, category) and search.
- `GET /api/products/{id}`: Retrieve detailed product info, including Avito trace.
- `PATCH /api/products/{id}`: Edit safe product fields (title, description, price, category, condition, internal notes, status, image metadata).
- `POST /api/products/{id}/mark-sold`: Special endpoint to handle sale logic (record sale price, date).
- `POST /api/products/{id}/status`: Change product status explicitly.
- `POST /api/price-tags/preview`: Generate printable price tag HTML/data.

## 7. Required UI screens/components
- **Product List Screen**: Table or grid showing products with search, filters (status/source), and sorting.
- **Product Detail Screen**: Form to edit product fields and view source data trace (e.g., Avito).
- **Print Preview Modal/Page**: Print-friendly HTML view for price tags.

## 8. Product editing rules
- Operators can edit: title, description, price, category, condition, internal notes, status, and images metadata.
- Read-only fields in UI (unless explicitly allowed): ID, import source trace info, creation timestamps.

## 9. Sale / mark-as-sold flow
1. Operator selects a product in `in_stock` status.
2. Clicks "Mark as Sold".
3. Optionally enters sale price (defaults to current price) and comment/contact info.
4. Core records sale transaction, updates status to `sold`, creates audit/sale record.
5. Product is removed from default `in_stock` views.

## 10. Price tag printing flow
1. Operator selects one or more products.
2. Clicks "Print Price Tags".
3. A print-friendly HTML page opens displaying fields: title, price, specs/condition, internal SKU.
4. Browser's native print dialog is used.

## 11. Data model gaps
- Need structured approach for price tag bulk operations.
- The `Product` model has many fields but might need adjustments for standardizing print tags.

## 12. Security/safety constraints
- All UI actions must strictly use Core API.
- Validate status transitions (e.g., cannot mark `draft` as `sold` without passing `in_stock` checks).

## 13. Logging/audit events
- Every status change must create an `AuditLog` or `ProductEvent` entry.
- Sale action must be logged with user context (if auth exists) or system audit trail.

## 14. Test plan
- Core: Unit tests for `PATCH /api/products/{id}`, status transitions, and `mark-sold` logic.
- Admin UI: Manual acceptance for the new views (list, edit, print).
- Security: Contract tests ensuring UI doesn't write to DB.

## 15. Implementation stages
- Stage04A: Core product list/detail/status API gaps
- Stage04B: Admin UI product list/detail MVP
- Stage04C: sale/mark-sold flow
- Stage04D: price tag print MVP
- Stage04E: integration audit/acceptance

## 16. Acceptance criteria
- All endpoints implemented and tested.
- UI allows full product management lifecycle without direct DB queries.
- Print tags feature works natively via browser.
- Logging and audit trails confirm safe operations.

## 17. Risks/blockers
- Potential complexity in printing specific label sizes; sticking to standard HTML print for MVP mitigates this.
