# Stage 07D-R1-R1 — Product Editor Sale Price Validation Fix

## 1. Overview & Problem Statement

In Stage 07D-R1, the Owner product editor at `/inventory/products/{id}/edit` failed when saving an existing product (reproduced on Product #168) after editing the description:
- HTTP 400 with raw Pydantic validation error:
  `[{'type': 'float_type', 'loc': ['body', 'sale_price'], 'msg': 'Input should be a valid number', 'input': None, 'url': 'https://errors.pydantic.dev/2.6/v/float_type'}]`
- The Owner interface exposed internal schema types and external URLs (`pydantic.dev`).
- The editor displayed two confusing price inputs: `Цена (базовая)` and `Цена продажи (актуальная)`, representing the same underlying business concept.

## 2. Root Cause Analysis

1. **Dual Price UI Ambiguity**: The HTML template previously included both `<input name="price">` and `<input name="sale_price">`. In the canonical SQLite schema, the `products` table has only `sale_price` and `purchase_price` (there is no `price` column).
2. **Missing Price on Existing Detail**: When existing product details were returned by Core, `sale_price` held the value while `price` was undefined (`None`).
3. **Empty Input to Null Conversion**: Submitting the form with an empty `sale_price` input resulted in `{"sale_price": null}` in the update payload.
4. **Strict Schema in Core**: `ProductFullUpdate.sale_price` in Core schema was typed as non-optional `float`. Pydantic rejected `None` with a `422 Unprocessable Entity` (`float_type`).
5. **Raw Error Leakage**: Inventory Sales Module directly rendered Core's raw validation detail list to the user without formatting or stripping external links.

## 3. Architecture & Price Semantics Audit

| Field Concept | DB Column / Canonical Name | JSON Import Mapping | Avito Import Mapping | Web UI Field Label |
|---|---|---|---|---|
| **Sale Price** | `products.sale_price` (`REAL`) | `product.price` / `product.sale_price` | `item.price` -> `sale_price` | **Цена продажи (₽) \*** |
| **Cost / Purchase Price** | `products.purchase_price` (`REAL`) | `product.cost_price` / `product.purchase_price` | N/A | **Себестоимость / Закупка (₽)** (опционально) |
| **Old "Price" Alias** | N/A (virtual alias in `ProductDetails`) | Synthesized as `p_dict["price"] = db_product.sale_price` | Synthesized for backward compatibility | **REMOVED duplicate from UI** |

### Key Business Rules:
- **Single Sale Price Field**: The duplicate `Цена (базовая)` field was permanently removed from `product_edit.html`. There is now exactly one required sale price input: `Цена продажи (₽) *`.
- **Decimal Comma Normalization**: The parser accepts both `8500.50` and `8500,50`, normalizing commas to decimal points before conversion to `float`.
- **Existing Price Preservation**: If an existing product already has a price and the edit submission does not modify it (or leaves the field untouched), the existing price is preserved.
- **Legacy Products with Null Price**: If a legacy product historically has `sale_price = None`, saving description or characteristics without setting a price is permitted without validation errors.
- **Safe Russian Error Presentation**: Pydantic 422 lists and errors are intercepted by `format_core_error()`, which maps field names to friendly Russian names (e.g. `sale_price` -> `Цена продажи`) and strips all URLs.

## 4. Implementation Details

### Core (`core/app/`)
- `schemas.py`:
  - `ProductFullUpdate.sale_price: Optional[float] = None`
  - `ProductDetails.price: Optional[float] = None` (backward compatibility alias matching `sale_price`)
- `routers/products.py`:
  - In `get_product_details`: added `p_dict["price"] = db_product.sale_price`.
  - In `full_update_product`: only updates `db_product.sale_price` if `product.sale_price is not None`, preventing unintentional resets to null. Also ensures `db_product.description` is updated.

### Inventory Sales Module (`inventory-sales-module/app/`)
- `templates/product_edit.html`:
  - Removed duplicate `Цена (базовая, ₽)`.
  - Maintained single `Цена продажи (₽) *` field pre-populated with `product.sale_price if product.sale_price is not none else (product.price or '')`.
- `routers/products.py`:
  - Added `format_core_error(detail)` to convert validation dictionaries and strings into Russian messages without tracebacks or `pydantic.dev` URLs.
  - Updated `_extract_product_payload` to accept `existing_product`, normalize decimal comma to dot, and preserve omitted fields on edit.
  - Updated `_validate_product_payload` to validate `sale_price` presence and non-negativity with clear Russian error `"Укажите корректную цену продажи."`.
  - Updated `update_product_full_endpoint` to fetch existing product details and pass to payload extraction and validation.

## 5. Verification Matrix

- **Reproduction Case (Product #168)**: Description edited without changing price -> saved successfully with 303 redirect.
- **JSON Imported Product (#157)**: Description updated -> 6500 ₽ price preserved.
- **Avito Product (#5)**: Description updated -> 100 ₽ price preserved.
- **Manual Product (#167)**: Description updated -> 44000 ₽ price and RAM/CPU characteristics preserved.
- **Legacy Product (#1)**: Legacy null price product edited -> saved cleanly without 422 error.
- **Integer Price Update**: Saved `29000` -> verified on product card.
- **Decimal Comma Update**: Saved `29550,50` -> normalized and verified as `29550.5` on product card.
- **Invalid Price Validation**: Empty/whitespace sale price on non-legacy product -> returned clean Russian error `"Укажите корректную цену продажи."` with no raw Pydantic errors or URLs.
