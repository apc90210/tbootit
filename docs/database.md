# Database Schema

Uses SQLite.

## Tables
- `categories`: Product categories.
- `products`: Main inventory (includes stock, prices, publication flags).
- `product_photos`: Metadata for images.
- `product_events`: Lifecycle events for products.
- `stock_movements`: Delta tracking for product inventory.
- `customers`: Client list.
- `repair_orders`: Repair tracking.
- `sales` & `sale_items`: Sales transactions.
- `audit_log`: System action history.
