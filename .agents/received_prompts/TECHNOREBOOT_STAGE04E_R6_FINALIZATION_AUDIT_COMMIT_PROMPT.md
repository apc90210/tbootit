# PROMPT — Техноребут / Stage 04E-R6 Finalization Audit & Commit

## Роль агента

Ты senior release engineer, QA auditor, FastAPI/Jinja2 reviewer и Git hygiene engineer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — финализировать Stage 04E-R6 после реализации дефолтных реквизитов организации и текста гарантии.

Это не новый функционал. Это finalization/audit/commit этап.

---

# 1. Почему нужен этот этап

Агент сообщил, что Stage04E-R6 реализован, но оставил проект в состоянии:

```text
worktree clean: false
committed files: None
```

Также были прогнаны только точечные тесты:

```text
core/tests/test_organization_settings_defaults.py
inventory-sales-module/tests/test_organization_settings_defaults_ui.py
inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py
```

Но prompt требовал полный regression:

```text
core pytest
inventory-sales-module pytest
avito-module pytest
```

Пока это не выполнено и не закоммичено, owner acceptance невозможен.

---

# 2. Заявленные изменения R6

Проверить и финализировать изменения:

```text
core/app/models.py
core/app/schemas.py
core/app/main.py
core/app/routers/settings.py
inventory-sales-module/app/routers/settings.py
inventory-sales-module/app/templates/settings_organization.html
inventory-sales-module/app/templates/sale_receipt_preview.html
core/tests/test_organization_settings_defaults.py
inventory-sales-module/tests/test_organization_settings_defaults_ui.py
inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py
logs/2026-07-03.md
```

Заявлено:

```text
1. OrganizationSettings получил warranty_text и no_warranty_text.
2. Core создаёт default organization settings, если их нет.
3. /settings/organization показывает дефолтные данные Атанова.
4. Настройки можно менять и сохранять.
5. Товарный чек берёт реквизиты из настроек.
6. Товарный чек показывает гарантийный текст.
7. При "Без гарантии" показывает no-warranty text.
```

---

# 3. Целевой статус

Текущий статус:

```text
STAGE04E_R6_IMPLEMENTED_BUT_UNCOMMITTED_AND_PARTIALLY_TESTED
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04E_R6_FINALIZED_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 4. Строгие запреты

Запрещено:

```text
начинать Stage04F
делать новый функционал
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
коммитить runtime DB/temp/cache
делать Base.metadata.drop_all/create_all
делать прямой DB access из inventory-sales-module
```

Разрешено:

```text
точечный bugfix, если полный regression выявит ошибку
создать report/doc
обновить log
targeted commit
обычный git push, если remote существует
```

---

# 5. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04E_R6_FINALIZATION_AUDIT_COMMIT_PROMPT.md
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
git diff -- core/app/models.py core/app/schemas.py core/app/main.py core/app/routers/settings.py
git diff -- inventory-sales-module/app/routers/settings.py inventory-sales-module/app/templates/settings_organization.html inventory-sales-module/app/templates/sale_receipt_preview.html
```

Проверить:

```text
1. Какие файлы изменены.
2. Какие новые тесты untracked.
3. Нет ли лишних temp/runtime файлов.
4. Нет ли accidental changes вне R6.
```

---

# 7. Code review checklist

Проверить:

## Core

```text
1. OrganizationSettings model имеет поля:
   - organization_name
   - inn
   - address
   - phone
   - default_customer_label
   - warranty_text
   - no_warranty_text

2. GET /api/settings/organization:
   - не возвращает пустоту;
   - создает default settings, если записи нет;
   - возвращает ИП Атанов Павел Сергеевич по умолчанию.

3. PUT /api/settings/organization:
   - сохраняет изменения;
   - если записи не было — создает;
   - не теряет warranty_text/no_warranty_text.

4. main.py safe migration:
   - добавляет колонки только если их нет;
   - не вызывает drop_all;
   - не удаляет данные.
```

## Inventory settings page

```text
1. /settings/organization открывается.
2. Поля prefilled:
   - ИП Атанов Павел Сергеевич
   - 667009336901
   - Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10
   - +7 343 344 88 95
   - Частное лицо
   - warranty_text
   - no_warranty_text

3. POST /settings/organization сохраняет изменения.
```

## Receipt

```text
1. /sales/{sale_id}/receipt показывает реквизиты организации.
2. Если warranty_enabled=true:
   - показывает warranty_days;
   - показывает warranty_text.
3. Если warranty_enabled=false:
   - показывает no_warranty_text;
   - не показывает гарантию 30 дней.
4. В чеке не должно быть пустого блока организации.
```

---

# 8. Required full tests

Обязательно выполнить:

```powershell
docker compose up --build -d
docker compose ps

docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Если любой тест падает:

```text
исправить точечно
повторить полный regression
```

---

# 9. Manual smoke

Проверить:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/settings/organization" -TimeoutSec 15 | Select-Object StatusCode
```

Проверить содержимое HTML:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/settings/organization" -TimeoutSec 15
$page.Content | Select-String "ИП Атанов Павел Сергеевич"
$page.Content | Select-String "667009336901"
$page.Content | Select-String "344 88 95"
$page.Content | Select-String "На все Б/У товары предоставляется гарантия 30 дней"
```

Если есть доступная продажа, проверить receipt:

```text
GET /sales/{sale_id}/receipt
```

Если продаж нет, не создавать мусорные runtime данные без необходимости; можно проверить template тестами.

---

# 10. Safety scans

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

Secret/runtime scan:

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 11. Docs/report/log

Создать/обновить:

```text
reports/stage04e_r6_finalization_audit_commit_report.md
docs/stage04e_r6_organization_defaults_receipt_warranty_text_repair.md
logs/2026-07-03.md
```

Report structure:

```text
# Stage 04E-R6 Finalization Audit & Commit Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## REASON

## PROMPT_DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## PRE_COMMIT_STATE

Branch:
HEAD:
Dirty files:
Untracked files:

## CODE_REVIEW

Core settings:
Safe migration:
Inventory settings page:
Receipt rendering:

## DEFAULT_ORGANIZATION_VALUES

organization_name:
inn:
address:
phone:
default_customer_label:

## DEFAULT_WARRANTY_TEXT

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

/settings/organization:
default values visible:
receipt with warranty:
receipt without warranty:

## SAFETY_SCAN

Runtime tracked:
Direct DB access:
Destructive DB calls:
Secrets:

## FILES_COMMITTED

## PUSH_STATUS

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R6_FINALIZED_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 12. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/main.py
git add core/app/routers/settings.py
git add core/tests/test_organization_settings_defaults.py

git add inventory-sales-module/app/routers/settings.py
git add inventory-sales-module/app/templates/settings_organization.html
git add inventory-sales-module/app/templates/sale_receipt_preview.html
git add inventory-sales-module/tests/test_organization_settings_defaults_ui.py
git add inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py

git add docs/stage04e_r6_organization_defaults_receipt_warranty_text_repair.md
git add reports/stage04e_r6_finalization_audit_commit_report.md
git add logs/2026-07-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R6_FINALIZATION_AUDIT_COMMIT_PROMPT.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R6_ORGANIZATION_DEFAULTS_RECEIPT_WARRANTY_TEXT_REPAIR_PROMPT.md

git commit -m "Finalize Stage 04E R6 organization defaults and warranty receipt"
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

# 13. Definition of Done

Готово, если:

```text
worktree changes reviewed
/settings/organization default values visible
receipt renders organization values
receipt renders warranty text
receipt renders no-warranty text
full core pytest PASS
full inventory-sales-module pytest PASS
full avito-module pytest PASS
safety scans clean
report created
targeted commit created
push done if remote exists
final git status clean
READY_FOR_OWNER_RECHECK
```

---

# 14. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R6_FINALIZED_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R6_FINALIZATION_FAIL

BLOCKERS:
...
```
