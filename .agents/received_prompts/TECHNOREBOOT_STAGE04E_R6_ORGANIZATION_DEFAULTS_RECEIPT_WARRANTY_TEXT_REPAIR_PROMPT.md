# PROMPT — Техноребут / Stage 04E-R6 Organization Defaults and Receipt Warranty Text Repair

## Роль агента

Ты senior fullstack bugfix engineer, FastAPI/Jinja2 developer, business settings engineer и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить owner-check blocker по настройкам организации и товарно-гарантийному чеку.

Это repair-этап внутри Stage04E/R5 acceptance chain. Не начинать следующий функциональный этап.

---

# 1. Owner-reported problem

Владелец сообщил:

```text
там по умалчанию ничего нет в организации,
имеется ввиду при открытии,
она должны быть заполнена Атанов,
но менять можно
```

Также ранее было сообщено:

```text
в товарниках пустно нет организации и текста
```

Интерпретация:

```text
1. Страница /settings/organization не должна открываться пустой.
2. Если настройки организации ещё не созданы, система должна автоматически показывать default реквизиты из предоставленного товарного чека.
3. Эти реквизиты можно менять и сохранять.
4. Товарно-гарантийный чек должен брать реквизиты организации из настроек.
5. В товарном чеке должен быть гарантийный текст из предоставленного чека.
6. Если продажа "Без гарантии", гарантийный текст заменяется на no-warranty disclaimer.
```

---

# 2. Source reference — default organization and warranty text

Владелец предоставил RTF:

```text
Tovarnyy_chek_rasshirennyy8888888.rtf
```

Использовать как default:

```text
Название организации: ИП Атанов Павел Сергеевич
ИНН: 667009336901
Адрес: Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10
Телефон: +7 343 344 88 95
Покупатель по умолчанию: Частное лицо
```

Default warranty text:

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

# 3. Target status

Текущий статус:

```text
STAGE04E_OWNER_CHECK_FAILED_ORGANIZATION_DEFAULTS_AND_RECEIPT_TEXT
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04E_R6_ORGANIZATION_DEFAULTS_RECEIPT_WARRANTY_TEXT_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 4. Strict prohibitions

Запрещено:

```text
начинать Stage04F
добавлять новый функционал вне задачи
делать прямой DB access из inventory-sales-module
создавать отдельную DB для inventory-sales-module
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
коммитить runtime DB/temp/cache
делать Base.metadata.drop_all/create_all
```

Разрешено:

```text
точечный bugfix Core settings
точечный bugfix inventory settings page
точечный bugfix receipt template
tests
report/log
targeted commit
normal push if remote exists
```

---

# 5. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04E_R6_ORGANIZATION_DEFAULTS_RECEIPT_WARRANTY_TEXT_REPAIR_PROMPT.md
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
```

Если worktree dirty — сначала понять почему.

---

# 7. Fix requirement A — organization settings must auto-create defaults

Проверить текущие файлы:

```text
core/app/models.py
core/app/schemas.py
core/app/routers/settings.py
core/app/main.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/settings.py
inventory-sales-module/app/templates/settings_organization.html
inventory-sales-module/app/templates/sale_receipt_preview.html
```

Нужно реализовать надежное поведение:

```text
GET /api/settings/organization
```

Если organization settings отсутствуют в Core DB:

```text
Core должен автоматически создать запись с default реквизитами
и вернуть её.
```

Предпочтительно:

```text
get_or_create default organization settings в Core
```

Default values:

```text
organization_name = "ИП Атанов Павел Сергеевич"
inn = "667009336901"
address = "Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10"
phone = "+7 343 344 88 95"
default_customer_label = "Частное лицо"
warranty_text = <default warranty text>
no_warranty_text = <default no warranty text>
```

---

# 8. Fix requirement B — organization page must be prefilled

Страница:

```text
GET /settings/organization
```

Должна показывать заполненную форму:

```text
Название организации: ИП Атанов Павел Сергеевич
ИНН: 667009336901
Адрес: Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10
Телефон: +7 343 344 88 95
Покупатель по умолчанию: Частное лицо
Текст гарантии: default warranty text
Текст без гарантии: default no warranty text
```

Не должно быть пустых полей при первом открытии.

Пользователь может изменить поля и сохранить.

После сохранения:

```text
GET /settings/organization
```

должен показывать измененные значения.

---

# 9. Fix requirement C — receipt must use organization settings

Страница:

```text
GET /sales/{sale_id}/receipt
```

Должна показывать:

```text
organization_name
ИНН
address
phone
default_customer_label
```

Если organization settings пустые/не найдены:

```text
использовать default settings из Core
не показывать пустоту
```

---

# 10. Fix requirement D — receipt warranty text

Если продажа с гарантией:

```text
warranty_enabled = true
```

В чеке показывать default warranty text из organization settings.

Первая строка может учитывать выбранное количество дней:

```text
На все Б/У товары предоставляется гарантия <warranty_days> дней.
```

Остальной текст — из default warranty text.

Если продажа без гарантии:

```text
warranty_enabled = false
```

В чеке показывать no warranty text:

```text
Товар продаётся без гарантии, в том состоянии, в котором есть.
Покупатель внимательно осмотрел товар при покупке.
```

И не показывать гарантию 30 дней.

---

# 11. Compatibility with existing settings table

Если таблица organization_settings уже есть, но без warranty fields:

```text
добавить поля:
warranty_text
no_warranty_text
```

Если migrations в проекте отсутствуют, использовать текущий project style:

```text
safe ad-hoc ensure columns on startup
без drop_all/create_all
```

Строго запрещено:

```text
drop_all
runtime DB reset
```

Если поля уже есть — не дублировать.

---

# 12. Tests — Core

Добавить/обновить:

```text
core/tests/test_organization_settings_defaults.py
```

Покрыть:

```text
1. GET /api/settings/organization returns defaults when DB has no explicit settings.
2. Defaults include organization_name = "ИП Атанов Павел Сергеевич".
3. Defaults include inn = "667009336901".
4. Defaults include address.
5. Defaults include phone.
6. Defaults include warranty_text.
7. Defaults include no_warranty_text.
8. PUT /api/settings/organization changes values.
9. GET after PUT returns changed values.
10. No empty organization response.
```

---

# 13. Tests — Inventory module

Добавить/обновить:

```text
inventory-sales-module/tests/test_organization_settings_defaults_ui.py
inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py
```

Покрыть:

```text
1. GET /settings/organization shows default org values.
2. Form fields are prefilled.
3. POST /settings/organization sends changed values to Core.
4. Receipt shows organization_name/inn/address/phone.
5. Receipt with warranty shows warranty text.
6. Receipt without warranty shows no-warranty text.
7. Receipt does not show blank organization area.
```

---

# 14. Manual smoke

После реализации:

```powershell
docker compose up --build -d
docker compose ps
```

Проверить:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/settings/organization" -TimeoutSec 15 | Select-Object StatusCode
```

В браузере:

```text
http://127.0.0.1:8030/settings/organization
```

Должно быть заполнено:

```text
ИП Атанов Павел Сергеевич
667009336901
Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10
+7 343 344 88 95
```

Проверить чек:

```text
1. Открыть любую продажу.
2. Нажать "Товарный чек".
3. Проверить реквизиты.
4. Проверить warranty text.
5. Оформить продажу "Без гарантии".
6. Проверить no-warranty text.
```

---

# 15. Regression tests

Запустить:

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

---

# 17. Docs/report/log

Создать:

```text
reports/stage04e_r6_organization_defaults_receipt_warranty_text_repair_report.md
docs/stage04e_r6_organization_defaults_receipt_warranty_text_repair.md
```

Обновить:

```text
logs/2026-07-03.md
```

---

# 18. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/routers/settings.py
git add core/app/main.py
git add core/tests/test_organization_settings_defaults.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/settings.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/settings_organization.html
git add inventory-sales-module/app/templates/sale_receipt_preview.html
git add inventory-sales-module/tests/test_organization_settings_defaults_ui.py
git add inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py

git add docs/stage04e_r6_organization_defaults_receipt_warranty_text_repair.md
git add reports/stage04e_r6_organization_defaults_receipt_warranty_text_repair_report.md
git add logs/2026-07-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R6_ORGANIZATION_DEFAULTS_RECEIPT_WARRANTY_TEXT_REPAIR_PROMPT.md

git commit -m "Repair organization defaults and receipt warranty text"
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
/settings/organization opens with default Atanov organization values
organization settings can be changed and saved
receipt shows organization values
receipt warranty sale shows warranty text from RTF/default settings
receipt no-warranty sale shows no-warranty disclaimer
no blank organization area in receipt
tests pass: core, inventory-sales-module, avito-module
no runtime/temp tracked
no direct DB access in inventory-sales-module
normal targeted commit
push if remote exists
READY_FOR_OWNER_RECHECK
```

---

# 20. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R6_ORGANIZATION_DEFAULTS_RECEIPT_WARRANTY_TEXT_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R6_ORGANIZATION_DEFAULTS_RECEIPT_WARRANTY_TEXT_FAIL

BLOCKERS:
...
```
