# TECHNOREBOOT — Stage 07D-R1
## Full Product Create/Edit UI + Characteristics + Photo Manager

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07D-R1 — Product Create/Edit and Photo Manager`

---

# 0. EXECUTION CONTRACT

Stage 07C JSON import/export UX is accepted.

Known Avito limitation remains accepted for now:
- Avito import may bring only the main photo;
- do NOT work on full Avito multi-photo extraction in this stage.

This new stage implements the missing normal product editor for everyday work.

Owner must be able to:

- create a product manually;
- open an existing product and edit it;
- change common fields;
- edit category-specific characteristics;
- add/remove/reorder photos;
- choose the main photo;
- save changes through the web UI;
- do all of this without CLI.

Do NOT redesign the whole architecture.
Do NOT bypass Core business logic.
Do NOT write directly to DB from Admin Shell/Inventory UI.
Do NOT start Internet deployment.
Do NOT change JSON canonical contract unless required for compatibility bugfixes.
Do NOT return to Avito full-gallery extraction.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07D_R1_PRODUCT_CREATE_EDIT_AND_PHOTO_MANAGER_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07D_R1_PRODUCT_CREATE_EDIT_AND_PHOTO_MANAGER_PROMPT.md`

Treat the copied prompt as authoritative.

---

# 1. OWNER GOAL

The current system can list products, show product detail cards, import from Avito and JSON, but Owner needs a normal editor.

Required workflow:

## Existing product

`Товары -> открыть товар -> Редактировать товар -> изменить -> Сохранить`

## New manual product

`Товары -> + Создать товар вручную -> заполнить -> Сохранить -> открыть карточку`

The editor must be practical, Russian-language and consistent with current UI.

---

# 2. FIRST — AUDIT CURRENT PRODUCT MODEL AND ROUTES

Before implementation inspect current:

- Core `Product` model;
- categories;
- Core product create/update routes;
- inventory-sales product list/detail routes;
- Avito attribute storage;
- JSON import service;
- `ProductPhoto` model;
- photo upload/storage helpers;
- media route;
- barcode/SKU logic;
- status/location/quantity conventions;
- current category schema and characteristics API.

Do not invent duplicate product fields.

Final report must include:

```text
CURRENT_CREATE_API:
CURRENT_UPDATE_API:
CURRENT_PHOTO_API:
CURRENT_CHARACTERISTICS_STORAGE:
REUSED_EXISTING_SERVICES:
```

---

# 3. PRODUCT LIST ACTIONS

On main product list `/inventory/products` keep all current controls and add:

`+ Создать товар вручную`

Keep existing:

`+ Добавить новый товар через JSON`

Do not remove:
- Все
- Магазин
- Мастерская
- Архив
- Черновики

Preferred top controls:

```text
Все | Магазин | Мастерская | Архив | Черновики

[ + Создать товар вручную ]
[ + Добавить новый товар через JSON ]
```

Both actions should be visible without scrolling.

---

# 4. PRODUCT DETAIL ACTION

On `/inventory/products/{product_id}` add a clear button:

`Редактировать товар`

It must open the editor for that exact product.

Preferred route:

`/inventory/products/{product_id}/edit`

Use actual project routing conventions if another path is more appropriate.

Keep current product detail page usable and unchanged except for editor entry point.

---

# 5. MANUAL CREATE PAGE

Use the same editor form in CREATE mode where practical.

Preferred route:

`/inventory/products/new`

Required fields/sections:

## Basic
- Название
- Категория
- Бренд
- Модель
- Состояние

## Prices
- Цена продажи
- Закупочная цена

## Inventory
- Количество
- Статус
- Место хранения
- SKU / артикул
- Штрихкод

SKU behavior:
- if empty, generate through existing Core mechanism;
- do not duplicate SKU generation logic in frontend.

## Description
- large textarea
- preserve line breaks

## Characteristics
category-aware dynamic section.

## Photos
optional on create.

Buttons:

- `Сохранить товар`
- `Отмена`

After successful create:
- show success message;
- provide `Открыть товар`;
- preferably automatically navigate to created product detail page, unless current UX conventions strongly favor staying on form.

No duplicate creation on repeated click.

Disable/save guard while request is in progress.

---

# 6. EDIT PAGE

For existing product, prefill ALL current values.

Owner must be able to edit:

- title;
- category;
- brand;
- model;
- sale price;
- purchase price;
- condition;
- status;
- quantity;
- storage location;
- barcode;
- description;
- category-specific characteristics.

SKU:
- display it clearly;
- whether editable or readonly must follow current Core uniqueness/business rules;
- if editing is supported, enforce uniqueness safely;
- do not casually allow duplicate SKU.

Buttons:

- `Сохранить изменения`
- `Отмена`
- optionally `Вернуться к товару`

After successful save:
- show clear success state;
- no raw API JSON;
- product detail page must reflect edits.

---

# 7. CATEGORY-SPECIFIC CHARACTERISTICS

This is important.

Technoreboot uses category-specific characteristics that should stay compatible with current Avito-oriented schema.

The editor must load the current schema for the selected category.

Do NOT use one fixed universal set of characteristics.

Expected categories include at least:

- Ноутбуки
- Системные блоки
- Принтеры и МФУ
- Мониторы
- Комплектующие
- Оргтехника

Use existing current category schema service/Avito mappings.

## Behavior

When category selected:

1. load known characteristics;
2. show current values;
3. allow edit;
4. allow blank/unknown values;
5. do not invent values;
6. preserve unknown existing characteristics if they exist and cannot be mapped;
7. do not silently delete characteristics that are not currently rendered unless Owner explicitly removes them.

If category changes:
- warn before dropping incompatible values;
- preferably preserve previous values until save;
- make data loss explicit.

---

# 8. PHOTO MANAGER

This is mandatory.

The Owner previously identified that there was no normal way to add/remove product photos.

Editor must support:

## Upload

- choose one or multiple local image files;
- JPEG / PNG / WebP at minimum if current backend supports them;
- use persistent product photo storage;
- enforce current safe size limit;
- show upload errors per file.

## Preview

Show existing photos as thumbnails/cards.

Each photo should display:

- preview;
- current order/position;
- source indicator if useful (`local`, `Avito`, etc.) without clutter.

## Delete

Each photo:
`Удалить`

Require a simple confirmation before permanent deletion.

Deletion must remove:
- DB photo row;
- local file when owned by Technoreboot and safe to delete.

Do not delete arbitrary external files/URLs.

## Reorder

Owner can change photo order.

Simple implementation is enough:

- `↑` / `↓` buttons;
or
- drag-and-drop.

No need for complex library.

Persist order in `ProductPhoto.position` or current equivalent.

## Main photo

Allow Owner to choose:

`Сделать главной`

The main photo should be position `0` or use current canonical main-photo mechanism.

Product list/detail should use this main photo.

## Persistence

Photos must:
- persist in `/data/storage/product_photos` or current canonical storage;
- survive Core restart;
- be included in backup;
- be served by current `/media/...` route.

No `/tmp` durable success.

---

# 9. PHOTO ERROR HANDLING

If one photo upload fails:

- do not crash the whole editor;
- show which file failed;
- successful uploads remain accounted for;
- no raw stack trace.

If storage unavailable:
- structured safe error;
- do not claim photo was saved.

---

# 10. SAVE SEMANTICS

Common product edits and characteristics should save through Core.

Prefer one clear update transaction for product fields + characteristics where possible.

Photo operations may use separate endpoints.

Do not make Admin Shell or inventory-sales-module directly mutate SQLite.

Core remains owner of business data.

---

# 11. UNSAVED CHANGES

Basic protection required.

If user changes form fields and tries to leave page:
- browser warning or simple unsaved-changes warning is desirable.

At minimum:
- Cancel should not save anything;
- Save should clearly indicate success/failure.

Do not overengineer.

---

# 12. VALIDATION

Frontend + backend validation.

At minimum:

- title required;
- valid numeric sale price;
- purchase price numeric or blank/null;
- quantity integer >= 0;
- valid status;
- category valid;
- SKU/barcode uniqueness according to current rules;
- image file type/size.

Russian-language errors.

No raw Pydantic/SQLAlchemy stack output in browser.

---

# 13. ACCESS CONTROL

Follow current product management policy.

Verify through real gateway:

OWNER:
- list
- detail
- create
- edit
- photo upload/delete/reorder

USER:
- follow same established product-management permissions as current system;
- document actual policy.

No client certificate:
- gateway denies access.

Do not create another auth layer.

---

# 14. REQUIRED API / CORE CAPABILITIES

Reuse existing routes if present.

If missing, add minimal Core endpoints/services for:

- create product;
- update product;
- get category schema;
- set/update characteristics;
- upload photo(s);
- delete photo;
- reorder photos / set main photo.

Example only:

```text
POST   /api/products/
PUT    /api/products/{id}
POST   /api/products/{id}/photos
DELETE /api/products/{id}/photos/{photo_id}
POST   /api/products/{id}/photos/reorder
```

Use actual project conventions.

Do not duplicate overlapping endpoints unnecessarily.

---

# 15. REQUIRED TESTS

## TEST A — manual create
Create one product manually through API/UI equivalent.

Verify generated SKU when blank.

## TEST B — edit common fields
Change:
- title;
- price;
- purchase price;
- description;
- condition;
- quantity;
- storage location.

Verify persistence.

## TEST C — category characteristics
Edit laptop characteristics and verify round-trip.

## TEST D — printer/MFP characteristics
Edit printer/MFP characteristics and verify round-trip.

## TEST E — unknown characteristics safety
Existing extra characteristic is not silently destroyed.

## TEST F — product detail entry
`Редактировать товар` is visible and opens correct product.

## TEST G — product list create entry
`+ Создать товар вручную` visible.

## TEST H — JSON shortcut preserved
`+ Добавить новый товар через JSON` still visible/works.

## TEST I — photo upload
Upload 2 local photos.

Verify:
- two DB rows;
- two persistent files;
- media HTTP 200.

## TEST J — photo reorder
Swap order and verify new order survives reload.

## TEST K — main photo
Set second photo as main and verify product card/list uses it.

## TEST L — photo delete
Delete one photo:
- row removed;
- owned local file removed;
- remaining photo valid.

## TEST M — restart persistence
Restart Core; photo and edits remain.

## TEST N — backup regression
Backup includes current product photos.

## TEST O — validation
Invalid title/price/quantity/file rejected safely.

## TEST P — duplicate SKU
Handled safely.

## TEST Q — JSON import regression
Still works.

## TEST R — JSON selected/full export regression
Still works.

## TEST S — Avito import regression
Current accepted Avito flow still works with known single-main-photo limitation.

## TEST T — Core full tests
Pass.

## TEST U — inventory-sales/admin-shell relevant tests
Pass.

## TEST V — OWNER mTLS
Real gateway access works; no-cert denied.

Report exact totals.

---

# 16. OWNER MANUAL CHECK

Browser-only.

Use an existing disposable/test product.

1. Open `Товары`.
2. Confirm both buttons:
   - `+ Создать товар вручную`
   - `+ Добавить новый товар через JSON`
3. Open an existing product.
4. Click `Редактировать товар`.
5. Change description and price.
6. Change/add at least two characteristics.
7. Upload TWO local photos.
8. Save.
9. Re-open product and verify changes.
10. Return to editor.
11. Swap photo order / make second photo main.
12. Delete one photo.
13. Save/reload and confirm state remains.
14. Create one new product manually from `+ Создать товар вручную`.
15. Confirm it appears in product list.

No CLI.

---

# 17. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07D_R1_PRODUCT_CREATE_EDIT_AND_PHOTO_MANAGER_PROMPT.md`

Create/update:

`docs\stage07d_r1_product_create_edit_and_photo_manager.md`

`reports\stage07d_r1_product_create_edit_and_photo_manager_report.md`

`logs\2026-09-10.md`

---

# 18. GIT / SAFETY

Before commit:
- no runtime DB;
- no real owner product photos;
- no exported JSON;
- no backup ZIP;
- no auth secrets;
- no tokens.

Commit source/tests/docs only.

Push `origin/main`.

Verify clean worktree.

---

# 19. FINAL REPORT CONTRACT

Return:

```text
# Stage 07D-R1 — Product Create/Edit and Photo Manager

## Existing Architecture Audit
CURRENT_CREATE_API:
CURRENT_UPDATE_API:
CURRENT_PHOTO_API:
CURRENT_CHARACTERISTICS_STORAGE:
REUSED_EXISTING_SERVICES:

## Product List / Detail
MANUAL_CREATE_BUTTON:
JSON_CREATE_BUTTON_PRESERVED:
EDIT_PRODUCT_BUTTON:
CREATE_ROUTE:
EDIT_ROUTE:

## Product Editor
COMMON_FIELDS_EDITABLE:
SKU_POLICY:
VALIDATION:
SAVE_BEHAVIOR:

## Characteristics
CATEGORY_AWARE:
LAPTOP:
PRINTER_MFP:
UNKNOWN_FIELDS_PRESERVED:
CATEGORY_CHANGE_POLICY:

## Photos
MULTI_UPLOAD:
PERSISTENT_STORAGE:
PREVIEW:
DELETE:
REORDER:
SET_MAIN:
SURVIVES_RESTART:
BACKUP_INCLUDED:

## Regression
JSON_IMPORT:
JSON_EXPORT:
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
TECHNOREBOOT_STAGE07D_R1_PRODUCT_EDITOR_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If Owner cannot edit description + characteristics + add/delete/reorder photos from web UI, return BLOCKED.

---

# 20. STOP

After implementation, verification, docs, commit/push and report:

STOP.

Do not start Internet deployment.
Wait for Owner acceptance.
