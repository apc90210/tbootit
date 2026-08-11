# Stage 06A — Authenticated Avito Catalog Import Documentation

## Architecture Summary
Stage 06A enables authorized import of company-owned Avito listings into the Technoreboot main product catalog (`Avito -> Technoreboot`).

### Core Model & Database Schema
1. **`ProductExternalListing` Model (`product_external_listings` table)**:
   - `product_id` (FK -> `products.id`)
   - `marketplace` (Default `'avito'`)
   - `external_account_key` (e.g. `'main'`, `'laptops'`, `'office'`)
   - `external_item_id` (Avito item ID)
   - `external_url` (URL to Avito item page)
   - `remote_status` (`'active'`, `'inactive'`)
   - `sync_state` (`'synced'`, `'failed'`)
   - Unique Partial Index: `CREATE UNIQUE INDEX ix_product_ext_listings_market_item ON product_external_listings(marketplace, external_item_id)`

2. **Product & Photo Fields**:
   - `Product.source_origin` (default `'avito'`)
   - `Product.source_attributes_json` (raw parameters & category data)
   - `ProductPhoto.source_url` and `ProductPhoto.content_hash` (SHA256 hash for photo deduplication)

### Ingestion API
- `POST /api/integrations/avito/import-item`
- Performs idempotent product and external listing upsert.
- Photo deduplication via SHA256 content hashing.
- Emits audit events (`avito.product_imported`, `avito.product_updated`, `avito.external_link_created`, `avito.external_link_updated`).

### Avito Module & Multi-account Isolation
- Multi-account management supporting 3 default browser profiles ("Main", "Laptops", "Office").
- UI on `/accounts` rendering profiles, auth statuses (`authorized`, `unauthorized`, `challenge_required`), scope selector (`active`, `archived`, `all`), live progress, graceful stop, and error retries.
- Local noVNC link (`http://localhost:8061`) for manual CAPTCHA / 2FA login.
- Zero direct database access from `avito-module` (all communication strictly via Core HTTP API).
