# Core Sales Flow

This document details the sales logic within the Core API, established in Stage 04C.

## Supported Payment Methods
- `cash`
- `card`
- `transfer`
- `mixed`
- `other`

## Sales Lifecycle
The Core API enforces a strict product lifecycle validation to prevent invalid operations.

### Allowed Statuses for Sale
A product must be in one of the following statuses to be sold:
- `in_stock`
- `reserved`

If a sale is attempted on a product in `draft`, `sold`, `written_off`, `for_parts`, or `in_repair`, the `/api/sales` endpoint will return a **400 Bad Request**.

### Creating a Sale (`POST /api/sales`)
When a sale is created:
1. The Core API validates all items (quantity > 0, price >= 0, status is valid, no duplicates in payload).
2. The `Sale` and `SaleItem` records are created.
3. The `Product.status` is transitioned to `sold`.
4. A `ProductEvent` (`event_type: "sale_completed"`) is written for each product sold.
5. An `AuditLog` (`action: "create"`) is written for the sale.

### Cancelling a Sale (`POST /api/sales/{id}/cancel`)
Sales can be safely reversed using the cancellation endpoint.
1. The endpoint validates that the sale has not already been cancelled.
2. The `Sale.status` is changed to `cancelled`, and the timestamp and reason are logged.
3. For every item in the sale, the `Product.status` reverts to `in_stock`.
4. A `ProductEvent` (`event_type: "sale_cancelled"`) is written for each product restored.
5. An `AuditLog` (`action: "cancel"`) is written for the sale.

## Known Limitations
- The current implementation only tracks quantity as integers but sets product status to `sold` aggressively on the first sold item (under the assumption that items are generally unique devices). For bulk items, further hardening may be required.
- The `published_avito` and `published_site` attributes do not currently block sales operations.
