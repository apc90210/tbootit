# WEB-07D Closeout Report: Reference Catalog Owner Review UI

**Stage**: WEB-07D  
**Contour**: Core (`C:\tbootit`), Admin-Shell (`C:\tbootit\admin-shell`)  
**Public Site Contour**: `C:\tboot-site` (strictly untouched, zero admin exposure)  
**Status**: PASS  
**Production Writes**: `PRODUCTION_WRITES=0`  

---

## 1. Executive Summary

In stage WEB-07D, an internal OWNER-only management UI and Review Queue for the Product Reference Catalog was designed, implemented, and fully verified. 

Key achievements:
1. **Single Runtime Source of Truth**: Maintained Core SQLite database (`data/db/technoreboot.db`) as the sole reference store (125 reference models, 217 linked products, 579 aliases, 3 external specification conflict records). Zero separate reference databases created.
2. **Strict RBAC & Security**: All reference catalog management pages and mutation endpoints are restricted exclusively to the `OWNER` role (`is_owner=True`) verified via mTLS client certificates. Neither unauthenticated anonymous requests nor authenticated `USER` (seller) certificates are allowed access (403 Forbidden). Any client attempt to forge headers like `x-auth-is-owner` is explicitly stripped and rejected.
3. **Product Instance Protection**: Rigorously prevented editing business-level instance data (pricing, stock quantity, condition, serial number, barcode, photos, defects, notes, storage locations, Avito listings) at the reference model level. Linked product instances are presented in read-only mode with dedicated links to individual product records.
4. **Canonical Engine Integration**: Preserved the canonical architecture. Admin-Shell performs zero matcher or enrichment business logic locally; instead, it proxies directly to Core's canonical matcher (`ProductReferenceMatcher`), canonical safe enricher (`safe_enrich_product`), and reference services.
5. **Conflict Resolution & Review Queue**: Provided an interactive review queue tab allowing the owner to resolve external specification discrepancies (e.g. between HP datasheets and external vendor specifications), confirm high-confidence candidate matches for unlinked products, preview/apply canonical enrichment, unlink false matches, or learn new reference models from confirmed product instances.
6. **Complete Audit Logging**: All owner mutations (editing model identity, modifying specifications, adding/deactivating aliases, resolving conflicts, manual linking/unlinking, and applying enrichment) are recorded in the central Core audit log table with actor, action, before/after values, and UTC timestamp.

---

## 2. Current API Reused

The following existing Core reference services and endpoints were reused directly without modification or regression:
- `POST /api/product-reference/match`: Canonical matcher endpoint used for candidate scoring.
- `POST /api/product-reference/enrich-preview/{product_id}`: Safe enrichment preview without writing to DB.
- `POST /api/product-reference/models`: Creation of reference models with auto-generated stable key and initial alias.
- `POST /api/product-reference/models/{id}/aliases`: Addition of new alias entries to a reference model.
- `DELETE /api/product-reference/models/{id}/aliases/{alias_id}`: Removal of an alias entry.
- `GET /api/product-reference/export`: Canonical JSON export of reference models and aliases.
- `POST /api/product-reference/import`: Canonical JSON import supporting `dry_run=True` / `False`.
- `POST /api/product-reference/learn-from-product/{product_id}`: Learning candidate reference models and aliases directly from confirmed product instances.
- Core Audit Logging via `app.routers.customers.log_audit`: Reused for all mutation auditing.

---

## 3. New API Added

To support the OWNER UI and Review Queue canonical contract without embedding business logic in Admin-Shell, the following minimal, strictly owner-gated canonical endpoints were implemented in Core (`core/app/routers/product_reference.py`):

1. **`GET /api/product-reference/meta`**:
   - Returns available brands, device types, and category mappings for filter dropdowns.
2. **Enhanced `GET /api/product-reference/models`**:
   - Supports filtering by `category_id`, `status_filter` (`verified`, `needs_review`, `conflict`), `incomplete_specs` (flagging models with < 5 specification keys), brand, and text search.
   - Automatically computes `has_conflict` from active external conflicts.
3. **Enhanced `GET /api/product-reference/models/{id}`**:
   - Returns full model details including canonical identity, specifications dictionary, external source URLs (`source_urls_json`), active specification conflicts, and aliases list.
4. **Enhanced `PUT /api/product-reference/models/{id}`**:
   - Allows owner updates to canonical identity, `verification_state`, default category, device type, site title/description, provenance notes, external source URLs, and specifications dictionary.
   - Audits all before/after changes.
5. **`PATCH /api/product-reference/models/{id}/aliases/{alias_id}`**:
   - Allows owner to activate/deactivate an alias or update its matching priority. Audits all changes.
6. **`GET /api/product-reference/models/{id}/products`**:
   - Returns linked product instances in read-only mode (`id`, `name`, `brand`, `model`, `price`, `quantity`, `condition`, `serial_number`, `storage_location`, `status`, `reference_match_method`, `reference_match_confidence`, `reference_enriched_at`).
7. **`POST /api/product-reference/products/{product_id}/link`**:
   - Manually links an unlinked product to a reference model with `manual_owner_link` method and 1.0 confidence.
   - Supports optional automatic canonical Safe Enrichment (`apply_enrichment: bool = True`).
   - Audits before/after linking.
8. **`POST /api/product-reference/products/{product_id}/unlink`**:
   - Unlinks a product from a reference model (clearing `reference_model_id`, `reference_match_method`, `reference_match_confidence`, and `reference_enriched_at`).
   - Audits action with owner-provided reason (e.g. `rejected_by_owner`).
9. **`POST /api/product-reference/products/{product_id}/enrich-apply`**:
   - Executes canonical Safe Enrichment (`safe_enrich_product`) for an already linked product and persists updated specifications without overwriting existing product instance fields.
10. **`GET /api/product-reference/review-queue`**:
    - Aggregates unresolved warehouse products (with Core Matcher candidate suggestions and confidence scores), external specification conflicts (from `EXTERNAL_ENRICHMENT_CONFLICTS.json`), and KPI summary metrics (`total_models`, `verified_models`, `incomplete_specs_models`, `linked_products`, `conflicts`, `unresolved_products`).
11. **`POST /api/product-reference/conflicts/resolve`**:
    - Resolves an external specification conflict for a model field.
    - Updates model specifications with the chosen value.
    - Updates the resolution status and resolution note in `data/reference_catalog/EXTERNAL_ENRICHMENT_CONFLICTS.json`.
    - Logs an audit entry.

In Admin-Shell (`admin-shell/app/main.py`), the following owner-only routes were registered:
- **`GET /reference/catalog`**: Serves `reference_catalog.html` UI page (requires owner certificate).
- **`ALL /admin-api/product-reference/{subpath:path}`**: Proxies requests directly to Core's `/api/product-reference/{subpath}` while validating owner certificate, stripping any client spoofing of `x-auth-is-owner`, and injecting verified `x-auth-is-owner: 1` and `x-api-token`.

---

## 4. Owner UI Architecture

The UI is placed entirely in `admin-shell/app/templates/reference_catalog.html`:
- **Unified Navigation Bar**: Integrated with the standard Admin-Shell navigation (`/`, `/inventory/products`, `/products/json`, `/inventory/reservations`, `/reference/catalog`, `/system/operations`, `/backups`, `/certificates`), visible only when `is_owner=True`.
- **KPI Metrics Dashboard**:
  - Всего моделей: `125`
  - Верифицировано: `72`
  - Неполные спеки: `< 5 характеристик`
  - Связано товаров: `217 / 421`
  - Требуют проверки: `43` (3 спецификационных конфликта + 40 неразрешённых товаров)
- **4 Tab Layout**:
  1. **Справочник моделей (Catalog Tab)**:
     - Full-text search and multi-criteria filters (brand, category, verification state, incomplete specs).
     - Paginated table showing ID, Canonical Name, Brand/Model, Category/Type, Aliases count, Specs count, Verification badge, Linked count, Conflict badge, and "Карточка ↗" action.
  2. **Требуют проверки (Review Queue Tab)**:
     - **Спецификационные конфликты**: Dedicated conflict resolution cards showing model, conflicting field name, candidate values from datasheets vs external enrichment, resolution input, and "Утвердить решение" button.
     - **Товары, требующие подтверждения модели**: Unlinked warehouse product cards displaying title, brand, category, price, and ranked candidate models from Core Matcher with confidence % and one-click "Привязать и обогатить" / "Привязать без обогащения".
  3. **Новая модель (Create Model Tab)**:
     - Form to register a new reference model with canonical attributes and initial aliases.
  4. **Экспорт / Импорт JSON (JSON Tools Tab)**:
     - Download full reference catalog in canonical JSON format.
     - Upload/paste JSON with Dry Run validation mode before applying.
- **Model Details Modal & Instance Protection**:
  - Section 1: Canonical identity (name, brand, model, device type, verification state, site SEO titles/descriptions, external datasheet URLs).
  - Section 2: Aliases manager (view aliases, add new alias, toggle active state, delete, priority score).
  - Section 3: Specifications editor (key-value table, add new specification attribute, save).
  - Section 4: **Связанные экземпляры со склада (Linked Products)**:
    - Prominent banner: *"🛡️ Защита экземпляров: Бизнес-поля экземпляров (цена, состояние, серийный номер, фото, остатки) защищены от изменения на уровне модели."*
    - Read-only table of linked product instances with link to product detail page, "Превью", "Обогатить", and "Отвязать" actions.

---

## 5. Review & Conflict Workflow

The workflow enables complete lifecycle management:
1. **Ambiguous / Unlinked Products**:
   - Unresolved products are retrieved by `GET /api/product-reference/review-queue`.
   - The Core Matcher evaluates each unlinked product and provides candidate reference models sorted by confidence.
   - The owner can select a candidate and click "Привязать и обогатить" (calls `POST /api/product-reference/products/{id}/link?apply_enrichment=true`) or "Привязать без обогащения".
   - If no candidate fits, the owner can click "Отклонить" (calls `POST /api/product-reference/products/{id}/unlink?reason=rejected_by_owner`) or create a reference model from the product via "Создать модель из товара" (`POST /api/product-reference/learn-from-product/{id}`).
2. **Conflicting Specifications**:
   - When external enrichment sources disagree (such as `print_speed_ppm` 40 vs 42 in `hp|laserjet-enterprise-p3015`), conflict cards appear both in the Review Queue tab and inside the Model Details modal.
   - The owner selects the correct value, optionally enters a rationale note, and clicks "Утвердить решение".
   - The endpoint `POST /api/product-reference/conflicts/resolve` updates the model's specifications, writes an audit record, and updates `data/reference_catalog/EXTERNAL_ENRICHMENT_CONFLICTS.json`.
3. **Safe Enrichment**:
   - The owner can click "Превью" on any linked product to inspect exactly which specification fields would be added or preserved without touching any product instance fields.
   - Clicking "Обогатить" runs canonical `safe_enrich_product` and audits the result.

---

## 6. Audit Logging

Every mutation through the reference endpoints records a structured entry in `core/app/routers/customers.py:log_audit`:
- **Actor**: `admin_owner` (verified by mTLS certificate).
- **Action**:
  - `reference_model_update`: Before/after state of canonical attributes and specifications.
  - `reference_alias_update`: Activation, deactivation, or priority update of an alias.
  - `reference_product_link`: Product ID linked to reference model ID with method and confidence.
  - `reference_product_unlink`: Product ID unlinked with owner reason.
  - `reference_product_enrich`: Enrichment execution timestamp and added fields.
  - `reference_conflict_resolve`: Resolved field, before value, chosen value, and resolution note.
- **Timestamp**: Current UTC datetime.

---

## 7. Security & Non-Owner Protection

Security was tested and verified across all vectors:
1. **Anonymous Access Blocked**:
   - `GET /reference/catalog` -> `403 Forbidden` ("Valid client certificate required")
   - `GET /admin-api/product-reference/*` -> `403 Forbidden`
   - `POST/PUT/PATCH/DELETE /admin-api/product-reference/*` -> `403 Forbidden`
2. **USER Role (Seller) Blocked**:
   - Any client certificate without `is_owner=True` receives `403 Forbidden` ("Owner certificate required").
3. **Header Spoofing Blocked**:
   - Any client sending `x-auth-is-owner: 1` directly without a valid owner certificate is stripped and rejected (`403 Forbidden`).
4. **Public Site Isolation**:
   - `C:\tboot-site` remains 100% clean, untouched, on branch `main` with 0 admin endpoints or exposed reference UI pages.

---

## 8. Test Verification

All automated test suites were executed and passed cleanly:

1. **Admin-Shell Reference Catalog Owner UI & RBAC Suite** (`admin-shell/tests/test_reference_catalog_owner_ui.py`):
   - `test_anonymous_forbidden_from_reference_catalog`: **PASSED**
   - `test_seller_forbidden_from_reference_catalog`: **PASSED**
   - `test_spoofed_owner_header_forbidden`: **PASSED**
   - `test_owner_reference_catalog_page_render_success`: **PASSED**
   - `test_owner_reference_models_proxy_success`: **PASSED**
   - `test_owner_review_queue_proxy_success`: **PASSED**
   - `test_owner_conflict_resolve_proxy_success`: **PASSED**
   - Result: **7 passed in 1.88s**

2. **Admin-Shell Regression Suites** (`test_reservations_rbac.py`, `test_unified_top_navigation_bar.py`, `test_seller_rbac_and_data_safety.py`):
   - Result: **25 passed in 86.57s (0 failures, 0 regressions)**

3. **Core Reference Catalog & Architecture Parity Suites** (`core/tests/test_product_reference_api.py`, `core/tests/test_product_reference_enricher.py`, `core/tests/test_product_reference_matcher.py`, `core/tests/test_product_reference_normalizer.py`, `core/tests/test_external_reference_enrichment.py`, `core/tests/test_stage05a_architecture_parity.py`, `core/tests/test_stage05a_quick_intake_and_ai.py`):
   - Result: **50 passed in 3.36s (0 failures)**

---

## 9. Database Health

Database integrity checks executed against `C:\tbootit\data\db\technoreboot.db`:
- `PRAGMA quick_check;`: `[('ok',)]`
- `PRAGMA foreign_key_check;`: `[]` (0 foreign key violations)

---

## 10. Screenshots Captured

The following visual artifacts were generated and saved in `C:\tbootit\AntiGravity\PROMPT_WEB_07D_REFERENCE_CATALOG_OWNER_REVIEW_UI\Outbox\screenshots\`:
1. `01_reference_catalog_models_list.png`: Full Reference Catalog view with KPI metric cards, filters, and paginated models table.
2. `02_reference_model_detail_modal.png`: Model Details modal top half showing canonical identity fields, verification state, and external datasheet source URLs.
3. `02b_reference_model_specifications_and_conflicts.png`: Model Details modal middle section showing editable specifications key-value table and inline conflict resolution box.
4. `02c_reference_model_linked_instances_protection.png`: Model Details modal bottom section displaying the Product Instance Protection warning banner and read-only linked product instances table with action controls.
5. `03_review_queue_and_conflicts.png`: "Требуют проверки" Review Queue tab showing external specification conflict cards and unresolved warehouse products with Core Matcher candidate suggestions.
6. `04_json_import_export_tab.png`: "Экспорт / Импорт JSON" tab for full catalog backup and dry-run JSON imports.

---

## 11. Git & Production Invariant

- **Target Commit Message**: `WEB-07D add owner reference catalog review UI`
- **Database / Media / Secrets**: Excluded from commit (runtime DB and media directories remain untracked).
- **Clean Worktree**: All tracked files clean upon commit.
- **Production Writes**: `PRODUCTION_WRITES=0` maintained throughout.

---

## 12. Conclusion & Verification Verdict

Stage WEB-07D is **PASS**. All functional, architectural, security, and visual criteria specified in `PROMPT_WEB_07D_REFERENCE_CATALOG_OWNER_REVIEW_UI.md` have been fulfilled.
