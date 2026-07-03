# PROMPT — Техноребут / Stage 04E-R5 Cascading Dynamic Product Filters

## Роль агента

Ты senior fullstack developer, UX engineer, FastAPI/Jinja2 developer и data-filtering architect проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — доработать фильтры товаров в `inventory-sales-module`: сделать их каскадными и динамическими слева направо.

Это owner UX repair внутри Stage04E/R4, не новый функциональный этап и не Stage04F.

---

# 1. Причина этапа

Владелец уточнил требование:

```text
Нужно, что бы фильтр товаров был динамический,
что бы слева направо я выбирал категорию,
а в левом фильтре можно было выбрать только на основании предыдущего выбора
```

Интерпретация:

```text
Фильтры не должны быть независимыми списками.
Фильтры должны быть каскадными:
1. выбираю категорию;
2. производитель показывает только производителей внутри выбранной категории;
3. модель показывает только модели выбранной категории + производителя;
4. статус/наличие показывает только статусы по уже выбранному набору;
5. место хранения/Авито/Сайт тоже пересчитываются по предыдущим фильтрам.
```

Текущий статус:

```text
STAGE04E_R4_OWNER_CHECK_NEEDS_CASCADING_DYNAMIC_FILTERS
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04E_R5_CASCADING_DYNAMIC_PRODUCT_FILTERS_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 2. Архитектурное правило

`inventory-sales-module` не имеет права читать БД напрямую.

Правильно:

```text
inventory-sales-module → Core API → Core DB
```

Неправильно:

```text
inventory-sales-module → Core DB напрямую
```

Фильтры должны строиться из данных Core.

---

# 3. Что должно быть в UI

На странице:

```text
http://127.0.0.1:8030/products
```

Фильтры должны располагаться слева направо в логическом порядке:

```text
Категория / Тип товара
→ Производитель / Бренд
→ Модель
→ Статус / Наличие
→ Место хранения
→ Авито
→ Сайт
→ Сортировка
```

Поведение:

```text
1. До выбора категории все фильтры могут показывать все доступные значения или быть disabled, кроме категории.
2. После выбора категории список производителей пересчитывается только по товарам выбранной категории.
3. После выбора производителя список моделей пересчитывается только по выбранной категории + производителю.
4. После выбора модели статусы/наличие пересчитываются по выбранной категории + производителю + модели.
5. Каждый следующий фильтр показывает только реально доступные значения.
6. Если предыдущий выбор меняется, все фильтры справа должны сбрасываться или пересчитываться.
7. Таблица товаров должна соответствовать текущему набору фильтров.
8. Кнопка "Сбросить фильтры" очищает все фильтры.
```

Важно:

```text
Фильтр не должен предлагать варианты, по которым будет 0 товаров.
```

---

# 4. Core API filter-options must accept current filters

Нужно доработать endpoint:

```text
GET /api/products/filter-options
```

Он должен принимать текущие query params:

```text
category_id
category
brand
model
status
storage_location
avito_ready
site_ready
q
```

И возвращать options, пересчитанные на основании уже выбранных фильтров.

Пример:

```text
GET /api/products/filter-options?category_id=2
```

возвращает:

```text
brands только по category_id=2
models только по category_id=2
statuses только по category_id=2
```

Пример:

```text
GET /api/products/filter-options?category_id=2&brand=Lenovo
```

возвращает:

```text
models только по category_id=2 + brand=Lenovo
statuses только по category_id=2 + brand=Lenovo
```

---

# 5. Важный UX нюанс: не терять выбранное значение

Если выбрано:

```text
category_id=2
brand=Lenovo
```

то в response filter-options выбранный brand должен остаться доступным, даже если расчёт следующего уровня идет с учетом brand.

Допустимые подходы:

## Подход A — dependent facets per level

Для каждого фильтра считать options с учетом всех фильтров слева, но без учета самого текущего фильтра и фильтров справа.

Пример порядка:

```text
category options: считаются без category/brand/model/status
brand options: считаются с category
model options: считаются с category + brand
status options: считаются с category + brand + model
storage options: считаются с category + brand + model + status
```

Это предпочтительный вариант.

## Подход B — simple full-current facets

Все options считаются по текущему набору фильтров. Это проще, но может скрыть выбранные значения. Если выбрать этот подход, нужно явно не ломать выбранный option.

Рекомендуется Approach A.

---

# 6. Response shape

Расширить response, чтобы UI понимал порядок и selected values.

Пример:

```json
{
  "selected": {
    "category_id": 2,
    "brand": "Lenovo",
    "model": "ThinkPad T480",
    "status": "in_stock"
  },
  "order": [
    "categories",
    "brands",
    "models",
    "statuses",
    "storage_locations",
    "avito_ready",
    "site_ready"
  ],
  "categories": [
    {"id": 2, "name": "Ноутбуки", "count": 12}
  ],
  "brands": [
    {"value": "Lenovo", "count": 5}
  ],
  "models": [
    {"value": "ThinkPad T480", "count": 2}
  ],
  "statuses": [
    {"value": "in_stock", "label": "В наличии", "count": 2}
  ],
  "storage_locations": [],
  "avito_ready": [],
  "site_ready": []
}
```

Можно не добавлять `selected/order`, если это ломает совместимость, но лучше добавить без удаления старых полей.

---

# 7. Products list filtering

Убедиться, что:

```text
GET /api/products/
```

и UI `/products` принимают одинаковые query params:

```text
q
category_id
brand
model
status
storage_location
avito_ready
site_ready
sort
limit
offset
```

Если filter-options предлагает значение, products list должен уметь по нему фильтровать.

---

# 8. inventory-sales-module behavior

В `inventory-sales-module`:

```text
/products
```

должен:

```text
1. Получить query params текущих фильтров.
2. Запросить Core products с этими params.
3. Запросить Core filter-options с этими же params.
4. Отрисовать фильтры в порядке слева направо.
5. Для каждого select сохранить выбранное значение.
6. При изменении раннего select сбрасывать правые select.
```

Рекомендуется реализовать простым способом без сложного JS:

```text
каждый select onchange отправляет форму GET
```

Но чтобы сбрасывались правые фильтры, можно добавить небольшой JS:

```text
если изменили category — очистить brand/model/status/storage/avito/site
если изменили brand — очистить model/status/storage/avito/site
если изменили model — очистить status/storage/avito/site
если изменили status — очистить storage/avito/site
```

JS должен быть простым и локальным.

---

# 9. UI labels

Все подписи на русском:

```text
Фильтры
Категория
Тип товара
Производитель
Модель
Наличие
Статус
Место хранения
Готово к Авито
Готово к сайту
Применить
Сбросить фильтры
Все категории
Все производители
Все модели
Все статусы
```

Запрещены пользовательские английские:

```text
Filter
Category
Brand
Model
Status
Apply
Reset
```

Технические class/id имена могут быть английскими.

---

# 10. Tests — Core

Добавить/обновить:

```text
core/tests/test_product_filter_options_cascading.py
```

Покрыть:

```text
1. Без фильтров возвращает все категории/бренды/модели.
2. С category_id возвращает только бренды этой категории.
3. С category_id+brand возвращает только модели этой категории и бренда.
4. С category_id+brand+model возвращает только статусы по выбранному набору.
5. Не возвращает options с count=0.
6. Counts корректны.
7. GET /api/products/ фильтрует по тем же params.
8. Backward compatibility: старый /api/products/filter-options без params работает.
```

---

# 11. Tests — inventory-sales-module

Добавить/обновить:

```text
inventory-sales-module/tests/test_cascading_product_filters_ui.py
inventory-sales-module/tests/test_core_client_cascading_filters.py
```

Покрыть:

```text
1. /products передает query params в get_product_filter_options.
2. /products передает query params в get_products.
3. Фильтры отрисованы слева направо.
4. Выбранные значения сохраняются.
5. Options показывают count.
6. Есть JS/reset правых фильтров при смене левого.
7. "Сбросить фильтры" очищает query params.
8. Если filter-options недоступен, таблица товаров всё равно открывается.
9. Русские подписи.
10. Нет отдельного "Ценники — скоро".
```

---

# 12. Regression tests

Запустить:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

---

# 13. Manual smoke

После реализации:

```powershell
docker compose up --build -d
docker compose ps
```

Проверить:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options?brand=Lenovo" | ConvertTo-Json -Depth 10
Invoke-WebRequest "http://127.0.0.1:8030/products" | Select-Object StatusCode
```

Ручной сценарий:

```text
1. Открыть /products.
2. Выбрать категорию.
3. Проверить, что производители справа стали только по этой категории.
4. Выбрать производителя.
5. Проверить, что модели стали только по категории + производителю.
6. Выбрать модель.
7. Проверить, что статусы/наличие соответствуют выбору.
8. Нажать "Применить".
9. Проверить таблицу.
10. Изменить категорию.
11. Проверить, что производитель/модель/status справа сбросились или пересчитались.
12. Нажать "Сбросить фильтры".
13. Проверить, что список вернулся к общему.
```

---

# 14. Safety scans

Direct DB access in inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Runtime files tracked:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

Browser/captcha automation:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

---

# 15. Documentation/report

Создать/обновить:

```text
docs/stage04e_r5_cascading_dynamic_product_filters.md
docs/inventory_sales_module_ui_map.md
docs/inventory_sales_module_core_api_contract.md
reports/stage04e_r5_cascading_dynamic_product_filters_report.md
logs/2026-07-02.md
```

Report structure:

```text
# Stage 04E-R5 Cascading Dynamic Product Filters Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REQUEST

## IMPLEMENTED

## CASCADING_ORDER

## CORE_API_CHANGES

## UI_CHANGES

## QUERY_PARAMS

## TESTS

## MANUAL_SMOKE

## SAFETY_SCAN

## FILES_CHANGED

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R5_CASCADING_DYNAMIC_PRODUCT_FILTERS_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
```

---

# 16. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/routers/products.py
git add core/app/schemas.py
git add core/tests/test_product_filter_options_cascading.py
git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/static/app.js
git add inventory-sales-module/app/static/app.css
git add inventory-sales-module/tests/test_cascading_product_filters_ui.py
git add inventory-sales-module/tests/test_core_client_cascading_filters.py
git add docs/stage04e_r5_cascading_dynamic_product_filters.md
git add docs/inventory_sales_module_ui_map.md
git add docs/inventory_sales_module_core_api_contract.md
git add reports/stage04e_r5_cascading_dynamic_product_filters_report.md
git add logs/2026-07-02.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R5_CASCADING_DYNAMIC_PRODUCT_FILTERS_PROMPT.md

git commit -m "Add cascading dynamic product filters"
git status --short --untracked-files=all
```

Forbidden:

```text
git add .
git add -A
git add -u
git commit --amend
```

---

# 17. Definition of Done

Готово, если:

```text
filter-options accepts current filter params
options are recalculated based on previous selections
category → brand → model → status cascade works
next filters do not show impossible values
right-side filters reset/recalculate when left filter changes
/products table matches selected filters
selected values persist
reset filters works
UI labels are Russian
tests pass: core, inventory-sales-module, avito-module
no direct DB access in inventory-sales-module
no runtime DB/temp tracked
normal commit created without add -A/amend
READY_FOR_OWNER_RECHECK
```

---

# 18. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R5_CASCADING_DYNAMIC_PRODUCT_FILTERS_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```
