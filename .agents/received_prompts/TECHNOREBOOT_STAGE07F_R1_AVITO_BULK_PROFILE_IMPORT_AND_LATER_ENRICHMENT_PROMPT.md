# TECHNOREBOOT — Stage 07F-R1
## Avito Bulk Profile Import + Later Per-Listing Enrichment

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07F-R1 — Avito Bulk Profile Import and Enrichment`

---

# 0. EXECUTION CONTRACT

This stage is prioritized before VDS deployment because Owner needs to quickly fill the Technoreboot database from the existing Avito account TODAY.

The feature must work through the existing Technoreboot Chrome Extension.

Goal:

1. Owner opens the Avito page containing all listings of the current Avito user/profile.
2. Presses one extension action:
   `Импортировать все объявления`
3. Extension walks through all available listing pages/pagination.
4. Every listing is quickly added/upserted into Technoreboot with the lightweight data visible in list/profile pages.
5. Later Owner may open ANY individual Avito listing and press:
   `Доимпортировать данные`
6. The same Technoreboot product is enriched with fuller information:
   - description;
   - photos available through the current accepted single-listing import flow;
   - characteristics;
   - model/brand/category/address/etc. when available.
7. Enrichment must UPDATE the existing product, NEVER create a duplicate for the same Avito item.

Known accepted limitation remains:
- current Avito single-listing flow may import only the main photo;
- do NOT reopen the difficult full-gallery extraction problem in this stage.

Do NOT redesign the extension architecture.
Do NOT require official Avito API/OAuth.
Do NOT publish/edit/pay for Avito listings.
Do NOT start Internet deployment.
Do NOT require Owner CLI.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07F_R1_AVITO_BULK_PROFILE_IMPORT_AND_LATER_ENRICHMENT_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_AVITO_BULK_PROFILE_IMPORT_AND_LATER_ENRICHMENT_PROMPT.md`

---

# 1. FIRST — AUDIT CURRENT EXTENSION CAPABILITIES

Before implementation inspect current Chrome Extension and existing import routes.

Explicitly determine:

```text
EXTENSION_VERSION_BEFORE:
CURRENT_SINGLE_LISTING_IMPORT:
CURRENT_PROFILE/LIST_IMPORT:
CURRENT_AVITO_ID_FIELD:
CURRENT_DEDUP_RULE:
CURRENT_UPSERT_RULE:
CURRENT_EXTENSION_TO_MODULE_ROUTE:
CURRENT_MODULE_TO_CORE_ROUTE:
```

Historical code may already contain older profile/list import logic. Reuse it if valid rather than starting from scratch.

Do not assume old code still works against current Avito DOM.

---

# 2. USER WORKFLOW — BULK IMPORT

Required Owner workflow:

1. Open own Avito profile/listings page where multiple ads are shown.
2. Open Technoreboot extension.
3. Extension recognizes:
   `Страница списка объявлений`
4. Show action:

`Импортировать все объявления`

Optionally also show:

`Импортировать текущую страницу`

but the primary function is ALL pages.

After click:

- extension discovers current listing cards;
- imports them;
- follows pagination / loads next result page when necessary;
- continues until last page;
- shows live progress.

Example:

```text
Найдено страниц: 4
Обработано: 37 / 82
Создано: 29
Обновлено: 8
Пропущено: 0
Ошибок: 0
```

At finish:

```text
Импорт завершён
Всего объявлений: 82
Создано: 74
Обновлено: 8
Ошибок: 0
```

No Owner terminal.

---

# 3. LIGHTWEIGHT LISTING DATA

The bulk importer is intentionally FAST.

For every listing collect only data reliably available from list/profile pages.

At minimum:

- Avito item ID;
- source URL;
- title;
- price;
- listing status if visible;
- category if reliably discoverable;
- location/address if present;
- main thumbnail/photo URL if trivially available;
- seller/profile identifier if already part of current model;
- any small reliable metadata already present in card DOM.

Do NOT open every ad merely to obtain:
- full description;
- full characteristics;
- full gallery.

That would defeat the purpose of fast bulk import.

Missing fields are allowed.

---

# 4. REQUIRED IDENTITY / DEDUPLICATION RULE

The canonical identity for an Avito-origin product is the Avito listing/item ID.

For the same Avito item:

```text
bulk import
    +
bulk import again
    +
single-listing full import later
    =
ONE Technoreboot product
```

Never duplicate by:
- title;
- price;
- URL text differences;
- page number.

Use the existing canonical Avito ID field if one already exists.

If old records lack the normalized field but contain a parseable source URL/item ID, migrate/match safely without destructive rewrites.

---

# 5. BULK UPSERT POLICY

For a listing not yet in Technoreboot:

Create a product with:
- source origin = Avito/current canonical equivalent;
- Avito item ID;
- URL;
- title;
- price;
- whatever lightweight metadata is available;
- safe initial status/location according to current product rules.

For an existing product with same Avito item ID:

Update ONLY fields that the bulk card reliably owns, for example:
- current title;
- current price;
- source URL;
- Avito status.

IMPORTANT:

Bulk import MUST NOT erase richer data already present in Technoreboot.

If existing product already has:
- description;
- characteristics;
- photos;
- brand/model;
- manually corrected category;
- barcode/SKU;
- purchase price;
- storage location;

then a lightweight bulk refresh must preserve those unless the current mapping explicitly and safely owns the field.

No downgrade of an enriched record.

---

# 6. LATER "ДОИМПОРТИРОВАТЬ ДАННЫЕ"

On an individual Avito listing page, extension must offer a clear action.

Preferred label:

`Доимпортировать данные`

If listing is not yet in Technoreboot, same action may behave as normal full import and create it.

If listing already exists:
- resolve product by Avito item ID;
- run current detailed single-listing extraction;
- UPDATE existing product.

Enrichment should attempt currently supported data:

- title;
- price;
- description;
- category;
- brand;
- model;
- condition;
- characteristics;
- address/location;
- current accepted photo import behavior;
- other current supported single-listing fields.

Again: do not require all photos in this stage.

---

# 7. NO DATA LOSS DURING ENRICHMENT

Detailed re-import should merge intelligently.

Rules:

- newly extracted non-empty values may update Avito-owned fields;
- missing extraction values must NOT blank an existing field;
- manually owned Technoreboot fields must be preserved unless current established architecture already allows Avito to update them;
- existing product SKU/barcode/purchase price/storage must remain;
- local manually uploaded photos must remain;
- imported Avito photo may be added/updated using current photo rules without deleting local photos.

---

# 8. MULTI-PAGE SUPPORT

Must support profiles with more than one page.

Inspect current Avito pagination behavior.

Implementation may use:

- explicit page links;
- `page=N`;
- pagination controls;
- browser-assisted navigation;
- current content-script architecture.

Do not assume only two pages.

Required stop conditions:

- last page reached;
- no new unique item IDs found;
- navigation fails repeatedly.

Add loop protection:

```text
MAX_PAGES
visited URLs/pages
seen Avito IDs
```

Do not infinite-loop.

Use a reasonable delay between pages if required for DOM stability.

No aggressive request storm.

---

# 9. PROGRESS + CANCEL

Extension popup/status UI should show:

- current page;
- total pages if known;
- found ads;
- processed;
- created;
- updated;
- skipped;
- errors.

Preferred:
`Остановить импорт`

If implementing cancel is low complexity, include it.

If not, at minimum:
- import state must not duplicate already processed items after reopening popup/retrying;
- repeated bulk import must be idempotent.

---

# 10. ERROR HANDLING

One broken card/listing must not stop the full batch.

For each failure keep:

- Avito ID if known;
- title if known;
- URL;
- error message.

Summary should show:

`Ошибок: N`

and allow viewing failed items.

Do not display raw stack traces.

If page navigation fails:
- retry a small finite number of times;
- then stop safely and report which page failed.

---

# 11. EXTENSION UX

Keep extension simple.

On a profile/list page:

```text
Техноребут — Avito
Страница списка объявлений

[ Импортировать все объявления ]
[ Импортировать текущую страницу ]   (optional)

Обработано: ...
```

On an individual listing:

```text
Техноребут — Avito
Объявление: 123456789

[ Импортировать / Доимпортировать данные ]
```

If extension can query Technoreboot and determine the item already exists, preferred labels:

- not exists: `Импортировать товар`
- exists: `Доимпортировать данные`

But do not block on this UX distinction if it materially complicates the stage; one idempotent `Импортировать / обновить` action is acceptable.

---

# 12. SERVER-SIDE BULK ENDPOINT

Do not send one fragile giant unvalidated blob directly to DB.

Reuse existing Avito module/Core boundaries.

Preferred architecture:

```text
Chrome Extension
    ↓
avito-module bulk/list import endpoint
    ↓
normalize each listing
    ↓
Core HTTP/API upsert
```

Core remains owner of product DB.

No extension direct DB access.

Batch endpoint may accept an array such as:

```json
{
  "items": [
    {
      "avito_id": "...",
      "url": "...",
      "title": "...",
      "price": 12345
    }
  ]
}
```

Use actual canonical names from current architecture.

Return per-item results:

```json
{
  "total": 50,
  "created": 40,
  "updated": 9,
  "skipped": 0,
  "errors": 1,
  "results": [...]
}
```

Every submitted item must be accounted for.

---

# 13. IDEMPOTENCY TEST

Mandatory:

Run the same 20-item bulk page twice.

Expected:

First run:
```text
created = 20
updated = 0
```

Second run:
```text
created = 0
updated = 20
```

Total product count must not increase on second run.

Then detailed-import one of those same 20 items.

Total count remains unchanged.

---

# 14. "FAST FILL TODAY" ACCEPTANCE SCENARIO

Create a realistic test fixture representing at least 3 Avito pages and 50+ listing cards.

Required automated verification:

```text
Page 1 -> 20
Page 2 -> 20
Page 3 -> 15
Total unique -> 55
```

Import all:

```text
created = 55
```

Repeat:

```text
updated = 55
created = 0
```

Then enrich item #17:
- same Technoreboot product ID;
- description becomes populated;
- characteristics become populated;
- current accepted photo behavior works;
- product count remains 55.

This scenario is critical.

---

# 15. REAL AVITO BROWSER SMOKE

Use current real browser-assisted extension test where safely possible.

Owner will perform final real manual check, but Antigravity should inspect current DOM/selectors and validate against a real or captured current Avito profile/list page.

Do not claim PASS solely from synthetic HTML if current real DOM selectors were not inspected.

Final report:

```text
REAL_AVITO_PROFILE_DOM_INSPECTED:
CURRENT_PAGE_SELECTOR:
PAGINATION_SELECTOR:
LISTING_CARD_SELECTOR:
AVITO_ID_EXTRACTION:
```

---

# 16. REQUIRED TESTS

## TEST A
Single profile page with 10 listings -> all 10 accounted.

## TEST B
Three pages / 55 unique listings -> all imported.

## TEST C
Second bulk run creates zero duplicates.

## TEST D
Same Avito ID with changed price -> existing product updated.

## TEST E
Bulk refresh does not delete existing description.

## TEST F
Bulk refresh does not delete existing characteristics.

## TEST G
Bulk refresh does not delete existing/local photos.

## TEST H
Detailed later import updates same product.

## TEST I
Detailed later import fills missing description.

## TEST J
Detailed later import fills supported characteristics.

## TEST K
Detailed later import keeps manual fields.

## TEST L
Current accepted photo behavior remains working.

## TEST M
One malformed listing does not abort batch.

## TEST N
Pagination loop protection works.

## TEST O
All result counters account for every listing.

## TEST P
Extension pairing still works.

## TEST Q
Existing normal single-listing import still works.

## TEST R
JSON import/export remains working.

## TEST S
Product editor remains working.

## TEST T
Core full suite passes.

## TEST U
Avito module full suite passes.

## TEST V
Admin Shell / Inventory relevant regressions pass.

Report exact totals.

---

# 17. OWNER MANUAL CHECK — REAL WORKFLOW

Browser only.

## Part A — bulk

1. Open Avito logged into Owner account.
2. Open own profile/listings page with all active ads.
3. Open Technoreboot extension.
4. Confirm button:
   `Импортировать все объявления`
5. Click it.
6. Watch progress through all pages.
7. At finish note:
   - total;
   - created;
   - updated;
   - errors.
8. Open Technoreboot `Товары`.
9. Confirm imported Avito listings are present.

## Part B — repeat / dedup

10. Run `Импортировать все объявления` again.
11. Confirm it updates existing items and does NOT double the catalog.

## Part C — enrichment

12. Pick one imported lightweight product that lacks description/photos/characteristics.
13. Open its original Avito listing.
14. Open extension.
15. Click `Доимпортировать данные`.
16. Return to Technoreboot product.
17. Confirm:
    - same product/card;
    - no duplicate;
    - description/characteristics supported by current extraction are filled;
    - current accepted photo import works.

No terminal.

---

# 18. EXTENSION VERSIONING

Bump extension version according to current project convention.

Final report:

```text
EXTENSION_VERSION_BEFORE:
EXTENSION_VERSION_AFTER:
```

Ensure `/avito/extension` serves/builds the new extension package using existing workflow.

---

# 19. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_AVITO_BULK_PROFILE_IMPORT_AND_LATER_ENRICHMENT_PROMPT.md`

Create/update:

`docs\stage07f_r1_avito_bulk_profile_import_and_later_enrichment.md`

`reports\stage07f_r1_avito_bulk_profile_import_and_later_enrichment_report.md`

`logs\2026-09-10.md`

Update extension docs/version/package as required.

---

# 20. GIT / SAFETY

Do not commit:
- Avito credentials;
- Owner profile private data;
- runtime DB;
- product photos;
- backup files;
- auth private keys.

Use synthetic fixtures for committed tests.

Commit source/tests/docs only.

Push `origin/main`.

Verify clean worktree.

---

# 21. FINAL REPORT CONTRACT

Return:

```text
# Stage 07F-R1 — Avito Bulk Profile Import + Later Enrichment

## Current Capability Audit
EXTENSION_VERSION_BEFORE:
CURRENT_SINGLE_LISTING_IMPORT:
CURRENT_PROFILE/LIST_IMPORT:
CURRENT_AVITO_ID_FIELD:
CURRENT_DEDUP_RULE:

## Bulk Import
EXTENSION_VERSION_AFTER:
IMPORT_ALL_BUTTON:
IMPORT_CURRENT_PAGE:
MULTI_PAGE:
PAGINATION_METHOD:
LOOP_PROTECTION:
PROGRESS_UI:
ERROR_ACCOUNTING:

## Lightweight Fields
AVITO_ID:
URL:
TITLE:
PRICE:
CATEGORY:
STATUS:
LOCATION:
MAIN_THUMBNAIL:

## Dedup / Upsert
IDENTITY_FIELD:
SECOND_RUN_NO_DUPLICATES:
RICH_EXISTING_DATA_PRESERVED:

## Later Enrichment
BUTTON:
SAME_PRODUCT_UPDATED:
DESCRIPTION_FILLED:
CHARACTERISTICS_FILLED:
PHOTOS:
MANUAL_FIELDS_PRESERVED:

## 55-Item Scenario
FIRST_RUN_CREATED:
FIRST_RUN_UPDATED:
SECOND_RUN_CREATED:
SECOND_RUN_UPDATED:
PRODUCT_COUNT_AFTER_SECOND_RUN:
ENRICHED_ITEM_SAME_PRODUCT:

## Real Avito DOM
REAL_AVITO_PROFILE_DOM_INSPECTED:
LISTING_CARD_SELECTOR:
PAGINATION_SELECTOR:
AVITO_ID_EXTRACTION:

## Regression
PAIRING:
SINGLE_IMPORT:
JSON:
PRODUCT_EDITOR:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07F_R1_AVITO_BULK_IMPORT_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If bulk import of multiple profile pages cannot run idempotently without creating duplicates, return BLOCKED.

If later detailed import creates a second product instead of enriching the same Avito item, return BLOCKED.

---

# 22. STOP

After implementation, tests, extension package/version update, docs, commit/push and report:

STOP.

Do not deploy to VDS yet.
Wait for Owner acceptance.
