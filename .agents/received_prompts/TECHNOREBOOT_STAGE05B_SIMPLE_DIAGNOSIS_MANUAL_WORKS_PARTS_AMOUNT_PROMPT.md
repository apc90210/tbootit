# PROMPT - Техноребут / Stage05B Simple Repair Diagnosis and Manual Estimate

## Роль

Ты senior FastAPI/Jinja2 developer, SQLite migration engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно реализовать максимально простой Stage05B.

Предыдущий сложный prompt Stage05B не выполнять.

Stage05C не начинать.

---

# 1. Решение владельца

На этом этапе не нужна сложная система диагностики и смет.

Нужно только вручную сохранять:

```text
1. Результат диагностики.
2. Перечень предполагаемых работ.
3. Перечень деталей и материалов.
4. Общую предполагаемую сумму ремонта.
```

Все текстовые данные вводятся сотрудником вручную в свободные поля.

Никаких отдельных позиций, таблиц, автоматических расчётов и согласований пока не делать.

---

# 2. Строго запрещённый scope

Не реализовывать:

```text
RepairDiagnosis как отдельную сущность;
RepairEstimate как отдельную сущность;
RepairEstimateItem;
версии диагностики;
версии сметы;
автоматический расчёт итогов;
отдельные строки работ;
отдельные строки деталей;
количество;
цена за единицу;
согласование клиента;
способы согласования;
историю согласований;
новые статусы ремонта;
customer_declined;
автоматические переходы статусов;
резервирование товара;
списание товара;
привязку к Product;
создание Sale;
оплату ремонта;
отдельную печатную смету;
SMS, Telegram, email;
подписи клиента;
сложный JavaScript-конструктор.
```

---

# 3. Новые поля ремонта

Добавить непосредственно в `RepairOrder` четыре простых поля.

Предпочтительные имена:

```text
diagnosis_text
planned_works_text
planned_parts_text
estimated_repair_amount
```

## Поля

### diagnosis_text

```text
Свободное многострочное поле.
Результат диагностики.
```

Пример:

```text
Неисправен разъём питания.
Требуется замена разъёма и чистка системы охлаждения.
```

### planned_works_text

```text
Свободное многострочное поле.
Перечень предполагаемых работ.
```

Пример:

```text
1. Разборка ноутбука - 500 ₽
2. Замена разъёма питания - 1500 ₽
3. Чистка системы охлаждения - 1000 ₽
```

Система не анализирует цифры внутри текста и ничего автоматически не считает.

### planned_parts_text

```text
Свободное многострочное поле.
Перечень предполагаемых деталей и материалов.
```

Пример:

```text
1. Разъём питания - 800 ₽
2. Термопаста - 300 ₽
```

Система не проверяет и не связывает эти строки со складом.

### estimated_repair_amount

```text
Общая предполагаемая стоимость ремонта.
Вводится сотрудником вручную.
Целые рубли.
```

Пример:

```text
4100
```

---

# 4. Денежный контракт

Для `estimated_repair_amount` использовать тот же контракт, что для стоимости диагностики:

```text
Python int;
Pydantic int;
SQLAlchemy Integer;
SQLite INTEGER;
JSON integer;
HTML number;
step=1;
min=0.
```

Допустимо:

```text
0;
500;
4100;
15000.
```

Недопустимо:

```text
-1;
500.5;
NaN;
Infinity;
буквы;
пустая строка при обязательном вводе.
```

Поле может быть nullable до проведения диагностики.

Если поле заполнено, оно должно быть целым числом не меньше нуля.

---

# 5. Миграция

Добавить поля в существующую таблицу:

```text
repair_orders
```

Миграция только additive и идемпотентная.

Для существующих ремонтов:

```text
diagnosis_text = null;
planned_works_text = null;
planned_parts_text = null;
estimated_repair_amount = null.
```

Запрещено:

```text
DROP TABLE;
DELETE FROM;
пересоздание live DB;
изменение существующих repair IDs;
изменение товаров;
изменение продаж;
изменение клиентов.
```

До миграции создать backup:

```text
C:\tbootit-data-backups\stage05b-simple\<timestamp>\
```

---

# 6. Core API

Добавить новые поля в:

```text
RepairOrder model;
RepairOrderCreate - необязательно;
RepairOrderUpdate;
RepairOrder response;
GET /api/repairs;
GET /api/repairs/{id};
GET /api/repairs/by-number/{number}.
```

Основной способ заполнения:

```text
PATCH /api/repairs/{id}
```

Пример:

```json
{
  "diagnosis_text": "Неисправен разъём питания",
  "planned_works_text": "Замена разъёма питания - 1500 ₽",
  "planned_parts_text": "Разъём питания - 800 ₽",
  "estimated_repair_amount": 2300
}
```

Ожидаемо:

```text
HTTP 200;
все поля сохранены;
repair.updated audit создан.
```

---

# 7. Статусы ремонта

Не менять существующую матрицу статусов.

Не добавлять новые статусы.

Заполнение полей диагностики разрешить для открытых ремонтов.

Для:

```text
issued;
canceled.
```

редактирование блокируется существующей terminal protection:

```text
HTTP 409.
```

Сохранение диагностики само по себе не должно автоматически менять статус ремонта.

Сотрудник меняет статус отдельно существующим механизмом.

---

# 8. UI карточки ремонта

На странице:

```text
http://localhost:8040/repairs/{id}
```

Добавить простой блок:

```text
Диагностика и предварительная стоимость
```

Показывать:

```text
Результат диагностики
Предполагаемые работы
Предполагаемые детали и материалы
Предполагаемая стоимость ремонта
```

Если поле пустое:

```text
Не указано
```

Для суммы:

```text
4100 ₽
```

Не показывать:

```text
4100.0;
None;
null.
```

---

# 9. Редактирование

На существующей странице:

```text
/repairs/{id}/edit
```

добавить:

```text
textarea «Результат диагностики»;
textarea «Предполагаемые работы»;
textarea «Предполагаемые детали и материалы»;
number «Предполагаемая стоимость ремонта, ₽».
```

Требования:

```text
сохранённые значения отображаются;
переносы строк сохраняются;
текст можно полностью очистить;
0 не заменяется на пустое значение;
ошибка формы сохраняет введённый текст;
HTML/JavaScript экранируется;
закрытый ремонт не редактируется.
```

---

# 10. Первичная форма приёма

В форму:

```text
/repairs/new
```

эти поля не добавлять.

Причина:

```text
диагностика заполняется после приёма техники.
```

Стоимость диагностики Stage05A-R6 остаётся отдельным полем первичной приёмки.

Не смешивать:

```text
diagnostic_fee
estimated_repair_amount
```

Разница:

```text
diagnostic_fee - стоимость диагностики при отказе/невозможности ремонта;
estimated_repair_amount - предполагаемая общая стоимость самого ремонта.
```

---

# 11. Печатный наряд-заказ

На этом этапе не перестраивать печатный наряд-заказ.

Допустимо добавить в существующий наряд-заказ один компактный блок, только если данные заполнены:

```text
Результат диагностики
Предполагаемые работы
Предполагаемые детали и материалы
Предполагаемая стоимость ремонта
```

Но не создавать:

```text
отдельную печатную смету;
новые страницы;
новые юридические условия;
новые подписи;
новый документ согласования.
```

Если добавление ломает утверждённые две страницы A4, не добавлять блок в печать и честно указать это в отчёте.

Приоритет:

```text
не сломать утверждённый наряд-заказ.
```

---

# 12. Audit

При изменении полей использовать существующий:

```text
repair.updated
```

В audit payload достаточно:

```text
changed_fields
```

Не сохранять полный свободный текст диагностики в audit, если текущая политика audit этого не требует.

Не создавать отдельную сложную историю диагностики.

---

# 13. Core tests

Создать:

```text
core/tests/test_repair_simple_diagnosis.py
```

Проверить:

```text
PATCH всех четырёх полей;
GET detail;
GET list;
GET by-number;
переносы строк;
unicode;
очистка nullable text fields;
amount 0;
amount 4100;
negative amount rejected;
decimal amount rejected;
terminal PATCH rejected;
audit repair.updated;
остальные поля ремонта не меняются.
```

---

# 14. Repairs-module tests

Создать:

```text
repairs-module/tests/test_repair_simple_diagnosis_ui.py
```

Проверить:

```text
поля есть в edit form;
поля отсутствуют в new form;
сохранённые значения отображаются;
textarea сохраняют переносы;
сумма отображается в рублях;
0 отображается как 0;
ошибка сохраняет ввод;
пустые поля показываются как «Не указано»;
пользовательский HTML экранируется;
закрытый ремонт не редактируется.
```

---

# 15. Runtime-проверка

Создать или использовать ремонт:

```text
ТЕСТ Stage05B SIMPLE DIAGNOSIS
```

Перевести в:

```text
diagnostics
```

Заполнить:

```text
Результат диагностики:
Неисправен разъём питания.

Предполагаемые работы:
1. Разборка - 500 ₽
2. Замена разъёма - 1500 ₽

Предполагаемые детали:
1. Разъём питания - 800 ₽

Предполагаемая стоимость:
2800
```

Проверить:

```text
API возвращает все значения;
карточка показывает все значения;
переносы строк сохранены;
сумма показывает 2800 ₽;
статус не изменился автоматически;
склад не изменился;
продажи не изменились.
```

Затем изменить:

```text
2800 -> 3200
```

Проверить обновление.

---

# 16. Складская и финансовая изоляция

До и после runtime проверить:

```text
products count;
product quantities;
sales count;
inventory movements.
```

Ожидаемо:

```text
без изменений.
```

---

# 17. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05B_SIMPLE_DIAGNOSIS_MANUAL_WORKS_PARTS_AMOUNT_PROMPT.md
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

# 18. Preflight

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
b5025f7
```

---

# 19. Полные тесты

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
```

До и после tests сравнить:

```text
LIVE_DB_SHA256;
products;
sales;
customers;
repairs;
repair history;
audit.
```

Все значения должны совпасть.

---

# 20. Safety scans

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

# 21. Документация

Создать:

```text
docs/stage05b_simple_diagnosis_manual_estimate.md
reports/stage05b_simple_diagnosis_manual_estimate_report.md
```

Обновить:

```text
README.md
logs/2026-08-05.md
```

Report:

```text
# Stage05B Simple Diagnosis and Manual Estimate Report

## STATUS
## OWNER_SCOPE_REDUCTION
## PROMPT_DISCOVERY
## PREFLIGHT
## BACKUP
## DATABASE_FIELDS
## CORE_API
## REPAIR_EDIT_UI
## REPAIR_DETAIL_UI
## PRINT_DECISION
## MONEY_CONTRACT
## AUDIT
## TESTS
## RUNTIME
## STOCK_ISOLATION
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

# 22. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/services/repair_migration.py
git add core/tests/test_repair_simple_diagnosis.py

git add repairs-module/app/routers/repairs.py
git add repairs-module/app/templates/repair_edit.html
git add repairs-module/app/templates/repair_detail.html
git add repairs-module/app/templates/repair_print_order.html
git add repairs-module/tests/test_repair_simple_diagnosis_ui.py

git add docs/stage05b_simple_diagnosis_manual_estimate.md
git add reports/stage05b_simple_diagnosis_manual_estimate_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05B_SIMPLE_DIAGNOSIS_MANUAL_WORKS_PARTS_AMOUNT_PROMPT.md
git add README.md
git add -f logs/2026-08-05.md
```

Не добавлять несуществующие файлы.

Запрещено:

```text
git add .
git add -A
git add -u
```

Коммит:

```powershell
git commit -m "Add simple repair diagnosis and manual estimate"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 23. Definition of Done

Готово только если:

```text
есть свободное поле диагностики;
есть свободное поле работ;
есть свободное поле деталей;
есть одна ручная итоговая сумма;
нет отдельных позиций;
нет автоматического расчёта;
нет согласования клиента;
нет версионирования;
нет новых статусов;
нет отдельной сметы;
нет stock mutation;
нет sales mutation;
сумма хранится как integer;
поля редактируются;
карточка отображает данные;
terminal protection работает;
Core safe tests PASS;
Inventory PASS;
Avito PASS;
Repairs PASS;
live DB не меняется от tests;
migration additive/idempotent;
safety scans clean;
targeted commit;
push;
clean Git;
owner manual check required.
```

---

# 24. Owner check guide

```text
1. Открыть ремонт в статусе «Диагностика»
2. Нажать редактирование
3. Заполнить результат диагностики
4. Ввести перечень работ обычным текстом
5. Ввести перечень деталей обычным текстом
6. Ввести общую сумму
7. Сохранить
8. Проверить данные в карточке
9. Изменить сумму
10. Убедиться, что статус не поменялся автоматически
11. Убедиться, что склад и продажи не изменились
```

---

# 25. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_SIMPLE_DIAGNOSIS_MANUAL_ESTIMATE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05C_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_SIMPLE_DIAGNOSIS_MANUAL_ESTIMATE_FAIL

BLOCKERS:
...
```
