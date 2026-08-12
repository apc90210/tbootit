# TECHNOREBOOT — Stage06A-R8-R4 Fix Extension Import Failure + Cart Item Removal Regression

Репозиторий:

```powershell
C:\tbootit
```

Стартовая точка:

```text
Stage06A-R8-R3
Commit: 47ae1dc
```

Это corrective stage.

НЕ начинать Stage06A-R9.
НЕ начинать Stage06B.

---

# 1. Реальные owner blockers

## Blocker A — Avito extension payload дошёл до Technoreboot, но Product не создан

Owner выполнил реальную передачу объявления:

```text
Лазерный цветной принтер hp m252n на запчасти
Avito ID: 8313765236
Цена: 7099 ₽
```

Popup показал:

```text
Объявление 8313765236 успешно передано!
(Product ID: null, Результат: failed)
```

Owner затем проверил список товаров:

```text
товара в Technoreboot нет.
```

Это означает:

```text
Chrome Extension → Bridge transport = вероятно PASS
Bridge → Core import = FAIL
```

Также popup показывает ложный success message при фактическом `failed`.

---

## Blocker B — сломано удаление товара из корзины

Owner открыл:

```text
Техноребут → Товары
```

и обнаружил товар, уже лежащий в корзине.

При попытке удалить его из корзины:

```text
ошибка;
операция недоступна;
товар из корзины не удаляется.
```

Это отдельная regression в Inventory/Sales и должна быть исправлена в этом corrective stage.

---

# 2. Stage status

Текущий Avito extension probe НЕ принят.

```text
OWNER_ONE_ITEM_EXTENSION_PROBE: FAILED
CART_REMOVE_OWNER_CHECK: FAILED
```

---

# PART A — AVITO EXTENSION REAL IMPORT FAILURE

# 3. Сначала воспроизвести реальный import failure

Не переписывать import вслепую.

Использовать sanitized fixture, соответствующий owner case:

```text
external_item_id = 8313765236
title = Лазерный цветной принтер hp m252n на запчасти
price = 7099
```

Зафиксировать весь путь:

```text
Extension payload
→ Admin Shell proxy
→ avito-module extension bridge
→ import_service
→ Core integration endpoint
→ Core response
```

Report:

```text
EXTENSION_PAYLOAD_ACCEPTED
BRIDGE_RESPONSE
IMPORT_SERVICE_REQUEST
CORE_ENDPOINT
CORE_STATUS_CODE
CORE_RESPONSE_BODY
IMPORT_EXCEPTION
ROOT_CAUSE
```

Не выводить cookies/token values.

---

# 4. Найти точную причину `result=failed`

Проверить минимум:

```text
payload field names;
schema_version;
price type;
external_item_id type/string;
external_url;
description;
characteristics structure;
photos structure;
category;
brand/model;
status;
source_origin;
Core request schema;
Core endpoint validation;
photo import behaviour.
```

Не предполагать.

---

# 5. Bridge transport success != Core import success

Разделить результаты.

## Transport accepted

Это означает только:

```text
Bridge получил payload.
```

## Import success

Только если Core действительно:

```text
создал/обновил Product;
вернул Product ID;
создал/обновил ProductExternalListing.
```

---

# 6. Правильный API contract

Если Core import failed:

Bridge НЕ должен возвращать пользовательский success contract.

Предпочтительно:

```text
HTTP 422
```

для validation/business payload errors,

или:

```text
HTTP 502
```

если Core/backend integration недоступна/упала.

Response example:

```json
{
  "status": "failed",
  "external_item_id": "8313765236",
  "product_id": null,
  "message": "Не удалось импортировать объявление в Техноребут.",
  "error_code": "CORE_IMPORT_FAILED"
}
```

Не отдавать:

```text
"success": true
```

при `result=failed`.

---

# 7. Popup success/error logic

Popup должен показывать success ТОЛЬКО если:

```text
response status is success/created/updated/unchanged
AND product_id != null
```

Успех:

```text
✓ Объявление импортировано в Техноребут.
Product ID: 123
Результат: Created
```

Ошибка:

```text
✕ Объявление получено, но импорт товара завершился ошибкой.
Код: CORE_IMPORT_FAILED
```

Не показывать:

```text
«успешно передано»
```

при `failed`.

---

# 8. Debug visibility для owner

На `/avito/extension` добавить safe блок:

```text
Последняя передача
Avito ID
Время
Статус
Product ID
Результат
```

Например:

```text
Avito ID: 8313765236
Статус: Ошибка импорта
Product ID: —
```

Без traceback/token/cookies.

---

# 9. Developer diagnostics

Detailed exception/response оставить в logs:

```text
listing ID;
Core status code;
safe error body;
exception type.
```

Не логировать:

```text
extension token;
cookies;
full Avito HTML;
credentials.
```

---

# 10. Core import must create ProductExternalListing

При successful single listing import проверить:

```text
Product exists;
ProductExternalListing exists;
marketplace = avito;
external_item_id = 8313765236;
external_url saved;
product_id linked;
source_origin = avito.
```

---

# 11. One real listing contract

После fix owner listing:

```text
ID 8313765236
```

должен пройти:

```text
extension
→ bridge
→ avito-module
→ Core
→ Product
```

Owner product title/price должны совпасть:

```text
Лазерный цветной принтер hp m252n на запчасти
7099 ₽
```

Описание/характеристики/photos проверяются по фактическим данным страницы.

---

# 12. Idempotency после первого PASS

Только после первого успешного import:

```text
повторить передачу того же Avito ID.
```

Ожидается:

```text
same Product ID;
no duplicate Product;
no duplicate ExternalListing;
no duplicate photos.
```

---

# PART B — CART REMOVE REGRESSION

# 13. Воспроизвести owner cart bug

В реально запущенной системе:

```text
http://localhost:8011
→ Товары
→ корзина
→ удалить существующий товар
```

Зафиксировать:

```text
OWNER_PAGE_URL
CART_ITEM_ID / PRODUCT_ID if available
DELETE/POST REQUEST_URL
HTTP_METHOD
HTTP_STATUS
RESPONSE
REDIRECT_LOCATION
ROOT_CAUSE
```

---

# 14. Не предполагать причину

Проверить:

```text
same-origin proxy prefix;
form action;
JS fetch URL;
route path;
HTTP method mismatch;
stale cart session;
missing product;
backend container route;
redirect Location;
session/cookie scope;
cart item identity.
```

---

# 15. Cart remove owner contract

Из owner UI:

```text
localhost:8011/inventory/...
```

операция удаления должна выполняться через same-origin URL.

После:

```text
Удалить
```

ожидается:

```text
item removed;
cart count decreases;
page remains on localhost:8011;
no raw module port;
no «недоступен».
```

---

# 16. Stale/missing Product cart item

Если в корзине лежит item, продукт которого уже:

```text
удалён;
недоступен;
изменён;
не находится;
```

пользователь ВСЁ РАВНО должен иметь возможность удалить строку из корзины.

Правило:

```text
cart item cleanup must not require product to be currently available.
```

Если product unavailable:

```text
показать «Товар больше недоступен»
```

но кнопка:

```text
Удалить из корзины
```

должна работать.

---

# 17. Cart should not become unrecoverable

Не должно быть состояния:

```text
в корзине лежит битая строка
+
удалить невозможно
```

Добавить safe cleanup contract.

---

# 18. Existing sale/cart rules preserve

Не ломать:

```text
ручную цену;
гарантию;
способы оплаты;
быструю корзину;
остатки;
stock isolation;
sale create;
reports.
```

---

# PART C — TESTS

# 19. Avito tests

Добавить/обновить:

```text
avito-module/tests/test_extension_realistic_listing_import.py
avito-module/tests/test_extension_import_failure_contract.py
avito-module/tests/test_extension_product_id_required_for_success.py
avito-module/tests/test_extension_external_listing_created.py
avito-module/tests/test_extension_import_idempotency_realistic.py
```

---

# 20. Popup tests

Добавить:

```text
chrome-extension/technoreboot-avito/tests/test_failed_import_not_shown_as_success.py
chrome-extension/technoreboot-avito/tests/test_success_requires_product_id.py
chrome-extension/technoreboot-avito/tests/test_success_message_created.py
```

Explicit owner regression:

```text
response:
{
  product_id: null,
  result: "failed"
}
```

Expected:

```text
ERROR UI
NOT success UI
```

---

# 21. Admin Shell Avito status tests

Добавить:

```text
admin-shell/tests/test_extension_last_import_failure_ui.py
admin-shell/tests/test_extension_last_import_success_ui.py
```

---

# 22. Cart tests

Добавить/обновить:

```text
inventory-sales-module/tests/test_cart_remove_item.py
inventory-sales-module/tests/test_cart_remove_item_same_origin.py
inventory-sales-module/tests/test_cart_remove_unavailable_product.py
inventory-sales-module/tests/test_cart_remove_stale_item.py
```

Explicit regression:

```text
cart contains item
→ remove
→ item absent
→ HTTP success/expected redirect
```

---

# 23. Live runtime Avito probe before owner

Agent must perform safe fixture/mock live bridge import against running Core.

Do NOT send/modify real Avito.

Prove:

```text
POST extension listing fixture
→ bridge
→ Core
→ Product ID non-null
```

Then clean only test fixture via established safe test DB strategy.

Do NOT destructively modify live owner DB.

If no safe runtime fixture isolation exists:

```text
do not create cleanup hacks;
use automated isolated test environment.
```

---

# 24. Live runtime cart smoke

Against running owner UI, do NOT delete owner data automatically.

Use isolated/test cart/session if possible.

Prove route/method same-origin.

Owner performs final actual cart removal.

---

# 25. Version bump

If popup extension logic changes, bump:

```text
0.1.2 → 0.1.3
```

Update:

```text
manifest
popup footer
service worker/content version if used
bridge supported version
download filename
Admin Shell version label
```

Rebuild validated ZIP.

---

# 26. Owner download UX

Technoreboot must clearly show:

```text
Расширение Chrome 0.1.3
```

Owner should know old 0.1.2 must be replaced.

---

# 27. Regression suites

Mandatory:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

---

# 28. Safety

Verify:

```text
direct DB from avito-module = 0;
cookies transferred = 0;
credentials stored = 0;
extension token logged = 0;
owner DB destructive cleanup = 0;
raw module port owner links = 0.
```

---

# 29. Documentation

Update/create:

```text
docs/stage06a_r8_extension_import_completion.md
reports/stage06a_r8_r4_import_and_cart_regression_report.md
chrome-extension/technoreboot-avito/README.md
README.md
logs/2026-08-12.md
```

---

# 30. Report

```text
STATUS
OWNER_AVITO_FAILURE
OWNER_CART_FAILURE
AVITO_IMPORT_ROOT_CAUSE
EXTENSION_PAYLOAD
BRIDGE_CORE_CONTRACT
CORE_RESPONSE
FAILED_UI_BEFORE
FAILED_UI_AFTER
PRODUCT_CREATION
EXTERNAL_LISTING
PHOTO_IMPORT
IDEMPOTENCY
CART_REMOVE_REPRODUCTION
CART_REMOVE_ROOT_CAUSE
STALE_CART_ITEM_HANDLING
SAME_ORIGIN_CART_ROUTE
TESTS
RUNTIME
SAFETY
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS
OWNER_CHECK
FINAL_STATUS
```

---

# 31. Git

Expected starting HEAD:

```text
47ae1dc
```

или фактический потомок.

Only targeted add.

Forbidden:

```text
git add .
git add -A
git add -u
git reset
git clean
git rebase
git commit --amend
force push
```

Commit:

```powershell
git commit -m "Fix Avito extension import and cart removal"
git push origin main
```

---

# 32. Definition of Done

R8-R4 done only if:

```text
failed Core import root cause found;
failed import returns error contract;
popup never reports failed as success;
successful extension import returns non-null Product ID;
Product created in Core;
ProductExternalListing created;
source_origin = avito;
same listing reimport idempotent;
cart item can be removed;
stale/unavailable cart item can be removed;
cart action stays localhost:8011;
all regression tests PASS;
new extension package valid if version changed;
commit pushed;
git clean.
```

---

# 33. Owner check after R8-R4

Owner first updates extension if version changed.

Then:

## A. Cart

```text
1. Техноребут → Товары.
2. Открыть корзину.
3. Удалить существующий товар.
4. Confirm item removed.
```

## B. Avito one-item import

```text
1. Open ordinary Chrome.
2. Open owner listing ID 8313765236.
3. Open Technoreboot extension.
4. Confirm paired.
5. Click «Передать объявление в Техноребут».
6. Expect Product ID != null.
7. Open Техноребут → Товары.
8. Find imported printer.
9. Compare title/price/details/photos.
```

STOP after first successful import.

Do not repeat import until owner confirms first product correctness.

---

# 34. Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R4_IMPORT_AND_CART_READY_FOR_OWNER_CHECK

OWNER_CART_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_IMPORT_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_REIMPORT_NOT_YET_AUTHORIZED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
