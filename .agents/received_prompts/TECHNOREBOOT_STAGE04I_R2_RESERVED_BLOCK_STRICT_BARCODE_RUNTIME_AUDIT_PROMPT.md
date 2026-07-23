# PROMPT — Техноребут / Stage04I-R2 Reserved Block, Strict Barcode Lookup and Runtime Audit

## Роль

Ты senior fullstack bugfix engineer, FastAPI engineer, архитектор товарного учёта, специалист по штрихкодам, Docker runtime auditor и release QA проекта «Техноребут».

Репозиторий:

```powershell
C:\tbootit
```

Нужно исправить нарушения Stage04I и выполнить недостающий runtime-аудит. Следующий этап не начинать.

## 1. Почему предыдущий Stage04I не принят

В отчёте указано:

```text
available = in_stock/reserved
```

Это ошибка. `reserved` нельзя продавать через обычный scanner flow.

Также заявлено:

```text
GET /api/products/by-barcode/{barcode}
ищет по barcode, SKU или numeric product ID
```

Это опасно. Endpoint `by-barcode` должен искать только точное совпадение `Product.barcode`.

Кроме того, отсутствуют:
- фактический runtime smoke barcode/scanner/price tag;
- число старых товаров, получивших barcode;
- доказательство идемпотентности второго bulk generation;
- Product.price до/после ручной цены ценника;
- аудит ошибочного commit `32ab7a0`;
- runtime regression Stage04H;
- SHA256 правильного Stage04I prompt;
- единый итоговый test count: в отчёте одновременно 110 и 109 Core tests.

## 2. Текущий статус

```text
STAGE04I_OWNER_CHECK_BLOCKED_RESERVED_PRODUCT_SELLABLE_AND_RUNTIME_AUDIT_INCOMPLETE
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_LOOKUP_RUNTIME_AUDIT_READY_FOR_OWNER_RECHECK
```

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

## 3. Запреты

Запрещено:

```text
разрешать reserved в обычной продаже
искать SKU/ID через by-barcode
закрывать задачу только unit-тестами
ссылаться на старые runtime результаты
direct DB access из inventory-sales-module
отдельная DB
git add .
git add -A
git add -u
git commit --amend
git reset
git clean
rebase
force push
Base.metadata.drop_all/create_all
runtime DB/temp/cache в git
```

## 4. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_BARCODE_RUNTIME_AUDIT_PROMPT.md
```

И основной prompt:

```text
TECHNOREBOOT_STAGE04I_BARCODES_SCANNER_PRICE_TAGS_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit\.agents\received_prompts
C:\tbootit
```

Если repair prompt найден в Downloads, скопировать:

```powershell
Copy-Item `
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_BARCODE_RUNTIME_AUDIT_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_BARCODE_RUNTIME_AUDIT_PROMPT.md `
  -Force
```

Посчитать SHA256 обоих prompt:

```powershell
Get-FileHash C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_BARCODE_RUNTIME_AUDIT_PROMPT.md -Algorithm SHA256
Get-FileHash C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_BARCODES_SCANNER_PRICE_TAGS_PROMPT.md -Algorithm SHA256
```

В отчёте:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
REPAIR_PROMPT_SHA256:
STAGE04I_PROMPT_SHA256:
```

## 5. Preflight

```powershell
Set-Location C:\tbootit
git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -15
git diff --name-status
git diff --stat
docker compose ps
```

Зафиксировать наличие commits:

```text
32ab7a0
e49f59d
```

## 6. Аудит неправильного commit 32ab7a0

```powershell
git show --stat --oneline 32ab7a0
git show --name-status 32ab7a0
git diff 32ab7a0^ 32ab7a0 -- inventory-sales-module
```

Проверить сохранность:

```text
Stage04H cancel UI
Stage04H reissue UI
Stage04H status filters
Stage04H receipt banners
Stage04G report filters
Stage04G canceled/superseded exclusions
```

Если регрессии есть, исправить точечно. Слепой revert запрещён.

## 7. Strict barcode endpoint

Проверить:

```text
core/app/routers/products.py
core/app/services/barcodes.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/cart.py
```

Endpoint:

```text
GET /api/products/by-barcode/{barcode}
```

должен делать только:

```python
Product.barcode == barcode
```

Нельзя искать через него по:

```text
Product.id
Product.sku
title
brand
model
serial_number
```

Unknown barcode:

```text
404
Товар с таким штрихкодом не найден.
```

Generic search `/api/products?q=...` продолжает поддерживать SKU/ID/name.

## 8. Scanner sellability

Разрешены только:

```text
in_stock
available
quantity > 0
допустимая магазинная локация
```

Блокировать:

```text
reserved
sold
draft
quantity <= 0
неподходящую локацию
```

Русские сообщения:

```text
reserved:
Товар найден, но зарезервирован и недоступен для продажи.

sold:
Товар уже продан и недоступен для продажи.

draft:
Товар ещё не готов к продаже.

quantity <= 0:
Товар найден, но отсутствует в остатках.
```

Товар не должен попасть в корзину.

## 9. Core tests

Обновить:

```text
core/tests/test_product_barcodes.py
core/tests/test_product_search.py
```

Покрыть:

```text
exact barcode lookup
SKU не совпадает в by-barcode
product ID не совпадает в by-barcode
title не совпадает в by-barcode
unknown barcode = 404
generic search находит SKU
generic search находит ID
barcode uniqueness
```

## 10. Inventory scanner tests

Обновить:

```text
inventory-sales-module/tests/test_barcode_scanner_ui.py
```

Покрыть:

```text
in_stock добавляется
available добавляется
reserved блокируется
sold блокируется
draft блокируется
quantity=0 блокируется
неверная локация блокируется
unknown barcode показывает русскую ошибку
SKU в scanner не добавляет товар
product ID в scanner не добавляет товар
unique item не дублируется
autofocus сохраняется
```

## 11. Docker rebuild и финальные тесты

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose up -d avito-module
docker compose ps

docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

В отчёте указать только финальные фактические числа. Не смешивать 109 и 110.

## 12. Runtime audit barcode

Получить через Core или служебный код внутри Core:

```text
TOTAL_PRODUCTS
WITH_BARCODE_BEFORE
WITHOUT_BARCODE_BEFORE
DUPLICATES_BEFORE
```

### Single generate

Выбрать реальный товар без barcode:

```text
PRODUCT_ID
BARCODE_BEFORE
BARCODE_AFTER
GENERATED
```

Повторный generate:

```text
barcode не меняется
generated=false
```

### Bulk

Первый запуск:

```text
processed
generated
skipped_existing
errors
WITHOUT_BARCODE_AFTER_FIRST
DUPLICATES_AFTER_FIRST
```

Второй запуск:

```text
generated=0
duplicates=0
существующие barcode не изменились
```

Указать, сколько старых товаров реально получили barcode.

## 13. Runtime strict lookup

Для реального товара проверить:

```text
реальный barcode через /by-barcode → 200 и правильный product_id
SKU через /by-barcode → 404
product ID через /by-barcode → 404
SKU через generic search → найден
ID через generic search → найден
```

## 14. Runtime scanner

Проверить фактически:

```text
in_stock barcode → товар добавлен
reserved barcode → не добавлен
sold barcode → не добавлен
quantity=0 barcode → не добавлен
unknown barcode → не добавлен
SKU в scanner → не добавлен
product ID в scanner → не добавлен
```

Для каждого сценария указать реальный HTTP status/UI result.

## 15. Runtime price tag

Выбрать реальный товар:

```text
PRODUCT_ID
PRODUCT_PRICE_BEFORE
BARCODE
```

Открыть:

```text
/products/{id}/price-tag/58x40
```

Проверить:

```text
@page 58mm 40mm
.price-tag width 58mm
.price-tag height 40mm
SVG barcode
barcode digits
title
price
warranty
Печать
Закрыть
```

Указать ручную цену:

```text
PRINT_PRICE
```

После preview снова получить товар через Core:

```text
PRODUCT_PRICE_AFTER
```

Должно быть:

```text
PRODUCT_PRICE_AFTER == PRODUCT_PRICE_BEFORE
```

## 16. Runtime regression Stage04H

Выполнить реальный smoke:

```text
создать тестовый товар
создать продажу
отменить продажу
проверить возврат товара
проверить уменьшение отчёта
выполнить reissue
проверить old/new linkage
проверить повторное списание
```

Зафиксировать:

```text
PRODUCT_ID
ORIGINAL_SALE_ID
REISSUED_SALE_ID
REPORT_TOTAL_BEFORE
REPORT_TOTAL_AFTER_SALE
REPORT_TOTAL_AFTER_CANCEL
REPORT_TOTAL_AFTER_REISSUE
```

## 17. Runtime regression Stage04G

Проверить:

```text
/reports/sales
/reports/sales?period=today
/reports/sales?period=week
/reports/sales?period=month
/reports/sales?period=year
```

Ожидаемо:

```text
везде 200
date_to = сегодня
default = 1 января — сегодня
canceled/superseded не входят в деньги
reissued входит
```

## 18. Safety scans

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

## 19. Документация

Создать:

```text
docs/stage04i_r2_reserved_block_strict_lookup_runtime_audit.md
reports/stage04i_r2_reserved_block_strict_lookup_runtime_audit_report.md
```

Обновить:

```text
logs/2026-07-23.md
```

Report должен содержать:

```text
причины отказа предыдущему Stage04I
аудит commit 32ab7a0
исправления reserved/by-barcode
barcode counts before/after
single и bulk runtime
strict lookup runtime
scanner runtime по всем статусам
Product.price before/print/after
Stage04H runtime regression
Stage04G runtime regression
финальные Core/Inventory/Avito tests
safety scans
commit/push/final git status
```

## 20. Git

Только targeted add:

```powershell
git add core/app/routers/products.py
git add core/app/services/barcodes.py
git add core/tests/test_product_barcodes.py
git add core/tests/test_product_search.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/cart.py
git add inventory-sales-module/app/templates/cart.html
git add inventory-sales-module/tests/test_barcode_scanner_ui.py
git add inventory-sales-module/tests/test_price_tag_58x40.py

git add docs/stage04i_r2_reserved_block_strict_lookup_runtime_audit.md
git add reports/stage04i_r2_reserved_block_strict_lookup_runtime_audit_report.md
git add logs/2026-07-23.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_BARCODE_RUNTIME_AUDIT_PROMPT.md
```

```powershell
git commit -m "Block reserved scanner items and audit Stage 04I runtime"
git push origin main
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

Финальный Git status должен быть пустым.

## 21. Definition of Done

```text
reserved blocked
sold/draft/quantity zero blocked
by-barcode exact only
SKU/ID не принимаются scanner
generic search SKU/ID работает
commit 32ab7a0 audited
Stage04H runtime passed
Stage04G runtime passed
single generation proven
bulk generation proven
second bulk generated=0
duplicates=0
old product barcode count reported
manual print price isolation proven
Core tests PASS
Inventory tests PASS
Avito tests PASS
single consistent test counts
safety scans clean
targeted commit
push
clean git
owner check required
```

## 22. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_LOOKUP_RUNTIME_AUDIT_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_LOOKUP_RUNTIME_AUDIT_FAIL

BLOCKERS:
...
```
