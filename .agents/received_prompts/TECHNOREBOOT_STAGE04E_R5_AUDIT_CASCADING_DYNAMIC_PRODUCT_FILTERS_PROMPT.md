# PROMPT — Техноребут / Stage 04E-R5-Audit Cascading Dynamic Product Filters

## Роль агента

Ты senior QA/audit engineer, fullstack reviewer, UX regression auditor и release-safety auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — провести аудит Stage 04E-R5:

```text
Cascading Dynamic Product Filters
```

Это аудит, а не новая разработка.

---

# 1. Почему нужен аудит

Stage04E-R5 implementation заявил успех, но в execution log есть caveats:

```text
1. Не видно запуска avito-module pytest, хотя prompt требовал core + inventory + avito.
2. Manual smoke по /products?category_id=1 завис/был принудительно остановлен через Stop-Process.
3. Финальный git status после commit не показан.
4. implementation_plan.md и task.md редактировались, могут быть untracked/dirty.
5. Нужно проверить, что каскад реально работает на реальных данных, а не только в тестах.
```

---

# 2. Заявленный результат Stage04E-R5

Заявлено:

```text
1. Core endpoint GET /api/products/filter-options доработан.
2. Реализован Approach A — dependent facets per level:
   category → brand → model → status → storage → avito/site.
3. Response содержит selected и order.
4. inventory-sales-module CoreClient передает query params.
5. /products router передает текущие GET params в Core.
6. products.html получил JS cascadeReset(level).
7. onchange у select очищает правые фильтры и отправляет форму.
8. Добавлены тесты:
   - core/tests/test_product_filter_options_cascading.py
   - inventory-sales-module/tests/test_core_client_cascading_filters.py
   - inventory-sales-module/tests/test_cascading_product_filters_ui.py
9. Созданы docs/report.
10. Commit:
   feat: Stage 04E-R5 Cascading dynamic product filters
```

---

# 3. Owner requirement to verify

Владелец требует:

```text
Фильтр товаров должен быть динамический.
Слева направо выбирается категория.
В следующем фильтре можно выбрать только значения на основании предыдущего выбора.
```

Проверить порядок:

```text
Категория / тип товара
→ Производитель / бренд
→ Модель
→ Статус / наличие
→ Место хранения
→ Авито
→ Сайт
```

Проверить поведение:

```text
1. После выбора категории бренды только из этой категории.
2. После выбора бренда модели только из категории + бренда.
3. После выбора модели статусы только из категории + бренда + модели.
4. Нельзя получить option, по которому будет 0 товаров.
5. При смене левого фильтра правые фильтры сбрасываются/пересчитываются.
6. Таблица товаров соответствует выбранным фильтрам.
```

---

# 4. Что запрещено в аудите

Запрещено:

```text
начинать следующий функциональный этап
переписывать фильтры заново без необходимости
делать прямой DB access из inventory-sales-module
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
коммитить runtime DB/temp files
```

Разрешено:

```text
создать audit report
дописать log
малый bugfix, если без него smoke не проходит
малый test/doc fix
```

Если найден blocker — статус `FAIL` и рекомендовать Stage04E-R5-R repair.

---

# 5. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04E_R5_AUDIT_CASCADING_DYNAMIC_PRODUCT_FILTERS_PROMPT.md
```

Искать:

```text
C:\tbootit
C:\tbootit\.agents
C:\tbootit\docs
C:\tbootit\docs\obsidian
C:\tbootit\prompts
C:\tbootit\logs\prompts
C:\Users\Apc\Downloads
```

Если prompt найден в Downloads — скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В отчете указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 6. Git/process audit

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -20
git show --name-status --oneline --stat HEAD
git diff --name-status
git diff --stat
```

Проверить:

```text
1. Нет ли dirty/untracked implementation_plan.md, task.md.
2. Нет ли dirty logs после commit.
3. Нет ли runtime DB/temp/cache tracked.
4. Commit содержит только expected R5 files.
```

Expected R5 files:

```text
core/app/routers/products.py
core/tests/test_product_filter_options_cascading.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/products.py
inventory-sales-module/app/templates/products.html
inventory-sales-module/tests/test_core_client_cascading_filters.py
inventory-sales-module/tests/test_cascading_product_filters_ui.py
docs/stage04e_r5_cascading_dynamic_product_filters.md
reports/stage04e_r5_cascading_dynamic_product_filters_report.md
logs/<date>.md
.agents/received_prompts/TECHNOREBOOT_STAGE04E_R5_CASCADING_DYNAMIC_PRODUCT_FILTERS_PROMPT.md
```

Danger scan:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py|task\.md|implementation_plan\.md"
```

---

# 7. Docker rebuild and full regression

Выполнить:

```powershell
docker compose down
docker compose up --build -d
docker compose ps
```

Затем обязательно:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Ожидание:

```text
all pass
```

Если avito tests не проходят — audit не PASS.

---

# 8. Core filter-options audit

Проверить API:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options" | ConvertTo-Json -Depth 10
```

Найти реальные значения.

Если в базе есть категории:

```powershell
$options = Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options"
$options.categories
```

Проверить cascade:

```powershell
# выбрать category_id из options
Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options?category_id=<id>" | ConvertTo-Json -Depth 10

# выбрать brand из результата
Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options?category_id=<id>&brand=<brand>" | ConvertTo-Json -Depth 10

# выбрать model из результата
Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options?category_id=<id>&brand=<brand>&model=<model>" | ConvertTo-Json -Depth 10
```

Проверить:

```text
selected заполнен
order есть
counts > 0
нет options с count=0
brand options реально сужаются после category
model options реально сужаются после category+brand
```

Если данных мало и сужение не видно, создать/импортировать безопасные тестовые товары с разными категориями/брендами/моделями через Core API, но не коммитить runtime DB.

---

# 9. Products list matching audit

Проверить, что products list фильтруется теми же params:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products/?category_id=<id>&brand=<brand>&model=<model>" | ConvertTo-Json -Depth 10
```

Ожидание:

```text
все returned items соответствуют выбранным category/brand/model
```

---

# 10. Inventory UI smoke — no hang

Особо проверить, что URL, который зависал, теперь работает:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/products?category_id=1" -TimeoutSec 15 | Select-Object StatusCode
```

Проверить общий UI:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/products" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?brand=Lenovo" -TimeoutSec 15 | Select-Object StatusCode
```

Если зависает — blocker.

---

# 11. Inventory UI cascade audit

Открыть в браузере или проверить HTML:

```text
http://127.0.0.1:8030/products
```

Проверить:

```text
1. Фильтры слева направо.
2. Русские labels.
3. onchange="cascadeReset(...)" есть у select.
4. JS сбрасывает правые фильтры.
5. "Сбросить фильтры" очищает query params.
6. selected values сохраняются.
7. Нет "Ценники — скоро".
```

HTML grep:

```powershell
Select-String -Path inventory-sales-module\app\templates\products.html -Pattern "cascadeReset|onchange|Категория|Производитель|Модель|Наличие|Сбросить фильтры"
```

---

# 12. Manual browser scenario

Проверить вручную:

```text
1. Открыть /products.
2. Выбрать категорию.
3. Убедиться, что страница перезагрузилась/обновилась.
4. Проверить, что производитель справа стал только по категории.
5. Выбрать производителя.
6. Проверить, что модель стала только по категории + производителю.
7. Выбрать модель.
8. Проверить, что статус/наличие соответствует выбору.
9. Проверить таблицу товаров.
10. Изменить категорию.
11. Проверить, что brand/model/status справа сброшены или пересчитаны.
12. Нажать "Сбросить фильтры".
13. Проверить полный список.
```

---

# 13. Safety scans

Direct DB access in inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Runtime tracked files:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

Browser/captcha automation:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

---

# 14. Audit report

Создать:

```text
reports/stage04e_r5_audit_cascading_dynamic_product_filters_report.md
```

Структура:

```text
# Stage 04E-R5 Audit Cascading Dynamic Product Filters Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## EXECUTIVE_SUMMARY

## PROMPT_DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## GIT_PROCESS_AUDIT

Branch:
Head:
Worktree before:
Worktree after:
Unexpected files:
Runtime tracked scan:

## TESTS

Core:
Inventory:
Avito:

## CORE_FILTER_OPTIONS_AUDIT

No params:
category params:
category+brand params:
category+brand+model params:
counts:
zero-count options:

## PRODUCTS_LIST_MATCHING_AUDIT

## UI_NO_HANG_AUDIT

/products:
products?category_id=1:
products?brand=...:

## UI_CASCADE_AUDIT

Order:
Selected persistence:
Right-side reset:
Reset filters:

## SAFETY_SCAN

## BLOCKERS

## NON_BLOCKING_ISSUES

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

If PASS:

TECHNOREBOOT_STAGE04E_R5_AUDIT_READY_FOR_OWNER_MANUAL_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 15. Git

Use targeted add only:

```powershell
git add reports/stage04e_r5_audit_cascading_dynamic_product_filters_report.md
git add logs/2026-07-02.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R5_AUDIT_CASCADING_DYNAMIC_PRODUCT_FILTERS_PROMPT.md
git commit -m "Audit Stage 04E R5 cascading dynamic product filters"
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

# 16. Definition of Done

Audit готов, если:

```text
final git status checked
no runtime/temp tracked
core pytest pass
inventory pytest pass
avito pytest pass
/products?category_id=1 does not hang
filter-options cascade verified on real data
products list matches filters
UI cascade/order/reset verified
Russian labels verified
no direct DB access in inventory-sales-module
audit report committed
READY_FOR_OWNER_MANUAL_CHECK
```

---

# 17. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R5_AUDIT_READY_FOR_OWNER_MANUAL_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```
