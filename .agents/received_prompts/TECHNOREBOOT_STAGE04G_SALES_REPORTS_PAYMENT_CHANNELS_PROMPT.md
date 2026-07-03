# PROMPT — Техноребут / Stage 04G Sales Reports and Payment Channels

## Роль агента

Ты senior fullstack developer, FastAPI backend engineer, Jinja2 UI developer, business reporting engineer и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — реализовать следующий функциональный этап после успешной ручной проверки R6-S: отдельный раздел отчётов по продажам и расширение способов поступления денег.

---

# 1. Owner request

Владелец сообщил:

```text
все дальше что?
еще нужна будет отчет за день, неделю и год,
отдельный раздел,
в котором видны все продажи,
видны сразу деньги за указанный период
и видно каким образом поступили деньги.
Нужно так же добавить деньги пришли на счет юр лица.
```

Интерпретация:

```text
1. Нужен отдельный раздел "Отчёты" / "Отчёты продаж".
2. В разделе должны быть отчёты:
   - за день;
   - за неделю;
   - за год;
   - дополнительно custom period: date_from/date_to.
3. В отчёте должна быть таблица всех продаж за выбранный период.
4. Сразу должны быть видны деньги за период:
   - общая сумма;
   - количество продаж;
   - количество товаров.
5. Должно быть видно, каким образом поступили деньги:
   - наличные;
   - карта/эквайринг;
   - перевод;
   - СБП;
   - счёт юрлица.
6. Нужно добавить вариант поступления денег:
   "На счёт юрлица" / `legal_entity_account`.
```

---

# 2. Stage status

Текущий принятый контекст:

```text
Stage04E-R6-S warranty text HTML cleanup and close button repair completed.
Owner says: "все дальше что?"
```

Новый этап:

```text
TECHNOREBOOT_STAGE04G_SALES_REPORTS_PAYMENT_CHANNELS
```

Целевой финальный статус:

```text
TECHNOREBOOT_STAGE04G_SALES_REPORTS_PAYMENT_CHANNELS_READY_FOR_OWNER_CHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Strict architecture rules

Система строго модульная.

Core:

```text
Core owns DB and business data.
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
отдельная DB для отчётов
ручное чтение core DB из UI module
git add .
git add -A
git add -u
git commit --amend
git reset / git clean / rebase / force push
runtime DB/temp/cache in git
Base.metadata.drop_all/create_all
```

Разрешено:

```text
Core API endpoints for reports
Core model/schema extension if needed
safe startup column ensure if project style requires it
Inventory UI pages calling Core API
tests
docs/report/log
targeted commit
normal push
```

---

# 4. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04G_SALES_REPORTS_PAYMENT_CHANNELS_PROMPT.md
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

# 5. Preflight

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

# 6. Data model requirements

Проверить текущую модель sale/sales.

Нужно обеспечить наличие полей:

```text
payment_method
payment_channel / payment_destination / payment_account
paid_to_legal_entity_account
```

Минимально для MVP можно сделать одно поле:

```text
payment_method: str
```

С допустимыми значениями:

```text
cash = Наличные
card = Карта / эквайринг
transfer = Перевод
sbp = СБП
legal_entity_account = Счёт юрлица
other = Другое
```

Если уже есть `payment_method`, расширить допустимые значения и UI.

Если нужно отдельно фиксировать, куда пришли деньги:

```text
payment_destination:
- cashbox = Касса
- personal_card = Личная карта
- legal_entity_account = Счёт юрлица
- other = Другое
```

Для текущего owner request достаточно обязательно добавить способ:

```text
legal_entity_account = Счёт юрлица
```

Важно:

```text
Отчёт должен показывать разбивку по способам поступления денег.
```

---

# 7. Checkout/sale creation UI requirement

В форме оформления продажи / корзине добавить выбор способа поступления денег.

Варианты на русском:

```text
Наличные
Карта / эквайринг
Перевод
СБП
Счёт юрлица
Другое
```

При оформлении продажи выбранное значение должно сохраняться в Core sale.

Если старые продажи не имеют payment_method:

```text
показывать "Не указано"
в отчётах учитывать в группе "Не указано"
```

---

# 8. Core API reports endpoints

Добавить endpoints в Core.

Рекомендуемый роутер:

```text
core/app/routers/reports.py
```

Endpoints:

```text
GET /api/reports/sales
GET /api/reports/sales/summary
```

Можно сделать один endpoint:

```text
GET /api/reports/sales?period=today|week|month|year&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
```

Response structure:

```json
{
  "period": "today",
  "date_from": "2026-07-03",
  "date_to": "2026-07-03",
  "total_amount": 12500,
  "sales_count": 5,
  "items_count": 7,
  "payment_breakdown": [
    {
      "payment_method": "cash",
      "label": "Наличные",
      "amount": 5000,
      "sales_count": 2
    },
    {
      "payment_method": "legal_entity_account",
      "label": "Счёт юрлица",
      "amount": 7500,
      "sales_count": 3
    }
  ],
  "sales": [
    {
      "id": 1,
      "created_at": "...",
      "total_amount": 2500,
      "items_count": 1,
      "payment_method": "legal_entity_account",
      "payment_method_label": "Счёт юрлица",
      "customer_label": "Частное лицо"
    }
  ]
}
```

Period logic:

```text
today: current local date
week: current week, Monday-Sunday
month: current month
year: current calendar year
custom: date_from/date_to from query
```

If user asked only day/week/year, still add custom period because it is useful and low-risk.

---

# 9. Inventory-sales-module UI

Добавить отдельный раздел в верхнее меню:

```text
Отчёты
```

URL:

```text
/reports/sales
```

Page title:

```text
Отчёт по продажам
```

UI should include:

```text
1. Quick period buttons:
   - Сегодня
   - Неделя
   - Месяц
   - Год
2. Custom period form:
   - date_from
   - date_to
   - Применить
3. Summary cards:
   - Выручка за период
   - Количество продаж
   - Количество товаров
4. Payment breakdown:
   - Наличные
   - Карта / эквайринг
   - Перевод
   - СБП
   - Счёт юрлица
   - Не указано
5. Table of sales:
   - Дата
   - № продажи
   - Сумма
   - Кол-во товаров
   - Способ поступления денег
   - Действия: Открыть, Товарный чек
```

Important:

```text
"Счёт юрлица" must be visible in checkout and report.
```

---

# 10. Core client

Add methods:

```python
get_sales_report(period=None, date_from=None, date_to=None)
```

Inventory-sales-module must call only Core HTTP API.

No direct DB access.

---

# 11. Tests — Core

Add:

```text
core/tests/test_sales_reports.py
```

Cover:

```text
1. Report today returns sales created today.
2. Report week returns current week sales.
3. Report year returns current year sales.
4. Custom date_from/date_to filters sales.
5. total_amount is correct.
6. sales_count is correct.
7. items_count is correct.
8. payment_breakdown groups by payment_method.
9. legal_entity_account is included and labelled "Счёт юрлица".
10. Old/blank payment_method appears as "Не указано".
```

If sale creation schema changed:

```text
Core sales create accepts payment_method=legal_entity_account.
```

---

# 12. Tests — Inventory module

Add:

```text
inventory-sales-module/tests/test_sales_reports_ui.py
inventory-sales-module/tests/test_sales_payment_channels_ui.py
```

Cover:

```text
1. /reports/sales opens.
2. Page has Russian labels.
3. Quick period buttons are visible:
   Сегодня, Неделя, Месяц, Год.
4. Summary cards show total amount/sales/items.
5. Payment breakdown shows "Счёт юрлица".
6. Sales table shows payment method label.
7. Checkout/cart form contains option "Счёт юрлица".
8. CoreClient calls /api/reports/sales.
9. No direct DB access.
```

---

# 13. Manual smoke

After implementation:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose ps
```

Check UI:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales" -TimeoutSec 15 | Select-Object StatusCode
```

Check HTML:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/reports/sales" -TimeoutSec 15
$page.Content | Select-String "Отчёт по продажам"
$page.Content | Select-String "Сегодня"
$page.Content | Select-String "Неделя"
$page.Content | Select-String "Год"
$page.Content | Select-String "Счёт юрлица"
$page.Content | Select-String "Выручка"
```

Check Core API:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=today" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=week" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=year" | ConvertTo-Json -Depth 10
```

---

# 14. Full regression

Run:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

All must pass.

---

# 15. Safety scans

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

# 16. Docs/report/log

Create:

```text
reports/stage04g_sales_reports_payment_channels_report.md
docs/stage04g_sales_reports_payment_channels.md
```

Update:

```text
logs/2026-07-03.md
```

Report structure:

```text
# Stage 04G Sales Reports and Payment Channels Report

## STATUS

READY_FOR_OWNER_CHECK / FAIL

## OWNER_REQUIREMENT

## IMPLEMENTED

### Payment channels

### Sales report Core API

### Sales report UI

### Checkout payment method

## API

## UI

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

/reports/sales:
Core /api/reports/sales:
Checkout payment channel:

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

TECHNOREBOOT_STAGE04G_SALES_REPORTS_PAYMENT_CHANNELS_READY_FOR_OWNER_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 17. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/main.py
git add core/app/routers/reports.py
git add core/app/routers/sales.py
git add core/tests/test_sales_reports.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/reports.py
git add inventory-sales-module/app/routers/cart.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/base.html
git add inventory-sales-module/app/templates/reports_sales.html
git add inventory-sales-module/app/templates/cart.html
git add inventory-sales-module/app/templates/sales_list.html
git add inventory-sales-module/tests/test_sales_reports_ui.py
git add inventory-sales-module/tests/test_sales_payment_channels_ui.py

git add docs/stage04g_sales_reports_payment_channels.md
git add reports/stage04g_sales_reports_payment_channels_report.md
git add logs/2026-07-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04G_SALES_REPORTS_PAYMENT_CHANNELS_PROMPT.md

git commit -m "Implement Stage 04G sales reports and payment channels"
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

# 18. Definition of Done

Готово, если:

```text
Отдельный раздел "Отчёты" появился
/reports/sales открывается
есть отчеты Сегодня/Неделя/Месяц/Год/custom
видна сумма денег за период
видны все продажи за период
виден способ поступления денег
есть вариант "Счёт юрлица"
оформление продажи позволяет выбрать "Счёт юрлица"
Core API reports implemented
Core/inventory/avito tests pass
safety scans clean
targeted commit
push
READY_FOR_OWNER_CHECK
```

---

# 19. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_SALES_REPORTS_PAYMENT_CHANNELS_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_SALES_REPORTS_PAYMENT_CHANNELS_FAIL

BLOCKERS:
...
```
