# TECHNOREBOOT — Stage 07G-R1
## Avito import = confirmed stock presence, reactivation by Avito ID, no duplicate products

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07G-R1 — Avito Import Reactivation and ID Sync`

---

# 0. IMPORTANT: THIS PROMPT REPLACES THE PREVIOUS STAGE07G-R1 PROMPT

The previous prompt `TECHNOREBOOT_STAGE07G_R1_AVITO_INVENTORY_STATE_SAFETY_PROMPT.md`
used the wrong business assumption.

The correct Owner rule is:

> **A deliberate import of an active Avito listing means that this physical product exists and is available again.**

Therefore, if an Avito item with the same Avito ID already exists in Technoreboot but is archived/sold/out of stock, importing that active listing must reactivate the SAME product.

This is not a passive remote-status sync.
It is an explicit Owner restock/reactivation action through Avito import.

Do NOT execute the superseded prompt.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07G_R1_AVITO_IMPORT_REACTIVATION_AND_ID_SYNC_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07G_R1_AVITO_IMPORT_REACTIVATION_AND_ID_SYNC_PROMPT.md`

---

# 1. CORE BUSINESS RULE

## Avito import means stock presence

When Owner imports an ACTIVE Avito listing:

```text
Avito listing exists + Owner imports it
=> Technoreboot must treat the physical item as available
```

For an individual used product, canonical active state is:

```text
status = in_stock
storage_location = store
quantity >= 1
```

For a previously archived/sold/zero-stock product, import restores:

```text
status = in_stock
storage_location = store
quantity = 1
```

unless the project already has an explicit quantity greater than 1 that should be preserved.

The import action itself is the confirmation that the product has appeared/reappeared in stock.

---

# 2. AVITO ID IS THE PRIMARY CROSS-SYSTEM IDENTITY

Everything starts with the Avito listing ID.

Lookup order:

1. `product_external_listings.external_item_id == avito_id`
2. fallback: `products.sku == "AVITO-{avito_id}"`

Search across the ENTIRE DB:
- in_stock;
- draft;
- sold;
- archived;
- store;
- archive;
- quantity 0;
- quantity >0.

Do NOT filter lookup by current product status or storage location.

If found by SKU fallback but external listing link is missing:
- repair/create the external listing relation;
- do NOT create another Product.

One Avito ID must correspond to one Product.

---

# 3. REQUIRED IMPORT STATE MACHINE

## CASE A — Avito ID does not exist in Technoreboot

Active Avito import:

```text
CREATE product
status = in_stock
storage_location = store
quantity = 1
```

Import available Avito fields:
- title;
- sale price;
- description if present;
- category/brand/model if present/reliable;
- characteristics;
- Avito URL;
- current Avito external metadata;
- thumbnail/photo according to existing import rules.

No duplicate.

---

## CASE B — Avito ID already exists and product is active/in stock

Example:

```text
before:
in_stock / store / 1

Avito:
active
```

Result:

```text
same Product ID
in_stock / store / existing positive quantity
```

Update changed Avito data in-place.

If nothing changed:
- keep same product;
- keep same quantity;
- update import timestamp/external metadata as appropriate.

Do NOT increment quantity on every import.

---

## CASE C — Avito ID exists but product is archived/sold/quantity 0

Example:

```text
before:
sold / archive / 0

Avito:
active
Owner explicitly imports listing
```

Required result:

```text
same Product ID
status = in_stock
storage_location = store
quantity = 1
```

Also update any changed Avito fields.

This is REQUIRED behavior.

Do NOT create a new Product.
Do NOT preserve `sold/archive/0` after a deliberate active Avito import.

Log a product event, for example:

```text
avito_import_reactivated
```

The event should make clear that stock was restored because Owner imported an active Avito listing.

---

## CASE D — product is draft but quantity is positive

Example:

```text
draft / store / 1
+ active Avito import
```

Result:

```text
in_stock / store / 1
```

Same Product ID.

---

# 4. LOCAL SALE LIFECYCLE REMAINS

Local sale behavior remains authoritative until another explicit Avito import occurs.

## Completed local sale

For a unique product when quantity reaches zero:

```text
status = sold
storage_location = archive
quantity = 0
```

## Cancel local sale

Restore stock according to existing cancellation logic.

## Later deliberate Avito import

If the same Avito ID is imported again while active:

```text
sold/archive/0
-> in_stock/store/1
```

This is intentional.

Interpretation:

> The new Avito import is a new confirmation that the physical item is available again.

---

# 5. DO NOT USE INACTIVE AVITO STATE TO CONTROL PHYSICAL STOCK

The Owner-defined automatic rule is ONLY:

```text
ACTIVE AVITO IMPORT => PRODUCT IS AVAILABLE
```

Do NOT implement the inverse as an automatic physical-stock rule.

These remote states:

```text
closed
inactive
archived
blocked
removed
rejected
hidden
suspended
```

must NOT automatically do:

```text
status = sold
storage_location = archive
quantity = 0
```

They may update external Avito listing metadata/status only.

Reason:
- listing may be temporarily hidden;
- blocked by moderation;
- manually removed from Avito;
- product may still physically exist in the shop.

Physical stock should go to sold/archive through:
- local sale;
- explicit manual stock action;
- another explicitly defined business workflow.

Do not infer physical sale merely from listing inactivity.

---

# 6. LOCAL-ONLY PRODUCTS WITHOUT AVITO ID ARE VALID

Technoreboot must support products that are never published on Avito.

Such products:
- have an internal Product ID;
- may have normal SKU/barcode;
- may appear on the website;
- may be sold through the shop;
- may have stock/status/location;
- do NOT require `external_item_id`;
- do NOT require `AVITO-*` SKU;
- are not affected by Avito import/sync unless later explicitly linked/imported.

No new requirement may make Avito mandatory for products.

---

# 7. NO QUANTITY INFLATION

Repeated active Avito imports must never do:

```text
1 -> 2 -> 3 -> 4
```

Rules:

```text
existing quantity > 0
=> preserve quantity

existing quantity <= 0 AND deliberate active import
=> set quantity = 1
```

For normal unique used goods, a reactivation returns one available item.

---

# 8. AVITO CONTENT SYNC

For the same Avito ID, import should update fields that Avito owns or supplies reliably:

- title;
- sale price;
- Avito URL;
- description when supplied;
- category/brand/model when supplied;
- condition/characteristics when supplied;
- external listing metadata/status;
- thumbnail/photo according to existing non-destructive photo rules;
- last imported/sync timestamp.

Do NOT overwrite local-only business fields unnecessarily:

- purchase price;
- internal notes;
- storage metadata unrelated to activation;
- barcode;
- manually uploaded photos;
- richer existing gallery with a lower-quality thumbnail;
- historical sales records.

---

# 9. PHOTO RULES REMAIN NON-DESTRUCTIVE

Keep current Stage07F behavior:

- bulk Avito import may add one thumbnail when product has zero photos;
- existing manual/full-quality photos are preserved;
- repeat import creates no duplicate photos;
- detailed enrichment may add richer data;
- no gallery deletion because bulk payload contains only a thumbnail.

---

# 10. REMOVE UNSAFE OLD BIDIRECTIONAL RULES

Audit current code introduced in the previous architecture stages.

Remove or modify rules that automatically do:

```text
remote inactive/closed/blocked/removed/archived
=> sold/archive/0
```

That is NOT the required business logic.

Keep/implement:

```text
deliberate active Avito import
=> reactivate SAME product by Avito ID
```

---

# 11. REQUIRED TRANSITION TABLE

Implement and document this exact behavior:

| Existing Technoreboot state | Incoming Avito import | Result |
|---|---|---|
| no product | active | create `in_stock/store/1` |
| `in_stock/store/1` | active | update same product, keep stock |
| `draft/store/1` | active | same product -> `in_stock/store/1` |
| `sold/archive/0` | active | same product -> `in_stock/store/1` |
| `archive/0` any archived state | active | same product -> `in_stock/store/1` |
| any product | closed/inactive/blocked/removed/archived | update external metadata only; physical stock unchanged |
| local-only product, no Avito ID | no Avito import | unaffected |

---

# 12. REQUIRED TESTS

## TEST A — create new Avito product
Active Avito ID absent:
- one Product created;
- `in_stock/store/1`;
- external relation created.

## TEST B — repeat active import
Existing `in_stock/store/1`:
- same Product ID;
- created = 0;
- updated = 1;
- quantity still 1.

## TEST C — archived product reactivation
Existing `sold/archive/0` with same Avito ID:
- import active listing;
- same Product ID;
- `in_stock/store/1`;
- event `avito_import_reactivated`;
- zero duplicate.

## TEST D — draft positive stock
`draft/store/1 + active -> in_stock/store/1`.

## TEST E — quantity inflation protection
Run same active import 5 times:
- quantity remains 1.

## TEST F — content update
Change Avito price/title:
- same Product ID;
- fields update;
- quantity unchanged.

## TEST G — inactive listing does NOT zero stock
`in_stock/store/1 + blocked`:
- physical state unchanged.

## TEST H
`in_stock/store/1 + removed`:
- physical state unchanged.

## TEST I
`in_stock/store/1 + archived`:
- physical state unchanged.

## TEST J
`in_stock/store/1 + closed`:
- physical state unchanged.

## TEST K — local sale
- local completed sale -> sold/archive/0.

## TEST L — local sale then deliberate re-import
- sold/archive/0;
- active same Avito ID imported;
- same Product -> in_stock/store/1.

## TEST M — sale history preserved
Reactivation must not delete/change historical Sale/SaleItem.

## TEST N — cancellation
Existing cancellation workflow still restores stock correctly.

## TEST O — external ID primary lookup
Find same product across all statuses.

## TEST P — SKU fallback
Missing external relation repaired without duplicate.

## TEST Q — local-only product
Create normal internal product without Avito ID:
- valid;
- appears in product workflows;
- unaffected by Avito sync.

## TEST R — photos
Existing photo/gallery preserved.

## TEST S — bulk current page
No duplicate products and stock semantics correct.

## TEST T — all-pages import
Same identity/state rules across all pages.

## TEST U — JSON/product editor regressions
Still pass.

## TEST V — reports/sales regressions
Historical sales and revenue unchanged.

Run full relevant suites and report exact totals.

---

# 13. EXISTING DB AUDIT

Audit products affected by the previously implemented bidirectional state logic.

Look for product events such as:
- `avito_reactivated`;
- `avito_archived`;
- other Avito-driven stock transitions.

Classify suspicious products.

Do NOT broadly mutate the DB.

Safe automatic repair is allowed only when current business state can be proven from:
- Avito ID;
- current active import data;
- local sale history;
- explicit product events.

Ambiguous rows:
- leave unchanged;
- list in report.

No real products may be deleted.

---

# 14. OWNER MANUAL CHECK

Browser-only.

1. Pick one Avito-linked product currently in stock.
2. Confirm its Avito ID in product detail.
3. Import same active listing again.
4. Confirm:
   - same product;
   - no duplicate;
   - quantity not incremented.
5. Pick/test one Avito-linked product in archive with quantity 0.
6. Import that same active Avito listing.
7. Confirm:
   - SAME product returns from archive;
   - status = В наличии;
   - location = Магазин;
   - quantity = 1.
8. Repeat import once more.
9. Confirm quantity remains 1.
10. Verify a normal local product without Avito ID still works and is unaffected.

No terminal.

---

# 15. DOCUMENTATION

Create/update:

`docs\stage07g_r1_avito_import_reactivation_and_id_sync.md`

`reports\stage07g_r1_avito_import_reactivation_and_id_sync_report.md`

`logs\2026-09-11.md`

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07G_R1_AVITO_IMPORT_REACTIVATION_AND_ID_SYNC_PROMPT.md`

---

# 16. GIT / SAFETY

Do not commit:
- runtime DB;
- backups;
- real Avito/customer data;
- photos;
- auth secrets;
- cookies/session.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

---

# 17. FINAL REPORT CONTRACT

Return:

```text
# Stage 07G-R1 — Avito Import Reactivation and ID Sync

## Business Rule
ACTIVE_AVITO_IMPORT_MEANS:
LOCAL_ONLY_PRODUCTS:
PHYSICAL_STOCK_INACTIVE_REMOTE_RULE:

## Identity
PRIMARY_LOOKUP:
FALLBACK_LOOKUP:
STATUS_FILTERS:
DUPLICATE_POLICY:

## Transition Matrix
NEW_ACTIVE:
EXISTING_ACTIVE:
DRAFT_ACTIVE:
ARCHIVED_ACTIVE:
SOLD_ACTIVE:
REMOTE_CLOSED:
REMOTE_BLOCKED:
REMOTE_REMOVED:
REMOTE_ARCHIVED:

## Quantity
ZERO_TO_ONE_ON_REACTIVATION:
NO_REPEAT_INCREMENT:

## Content Sync
FIELDS_UPDATED:
LOCAL_FIELDS_PRESERVED:
PHOTOS_PRESERVED:

## Sale Lifecycle
LOCAL_SALE:
LOCAL_CANCEL:
SALE_THEN_REIMPORT:
SALE_HISTORY_PRESERVED:

## Existing DB Audit
AVITO_STATE_EVENTS_AUDITED:
SUSPICIOUS_PRODUCTS:
AUTO_REPAIRED:
AMBIGUOUS_LEFT_UNCHANGED:
REAL_PRODUCTS_DELETED: 0

## Regression
BULK_CURRENT_PAGE:
BULK_ALL_PAGES:
JSON:
PRODUCT_EDITOR:
REPORTS:
LOCAL_ONLY_PRODUCT:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07G_R1_AVITO_IMPORT_REACTIVATION_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If an active Avito import creates a duplicate instead of reactivating the existing same-ID product, return BLOCKED.

If repeated imports increment quantity above 1 for the same unique item, return BLOCKED.

If blocked/removed/archived/closed automatically zero physical stock, return BLOCKED.

---

# 18. STOP

After implementation, tests, DB audit, docs, commit/push and report:

STOP.

Do not deploy to VDS.
Wait for Owner acceptance.
