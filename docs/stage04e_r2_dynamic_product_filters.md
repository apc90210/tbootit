# Stage 04E-R2: Dynamic Product Filters

## 1. Overview
This document records the implementation of dynamic product filters in the Sales UI, an enhancement requested by the project owner during the UX check of Stage 04E.

## 2. Requirements Addressed
The owner requested that the product list page (`/products`) include a comprehensive top-bar filter panel with options dynamically populated based on actual data stored in the Core Database. Required filters included Type/Category, Brand, Model, Status, Storage Location, and Publication Readiness (Avito/Site).

## 3. Implementation Details

### Core API
A new endpoint was introduced: `GET /api/products/filter-options`.
This endpoint queries the database and aggregates unique values for:
- Brands (`brands`)
- Models (`models`)
- Statuses (`statuses`)
- Storage Locations (`storage_locations`)
- Categories (`categories`)
- Avito Readiness (`avito_ready`)
- Site Readiness (`site_ready`)

It groups the values and includes a `count` for each, ensuring the UI can display how many products match each option. The `GET /api/products/` endpoint was also updated to accept a `model` parameter.

### Inventory Sales Module
1. **CoreClient:** Added the `get_product_filter_options()` method to communicate with the new Core endpoint.
2. **Router:** The `/products` route now fetches filter options asynchronously and passes them to the Jinja template. It also parses new query parameters and forwards them to Core. If `filter-options` fails to load, the error is caught to prevent blocking access to the product list.
3. **Template:** Replaced the simple search form in `products.html` with a comprehensive flexbox-based filter panel. The template renders the dropdowns based on the `filter_options` dictionary, handles fallback gracefully, and preserves selected values across requests. All labels were localized to Russian.

## 4. Verification
- Full test coverage is implemented across Core and Inventory Sales modules.
- End-to-end testing confirms that filters accurately reflect the database state, UI interactions work properly, and fallback mechanisms prevent page crashes on partial API failure.
