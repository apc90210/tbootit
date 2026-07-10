# Stage 04H: Product Locations, Stock, and Sales Reissue

## 1. Product Locations
- **Feature**: Track physical location of products.
- **Values**: `store` (Магазин), `workshop` (Мастерская), `archive` (Архив), `draft` (Черновик).
- **Default**: `store`.
- **Validation**: A product can only be added to a sale if its `storage_location == 'store'`.

## 2. Product Detail Stock Edit
- Users can manually update the `storage_location` and `quantity` of a product directly from the product detail page in the inventory module.
- Calling `PATCH /api/products/{id}` automatically validates and applies stock changes.

## 3. Sale Cancellation
- **Feature**: Ability to cancel a completed sale if the customer returns all items.
- **API**: `POST /api/sales/{sale_id}/cancel`.
- **Logic**:
  - Validates sale is completed.
  - Generates product events (`sale_canceled`).
  - Restores the product `status` and `quantity` to their pre-sale states.
  - Updates the sale status to `canceled`.

## 4. Sale Reissue (Переоформление)
- **Feature**: Ability to modify a completed sale by "reissuing" it with new items/prices/payment methods.
- **API**: `POST /api/sales/{sale_id}/reissue`.
- **Logic**:
  - Atomically restores items from the old sale.
  - Deducts items for the new sale.
  - Sets the old sale status to `superseded` and links it to the new sale via `replaced_by_sale_id`.
  - Sets the new sale `original_sale_id` to link back to the old sale.

## 5. Sales Reporting Adjustments
- Core API `GET /api/reports/sales` now dynamically filters out any sales with status `canceled` or `superseded`.
- This ensures daily totals, summaries, and legal entity breakdowns are entirely accurate and do not double-count reissued items.

## 6. Audit Logging
- Every step of the cancellation and reissue process correctly generates an `audit_events` log for the sale, tracking the state changes and ID links.
- Product events properly log the stock movements (`sale_reissue_return`, `sale_reissue_deduct`, `sale_canceled`).
