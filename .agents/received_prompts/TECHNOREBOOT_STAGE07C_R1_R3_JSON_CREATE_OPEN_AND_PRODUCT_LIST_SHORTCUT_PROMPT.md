# TECHNOREBOOT — Stage 07C-R1-R3
## JSON create UX: open created product + shortcut from product list

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07C-R1-R3 — JSON Create/Open UX`

---

# 0. EXECUTION CONTRACT

Stage 07C JSON import/export is working and this stage adds two small Owner-facing UX improvements.

Scope is intentionally narrow.

Do NOT redesign JSON import/export.
Do NOT change canonical JSON contract.
Do NOT change duplicate/update policy.
Do NOT implement the full product editor yet.
Do NOT return to Avito multi-photo extraction.
Do NOT start Internet deployment.
No Owner CLI workflow.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07C_R1_R3_JSON_CREATE_OPEN_AND_PRODUCT_LIST_SHORTCUT_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07C_R1_R3_JSON_CREATE_OPEN_AND_PRODUCT_LIST_SHORTCUT_PROMPT.md`

Treat the copied prompt as authoritative.

---

# 1. REQUIREMENT A — OPEN NEWLY CREATED PRODUCT IMMEDIATELY

Current JSON import page shows import results after creating products.

Owner wants to be able to open the newly created product immediately WITHOUT leaving the JSON import page.

Required behavior:

After successful import of a product, each result row with status `created` must contain a clear action:

`Открыть товар`

Behavior:

- click opens the corresponding product detail page;
- MUST open in a NEW browser tab/window (`target="_blank"` or equivalent safe JS);
- current `/products/json` page remains open and keeps its import result state;
- use the actual created `product_id` returned by Core;
- do not guess IDs;
- if multiple products are created, each result row gets its own correct `Открыть товар` action.

If a row is updated, an `Открыть товар` action is also acceptable and preferred when a valid product_id exists.

Skipped/error rows must not get a misleading open button unless a valid existing product ID is explicitly known.

The product URL must reuse the current accepted product detail route.

Do NOT open the editor because full editor is not implemented yet.
Open the normal product card/detail page.

---

# 2. REQUIREMENT B — JSON CREATE SHORTCUT IN MAIN PRODUCT LIST

Owner opens the main product list via the normal `Товары` menu.

At the top of that product list there are already quick controls/tabs/buttons such as:

- Магазин
- Мастерская
- Архив
- Черновики

Add a clearly visible button near these controls:

`+ Добавить новый товар через JSON`

Behavior:

- clicking navigates to `/products/json`;
- no new authentication mechanism;
- same access policy as product management;
- visually consistent with existing top controls;
- visible without scrolling;
- does not replace existing buttons/tabs.

This is an entry point only.
Do not duplicate JSON import UI inside the product list.

---

# 3. IMPORT RESULT CONTRACT

Verify the actual current result object before coding.

The frontend must use the real product ID returned by Core/Admin Shell.

Expected structure is similar to:

{
  "results": [
    {
      "status": "created",
      "product_id": 154,
      "sku": "PRD-...",
      "title": "..."
    }
  ]
}

Use actual current field names if different.

Do not derive the ID from displayed text.

---

# 4. UI DETAILS

## JSON import page

For created/updated result rows:

- text: `Открыть товар`;
- opens in new tab;
- visible only when valid product_id exists;
- no broken href;
- current import page remains open.

Prefer a semantic link with `target="_blank"` and `rel="noopener"`.

Use the actual current product detail URL pattern.

## Main product list

Add:

`+ Добавить новый товар через JSON`

near the existing top quick controls.

Do not hide it in a secondary menu.

---

# 5. ACCESS CONTROL

Follow current product-management access policy.

Verify:

- OWNER can see/use both entry points;
- USER follows same current product-management policy;
- no client certificate remains blocked by gateway.

Do not make `/products/json` more permissive than current product pages.

---

# 6. REQUIRED TESTS

A. After one-product JSON create, result row contains correct product_id.
B. Created row renders `Открыть товар`.
C. Open link points to actual created product detail route.
D. Link opens in new tab/window.
E. Current JSON import page remains available.
F. Batch create of 2 products: each row gets its own correct link.
G. Error/skipped rows do not get misleading open links.
H. Main product list contains visible `Добавить новый товар через JSON`.
I. Shortcut navigates to `/products/json`.
J. Existing top controls Магазин / Мастерская / Архив / Черновики remain present and functional.
K. JSON import regression still works.
L. Selected/full JSON export regressions still work.
M. Relevant Admin Shell tests pass.
N. Relevant Core tests pass if Core touched.
O. OWNER/gateway access remains valid.

Report exact totals.

---

# 7. OWNER MANUAL CHECK

Browser-only:

1. Open main `Товары` list.
2. Confirm top button `+ Добавить новый товар через JSON` is visible near existing quick controls.
3. Click it and confirm `/products/json` opens.
4. Import one new disposable test product.
5. In the result row click `Открыть товар`.
6. Confirm the product opens in a NEW tab.
7. Confirm the JSON import page remains open in the original tab.
8. Confirm the opened product is exactly the one just created.
9. Repeat once with two products and confirm both result rows open the correct cards.

No CLI.

---

# 8. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07C_R1_R3_JSON_CREATE_OPEN_AND_PRODUCT_LIST_SHORTCUT_PROMPT.md`

Create/update:

`docs\stage07c_r1_r3_json_create_open_and_product_list_shortcut.md`

`reports\stage07c_r1_r3_json_create_open_and_product_list_shortcut_report.md`

`logs\2026-09-10.md`

---

# 9. GIT / SAFETY

Do not commit runtime DB, real imported Owner products, exported JSON, secrets/tokens, or backup archives.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

---

# 10. FINAL REPORT CONTRACT

Return:

# Stage 07C-R1-R3 — JSON Create/Open UX

## Requirement A
CREATED_ROW_OPEN_BUTTON:
USES_REAL_PRODUCT_ID:
OPENS_NEW_TAB:
BATCH_ROWS_LINK_CORRECTLY:
ERROR_ROWS_SAFE:

## Requirement B
PRODUCT_LIST_SHORTCUT_VISIBLE:
SHORTCUT_LABEL:
SHORTCUT_TARGET:
EXISTING_TOP_CONTROLS_PRESERVED:

## Regression
JSON_IMPORT:
SELECTED_EXPORT:
FULL_EXPORT:
PRODUCT_DETAIL:
OWNER_ACCESS:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07C_R1_R3_JSON_CREATE_OPEN_UX_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true

If the newly created product cannot be opened directly from the import result without leaving the JSON page, return BLOCKED.

If the main product list does not visibly expose the JSON creation shortcut at the top, return BLOCKED.

---

# 11. STOP

After implementation, tests, docs, commit/push and report:

STOP.

Do not implement the full product editor yet.
Do not start Internet deployment.
Wait for Owner acceptance.
