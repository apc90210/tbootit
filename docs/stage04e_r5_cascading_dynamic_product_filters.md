# Stage 04E-R5: Cascading Dynamic Product Filters

## Overview
This document covers the implementation of cascading (dependent) dynamic product filters in `inventory-sales-module` and `core`.

## Requirements
- Filters must cascade from left to right: `Category` -> `Brand` -> `Model` -> `Status` -> `Storage Location` -> `Avito / Site Ready`.
- When a user selects a filter at level N, all subsequent filters (level N+1, N+2, etc.) must reset and recalculate their options based on the upstream selections.
- The UI must immediately submit the search form and refresh when any filter changes.
- Russian labels must be maintained for standard fields.
- The Core API must support the dependency calculations on `GET /api/products/filter-options`.

## Implementation Details

### Core API (`core/app/routers/products.py`)
- Updated `get_product_filter_options` to accept query parameters (`category_id`, `brand`, `model`, etc.).
- Using **Approach A (Dependent Facets per Level)**:
  - `categories` counts use base query (no filter).
  - `brands` counts use `category_id` filter.
  - `models` counts use `category_id` + `brand` filter.
  - `statuses` counts use `category_id` + `brand` + `model` filter.
  - `storage_locations` counts use `category_id` + `brand` + `model` + `status` filter.
  - `avito_ready` & `site_ready` counts use all previous filters.

### Inventory-Sales Module UI
- Updated `core_client.get_product_filter_options(params)` to transmit UI state to the core backend.
- Added Javascript `cascadeReset(level)` to `products.html`. When an `onchange` triggers, it blanks out values for downstream `<select>` fields to enforce the strict left-to-right cascade.
- Form submits automatically, improving user experience.

## Tests
- `test_product_filter_options_cascading.py` verifies the facet generation logic in Core.
- `test_cascading_product_filters_ui.py` verifies the template includes the proper JS and event bindings.
- All tests pass in their respective containers.
