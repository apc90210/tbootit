# TECHNOREBOOT — Stage 07F-R1-R1
## Fix real Avito profile detection: 0 listings / 1 page false success

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07F-R1-R1 — Real Avito Profile Zero Listings Fix`

# 0. EXECUTION CONTRACT

Stage 07F-R1 is NOT accepted.

Owner tested Chrome Extension v0.2.48 on the REAL Avito listings page.

Actual result:

```text
Найдено объявлений на странице: 0
Страница: 1 из 1

Обработка страницы 1...

Найдено страниц: 1
Обработано: 0 / 0
Создано: 0
Обновлено: 0
Пропущено: 0
Ошибок: 0

✓ Импорт успешно завершен!
Страниц обработано: 1, объявлений: 0
Создано новых: 0, обновлено: 0, ошибок: 0
```

This is a real browser failure.

The extension recognizes the page as a listings page, but current DOM extraction finds ZERO cards and incorrectly assumes 1/1 page.

Do NOT rely only on synthetic fixtures.
Do NOT claim success until current REAL Avito DOM or a fresh sanitized DOM capture is inspected.
Do NOT redesign architecture.
Do NOT use official Avito API.
Do NOT start VDS deployment.
Do NOT reopen full-gallery photo extraction.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07F_R1_R1_AVITO_REAL_PROFILE_ZERO_LISTINGS_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R1_AVITO_REAL_PROFILE_ZERO_LISTINGS_FIX_PROMPT.md`

# 1. REPRODUCE EXACT OWNER FAILURE

Reproduce:

```text
list page detected
listing_count = 0
page = 1
total_pages = 1
```

Capture:

```text
REAL_PAGE_URL_PATTERN:
REAL_PAGE_TYPE_DETECTED:
CONTENT_SCRIPT_FUNCTION:
CURRENT_CARD_SELECTORS:
CURRENT_PAGINATION_SELECTORS:
DOM_READY_STATE:
FOUND_CARD_NODES:
FOUND_LINK_NODES:
FOUND_AVITO_IDS:
```

Investigate and PROVE the cause. Possible causes to inspect:
- changed `data-marker`;
- own-listings DOM differs from public seller profile/search;
- selectors match only public catalog cards;
- async/lazy React rendering;
- different card root element;
- ID only available in href;
- pagination changed to another control/infinite scroll;
- script executes too early.

# 2. REAL DOM INSPECTION IS MANDATORY

Inspect CURRENT Avito DOM for the actual page type used by Owner.

Find robust selectors/signals for:
- listing card root;
- listing URL;
- Avito ID;
- title;
- price;
- pagination or lazy/infinite load.

Prefer stable attributes:
- `data-marker`;
- `itemprop`;
- semantic wrappers;
- stable listing href patterns.

Avoid minified/random CSS class names as primary selectors.

Avito ID:
1. explicit stable attribute if available;
2. fallback: parse from canonical listing URL.

Deduplicate by Avito ID.

# 3. SUPPORT BOTH PAGE TYPES

Must support at least:
1. Owner's own listings/profile-management page — PRIMARY.
2. Public seller/profile listings page where feasible.

If DOMs differ, implement separate extraction strategies.

Report:

```text
OWN_LISTINGS_PAGE_SUPPORTED:
PUBLIC_SELLER_PAGE_SUPPORTED:
STRATEGY_PER_PAGE_TYPE:
```

# 4. ASYNC / DYNAMIC RENDERING

Do not return zero immediately while page is still rendering.

Implement bounded wait:
- MutationObserver or polling;
- e.g. 8–12 sec max;
- stop early when cards appear.

If timeout expires and zero cards are found:
- show warning/error;
- DO NOT show green success.

# 5. ZERO-RESULT MUST NOT BE GREEN SUCCESS

For a recognized listings page:

```text
detected_list_page = true
AND extracted_count = 0
```

must NOT produce:

`✓ Импорт успешно завершен!`

Show something like:

```text
Объявления не найдены.
Проверьте, что список объявлений загрузился полностью.
```

# 6. LAYERED EXTRACTION FALLBACKS

Use layered extraction:

Card:
1. stable current Avito marker;
2. stable listing href scan inside content area;
3. deduplicate anchors by Avito ID.

Title:
1. stable title node;
2. anchor text;
3. accessible label.

Price:
1. stable price marker;
2. itemprop/meta;
3. safe text parser.

Missing price must not drop the whole listing.

# 7. PAGINATION / MULTI-PAGE

Fix current-page extraction first, then verify actual multi-page traversal.

Do not hardcode 1/1.

Support the actual current mechanism:
- numbered pages / next link;
or
- infinite/lazy scroll.

Required protections:
- `MAX_PAGES`;
- visited URLs/pages;
- seen Avito IDs;
- stop if repeated cycles produce no new IDs.

Report ACTUAL mechanism.

# 8. FAST IMPORT GOAL

On Owner's real page after fix:
- displayed count must be non-zero and correspond to visible listings;
- current-page import must process those items;
- all-pages import must reach all available pages/items;
- each listing accounted for.

Bulk import remains lightweight. Do not open each listing for full description/characteristics.

# 9. REQUIRED TESTS

A. Fresh real/sanitized Owner DOM -> count > 0.  
B. One visible card -> one unique Avito ID.  
C. Duplicate anchors -> one listing only.  
D. Title extraction.  
E. Price extraction.  
F. Missing price does not drop listing.  
G. Async-rendered cards detected.  
H. Recognized list + zero cards -> warning, not green success.  
I. Current-page import sends all extracted items.  
J. Repeat import creates no duplicates.  
K. Real pagination/scroll works.  
L. Existing 3-page synthetic regression still passes.  
M. Detailed enrichment updates same product.  
N. Pairing regression passes.  
O. Single-listing import passes.  
P. JSON regression passes.  
Q. Product editor regression passes.  
R. Avito module full suite passes.  
S. Core relevant/full suite passes.  
T. Admin Shell relevant suite passes.

# 10. EXTENSION VERSION

Bump:
`0.2.48` -> `0.2.49`

Update:
- manifest;
- built ZIP;
- `/avito/extension`;
- version tests.

# 11. OWNER MANUAL CHECK

Browser-only:

1. Download/update extension v0.2.49 from `/avito/extension`.
2. Open the SAME Avito listings page where v0.2.48 showed zero.
3. Open extension.
4. Expected:
   - `Найдено объявлений на странице: N`, `N > 0`;
   - real page count or actual loaded-batch mechanism.
5. Click `Импортировать текущую страницу`.
6. Confirm processed > 0 and counters account for all items.
7. Click `Импортировать все объявления`.
8. Verify all pages/items are traversed.
9. Open Technoreboot `Товары` and confirm items from later pages exist.
10. Run bulk import again and confirm no duplicate growth.

No CLI.

# 12. DIAGNOSTIC REPORT CONTRACT

Final report must include:

```text
REAL_PAGE_URL_PATTERN:
REAL_PAGE_TYPE:
OLD_SELECTOR:
OLD_SELECTOR_MATCH_COUNT:
NEW_PRIMARY_SELECTOR:
NEW_PRIMARY_MATCH_COUNT:
FALLBACK_STRATEGY:
AVITO_ID_SOURCE:
PAGINATION_OR_SCROLL_MECHANISM:
ASYNC_WAIT_METHOD:
ZERO_RESULT_UI_POLICY:
```

# 13. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R1_AVITO_REAL_PROFILE_ZERO_LISTINGS_FIX_PROMPT.md`

Create/update:

`docs\stage07f_r1_r1_avito_real_profile_zero_listings_fix.md`

`reports\stage07f_r1_r1_avito_real_profile_zero_listings_fix_report.md`

`logs\2026-09-10.md`

# 14. GIT / SAFETY

Do not commit:
- Owner cookies/session data;
- private unsanitized profile HTML;
- runtime DB;
- auth secrets;
- photos.

If committing DOM fixture, sanitize personal/private data and keep only structural markup needed for selectors.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

# 15. FINAL REPORT CONTRACT

Return:

```text
# Stage 07F-R1-R1 — Real Avito Profile Zero Listings Fix

## Reproduction
REAL_PAGE_URL_PATTERN:
REAL_PAGE_TYPE:
OLD_SELECTOR:
OLD_SELECTOR_MATCH_COUNT:
PROVEN_ROOT_CAUSE:

## DOM Fix
NEW_PRIMARY_SELECTOR:
NEW_PRIMARY_MATCH_COUNT:
FALLBACK_STRATEGY:
AVITO_ID_SOURCE:
TITLE_SOURCE:
PRICE_SOURCE:
ASYNC_WAIT_METHOD:

## Pagination
MECHANISM:
CURRENT_PAGE:
TOTAL_PAGES_OR_SCROLL_BATCHES:
MULTI_PAGE_VERIFIED:
LOOP_PROTECTION:

## UI
ZERO_RESULT_GREEN_SUCCESS_REMOVED:
ZERO_RESULT_MESSAGE:
EXTENSION_VERSION_AFTER:

## Bulk
CURRENT_PAGE_COUNT:
CURRENT_PAGE_IMPORT:
ALL_IMPORT:
SECOND_RUN_NO_DUPLICATES:

## Regression
PAIRING:
SINGLE_IMPORT:
ENRICHMENT:
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
TECHNOREBOOT_STAGE07F_R1_R1_REAL_PROFILE_FIX_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If the SAME real Avito page still reports zero listings, return BLOCKED.

# 16. STOP

After fix, real DOM verification, tests, package/version update, docs, commit/push and report:

STOP.

Do not deploy to VDS.
Wait for Owner acceptance.
