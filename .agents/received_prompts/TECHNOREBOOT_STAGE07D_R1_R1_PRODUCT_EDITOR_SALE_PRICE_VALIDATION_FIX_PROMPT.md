# TECHNOREBOOT — Stage 07D-R1-R1
## Fix product editor save failure: `sale_price = null` / Pydantic float_type

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07D-R1-R1 — Product Editor Sale Price Validation Fix`

---

# 0. EXECUTION CONTRACT

Stage 07D-R1 is NOT accepted yet.

Owner attempted to edit an existing product through the new web editor and Save failed with a raw Pydantic validation error:

```text
[{
  'type': 'float_type',
  'loc': ['body', 'sale_price'],
  'msg': 'Input should be a valid number',
  'input': None,
  'url': 'https://errors.pydantic.dev/2.6/v/float_type'
}]
```

This means the editor/proxy sent:

```json
"sale_price": null
```

to a Core schema that currently requires a valid float.

This is a real Owner workflow bug.

The stage must:

1. reproduce the exact failure through the web editor;
2. prove why `sale_price` becomes `null`;
3. fix the price-field contract cleanly;
4. remove any confusing duplicate price semantics in the UI if present;
5. prevent raw Pydantic errors from being shown to Owner;
6. preserve all already-working editor/photo/JSON/Avito behavior.

Do NOT redesign the product model broadly.
Do NOT start Internet deployment.
Do NOT return to Avito multi-photo work.
Do NOT use CLI in Owner workflow.

First copy this prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07D_R1_R1_PRODUCT_EDITOR_SALE_PRICE_VALIDATION_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07D_R1_R1_PRODUCT_EDITOR_SALE_PRICE_VALIDATION_FIX_PROMPT.md`

---

# 1. REPRODUCE THE OWNER BUG FIRST

Use a real existing product that can currently open in:

`/inventory/products/{product_id}/edit`

Do not use only a synthetic API unit test.

Capture:

```text
PRODUCT_ID:
EDITOR_GET_STATUS:
FORM_PRICE_FIELDS:
FORM_VALUES:
POST/PUT_TARGET:
OUTGOING_REQUEST_JSON:
CORE_SCHEMA:
CORE_STATUS:
CORE_RESPONSE:
```

Explicitly prove which field in the HTML/form maps to Core `sale_price`.

Determine why it becomes `None`.

Possible causes to investigate, NOT assume:

- form uses `price`, Core expects `sale_price`;
- editor contains both `price` and `sale_price` and only one is filled;
- existing product detail API returns `price` but editor expects `sale_price`;
- blank HTML input is converted to `None`;
- `core_client.py` maps a missing field to `None`;
- a legacy/imported product has `sale_price = null`;
- template uses wrong variable;
- create and edit modes use different field names.

Final report must state exact proven root cause.

---

# 2. AUDIT PRICE SEMANTICS

Before fixing, inspect the actual canonical product model and current flows:

- Product DB/model price fields;
- JSON import contract (`price`);
- Avito import mapping;
- sales module;
- product detail response;
- editor create/update schema;
- receipt/sales logic.

Answer:

```text
CANONICAL_SALE_PRICE_FIELD:
JSON_PRICE_MAPS_TO:
AVITO_PRICE_MAPS_TO:
PURCHASE_PRICE_FIELD:
OTHER_PRICE_FIELD_EXISTS:
```

If the editor currently shows both something like:

- `Розничная цена`
- `Цена продажи`

but they represent the same underlying value, REMOVE the duplicate from the Owner UI and keep one clear field:

`Цена продажи`

Do not maintain two editable fields for one business concept.

If they are genuinely different business fields, document the difference and map both correctly.

---

# 3. REQUIRED SAVE CONTRACT

For EDIT mode:

- if product already has a sale price and Owner does not change it, save must preserve it;
- if Owner enters a valid number, save new value;
- empty optional price field must not be converted into invalid `null` for a required Core field;
- if sale price is truly mandatory, frontend must require it and show a Russian message before API call;
- if current business rules allow a product without sale price (e.g. draft), Core update schema may accept `Optional[float]`, but persistence semantics must be explicit.

Choose behavior based on current actual system rules, not convenience.

For CREATE mode:

- if sale price is required, prevent create without it;
- if optional for draft, handle it consistently with edit.

No `float_type` should reach the Owner.

---

# 4. UPDATE SCHEMA SEMANTICS

Important distinction:

A full update model and a partial update model are not the same.

Inspect `ProductFullUpdate`.

If it is intended to represent a complete form submission:
- ensure frontend always sends valid required values.

If it is intended to support partial updates:
- fields not supplied should be optional;
- `None` should mean either “clear value” only when the DB/business model permits it;
- otherwise omit field rather than send null.

Do not blindly make every float Optional just to silence Pydantic.

The fix must preserve data integrity.

---

# 5. FRONTEND NORMALIZATION

In the web editor:

- numeric inputs should be parsed deliberately;
- blank string must not accidentally become `None` for required numeric fields;
- decimal comma input (`8500,50`) may either be normalized or rejected with a clear Russian message;
- valid examples:
  - `8500`
  - `8500.50`

Preferred Owner error:

`Укажите корректную цену продажи.`

Not:

`float_type ... pydantic.dev`

---

# 6. SAFE ERROR PRESENTATION

Inventory Sales Module must translate Core validation errors into readable Russian UI.

For 422 validation errors:
- parse the safe validation detail;
- map known fields to Russian labels;
- do not render Python repr/list/dict directly;
- do not expose Pydantic documentation URLs.

Example:

```text
Не удалось сохранить товар:
Цена продажи должна быть числом.
```

No raw traceback.

---

# 7. REGRESSION FOR EXISTING PRODUCTS

Mandatory live checks on at least:

1. product created through JSON import;
2. product imported from Avito if available;
3. manually created product;
4. older/legacy product with missing/null optional fields.

For each:
- open editor;
- change ONLY description;
- save;
- verify price is preserved;
- no 422.

This is important because existing products may have different historical field shapes.

---

# 8. REQUIRED TESTS

## TEST A
Reproduce exact old failure: `sale_price=None` -> 422 before fix.

## TEST B
Existing product: edit description only -> save succeeds and sale price unchanged.

## TEST C
Change sale price to valid integer -> persists.

## TEST D
Change sale price to valid decimal -> persists.

## TEST E
Blank required sale price -> controlled Russian validation, no API/raw Pydantic error.

## TEST F
Purchase price blank/null follows current intended optional policy.

## TEST G
JSON-imported product can be edited and saved.

## TEST H
Avito-imported product can be edited and saved.

## TEST I
Manual product can be edited and saved.

## TEST J
Legacy product with optional null fields can be edited without unrelated validation failure.

## TEST K
No duplicate confusing sale-price fields in UI unless genuinely distinct business concepts.

## TEST L
Create form price semantics match edit form.

## TEST M
Characteristics remain preserved after edit.

## TEST N
Photos remain preserved after edit.

## TEST O
Photo manager regression passes.

## TEST P
JSON import/export regressions pass.

## TEST Q
Avito accepted regression flow passes.

## TEST R
Core full test suite passes.

## TEST S
Inventory Sales full test suite passes.

## TEST T
Admin Shell relevant suite passes.

## TEST U
OWNER gateway access remains valid.

Report exact totals.

---

# 9. OWNER MANUAL CHECK

Browser-only:

1. Open the SAME product that previously failed.
2. Click `Редактировать товар`.
3. Change only the description.
4. Click `Сохранить изменения`.
5. Expected: save succeeds; no Pydantic message.
6. Reopen editor.
7. Change `Цена продажи` to another valid number.
8. Save and verify product card shows new price.
9. Reopen editor and verify characteristics/photos are still present.

No terminal.

---

# 10. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07D_R1_R1_PRODUCT_EDITOR_SALE_PRICE_VALIDATION_FIX_PROMPT.md`

Create/update:

`docs\stage07d_r1_r1_product_editor_sale_price_validation_fix.md`

`reports\stage07d_r1_r1_product_editor_sale_price_validation_fix_report.md`

`logs\2026-09-10.md`

---

# 11. GIT / SAFETY

Do not commit:
- runtime DB;
- real Owner photos;
- exported JSON;
- backups;
- secrets/tokens.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

---

# 12. FINAL REPORT CONTRACT

Return:

```text
# Stage 07D-R1-R1 — Product Editor Sale Price Validation Fix

## Reproduction
PRODUCT_ID:
FORM_PRICE_FIELDS:
OUTGOING_REQUEST_JSON_BEFORE:
CORE_SCHEMA_BEFORE:
CORE_RESPONSE_BEFORE:
PROVEN_ROOT_CAUSE:

## Price Semantics
CANONICAL_SALE_PRICE_FIELD:
JSON_PRICE_MAPS_TO:
AVITO_PRICE_MAPS_TO:
PURCHASE_PRICE_FIELD:
DUPLICATE_PRICE_UI_REMOVED:

## Fix
FRONTEND_MAPPING_FIXED:
CORE_SCHEMA_CHANGED:
CLIENT_MAPPING_FIXED:
SAFE_422_UI:
REQUIRED_PRICE_POLICY:

## Live Verification
JSON_IMPORTED_PRODUCT:
AVITO_IMPORTED_PRODUCT:
MANUAL_PRODUCT:
LEGACY_PRODUCT:
DESCRIPTION_ONLY_EDIT:
SALE_PRICE_EDIT:
CHARACTERISTICS_PRESERVED:
PHOTOS_PRESERVED:

## Regression
PHOTO_MANAGER:
JSON:
AVITO:
OWNER_MTLS:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07D_R1_R1_SALE_PRICE_FIX_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If editing an existing product without changing price can still send `sale_price: null`, return BLOCKED.

---

# 13. STOP

After fix, tests, docs, commit/push and report:

STOP.

Do not start Internet deployment.
Wait for Owner acceptance.
