# TECHNOREBOOT — Stage 07C-R1-R2
## Fix JSON import false success: "Создано 0, обновлено 0, ошибок 0"

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07C-R1-R2 — JSON Import Zero-Result Fix`

---

# 0. EXECUTION CONTRACT

Stage 07C JSON import/export is NOT accepted yet.

Owner performed a real browser import using a JSON file that matches the exact AI prompt/schema shown by Technoreboot.

UI returned:

`✓ Импорт успешно завершён! Создано: 0, обновлено: 0, ошибок: 0.`

This is an invalid success state.

The supplied file contained TWO products and neither had an explicit `id` or `sku`, so under the documented current policy they should have been CREATED as new products.

Expected result:

`Создано: 2`

or explicit product-level errors.

A result of:

`created=0, updated=0, errors=0`

for a non-empty valid `products[]` array must NEVER be shown as successful import.

This stage is narrowly focused on finding and fixing that defect.

Do NOT redesign JSON schema.
Do NOT change export behavior except regression fixes.
Do NOT implement product editor in this stage.
Do NOT return to Avito multi-photo extraction.
Do NOT start Internet deployment.
No Owner CLI workflow.

First copy this prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07C_R1_R2_JSON_IMPORT_ZERO_RESULT_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07C_R1_R2_JSON_IMPORT_ZERO_RESULT_FIX_PROMPT.md`

---

# 1. EXACT OWNER REPRODUCTION PAYLOAD

Use this exact payload in tests and live verification:

```json
{
  "format": "technoreboot-products",
  "version": 1,
  "products": [
    {
      "title": "Монитор Dell P2419H 24\" Full HD",
      "category": "Мониторы",
      "brand": "Dell",
      "model": "P2419H",
      "price": 8500.0,
      "purchase_price": 5000.0,
      "condition": "Б/у",
      "status": "in_stock",
      "quantity": 1,
      "description": "Монитор Dell P2419H в рабочем состоянии. Экран без трещин, изображение стабильное. Подходит для офиса, дома и работы с документами. В комплекте кабель питания.",
      "storage_location": "Витрина",
      "barcode": "",
      "characteristics": {
        "Диагональ": "24\"",
        "Разрешение": "1920x1080",
        "Тип матрицы": "IPS",
        "Частота обновления": "60 Гц",
        "Разъемы": "HDMI, DisplayPort, VGA, USB"
      },
      "photos": []
    },
    {
      "title": "Ноутбук HP ProBook 450 G6 15.6\"",
      "category": "Ноутбуки",
      "brand": "HP",
      "model": "ProBook 450 G6",
      "price": 24500.0,
      "purchase_price": 15500.0,
      "condition": "Б/у",
      "status": "in_stock",
      "quantity": 1,
      "description": "Рабочий ноутбук HP ProBook 450 G6. Подходит для офисных задач, учебы, интернета и удаленной работы. Ноутбук проверен, основные функции работают исправно. Блок питания в комплекте.",
      "storage_location": "Склад 1",
      "barcode": "",
      "characteristics": {
        "Процессор": "Intel Core i5-8265U",
        "Оперативная память": "8 ГБ",
        "Объем накопителя": "256 ГБ",
        "Тип накопителя": "SSD",
        "Видеокарта": "Intel UHD Graphics 620",
        "Диагональ экрана": "15.6\"",
        "Разрешение экрана": "1920x1080 Full HD",
        "Операционная система": "Windows 10 Pro"
      },
      "photos": []
    }
  ]
}
```

Do not alter this fixture when reproducing the Owner defect.

---

# 2. FIRST — CAPTURE THE REAL REQUEST/RESPONSE CONTRACT

Before fixing anything:

1. Reproduce through the actual web route used by `/products/json`.
2. Capture:
   - browser/Admin Shell request path;
   - HTTP method;
   - request content type;
   - exact JSON/body sent to Core;
   - Admin Shell proxy response;
   - Core response;
   - response status codes;
   - response JSON keys and values.
3. Compare frontend expected keys with actual backend response keys.

Explicitly inspect for likely mismatch such as:

- backend returns `created_count`, UI reads `created`;
- backend returns `results`, UI only reads `errors`;
- backend returns `imported`, UI reads `created`;
- backend returns `skipped`, UI ignores it;
- proxy wraps Core response under `detail`, `data`, `result`, etc.;
- upload form field contains JSON string while proxy sends wrong multipart/form encoding;
- textarea import path differs from file-upload path;
- Core parser accepts envelope but loop iterates wrong property;
- valid records are marked skipped but frontend hides skipped count;
- transaction commits nothing although response reports success.

Do not guess. Prove exact root cause.

Final report must contain:

```text
OWNER_REQUEST_PATH:
ADMIN_SHELL_REQUEST_BODY:
CORE_REQUEST_PATH:
CORE_REQUEST_BODY:
CORE_RESPONSE_STATUS:
CORE_RESPONSE_JSON:
FRONTEND_EXPECTED_KEYS:
PROVEN_ROOT_CAUSE:
```

---

# 3. NON-EMPTY IMPORT INVARIANT

For any request where:

```text
len(products) > 0
```

one of these must be true:

```text
created + updated + skipped + errors == len(products)
```

or equivalent exact accounting under the current response model.

No product may disappear from accounting.

Specifically:

- 2 products -> totals must account for 2;
- 10 products -> totals must account for 10.

If the backend returns zero total processed for non-empty input, return a controlled error, not success.

---

# 4. OWNER PAYLOAD EXPECTED RESULT

The exact Owner payload above contains:

- 2 products;
- no `id`;
- no `sku`.

Under current documented policy both should be new CREATE operations.

Required live result:

```text
created = 2
updated = 0
skipped = 0
errors = 0
```

Both records must exist in the Core DB afterwards with generated unique SKU values.

---

# 5. FIELD VERIFICATION

After successful import verify both products:

## Dell monitor
- title exact;
- category `Мониторы`;
- brand `Dell`;
- model `P2419H`;
- price `8500`;
- purchase_price `5000`;
- condition `Б/у`;
- quantity `1`;
- description;
- storage_location `Витрина`;
- all provided monitor characteristics.

## HP laptop
- title exact;
- category `Ноутбуки`;
- brand `HP`;
- model `ProBook 450 G6`;
- price `24500`;
- purchase_price `15500`;
- condition `Б/у`;
- quantity `1`;
- description;
- storage_location `Склад 1`;
- all provided laptop characteristics.

No silent field loss.

---

# 6. UI RESULT SUMMARY

The browser must display ALL outcome classes:

- Создано
- Обновлено
- Пропущено
- Ошибок

Example:

```text
Импорт завершён.
Создано: 2
Обновлено: 0
Пропущено: 0
Ошибок: 0
```

Do NOT show green success when all counters are zero for non-empty input.

---

# 7. FILE UPLOAD AND TEXTAREA MUST MATCH

The page supports both:
- uploaded `.json` file;
- pasted JSON text.

Test BOTH.

They must call the same canonical import logic and produce the same outcome.

---

# 8. REQUIRED TESTS

A. Exact Owner payload reproduces old 0/0/0 defect before fix.  
B. Exact Owner payload after fix -> created=2.  
C. DB contains both imported products.  
D. Generated SKUs are unique.  
E. Monitor common fields preserved.  
F. Monitor characteristics preserved.  
G. Laptop common fields preserved.  
H. Laptop characteristics preserved.  
I. File upload path succeeds.  
J. Textarea path succeeds.  
K. File and textarea paths use same canonical service.  
L. Non-empty input can never return unaccounted 0/0/0 success.  
M. Skipped result is shown/counts correctly.  
N. Invalid product reports an error and is accounted for.  
O. Mixed batch accounts for every item.  
P. Export/re-import round-trip still works.  
Q. Selected export still works.  
R. Full export still works.  
S. Relevant Core tests pass.  
T. Relevant Admin Shell tests pass.  
U. Avito regression smoke passes.  
V. OWNER access through gateway remains valid.

Report exact totals.

---

# 9. OWNER MANUAL CHECK

Browser-only.

1. Open `https://127.0.0.1:8443/products/json`
2. Paste the exact two-product JSON.
3. Click `Импортировать товары`.
4. Expected:
   - Создано: 2
   - Обновлено: 0
   - Пропущено: 0
   - Ошибок: 0
5. Confirm both products exist in catalog.
6. Confirm fields and characteristics.
7. Repeat once using `.json` file upload with separate disposable fixture.

No CLI.

---

# 10. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07C_R1_R2_JSON_IMPORT_ZERO_RESULT_FIX_PROMPT.md`

Create/update:

`docs\stage07c_r1_r2_json_import_zero_result_fix.md`

`reports\stage07c_r1_r2_json_import_zero_result_fix_report.md`

`logs\2026-09-09.md`

---

# 11. GIT / SAFETY

Do not commit runtime DB, exported owner data, backups, secrets or tokens.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

---

# 12. FINAL REPORT CONTRACT

Return:

```text
# Stage 07C-R1-R2 — JSON Import Zero-Result Fix

## Reproduction
OWNER_REQUEST_PATH:
CORE_REQUEST_PATH:
CORE_RESPONSE_BEFORE:
FRONTEND_RESULT_BEFORE:
PROVEN_ROOT_CAUSE:

## Fix
BACKEND_CHANGED:
ADMIN_SHELL_CHANGED:
FRONTEND_CHANGED:
ACCOUNTING_INVARIANT_ENFORCED:

## Owner Fixture
INPUT_PRODUCTS: 2
CREATED:
UPDATED:
SKIPPED:
ERRORS:

## Field Verification
DELL_MONITOR:
HP_LAPTOP:
CHARACTERISTICS_PRESERVED:

## Import Paths
TEXTAREA:
FILE_UPLOAD:
SAME_CANONICAL_LOGIC:

## Regression
SELECTED_EXPORT:
FULL_EXPORT:
ROUND_TRIP:
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
TECHNOREBOOT_STAGE07C_R1_R2_JSON_IMPORT_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If the exact two-product Owner payload still returns 0/0/0, return BLOCKED.

---

# 13. STOP

After fix, tests, docs, commit/push and report:

STOP.

Do not implement product editor yet.
Do not start Internet deployment.
Wait for Owner acceptance.
