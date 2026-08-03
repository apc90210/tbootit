# PROMPT — Техноребут / Stage05A-R1 Acceptance Gaps, Status Matrix and Live DB Audit

## Роль

Ты senior FastAPI engineer, domain workflow auditor, SQLite migration auditor, Jinja2 UX developer, Docker runtime validator и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — выполнить точечный acceptance-аудит и исправление Stage05A.

Новый этап Stage05B не начинать.

---

# 1. Почему Stage05A пока не принят

Основной модуль ремонтов создан и тесты проходят, но итоговый отчёт не доказывает несколько обязательных требований Stage05A.

## 1.1. Описанная матрица переходов неполная

В отчёте указано:

```text
received -> diagnostics, canceled

diagnostics / waiting_customer / waiting_parts
-> in_repair, unrepairable, canceled

in_repair -> ready, unrepairable, canceled

ready -> issued
```

Но исходный Stage05A требовал точную матрицу:

```text
received:
  diagnostics
  canceled

diagnostics:
  waiting_customer
  waiting_parts
  in_repair
  unrepairable
  canceled

waiting_customer:
  diagnostics
  waiting_parts
  in_repair
  unrepairable
  canceled

waiting_parts:
  waiting_customer
  in_repair
  unrepairable
  canceled

in_repair:
  waiting_customer
  waiting_parts
  ready
  unrepairable
  canceled

ready:
  in_repair
  issued

unrepairable:
  issued
  canceled

issued:
  terminal

canceled:
  terminal
```

Нужно проверить фактический код. Если переходы отсутствуют — исправить.

---

## 1.2. Не доказаны обязательные Core endpoints

В итоговом отчёте нет свежих runtime-доказательств:

```text
GET /api/repairs/by-number/{number}
GET /api/repairs/options
```

Также не доказано полное поведение:

```text
PATCH /api/repairs/{id}
GET /api/repairs/{id}/history
```

---

## 1.3. Не доказаны все обязательные фильтры

Stage05A требовал:

```text
q
status
priority
device_type
assigned_to
date_from
date_to
customer_phone
serial_number
page
page_size
sort
```

В отчёте упомянуты только:

```text
q
status
device_type
priority
pagination
```

Нужно проверить и доказать все фильтры.

---

## 1.4. В UI не доказаны все статусные фильтры

В отчёте перечислены:

```text
Принят
Диагностика
В ремонте
Готов
Выдан
Отменён
```

Но отсутствуют обязательные:

```text
Ожидает клиента
Ожидает запчасти
Ремонт невозможен
```

---

## 1.5. Не доказана интеграция с существующей моделью клиентов

Stage05A требовал:

```text
аудит существующего Customer;
использование customer_id при выборе существующего клиента;
создание клиента через Core API при необходимости;
snapshot имени/телефона/email в RepairOrder;
никакой локальной таблицы клиентов в repairs-module.
```

Итоговый отчёт не показывает результат этого аудита.

---

## 1.6. Не доказана целостность legacy repair_orders

До Stage05A таблица `repair_orders` уже существовала.

Отчёт сообщает:

```text
добавлено 24 столбца;
runtime repair R-20260803-0002 имеет ID 4.
```

Нужно объяснить:

```text
какие строки существовали до миграции;
какие строки появились во время Stage05A;
почему runtime-запись имеет ID 4 и номер 0002;
нет ли частично созданных или тестовых записей;
не потеряны ли legacy repair rows;
все ли legacy строки получили валидные значения.
```

---

## 1.7. Не приведено полное доказательство live DB preservation

Есть backup и общая фраза:

```text
Live DB preserved
```

Но итоговый отчёт должен отдельно показать:

```text
A. Миграция ожидаемо изменила schema/hash.
B. Products и sales не были потеряны.
C. Safe tests после миграции не изменили live DB.
D. Runtime smoke ожидаемо создал repair/history/audit rows.
```

---

## 1.8. Не приведён обязательный финальный status block

В итоговом сообщении отсутствует точный блок:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_REPAIR_INTAKE_REGISTRY_MVP_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 2. Текущий статус

```text
STAGE05A_BLOCKED_ACCEPTANCE_GAPS_AND_INCOMPLETE_STATUS_MATRIX_EVIDENCE
```

Целевой статус:

```text
TECHNOREBOOT_STAGE05A_R1_ACCEPTANCE_GAPS_REPAIRED_READY_FOR_OWNER_CHECK
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
добавлять диагностику, смету, работы, запчасти или оплату;
удалять legacy repairs;
удалять runtime test repairs напрямую;
использовать DELETE FROM;
использовать DROP TABLE;
использовать drop_all;
пересоздавать live DB;
запускать docker compose exec core pytest;
использовать direct DB access из repairs-module;
git add .;
git add -A;
git add -u;
git reset;
git clean;
git rebase;
git commit --amend;
force push;
коммитить DB, backup, cache или temp.
```

Core tests запускать только:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

---

# 4. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05A_R1_ACCEPTANCE_GAPS_STATUS_MATRIX_LIVE_DB_AUDIT_PROMPT.md
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
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE05A_R1_ACCEPTANCE_GAPS_STATUS_MATRIX_LIVE_DB_AUDIT_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE05A_R1_ACCEPTANCE_GAPS_STATUS_MATRIX_LIVE_DB_AUDIT_PROMPT.md `
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
410c9e8
```

Если фактический HEAD другой — указать его.

---

# 6. Live DB identity and backup

Определить:

```text
Core DATABASE_URL
container live DB path
host bind-mount path
SHA256
file size
mtime
```

Создать новую backup-копию до R1:

```text
C:\tbootit-data-backups\stage05a-r1\<timestamp>\
```

Записать:

```text
BACKUP_PATH
BACKUP_SHA256
```

Не коммитить backup.

---

# 7. Полный профиль live DB до изменений

Read-only снять:

```text
PRODUCT_COUNT
PRODUCT_WITH_BARCODE_COUNT
SALE_COUNT
SALE_STATUS_COUNTS
REPAIR_COUNT
REPAIR_HISTORY_COUNT
AUDIT_COUNT
```

Вывести все `repair_orders`:

```text
id
number
status
customer_id
customer_name
customer_phone
device_type
reported_issue
created_at
accepted_at
closed_at
```

Вывести repair status history:

```text
repair_id
old_status
new_status
comment
changed_at
```

Классифицировать каждую существующую repair row:

```text
legacy до Stage05A;
runtime Stage05A;
неудачная/частичная попытка;
неизвестное происхождение.
```

Ничего не удалять.

---

# 8. Legacy migration audit

Проверить:

```text
все legacy rows сохранены;
number уникален и не null;
status находится в allowlist;
customer_name/phone/device_type/reported_issue не нарушают schema;
timestamps валидны;
нет duplicate number;
нет orphan history;
нет history для несуществующего repair;
индексы существуют;
повторный migration startup не меняет rows/schema.
```

Снять:

```text
REPAIR_COUNT_BEFORE_RESTART
REPAIR_COUNT_AFTER_RESTART
SCHEMA_BEFORE_RESTART
SCHEMA_AFTER_RESTART
```

Ожидаемо:

```text
идемпотентно;
0 новых столбцов/индексов при повторном запуске;
0 потерянных строк.
```

---

# 9. Точная статусная матрица

Найти фактическую константу/сервис переходов.

Матрица должна быть точно такой:

```python
{
    "received": {
        "diagnostics",
        "canceled",
    },
    "diagnostics": {
        "waiting_customer",
        "waiting_parts",
        "in_repair",
        "unrepairable",
        "canceled",
    },
    "waiting_customer": {
        "diagnostics",
        "waiting_parts",
        "in_repair",
        "unrepairable",
        "canceled",
    },
    "waiting_parts": {
        "waiting_customer",
        "in_repair",
        "unrepairable",
        "canceled",
    },
    "in_repair": {
        "waiting_customer",
        "waiting_parts",
        "ready",
        "unrepairable",
        "canceled",
    },
    "ready": {
        "in_repair",
        "issued",
    },
    "unrepairable": {
        "issued",
        "canceled",
    },
    "issued": set(),
    "canceled": set(),
}
```

Не расширять матрицу без отдельного решения владельца.

---

# 10. Core tests для каждого перехода

Создать/расширить:

```text
core/tests/test_repairs_status_matrix_complete.py
```

Проверить каждый разрешённый переход отдельно.

Также проверить запрещённые примеры:

```text
received -> ready
received -> issued
diagnostics -> issued
waiting_parts -> diagnostics
ready -> canceled
unrepairable -> ready
issued -> diagnostics
canceled -> diagnostics
```

Ожидаемо:

```text
разрешённые -> 200;
запрещённые -> 409;
history создаётся только при успешном переходе;
при 409 status/history не меняются.
```

---

# 11. Runtime status paths

Создать отдельные явно тестовые repairs и проверить пути.

## Path A

```text
received
-> diagnostics
-> waiting_customer
-> diagnostics
-> waiting_parts
-> waiting_customer
-> in_repair
-> waiting_parts
-> in_repair
-> ready
-> in_repair
-> ready
-> issued
```

## Path B

```text
received
-> diagnostics
-> unrepairable
-> issued
```

## Path C

```text
received
-> canceled
```

Оставить их с явной маркировкой:

```text
ТЕСТ Stage05A-R1 PATH A
ТЕСТ Stage05A-R1 PATH B
ТЕСТ Stage05A-R1 PATH C
```

Не удалять напрямую.

---

# 12. Core API contract audit

Свежо проверить:

```text
POST   /api/repairs
GET    /api/repairs
GET    /api/repairs/{id}
PATCH  /api/repairs/{id}
POST   /api/repairs/{id}/status
GET    /api/repairs/{id}/history
GET    /api/repairs/by-number/{number}
GET    /api/repairs/options
```

Для каждого:

```text
request
HTTP status
response keys
error behavior
```

Если endpoint отсутствует — реализовать и протестировать.

---

# 13. Options endpoint

Ожидаемый response:

```json
{
  "statuses": [
    {"value": "received", "label": "Принят"}
  ],
  "priorities": [
    {"value": "normal", "label": "Обычный"},
    {"value": "urgent", "label": "Срочный"}
  ],
  "device_types": [
    "Ноутбук",
    "Системный блок",
    "Моноблок",
    "Монитор",
    "Принтер",
    "МФУ",
    "Планшет",
    "Телефон",
    "Сетевое оборудование",
    "Комплектующее",
    "Другое"
  ]
}
```

Допустима совместимая структура, но UI должен использовать Core values.

---

# 14. GET list filters

Проверить и при необходимости реализовать:

```text
q
status
priority
device_type
assigned_to
date_from
date_to
customer_phone
serial_number
page
page_size
sort
```

Тесты:

```text
q по number;
q по customer_name;
q по phone;
q по device_type;
q по brand/model;
q по serial_number;
q по reported_issue;

status exact;
priority exact;
device_type exact;
assigned_to exact;
customer_phone exact/contains согласно документированному контракту;
serial_number exact/contains согласно контракту;
date_from inclusive;
date_to inclusive;
date range;
pagination;
page_size limit;
sort accepted_at desc;
sort accepted_at asc;
unknown sort rejected или безопасно заменён.
```

---

# 15. By-number endpoint

Проверить:

```text
GET /api/repairs/by-number/R-YYYYMMDD-XXXX
```

Ожидаемо:

```text
200 и точная запись;
404 для неизвестного number;
поиск не зависит от ID;
number immutable.
```

---

# 16. PATCH contract

Проверить:

```text
разрешённые поля меняются;
number не меняется;
status не меняется;
timestamps не принимаются;
issued/canceled не редактируются;
audit repair.updated создаётся;
history не создаётся от обычного PATCH.
```

---

# 17. Customer integration audit

Найти существующие:

```text
Customer model
customer API
customer UI/API usage в sales
```

Выдать честный вывод:

```text
A. Customer integration полностью подключена.
B. Customer model есть, но repair UI использует только snapshot.
C. Customer model отсутствует/недостаточна.
```

Если Customer model/API существуют и пригодны:

```text
repair_new должен позволять найти/выбрать существующего клиента;
customer_id передаётся в Core;
snapshot name/phone/email сохраняется;
при изменении Customer snapshot старого ремонта не меняется.
```

Если UI выбора клиента не входит в реально существующую инфраструктуру:

```text
не создавать большой новый клиентский модуль;
задокументировать gap;
оставить customer_id nullable;
создать минимальный API test snapshot behavior;
не объявлять интеграцию выполненной без доказательства.
```

---

# 18. UI status filters

На `/repairs` должны быть фильтры:

```text
Все
Приняты
Диагностика
Ожидают клиента
Ожидают запчасти
В ремонте
Готовы
Ремонт невозможен
Выданы
Отменены
```

Каждый фильтр:

```text
передаёт правильный status;
показывает правильные records;
не показывает records других статусов;
сохраняет q/другие фильтры при необходимости.
```

---

# 19. UI form options

Форма создания и редактирования должна использовать согласованные values:

```text
device types;
priority;
assigned_to;
available status actions.
```

Не должно быть расхождения между Core allowlist и HTML hardcode.

---

# 20. UI runtime checks

Свежо проверить:

```text
GET /repairs
GET /repairs/new
POST /repairs/new
GET /repairs/{id}
GET /repairs/{id}/edit
POST /repairs/{id}/edit
POST /repairs/{id}/status
```

Проверить:

```text
русские ошибки;
нет raw JSON/Pydantic;
введённые поля сохраняются при ошибке;
allowed next statuses корректны;
history timeline полная;
terminal status скрывает edit/status actions.
```

---

# 21. Test-isolation proof

После завершения runtime-сценариев снять:

```text
LIVE_DB_SHA256_BEFORE_TESTS
PRODUCT_COUNT_BEFORE_TESTS
SALE_COUNT_BEFORE_TESTS
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

После:

```text
LIVE_DB_SHA256_AFTER_TESTS
PRODUCT_COUNT_AFTER_TESTS
SALE_COUNT_AFTER_TESTS
REPAIR_COUNT_AFTER_TESTS
HISTORY_COUNT_AFTER_TESTS
```

Ожидаемо:

```text
все значения до/после tests идентичны.
```

---

# 22. Migration preservation proof

Отдельно сравнить pre-Stage05A backup и текущую DB:

```text
products по ID/count;
sales по ID/count/status;
organization settings;
customers;
product barcodes;
sale totals.
```

Schema repair tables ожидаемо отличается.

Не требовать одинакового SHA256 между backup и текущей DB, потому что миграция и runtime repairs законно изменили DB.

Вывод должен быть:

```text
EXISTING_PRODUCT_DATA_PRESERVED: true/false
EXISTING_SALES_DATA_PRESERVED: true/false
LEGACY_REPAIR_DATA_PRESERVED: true/false
```

---

# 23. Audit events

Проверить для runtime repairs:

```text
repair.created
repair.updated
repair.status_changed
repair.issued
repair.canceled
```

Проверить:

```text
нет паролей/PIN;
нет полного сырого request body;
repair_id и status присутствуют;
число событий соответствует действиям.
```

---

# 24. Repairs-module direct DB scan

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO\|UPDATE .* SET\|DELETE FROM" -- repairs-module
```

Ожидаемо:

```text
0 production matches.
```

Тестовые строки запрета нужно отдельно объяснить.

---

# 25. Destructive scan

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests repairs-module
```

Если regression test содержит буквальную запрещённую строку:

```text
вывести точные matches;
доказать, что это только source scan assertion;
production executable matches = 0.
```

Не писать просто `0 matches`, если фактически есть test-string matches.

---

# 26. Secrets scan

```powershell
git grep -n -I "device_password\|password.*device\|unlock_code\|pin_code\|graphic_key" -- core repairs-module
```

Допустимы только тестовые проверки запрета.

Также:

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 27. DB/cache scan

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
```

Ожидаемо:

```text
0 tracked runtime/test DB files.
```

---

# 28. Документация

Создать:

```text
docs/stage05a_r1_acceptance_gaps_status_matrix_live_db_audit.md
reports/stage05a_r1_acceptance_gaps_status_matrix_live_db_audit_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report:

```text
# Stage05A-R1 Acceptance Gaps and Live DB Audit Report

## STATUS
## WHY_STAGE05A_WAS_NOT_ACCEPTED
## PROMPT_DISCOVERY
## PREFLIGHT
## LIVE_DB_IDENTITY
## BACKUP
## LEGACY_REPAIR_RECONCILIATION
## MIGRATION_IDEMPOTENCY
## PRODUCT_AND_SALES_PRESERVATION
## STATUS_MATRIX_BEFORE
## STATUS_MATRIX_AFTER
## ALLOWED_TRANSITION_TESTS
## REJECTED_TRANSITION_TESTS
## CORE_ENDPOINTS
## OPTIONS_ENDPOINT
## LIST_FILTERS
## BY_NUMBER
## PATCH_CONTRACT
## CUSTOMER_INTEGRATION_VERDICT
## UI_STATUS_FILTERS
## UI_FORMS
## RUNTIME_PATH_A
## RUNTIME_PATH_B
## RUNTIME_PATH_C
## AUDIT_EVENTS
## SAFE_TEST_PRESERVATION
## TESTS
## SAFETY_SCANS
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_CHECK_GUIDE
## FINAL_STATUS
```

---

# 29. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/routers/repairs.py
git add core/app/schemas.py
git add core/app/services/repair_migration.py
git add core/tests/test_repairs_status_matrix_complete.py
git add core/tests/test_repairs_search_filters.py
git add core/tests/test_repairs_create.py

git add repairs-module/app/core_client.py
git add repairs-module/app/routers/repairs.py
git add repairs-module/app/templates/repairs_list.html
git add repairs-module/app/templates/repair_new.html
git add repairs-module/app/templates/repair_detail.html
git add repairs-module/app/templates/repair_edit.html
git add repairs-module/tests/test_repairs_ui.py
git add repairs-module/tests/test_repairs_filters.py

git add docs/stage05a_r1_acceptance_gaps_status_matrix_live_db_audit.md
git add reports/stage05a_r1_acceptance_gaps_status_matrix_live_db_audit_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05A_R1_ACCEPTANCE_GAPS_STATUS_MATRIX_LIVE_DB_AUDIT_PROMPT.md
git add -f logs/2026-08-03.md
```

Не добавлять несуществующие файлы.

Коммит:

```powershell
git commit -m "Complete Stage 05A repair workflow acceptance gaps"
git push origin main
```

После push:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

Worktree должен быть чистым.

---

# 30. Definition of Done

Готово только если:

```text
точная статусная матрица реализована;
каждый разрешённый переход протестирован;
ключевые запрещённые переходы дают 409;
waiting_customer работает;
waiting_parts работает;
unrepairable работает;
ready -> in_repair работает;
unrepairable -> issued/canceled работает;
все обязательные Core endpoints существуют;
by-number доказан;
options доказан;
все обязательные list filters доказаны;
в UI есть все статусные фильтры;
customer integration честно классифицирована;
legacy repair rows полностью классифицированы;
partial/test rows не скрыты;
migration идемпотентна;
products и sales сохранены;
safe tests не меняют live DB;
audit events доказаны;
Core safe tests PASS;
Inventory tests PASS;
Avito tests PASS;
Repairs tests PASS;
safety scans честны;
targeted commit;
push;
clean Git;
owner manual check required.
```

---

# 31. Owner check guide

В отчёте дать проверку:

```text
1. Открыть http://localhost:8040/repairs
2. Проверить все 9 status-фильтров
3. Принять новый ремонт
4. Найти его по номеру
5. Найти его по телефону
6. Найти его по серийному номеру
7. Открыть карточку и изменить разрешённое поле
8. Проверить путь:
   Принят -> Диагностика -> Ожидает клиента
   -> Ожидает запчасти -> В ремонте -> Готов -> Выдан
9. Проверить историю
10. Убедиться, что после «Выдан» редактирование заблокировано
```

---

# 32. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R1_ACCEPTANCE_GAPS_REPAIRED_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05B_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R1_ACCEPTANCE_GAPS_REPAIR_FAIL

BLOCKERS:
...
```
