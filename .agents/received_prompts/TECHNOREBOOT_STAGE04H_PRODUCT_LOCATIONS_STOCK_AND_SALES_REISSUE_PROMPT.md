# PROMPT — Техноребут / Stage 04H Product Locations, Stock Quantity Editing, and Sales Reissue Workflow

## Роль агента

Ты senior fullstack developer, FastAPI backend engineer, inventory/accounting workflow architect, Jinja2 UI developer и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — реализовать следующий функциональный этап после Stage04G-S: фильтры местонахождения товара, редактирование местонахождения/количества товара и безопасный workflow отмены/переоформления продажи с корректным пересчётом отчётов.

---

# 1. Owner requirement

Владелец сообщил:

```text
в разделе товары сверху большие кнопки фильтры места нахождения товара
магазин мастерская архив черновик.

при нажатии открыть можно менять местоположение товара и количество.

так же нужно сделать редактирование (переооформление продажи,
то есть отменять полностью, менять состав товаров
и сразу все сменяется во всех отчетах)
```

Интерпретация:

```text
1. На странице товаров нужны крупные быстрые кнопки-фильтры:
   - Магазин
   - Мастерская
   - Архив
   - Черновик

2. При открытии карточки товара нужно иметь возможность:
   - изменить местонахождение товара;
   - изменить количество товара.

3. Продажи нужно уметь:
   - полностью отменять;
   - переоформлять;
   - менять состав товаров;
   - корректно возвращать/списывать остатки;
   - сразу пересчитывать отчёты.

4. Отчёты Stage04G должны учитывать только актуальные продажи.
   Отменённые продажи не должны попадать в выручку.
```

---

# 2. Важное архитектурное решение

Продажи нельзя редактировать бесследно, потому что это ломает историю, остатки, товарные чеки и отчёты.

Правильный MVP workflow:

## Полная отмена продажи

```text
sale.status = canceled
sale.canceled_at = now
sale.cancel_reason = user input / optional
товары из продажи возвращаются на остаток
отчёты исключают canceled sale
товарный чек остается доступен как исторический, но помечен "Продажа отменена"
```

## Переоформление продажи

В MVP сделать безопасно:

```text
1. Открыть продажу.
2. Нажать "Переоформить".
3. Система создаёт форму новой продажи на основе старой.
4. Пользователь меняет состав товаров/количество/цены/способ оплаты.
5. При подтверждении:
   - старая продажа получает status = superseded или canceled;
   - товары старой продажи возвращаются на остаток;
   - новая продажа создаётся со status = completed;
   - товары новой продажи списываются;
   - связь сохраняется:
     old_sale.replaced_by_sale_id = new_sale.id
     new_sale.original_sale_id = old_sale.id
6. Отчёты учитывают только новую completed sale.
```

Если проще для MVP:

```text
Переоформление = отменить старую продажу + создать новую вручную из корзины.
```

Но в UI должно быть понятно и удобно.

---

# 3. Target status

Новый этап:

```text
TECHNOREBOOT_STAGE04H_PRODUCT_LOCATIONS_STOCK_AND_SALES_REISSUE
```

Целевой финальный статус:

```text
TECHNOREBOOT_STAGE04H_PRODUCT_LOCATIONS_STOCK_AND_SALES_REISSUE_READY_FOR_OWNER_CHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 4. Strict architecture rules

Система строго модульная.

Core:

```text
Core owns DB and business state.
Core owns product/sale/stock/report logic.
Core exposes HTTP API.
```

Inventory-sales-module:

```text
No direct DB access.
Only calls Core over HTTP.
```

Запрещено:

```text
direct DB access from inventory-sales-module
отдельная DB для остатков/отчетов
ручное чтение core DB из UI module
git add .
git add -A
git add -u
git commit --amend
git reset / git clean / rebase / force push
runtime DB/temp/cache in git
Base.metadata.drop_all/create_all
бесследно переписывать completed sale без audit/history/status
```

Разрешено:

```text
Core API endpoints for product location/quantity updates
Core API endpoints for sale cancel/reissue
Core model/schema extension if needed
safe startup column ensure if project style already uses it
Inventory UI pages calling Core API
tests
docs/report/log
targeted commit
normal push
```

---

# 5. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04H_PRODUCT_LOCATIONS_STOCK_AND_SALES_REISSUE_PROMPT.md
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

# 6. Preflight

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Если worktree dirty — STOP и разобраться.

---

# 7. Product location requirements

## Locations

Добавить/использовать поле product location/location_status.

Допустимые значения:

```text
store = Магазин
workshop = Мастерская
archive = Архив
draft = Черновик
```

Если уже есть похожие поля:

```text
location
status
product_status
inventory_status
storage_location
```

не дублировать без необходимости. Лучше аккуратно расширить существующую модель.

## Default

Для существующих товаров без location:

```text
default = store
```

или если товар `draft`, то `draft`.

В UI пустое значение не показывать.

## Product list filters

На странице:

```text
/products
```

сверху добавить большие кнопки-фильтры:

```text
[Магазин] [Мастерская] [Архив] [Черновик] [Все]
```

Требования:

```text
1. Кнопки крупные, заметные.
2. Активный фильтр подсвечен.
3. При нажатии фильтр применяется.
4. Фильтр работает вместе с существующими фильтрами category/brand/model.
5. URL query должен быть понятный:
   /products?location=store
   /products?location=workshop
   /products?location=archive
   /products?location=draft
```

---

# 8. Product edit requirements

В карточке товара / product detail добавить блок:

```text
Местонахождение и остаток
```

Поля:

```text
Местонахождение:
- Магазин
- Мастерская
- Архив
- Черновик

Количество:
- number input
```

Действия:

```text
Сохранить изменения
```

Поведение:

```text
1. Можно менять location.
2. Можно менять quantity.
3. Quantity не может быть отрицательным.
4. Изменение quantity должно фиксироваться в Core.
5. В списке товаров сразу видны актуальные location и quantity.
```

Если товар является уникальной единицей и сейчас модель не поддерживает quantity:

```text
добавить quantity integer default 1
```

Если уже есть quantity/stock fields:

```text
использовать существующее поле.
```

---

# 9. Core API — products

Добавить/расширить endpoints:

```text
GET /api/products/?location=store
GET /api/products/filter-options
PATCH /api/products/{product_id}
```

Если PATCH уже есть — расширить.

Payload:

```json
{
  "location": "store",
  "quantity": 3
}
```

Response должен вернуть обновлённый product.

Validation:

```text
location must be one of store/workshop/archive/draft
quantity >= 0
```

---

# 10. Sales cancel requirements

В продаже добавить status.

Допустимые статусы:

```text
completed = Завершена
canceled = Отменена
superseded = Переоформлена / заменена
```

Если sale status уже есть — использовать/расширить.

Core endpoint:

```text
POST /api/sales/{sale_id}/cancel
```

Payload:

```json
{
  "reason": "ошибка продажи"
}
```

Behavior:

```text
1. Если sale already canceled/superseded — вернуть понятную ошибку 400.
2. Вернуть товары из продажи на остаток.
3. Установить status=canceled.
4. Записать canceled_at, cancel_reason.
5. Reports exclude canceled sale.
6. Product statuses/quantities обновляются сразу.
```

---

# 11. Sales reissue requirements

Core endpoint:

```text
POST /api/sales/{sale_id}/reissue
```

Payload:

```json
{
  "reason": "изменение состава товаров",
  "payment_method": "cash",
  "warranty_enabled": true,
  "warranty_days": 30,
  "items": [
    {
      "product_id": 1,
      "quantity": 1,
      "unit_price": 1000
    }
  ]
}
```

Behavior:

```text
1. Проверить, что old sale status=completed.
2. Проверить наличие товаров/quantity для новой продажи.
3. В одной транзакционной операции:
   - вернуть товары old sale на остаток;
   - old sale status=superseded;
   - создать new sale status=completed;
   - списать товары new sale;
   - связать old_sale.replaced_by_sale_id = new_sale.id;
   - связать new_sale.original_sale_id = old_sale.id.
4. Reports exclude old superseded sale.
5. Reports include new completed sale.
6. Receipt for old sale displays status "Переоформлена".
7. Receipt for new sale works normally.
```

Если транзакционность в текущей архитектуре сложна:

```text
реализовать максимально атомарно внутри Core request с DB session commit only at the end.
```

---

# 12. Reports integration

Stage04G reports must change:

```text
1. Include only sale.status == completed.
2. Exclude canceled.
3. Exclude superseded.
4. If old rows have null status, treat as completed for backward compatibility.
```

Money summary rows must update immediately after:

```text
sale cancel
sale reissue
```

---

# 13. Inventory-sales-module UI — sale actions

На странице продажи:

```text
/sales/{sale_id}
```

или где сейчас sale detail exists, добавить действия:

```text
Отменить продажу
Переоформить продажу
```

## Cancel UI

Flow:

```text
1. Нажать "Отменить продажу".
2. Показать предупреждение:
   "Продажа будет отменена, товары вернутся на остаток, отчёты пересчитаются."
3. Поле причина.
4. Подтвердить.
5. После успеха показать продажу со статусом "Отменена".
```

## Reissue UI

Flow MVP:

```text
1. Нажать "Переоформить".
2. Открывается форма с текущими товарами продажи.
3. Можно удалить товар.
4. Можно изменить quantity.
5. Можно изменить цену.
6. Можно добавить другой товар из доступных товаров.
7. Можно изменить payment_method.
8. Подтвердить переоформление.
9. Старая продажа становится "Переоформлена".
10. Новая продажа открывается.
```

Если добавить выбор нового товара в одну стадию сложно:

```text
MVP допустимо:
- форма показывает текущие товары;
- позволяет менять quantity/price/remove;
- добавление товаров через existing cart flow with replacement marker.
```

Но в отчёте и остатках всё должно быть корректно.

---

# 14. Product quantity and sale stock rules

Rules:

```text
1. Продажа списывает quantity.
2. Отмена возвращает quantity.
3. Переоформление возвращает старую quantity и списывает новую quantity.
4. Нельзя продать больше, чем quantity в наличии.
5. Нельзя сделать quantity отрицательным.
6. Archive/draft товары не должны случайно продаваться, если это уже логично в текущей системе.
```

Для MVP:

```text
Продавать только товары location=store, quantity > 0.
```

Если это ломает существующий поток, хотя бы предупреждать и тестами зафиксировать.

---

# 15. Backward compatibility

Для старых товаров:

```text
location missing -> store
quantity missing -> 1
```

Для старых продаж:

```text
status missing/null -> completed
payment_method missing/null -> unspecified in reports
```

Нельзя ломать старые продажи/отчёты.

---

# 16. Tests — Core

Добавить/обновить:

```text
core/tests/test_product_locations_and_quantity.py
core/tests/test_sales_cancel_reissue.py
core/tests/test_sales_reports.py
```

Cover:

## Product location/quantity

```text
1. Product can be filtered by location=store/workshop/archive/draft.
2. Product with missing location returns default store.
3. Product quantity can be updated.
4. Negative quantity rejected.
5. Invalid location rejected.
6. filter-options include locations if applicable.
```

## Sale cancel

```text
1. Cancel completed sale succeeds.
2. Cancel returns product quantities.
3. Canceled sale excluded from reports total.
4. Cancel already canceled sale rejected.
5. Receipt/detail shows status canceled.
```

## Sale reissue

```text
1. Reissue completed sale creates new sale.
2. Old sale status becomes superseded.
3. Old sale linked to new sale.
4. New sale linked to original sale.
5. Old quantities returned, new quantities deducted.
6. Reports exclude superseded old sale.
7. Reports include new sale.
8. Reissue with insufficient stock rejected.
9. Reissue canceled sale rejected.
```

---

# 17. Tests — Inventory-sales-module

Добавить/обновить:

```text
inventory-sales-module/tests/test_product_location_filters_ui.py
inventory-sales-module/tests/test_product_location_quantity_edit_ui.py
inventory-sales-module/tests/test_sales_cancel_reissue_ui.py
inventory-sales-module/tests/test_sales_reports_ui.py
```

Cover:

```text
1. /products shows big buttons: Магазин, Мастерская, Архив, Черновик, Все.
2. /products?location=store calls Core with location=store.
3. Active location filter highlighted.
4. Product detail shows location dropdown and quantity input.
5. Saving product detail sends PATCH to Core.
6. Sale detail shows cancel and reissue buttons.
7. Cancel form posts to Core cancel endpoint.
8. Reissue form posts to Core reissue endpoint.
9. Reports UI still opens and uses only completed sales returned by Core.
```

---

# 18. Manual smoke

After implementation:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose ps
```

## Product filters

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/products" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?location=store" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?location=workshop" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?location=archive" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?location=draft" -TimeoutSec 15 | Select-Object StatusCode
```

HTML check:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/products" -TimeoutSec 15
$page.Content | Select-String "Магазин"
$page.Content | Select-String "Мастерская"
$page.Content | Select-String "Архив"
$page.Content | Select-String "Черновик"
```

## Product edit

Manual browser:

```text
/products
Открыть товар
изменить местонахождение
изменить количество
сохранить
вернуться в список
проверить фильтры
```

## Sale cancel/reissue

Manual browser:

```text
1. Создать продажу.
2. Открыть отчёт сегодня и запомнить сумму.
3. Отменить продажу.
4. Проверить:
   - продажа помечена "Отменена";
   - товар вернулся на остаток;
   - сумма отчёта уменьшилась.
5. Создать продажу.
6. Переоформить продажу.
7. Проверить:
   - старая продажа "Переоформлена";
   - новая продажа создана;
   - отчёт считает новую, но не старую.
```

---

# 19. Full regression

Run:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

All must pass.

---

# 20. Safety scans

Runtime tracked:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

Direct DB access in inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Destructive DB calls:

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
```

Secrets:

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 21. Docs/report/log

Create:

```text
reports/stage04h_product_locations_stock_sales_reissue_report.md
docs/stage04h_product_locations_stock_sales_reissue.md
```

Update:

```text
logs/2026-07-10.md
```

Report structure:

```text
# Stage 04H Product Locations, Stock Quantity Editing, and Sales Reissue Report

## STATUS

READY_FOR_OWNER_CHECK / FAIL

## OWNER_REQUIREMENT

## IMPLEMENTED

### Product location filters

### Product location/quantity editing

### Sale cancel workflow

### Sale reissue workflow

### Reports integration

## DATA_MODEL

Product fields:
Sale fields:
Compatibility defaults:

## API

Product endpoints:
Sale cancel:
Sale reissue:
Reports changes:

## UI

Products:
Product detail:
Sale detail:
Reports:

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

Product filters:
Product edit:
Sale cancel:
Sale reissue:
Reports recalculation:

## SAFETY_SCAN

Runtime tracked:
Direct DB access:
Destructive DB calls:
Secrets:

## FILES_CHANGED

## COMMIT

## PUSH

## OWNER_CHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04H_PRODUCT_LOCATIONS_STOCK_AND_SALES_REISSUE_READY_FOR_OWNER_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 22. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/main.py
git add core/app/routers/products.py
git add core/app/routers/sales.py
git add core/app/routers/reports.py
git add core/tests/test_product_locations_and_quantity.py
git add core/tests/test_sales_cancel_reissue.py
git add core/tests/test_sales_reports.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/templates/sales_detail.html
git add inventory-sales-module/app/templates/sales_reissue.html
git add inventory-sales-module/app/templates/reports_sales.html
git add inventory-sales-module/tests/test_product_location_filters_ui.py
git add inventory-sales-module/tests/test_product_location_quantity_edit_ui.py
git add inventory-sales-module/tests/test_sales_cancel_reissue_ui.py
git add inventory-sales-module/tests/test_sales_reports_ui.py

git add docs/stage04h_product_locations_stock_sales_reissue.md
git add reports/stage04h_product_locations_stock_sales_reissue_report.md
git add logs/2026-07-10.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04H_PRODUCT_LOCATIONS_STOCK_AND_SALES_REISSUE_PROMPT.md

git commit -m "Implement Stage 04H product locations stock and sales reissue"
git status --short --untracked-files=all
```

Forbidden:

```text
git add .
git add -A
git add -u
git commit --amend
```

If remote exists:

```powershell
git push
```

No force push.

---

# 23. Definition of Done

Готово, если:

```text
/products has big location filter buttons
location filters work with existing filters
product detail can update location
product detail can update quantity
negative quantity rejected
sale can be canceled
cancel returns stock
canceled sale excluded from reports
sale can be reissued
reissue returns old stock and deducts new stock
old sale excluded from reports
new sale included in reports
reports update immediately
core/inventory/avito tests pass
safety scans clean
targeted commit
push
READY_FOR_OWNER_CHECK
```

---

# 24. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04H_PRODUCT_LOCATIONS_STOCK_AND_SALES_REISSUE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04H_PRODUCT_LOCATIONS_STOCK_AND_SALES_REISSUE_FAIL

BLOCKERS:
...
```
