# PROMPT — Техноребут / Stage 04E-R5-R Cascading Filters Owner Check Repair

## Роль агента

Ты senior fullstack bugfix engineer, FastAPI/Jinja2 developer, UX regression engineer и release safety auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить owner-check blockers после Stage04E-R5 cascading filters.

Это repair-этап, не новый функционал и не Stage04F.

---

# 1. Owner-reported bugs

Владелец при ручной проверке сообщил:

```text
Ценники — скоро (Stage04F) остался.

{"detail":[{"type":"int_parsing","loc":["query","category_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":""}]}

ошибки при выборе фильра сразу если иду не слева направо, а фильтр в середине,
если слева направо то ок
```

Интерпретация:

```text
1. В UI всё ещё остался пункт/текст "Ценники — скоро (Stage04F)".
   Это запрещено. Ценники не являются отдельным разделом.

2. Если пользователь выбирает фильтр не строго слева направо, например сразу "Производитель",
   форма отправляет пустой параметр category_id=.
   Core ожидает category_id как int и падает с int_parsing.
```

---

# 2. Целевой статус

Текущий статус:

```text
STAGE04E_R5_OWNER_CHECK_FAILED
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04E_R5_R_CASCADING_FILTERS_OWNER_CHECK_REPAIR_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Что строго запрещено

Запрещено:

```text
начинать Stage04F
добавлять отдельный раздел "Ценники"
оставлять текст "Ценники — скоро"
делать прямой DB access из inventory-sales-module
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
коммитить runtime DB/temp/cache
```

Разрешено:

```text
точечный bugfix UI/router/CoreClient/Core endpoint
tests
docs/report/log
targeted commit
```

---

# 4. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04E_R5_R_CASCADING_FILTERS_OWNER_CHECK_REPAIR_PROMPT.md
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
```

Если worktree dirty — сначала понять почему, не начинать правки вслепую.

---

# 6. Bug 1 — remove "Ценники — скоро (Stage04F)"

Найти все вхождения:

```powershell
git grep -n -I "Ценники\|Stage04F\|ценники.*скоро\|Ценники.*скоро" -- .
```

Исправить UI:

```text
1. Убрать "Ценники — скоро" из верхнего меню.
2. Убрать "Stage04F" из пользовательского UI.
3. Не добавлять отдельный раздел ценников.
4. Оставить печать ценника только как action у товара:
   - в списке товаров;
   - в карточке товара.
```

Допустимо оставить Stage04F только в docs/reports/prompts как историческое упоминание, но не в пользовательских templates/UI.

Важно:

```text
Если git grep находит Stage04F в docs/prompts — это не blocker.
Если находит в templates/static UI — blocker.
```

---

# 7. Bug 2 — empty category_id causes Core int_parsing

## 7.1 Root cause to confirm

Проверить URL, который падает:

```text
/products?category_id=&brand=Lenovo
/products?category_id=&model=...
```

И Core/API запросы:

```text
/api/products/filter-options?category_id=&brand=Lenovo
/api/products/?category_id=&brand=Lenovo
```

Ошибка:

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["query", "category_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": ""
    }
  ]
}
```

## 7.2 Preferred fix

Исправить на уровне `inventory-sales-module`:

```text
Перед отправкой query params в Core удалять пустые значения:
- None
- ""
- whitespace-only strings
```

То есть `category_id=""` вообще не должен уходить в Core.

Где проверить/исправить:

```text
inventory-sales-module/app/routers/products.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/templates/products.html
```

Рекомендуемая функция:

```python
def clean_query_params(params: dict) -> dict:
    return {
        key: value
        for key, value in params.items()
        if value is not None and str(value).strip() != ""
    }
```

Использовать для:

```text
get_products(...)
get_product_filter_options(...)
```

## 7.3 UI JS fix

Перед submit можно также отключать/удалять пустые select/input:

```javascript
function cleanEmptyFilterInputs(form) {
  form.querySelectorAll('select, input').forEach(function(el) {
    if (!el.value || el.value.trim() === '') {
      el.disabled = true;
    }
  });
}
```

Или делать это только для filter form.

Важно:

```text
Не disabled permanently после страницы.
Это только перед submit.
```

Можно обойтись без JS-clean, если backend/router/CoreClient гарантированно чистит params.

## 7.4 Optional Core hardening

Можно дополнительно сделать Core tolerant к пустым query params, но аккуратно:

```text
category_id as Optional[str] with normalization
или dependency that parses blank as None
```

Но preferred fix — не отправлять пустые параметры из inventory-sales-module.

Если меняется Core endpoint, добавить тесты.

---

# 8. Expected behavior after fix

Проверить сценарии:

```text
1. Открыть /products.
2. Не выбирать категорию.
3. Сразу выбрать Производитель = Lenovo.
4. Страница должна открыться 200.
5. URL не должен содержать category_id=.
   Допустимо: /products?brand=Lenovo
   Нежелательно: /products?category_id=&brand=Lenovo
6. Таблица должна показать Lenovo без ошибки.
7. filter-options должен получить brand=Lenovo без пустого category_id.
```

Также:

```text
1. Не выбирать категорию/бренд.
2. Сразу выбрать модель.
3. Нет 422/int_parsing.
```

Также:

```text
1. Выбрать категорию.
2. Потом бренд.
3. Потом сменить категорию.
4. Правые фильтры сбрасываются.
5. Нет пустых int params.
```

---

# 9. Tests — required

Добавить/обновить tests.

Core tests:

```text
core/tests/test_product_filter_options_cascading.py
```

Если Core hardened:

```text
GET /api/products/filter-options?category_id=&brand=Lenovo does not 422
GET /api/products/?category_id=&brand=Lenovo does not 422
```

Если fix только в inventory-sales-module, core test not required for blank int.

Inventory tests:

```text
inventory-sales-module/tests/test_cascading_product_filters_ui.py
inventory-sales-module/tests/test_core_client_cascading_filters.py
```

Покрыть обязательно:

```text
1. /products?category_id=&brand=Lenovo returns 200, not Core API error.
2. /products?category_id=&model=ThinkPad returns 200, not Core API error.
3. CoreClient does not pass category_id="" to Core.
4. Empty params are removed before request.
5. UI does not contain "Ценники — скоро".
6. UI does not contain "Stage04F" in templates/nav.
7. Reset filters link works.
8. Existing left-to-right cascade still works.
```

---

# 10. Manual smoke

После fix:

```powershell
docker compose up --build -d
docker compose ps
```

Проверить:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/products" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?category_id=&brand=Lenovo" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?category_id=&model=ThinkPad" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?brand=Lenovo" -TimeoutSec 15 | Select-Object StatusCode
```

Ожидание:

```text
200
200
200
200
```

Проверить Core directly, если Core hardened:

```powershell
Invoke-WebRequest "http://127.0.0.1:8000/api/products/filter-options?category_id=&brand=Lenovo" -TimeoutSec 15 | Select-Object StatusCode
```

---

# 11. Regression tests

Запустить:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Все должны пройти.

---

# 12. Safety scans

Runtime tracked:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

Direct DB access in inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Browser/captcha automation:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

---

# 13. Docs/report/log

Создать:

```text
reports/stage04e_r5_r_cascading_filters_owner_check_repair_report.md
docs/stage04e_r5_r_cascading_filters_owner_check_repair.md
```

Обновить:

```text
logs/2026-07-03.md
```

Report structure:

```text
# Stage 04E-R5-R Cascading Filters Owner Check Repair Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REPORTED_BUGS

## ROOT_CAUSE

## FIXES

### Removed Price Tags Nav

### Empty Query Param Sanitization

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

/products:
/products?category_id=&brand=Lenovo:
/products?category_id=&model=ThinkPad:
/products?brand=Lenovo:

## SAFETY_SCAN

## FILES_CHANGED

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R5_R_CASCADING_FILTERS_OWNER_CHECK_REPAIR_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 14. Git

Use targeted add only.

Possible files:

```powershell
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/base.html
git add inventory-sales-module/tests/test_cascading_product_filters_ui.py
git add inventory-sales-module/tests/test_core_client_cascading_filters.py
git add core/app/routers/products.py
git add core/tests/test_product_filter_options_cascading.py
git add docs/stage04e_r5_r_cascading_filters_owner_check_repair.md
git add reports/stage04e_r5_r_cascading_filters_owner_check_repair_report.md
git add logs/2026-07-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R5_R_CASCADING_FILTERS_OWNER_CHECK_REPAIR_PROMPT.md

git commit -m "Repair cascading filters owner check issues"
git status --short --untracked-files=all
```

Forbidden:

```text
git add .
git add -A
git add -u
git commit --amend
```

If remote GitHub already exists, push after clean commit:

```powershell
git push
```

No force push.

---

# 15. Definition of Done

Готово, если:

```text
"Ценники — скоро" removed from user UI
"Stage04F" removed from user UI
/products?category_id=&brand=Lenovo returns 200
/products?category_id=&model=... returns 200
blank category_id not forwarded to Core or Core tolerates it safely
selecting middle filter first works
left-to-right cascade still works
reset filters works
tests pass: core, inventory-sales-module, avito-module
no runtime/temp tracked
no direct DB access in inventory-sales-module
normal targeted commit
push if repo remote exists
READY_FOR_OWNER_RECHECK
```

---

# 16. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R5_R_CASCADING_FILTERS_OWNER_CHECK_REPAIR_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R5_R_CASCADING_FILTERS_OWNER_CHECK_REPAIR_FAIL

BLOCKERS:
...
```
