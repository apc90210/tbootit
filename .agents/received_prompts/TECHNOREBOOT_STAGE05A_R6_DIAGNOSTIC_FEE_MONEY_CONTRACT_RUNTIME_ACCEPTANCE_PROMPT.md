# PROMPT - Техноребут / Stage05A-R6 Diagnostic Fee Money Contract and Runtime Acceptance

## Роль

Ты senior FastAPI engineer, money-domain auditor, SQLite migration engineer, Jinja2 print engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно закрыть оставшиеся acceptance-блокеры Stage05A-R5.

Stage05B не начинать.

---

# 1. Почему Stage05A-R5 пока не принят

Основной функционал стоимости диагностики реализован, но итоговый отчёт и фактическое описание реализации содержат несоответствия требованиям.

## 1.1. Несогласованный денежный тип

В отчёте указано:

```text
diagnostic_fee = Float
```

При этом печатный шаблон использует:

```jinja2
| int
```

Это создаёт риск:

```text
650.50 хранится как Float;
в документе печатается 650;
копейки молча теряются;
значение в API и документе расходится.
```

Нужно выбрать один точный контракт:

```text
A. Только целые рубли.
B. Рубли и копейки.
```

Для текущего этапа предпочтительно:

```text
только целые рубли;
тип integer;
input step=1;
API integer;
DB integer;
без Float;
без скрытого округления.
```

Если проект уже строго использует дробные денежные значения и это доказано, разрешён Decimal-safe вариант с двумя знаками. Но нельзя одновременно хранить Float и печатать `int`.

---

## 1.2. В production print template остался hardcode 500

В отчёте приведено выражение:

```jinja2
{{ (repair.get('diagnostic_fee')
    if (repair.get('diagnostic_fee') is not none)
    else 500) | int }}
```

Это означает, что production-документ всё ещё содержит резервную договорную сумму `500`.

Требование Stage05A-R5:

```text
все существующие и новые RepairOrder после миграции
обязаны иметь diagnostic_fee;
print template не должен самостоятельно придумывать default;
источник истины - RepairOrder.
```

Нужно убрать из print template:

```text
else 500
```

При неожиданно отсутствующем значении:

```text
не печатать выдуманную сумму;
показать контролируемую ошибку;
либо использовать централизованный formatter,
который требует непустое поле RepairOrder.
```

---

## 1.3. Нет live runtime-доказательств

Prompt требовал реальные runtime-сценарии:

```text
A. default 500;
B. custom 800;
C. edit 800 -> 650;
D. zero 0.
```

В отчёте приведена только инструкция владельцу, но не результаты выполнения этих сценариев.

Нужно выполнить их через живые Core/repairs-module endpoints и показать:

```text
repair ID;
repair number;
API value;
detail HTML value;
print page 1 value;
detachable ticket value;
page 2 value;
absence of stale 500 for custom repair.
```

---

## 1.4. Не доказана неизменность live DB от тестов

В отчёте приведён один SHA:

```text
895497...
```

Но отсутствуют отдельно:

```text
LIVE_DB_SHA256_BEFORE_TESTS
LIVE_DB_SHA256_AFTER_TESTS
```

Нужно доказать идентичность до и после всех тестов.

---

# 2. Текущий статус

```text
STAGE05A_R5_BLOCKED_MONEY_TYPE_PRINT_FALLBACK_AND_RUNTIME_PROOF
```

Целевой статус:

```text
TECHNOREBOOT_STAGE05A_R6_DIAGNOSTIC_FEE_MONEY_CONTRACT_READY_FOR_OWNER_CHECK
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
обнулять live DB;
использовать DROP TABLE;
использовать DELETE FROM;
использовать drop_all;
пересоздавать live DB;
запускать unsafe Core pytest;
оставлять Float + |int;
оставлять else 500 в print template;
оставлять разные суммы в разных частях документа;
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

Core tests запускать только:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

---

# 4. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05A_R6_DIAGNOSTIC_FEE_MONEY_CONTRACT_RUNTIME_ACCEPTANCE_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit\.agents\received_prompts
C:\tbootit
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
```

Ожидаемый HEAD:

```text
c0b8c2f
```

Если отличается - указать фактический.

---

# 6. Backup

До изменения денежного типа:

```text
создать backup live DB;
сохранить SHA256;
сохранить counts;
сохранить diagnostic_fee по всем repair IDs.
```

Каталог:

```text
C:\tbootit-data-backups\stage05a-r6\<timestamp>\
```

Отчёт:

```text
BACKUP_PATH
BACKUP_SHA256
REPAIR_COUNT
NULL_DIAGNOSTIC_FEE_COUNT
NON_INTEGER_DIAGNOSTIC_FEE_ROWS
```

Ничего не удалять.

---

# 7. Выбор денежного контракта

Сначала проверить денежные соглашения проекта.

Для `diagnostic_fee` принять один контракт.

## Предпочтительный контракт Stage05A

```text
целые рубли;
Python int;
Pydantic int;
SQLAlchemy Integer;
SQLite INTEGER;
HTML input type=number step=1;
min=0;
API JSON integer;
print integer без преобразования Float -> int.
```

Допустимые значения:

```text
0
500
650
800
1500
```

Недопустимые:

```text
-1
500.5
"500 рублей"
NaN
Infinity
null при создании
пустая строка
```

Если отправлено `500.5`:

```text
HTTP 422;
не округлять;
не обрезать;
не сохранять.
```

---

# 8. Safe additive migration Float -> Integer

Проверить SQLite schema.

Если колонка уже REAL/Float:

```text
не использовать DROP TABLE;
не пересоздавать live table;
не выполнять destructive migration.
```

SQLite имеет динамическую типизацию, поэтому безопасный вариант:

```text
- изменить SQLAlchemy/Pydantic contract на Integer;
- проверить все существующие значения;
- убедиться, что они целочисленные;
- нормализовать только значения вида 500.0 -> 500;
- не менять repair IDs;
- не менять числа, если есть дробные значения;
- при дробных значениях остановиться и выдать OWNER_DECISION_REQUIRED.
```

Не выполнять молчаливое округление.

Отчёт:

```text
EXISTING_NON_INTEGER_VALUES
NORMALIZED_INTEGER_VALUES
ROWS_CHANGED
DATA_LOSS_OCCURRED: false
```

---

# 9. Core model и schemas

Обновить согласованно:

```text
RepairOrder.diagnostic_fee
RepairOrderCreate.diagnostic_fee
RepairOrderUpdate.diagnostic_fee
RepairOrder response
list response
options response
```

Должно быть:

```text
integer >= 0
```

Default:

```text
500
```

`GET /api/repairs/options`:

```json
{
  "default_diagnostic_fee": 500
}
```

---

# 10. Core validation

Проверить:

```text
отсутствует поле -> 500;
500 -> 500;
0 -> 0;
800 -> 800;
-1 -> 422;
500.5 -> 422;
"500" - поведение строго документировать;
"" -> 422;
null -> 422 либо default только если поле отсутствует;
NaN/Infinity -> 422.
```

Предпочтительно не принимать строковые числа через JSON API.

---

# 11. Print template без fallback

В:

```text
repairs-module/app/templates/repair_print_order.html
```

убрать:

```jinja2
else 500
| int
```

Использовать строго сохранённое значение:

```jinja2
{{ repair.diagnostic_fee }}
```

или безопасный formatter:

```jinja2
{{ format_rubles(repair.diagnostic_fee) }}
```

Formatter:

```text
принимает int;
не округляет Float;
не подставляет 500;
не скрывает отсутствие значения;
возвращает единый формат.
```

Если значение отсутствует из-за поврежденных данных:

```text
print route возвращает контролируемую ошибку;
не выдаёт юридический документ с выдуманной суммой.
```

---

# 12. Единое количество упоминаний

Для print HTML определить ожидаемое число упоминаний стоимости.

Например:

```text
основные условия page 1;
отрывной талон;
подробные условия page 2.
```

Для `diagnostic_fee=800`:

```text
все договорные упоминания = 800;
договорных упоминаний 500 = 0.
```

Для `diagnostic_fee=0`:

```text
все договорные упоминания = 0;
default 500 не появляется.
```

---

# 13. Production hardcode scan

Выполнить:

```powershell
git grep -n -I "500 рублей\|500 руб\|500 ₽\|else 500\|diagnostic.*500" -- core/app repairs-module/app
```

Классифицировать каждый match.

Допустимо в production:

```text
одна Core-константа DEFAULT_DIAGNOSTIC_FEE = 500;
migration default/backfill logic;
options response на основе той же Core-константы.
```

Запрещено:

```text
500 в print templates;
500 в repair detail template;
500 в edit template;
500 как независимый UI fallback;
else 500;
дублирующиеся несвязанные defaults.
```

Финальный показатель:

```text
FORBIDDEN_PRODUCTION_DIAGNOSTIC_FEE_HARDCODE_MATCHES: 0
```

---

# 14. UI

## New form

```text
value приходит из Core options;
step=1;
min=0;
500.5 не принимается;
0 не заменяется;
после ошибки сохраняется исходное введённое значение.
```

## Edit form

```text
показывает сохранённый int;
0 отображается как 0;
не использует `value or 500`;
не использует truthy fallback;
не округляет.
```

## Detail

```text
500 ₽
800 ₽
0 ₽
```

Без:

```text
500.0
800.0
```

---

# 15. Core tests

Обновить:

```text
core/tests/test_repair_diagnostic_fee.py
```

Покрыть минимум:

```text
1. Create без поля -> int 500.
2. Create 800 -> int 800.
3. Create 0 -> int 0.
4. Negative -> 422.
5. Decimal 500.5 -> 422.
6. Empty -> 422.
7. Null -> строгий документированный результат.
8. Detail JSON type integer.
9. List JSON type integer.
10. By-number JSON type integer.
11. PATCH 800 -> 650.
12. PATCH 650 -> 0.
13. PATCH decimal -> 422.
14. Terminal PATCH -> 409.
15. Options default integer 500.
16. Existing rows have integer-compatible values.
17. Audit uses exact integer.
```

---

# 16. Repairs-module tests

Обновить:

```text
repairs-module/tests/test_repair_diagnostic_fee_ui.py
```

Проверить:

```text
new form step=1;
new form min=0;
default получен из options;
custom 800;
zero 0;
decimal rejected;
negative rejected;
validation retains input;
edit 650;
edit zero;
detail formatting;
нет `or 500`;
нет truthy fallback.
```

---

# 17. Print tests

Обновить:

```text
repairs-module/tests/test_repair_print_order.py
```

Проверить:

## 500

```text
все договорные упоминания 500;
нет 500.0.
```

## 800

```text
все договорные упоминания 800;
нет договорного 500;
нет 800.0.
```

## 0

```text
все договорные упоминания 0;
нет возврата 500;
нет отсутствующей суммы.
```

## Missing diagnostic_fee

```text
контролируемая ошибка;
не генерируется документ с fallback 500.
```

---

# 18. Runtime A - default 500

Создать через живой UI или API:

```text
ТЕСТ Stage05A-R6 DEFAULT 500
```

Поле не менять.

Зафиксировать:

```text
REPAIR_ID
REPAIR_NUMBER
API_DIAGNOSTIC_FEE
DETAIL_HTML
PRINT_PAGE1_MATCHES
TICKET_MATCHES
PRINT_PAGE2_MATCHES
STALE_OTHER_FEE_MATCHES
```

Ожидаемо:

```text
везде 500;
JSON type integer.
```

---

# 19. Runtime B - custom 800

Создать:

```text
ТЕСТ Stage05A-R6 CUSTOM 800
diagnostic_fee=800
```

Зафиксировать те же показатели.

Ожидаемо:

```text
везде 800;
договорный 500 отсутствует.
```

---

# 20. Runtime C - edit 800 -> 650

Изменить открытый repair B:

```text
800 -> 650
```

Проверить:

```text
API=650;
detail=650;
print page 1=650;
ticket=650;
page 2=650;
старое 800 отсутствует;
другой repair A остается 500;
repair.updated audit создан.
```

---

# 21. Runtime D - zero

Создать:

```text
ТЕСТ Stage05A-R6 ZERO
diagnostic_fee=0
```

Проверить:

```text
API=0;
detail=0;
print=0;
ticket=0;
page 2=0;
500 не вернулся;
нет truthy fallback.
```

---

# 22. Runtime E - decimal rejection

Попытаться создать или изменить:

```text
diagnostic_fee=500.5
```

Ожидаемо:

```text
HTTP 422;
repair не создан или не изменён;
нет history/audit бизнес-изменения;
нет округления до 500;
нет обрезания до 500.
```

---

# 23. Live DB test isolation

После runtime-сценариев снять:

```text
LIVE_DB_SHA256_BEFORE_TESTS
PRODUCT_COUNT_BEFORE_TESTS
SALE_COUNT_BEFORE_TESTS
CUSTOMER_COUNT_BEFORE_TESTS
REPAIR_COUNT_BEFORE_TESTS
HISTORY_COUNT_BEFORE_TESTS
AUDIT_COUNT_BEFORE_TESTS
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
CUSTOMER_COUNT_AFTER_TESTS
REPAIR_COUNT_AFTER_TESTS
HISTORY_COUNT_AFTER_TESTS
AUDIT_COUNT_AFTER_TESTS
```

Ожидаемо:

```text
SHA и все counts идентичны.
```

---

# 24. Safety scans

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests repairs-module
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO\|UPDATE .* SET\|DELETE FROM" -- repairs-module/app
```

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
```

---

# 25. Документация

Создать:

```text
docs/stage05a_r6_diagnostic_fee_money_contract.md
reports/stage05a_r6_diagnostic_fee_money_contract_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report:

```text
# Stage05A-R6 Diagnostic Fee Money Contract Report

## STATUS
## WHY_R5_WAS_NOT_ACCEPTED
## PROMPT_DISCOVERY
## PREFLIGHT
## BACKUP
## MONEY_CONTRACT_BEFORE
## MONEY_CONTRACT_AFTER
## EXISTING_VALUE_AUDIT
## INTEGER_NORMALIZATION
## CORE_MODEL
## CORE_VALIDATION
## UI_VALIDATION
## PRINT_FALLBACK_REMOVAL
## HARDCODE_SCAN
## CORE_TESTS
## REPAIRS_TESTS
## PRINT_TESTS
## RUNTIME_DEFAULT_500
## RUNTIME_CUSTOM_800
## RUNTIME_EDIT_650
## RUNTIME_ZERO
## RUNTIME_DECIMAL_REJECTION
## LIVE_DB_BEFORE_TESTS
## LIVE_DB_AFTER_TESTS
## TEST_ISOLATION_VERDICT
## SAFETY_SCANS
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_CHECK_GUIDE
## FINAL_STATUS
```

---

# 26. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/routers/repairs.py
git add core/app/services/repair_migration.py
git add core/tests/test_repair_diagnostic_fee.py

git add repairs-module/app/routers/repairs.py
git add repairs-module/app/templates/repair_new.html
git add repairs-module/app/templates/repair_edit.html
git add repairs-module/app/templates/repair_detail.html
git add repairs-module/app/templates/repair_print_order.html
git add repairs-module/tests/test_repair_diagnostic_fee_ui.py
git add repairs-module/tests/test_repair_print_order.py

git add docs/stage05a_r6_diagnostic_fee_money_contract.md
git add reports/stage05a_r6_diagnostic_fee_money_contract_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05A_R6_DIAGNOSTIC_FEE_MONEY_CONTRACT_RUNTIME_ACCEPTANCE_PROMPT.md
git add -f logs/2026-08-03.md
```

Не добавлять несуществующие файлы.

Коммит:

```powershell
git commit -m "Harden repair diagnostic fee money contract"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 27. Definition of Done

Готово только если:

```text
diagnostic_fee имеет один согласованный денежный тип;
Float + |int устранён;
копейки не теряются молча;
предпочтительно используются целые рубли;
decimal input отклоняется;
default централизован в Core;
print template не содержит else 500;
print template не содержит независимый default;
все RepairOrder имеют diagnostic_fee;
runtime 500 доказан;
runtime 800 доказан;
runtime edit 650 доказан;
runtime zero доказан;
runtime decimal rejection доказан;
API/detail/print/ticket/page2 согласованы;
изменение одного ремонта не влияет на другой;
live DB SHA до/после tests идентичен;
Core safe tests PASS;
Inventory PASS;
Avito PASS;
Repairs PASS;
safety scans clean;
targeted commit;
push;
clean Git;
owner manual check required.
```

---

# 28. Owner check guide

```text
1. Открыть http://localhost:8040/repairs/new
2. Проверить default 500
3. Проверить, что 500.5 не принимается
4. Создать repair с 800
5. Проверить 800 в карточке и всех частях печати
6. Изменить 800 на 650
7. Проверить 650 в новой печати
8. Создать repair с 0
9. Проверить, что 0 не заменился на 500
10. Проверить, что другой repair сохранил собственную сумму
```

---

# 29. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R6_DIAGNOSTIC_FEE_MONEY_CONTRACT_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05B_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R6_DIAGNOSTIC_FEE_MONEY_CONTRACT_FAIL

BLOCKERS:
...
```
