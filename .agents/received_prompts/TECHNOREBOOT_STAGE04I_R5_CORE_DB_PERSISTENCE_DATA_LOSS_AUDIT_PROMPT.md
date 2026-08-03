# PROMPT — Техноребут / Stage04I-R5 Core DB Persistence and Data-Loss Audit

## Роль

Ты senior data-integrity auditor, Docker persistence engineer, FastAPI/Core DB engineer и Git release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — выяснить и устранить критическое расхождение данных между Stage04I-R3 и Stage04I-R4.

Новый функциональный этап не начинать.

---

# 1. Критическое расхождение

Stage04I-R3 сообщил:

```text
TOTAL_PRODUCTS: 66
WITH_BARCODE: 59
WITHOUT_BARCODE: 7
DUPLICATES: 0
```

Stage04I-R4 сообщил:

```text
TOTAL_PRODUCTS_BEFORE: 53
WITH_BARCODE_BEFORE: 1
WITHOUT_BARCODE_BEFORE: 52
DUPLICATES_BEFORE: 0
```

Между отчётами необъяснимо:

```text
исчезло 13 товаров
исчезло 58 barcode
изменилось состояние рабочей Core DB
```

Возможные причины:

```text
другая SQLite DB
неподключённый Docker volume
пересоздание контейнера с новой внутренней DB
тестовая DB вместо рабочей
переменная DATABASE_URL изменилась
runtime test cleanup удалил данные
seed перезаписал данные
```

Пока причина не доказана, Stage04I принимать нельзя.

---

# 2. Текущий статус

```text
STAGE04I_R4_BLOCKED_CORE_DB_STATE_INCONSISTENT_POSSIBLE_DATA_LOSS
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04I_R5_CORE_DB_PERSISTENCE_AUDITED_READY_FOR_OWNER_CHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Запреты

Запрещено:

```text
начинать следующий этап
снова запускать backfill до установления причины
удалять товары
очищать Core DB
перезаписывать DB
Base.metadata.drop_all/create_all
DROP TABLE
DELETE FROM без точечной доказанной необходимости
git reset
git clean
git rebase
force push
git add .
git add -A
git add -u
git commit --amend
коммитить runtime DB
```

До завершения read-only аудита:

```text
никаких write операций в Core DB
```

---

# 4. Prompt discovery

Найти точный файл:

```text
TECHNOREBOOT_STAGE04I_R5_CORE_DB_PERSISTENCE_DATA_LOSS_AUDIT_PROMPT.md
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
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04I_R5_CORE_DB_PERSISTENCE_DATA_LOSS_AUDIT_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_R5_CORE_DB_PERSISTENCE_DATA_LOSS_AUDIT_PROMPT.md `
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
git log --oneline -15
git diff --name-status
git diff --stat
docker compose ps
```

Ожидаемый HEAD:

```text
0c211abf932105d33ed29e4fb5824e7aca43cc7c
```

---

# 6. Docker persistence audit

Проверить:

```powershell
docker compose config
docker inspect technoreboot-core
docker volume ls
docker volume inspect <core-volume-name>
```

Зафиксировать:

```text
Core container name
DATABASE_URL
DB path inside container
volume name
volume mount source
volume mount destination
whether mount is named volume or bind mount
```

Проверить Docker Compose:

```text
core volumes
environment
working_dir
command
```

Ответить:

```text
Сохраняется ли DB после docker compose up --force-recreate?
```

---

# 7. Найти все потенциальные Core DB

Только read-only:

```powershell
Get-ChildItem C:\tbootit -Recurse -Force -ErrorAction SilentlyContinue |
Where-Object {
    $_.Name -match '\.(db|sqlite|sqlite3)$'
} |
Select-Object FullName,Length,LastWriteTime
```

Внутри Docker:

```powershell
docker compose exec -T core sh -lc "find / -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) 2>/dev/null"
```

Для каждого найденного DB-файла указать:

```text
path
size
modified time
product count
barcode count
sale count
```

Не копировать DB в Git.

---

# 8. Проверить DATABASE_URL во всех контекстах

Проверить:

```text
docker-compose.yml
core/app/config.py
core/app/database.py
.env.example
test fixtures
pytest configuration
startup scripts
```

Выполнить:

```powershell
docker compose exec -T core env | Select-String "DATABASE"
```

Проверить, что:

```text
runtime Core
pytest Core
служебные audit scripts
Inventory CoreClient
```

не используют разные DB.

---

# 9. Проверить историю контейнеров и volume

Зафиксировать:

```powershell
docker ps -a --filter name=technoreboot-core
docker inspect technoreboot-core --format "{{json .Mounts}}"
docker volume ls
```

Если volume создавался заново:

```text
объяснить почему
указать старый volume, если сохранился
```

Не удалять ни один volume.

---

# 10. Read-only content audit current DB

Через Core container:

```text
TOTAL_PRODUCTS
WITH_BARCODE
WITHOUT_BARCODE
DUPLICATES
TOTAL_SALES
MAX_PRODUCT_ID
MAX_SALE_ID
MIN_CREATED_AT
MAX_CREATED_AT
```

Также вывести:

```text
последние 20 product IDs
последние 20 sale IDs
```

---

# 11. Сопоставить с предыдущими runtime IDs

Из прошлых отчётов проверить наличие:

```text
Product 60
Product 65
Product 66
Sale 38
Sale 39
Sale 42
Sale 43
```

Для каждого:

```text
exists yes/no
status
barcode
created_at
```

Если отсутствуют:

```text
это прямое доказательство смены/сброса DB
```

---

# 12. Audit test isolation

Проверить fixtures:

```text
core/tests/conftest.py
inventory-sales-module tests
pytest env
temporary DB creation
dependency overrides
```

Ответить:

```text
Могли ли тесты удалить или заменить рабочую DB?
```

Проверить опасные конструкции:

```powershell
git grep -n -I "unlink\|remove\|drop_all\|create_all\|test.db\|tmp.*db\|DATABASE_URL" -- core inventory-sales-module
```

---

# 13. Audit startup migration and seed

Проверить:

```text
core/app/main.py
seed logic
startup events
migrate_db()
```

Ответить:

```text
может ли startup reset/reseed уменьшить product count?
может ли startup создать новую пустую DB?
```

---

# 14. Определить источник истины

После read-only аудита зафиксировать:

```text
AUTHORITATIVE_DB_PATH:
AUTHORITATIVE_VOLUME:
AUTHORITATIVE_TOTAL_PRODUCTS:
AUTHORITATIVE_TOTAL_SALES:
```

Источник истины должен быть именно persistent Core DB текущего проекта.

Если обнаружено несколько DB:

```text
не объединять автоматически
не удалять
описать каждую
```

---

# 15. Data recovery decision

## Сценарий A — старый volume найден

Если найден volume/DB с 66 товарами:

```text
не переключать молча
сформировать сравнение
предложить безопасный план восстановления
```

Если данные очевидно являются более полной рабочей DB и нет конфликтов:

```text
сделать резервную копию текущей DB
подключить правильный persistent volume
повторно проверить counts
```

Все действия подробно записать.

## Сценарий B — 66 товаров были только временными runtime test data

Доказать:

```text
какие именно 13 товаров были временными
кто и когда их удалил
каким разрешённым механизмом
почему 58 barcode исчезли
```

Если barcode исчезли из-за другой DB, всё равно исправить persistence.

## Сценарий C — данные реально потеряны

Остановиться:

```text
FINAL_STATUS = FAIL
BLOCKER = DATA LOSS
```

Не продолжать Stage04I.

---

# 16. Persistence repair

Если подтверждена проблема Docker volume/path:

```text
исправить docker-compose.yml/config
подключить persistent named volume или bind mount
```

Требование:

```text
docker compose up --build -d --force-recreate core
не меняет product count
не меняет barcode count
не меняет sale count
```

Добавить автоматический regression test или validation script.

---

# 17. Persistence runtime proof

Зафиксировать до recreate:

```text
PRODUCT_COUNT_BEFORE_RECREATE
BARCODE_COUNT_BEFORE_RECREATE
SALE_COUNT_BEFORE_RECREATE
DB_FINGERPRINT_BEFORE
```

Выполнить:

```powershell
docker compose up --build -d --force-recreate core
```

После:

```text
PRODUCT_COUNT_AFTER_RECREATE
BARCODE_COUNT_AFTER_RECREATE
SALE_COUNT_AFTER_RECREATE
DB_FINGERPRINT_AFTER
```

Ожидаемо:

```text
counts identical
fingerprint/identity consistent
```

Повторить второй раз.

---

# 18. Barcode final state

Только после установления правильной persistent DB:

```text
TOTAL_PRODUCTS
WITH_BARCODE
WITHOUT_BARCODE
DUPLICATES
```

Ожидаемо:

```text
WITH_BARCODE = TOTAL_PRODUCTS
WITHOUT_BARCODE = 0
DUPLICATES = 0
```

Если в правильной DB есть товары без barcode:

```text
запустить generate-missing один раз через Core API
```

Повторный запуск:

```text
generated=0
```

---

# 19. Sales integrity recheck

Проверить, что в authoritative DB существуют и корректны:

```text
completed
canceled
superseded
reissued
```

Проверить отчёты:

```text
canceled не входит
superseded не входит
reissued входит один раз
```

---

# 20. Full tests

После исправления:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Указать финальные фактические числа.

---

# 21. Safety scans

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
```

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 22. Documentation

Создать:

```text
docs/stage04i_r5_core_db_persistence_data_loss_audit.md
reports/stage04i_r5_core_db_persistence_data_loss_audit_report.md
```

Обновить:

```text
logs/2026-07-23.md
```

Report structure:

```text
# Stage04I-R5 Core DB Persistence and Data-Loss Audit Report

## STATUS

## INCONSISTENCY

R3:
R4:
Difference:

## PREFLIGHT

## DATABASE_URL_AUDIT

## DOCKER_VOLUME_AUDIT

## ALL_DISCOVERED_DATABASES

## CURRENT_DB_CONTENT

## HISTORICAL_IDS_CHECK

## TEST_ISOLATION_AUDIT

## STARTUP_AND_SEED_AUDIT

## ROOT_CAUSE

## AUTHORITATIVE_DB

## RECOVERY_ACTIONS

## PERSISTENCE_PROOF

Before recreate:
After recreate 1:
After recreate 2:

## FINAL_BARCODE_STATE

## SALES_INTEGRITY

## TESTS

Core:
Inventory:
Avito:

## SAFETY_SCAN

## FILES_CHANGED

## COMMIT

## PUSH

## FINAL_GIT_STATUS

## OWNER_CHECK_GUIDE

## FINAL_STATUS
```

---

# 23. Git

Только targeted add.

Возможные файлы:

```powershell
git add docker-compose.yml
git add core/app/config.py
git add core/app/database.py
git add core/tests/test_database_persistence_config.py
git add docs/stage04i_r5_core_db_persistence_data_loss_audit.md
git add reports/stage04i_r5_core_db_persistence_data_loss_audit_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04I_R5_CORE_DB_PERSISTENCE_DATA_LOSS_AUDIT_PROMPT.md
git add -f logs/2026-07-23.md
```

Коммит:

```powershell
git commit -m "Audit and secure Core database persistence"
git push origin main
```

После push:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 24. Definition of Done

Готово только если:

```text
причина 66 -> 53 доказана
причина 59 barcode -> 1 доказана
authoritative DB определена
никакие реальные данные не потеряны или потеря явно зафиксирована
Docker persistence доказана двумя recreates
product count стабилен
barcode count стабилен
sale count стабилен
WITHOUT_BARCODE = 0
DUPLICATES = 0
sales statuses сохранены
Core tests PASS
Inventory tests PASS
Avito tests PASS
safety scans clean
targeted commit
push
clean Git
owner manual check required
```

---

# 25. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R5_CORE_DB_PERSISTENCE_AUDITED_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если подтверждена потеря данных или источник истины не определён:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R5_CORE_DB_PERSISTENCE_DATA_LOSS_AUDIT_FAIL

BLOCKERS:
...
```
