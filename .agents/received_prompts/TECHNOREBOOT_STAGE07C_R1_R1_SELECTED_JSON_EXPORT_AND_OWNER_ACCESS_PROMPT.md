# TECHNOREBOOT — Stage 07C-R1-R1
## Selected Product JSON Export + Owner Access Verification

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07C-R1-R1 — Selected JSON Export and Access Verification`

---

# 0. EXECUTION CONTRACT

Stage 07C-R1 is NOT fully accepted yet.

The implementation is generally correct, but one Owner requirement from the original prompt is not fully satisfied in the web UI:

Current UI report says:

`[ Экспортировать все товары в JSON ]`

The original requirement was:

- export one product;
- export multiple selected products;
- optionally export filtered/all products.

Therefore this corrective stage is narrow:

1. Keep the existing canonical JSON contract and import logic.
2. Add a simple web workflow for exporting ONE or MULTIPLE SELECTED products.
3. Keep "Export all" only as an additional convenience.
4. Verify access control for `/products/json` and its import/export APIs using the existing mTLS authorization model.
5. Do not redesign anything else.

Do NOT start Internet deployment.
Do NOT return to Avito multi-photo work.
Do NOT change canonical format version unless absolutely necessary.
Do NOT change duplicate policy.
Do NOT add CLI workflow.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07C_R1_R1_SELECTED_JSON_EXPORT_AND_OWNER_ACCESS_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07C_R1_R1_SELECTED_JSON_EXPORT_AND_OWNER_ACCESS_PROMPT.md`

Treat the copied prompt as authoritative.

---

# 1. ACCEPTED BASELINE TO PRESERVE

Keep current Stage07C-R1 behavior:

- canonical format:
  `technoreboot-products`
- version:
  `1`
- one or many products per file;
- AI prompt generator;
- JSON upload/import;
- per-product import result summary;
- category-specific `characteristics`;
- photos optional;
- existing duplicate/update policy;
- round-trip support;
- Core owns product business logic;
- Admin Shell is UI/proxy;
- current tests.

Do not create a second format.

---

# 2. REQUIRED WEB EXPORT UX

On `/products/json`, add a simple product selection area.

Preferred UX:

```text
Экспорт JSON

[ Поиск / фильтр товаров ]

☐  Lenovo ThinkPad T480 — PRD-...
☐  HP LaserJet M404dn — PRD-...
☐  Dell OptiPlex 7050 — PRD-...

[ Выбрать все показанные ]
[ Снять выбор ]

Выбрано: 3

[ Экспортировать выбранные в JSON ]

[ Экспортировать все товары в JSON ]
```

Keep it simple.

No complex data grid required.

At minimum:

- user can select exactly ONE product;
- user can select TWO OR MORE products;
- selected count is visible;
- clicking export downloads JSON containing only selected items;
- "Export all" may remain.

If the current product list already has reusable filters/search controls, reuse them instead of building a second complex selector.

---

# 3. BACKEND CONTRACT

Use the SAME canonical exporter already implemented.

Do NOT duplicate serialization logic.

Preferred API behavior:

```text
GET/POST /api/products/json/export?ids=1,2,3
```

or:

```json
{
  "ids": [1, 2, 3]
}
```

Use current project conventions.

Requirements:

- no IDs / explicit all-mode -> export all;
- one ID -> one product;
- many IDs -> only those products;
- unknown IDs -> clear safe validation behavior;
- output remains:
  `technoreboot-products`, version 1.

The order in exported JSON should be deterministic.

Prefer the selection order if practical; otherwise stable product ID order is acceptable and must be documented.

---

# 4. ROUND-TRIP FOR SELECTED EXPORT

Mandatory tests:

## Case A — one product
1. Select one product.
2. Export.
3. JSON contains exactly 1 product.
4. Validate with importer/schema.

## Case B — multiple products
1. Select 3 products.
2. Export.
3. JSON contains exactly those 3 products.
4. No unselected products included.
5. Validate with importer/schema.

## Case C — re-import
Re-import selected export in isolated/disposable context or by controlled update semantics.

Verify:
- title;
- price;
- description;
- category;
- brand;
- model;
- condition;
- characteristics.

---

# 5. OWNER ACCESS VERIFICATION

The report calls `/products/json` a Owner web page, but this corrective stage must explicitly verify the real gateway authorization path.

Required through `https://127.0.0.1:8443`:

## OWNER
- `/products/json` -> 200
- AI prompt endpoint -> allowed
- import endpoint -> allowed
- selected export endpoint -> allowed

## USER
Follow the current intended product-management access policy.

If this page is intended OWNER-only:
- USER -> 403 for page/import/export/prompt.

If ordinary authenticated USER is intentionally allowed to manage products elsewhere:
- follow the SAME established authorization level as existing product-management routes;
- document it explicitly;
- do not accidentally make JSON import/export more permissive than normal product editing.

## No client certificate
- denied by gateway.

Do not use test bypass headers as the final end-to-end proof.

---

# 6. UI RESULT / ERRORS

Selected export:

- if nothing selected:
  show:
  `Выберите хотя бы один товар для экспорта.`
- if export fails:
  show safe Russian error;
- no stack trace;
- no raw internal JSON exception.

Filename remains:

`TECHNOREBOOT_PRODUCTS_YYYY-MM-DD_HHMMSS.json`

Optional filename suffix such as `_3_ITEMS` is acceptable but not required.

---

# 7. AI / IMPORT REGRESSION

Do not change AI prompt semantics unless needed for a bug.

Smoke verify:

- prompt copies;
- valid two-product AI-style JSON imports;
- photos remain optional;
- category-specific characteristics remain intact.

---

# 8. REQUIRED TESTS

## TEST A
One selected product export -> exactly 1 item.

## TEST B
Three selected products export -> exactly 3 selected items.

## TEST C
Unselected product is absent.

## TEST D
Export all still works.

## TEST E
Selected export uses same canonical format/version.

## TEST F
Selected export validates against importer.

## TEST G
Selected export round-trip preserves common fields.

## TEST H
Selected export round-trip preserves category characteristics.

## TEST I
No selection gives controlled UI error.

## TEST J
Unknown product ID handled safely.

## TEST K
OWNER/access policy through real gateway verified.

## TEST L
No-cert denied.

## TEST M
AI prompt/import regression smoke passes.

## TEST N
Core tests pass.

## TEST O
Admin Shell tests pass.

## TEST P
Avito pairing/import smoke remains unchanged.

Report exact totals.

---

# 9. OWNER MANUAL CHECK

Browser-only:

1. Open:
   `https://127.0.0.1:8443/products/json`
2. In export section select ONE product.
3. Click:
   `Экспортировать выбранные в JSON`
4. Open downloaded JSON and confirm it contains exactly one product.
5. Return to page and select 2–3 products.
6. Export again.
7. Confirm JSON contains exactly those selected products.
8. Confirm `Экспортировать все товары в JSON` still works.
9. Optionally re-import the selected export and confirm the documented update/duplicate behavior.

No terminal commands.

---

# 10. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07C_R1_R1_SELECTED_JSON_EXPORT_AND_OWNER_ACCESS_PROMPT.md`

Create/update:

`docs\stage07c_r1_r1_selected_json_export_and_owner_access.md`

`reports\stage07c_r1_r1_selected_json_export_and_owner_access_report.md`

`logs\2026-09-08.md`

---

# 11. GIT / SAFETY

Before commit:

- no runtime DB;
- no real exported owner product JSON;
- no auth secrets;
- no backup ZIP;
- no tokens.

Commit/push safe source/tests/docs only.

Push `origin/main`.

Verify clean tracked worktree.

---

# 12. FINAL REPORT CONTRACT

Return:

```text
# Stage 07C-R1-R1 — Selected JSON Export and Owner Access

## Existing Canonical Contract
FORMAT:
VERSION:
CONTRACT_CHANGED: false

## Export UI
ONE_PRODUCT_SELECTABLE:
MULTIPLE_PRODUCTS_SELECTABLE:
SELECTED_COUNT_VISIBLE:
EXPORT_SELECTED_BUTTON:
EXPORT_ALL_RETAINED:

## Export API
ONE_ID:
MULTIPLE_IDS:
UNKNOWN_ID_POLICY:
USES_CANONICAL_EXPORTER:

## Round Trip
ONE_PRODUCT:
MULTIPLE_PRODUCTS:
UNSELECTED_EXCLUDED:
COMMON_FIELDS_PRESERVED:
CATEGORY_FIELDS_PRESERVED:

## Access
OWNER_PAGE:
OWNER_IMPORT:
OWNER_EXPORT:
USER_POLICY:
NO_CERT:

## Regression
AI_PROMPT:
JSON_IMPORT:
AVITO:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07C_R1_R1_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If UI still only supports "export all" and not one/multiple selected products, return BLOCKED.

---

# 13. STOP

After implementation, tests, docs, commit/push and report:

STOP.

Do not start Internet deployment.
Wait for Owner acceptance.
