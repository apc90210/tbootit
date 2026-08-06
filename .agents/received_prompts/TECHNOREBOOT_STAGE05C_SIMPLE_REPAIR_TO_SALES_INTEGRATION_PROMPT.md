# PROMPT - Техноребут / Stage05C Simple Repair-to-Sales Integration

## Роль

Ты senior FastAPI engineer, transactional data-integrity engineer, sales-domain auditor и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно выполнить минимальный финальный этап текущего модуля ремонтов:

```text
Stage05C - автоматический учёт готового ремонта в общих продажах
```

После этого не начинать новые этапы ремонтов без отдельного указания владельца.

---

# 1. Решение владельца

Когда ремонт переводится в статус:

```text
ready
Готов
```

его итоговая стоимость должна автоматически попадать в общий учёт продаж.

Нужно создать в существующей системе продаж одну связанную запись с пометкой:

```text
Ремонт
```

и кратким описанием этого ремонта.

На этом этапе больше ничего не добавлять.

---

# 2. Ограниченный scope

Реализовать только:

```text
1. Переход ремонта в ready.
2. Создание одной связанной записи продажи.
3. Сумма продажи = estimated_repair_amount.
4. Источник продажи = repair.
5. Краткое описание ремонта.
6. Отображение записи в общем списке продаж.
7. Учёт суммы в существующих общих отчётах продаж.
8. Защита от дублей.
```

Не реализовывать:

```text
приём оплаты;
кассовый чек;
выбор способа оплаты в ремонтах;
долги;
предоплату;
частичную оплату;
возврат денег;
складское списание деталей;
резервирование деталей;
создание фиктивных товаров;
отдельный отчёт по ремонтам;
новую кассу;
гарантию на ремонт;
SMS/Telegram;
фискализацию;
отдельные позиции работ;
отдельные позиции деталей.
```

---

# 3. Архитектура

Core владеет:

```text
RepairOrder;
Sale;
связью ремонта с продажей;
статусным переходом;
атомарной транзакцией.
```

`repairs-module`:

```text
не обращается к sales DB напрямую;
не создаёт продажу отдельным HTTP-запросом;
только отправляет существующий запрос смены статуса в Core.
```

`inventory-sales-module`:

```text
получает и отображает продажу через существующий Core API;
не получает прямой доступ к repair DB;
не изменяет ремонт.
```

---

# 4. Триггер

Триггер создания продажи:

```text
успешный переход RepairOrder в status=ready.
```

Продажа создаётся в той же Core-транзакции, что и:

```text
сохранение estimated_repair_amount;
смена статуса;
RepairStatusHistory;
AuditLog.
```

Если создание продажи не удалось:

```text
status не меняется;
estimated_repair_amount не меняется;
history не создаётся;
audit смены статуса не создаётся;
частичная продажа не остаётся.
```

---

# 5. Сумма

Сумма продажи:

```text
repair.estimated_repair_amount
```

Правила:

```text
integer;
целые рубли;
0 допустимо;
null недопустимо при выходе из diagnostics;
никаких Float;
никакого округления.
```

Если сумма равна `0`, создать связанную продажу на `0 ₽`. Это фиксирует факт бесплатного ремонта.

---

# 6. Одна продажа на один ремонт

Для одного `RepairOrder` может существовать только одна связанная продажа типа `repair`.

Предпочтительный контракт:

```text
Sale.source_type = "repair"
Sale.source_id = repair.id
```

Добавить уникальность связи:

```text
(source_type, source_id)
```

Если текущая модель Sale уже имеет подходящие поля ссылки/источника, использовать их и не создавать параллельный контракт.

---

# 7. Повторный переход в ready

Если ремонт может повторно попасть в `ready`, новую продажу не создавать.

Правило:

```text
найти существующую repair-sale;
обновить её сумму и описание актуальными данными;
не создавать дубль.
```

После любого количества допустимых повторов:

```text
один repair;
одна связанная sale.
```

---

# 8. Отмена после ready

Для минимальной корректности отчётов:

```text
если ремонт с уже созданной repair-sale позднее переводится в canceled,
связанную продажу не удалять,
а перевести в существующий статус canceled.
```

Это нужно, чтобы отменённый ремонт не продолжал увеличивать итог продаж.

Не реализовывать возврат денег и новую финансовую логику.

Если существующая матрица не допускает отмену после `ready`, ничего дополнительно не добавлять.

---

# 9. Данные продажи

Продажа должна иметь явную пометку:

```text
Ремонт
```

Минимальные данные:

```text
source_type: repair
source_id: repair.id
repair_number
total_amount
description
status
created_at
```

Если существующая модель требует дополнительные поля, использовать минимальные совместимые значения.

Не создавать вымышленные товары и не уменьшать складские остатки.

---

# 10. Описание

Пример:

```text
Ремонт R-20260806-0012 - ноутбук Lenovo IdeaPad.
Неисправность: не включается.
```

Использовать доступные поля:

```text
repair.number;
device_type;
brand;
model;
reported_issue.
```

Допустимо добавить свободные поля работ/деталей только при их наличии и без усложнения UI.

Не включать:

```text
пароли;
PIN;
внутренние секретные заметки;
номер телефона;
полный адрес клиента.
```

---

# 11. Отображение в продажах

В общем списке продаж запись должна быть заметна как ремонт.

Показывать:

```text
Тип: Ремонт
Номер ремонта
Краткое описание
Сумма
Статус продажи
Дата
```

Допустима ссылка:

```text
Открыть ремонт
```

на:

```text
http://localhost:8040/repairs/{repair_id}
```

Отдельную страницу ремонтных продаж не создавать.

---

# 12. Общие отчёты

Связанная repair-sale должна учитываться в существующих общих итогах продаж:

```text
сегодня;
неделя;
месяц;
год;
произвольный период;
общая сумма.
```

Отдельный отчёт по ремонтам не создавать.

Продажа со статусом `canceled` не входит в завершённую выручку по существующим правилам.

Продажа с суммой `0` видна как операция, но не меняет денежный итог.

---

# 13. Способ оплаты

На этапе `ready` способ оплаты не вводится.

Если существующая схема Sale требует обязательный способ оплаты:

```text
использовать существующее нейтральное значение "other";
русская подпись: "Другое".
```

Ремонт — это источник продажи, а не способ оплаты. Не добавлять способ оплаты «Ремонт».

В отчёте зафиксировать выбранное совместимое решение.

---

# 14. Позиции продажи

Предпочтительно создать одну нескладскую строку:

```text
Наименование: Ремонт <номер>
Количество: 1
Цена: estimated_repair_amount
Сумма: estimated_repair_amount
Тип: service/repair
```

Только если существующая модель поддерживает нескладские позиции.

Запрещено:

```text
создавать фиктивный Product;
привязывать случайный Product;
уменьшать product.quantity;
создавать inventory movement;
резервировать товар.
```

Если Sale без Product невозможна, добавить минимальную additive поддержку generic/service line, но не создавать товар-заглушку.

---

# 15. Core API

Переиспользовать существующий endpoint:

```text
POST /api/repairs/{repair_id}/status
```

Request:

```json
{
  "status": "ready",
  "comment": null,
  "estimated_repair_amount": 2800
}
```

Допустимо расширить response/read model полем:

```text
linked_sale_id
```

чтобы связь была видна через:

```text
GET /api/repairs/{id}
```

---

# 16. Audit

Добавить или использовать события:

```text
repair.sale_created
repair.sale_updated
repair.sale_canceled
```

Payload:

```text
repair_id;
repair_number;
sale_id;
amount;
source_type.
```

Не сохранять полные свободные тексты в audit.

---

# 17. Миграция

До изменения:

```text
backup live DB;
SHA256;
counts;
schema sales/repair_orders.
```

Каталог:

```text
C:\tbootit-data-backups\stage05c-repair-sales\<timestamp>\
```

Миграция:

```text
только additive;
идемпотентная;
никаких DROP;
никаких DELETE;
никакого пересоздания live DB.
```

Для уже существующих ремонтов в `ready` массово продажи не создавать.

Только новые успешные переходы в `ready` после внедрения создают repair-sale.

---

# 18. Core tests

Создать:

```text
core/tests/test_repair_ready_creates_sale.py
core/tests/test_repair_sale_idempotency.py
core/tests/test_repair_sale_reports.py
core/tests/test_repair_sale_stock_isolation.py
```

Покрыть:

```text
diagnostics -> ready с amount=2800 создаёт sale;
sale amount=2800;
source_type=repair;
source_id=repair.id;
описание содержит номер ремонта;
sale входит в общий отчёт;
amount=0 создаёт sale 0;
повторный ready не создаёт дубль;
существующая sale обновляется;
уникальная связь работает;
при ошибке операция откатывается;
product quantity не меняется;
inventory movement не создаётся;
обычные продажи не ломаются;
canceled repair-sale не входит в завершённую выручку;
audit создан.
```

---

# 19. Inventory/Sales tests

Создать или обновить:

```text
inventory-sales-module/tests/test_repair_sales_ui.py
inventory-sales-module/tests/test_repair_sales_reports.py
```

Проверить:

```text
repair-sale видна в общем списке;
есть пометка «Ремонт»;
виден номер ремонта;
видно описание;
видна сумма;
нет фиктивного товара;
нет складского списания;
repair-sale входит в общие отчёты;
canceled repair-sale не входит в завершённую выручку;
обычные продажи отображаются без изменений.
```

---

# 20. Repairs tests

Создать:

```text
repairs-module/tests/test_ready_creates_linked_sale_ui.py
```

Проверить:

```text
переход в ready проходит существующей формой;
отдельного sales-запроса из repairs-module нет;
после ready карточка может показать ссылку/ID продажи;
повторный ready не создаёт дубль;
нет прямого доступа к DB.
```

---

# 21. Runtime A - 2800

Создать:

```text
ТЕСТ Stage05C REPAIR SALE 2800
```

Провести:

```text
received -> diagnostics;
в форме статуса указать 2800;
перевести в ready.
```

Проверить:

```text
repair.status=ready;
repair.estimated_repair_amount=2800;
создана ровно одна sale;
sale source_type=repair;
sale source_id=repair.id;
sale total=2800;
описание содержит номер ремонта;
продажа видна в общем списке;
общий отчёт увеличился на 2800.
```

---

# 22. Runtime B - 0

Создать бесплатный тестовый ремонт с `estimated_repair_amount=0` и перевести в `ready`.

Проверить:

```text
создана одна sale с total=0;
пометка «Ремонт» присутствует;
денежный итог не изменился.
```

---

# 23. Runtime C - idempotency

Проверить допустимый повторный сценарий `ready`.

Ожидаемо:

```text
repair-sale count остаётся 1;
сумма и описание актуализированы;
новая sale не создана.
```

Не расширять статусную матрицу ради теста.

---

# 24. Runtime D - складская изоляция

До и после runtime сравнить:

```text
products count;
product quantities;
inventory movements;
обычные sales count;
repair sales count.
```

Ожидаемо:

```text
product quantities не изменились;
inventory movements не созданы;
добавлены только repair-sale records.
```

---

# 25. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05C_SIMPLE_REPAIR_TO_SALES_INTEGRATION_PROMPT.md
```

Скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

Указать:

```text
PROMPT_SEARCH_DONE
PROMPT_USED
PROMPT_SOURCE
PROMPT_LOCAL_COPY
PROMPT_SHA256
```

---

# 26. Preflight

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
b9d93df
```

---

# 27. Полные тесты

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
```

До и после тестов сравнить SHA live DB и counts.

---

# 28. Safety scans

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests repairs-module
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO\|UPDATE .* SET\|DELETE FROM" -- repairs-module/app inventory-sales-module/app
```

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
```

---

# 29. Документация

Создать:

```text
docs/stage05c_simple_repair_to_sales_integration.md
reports/stage05c_simple_repair_to_sales_integration_report.md
```

Обновить:

```text
README.md
logs/2026-08-06.md
```

---

# 30. Git

Только targeted add.

Коммит:

```powershell
git commit -m "Add completed repairs to sales"
git push origin main
```

Запрещено:

```text
git add .
git add -A
git add -u
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 31. Definition of Done

Готово только если:

```text
переход в ready создаёт repair-sale;
сумма равна estimated_repair_amount;
0 поддерживается;
есть пометка repair;
есть описание;
sale видна в общем списке;
sale входит в общие отчёты;
один repair создаёт максимум одну sale;
повторный ready не создаёт дубль;
операция status + sale атомарная;
нет фиктивного Product;
нет stock mutation;
нет inventory movement;
обычные продажи не сломаны;
canceled repair-sale не увеличивает завершённую выручку;
все тесты PASS;
live DB не меняется от tests;
migration additive/idempotent;
safety scans clean;
targeted commit;
push;
clean Git;
owner manual check required.
```

---

# 32. Owner check guide

```text
1. Открыть ремонт в статусе «Диагностика».
2. Указать стоимость 2800.
3. Перевести в «Готов».
4. Открыть общий список продаж.
5. Найти запись с пометкой «Ремонт».
6. Проверить номер ремонта и описание.
7. Проверить сумму 2800 ₽.
8. Открыть общий отчёт продаж.
9. Проверить увеличение итога на 2800 ₽.
10. Повторить с бесплатным ремонтом 0 ₽.
11. Убедиться, что складские остатки не изменились.
12. Убедиться, что повторный ready не создаёт вторую продажу.
```

---

# 33. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05C_SIMPLE_REPAIR_TO_SALES_INTEGRATION_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_REPAIR_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05C_SIMPLE_REPAIR_TO_SALES_INTEGRATION_FAIL

BLOCKERS:
...
```
