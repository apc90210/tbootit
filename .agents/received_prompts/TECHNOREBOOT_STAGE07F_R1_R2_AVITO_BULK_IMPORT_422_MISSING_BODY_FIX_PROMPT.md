# TECHNOREBOOT — Stage 07F-R1-R2
## Fix Avito bulk import 422 `body field required` + accounting / false success

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07F-R1-R2 — Bulk Import 422 Missing Body Fix`

---

# 0. EXECUTION CONTRACT

Stage 07F-R1/R1-R1 is NOT accepted yet.

Real Owner browser test with extension v0.2.49 now correctly detects the real Avito listings page:

```text
Найдено объявлений на странице: 50
Страница: 1 из 3
```

So the real DOM/list detection fix is working.

However, when Owner starts bulk import, the extension reaches processing and fails with:

```text
Обработка страницы 2...

Найдено страниц: 3
Обработано: 50 / 50
Создано: 0
Обновлено: 0
Пропущено: 0
Ошибок: 1

1: Ошибка сервера 422:
[{
  "type":"missing",
  "loc":["body"],
  "msg":"Field required",
  "input":null,
  "url":"https://errors.pydantic.dev/2.5/v/missing"
}]
```

Despite the error, UI then incorrectly shows:

```text
✓ Импорт успешно завершен!
Страниц обработано: 2, объявлений: 50
Создано новых: 0, обновлено: 0, ошибок: 1
```

This stage must fix BOTH defects:

1. the real `422 body field required` request failure;
2. false green success / broken item accounting.

Do NOT redesign the feature.
Do NOT change Avito DOM selectors unless the real bug requires it.
Do NOT use official Avito API.
Do NOT reopen full-gallery extraction.
Do NOT start VDS deployment.
No Owner CLI.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07F_R1_R2_AVITO_BULK_IMPORT_422_MISSING_BODY_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R2_AVITO_BULK_IMPORT_422_MISSING_BODY_FIX_PROMPT.md`

---

# 1. PRESERVE CONFIRMED WORKING REAL-DOM BEHAVIOR

Do not regress the successful v0.2.49 detection.

The same Owner page currently correctly reports:

```text
50 listings on current page
page 1 of 3
```

Required after fix:

```text
CURRENT_PAGE_LISTING_COUNT = 50
TOTAL_PAGES = 3
```

or the real current equivalent if Avito changes during testing.

The problem now is transport/request handling, not basic card discovery.

---

# 2. REPRODUCE THE EXACT 422 THROUGH THE REAL EXTENSION FLOW

Reproduce through the same flow:

```text
Avito page
-> content.js
-> popup.js
-> service_worker.js
-> Technoreboot extension bridge
-> avito-module
-> Core
```

Capture EVERY hop.

Mandatory report:

```text
PAGE_NUMBER:
EXTRACTED_ITEMS_COUNT:
POPUP_MESSAGE_ACTION:
POPUP_MESSAGE_PAYLOAD:
SERVICE_WORKER_RECEIVED_MESSAGE:
SERVICE_WORKER_FETCH_URL:
SERVICE_WORKER_FETCH_METHOD:
SERVICE_WORKER_REQUEST_HEADERS:
SERVICE_WORKER_REQUEST_BODY:
AVITO_MODULE_ROUTE:
AVITO_MODULE_HTTP_STATUS:
AVITO_MODULE_RESPONSE:
CORE_ROUTE_IF_REACHED:
CORE_REQUEST_BODY_IF_REACHED:
CORE_HTTP_STATUS_IF_REACHED:
PROVEN_ROOT_CAUSE:
```

Do not guess.

The FastAPI error:

```json
{
  "type": "missing",
  "loc": ["body"],
  "msg": "Field required",
  "input": null
}
```

strongly indicates a POST endpoint received no request body, but prove exactly where the body is lost.

---

# 3. AUDIT MESSAGE / FETCH CONTRACT

Inspect current v0.2.49 code in:

- `popup.js`
- `service_worker.js`
- `content.js`
- `avito-module/app/routers/extension_bridge.py`

Determine exact expected payload for bulk batch.

Example only:

```json
{
  "items": [...]
}
```

Verify whether popup currently sends something like:

```js
chrome.runtime.sendMessage({
  action: "bulk_import_batch",
  payload: ...
})
```

and whether service worker reads the SAME key.

Explicitly inspect for mismatches such as:

- sender uses `items`, receiver reads `payload`;
- sender uses `payload`, receiver reads `data`;
- receiver calls fetch without `body`;
- receiver uses `body: JSON.stringify(undefined)`;
- page-navigation branch calls the message without payload;
- current-page path works but all-pages path sends an empty body;
- first page and subsequent pages use different functions;
- `Content-Type: application/json` missing;
- request is being made as GET instead of POST;
- message object is lost when the tab navigates/reloads;
- async tab update destroys popup-local state before body creation.

---

# 4. BATCH ENDPOINT CONTRACT

The bulk endpoint must have ONE explicit request contract.

Preferred conceptual shape:

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

Use actual canonical names already present in project.

For every batch:

- HTTP method must be POST;
- `Content-Type: application/json`;
- body must be non-empty valid JSON;
- `items` must exist;
- empty array is allowed only if intentionally handled as no-op/warning;
- missing body must never occur in normal extension flow.

---

# 5. CURRENT PAGE VS ALL PAGES MUST USE SAME BATCH SENDER

Critical requirement:

`Импортировать текущую страницу`

and

`Импортировать все объявления`

must call the SAME canonical batch submission helper.

Do not maintain two separate implementations that can drift.

Recommended architecture:

```text
extract page
-> normalize items
-> sendBulkBatch(items)
-> update counters
```

The all-pages flow only adds navigation/pagination around that same helper.

---

# 6. PAGINATION STATE MUST SURVIVE NAVIGATION

The screenshot shows the extension successfully moved toward page 2.

Inspect whether popup-driven navigation causes state loss.

If popup closes/reloads during `chrome.tabs.update()` or page navigation:

- do not depend on transient popup-local variables only;
- keep minimal import session state in extension service worker / `chrome.storage.session` (or current appropriate extension mechanism);
- preserve:
  - seen Avito IDs;
  - current page;
  - target/total pages;
  - counters;
  - cancel state.

Do not overengineer.

But the import must not lose the batch payload or session when moving from page 1 to page 2.

---

# 7. RESULT ACCOUNTING INVARIANT

Current screenshot is logically impossible:

```text
Обработано: 50
Создано: 0
Обновлено: 0
Пропущено: 0
Ошибок: 1
```

50 processed listings cannot disappear from outcome accounting.

For each submitted item:

```text
created + updated + skipped + errors == submitted_items
```

Across all pages:

```text
total_created
+ total_updated
+ total_skipped
+ total_errors
== total_unique_submitted
```

No silent loss.

If an entire 50-item HTTP batch fails before item processing:
- count the batch failure explicitly;
- do NOT mark all 50 as successfully "processed";
- show page/batch failure clearly.

Preferred UX:

```text
Страница 1:
Отправлено: 50
Создано: 47
Обновлено: 3
Ошибок: 0
```

If request itself fails:

```text
Страница 1 не импортирована:
Ошибка отправки пакета (HTTP 422)
```

Do not pretend the 50 items were processed.

---

# 8. NO GREEN SUCCESS WITH ERRORS / ZERO IMPORTED

The extension must show green success only if:

```text
errors == 0
AND (created + updated + skipped) > 0
AND all intended pages completed
```

If `errors > 0`, final state must be warning/error, not green success.

Example:

```text
⚠ Импорт завершён с ошибками
Страниц обработано: 2 из 3
Создано: 50
Обновлено: 0
Ошибок: 1
```

If a batch request prevents continuation:

```text
✗ Импорт остановлен из-за ошибки
Страница 2 не импортирована
```

No `✓ Импорт успешно завершен!`.

---

# 9. SAFE ERROR UI

Do not expose raw Pydantic objects/URLs to Owner.

Translate server 422 into concise Russian message.

For this exact case:

```text
Ошибка отправки данных в Техноребут: сервер не получил пакет объявлений.
```

Technical details may be available under `Показать детали`, but:
- no giant horizontal raw JSON line;
- no `pydantic.dev` URL in normal UI.

---

# 10. IDEMPOTENCY / DUPLICATES

After transport fix:

First import on one real 50-item page:

```text
created + updated + skipped + errors = 50
```

Repeat same page:

```text
created = 0
```

unless new Avito items appeared in between.

Product count must not grow due to duplicates.

Same Avito ID remains canonical identity.

---

# 11. REAL 3-PAGE ACCEPTANCE TARGET

Owner's current real page reports 3 pages, first page 50 listings.

The actual total may be:
- 50 + 50 + N
or another real distribution.

Required:
- page 1 imported;
- page 2 imported;
- page 3 imported;
- no transport 422;
- every unique listing accounted for;
- later-page items visible in Technoreboot.

Report real counts:

```text
PAGE_1_EXTRACTED:
PAGE_1_CREATED:
PAGE_1_UPDATED:
PAGE_1_ERRORS:

PAGE_2_EXTRACTED:
PAGE_2_CREATED:
PAGE_2_UPDATED:
PAGE_2_ERRORS:

PAGE_3_EXTRACTED:
PAGE_3_CREATED:
PAGE_3_UPDATED:
PAGE_3_ERRORS:

TOTAL_UNIQUE:
TOTAL_CREATED:
TOTAL_UPDATED:
TOTAL_SKIPPED:
TOTAL_ERRORS:
```

---

# 12. REQUIRED TESTS

## TEST A
Reproduce old 422 from real all-pages flow before fix.

## TEST B
Bulk sender always emits non-empty JSON body for non-empty item list.

## TEST C
Current-page import and all-pages import call same batch sender.

## TEST D
50-item batch reaches Avito module with exactly 50 items.

## TEST E
Avito module response accounts for all 50.

## TEST F
Page navigation does not lose import session state.

## TEST G
Page 2 uses valid request body.

## TEST H
Page 3 uses valid request body.

## TEST I
No raw Pydantic error displayed in normal extension UI.

## TEST J
Any error prevents green all-success state.

## TEST K
Counter invariant holds per batch.

## TEST L
Counter invariant holds across full multi-page import.

## TEST M
Second import creates no duplicates.

## TEST N
Detailed enrichment still updates same product.

## TEST O
v0.2.49 real listing detection remains non-zero.

## TEST P
Pairing works.

## TEST Q
Single-listing import works.

## TEST R
JSON import/export works.

## TEST S
Product editor works.

## TEST T
Avito module full suite passes.

## TEST U
Core full/relevant suite passes.

## TEST V
Admin Shell relevant suite passes.

Report exact totals.

---

# 13. EXTENSION VERSION

Bump version:

`0.2.49` -> `0.2.50`

Update consistently:
- manifest;
- popup/service worker displayed/internal version;
- download ZIP;
- `/avito/extension`;
- tests.

Ensure downloaded ZIP really contains v0.2.50.

---

# 14. OWNER MANUAL CHECK

Browser-only.

1. Download/update extension v0.2.50.
2. Open SAME Avito listings page.
3. Confirm:
   - listings count > 0;
   - real `1 из 3`.
4. Click `Импортировать текущую страницу`.
5. Expected:
   - no HTTP 422;
   - submitted/accounted count = 50;
   - created/updated/skipped/errors sum to 50.
6. Open Technoreboot `Товары` and verify those items exist.
7. Return to Avito and click `Импортировать все объявления`.
8. Confirm page 2 and page 3 are actually processed.
9. Final result must NOT contain false green success when any page failed.
10. Repeat all-pages import and confirm no duplicate growth.

No terminal.

---

# 15. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R2_AVITO_BULK_IMPORT_422_MISSING_BODY_FIX_PROMPT.md`

Create/update:

`docs\stage07f_r1_r2_avito_bulk_import_422_missing_body_fix.md`

`reports\stage07f_r1_r2_avito_bulk_import_422_missing_body_fix_report.md`

`logs\2026-09-10.md`

---

# 16. GIT / SAFETY

Do not commit:
- Owner Avito private data;
- cookies/session data;
- runtime DB;
- auth keys;
- photos;
- backup files.

Commit source/tests/docs only.

Push `origin/main`.

Verify clean worktree.

---

# 17. FINAL REPORT CONTRACT

Return:

```text
# Stage 07F-R1-R2 — Bulk Import 422 Missing Body Fix

## Reproduction
REAL_PAGE_LISTINGS:
REAL_TOTAL_PAGES:
PAGE_WHERE_422_OCCURRED:
POPUP_MESSAGE_PAYLOAD_BEFORE:
SERVICE_WORKER_REQUEST_BODY_BEFORE:
AVITO_MODULE_RESPONSE_BEFORE:
PROVEN_ROOT_CAUSE:

## Contract Fix
CANONICAL_BATCH_HELPER:
REQUEST_METHOD:
CONTENT_TYPE:
REQUEST_BODY_SHAPE:
CURRENT_PAGE_AND_ALL_PAGES_SHARE_HELPER:
SESSION_STATE_SURVIVES_NAVIGATION:

## Accounting
PER_BATCH_INVARIANT:
GLOBAL_INVARIANT:
FALSE_PROCESSED_COUNT_FIXED:
GREEN_SUCCESS_POLICY:
SAFE_ERROR_UI:

## Real Multi-page
PAGE_1_EXTRACTED:
PAGE_1_RESULT:
PAGE_2_EXTRACTED:
PAGE_2_RESULT:
PAGE_3_EXTRACTED:
PAGE_3_RESULT:
TOTAL_UNIQUE:
TOTAL_CREATED:
TOTAL_UPDATED:
TOTAL_SKIPPED:
TOTAL_ERRORS:

## Regression
REAL_DOM_DETECTION:
PAIRING:
SINGLE_IMPORT:
ENRICHMENT:
JSON:
PRODUCT_EDITOR:

## Extension
VERSION_AFTER:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07F_R1_R2_BULK_422_FIX_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If page 2 or page 3 still sends an empty request body, return BLOCKED.

If 50 extracted items can still result in unaccounted counters, return BLOCKED.

---

# 18. STOP

After fix, tests, extension package/version update, docs, commit/push and report:

STOP.

Do not deploy to VDS.
Wait for Owner acceptance.
