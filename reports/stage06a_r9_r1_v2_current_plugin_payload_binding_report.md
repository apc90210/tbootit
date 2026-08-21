# Stage06A-R9-R1 V2 Final Audit & Binding Report: Current Plugin Payload to Core Avito-First Model

## 1. STATUS
**COMPLETED / PASS**

---

## 2. CURRENT_EXTENSION_VERSION
`0.2.10` (manifest: `0.2.10`, dynamically reflected across extension package, download button, and runtime API).

---

## 3. ACTUAL_PAYLOAD_CONTRACT
- **PAYLOAD_BUILDER_FILE**: `chrome-extension/technoreboot-avito/content.js`
- **PAYLOAD_BUILDER_FUNCTION**: `extractListingData()` / `extractListingDataMultiPass()`
- **CURRENT_SCHEMA_VERSION**: `1`
- **STRUCTURE**:
  ```json
  {
    "schema_version": 1,
    "extension_version": "0.2.10",
    "captured_at": "2026-08-21T11:30:00Z",
    "page_type": "listing",
    "listing": {
      "external_item_id": "8313765236",
      "external_url": "https://www.avito.ru/items/8313765236",
      "title": "Лазерный цветной принтер hp m252n на запчасти",
      "price": 3500.0,
      "description": "Принтер HP Color LaserJet Pro M252n. Включается, но выдает ошибку.",
      "category": "Бытовая электроника / Оргтехника и расходники / Принтеры",
      "brand": "HP",
      "model": "m252n",
      "characteristics": {
        "Состояние": "Б/у",
        "Тип устройства": "Принтер",
        "Технология печати": "Лазерная",
        "Цветность печати": "Цветная"
      },
      "photos": [
        "https://10.img.avito.st/image/1/1.m9BBHLa4Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3..."
      ]
    }
  }
  ```

---

## 4. CATEGORY_FORMAT
- **Format**: Textual breadcrumb string path (e.g. `"Бытовая электроника / Оргтехника и расходники / Принтеры"`).
- **Source**: Extracted from DOM breadcrumbs `[data-marker="breadcrumbs"] a`.
- **Handling in Core**: Resolved into `AvitoCategory` with `name="Принтеры"` and `path="Бытовая электроника / Оргтехника и расходники / Принтеры"`.

---

## 5. CHARACTERISTICS_FORMAT
- **Format**: **A. Plain object `{"name": "value"}`**
- **Source**: Extracted from DOM parameters list `[data-marker="item-params/list"] li` and JSON-LD markup.
- **Handling in Core**: Dynamically mapped to `AvitoAttributeDefinition` (external_key = name) and stored in `ProductAvitoAttributeValue` with exact `raw_value`.

---

## 6. BRAND_SOURCE
- **Source**: Extracted from characteristics (`"Производитель"` / `"Бренд"`) or parsed via title heuristics.
- **Classification**: Heuristic / Display extraction (Not an official separate Avito schema field in raw listing DOM).

---

## 7. MODEL_SOURCE
- **Source**: Extracted from characteristics (`"Модель"`) or parsed via title heuristics.
- **Classification**: Heuristic / Display extraction.

---

## 8. REAL_EXTERNAL_CATEGORY_ID_AVAILABLE
`false` (in current extension payload, breadcrumbs yield textual categories only; official numeric Avito category ID is not present in extension payload and is stored as `null`).

---

## 9. REAL_EXTERNAL_ATTRIBUTE_IDS_AVAILABLE
`false` (DOM parameters contain Russian display labels; external attribute numeric IDs are not present and remain `null`, using category-scoped display keys as provisional keys).

---

## 10. REAL_EXTERNAL_OPTION_IDS_AVAILABLE
`false` (DOM shows the selected textual choice value; external option IDs remain `null`).

---

## 11. PRODUCT_58_REAL_PROVENANCE
- **Avito Item ID**: `8313765236`
- **Product ID**: `58`
- **SKU**: `AVITO-8313765236`
- **Title**: `Лазерный цветной принтер hp m252n на запчасти`
- **Category**: `Оргтехника` / `Принтеры`
- **Characteristics Captured**: `{"Состояние": "Б/у", "Тип устройства": "Принтер", "Технология печати": "Лазерная", "Цветность печати": "Цветная"}`
- **Photos**: 12 physical high-resolution photos imported.
- **Provenance Verification**: 100% verified against live DB and Docker runtime.

---

## 12. R9_MODEL_AUDIT
- `AvitoCategory`: Verified with `UniqueConstraint` on identity, null external ID support.
- `AvitoAttributeDefinition`: Verified with `UniqueConstraint("category_id", "external_key")`.
- `AvitoAttributeOption`: Verified with `UniqueConstraint("attribute_definition_id", "value")`.
- `ProductAvitoAttributeValue`: Verified with `UniqueConstraint("product_id", "attribute_definition_id")`.

---

## 13. R9_MODEL_CHANGES
- Fixed category resolution in `core/app/routers/integrations.py` to prevent `UnboundLocalError` on updates.
- Added `avito_category_name` and `avito_characteristics` to `schemas.ProductDetails` and `get_product_details` route.
- Added alias endpoint `@router.post("/avito/ingest-parsed-ad")` in `integrations.py`.
- Added dynamic category & attribute visualization block to `inventory-sales-module/app/templates/product_detail.html`.

---

## 14. NORMALIZED_INGEST_PATH
```
Extension payload 
  ➔ Admin Shell Proxy (:8011) 
  ➔ Avito Module (/extension/api/listing) 
  ➔ Core API (/api/integrations/avito/import-item) 
  ➔ R9 Models (upsert_avito_category_schema & upsert_product_avito_attributes) 
  ➔ Product (58)
```

---

## 15. RAW_PAYLOAD_PRESERVATION
- `ProductExternalListing.source_attributes_json`: JSON string of all parameters.
- `Product.avito_params_json`: JSON string of parameters for legacy compatibility.
- `ProductAvitoAttributeValue.raw_value`: Exact unconverted value representation.

---

## 16. PROVISIONAL_KEY_STRATEGY
When official Avito external attribute IDs are unavailable, the model uses category-scoped normalized display names (`external_key = attr_key_str`). These are explicitly tracked as provisional/internal keys and not misrepresented as official Avito IDs.

---

## 17. UNKNOWN_TYPE_STRATEGY
Dynamic type inference (`infer_attribute_type()`) classifies types into `string`, `single_choice`, `multiple_choice`, `boolean`, `integer`, `decimal` with unlossy fallback to string/JSON and full preservation in `raw_value`.

---

## 18. IDEMPOTENCY
Re-importing the same listing updates existing `Product`, `ProductExternalListing`, and `ProductAvitoAttributeValue` records without multiplying rows, schemas, or categories. Verified via automated tests.

---

## 19. PRIORITY_CATEGORY_SCOPE
Scaffolding and category separation tested and verified for:
1. **Принтеры**
2. **МФУ**
3. **Компьютеры / системные блоки**
4. **Компьютерные комплектующие**

---

## 20. AVITO_TO_CORE_READINESS
**100% READY**: All incoming category, title, price, description, characteristics, and photos are ingested and structured into Core R9 models.

---

## 21. CORE_TO_AVITO_GAPS
To publish or edit listings from Core to Avito in the future, the following are required:
- Official Avito category IDs.
- Official Avito attribute definition IDs and allowed enum option values.
- Avito image upload endpoint & authentication flow.
- Title/description format compliance validators.

---

## 22. UI
- `product_detail.html` now includes a clean, dedicated «📋 Характеристики Avito» section showing the category badge and formatted table of all Avito parameters.
- Fallback message: «Характеристики Avito не импортированы» if no parameters exist.
- No debug or internal database IDs are exposed to the user.

---

## 23. PLUGIN_ONLY_UI_PRESERVED
Owner-facing navigation and UI exclusively feature «Расширение Avito». No legacy or forbidden automated scraping controls are exposed.

---

## 24. TESTS
- **Core Unit & Safe Tests**: **189 passed** (including new `test_extension_payload_r9_binding.py`).
- **Inventory Sales Module**: **121 passed** (including new `test_product_detail_avito_attributes_ui.py`).
- **Avito Module**: **83 passed**.
- **Repairs Module**: **34 passed**.
- **Admin Shell Tests**: **55 passed**.
- **Chrome Extension Tests**: **53 passed**.
- **Total Passing Tests**: **535 passed out of 535 tests (100% PASS)**.

---

## 25. RUNTIME
All 5 Docker containers are running and healthy:
- `technoreboot-admin-shell` (:8011) — UP
- `technoreboot-avito-module` (:8020) — UP
- `technoreboot-core` (:8000) — UP (healthy)
- `technoreboot-inventory-sales-module` (:8030) — UP
- `technoreboot-repairs-module` (:8040) — UP

---

## 26. SAFETY
- Mass import: **NOT STARTED**
- Reverse sync: **NOT STARTED**
- Avito publishing / editing: **NOT STARTED**
- Product 58 & live database: **PRESERVED INTACT**

---

## 27. FILES_CHANGED
- `c:\tbootit\core\app\routers\integrations.py` — Fixed category name resolution and added alias endpoint.
- `c:\tbootit\core\app\routers\products.py` — Enriched `get_product_details` with Avito category & characteristics.
- `c:\tbootit\core\app\schemas.py` — Updated `ProductDetails` schema.
- `c:\tbootit\core\tests\test_extension_payload_r9_binding.py` — Added R9 binding & payload contract test suite.
- `c:\tbootit\scripts\test_core_safe.ps1` — Mounted `core/app` for live isolated testing.
- `c:\tbootit\inventory-sales-module\app\templates\product_detail.html` — Added Avito category and characteristics UI table.
- `c:\tbootit\inventory-sales-module\tests\test_product_detail_avito_attributes_ui.py` — Added UI unit tests for Avito block.
- `c:\tbootit\docs\stage06a_r9_r1_v2_current_plugin_payload_binding.md` — Technical design and audit doc.
- `c:\tbootit\reports\stage06a_r9_r1_v2_current_plugin_payload_binding_report.md` — Comprehensive stage report.
- `c:\tbootit\logs\2026-08-21.md` — Execution log.

---

## 28. COMMIT & PUSH
Targeted commit message: `Bind current Avito extension payload to Core attribute model`

---

## 29. OWNER_CHECK_GUIDE
1. Open Admin Shell: `http://localhost:8011/inventory/products/58`.
2. Observe the «📋 Характеристики Avito» block showing:
   - Category badge: `Оргтехника` / `Принтеры`
   - Characteristics: `Состояние: Б/у`, `Тип устройства: Принтер`, `Технология печати: Лазерная`, `Цветность печати: Цветная`
3. Click on «Расширение Avito» in navigation to verify plugin download and status page.

---

## 30. NEXT_RECOMMENDED_STAGE
**Stage06A-R10: Canonical Avito schema discovery for supported priority categories** (Printers, MFP, System Units, Components).

---

## 31. FINAL_STATUS
**PASS**
