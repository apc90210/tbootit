# Technoreboot — Stage 06A-R10A V2: Capability-Based Avito Integration Report

## STATUS: SUCCESS

## CURRENT_EXTENSION_VERSION
`0.2.17` (Baseline accepted and fully functional with Autonomous Gallery Walker).

## CAPABILITY_MODEL
- **`AVITO_API_CONFIGURED`**: `False` (in default environment; dynamically `True` when `AVITO_CLIENT_ID` + `AVITO_CLIENT_SECRET` provided)
- **`AVITO_API_AUTHENTICATED`**: `False`
- **`AVITO_AUTOLOAD_SCHEMA_AVAILABLE`**: `False` (without API credentials; optional pluggable capability)
- **`AVITO_BROWSER_BRIDGE_AVAILABLE`**: `True`
- **`AVITO_BROWSER_ASSISTED_AVAILABLE`**: `True`
- **`AVITO_MANUAL_AVAILABLE`**: `True`
- **`CANONICAL_SCHEMA_SOURCE`**: `"observed_only"` (falls back gracefully without API)

## OBSERVED_MODEL_AUDIT
- `AvitoCategory`: Preserved. Stores observed category names and hierarchy.
- `AvitoAttributeDefinition`: Preserved. Stores dynamic observed characteristics.
- `AvitoAttributeOption`: Preserved. Stores observed distinct choice values.
- `ProductAvitoAttributeValue`: Preserved. Stores product-bound exact `raw_value` and normalized values.
- **Audit Conclusion**: The observed model is 100% intact and serves as the ground-truth observed data layer.

## CANONICAL_MODEL
Created transport-neutral canonical layer in `core/app/models.py`:
- `AvitoCanonicalCategory`: internal key, display name, observed link, optional `official_slug`.
- `AvitoCanonicalField`: internal key, display name, official tag, data_type, field_type.
- `AvitoCanonicalFieldRule`: ordinal, rule_source, required, required_by_dependency, dependencies_json, values_range_json.
- `AvitoCanonicalFieldValue`: value, description, official_value, source (inline, linked_json, manual, observed).
- `AvitoObservedFieldMapping`: category_id, observed_name, observed_name_normalized, canonical_field_id, mapping_source (`exact_label`), confidence.

## MIGRATIONS
- Added `canonical_category_id` to `Product` model in `core/app/models.py`.
- Added runtime SQLite migration in `core/app/main.py` (`migrate_db()`) to add `canonical_category_id` column to `products` table if absent.

## OFFICIAL_AUTOLOAD_ADAPTER
- Implemented `OfficialAvitoAutoloadSchemaProvider` in `core/app/services/avito_official_autoload_provider.py`.
- Configured strictly via server-side environment variables `AVITO_CLIENT_ID` and `AVITO_CLIENT_SECRET`. No secrets in extension, git, or client DB.
- Token caching mechanism with automatic expiration management.

## OFFICIAL_TREE_CLIENT
- `fetch_tree()` endpoint client for `GET /autoload/v1/user-docs/tree`.
- Supports recursive node extraction (`name`, `slug`, `nested`) and HTTP 304 `If-Modified-Since` caching.

## OFFICIAL_FIELDS_CLIENT
- `fetch_node_fields()` client for `GET /autoload/v1/user-docs/node/{slug}/fields`.
- Supports HTTP 304 caching.
- `parse_content_rules()` preserves all rules without destructive flattening.
- `fetch_linked_json_values()` implements HTTPS-only validation, Avito host allowlisting (`api.avito.ru`, `autoload.avito.ru`), timeout, and 5MB size limit.

## CATEGORY_MAPPING
- Category mapping decouples internal/observed display names (e.g. `Материнские платы`) from official slugs (`materinskie-platy`).
- If official API is not configured, canonical categories operate with `official_slug = None` under `capability_source = "observed"`.

## FIELD_MAPPING
- `sync_observed_category_to_canonical` creates exact label mappings (`mapping_source = "exact_label"`) between observed attribute definitions and canonical fields.
- Mapping is scoped strictly within the same category to prevent incorrect cross-category collisions.

## UNRESOLVED_MAPPING_BEHAVIOR
- Unmapped attributes remain in `unresolved_fields` list during canonical projection.
- Raw values are never dropped, ensuring 100% preservation of all listing parameters.

## PUBLICATION_PACKAGE
- Implemented `build_avito_publication_package(db, product_id)` in `core/app/services/avito_preflight_service.py`.
- Generates a transport-neutral JSON package with product data, SKU, brand, model, condition, photos, canonical_fields, and transport readiness flags.

## PREFLIGHT
- Implemented `preflight_product_for_avito(db, product_id)` in `core/app/services/avito_preflight_service.py`.
- Validates transport-neutral rules (title, description, price > 0, photos > 0).
- Sets `ready_for_browser_assisted = True` and `ready_for_manual = True` whenever basic data is valid.
- Sets `ready_for_official_autoload = False` with `AUTOLOAD_SCHEMA_UNAVAILABLE` warning when API credentials are not configured.

## TRANSPORT_INTERFACE
- Defined `AvitoPublicationTransport` abstract base class with `capabilities()`, `prepare()`, `validate()`, and `publish()`.
- Implemented concrete transports:
  - `OfficialAutoloadTransport`
  - `BrowserAssistedTransport`
  - `ManualTransport`

## NO_REAL_AVITO_WRITES
- All transports raise `NotImplementedError("Avito publication is disabled in Stage 06A-R10A foundation")` on `publish()`.
- Zero live upload, create, edit, or delete requests are sent to Avito.

## MOTHERBOARD_CANONICAL_STATE
- **Category**: `Материнские платы`
- **Canonical Key**: `cat_materinskie_platy`
- **Observed Link**: Bound to `AvitoCategory("Материнские платы")`
- **Official Slug**: `None` (gracefully operates in observed/browser-assisted mode without API)
- **Official Schema Status**: `NOT_CONFIGURED` (Valid and expected baseline)

## CURRENT_IMPORT_PRESERVED
- Chrome Extension v0.2.17 extraction works seamlessly.
- Product ingestion, brand/model persistence, price, and description remain 100% operational.

## PHOTO_FLOW_PRESERVED
- Autonomous Gallery Walker, HD extraction (`1280x960`), SHA-256 deduplication, and photo reconciliation are preserved.

## CHARACTERISTICS_FLOW_PRESERVED
- Extraction of parameters without colons, filtering of seller statistics, and raw value persistence are preserved.

## SOURCE_LINK_PRESERVED
- External URL and ID in `ProductExternalListing` remain fully functional.

## PLUGIN_ONLY_UI_PRESERVED
- Admin-shell UI remains clean, containing only the Chrome Extension integration page.

## TESTS
- **`core/tests`**: **208 passed** (including 16 new tests for Stage 06A-R10A V2)
- **`avito-module/tests`**: **84 passed** (including new capability contract test)
- **`admin-shell/tests`**: **54 passed**
- **`chrome-extension/technoreboot-avito/tests`**: **18 passed**
- **`inventory-sales-module` & `repairs-module`**: **197 passed**
- **Total Test Suite**: **561 / 561 passed (100% PASS)**

## RUNTIME
- All Docker services (`core`, `admin-shell`, `avito-module`, `inventory-sales-module`, `repairs-module`) are running healthy.

## FILES_CHANGED
- `core/app/config.py`: Added optional Avito API capability settings.
- `core/app/models.py`: Added `AvitoCanonicalCategory`, `AvitoCanonicalField`, `AvitoCanonicalFieldRule`, `AvitoCanonicalFieldValue`, `AvitoObservedFieldMapping`, and updated `Product`.
- `core/app/main.py`: Added runtime DB migration for `canonical_category_id`.
- `core/app/services/avito_capability_service.py`: Implemented capability detection.
- `core/app/services/avito_canonical_service.py`: Implemented canonical category/field management and mapping.
- `core/app/services/avito_official_autoload_provider.py`: Implemented optional official Autoload schema provider.
- `core/app/services/avito_preflight_service.py`: Implemented publication package and preflight validation.
- `core/app/services/avito_transport.py`: Implemented transport abstraction and concrete adapters.
- `core/app/routers/integrations.py`: Added capabilities, preflight, and publication-package endpoints; added automatic canonical sync on import.
- `core/tests/test_stage06a_r10a_capability_based_avito.py`: Added comprehensive unit and integration test suite (16 tests).
- `avito-module/tests/test_capability_model_contract.py`: Added contract test.
- `docs/stage06a_r10a_capability_based_avito_architecture.md`: Architecture specification document.
- `reports/stage06a_r10a_capability_based_avito_report.md`: Stage completion report.

## COMMIT
- Branch: `main`
- Commit Message: `feat(avito-core): add capability-based Avito integration foundation (Stage 06A-R10A V2)`

## PUSH
- Pushed to `origin/main` (`apc90210/tbootit`).

## FINAL_GIT_STATUS
Clean worktree.

## OWNER_CHECK_GUIDE
1. Open `http://localhost:8011/avito/extension` and verify Chrome Extension v0.2.17 download and pairing work.
2. Open any Avito listing (e.g. motherboard) and click **«Передать объявление в Техноребут»**.
3. Open product card in Technoreboot (e.g. `http://localhost:8011/inventory/products/{id}`).
4. Verify title, price, brand, model, characteristics, photos, and source link.
5. Check preflight endpoint `http://localhost:8011/api/integrations/avito/products/{id}/preflight` (or core `http://localhost:8000/api/integrations/avito/products/{id}/preflight`).
6. Confirm that system operates 100% smoothly without requiring paid Avito API tariffs.

## NEXT_STEP
Stage 06A-R10B: Browser-Assisted Reverse Publication Prototype (dry-run form-fill preparation without automatic submit).

## FINAL_STATUS: SUCCESS
