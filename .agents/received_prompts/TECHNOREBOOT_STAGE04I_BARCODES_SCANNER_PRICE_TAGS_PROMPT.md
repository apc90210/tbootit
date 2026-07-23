# PROMPT — Техноребут / Stage 04I Barcodes, Scanner Search and 58×40 Price Tags

## Роль агента

Ты senior fullstack developer, архитектор товарного учёта, FastAPI engineer, Jinja2 UI developer, специалист по штрихкодам и печатным формам, Docker runtime validator и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — реализовать следующий этап:

```text
Stage04I — Штрихкоды товаров, поиск/добавление товара сканером и ценники 58×40 мм
```

После реализации этап обязательно проходит ручную проверку владельцем.

---

# 1. Архитектурный контекст

```text
Core API + DB владеет товарами, продажами, статусами, аудитом и штрихкодами.
inventory-sales-module работает только через HTTP API Core.
Прямой доступ inventory-sales-module к Core DB запрещён.
Все модули работают в отдельных Docker-контейнерах.
```

---

# 2. Принятое состояние

Приняты этапы:

```text
Stage04G — отчёты по продажам
Stage04H — отмена продажи, возврат товара, повторное оформление
```

Следующая цель:

```text
быстрый поиск товара сканером
добавление товара в корзину по штрихкоду
единый barcode для товара
индивидуальный ценник 58×40 мм
```

---

# 3. Требования владельца

Реализовать:

```text
1. У каждого товара может быть уникальный штрихкод.

2. Старым товарам без штрихкода можно:
   - сгенерировать штрихкод вручную;
   - массово сгенерировать отсутствующие штрихкоды.

3. Поиск товаров должен работать по:
   - штрихкоду;
   - названию;
   - SKU/артикулу;
   - ID товара.

4. В продаже товар можно добавить сканером:
   - сканер вводит barcode;
   - Enter запускает поиск;
   - найденный товар добавляется в корзину;
   - поле очищается;
   - фокус возвращается в поле сканера.

5. Если товар недоступен:
   - sold;
   - reserved;
   - quantity=0;
   выводится понятная русская ошибка.

6. У каждого товара есть кнопка:
   "Ценник 58×40".

7. Ценник показывает:
   - название;
   - цену;
   - штрихкод;
   - числовое значение;
   - гарантию или "Без гарантии";
   - при необходимости состояние Б/У.

8. Цена для печати:
   - по умолчанию берётся из товара;
   - может быть изменена вручную;
   - изменение не должно менять Product.price в Core.
```

---

# 4. Целевой статус

```text
TECHNOREBOOT_STAGE04I_BARCODES_SCANNER_PRICE_TAGS_READY_FOR_OWNER_CHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 5. Запреты

Запрещено:

```text
direct DB access из inventory-sales-module
отдельная DB для штрихкодов
перезаписывать существующие barcode при bulk generation
создавать дубли barcode
менять Product.price при печати ценника
делать только массовую печать без кнопки у товара
git add .
git add -A
git add -u
git commit --amend
git reset
git clean
rebase
force push
runtime DB/temp/cache в git
Base.metadata.drop_all/create_all
```

---

# 6. Prompt discovery

Найти:

```text
TECHNOREBOOT_STAGE04I_BARCODES_SCANNER_PRICE_TAGS_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit
C:\tbootit\.agents
C:\tbootit\.agents\received_prompts
C:\tbootit\prompts
C:\tbootit\docs
```

Если найден в Downloads — скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В report указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 7. Preflight

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Если worktree dirty — сначала определить причину.

---

# 8. Исследовать текущий код

Проверить:

```text
core/app/models.py
core/app/schemas.py
core/app/routers/products.py
core/app/main.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/products.py
inventory-sales-module/app/routers/sales.py
inventory-sales-module/app/templates/products_list.html
inventory-sales-module/app/templates/product_detail.html
inventory-sales-module/app/templates/sales_create.html
inventory-sales-module/app/templates/price_tag*.html
core/tests
inventory-sales-module/tests
docker-compose.yml
```

Определить:

```text
есть ли barcode/SKU
как устроен текущий поиск
как добавляется товар в корзину
как сейчас печатается ценник
какие product statuses используются
```

---

# 9. Модель данных

Добавить в Product:

```text
barcode: str | null
sku: str | null
```

Требования:

```text
barcode уникальный
barcode индексированный
существующие данные не теряются
миграция идемпотентна
```

Если `sku` уже существует — использовать существующее поле.

---

# 10. Формат barcode

Выбрать внутренний формат магазина.

Предпочтительный MVP:

```text
12 цифр
пример: 200000000123
```

Для печати предпочтительно Code128.

Если выбран EAN-13:

```text
обязательно корректно считать контрольную цифру
```

Формат описать в документации.

---

# 11. Генерация barcode

Добавить:

```text
generate_unique_barcode()
```

Требования:

```text
проверяет уникальность
не перезаписывает существующий barcode
работает повторяемо
bulk затрагивает только NULL/blank
```

---

# 12. Core API

Добавить:

```text
GET /api/products/by-barcode/{barcode}
POST /api/products/{product_id}/barcode/generate
POST /api/products/barcodes/generate-missing
```

Расширить поиск:

```text
GET /api/products?search=...
```

или:

```text
GET /api/products/search?q=...
```

Поиск:

```text
barcode
sku
id
name
```

При точном barcode товар должен идти первым.

---

# 13. Примеры response

Lookup:

```json
{
  "id": 123,
  "name": "Ноутбук Lenovo ThinkPad",
  "barcode": "200000000123",
  "sku": "NB-00123",
  "price": 18500,
  "status": "in_stock",
  "quantity": 1,
  "warranty_days": 30
}
```

Single generate:

```json
{
  "product_id": 123,
  "barcode": "200000000123",
  "generated": true
}
```

Bulk generate:

```json
{
  "processed": 150,
  "generated": 47,
  "skipped_existing": 103,
  "errors": []
}
```

---

# 14. Ошибки API

```text
404 — barcode/product не найден
409 — duplicate/conflict
422 — некорректный barcode
```

Сообщения UI должны быть по-русски.

---

# 15. Audit/events

Создать события:

```text
product.barcode_generated
product.barcode_assigned
product.barcode_bulk_generated
```

Payload:

```text
product_id
barcode
actor
source
timestamp
```

---

# 16. Inventory UI — список товаров

Добавить поиск:

```text
Название, ID, артикул или штрихкод
```

При точном barcode:

```text
открыть или выделить найденный товар
```

На каждой строке товара:

```text
Ценник 58×40
```

---

# 17. Карточка товара

Показать:

```text
Штрихкод
Артикул
Цена
Статус
Гарантия
```

Кнопки:

```text
Сгенерировать штрихкод
Ценник 58×40
```

Если barcode уже есть — не перезаписывать.

---

# 18. Массовая генерация UI

Добавить действие:

```text
Сгенерировать отсутствующие штрихкоды
```

С подтверждением:

```text
Будут созданы штрихкоды только товарам, у которых они отсутствуют.
Существующие штрихкоды не изменятся.
```

Показать результат:

```text
Сгенерировано
Пропущено
Ошибки
```

---

# 19. Поле сканера в продаже

На странице продажи добавить:

```text
Сканировать штрихкод
```

Требования:

```text
autofocus
Enter отправляет barcode
точный lookup через Core
товар добавляется в корзину
поле очищается
фокус возвращается
```

---

# 20. Корзина

Если товар доступен:

```text
status=in_stock/available
quantity > 0
```

добавить.

Если товар уже в корзине:

```text
количественный товар — увеличить quantity
уникальный товар — не создавать дубль строки
```

Если недоступен:

```text
Товар найден, но сейчас недоступен для продажи.
```

Если не найден:

```text
Товар со штрихкодом ... не найден.
```

---

# 21. Ценник 58×40 — route

Добавить:

```text
GET /products/{product_id}/price-tag/58x40
```

Форма перед preview:

```text
Цена для печати
Гарантия
Краткое состояние
```

---

# 22. Ценник 58×40 — CSS

Обязательно:

```css
@page {
  size: 58mm 40mm;
  margin: 0;
}

.price-tag {
  width: 58mm;
  height: 40mm;
}
```

Проверить:

```text
одна страница
нет обрезки
нет второй пустой страницы
нет системных кнопок внутри печатной области
```

---

# 23. Содержимое ценника

Обязательно:

```text
Название товара
Цена
Штрихкод
Код цифрами
Гарантия
```

Опционально:

```text
SKU
Состояние Б/У
Техноребут
```

Приоритет:

```text
Цена — крупно
Название — 2–3 строки
Штрихкод — сканируемо
Код — читаемо
Гарантия — компактно
```

---

# 24. Ручная цена

По умолчанию:

```text
product.price
```

Пользователь может изменить цену только для печати.

Критическое правило:

```text
Product.price в Core не меняется.
```

Это должно быть доказано тестом и runtime smoke.

---

# 25. Гарантия

Поддержать:

```text
Гарантия N дней
Без гарантии
```

Ручное значение для печати не должно менять товар или продажу.

---

# 26. Barcode rendering

Использовать локальную библиотеку:

```text
python-barcode
Pillow
SVG generation
reportlab
```

Предпочтительно SVG.

Запрещено использовать внешний интернет-сервис генерации.

---

# 27. Print buttons

На preview:

```text
Печать
Закрыть
```

```javascript
window.print()
```

```css
@media print {
  .no-print {
    display: none !important;
  }
}
```

---

# 28. Длинные названия

Проверить:

```text
название не выходит за 58×40
не перекрывает цену
не перекрывает barcode
контролируемо уменьшается или обрезается
```

---

# 29. Duplicate audit

Проверить существующие barcode.

Если есть дубли:

```text
не исправлять молча
сформировать blocker
```

Если дублей нет:

```text
создать unique index
```

---

# 30. Core tests

Создать:

```text
core/tests/test_product_barcodes.py
core/tests/test_product_search.py
```

Покрыть:

```text
single generate
uniqueness
existing barcode not overwritten
lookup
unknown barcode 404
bulk generate missing only
second bulk generates zero
search by barcode
search by sku
search by id
search by name
duplicate rejected
audit event created
```

---

# 31. Inventory tests

Создать:

```text
inventory-sales-module/tests/test_barcode_scanner_ui.py
inventory-sales-module/tests/test_price_tag_58x40.py
```

Покрыть:

```text
scanner field exists
autofocus exists
found product added
unknown barcode error
sold product blocked
quantity zero blocked
unique item not duplicated
price tag route 200
58mm × 40mm CSS
name/price/barcode/warranty visible
manual print price works
manual price does not change Core product
print button exists
close button exists
```

---

# 32. Regression

Обязательно проверить, что не сломаны:

```text
обычная продажа
отмена продажи
повторное оформление
отчёты
поиск товаров
```

---

# 33. Docker dependencies

Если добавлена библиотека — обновить:

```text
requirements.txt
Docker build
```

Не устанавливать только локально.

---

# 34. Docker rebuild

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose up -d avito-module
docker compose ps
```

---

# 35. Full regression

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Все должны пройти.

---

# 36. Runtime smoke — barcode

Проверить товар без barcode:

```text
до: barcode пустой
generate
после: barcode заполнен
повторный generate не меняет код
```

---

# 37. Runtime smoke — scanner

Проверить:

```text
существующий barcode
товар появился в корзине
поле очистилось
фокус вернулся
```

Неизвестный barcode:

```text
русская ошибка
без 500
```

Недоступный товар:

```text
не добавляется
понятная ошибка
```

---

# 38. Runtime smoke — price tag

Проверить:

```text
кнопка у конкретного товара
58×40 preview
название
цена
barcode
цифровой код
гарантия
Печать
Закрыть
```

Изменить цену в форме ценника.

Проверить через Core:

```text
Product.price не изменился
```

---

# 39. Print check

Проверить:

```text
@page 58mm 40mm
одна страница
нет обрезки
barcode читаем
кнопки не печатаются
```

---

# 40. Safety scans

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
```

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 41. Documentation/report

Создать:

```text
docs/stage04i_barcodes_scanner_price_tags.md
reports/stage04i_barcodes_scanner_price_tags_report.md
```

Обновить:

```text
logs/2026-07-22.md
```

Report:

```text
# Stage 04I Barcodes, Scanner Search and 58×40 Price Tags Report

## STATUS
## OWNER_REQUIREMENTS
## ARCHITECTURE
## BARCODE_FORMAT
## DATA_MODEL
## API
## SCANNER_FLOW
## CART_BEHAVIOR
## PRICE_TAG_58X40
## TESTS
## RUNTIME_SMOKE
## PRINT_CHECK
## SAFETY_SCAN
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_CHECK_GUIDE
## FINAL_STATUS
```

---

# 42. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/main.py
git add core/app/routers/products.py
git add core/app/services/barcodes.py
git add core/tests/test_product_barcodes.py
git add core/tests/test_product_search.py
git add core/requirements.txt

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/products_list.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/templates/sales_create.html
git add inventory-sales-module/app/templates/price_tag_58x40.html
git add inventory-sales-module/tests/test_barcode_scanner_ui.py
git add inventory-sales-module/tests/test_price_tag_58x40.py
git add inventory-sales-module/requirements.txt

git add docs/stage04i_barcodes_scanner_price_tags.md
git add reports/stage04i_barcodes_scanner_price_tags_report.md
git add logs/2026-07-22.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04I_BARCODES_SCANNER_PRICE_TAGS_PROMPT.md
```

Коммит:

```powershell
git commit -m "Implement product barcodes scanner flow and 58x40 price tags"
git push
```

После push:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -3
```

Финальный status должен быть пустым.

---

# 43. Definition of Done

```text
barcode field implemented
barcode uniqueness enforced
single generation works
bulk missing generation works
existing barcode not overwritten
lookup by barcode works
search by barcode/SKU/ID/name works
scanner adds product to cart
unknown barcode handled
unavailable product blocked
price tag button exists per product
price tag is 58×40 mm
manual print price works
Product.price unchanged
barcode visible and scannable
warranty visible
Core tests PASS
Inventory tests PASS
Avito tests PASS
runtime barcode smoke PASS
runtime scanner smoke PASS
runtime price tag smoke PASS
print check PASS
safety scans clean
targeted commit
push
final git status clean
owner manual check required
```

---

# 44. Финальный ответ агента

Обязательно указать:

```text
формат barcode
как гарантируется уникальность
сколько старых товаров получили barcode
как работает scanner flow
как работает ценник 58×40
как доказано, что ручная цена не меняет Product.price
результаты Core/Inventory/Avito tests
runtime smoke
commit hash
push result
final git status
```

Успешный статус:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_BARCODES_SCANNER_PRICE_TAGS_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

При проблеме:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_BARCODES_SCANNER_PRICE_TAGS_FAIL

BLOCKERS:
...
```
