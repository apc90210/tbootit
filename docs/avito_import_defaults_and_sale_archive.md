# Avito Import Defaults and Sale Auto-Archiving

## Overview
This document specifies the default lifecycle states for products imported from Avito and their automated transitions upon sale and sale cancellation.

## 1. Avito Import Default State
When items are imported from Avito (via Chrome Extension or Core API `/api/integrations/avito/import-item`):
- **Status:** `in_stock` ("В наличии")
- **Storage Location:** `store` ("Магазин")
- **Quantity:** `1`

Previously, items imported from Avito were assigned `status = "draft"`, requiring manual activation before they could be sold or added to the sales cart. Under this update, products are immediately sellable and visible in the store catalog.

## 2. Automatic Move to Archive on Sale
When a product is sold (via `/api/sales/` or the Web Cart checkout `/inventory/cart/checkout`):
- If the remaining quantity of the product reaches `0`:
  - `status` is set to `"sold"` ("Продан")
  - `storage_location` is automatically updated to `"archive"` ("Архив")
- A `ProductEvent` with `event_type = "sale_completed"` records the transition with previous and new values of `status`, `quantity`, and `storage_location`.

## 3. Sale Reissue Semantics
When a sale is reissued (`/api/sales/{sale_id}/reissue`):
- The newly deducted product observes the same rule: if quantity reaches `0`, `status = "sold"` and `storage_location = "archive"`.

## 4. Sale Cancellation Restores to Store
When a sale is canceled (`/api/sales/{sale_id}/cancel`):
- If the product was in `sold` status and its quantity is restored to `> 0`:
  - `status` returns to `"in_stock"` ("В наличии")
  - If `storage_location` was `"archive"`, it is restored to `"store"` ("Магазин")
- A `ProductEvent` with `event_type = "sale_canceled"` records the restoration.

## 5. Existing Data Migration
- All 46 existing draft Avito products in `data/db/technoreboot.db` were migrated to `status = 'in_stock'` and `storage_location = 'store'`.
- All 50 active products currently in the catalog are now in stock and located in the store.

## 6. Bidirectional Archive Synchronization on Re-Import

The Avito integration supports automatic bidirectional synchronization between Avito listing states and the store's inventory location / status:

### A. Automatic Reactivation (Archive -> Store)
- **Condition:** An item already exists in the database with `storage_location == "archive"`, `status in ["sold", "draft", "archived"]`, or `quantity <= 0`, and is re-imported from Avito with active status (`remote_status == "active"` or raw text containing "активно").
- **Actions:**
  - `status` is set to `"in_stock"` ("В наличии").
  - `storage_location` is set to `"store"` ("Магазин").
  - `quantity` is set to `max(quantity, 1)`.
  - All updated attributes (price, title, description, parameters, photos) are synced.
  - A `ProductEvent` is logged with `event_type = "avito_reactivated"`.
- **Financial Ledger Integrity:** Historical `Sale` and `SaleItem` records remain immutable. Reactivating a previously sold listing restores physical inventory availability without altering past financial receipts.

### B. Automatic Archiving (Store -> Archive)
- **Condition:** An item is currently active in the store (`status == "in_stock"` or `storage_location != "archive"`), and is re-imported from Avito with an inactive / closed / archived status (`remote_status in ["inactive", "closed", "archived", "blocked", "removed", "sold", "old"]` or raw text containing "завершено", "архив", "снято", "неактивно", "заблокировано", "отклонено").
- **Actions:**
  - `status` is set to `"sold"` ("Продан / В архиве").
  - `storage_location` is set to `"archive"` ("Архив").
  - `quantity` is set to `0`.
  - A `ProductEvent` is logged with `event_type = "avito_archived"`.

### C. Initial Import of Inactive Listings
- If a listing is imported from Avito for the first time with an inactive status, it is directly created in the archive with `status = "sold"`, `storage_location = "archive"`, and `quantity = 0`.

