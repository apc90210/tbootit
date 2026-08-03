# PROMPT — Техноребут / Stage04I-R9 Reissued Sale Status and Filter Semantics Repair

## Роль

Ты senior FastAPI engineer, domain-model auditor, специалист по продажам и статусам, Jinja2 UI developer, migration engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить последний выявленный регресс в повторном оформлении продажи.

Новый функциональный этап не начинать.

---

# 1. Ошибка, найденная в Stage04I-R8

R8 подтвердил создание повторно оформленной продажи:

```text
Original Sale #37:
status = superseded

New Sale #39:
source_sale_id = 37
status = completed
```

Это противоречит принятой модели Stage04H:

```text
completed
canceled
superseded
reissued
```

Повторно оформленная продажа должна иметь:

```text
status = reissued
```

а не:

```text
status = completed
```

Иначе:

```text
фильтр "Повторно оформленные" не показывает продажу;
фильтр "Завершённые" ошибочно включает её;
чек может не показывать маркер повторного оформления;
UI может предлагать неправильные действия;
аналитика не различает обычную и повторно оформленную продажу.
```

---

# 2. Текущий статус

```text
STAGE04I_R8_BLOCKED_REISSUED_SALE_CREATED_AS_COMPLETED
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIRED_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Архитектурное правило

```text
Обычная успешно завершённая продажа:
status = completed

Отменённая продажа:
status = canceled

Старая продажа после повторного оформления:
status = superseded

Новая продажа, созданная из отменённой:
status = reissued
```

Отчёт по выручке должен учитывать:

```text
completed
reissued
```

и исключать:

```text
canceled
superseded
```

---

# 4. Запреты

Запрещено:

```text
начинать следующий этап
оставлять новую reissue-продажу со статусом completed
маскировать проблему только UI-текстом
ломать отчёты
дублировать выручку
удалять существующие продажи
использовать DELETE FROM
использовать DROP TABLE
использовать drop_all
использовать direct DB access из Inventory
запускать небезопасный core pytest
git add .
git add -A
git add -u
git reset
git clean
git rebase
force push
commit --amend
коммитить DB/temp/cache
```

Core tests запускать только:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

---

# 5. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIR_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit\.agents\received_prompts
C:\tbootit
```

Если найден в Downloads:

```powershell
Copy-Item `
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIR_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIR_PROMPT.md `
  -Force
```

В отчёте:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
PROMPT_SHA256:
```

---

# 6. Preflight

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -15
git diff --name-status
git diff --stat
docker compose ps
```

Ожидаемый исходный HEAD:

```text
f284bcc
```

Если HEAD другой — указать фактический.

---

# 7. Защитить live DB

До изменений снять read-only состояние:

```text
LIVE_DB_SHA256_BEFORE
PRODUCT_COUNT_BEFORE
BARCODE_COUNT_BEFORE
SALE_COUNT_BEFORE
MAX_SALE_ID_BEFORE
```

Также вывести все продажи:

```text
source_sale_id IS NOT NULL
```

с полями:

```text
id
status
source_sale_id
superseded_by_sale_id
total_amount
payment_method
created_at
```

---

# 8. Воспроизвести проблему

Проверить фактическую Sale #39:

```text
GET /api/sales/39
GET /sales/39
GET /sales/39/receipt
```

Зафиксировать:

```text
status
source_sale_id
UI badge
receipt marker
list filter membership
```

Если Sale #39 отсутствует — выбрать любую продажу:

```text
source_sale_id IS NOT NULL
status = completed
```

---

# 9. Найти root cause

Проверить:

```text
core/app/routers/sales.py
core/app/schemas.py
core/app/models.py
core/app/services/*
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/sales.py
inventory-sales-module/app/templates/sales*.html
inventory-sales-module/app/templates/sale_receipt_preview.html
core/app/routers/reports.py
```

Найти место, где reissue создаёт новую Sale.

Ожидаемая ошибка:

```python
status="completed"
```

вместо:

```python
status="reissued"
```

---

# 10. Исправить Core reissue flow

При создании новой продажи через:

```text
POST /api/sales/{sale_id}/reissue
```

новая запись должна иметь:

```text
status = reissued
source_sale_id = old_sale.id
```

Старая запись:

```text
status = superseded
superseded_by_sale_id = new_sale.id
```

Операция должна быть атомарной.

---

# 11. Исправить уже созданные неправильные записи

В live DB могут существовать продажи:

```text
source_sale_id IS NOT NULL
status = completed
```

Нужно выполнить безопасную идемпотентную нормализацию.

Критерий legacy misclassified reissue:

```text
source_sale_id IS NOT NULL
status = completed
```

Перед изменением:

```text
вывести список затрагиваемых sale IDs;
создать backup live DB вне Git;
сохранить SHA256 backup;
зафиксировать количество записей.
```

Нормализация:

```text
completed -> reissued
```

Только для записей с `source_sale_id IS NOT NULL`.

Не менять:

```text
обычные completed продажи без source_sale_id;
canceled;
superseded;
уже reissued.
```

Допустимые способы:

```text
идемпотентная Core migration;
одноразовая Core repair-функция;
служебный Core endpoint с audit event.
```

Предпочтительно:

```text
идемпотентная startup migration с точным условием и audit/log.
```

Повторный запуск должен изменить:

```text
0 записей
```

---

# 12. Audit events

Для исправленных legacy записей создать или записать:

```text
sale.status_normalized
```

Payload:

```text
sale_id
old_status
new_status
source_sale_id
reason = legacy_reissue_status_repair
timestamp
```

Если текущая audit infrastructure не поддерживает массовую startup-запись, минимум записать точный migration report и application log.

---

# 13. Sales list filters

Проверить фильтры:

```text
Все
Завершённые
Отменённые
Заменённые
Повторно оформленные
```

Правила:

```text
completed filter -> только status=completed
canceled filter -> только status=canceled
superseded filter -> только status=superseded
reissued filter -> только status=reissued
```

Sale #39 или её эквивалент:

```text
не должна отображаться в completed;
должна отображаться в reissued.
```

---

# 14. Sale detail UI

Для `reissued` показать:

```text
badge "Повторно оформлена"
source sale link
номер исходной продажи
```

Для `superseded` показать:

```text
badge "Заменена"
superseded_by link
номер новой продажи
```

Не смешивать статусы.

---

# 15. Receipt UI

Новая повторно оформленная продажа должна показывать:

```text
Повторно оформленная продажа
Исходная продажа №...
```

Старая superseded должна сохранять исторический чек:

```text
Продажа заменена
Новая продажа №...
```

---

# 16. Допустимые действия по статусам

Проверить UI-кнопки и Core guards.

Минимальные правила:

```text
completed:
можно отменить

canceled:
можно переоформить

superseded:
нельзя повторно отменять;
нельзя повторно переоформлять

reissued:
считать действующей продажей;
дальнейшие действия должны соответствовать принятой бизнес-логике.
```

Если reissued разрешено отменять:

```text
отмена должна корректно вернуть товар и исключить сумму из отчёта.
```

Если не разрешено:

```text
Core должен вернуть понятный 409;
UI не должен показывать кнопку.
```

Не придумывать новую политику молча. Использовать существующую принятую логику проекта и документировать.

---

# 17. Reports

Проверить все денежные запросы.

Включать:

```text
completed
reissued
```

Исключать:

```text
canceled
superseded
```

Проверить:

```text
total_amount
sales_count
items_count
payment breakdown
today/week/month/year
```

Новая reissued sale учитывается ровно один раз.

---

# 18. Core tests

Обновить/создать:

```text
core/tests/test_sale_reissue_status_semantics.py
```

Покрыть:

```text
1. Новая reissue sale получает status=reissued.
2. Старая получает status=superseded.
3. source_sale_id корректен.
4. superseded_by_sale_id корректен.
5. Обычная продажа остаётся completed.
6. completed filter исключает reissued.
7. reissued filter включает reissued.
8. report включает completed.
9. report включает reissued.
10. report исключает canceled.
11. report исключает superseded.
12. reissued учитывается ровно один раз.
13. payment breakdown учитывает reissued.
14. legacy completed + source_sale_id нормализуется.
15. повторная migration изменяет 0 записей.
```

---

# 19. Inventory tests

Создать/обновить:

```text
inventory-sales-module/tests/test_reissued_status_ui.py
```

Покрыть:

```text
reissued badge
source sale link
superseded badge
new sale link
completed filter excludes reissued
reissued filter includes reissued
receipt marker
actions correspond to status
```

---

# 20. Docker rebuild

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose up -d avito-module
docker compose ps
```

---

# 21. Safe tests

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
```

После safe tests:

```text
live DB hash/counts не должны измениться.
```

---

# 22. Runtime migration validation

До migration:

```text
MISCLASSIFIED_REISSUED_BEFORE
```

После migration:

```text
MISCLASSIFIED_REISSUED_AFTER = 0
NORMALIZED_COUNT
```

Проверить Sale #39:

```text
status = reissued
source_sale_id = 37
```

Проверить Sale #37:

```text
status = superseded
superseded_by_sale_id = 39
```

Если IDs отличаются — указать фактические.

---

# 23. Runtime new reissue scenario

Создать отдельный безопасный runtime сценарий:

```text
создать товар;
создать completed sale;
отменить;
reissue.
```

Зафиксировать:

```text
PRODUCT_ID
ORIGINAL_SALE_ID
NEW_SALE_ID
ORIGINAL_STATUS
NEW_STATUS
SOURCE_SALE_ID
SUPERSEDED_BY_SALE_ID
```

Обязательное ожидание:

```text
ORIGINAL_STATUS = superseded
NEW_STATUS = reissued
```

---

# 24. Runtime filter validation

Проверить:

```text
/sales?status=completed
/sales?status=canceled
/sales?status=superseded
/sales?status=reissued
```

Новая reissue sale:

```text
отсутствует в completed;
присутствует в reissued.
```

Старая sale:

```text
присутствует в superseded.
```

---

# 25. Runtime report validation

Зафиксировать:

```text
REPORT_TOTAL_BEFORE
REPORT_TOTAL_AFTER_INITIAL_SALE
REPORT_TOTAL_AFTER_CANCEL
REPORT_TOTAL_AFTER_REISSUE
```

Ожидаемо:

```text
после initial sale: + сумма;
после cancel: возврат к before;
после reissue: + новая сумма ровно один раз.
```

Проверить payment bucket.

---

# 26. Runtime receipt validation

Проверить:

```text
GET /sales/{new_id}/receipt
GET /sales/{old_id}/receipt
```

Новый чек:

```text
маркер reissued;
ссылка/номер original.
```

Старый чек:

```text
маркер superseded;
ссылка/номер new.
```

---

# 27. Safety scans

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests
```

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 28. Документация

Создать:

```text
docs/stage04i_r9_reissued_status_filters_repair.md
reports/stage04i_r9_reissued_status_filters_repair_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report:

```text
# Stage04I-R9 Reissued Status and Filters Repair Report

## STATUS
## WHY_R8_WAS_NOT_ACCEPTED
## ROOT_CAUSE
## DOMAIN_STATUS_RULES
## LEGACY_MISCLASSIFIED_SALES
## BACKUP
## NORMALIZATION
## REISSUE_FLOW_REPAIR
## FILTERS
## DETAIL_UI
## RECEIPTS
## REPORTS
## TESTS
## LIVE_DB_PRESERVATION
## RUNTIME_REISSUE
## RUNTIME_FILTERS
## RUNTIME_REPORTS
## RUNTIME_RECEIPTS
## SAFETY_SCAN
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_RECHECK_GUIDE
## FINAL_STATUS
```

---

# 29. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/main.py
git add core/app/routers/sales.py
git add core/app/routers/reports.py
git add core/app/services/sale_status_repair.py
git add core/tests/test_sale_reissue_status_semantics.py

git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/sales_list.html
git add inventory-sales-module/app/templates/sales_detail.html
git add inventory-sales-module/app/templates/sale_receipt_preview.html
git add inventory-sales-module/tests/test_reissued_status_ui.py

git add docs/stage04i_r9_reissued_status_filters_repair.md
git add reports/stage04i_r9_reissued_status_filters_repair_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIR_PROMPT.md
git add -f logs/2026-08-03.md
```

Не добавлять DB/backup.

Коммит:

```powershell
git commit -m "Repair reissued sale status and filters"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 30. Definition of Done

```text
new reissue sale status = reissued
old sale status = superseded
source link correct
superseded link correct
legacy misclassified sales normalized
normalization idempotent
completed filter excludes reissued
reissued filter includes reissued
receipts show correct markers
report includes reissued once
report excludes canceled/superseded
payment breakdown correct
Core safe tests PASS
Inventory tests PASS
Avito tests PASS
live DB protected from tests
runtime reissue status proven
runtime filters proven
runtime reports proven
runtime receipts proven
safety scans clean
targeted commit
push
clean Git
owner manual recheck required
```

---

# 31. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIRED_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R9_REISSUED_STATUS_FILTERS_REPAIR_FAIL

BLOCKERS:
...
```
