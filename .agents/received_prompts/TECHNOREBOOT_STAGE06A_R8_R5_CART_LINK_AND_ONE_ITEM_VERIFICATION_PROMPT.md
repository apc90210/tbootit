# TECHNOREBOOT — Stage06A-R8-R5 Fix Empty Cart Products Link + Final One-Item Verification

Репозиторий:
```powershell
C:\tbootit
```

Старт:
```text
Stage06A-R8-R4
Commit: 5a8247f
```

Corrective stage. Не начинать R9/Stage06B.

## Owner result

Реальная карточка Avito успешно импортирована:

```text
Title: Лазерный цветной принтер hp m252n на запчасти
Avito ID: 8313765236
Current price: 6900 ₽
Product ID: 58
Result: updated
```

Это означает, что extension → bridge → Core уже работает и тот же Avito ID обновляет существующий Product.

## Новый blocker

Из пустой корзины ссылка «Товары» ведёт на:

```text
http://localhost:8011/products
```

Должно быть:

```text
http://localhost:8011/inventory/products
```

## Цель

Исправить все owner-facing ссылки из cart flow на canonical inventory prefix.

Проверить:
```text
inventory-sales-module/app/templates/cart.html
inventory-sales-module/app/templates/products.html
inventory-sales-module/app/templates/product_detail.html
inventory-sales-module/app/static/cart_quick_add.js
inventory-sales-module/app/routers/cart.py
```

Искать:
```text
href="/products"
location.href="/products"
window.location="/products"
redirect("/products")
```

Owner-facing target:
```text
/inventory/products
```

## Empty cart UX

Когда корзина пуста:

```text
Корзина пуста
[Перейти к товарам]
```

Кнопка должна вести на:
```text
/inventory/products
```

и возвращать HTTP 200 через localhost:8011.

## Preserve previous cart fix

Не ломать:
```text
удаление обычной позиции;
удаление stale/unavailable item;
обновление счётчика;
same-origin cart actions.
```

## Tests

Добавить:
```text
inventory-sales-module/tests/test_empty_cart_products_link.py
inventory-sales-module/tests/test_cart_products_link_same_origin.py
admin-shell/tests/test_empty_cart_inventory_route.py
```

Regression:
```text
empty cart page contains href="/inventory/products"
```

Forbidden:
```text
href="/products"
```

## Product 58 final verification

Не удалять Product 58.

Проверить:
```text
Product ID = 58
external_item_id = 8313765236
marketplace = avito
source_origin = avito
price = 6900
```

External listing:
```text
one ProductExternalListing for (avito, 8313765236)
product_id = 58
correct external_url
```

Не должно быть дубля Product/ExternalListing.

На `/avito/extension` last ingest должен показывать:
```text
Avito ID: 8313765236
Product ID: 58
Result: updated
Status: success
```

## Owner visual check

Подготовить Product 58 для проверки:
```text
title
price
description
characteristics
photos
```

Не делать повторный импорт автоматически.

## Regression

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

## Safety

```text
Product 58 preserved
no destructive live DB cleanup
direct DB from avito-module = 0
credentials/cookies exposed = 0
owner raw module ports = 0
```

## Docs

Обновить:
```text
docs/stage06a_r8_extension_import_completion.md
reports/stage06a_r8_r5_cart_link_and_owner_probe_report.md
README.md
logs/2026-08-12.md
```

## Git

Expected HEAD:
```text
5a8247f
```

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
git commit -m "Fix empty cart products link"
git push origin main
```

## Definition of Done

```text
empty-cart Products link = /inventory/products
no /products owner CTA remains
live click works on localhost:8011
cart remove still works
Product 58 preserved
Product 58 linked to Avito ID 8313765236
Product 58 price = 6900
no duplicate ProductExternalListing
last ingest = success / Product 58 / updated
all regression suites PASS
commit pushed
git clean
```

## Owner check

### Cart
```text
Open empty cart
→ click «Товары»
→ URL must be http://localhost:8011/inventory/products
```

### Product 58
Проверить:
```text
title
price = 6900 ₽
description
characteristics
photos
```

STOP. Full account sync not authorized.

## Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R5_CART_LINK_AND_ONE_ITEM_READY_FOR_OWNER_ACCEPTANCE

OWNER_CART_LINK_CHECK_REQUIRED: true
OWNER_PRODUCT_58_VISUAL_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_REIMPORT_NOT_REQUIRED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
