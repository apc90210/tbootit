# PROMPT — Техноребут / Stage 04E-R2 Dynamic Product Filters Owner UX Repair

## Роль агента

Ты senior fullstack developer, UX-focused backend/frontend integrator и owner-check repair engineer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — выполнить owner UX repair после ручной проверки Stage04E: добавить верхнюю панель фильтров в список товаров `inventory-sales-module`.

Это repair/UX stage, а не переход к Stage04F.

---

# 1. Причина repair

Владелец проекта при проверке рабочего UI уточнил обязательное требование:

```text
Сверху нужны фильтры по типу товару, производителю, наличию, модели и т.д.
Фильтры должны быть в виде списка, который формируется на основе товаров в базе.
```

Это означает:

```text
Stage04E пока не owner-accepted.
Stage04F начинать нельзя.
Нужно доработать products list UI и Core API contract для динамических фильтров.
```

---

# 2. Главный статус

Текущий статус:

```text
STAGE04E_OWNER_RECHECK_NEEDS_DYNAMIC_PRODUCT_FILTERS
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04E_R2_DYNAMIC_PRODUCT_FILTERS_READY_FOR_OWNER_RECHECK
```

После repair нельзя автоматически идти в Stage04F.

Нужен gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_STAGE04F_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Архитектурное правило

`inventory-sales-module` не имеет права читать БД напрямую.

Правильно:

```text
inventory-sales-module → Core API → Core DB
```

Неправильно:

```text
inventory-sales-module → Core DB напрямую
```

Фильтры должны формироваться на основе товаров в базе, но получать данные нужно только через Core API.

---

# 4. Что нужно реализовать

На странице:

```text
http://127.0.0.1:8030/products
```

сверху должна появиться панель фильтров.

Фильтры должны быть списками/select, сформированными из реальных данных товаров.

Минимальный набор:

```text
Тип / категория товара
Производитель / бренд
Модель
Наличие / статус
Место хранения
Готовность к Авито
Готовность к сайту
```

Также оставить:

```text
строку поиска
сортировку
limit/offset pagination
кнопку "Сбросить фильтры"
```

---

# 5. Core API — динамические options/facets

Если в Core уже есть endpoint для filter options — использовать его.

Если нет — добавить endpoint в Core:

```text
GET /api/products/filter-options
```

Рекомендуемый response:

```json
{
  "categories": [
    {"id": 1, "name": "Ноутбуки", "count": 12}
  ],
  "brands": [
    {"value": "Lenovo", "count": 5}
  ],
  "models": [
    {"value": "ThinkPad T480", "count": 2}
  ],
  "statuses": [
    {"value": "in_stock", "label": "В наличии", "count": 7},
    {"value": "reserved", "label": "Резерв", "count": 1},
    {"value": "sold", "label": "Продан", "count": 10}
  ],
  "storage_locations": [
    {"value": "Склад", "count": 4}
  ],
  "availability": [
    {"value": "available", "label": "Можно продать", "count": 7},
    {"value": "not_available", "label": "Нельзя продать", "count": 11}
  ],
  "avito_ready": [
    {"value": "true", "label": "Готово к Авито", "count": 6},
    {"value": "false", "label": "Не готово к Авито", "count": 12}
  ],
  "site_ready": [
    {"value": "true", "label": "Готово к сайту", "count": 4},
    {"value": "false", "label": "Не готово к сайту", "count": 14}
  ]
}
```

Важно:

```text
empty/null values не должны ломать endpoint
дубликаты убрать
сортировка значений по алфавиту
counts желательны
```

---

# 6. Core products filtering

Проверить существующий:

```text
GET /api/products
```

Он должен принимать:

```text
q
status
category_id
brand
model
storage_location
avito_ready
site_ready
limit
offset
sort
```

Если какого-то фильтра нет, добавить только минимально нужный.

Нельзя ломать уже существующие query params.

---

# 7. inventory-sales-module CoreClient

Расширить:

```text
inventory-sales-module/app/core_client.py
```

Добавить метод:

```text
get_product_filter_options()
```

Он должен вызывать:

```text
GET /api/products/filter-options
```

В `get_products(params)` убедиться, что выбранные фильтры передаются в Core.

---

# 8. UI `/products`

В template:

```text
inventory-sales-module/app/templates/products.html
```

Добавить верхнюю панель:

```text
Фильтры
[Поиск]
[Тип товара]
[Производитель]
[Модель]
[Наличие/Статус]
[Место хранения]
[Авито]
[Сайт]
[Сортировка]
[Применить]
[Сбросить фильтры]
```

Все подписи — на русском.

Select options должны показывать count, если он есть:

```text
Lenovo (5)
ThinkPad T480 (2)
В наличии (7)
```

Выбранные значения должны сохраняться после применения фильтра.

Если Core filter-options недоступен:

```text
показать список товаров
и сверху русское предупреждение:
"Не удалось загрузить список фильтров. Поиск и таблица товаров доступны."
```

Не показывать generic:

```text
Ошибка Core API
```

если сами товары загрузились.

---

# 9. UX requirements

Фильтры должны быть сверху страницы, перед таблицей.

Сценарий владельца:

```text
1. Открываю /products.
2. Вижу сверху списки фильтров.
3. Выбираю производителя.
4. Нажимаю "Применить".
5. Таблица показывает товары этого производителя.
6. Выбираю модель.
7. Таблица сужается.
8. Нажимаю "Сбросить фильтры".
9. Вижу все товары.
```

---

# 10. Русский UI

Запрещены пользовательские английские подписи:

```text
Filter
Apply
Reset
Brand
Model
Status
Category
Available
```

Использовать:

```text
Фильтры
Применить
Сбросить фильтры
Тип товара
Производитель
Модель
Наличие
Статус
Место хранения
Готово к Авито
Готово к сайту
Все
```

---

# 11. Tests

Добавить/обновить tests.

Core tests:

```text
core/tests/test_product_filter_options.py
```

Покрыть:

```text
GET /api/products/filter-options returns 200
returns brands/models/statuses/categories
null/empty values ignored or handled
counts are numeric
```

Inventory module tests:

```text
inventory-sales-module/tests/test_product_filters_ui.py
inventory-sales-module/tests/test_core_client_filters.py
```

Покрыть:

```text
CoreClient calls /api/products/filter-options
/products renders filter panel
filters preserve selected values
filter options render counts
products route passes query params to CoreClient.get_products
if filter-options fails, products still render with warning if product list works
Russian labels present
no English UI labels
```

Запустить:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

---

# 12. Manual smoke

После реализации:

```powershell
docker compose up --build -d
docker compose ps
```

Проверить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/products/filter-options | ConvertTo-Json -Depth 10
Invoke-WebRequest http://127.0.0.1:8030/products | Select-Object StatusCode
```

Проверить HTML:

```text
Фильтры
Тип товара
Производитель
Модель
Наличие
Применить
Сбросить фильтры
```

Проверить фильтр по бренду:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/products?brand=Lenovo" | Select-Object StatusCode
```

Если Lenovo отсутствует в базе, взять любой brand из `/api/products/filter-options`.

---

# 13. Safety scans

Direct DB access:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Ожидание:

```text
нет прямого DB access
```

Browser automation:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

Runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

---

# 14. Documentation

Создать/обновить:

```text
docs/stage04e_r2_dynamic_product_filters.md
docs/inventory_sales_module_ui_map.md
docs/inventory_sales_module_core_api_contract.md
reports/stage04e_r2_dynamic_product_filters_report.md
logs/2026-07-02.md
```

Report structure:

```text
# Stage 04E-R2 Dynamic Product Filters Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REQUEST

## IMPLEMENTED

## CORE_API_CHANGES

## UI_CHANGES

## FILTER_OPTIONS

## TESTS

## MANUAL_SMOKE

## SAFETY_SCAN

## FILES_CHANGED

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R2_DYNAMIC_PRODUCT_FILTERS_READY_FOR_OWNER_RECHECK
```

---

# 15. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/routers/products.py
git add core/app/schemas.py
git add core/tests/test_product_filter_options.py
git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/static/app.css
git add inventory-sales-module/tests/test_product_filters_ui.py
git add inventory-sales-module/tests/test_core_client_filters.py
git add docs/stage04e_r2_dynamic_product_filters.md
git add docs/inventory_sales_module_ui_map.md
git add docs/inventory_sales_module_core_api_contract.md
git add reports/stage04e_r2_dynamic_product_filters_report.md
git add logs/2026-07-02.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R2_DYNAMIC_PRODUCT_FILTERS_PROMPT.md

git commit -m "Add dynamic product filters to sales UI"
git status --short --untracked-files=all
```

Strictly forbidden:

```text
git add .
git add -u
git commit --amend
```

If log needs update after commit:

```text
create a separate normal commit
```

---

# 16. Definition of Done

Готово, если:

```text
Core endpoint filter-options работает
/products сверху показывает фильтры
фильтры строятся по реальным данным Core
выбранные значения сохраняются
brand/model/status/category filters работают
reset filters работает
UI русский
нет generic Ошибка Core API на happy path
tests pass: core, inventory-sales-module, avito-module
direct DB access отсутствует
ценники не начаты
commit без amend
READY_FOR_OWNER_RECHECK
```

---

# 17. Главное правило

После Stage04E-R2 не переходить к Stage04F.

Финальный статус:

```text
TECHNOREBOOT_STAGE04E_R2_DYNAMIC_PRODUCT_FILTERS_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
NEXT_STEP: владелец проверяет фильтры в UI
```
