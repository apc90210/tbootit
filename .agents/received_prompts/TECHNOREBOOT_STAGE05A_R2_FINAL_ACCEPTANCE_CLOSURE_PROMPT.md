# PROMPT — Техноребут / Stage05A-R2 Final Acceptance Closure

## Роль

Ты senior FastAPI engineer, SQLite forensic auditor, domain-workflow QA, Docker release validator и архитектор проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — закрыть последние доказательные и безопасностные пробелы Stage05A.

Новый этап Stage05B не начинать.

---

# 1. Почему Stage05A-R1 пока не принят

Stage05A-R1 подтвердил полную матрицу статусов, `by-number`, `options`, новые UI-фильтры и safe-test isolation. Однако финальный отчёт не закрывает следующие обязательные пункты.

## 1.1. Не классифицированы все repair rows

В отчёте описаны:

```text
ID 1 — legacy
ID 2 — legacy
ID 5 — runtime PATH A
ID 6 — runtime PATH B
ID 7 — runtime PATH C
```

Но полностью отсутствует происхождение:

```text
ID 3
ID 4
```

Ранее Stage05A сообщал о runtime-записи:

```text
ID 4
R-20260803-0002
```

Нужно классифицировать каждую строку `repair_orders`, без исключений.

---

## 1.2. Не доказаны все обязательные list filters

В runtime-доказательствах приведены только:

```text
q
status
customer_phone
```

Но Stage05A требует также:

```text
priority
device_type
assigned_to
date_from
date_to
serial_number
page
page_size
sort
```

Фраза «все фильтры выполнены» без отдельных тестов и результатов недостаточна.

---

## 1.3. PATCH и history endpoints не доказаны runtime

Нужно явно проверить:

```text
PATCH /api/repairs/{id}
GET /api/repairs/{id}/history
```

Включая запрет изменения:

```text
number
status
timestamps
```

и terminal protection.

---

## 1.4. Customer integration доказана не полностью

Отчёт утверждает:

```text
lookup Customer по customer_id или phone;
автоматическое создание Customer;
snapshot в RepairOrder.
```

Но не доказаны:

```text
выбор существующего клиента через UI;
отсутствие дубля при повторном телефоне;
snapshot immutability;
поведение при customer_id + конфликтующем phone/name;
валидация несуществующего customer_id;
отсутствие локальной customer table в repairs-module.
```

Автоматическое создание Customer не должно молча создавать дубли или подменять существующего клиента.

---

## 1.5. Не доказано сохранение products и sales

Нужны сравнения с pre-Stage05A backup:

```text
products: count, IDs, barcodes;
sales: count, IDs, statuses, totals;
organization settings;
customers.
```

В отчёте отсутствуют обязательные verdict-флаги:

```text
EXISTING_PRODUCT_DATA_PRESERVED
EXISTING_SALES_DATA_PRESERVED
LEGACY_REPAIR_DATA_PRESERVED
```

---

## 1.6. Safety scan содержит опасную оговорку

В отчёте указано:

```text
0 production matches outside reset endpoint
```

Это означает, что в production-коде может существовать reset endpoint с destructive SQL.

Нужно:

```text
найти точный endpoint;
показать файл и строки;
объяснить назначение;
удалить или гарантированно отключить в normal/local production profile;
доказать, что он недоступен через HTTP;
добавить regression test.
```

Stage05A нельзя принимать при доступном destructive reset endpoint.

---

## 1.7. Новый test file не подтверждён collect-only доказательством

Добавлен:

```text
core/tests/test_repairs_status_matrix_complete.py
```

Но итоговый Core count остался `136`, как и до добавления файла.

Нужно доказать:

```text
pytest действительно собирает новый файл;
сколько тестов в нём;
collect-only содержит его;
отдельный запуск файла проходит;
общий test count объяснён.
```

---

## 1.8. Не доказан финальный clean worktree

Нужны точные результаты:

```text
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 2. Текущий статус

```text
STAGE05A_R1_BLOCKED_INCOMPLETE_ROW_RECONCILIATION_FILTER_PROOF_AND_RESET_ENDPOINT_RISK
```

Целевой статус:

```text
TECHNOREBOOT_STAGE05A_R2_FINAL_ACCEPTANCE_CLOSURE_READY_FOR_OWNER_CHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_STAGE05B_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Запреты

Запрещено:

```text
начинать Stage05B;
удалять repair rows;
удалять test/runtime rows напрямую;
использовать DELETE FROM;
использовать DROP TABLE;
использовать drop_all;
пересоздавать live DB;
запускать unsafe Core pytest;
оставлять доступный destructive reset endpoint;
использовать direct DB access из repairs-module;
git add .;
git add -A;
git add -u;
git reset;
git clean;
git rebase;
git commit --amend;
force push;
коммитить DB/backup/cache/temp.
```

Core tests:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

---

# 4. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05A_R2_FINAL_ACCEPTANCE_CLOSURE_PROMPT.md
```

Скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В отчёте:

```text
PROMPT_SEARCH_DONE
PROMPT_USED
PROMPT_SOURCE
PROMPT_LOCAL_COPY
PROMPT_SHA256
```

---

# 5. Preflight

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
docker compose config
```

Ожидаемый HEAD:

```text
cc9cf91
```

---

# 6. Backup and live DB profile

Создать backup:

```text
C:\tbootit-data-backups\stage05a-r2\<timestamp>\
```

Зафиксировать:

```text
BACKUP_PATH
BACKUP_SHA256
LIVE_DB_PATH
LIVE_DB_SHA256
LIVE_DB_SIZE
LIVE_DB_MTIME
```

Read-only профиль:

```text
PRODUCT_COUNT
PRODUCT_WITH_BARCODE_COUNT
SALE_COUNT
SALE_STATUS_COUNTS
SALE_TOTALS
CUSTOMER_COUNT
REPAIR_COUNT
REPAIR_HISTORY_COUNT
AUDIT_COUNT
```

---

# 7. Полная reconciliation таблица repairs

Вывести каждую строку `repair_orders`:

```text
id
number
status
customer_id
customer_name
customer_phone
device_type
brand
model
serial_number
reported_issue
accepted_at
created_at
closed_at
```

Для каждой строки дать:

```text
ORIGIN
CLASSIFICATION
EVIDENCE
OWNER_DATA_OR_TEST
VALID_NUMBER
VALID_STATUS
HISTORY_PRESENT
AUDIT_PRESENT
```

Обязательно классифицировать:

```text
ID 1
ID 2
ID 3
ID 4
ID 5
ID 6
ID 7
все IDs выше 7, если существуют
```

Допустимые классификации:

```text
legacy pre-Stage05A;
Stage05A migration test;
Stage05A runtime smoke;
Stage05A-R1 runtime path;
owner-created;
unknown.
```

Если происхождение нельзя доказать:

```text
UNKNOWN_ORIGIN
OWNER_DECISION_REQUIRED
```

Ничего не удалять.

---

# 8. История и audit reconciliation

Для каждого repair:

```text
число history rows;
первая history row;
последняя history row;
число audit events;
actions;
orphan status.
```

Проверить:

```text
нет orphan history;
нет history с invalid status;
created history присутствует;
terminal timestamps соответствуют status;
audit events не содержат секретов.
```

---

# 9. Full filter contract tests

Создать/расширить:

```text
core/tests/test_repairs_filters_complete.py
```

Отдельно проверить:

```text
q by number
q by customer_name
q by phone
q by device_type
q by brand
q by model
q by serial_number
q by reported_issue

status
priority
device_type
assigned_to
customer_phone
serial_number
date_from inclusive
date_to inclusive
date_from + date_to
page
page_size
sort accepted_at asc
sort accepted_at desc
invalid sort behavior
invalid page/page_size behavior
```

Для каждого test:

```text
создать минимум две различающиеся записи;
проверить inclusion;
проверить exclusion;
проверить total;
проверить pagination metadata.
```

---

# 10. Runtime filter matrix

Создать две явно тестовые записи:

```text
ТЕСТ Stage05A-R2 FILTER A
ТЕСТ Stage05A-R2 FILTER B
```

С разными:

```text
priority
device_type
assigned_to
phone
serial
accepted date
```

Проверить каждый query отдельно и записать:

```text
URL
HTTP status
matched IDs
excluded IDs
total
```

Не ограничиваться `q/status/phone`.

---

# 11. PATCH runtime contract

На открытом test repair проверить:

```text
PATCH allowed fields -> 200;
customer_name changed;
assigned_to changed;
priority changed;
updated_at changed;
number unchanged;
status unchanged;
history count unchanged;
repair.updated audit created.
```

Попытки передать:

```text
number
status
created_at
issued_at
closed_at
```

должны:

```text
быть отклонены 422/400
или гарантированно ignored согласно документированному contract.
```

Предпочтительно:

```text
extra fields forbidden.
```

На `issued` и `canceled`:

```text
PATCH -> 409.
```

---

# 12. History endpoint runtime

Проверить:

```text
GET /api/repairs/{id}/history
```

Ожидаемо:

```text
200;
chronological order;
created row;
all transition rows;
old_status/new_status корректны;
comments сохранены;
unknown repair -> 404.
```

---

# 13. Customer integration final contract

Провести полный аудит существующего Customer API и repair flow.

## 13.1 Existing customer

Создать/найти Customer:

```text
customer_id
name
phone
email
```

Создать repair с `customer_id`.

Проверить:

```text
RepairOrder.customer_id сохранён;
snapshot совпадает с Customer на момент создания.
```

## 13.2 Snapshot immutability

Изменить Customer через Core API.

Проверить:

```text
старый RepairOrder snapshot не изменился.
```

## 13.3 Same phone

Создать второй repair с тем же phone.

Проверить:

```text
новый Customer не создан;
использован существующий Customer;
дубликатов phone не появилось.
```

## 13.4 Conflict

Передать:

```text
customer_id существующего клиента;
другой customer_phone/customer_name.
```

Выбрать и документировать строгую политику:

```text
A. Customer ID является источником истины и snapshot берётся из Customer.
B. Конфликт отклоняется 409/422.
```

Не разрешать молчаливую подмену.

## 13.5 Unknown customer_id

Ожидаемо:

```text
404/422;
не создавать случайного Customer.
```

## 13.6 UI

Проверить, что repair form:

```text
либо позволяет выбрать существующего клиента;
либо честно обозначает snapshot-only flow.
```

Если UI выбора клиента отсутствует:

```text
не объявлять полную UI customer integration;
выдать CUSTOMER_UI_INTEGRATION_PENDING;
не расширять scope без отдельного этапа.
```

---

# 14. Preservation comparison with pre-Stage05A backup

Использовать backup:

```text
C:\tbootit-data-backups\stage05a\20260803-094534\host_data_db_technoreboot.db
```

Если путь существует.

Сравнить old/current:

## Products

```text
count
ID set
barcode map
name/title
price
status
quantity
storage_location
```

## Sales

```text
count
ID set
status
total_amount
payment_method
source/superseded links
```

## Organization settings

```text
all rows/values
```

## Customers

```text
pre-existing IDs
name
phone
email
```

Разрешённые различия:

```text
новые runtime sales/repairs/customers, созданные после backup;
новая repair schema/history/audit.
```

Нельзя скрывать различия.

Финальные verdict:

```text
EXISTING_PRODUCT_DATA_PRESERVED: true/false
EXISTING_SALES_DATA_PRESERVED: true/false
EXISTING_ORGANIZATION_DATA_PRESERVED: true/false
EXISTING_CUSTOMER_DATA_PRESERVED: true/false
LEGACY_REPAIR_DATA_PRESERVED: true/false
```

---

# 15. Destructive reset endpoint audit

Выполнить:

```powershell
git grep -n -I "reset\|drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module repairs-module admin-shell
```

Для каждого production match указать:

```text
FILE
LINE
ROUTE
METHOD
AUTH
ENV GUARD
PURPOSE
RISK
```

Если существует reset endpoint:

```text
удалить его из production router;
или сделать недоступным при обычном запуске;
или перенести только в tests/dev tooling вне app router.
```

Минимальные требования:

```text
normal docker compose profile -> endpoint отсутствует или 404;
нет unauthenticated destructive HTTP action;
нет GET destructive action;
нет Core startup destructive behavior.
```

Добавить test:

```text
core/tests/test_no_destructive_runtime_endpoints.py
```

Проверить известные пути:

```text
/api/reset
/api/admin/reset
/api/dev/reset
/reset
```

Ожидаемо:

```text
404/405;
live DB hash unchanged.
```

---

# 16. Test collection proof

Выполнить безопасно внутри изолированного container run:

```powershell
docker compose run --rm `
  -e DATABASE_URL=sqlite:////tmp/technoreboot_collect_only.db `
  core pytest --collect-only -q
```

Зафиксировать:

```text
TOTAL_COLLECTED
test_repairs_status_matrix_complete.py collected count
test_repairs_filters_complete.py collected count
test_no_destructive_runtime_endpoints.py collected count
```

Отдельно:

```powershell
docker compose run --rm `
  -e DATABASE_URL=sqlite:////tmp/technoreboot_status_matrix.db `
  core pytest -q core/tests/test_repairs_status_matrix_complete.py
```

Использовать фактический container workdir/path.

Объяснить, почему общий count был или остаётся `136`.

---

# 17. Full tests and live DB preservation

Перед tests:

```text
LIVE_DB_SHA256_BEFORE_TESTS
PRODUCT_COUNT_BEFORE_TESTS
SALE_COUNT_BEFORE_TESTS
CUSTOMER_COUNT_BEFORE_TESTS
REPAIR_COUNT_BEFORE_TESTS
HISTORY_COUNT_BEFORE_TESTS
```

Запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
```

После tests:

```text
LIVE_DB_SHA256_AFTER_TESTS
PRODUCT_COUNT_AFTER_TESTS
SALE_COUNT_AFTER_TESTS
CUSTOMER_COUNT_AFTER_TESTS
REPAIR_COUNT_AFTER_TESTS
HISTORY_COUNT_AFTER_TESTS
```

Ожидаемо:

```text
идентично до/после tests.
```

---

# 18. Safety scans

## Destructive calls

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests repairs-module
```

Разделить:

```text
PRODUCTION_EXECUTABLE_MATCHES
TEST_ASSERTION_STRING_MATCHES
```

Не заявлять `0 matches`, если строки находятся в test assertions.

## Repairs direct DB

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO\|UPDATE .* SET\|DELETE FROM" -- repairs-module/app
```

Ожидаемо:

```text
0
```

## DB/cache

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
```

## Secrets

```powershell
git grep -n -I "device_password\|password.*device\|unlock_code\|pin_code\|graphic_key" -- core repairs-module
```

---

# 19. Documentation

Создать:

```text
docs/stage05a_r2_final_acceptance_closure.md
reports/stage05a_r2_final_acceptance_closure_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report:

```text
# Stage05A-R2 Final Acceptance Closure Report

## STATUS
## WHY_R1_WAS_NOT_ACCEPTED
## PROMPT_DISCOVERY
## PREFLIGHT
## BACKUP
## LIVE_DB_PROFILE
## COMPLETE_REPAIR_ROW_RECONCILIATION
## ID_3_CLASSIFICATION
## ID_4_CLASSIFICATION
## HISTORY_RECONCILIATION
## AUDIT_RECONCILIATION
## FILTER_TEST_MATRIX
## FILTER_RUNTIME_MATRIX
## PATCH_RUNTIME
## HISTORY_ENDPOINT_RUNTIME
## CUSTOMER_INTEGRATION
## CUSTOMER_SNAPSHOT_IMMUTABILITY
## CUSTOMER_UI_VERDICT
## PRE_STAGE05A_BACKUP_COMPARISON
## PRESERVATION_VERDICTS
## RESET_ENDPOINT_AUDIT
## RESET_ENDPOINT_RUNTIME_PROOF
## TEST_COLLECTION_PROOF
## STATUS_MATRIX_FILE_PROOF
## FULL_TESTS
## LIVE_DB_TEST_ISOLATION
## SAFETY_SCANS
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_CHECK_GUIDE
## FINAL_STATUS
```

---

# 20. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/routers/repairs.py
git add core/app/routers/*
git add core/app/main.py
git add core/tests/test_repairs_filters_complete.py
git add core/tests/test_no_destructive_runtime_endpoints.py
git add core/tests/test_repairs_customer_integration.py

git add repairs-module/app/routers/repairs.py
git add repairs-module/app/templates/repair_new.html
git add repairs-module/tests/test_repairs_ui.py

git add docs/stage05a_r2_final_acceptance_closure.md
git add reports/stage05a_r2_final_acceptance_closure_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05A_R2_FINAL_ACCEPTANCE_CLOSURE_PROMPT.md
git add -f logs/2026-08-03.md
```

Не добавлять несуществующие файлы.

Коммит:

```powershell
git commit -m "Close Stage 05A repair acceptance gaps"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 21. Definition of Done

Готово только если:

```text
все repair IDs классифицированы;
ID 3 объяснён;
ID 4 объяснён;
нет скрытых unknown rows;
все list filters покрыты tests;
все list filters доказаны runtime;
PATCH contract доказан;
history endpoint доказан;
Customer reuse доказан;
Customer snapshot immutability доказана;
customer conflict policy определена;
unknown customer_id отклоняется;
UI customer integration честно классифицирована;
products сохранены;
sales сохранены;
organization settings сохранены;
legacy customers сохранены;
legacy repairs сохранены;
destructive reset endpoint отсутствует/недоступен;
runtime reset checks не меняют DB;
new test files реально collected;
status matrix file отдельно проходит;
Core safe tests PASS;
Inventory PASS;
Avito PASS;
Repairs PASS;
live DB не меняется от tests;
safety scans честны;
targeted commit;
push;
clean Git;
owner manual check required.
```

---

# 22. Owner check guide

В отчёте дать короткую проверку:

```text
1. Открыть http://localhost:8040/repairs
2. Проверить поиск и каждый фильтр
3. Создать repair с новым клиентом
4. Создать repair с существующим клиентом
5. Проверить отсутствие дубликата клиента
6. Изменить разрешённые поля
7. Проверить историю
8. Пройти один полный status path
9. Проверить terminal protection
10. Проверить, что destructive reset URL недоступны
```

---

# 23. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R2_FINAL_ACCEPTANCE_CLOSURE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05B_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R2_FINAL_ACCEPTANCE_CLOSURE_FAIL

BLOCKERS:
...
```
