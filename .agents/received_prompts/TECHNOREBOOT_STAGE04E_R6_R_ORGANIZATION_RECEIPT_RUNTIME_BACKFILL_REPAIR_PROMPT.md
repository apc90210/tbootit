# PROMPT — Техноребут / Stage 04E-R6-R Organization Defaults Runtime Backfill and Receipt Binding Repair

## Роль агента

Ты senior fullstack bugfix engineer, FastAPI/Jinja2 runtime auditor, Docker verification engineer и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить owner-check fail после Stage04E-R6.

Это repair-этап. Не начинать Stage04F и не добавлять новый функционал.

---

# 1. Owner-reported fail

После заявленного R6 owner recheck владелец сообщил:

```text
ничего не поменялось ни товарный чек, не организация (теперь пустая)
```

Это blocker.

Ожидалось:

```text
/settings/organization сразу заполнена реквизитами ИП Атанов
товарный чек показывает реквизиты организации
товарный чек показывает текст гарантии
```

Фактически:

```text
/settings/organization пустая
товарный чек пустой/без реквизитов/без текста
```

---

# 2. Вероятная причина

Проверить обе причины:

## Причина A — existing blank DB row

R6 мог создать default только если записи `organization_settings` нет.

Но в runtime DB уже может быть существующая запись с пустыми строками:

```text
organization_name = ""
inn = ""
address = ""
phone = ""
warranty_text = ""
no_warranty_text = ""
```

Тогда `get_or_create` не срабатывает, потому что запись есть, но UI остаётся пустым.

Правильное поведение:

```text
GET /api/settings/organization всегда должен возвращать effective defaults.
Если любое поле null/empty/whitespace — подставить default по этому полю.
При необходимости backfill сохранить defaults в DB.
```

## Причина B — running containers not using new code

Возможно, локальный UI крутится на старом контейнере/образе.

Нужно проверить:

```text
код внутри контейнера соответствует repo
docker compose up --build -d действительно пересоздал core и inventory-sales-module
```

---

# 3. Source defaults

Использовать эти default values:

```text
organization_name: ИП Атанов Павел Сергеевич
inn: 667009336901
address: Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10
phone: +7 343 344 88 95
default_customer_label: Частное лицо
```

Warranty text:

```text
На все Б/У товары предоставляется гарантия 30 дней.
Гарантийный ремонт и обмен Б/У товара возможен только в случае обнаружения дефекта товара в течении 30 дней с даты продажи.
Товар Б/У без дефектов возврату - не подлежит, возможен обмен, но только по согласованию с менеджером магазина. В случае обнаружения дефекта товара по вине покупателя обмен и возврат товара – невозможен.
На программное обеспечение и расходные материалы гарантия не предоставляется.
В случае обнаружения неисправности – товар сдается на диагностику. По согласованию с продавцом – возможна мгновенная замена товара, без проведения диагностики.
```

No warranty text:

```text
Товар продаётся без гарантии, в том состоянии, в котором есть.
Покупатель внимательно осмотрел товар при покупке.
```

---

# 4. Target status

Текущий статус:

```text
STAGE04E_R6_OWNER_RECHECK_FAILED_ORGANIZATION_AND_RECEIPT_EMPTY
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04E_R6_R_ORGANIZATION_RECEIPT_RUNTIME_BACKFILL_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 5. Строгие запреты

Запрещено:

```text
начинать Stage04F
делать новый функционал
делать direct DB access из inventory-sales-module
создавать отдельную DB для inventory-sales-module
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
коммитить runtime DB/temp/cache
делать Base.metadata.drop_all/create_all
очищать runtime DB для прохождения проверки
```

Разрешено:

```text
точечный bugfix Core settings defaults/backfill
точечный bugfix receipt route/template binding
точечный Docker runtime verification
tests
report/log
targeted commit
normal push
```

---

# 6. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04E_R6_R_ORGANIZATION_RECEIPT_RUNTIME_BACKFILL_REPAIR_PROMPT.md
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

# 7. Preflight

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

Если worktree dirty — сначала понять почему.

---

# 8. Runtime verification before fix

Проверить что реально отдаёт Core:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/settings/organization" | ConvertTo-Json -Depth 10
```

Проверить что реально отдаёт UI:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/settings/organization" -TimeoutSec 15
$page.StatusCode
$page.Content | Select-String "ИП Атанов"
$page.Content | Select-String "667009336901"
$page.Content | Select-String "344 88 95"
$page.Content | Select-String "На все Б/У товары"
```

Проверить код внутри контейнера:

```powershell
docker compose exec core sh -c "grep -R \"ИП Атанов\" -n /app || true"
docker compose exec inventory-sales-module sh -c "grep -R \"warranty_text\" -n /app || true"
```

Если контейнеры не видят новый код — выполнить rebuild/recreate:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
```

---

# 9. Fix A — normalize defaults per field

В Core сделать не просто get_or_create, а get_or_create_and_backfill.

Нужно найти/создать единый источник default settings, например:

```text
core/app/defaults.py
```

или внутри `core/app/routers/settings.py`, если так проще для MVP.

Функция должна делать:

```python
def default_organization_settings_payload() -> dict:
    return {
        "organization_name": "ИП Атанов Павел Сергеевич",
        "inn": "667009336901",
        "address": "Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10",
        "phone": "+7 343 344 88 95",
        "default_customer_label": "Частное лицо",
        "warranty_text": "...",
        "no_warranty_text": "...",
    }

def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""
```

GET behavior:

```text
1. Если записи нет — создать с defaults.
2. Если запись есть, но какие-то поля пустые — заполнить только пустые поля defaults.
3. Commit DB.
4. Вернуть уже заполненную запись.
```

PUT behavior:

```text
1. Если записи нет — создать.
2. Сохранять значения пользователя.
3. Но если пользователь прислал пустое поле случайно:
   - для обязательных реквизитов можно либо сохранить пустое как conscious choice,
   - либо backfill при следующем GET.
```

Для MVP owner requirement сильнее:

```text
/settings/organization при открытии не должна быть пустой.
```

Поэтому GET обязан backfill пустые значения.

---

# 10. Fix B — receipt route must fetch organization settings

Проверить:

```text
inventory-sales-module/app/routers/sales.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/templates/sale_receipt_preview.html
```

Убедиться:

```text
1. sales receipt route запрашивает organization settings через Core API.
2. Передает organization/settings в template.
3. Template отображает:
   - organization_name
   - inn
   - address
   - phone
   - default_customer_label
   - warranty_text или no_warranty_text
4. Если Core API недоступен/вернул пустое — UI использует fallback defaults,
   чтобы чек не был пустым.
```

Важно:

```text
Нельзя оставлять чек пустым.
```

---

# 11. Fix C — organization page must use effective settings

Проверить:

```text
inventory-sales-module/app/routers/settings.py
inventory-sales-module/app/templates/settings_organization.html
```

Убедиться:

```text
1. GET /settings/organization получает effective settings из Core.
2. Если Core вернул пустые значения — UI fallback подставляет defaults.
3. Все поля формы имеют value/default content:
   - organization_name
   - inn
   - address
   - phone
   - default_customer_label
   - warranty_text textarea
   - no_warranty_text textarea
```

---

# 12. Tests — must add failing scenario

Core tests:

```text
core/tests/test_organization_settings_defaults.py
```

Добавить tests:

```text
1. Existing blank OrganizationSettings row is backfilled on GET.
2. Existing partial OrganizationSettings row gets defaults only for blank fields.
3. GET never returns blank organization_name/inn/address/phone/warranty_text/no_warranty_text.
```

Inventory tests:

```text
inventory-sales-module/tests/test_organization_settings_defaults_ui.py
inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py
```

Добавить tests:

```text
1. /settings/organization renders defaults when Core returns defaults.
2. /settings/organization renders fallback defaults if Core returns blank fields.
3. receipt renders organization defaults and warranty text.
4. receipt renders no-warranty disclaimer.
5. receipt does not contain empty organization block.
```

---

# 13. Manual smoke after fix

Полный rebuild/recreate:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose ps
```

Проверить Core:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/settings/organization" | ConvertTo-Json -Depth 10
```

В ответе должны быть:

```text
ИП Атанов Павел Сергеевич
667009336901
+7 343 344 88 95
На все Б/У товары предоставляется гарантия 30 дней.
```

Проверить UI:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/settings/organization" -TimeoutSec 15
$page.StatusCode
$page.Content | Select-String "ИП Атанов Павел Сергеевич"
$page.Content | Select-String "667009336901"
$page.Content | Select-String "344 88 95"
$page.Content | Select-String "На все Б/У товары предоставляется гарантия 30 дней"
```

Проверить browser manually:

```text
http://127.0.0.1:8030/settings/organization
```

---

# 14. Receipt smoke

Если есть продажа:

```text
Открыть /sales
Открыть любой товарный чек
```

Проверить:

```text
есть organization_name
есть ИНН
есть адрес
есть телефон
есть warranty text
```

Если продаж нет, создать тестовую продажу через UI только если это безопасно для runtime MVP. В report указать, была ли создана тестовая продажа.

PowerShell проверка, если sale_id известен:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/sales/<sale_id>/receipt" -TimeoutSec 15
$page.Content | Select-String "ИП Атанов Павел Сергеевич"
$page.Content | Select-String "667009336901"
$page.Content | Select-String "На все Б/У товары"
```

---

# 15. Full regression

Обязательно:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Все должны пройти.

---

# 16. Safety scans

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

# 17. Report/log

Создать:

```text
reports/stage04e_r6_r_organization_receipt_runtime_backfill_repair_report.md
docs/stage04e_r6_r_organization_receipt_runtime_backfill_repair.md
```

Обновить:

```text
logs/2026-07-03.md
```

Report structure:

```text
# Stage 04E-R6-R Organization Receipt Runtime Backfill Repair Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REPORTED_FAIL

## ROOT_CAUSE

Existing blank DB row:
Running container stale code:
Receipt binding issue:

## FIXES

### Core effective defaults/backfill

### Organization settings UI fallback

### Receipt settings binding

### Docker runtime rebuild verification

## DEFAULT_VALUES_VERIFIED

organization_name:
inn:
address:
phone:
warranty_text:
no_warranty_text:

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

Core GET /api/settings/organization:
UI /settings/organization:
Receipt with warranty:
Receipt without warranty:

## SAFETY_SCAN

Runtime tracked:
Direct DB access:
Destructive DB calls:
Secrets:

## FILES_CHANGED

## COMMIT

## PUSH

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R6_R_ORGANIZATION_RECEIPT_RUNTIME_BACKFILL_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 18. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/defaults.py
git add core/app/models.py
git add core/app/schemas.py
git add core/app/main.py
git add core/app/routers/settings.py
git add core/tests/test_organization_settings_defaults.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/settings.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/settings_organization.html
git add inventory-sales-module/app/templates/sale_receipt_preview.html
git add inventory-sales-module/tests/test_organization_settings_defaults_ui.py
git add inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py

git add docs/stage04e_r6_r_organization_receipt_runtime_backfill_repair.md
git add reports/stage04e_r6_r_organization_receipt_runtime_backfill_repair_report.md
git add logs/2026-07-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R6_R_ORGANIZATION_RECEIPT_RUNTIME_BACKFILL_REPAIR_PROMPT.md

git commit -m "Repair organization defaults runtime backfill and receipt binding"
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

# 19. Definition of Done

Готово, если:

```text
Owner-reported empty organization reproduced or explained
Core GET /api/settings/organization returns non-empty Atanov defaults
Existing blank row is backfilled on GET
/settings/organization browser page displays Atanov defaults
Receipt displays organization defaults
Receipt displays warranty text
Receipt without warranty displays no-warranty text
Docker runtime verified after force recreate
full core pytest PASS
full inventory-sales-module pytest PASS
full avito-module pytest PASS
safety scans clean
targeted commit
push
READY_FOR_OWNER_RECHECK
```

---

# 20. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R6_R_ORGANIZATION_RECEIPT_RUNTIME_BACKFILL_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R6_R_ORGANIZATION_RECEIPT_RUNTIME_BACKFILL_FAIL

BLOCKERS:
...
```
