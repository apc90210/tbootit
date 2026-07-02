# PROMPT — Техноребут / Stage 04E-R4-Audit Sales Cart Receipt Price Tag Requirements

## Роль агента

Ты senior QA/audit engineer, release auditor, fullstack reviewer, test coverage auditor и process-safety auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — провести независимый аудит Stage 04E-R4:

```text
Sales Cart, Receipt, Price Tag Requirements & R3 Recovery
```

Это аудит, а не новая разработка.

---

# 1. Почему нужен аудит

Агент заявил, что Stage04E-R4 выполнен:

```text
корзина продаж
товарно-гарантийный чек
ценник 58×40 мм
реквизиты организации
таблица продаж
тесты проходят
commit создан
```

Но в execution log есть серьезные process caveats:

```text
1. Агент использовал запрещенный git add -A.
2. Агент удалял старые тесты:
   - tests/test_core_client_sales.py
   - tests/test_sales_routes.py
   - tests/test_sales_ui_russian.py
   - tests/test_sales_warranty_ui.py
3. Нужно проверить, что coverage не потеряно.
4. Агент дописал logs/2026-07-02.md после commit, возможен dirty worktree.
5. Нужно проверить, не попали ли runtime DB, temp/debug files, root reports.
6. Ранее в R3 были опасные runtime DB actions, нужно убедиться, что в R4 они не повторялись и не закреплены в коде.
```

---

# 2. Текущий заявленный Stage04E-R4 результат

Заявлено:

```text
1. Старый sales_new flow заменен корзиной.
2. У товара есть кнопка "В корзину" для in_stock/reserved.
3. В корзине можно менять:
   - цену вручную;
   - количество;
   - гарантию;
   - без гарантии;
   - способ оплаты.
4. /sales показывает историю продаж и количество товаров.
5. В /sales и /sales/{id} есть кнопка "Товарный чек".
6. sale_receipt_preview.html сделан по reference receipt.
7. OrganizationSettings берутся из Core API.
8. price_tag_preview.html сделан под 58×40 мм.
9. Ценник доступен только из товара, не отдельным пунктом меню.
10. Штрихкод пока placeholder/future-ready.
11. Docker rebuilt.
12. Commit:
    Implement Stage 04E R4 Sales Cart, Receipt, and Price Tag Requirements
```

---

# 3. Owner requirements to verify

Проверить строго:

```text
1. Ценник 58×40 мм.
2. Ценник печатается на термопринтере через browser print preview.
3. Ценник — кнопка у товара, не отдельный раздел.
4. Сейчас ценник можно без штрихкода.
5. Штрихкод заложен как future-ready, но не ломает MVP.
6. Продажа идет через корзину:
   товары сначала добавляются в корзину, потом оформляется продажа.
7. В корзине/checkout:
   - ручная цена;
   - количество;
   - способ оплаты;
   - гарантия по умолчанию 30 дней;
   - гарантию можно изменить;
   - гарантию можно убрать чекбоксом.
8. Если без гарантии, в товарно-гарантийном чеке есть текст:
   "Товар продаётся без гарантии, в том состоянии, в котором есть.
    Покупатель внимательно осмотрел товар при покупке."
9. Все продажи фиксируются в таблице продаж.
10. Продажи можно смотреть отдельно.
11. Реквизиты организации есть в настройках.
12. Реквизиты по умолчанию взяты из reference receipt.
```

Default реквизиты:

```text
Название: ИП Атанов Павел Сергеевич
ИНН: 667009336901
Адрес: Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10
Телефон: +7 343 344 88 95
```

---

# 4. Что запрещено в аудите

Не делать новый функционал.

Запрещено:

```text
начинать следующий этап
добавлять новый print engine
добавлять PDF
делать отдельный раздел "Ценники"
делать silent print
делать прямой DB access из inventory-sales-module
коммитить runtime DB
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
делать Base.metadata.drop_all/create_all
удалять runtime данные
```

Разрешено:

```text
audit report
log
малые test/doc fixes
очевидный bugfix, если без него audit невозможен
```

Если найден функциональный blocker — статус `FAIL` и рекомендовать Stage04E-R4-R repair.

---

# 5. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04E_R4_AUDIT_SALES_CART_RECEIPT_PRICE_TAG_REQUIREMENTS_PROMPT.md
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
1. Есть ли dirty logs/2026-07-02.md после commit.
2. Есть ли untracked temp files:
   - task.md
   - implementation_plan.md
   - debug.py
   - TECHNOREBOOT_STAGE04E_R3_REPORT.md
3. Попал ли reference RTF в docs/reference_templates.
4. Попали ли runtime DB/data files.
5. Какой реальный состав commit после git add -A.
```

Команды:

```powershell
git show --name-only HEAD
git ls-files | Select-String -Pattern "technoreboot.db|tbootit.db|data/db|data/avito-module|__pycache__|pytest_cache|debug.py|task.md|implementation_plan.md"
```

Если dirty только log — создать отдельный normal commit после audit, не amend.

---

# 7. Removed tests coverage audit

Агент удалил старые тесты. Нужно проверить, что важное покрытие не потеряно.

Проверить:

```powershell
git show --name-status HEAD | Select-String -Pattern "test_core_client_sales|test_sales_routes|test_sales_ui_russian|test_sales_warranty_ui"
```

Оценить, покрывают ли новые тесты старые сценарии:

```text
CoreClient sales methods
sales routes happy path
sales error handling
Russian UI
warranty UI
no direct DB access
```

Если coverage потеряно — статус минимум `PASS_WITH_NOTES`, а лучше `FAIL` с repair.

---

# 8. Docker rebuild and tests

Выполнить:

```powershell
docker compose down
docker compose up --build -d
docker compose ps
```

Затем:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Ожидание:

```text
all pass
```

Если core tests pass only after destructive DB reset — это blocker.

---

# 9. Core API audit

Проверить endpoints:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/settings/organization | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:8000/api/sales | ConvertTo-Json -Depth 10
```

Проверить:

```text
organization settings exist
default requisites match owner receipt
sales list exists
sale detail returns sale items
warranty fields exist
```

---

# 10. Inventory UI smoke

Проверить:

```powershell
Invoke-WebRequest http://127.0.0.1:8030/ | Select-Object StatusCode
Invoke-WebRequest http://127.0.0.1:8030/products | Select-Object StatusCode
Invoke-WebRequest http://127.0.0.1:8030/cart | Select-Object StatusCode
Invoke-WebRequest http://127.0.0.1:8030/sales | Select-Object StatusCode
Invoke-WebRequest http://127.0.0.1:8030/settings/organization | Select-Object StatusCode
```

Проверить HTML:

```text
нет "Ценники — скоро" в меню
есть "В корзину" у доступного товара
есть "Печать ценника" у товара в наличии
есть "Настройки" если добавлены organization settings
```

---

# 11. Price tag audit 58×40

Проверить route:

```text
GET /products/{product_id}/price-tag
```

Найти in_stock product:

```powershell
$products = Invoke-RestMethod "http://127.0.0.1:8000/api/products?status=in_stock&limit=5"
$productId = $products.items[0].id
Invoke-WebRequest "http://127.0.0.1:8030/products/$productId/price-tag" | Select-Object StatusCode
```

Проверить template/CSS:

```powershell
Select-String -Path inventory-sales-module\app\templates\price_tag_preview.html -Pattern "58mm|40mm|@page|window.print|Магазин Техноребут|Код"
```

Ожидание:

```text
@page size 58mm 40mm
кнопка Печать
нет обязательного штрихкода сейчас
есть future-ready placeholder
```

---

# 12. Cart flow audit

Manual/API flow:

```text
1. Add product to cart.
2. Open /cart.
3. Change manual price.
4. Change quantity.
5. Checkout with warranty 30.
6. Sale created.
7. Sale appears in /sales.
8. Open sale detail.
9. Open receipt.
```

Проверить через browser или HTTP.

Если current cart uses cookie/session, убедиться:

```text
inventory-sales-module не создал собственную DB
cart не сохраняется в runtime DB inventory module
checkout creates Core sale
```

---

# 13. Warranty/no-warranty audit

Нужно проверить два сценария:

```text
1. Sale with warranty_days=30.
2. Sale with no_warranty=true.
```

Receipt must show:

```text
Гарантия: 30 дней
```

или гарантийный текст 30 дней.

No warranty receipt must show:

```text
Товар продаётся без гарантии, в том состоянии, в котором есть.
Покупатель внимательно осмотрел товар при покупке.
```

---

# 14. Receipt template audit

Проверить:

```text
GET /sales/{sale_id}/receipt
```

Шаблон должен содержать:

```text
organization name
ИНН
address
phone
Товарный чек №
date/time
table columns:
№, Наименование, Код, Ед. изм., Кол-во, Цена, Сумма
Итого
Предоплата
К оплате
Всего наименований
Отпустил
Покупатель
Частное лицо
warranty terms
signature line
Печать button
```

Проверить CSS print layout does not hide required data.

---

# 15. Sales table audit

Проверить `/sales`:

```text
номер продажи
дата
количество товаров
сумма
способ оплаты
гарантия
статус
Открыть
Товарный чек
```

Проверить, что продажа, созданная через cart, появилась в списке.

---

# 16. Organization settings UI audit

Проверить:

```text
GET /settings/organization
POST /settings/organization
```

Проверить, что можно изменить:

```text
название
ИНН
адрес
телефон
кассир/default cashier if present
customer label if present
```

Проверить, что updated settings используются в receipt preview.

---

# 17. Safety scans

Direct DB access in inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Destructive DB calls:

```powershell
git grep -n -I "drop_all\|create_all\|ALTER TABLE\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
```

Browser/captcha automation:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

Runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

---

# 18. Audit report

Создать:

```text
reports/stage04e_r4_audit_sales_cart_receipt_price_tag_requirements_report.md
```

Структура:

```text
# Stage 04E-R4 Audit Sales Cart Receipt Price Tag Requirements Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## EXECUTIVE_SUMMARY

## PROMPT_DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## GIT_PROCESS_AUDIT

git add -A impact:
worktree before:
worktree after:
unexpected files:
runtime data:

## REMOVED_TESTS_COVERAGE_AUDIT

Removed tests:
Replacement coverage:
Findings:

## DOCKER_AND_TESTS

Core:
Inventory:
Avito:

## CORE_API_AUDIT

## ORGANIZATION_SETTINGS_AUDIT

## PRICE_TAG_58X40_AUDIT

## CART_FLOW_AUDIT

## WARRANTY_NO_WARRANTY_AUDIT

## RECEIPT_TEMPLATE_AUDIT

## SALES_TABLE_AUDIT

## SAFETY_SCAN

## BLOCKERS

## NON_BLOCKING_ISSUES

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

If PASS:

TECHNOREBOOT_STAGE04E_R4_AUDIT_READY_FOR_OWNER_MANUAL_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 19. Git

Use targeted add only:

```powershell
git add reports/stage04e_r4_audit_sales_cart_receipt_price_tag_requirements_report.md
git add logs/2026-07-02.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R4_AUDIT_SALES_CART_RECEIPT_PRICE_TAG_REQUIREMENTS_PROMPT.md
git commit -m "Audit Stage 04E R4 sales cart receipt price tag requirements"
git status --short --untracked-files=all
```

If any small fix was required, commit it separately with targeted add.

Forbidden:

```text
git add .
git add -A
git add -u
git commit --amend
```

---

# 20. Definition of Done

Audit готов, если:

```text
git add -A impact checked
worktree final status checked
runtime data not committed
removed tests coverage checked
core tests pass
inventory tests pass
avito tests pass
organization settings work
cart flow works
manual price works
quantity works
warranty 30 works
no warranty works
receipt preview resembles reference structure
price tag 58×40 works
sales table shows sales
no separate price tags nav
no direct DB access in inventory-sales-module
audit report committed
final status READY_FOR_OWNER_MANUAL_CHECK
```

---

# 21. Final answer required from agent

Не писать, что можно начинать следующий этап.

Финальный ответ должен быть:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R4_AUDIT_READY_FOR_OWNER_MANUAL_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```
