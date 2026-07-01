# Stage 04C: Core Sales Flow Hardening

## Overview
Stage 04C strengthens the Core API by introducing strict business rules and lifecycles around the sales processing. The `/api/sales` endpoints are now fully prepared to act as the backend for the `inventory-sales-module`.

## Features Added

### 1. Robust Sales Validation
The `POST /api/sales` endpoint has been thoroughly hardened:
- Validates payment methods against a whitelist (`cash`, `card`, `transfer`, `mixed`, `other`).
- Requires items to have valid `quantity` (> 0) and `price` (>= 0).
- Rejects requests that contain duplicate `product_id`s in a single transaction payload.
- Strictly verifies that the `product.status` is either `in_stock` or `reserved`. It will actively reject `draft`, `sold`, `written_off`, or `in_repair` items.

### 2. Transaction Auditing & Events
- Creating a sale logs an `AuditLog` entry.
- Modifying the product status to `sold` also correctly triggers a `ProductEvent` indicating `sale_completed`, with details on the sale context.

### 3. Sale Cancellations
- Added `POST /api/sales/{id}/cancel` to safely revert sales transactions.
- Reverts product statuses from `sold` back to `in_stock`.
- Adds a `cancel_reason` and sets `status = "cancelled"` on the `Sale` record.
- Triggers `sale_cancelled` `ProductEvent`s for restored items and logs an `AuditLog`.

### 4. Paginated List and Filtering
- Enhanced `GET /api/sales` to support `limit`, `offset`, and advanced filtering by `payment_method`, `customer_id`, `date_from`, and `date_to`.
- Added a convenience `GET /api/sales/today` endpoint to rapidly fetch the current day's business.

## Database Migrations
Safely appended `status`, `cancelled_at`, and `cancel_reason` columns to the `sales` table utilizing an ad-hoc PRAGMA script within `app/main.py`. This ensures seamless SQLite schema updates without losing existing mock data.
