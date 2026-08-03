# PROMPT — Техноребут / Stage04I-R6 Data Recovery and Test Isolation Hardening

## Роль

Ты senior data-recovery engineer, SQLite forensic auditor, Docker persistence engineer, FastAPI test-isolation architect и release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — выполнить судебный аудит потери данных, найти все доступные копии Core DB, полностью объяснить расхождение данных и окончательно исключить возможность запуска destructive pytest против рабочей базы.

Новый функциональный этап не начинать.

---

# 1. Почему Stage04I-R5 не принят

Stage04I-R5 установил критический факт:

```text
pytest выполнил Base.metadata.drop_all(bind=engine)
против рабочей базы:
/data/db/technoreboot.db
```

После этого тесты создали seed-данные.

Следовательно:

```text
рабочая база была полностью удалена и создана заново;
текущее содержимое не является доказанно прежним рабочим набором данных.
```

При этом отчёт утверждает:

```text
No real user/owner inventory was lost.
```

Это утверждение не доказано.

Дополнительное противоречие:

```text
Stage04I-R3: 66 товаров
Stage04I-R4: 53 товара
Разница: 13 товаров
```

Но R5 объясняет только временные товары IDs 61–66. Это 6 товаров.

Не объяснены ещё 7 товаров.

Также найден второй DB-файл:

```text
/app/technoreboot.db
```

Но в отчёте отсутствуют его hash, размер, время изменения, counts и сравнение с `/data/db/technoreboot.db`.

Ещё одно противоречие:

```text
R5 утверждает destructive SQL scan = 0 matches.
```

Но root cause найден в tracked test-файле с `Base.metadata.drop_all(bind=engine)`. Если файл не изменён, scan не мог честно вернуть 0 matches.

---

# 2. Текущий статус

```text
STAGE04I_R5_BLOCKED_DATA_LOSS_NOT_FULLY_RECONCILED_AND_DESTRUCTIVE_TEST_REMAINS
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04I_R6_DATA_RECOVERY_AND_TEST_ISOLATION_HARDENED_READY_FOR_OWNER_DECISION
```

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Главный принцип

До создания резервных копий запрещены любые действия, способные изменить Core DB.

Сначала:

```text
freeze
backup
hash
inventory
compare
```

Только после этого допускаются исправления тестов.

---

# 4. Строгие запреты

Запрещено:

```text
запускать pytest до завершения backup и forensic inventory
запускать barcode backfill
создавать runtime test products
создавать runtime sales
удалять товары или продажи
удалять DB-файлы или Docker volumes
перезаписывать /data/db/technoreboot.db
перезаписывать /app/technoreboot.db
выполнять drop_all / DROP TABLE / массовый DELETE
делать blind restore
объединять DB автоматически
git reset
git clean
rebase
force push
git commit --amend
git add .
git add -A
git add -u
коммитить DB или backup в Git
```

---

# 5. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE04I_R6_DATA_RECOVERY_TEST_ISOLATION_HARDENING_PROMPT.md
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
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04I_R6_DATA_RECOVERY_TEST_ISOLATION_HARDENING_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_R6_DATA_RECOVERY_TEST_ISOLATION_HARDENING_PROMPT.md `
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

# 6. Preflight без запуска тестов

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
d96107c035dde71af6809f3fa0c36687854045a6
```

---

# 7. Немедленный immutable backup

Создать каталог вне Git:

```text
C:\tbootit-data-recovery\stage04i-r6\<timestamp>\
```

Скопировать туда:

```text
C:\tbootit\data\db\technoreboot.db
```

Из контейнера сохранить отдельно:

```text
/data/db/technoreboot.db
/app/technoreboot.db
```

Имена:

```text
host_data_db_technoreboot.db
container_data_db_technoreboot.db
container_app_technoreboot.db
```

Для каждого зафиксировать:

```text
path
size
LastWriteTime
SHA256
```

Не добавлять recovery-каталог в Git.

---

# 8. Найти все потенциальные DB и backup

На хосте:

```powershell
Get-ChildItem `
  C:\tbootit,C:\Users\Apc `
  -Recurse `
  -Force `
  -ErrorAction SilentlyContinue |
Where-Object {
    $_.Name -match '\.(db|sqlite|sqlite3|bak|backup)$'
} |
Select-Object FullName,Length,LastWriteTime
```

Проверить:

```text
C:\tbootit\data
C:\tbootit\backups
C:\tbootit\reports
C:\tbootit\logs
C:\Users\Apc\Downloads
Docker volumes
Docker container writable layers
Windows Previous Versions / File History, если доступны
```

В Docker:

```powershell
docker volume ls
docker ps -a
docker compose exec -T core sh -lc "find / -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.bak' \) 2>/dev/null"
```

Ничего не удалять.

---

# 9. Forensic profile каждой DB

Для каждой SQLite DB создать read-only профиль через:

```python
sqlite3.connect(f"file:{path}?mode=ro", uri=True)
```

Зафиксировать:

```text
FILE_PATH
SHA256
SIZE
MTIME
TABLES
TOTAL_PRODUCTS
WITH_BARCODE
WITHOUT_BARCODE
DUPLICATES
MAX_PRODUCT_ID
TOTAL_SALES
MAX_SALE_ID
SALES_BY_STATUS
TOTAL_AUDIT_LOGS
TOTAL_PRODUCT_EVENTS
MIN_CREATED_AT
MAX_CREATED_AT
```

Никаких migrations и create_all.

---

# 10. Обязательное сравнение DB

Сравнить:

```text
/data/db/technoreboot.db
/app/technoreboot.db
C:\tbootit\data\db\technoreboot.db
все найденные backups
```

Сформировать таблицу:

```text
DB
Products
Barcodes
Sales
Max product ID
Max sale ID
Hash
Likely origin
```

Ответить:

```text
Что такое /app/technoreboot.db?
Когда она создана?
Содержит ли она данные до destructive pytest?
Может ли она быть источником восстановления?
```

---

# 11. Полное объяснение 66 → 53

Проверить Product IDs:

```text
54
55
56
57
58
59
60
61
62
63
64
65
66
```

Для каждой DB вывести:

```text
id
title
sku
status
barcode
quantity
storage_location
created_at
updated_at
```

Классифицировать каждый ID:

```text
runtime validation
pytest seed
возможный реальный товар
не найден
неизвестное происхождение
```

Для каждого ID нужна доказательная классификация.

---

# 12. Полное объяснение sales-разницы

Проверить Sale IDs:

```text
34–43
```

Для каждой DB вывести:

```text
id
status
total_amount
payment_method
created_at
source_sale_id
superseded_by_sale_id
cancel_reason
```

Классифицировать каждую продажу.

---

# 13. Audit logs и execution logs

Проверить:

```text
audit_logs
product_events
stock_movements
logs/2026-07-22.md
logs/2026-07-23.md
reports Stage04H/Stage04I
agent execution logs, если доступны
```

Найти доказательства создания Products 54–66 и Sales 34–43. Сопоставить timestamps.

---

# 14. Честный data-loss verdict

Допустимы только:

## Verdict A — данные восстановимы

Найдена более полная DB/backup. Не восстанавливать автоматически. Создать comparison и owner-safe restore plan.

## Verdict B — все исчезнувшие записи доказанно временные

Для всех 13 товаров и sales есть доказательства test/runtime происхождения. Только тогда можно писать, что owner data не потеряны.

## Verdict C — доказательств недостаточно

Если хотя бы одна запись не классифицирована:

```text
DATA LOSS CANNOT BE EXCLUDED
```

Нельзя утверждать, что реальные данные не потеряны.

---

# 15. Удалить destructive test behavior

Найти:

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM\|unlink\|os.remove\|Path.*unlink" -- core inventory-sales-module
```

Особенно проверить:

```text
core/tests/test_product_filter_options_cascading.py
```

Требование:

```text
ни один tracked test не вызывает Base.metadata.drop_all()
ни один test не использует live app.database.engine
```

Исправить destructive fixtures через temporary isolated DB, transaction rollback или dependency override.

Не оставлять `drop_all` даже для test DB: project gate считает destructive DB calls blocker.

---

# 16. Hard test isolation

`core/tests/conftest.py` должен:

```text
создавать уникальную временную SQLite DB
делать это до импорта app.database
никогда не использовать /data/db/technoreboot.db
никогда не использовать ./technoreboot.db
не оставлять test_core_isolated.db
удалять только собственный временный файл
```

Использовать:

```text
tempfile.TemporaryDirectory
pytest tmp_path_factory
```

Добавить hard fail:

```python
assert "/data/db/technoreboot.db" not in str(engine.url)
```

---

# 17. Безопасный способ запуска Core tests

Создать:

```text
scripts/test_core_safe.ps1
```

Пример:

```powershell
docker compose run --rm `
  -e DATABASE_URL=sqlite:////tmp/technoreboot_core_tests.db `
  core pytest
```

Требования:

```text
test DB находится в /tmp
test process не пишет в /data/db
до/после live DB hash и counts одинаковы
```

---

# 18. Regression tests isolation

Добавить/обновить:

```text
core/tests/test_database_persistence_config.py
core/tests/test_no_destructive_test_database_calls.py
```

Проверить:

```text
engine path не live
SessionLocal не live
test files не содержат drop_all
test files не содержат DROP TABLE
test files не содержат DELETE FROM
Core test run не меняет live DB
```

---

# 19. Live DB preservation proof

До safe tests:

```text
SHA256_BEFORE
PRODUCTS_BEFORE
BARCODES_BEFORE
SALES_BEFORE
AUDIT_BEFORE
LAST_WRITE_BEFORE
```

Запустить только safe test command.

После:

```text
SHA256_AFTER
PRODUCTS_AFTER
BARCODES_AFTER
SALES_AFTER
AUDIT_AFTER
LAST_WRITE_AFTER
```

Ожидаемо live DB не изменена.

---

# 20. Docker recreate proof

После safe tests дважды выполнить:

```powershell
docker compose up --build -d --force-recreate core
```

После каждого проверить:

```text
products unchanged
barcodes unchanged
sales unchanged
```

---

# 21. Barcode и sales state

В доказанной authoritative DB:

```text
TOTAL_PRODUCTS
WITH_BARCODE
WITHOUT_BARCODE
DUPLICATES
```

Ожидаемо:

```text
WITHOUT_BARCODE = 0
DUPLICATES = 0
```

Проверить статусы продаж и отчёт:

```text
completed включены
reissued включены ровно один раз
canceled исключены
superseded исключены
```

---

# 22. Fresh tests

После hardening:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Не использовать обычный `docker compose exec core pytest`, пока он не доказан безопасным.

---

# 23. Честные safety scans

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests
```

Ожидаемо 0 matches.

Также:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

Не писать 0 matches, если output содержит match.

---

# 24. Документация

Создать:

```text
docs/stage04i_r6_data_recovery_test_isolation_hardening.md
reports/stage04i_r6_data_recovery_test_isolation_hardening_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report:

```text
# Stage04I-R6 Data Recovery and Test Isolation Hardening Report

## STATUS
## WHY_R5_WAS_REJECTED
## PREFLIGHT
## IMMUTABLE_BACKUPS
## ALL_DISCOVERED_DATABASES
## DATABASE_FORENSIC_PROFILES
## DATASET_COMPARISON
## PRODUCT_IDS_54_TO_66_RECONCILIATION
## SALE_IDS_34_TO_43_RECONCILIATION
## DATA_LOSS_VERDICT
## ROOT_CAUSE
## DESTRUCTIVE_TEST_SCAN_BEFORE
## TEST_ISOLATION_REPAIR
## DESTRUCTIVE_TEST_SCAN_AFTER
## SAFE_TEST_COMMAND
## LIVE_DB_PRESERVATION_PROOF
## DOCKER_RECREATE_PROOF
## AUTHORITATIVE_DB
## FINAL_BARCODE_STATE
## SALES_INTEGRITY
## FINAL_TESTS
## SAFETY_SCAN
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_DECISION_REQUIRED
## FINAL_STATUS
```

---

# 25. Git

Только targeted add.

```powershell
git add core/tests/conftest.py
git add core/tests/test_product_filter_options_cascading.py
git add core/tests/test_database_persistence_config.py
git add core/tests/test_no_destructive_test_database_calls.py
git add scripts/test_core_safe.ps1
git add docs/stage04i_r6_data_recovery_test_isolation_hardening.md
git add reports/stage04i_r6_data_recovery_test_isolation_hardening_report.md
git add logs/2026-08-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04I_R6_DATA_RECOVERY_TEST_ISOLATION_HARDENING_PROMPT.md
```

Не добавлять DB/backups.

Коммит:

```powershell
git commit -m "Harden Core test isolation and audit database recovery"
git push origin main
```

После push:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 26. Definition of Done

```text
все DB-копии сохранены и захешированы
/data/db и /app DB исследованы
разница 66 -> 53 полностью объяснена
все 13 Product IDs классифицированы
Sales 34–43 классифицированы
data-loss verdict доказанный
ни один test не вызывает drop_all
ни один test не использует live engine
safe test command создан
live DB не меняется после tests
live DB не меняется после двух recreates
WITHOUT_BARCODE = 0
DUPLICATES = 0
sales integrity сохранена
Core safe tests PASS
Inventory tests PASS
Avito tests PASS
safety scans честные
targeted commit
push
clean Git
owner decision required
```

---

# 27. Финальный статус

Если всё доказано:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R6_DATA_RECOVERY_AND_TEST_ISOLATION_HARDENED_READY_FOR_OWNER_DECISION

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если потеря не исключена:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R6_DATA_RECOVERY_INCONCLUSIVE

BLOCKERS:
DATA LOSS CANNOT BE EXCLUDED

OWNER_DECISION_REQUIRED: true
DO_NOT_START_NEXT_STAGE: true
```

Если потеря подтверждена:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R6_DATA_LOSS_CONFIRMED

RECOVERY_OPTIONS:
...

OWNER_DECISION_REQUIRED: true
DO_NOT_START_NEXT_STAGE: true
```
