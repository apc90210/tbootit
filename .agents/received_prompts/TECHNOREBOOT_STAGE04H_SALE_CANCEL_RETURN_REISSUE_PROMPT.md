# PROMPT — Техноребут / Stage 04H Sale Cancellation, Stock Return and Reissue Flow

## Роль агента

Ты senior backend/fullstack developer, архитектор транзакций продаж, FastAPI engineer, Jinja2 UI developer, Docker runtime validator и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — реализовать следующий функциональный этап после принятия Stage04G-R4:

```text
Stage04H — Отмена продажи, возврат товара в остатки и повторное оформление
```

Это отдельный этап. После реализации обязательно требуется ручная проверка владельцем.

---

# 1. Контекст проекта

«Техноребут» — магазин и сервисный центр по ремонту и продаже компьютерной и оргтехники, преимущественно Б/У.

Архитектура строго модульная:

```text
Core API + DB владеет данными и бизнес-логикой.
inventory-sales-module работает только через HTTP API Core.
Прямой доступ к Core DB из inventory-sales-module запрещён.
Все модули работают в отдельных Docker-контейнерах.
```

---

# 2. Принятое состояние предыдущего этапа

Принят Stage04G-R4:

```text
отчёты по продажам
денежная сводка
способы оплаты
счёт юрлица
фильтры Сегодня / Неделя / Месяц / Год
default period с 1 января по сегодня
```

Следующая задача нужна для корректности остатков и отчётов:

```text
отмена продажи должна возвращать товар в остатки
отменённая продажа не должна учитываться в выручке
история продажи не должна физически удаляться
```

---

# 3. Owner requirements

Реализовать:

```text
1. Статусы продажи:
   - completed
   - canceled
   - superseded
   - reissued

2. Отмена продажи:
   - кнопка "Отменить продажу";
   - обязательная причина;
   - подтверждение действия;
   - дата и время отмены;
   - кто отменил;
   - возврат товаров из продажи в остатки.

3. Отчёты:
   - canceled не входит в выручку;
   - canceled не входит в денежную разбивку;
   - canceled не входит в количество завершённых продаж;
   - canceled можно увидеть отдельным фильтром.

4. Повторное оформление:
   - из отменённой продажи можно создать новую;
   - новая продажа связывается со старой;
   - старая получает статус superseded;
   - новая получает статус reissued или completed с признаком reissue;
   - новый товарный чек формируется для новой продажи.

5. Аудит:
   - кто отменил;
   - когда;
   - причина;
   - какие товары вернулись;
   - ссылка на исходную и новую продажу.
```

---

# 4. Целевой статус

```text
TECHNOREBOOT_STAGE04H_SALE_CANCEL_RETURN_REISSUE_READY_FOR_OWNER_CHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 5. Строгие запреты

Запрещено:

```text
физически удалять продажу
удалять sale items
переписывать историю продажи задним числом
возвращать товар в остатки без транзакции
делать direct DB access из inventory-sales-module
создавать отдельную DB для inventory-sales-module
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset
использовать git clean
использовать rebase
использовать force push
коммитить runtime DB/temp/cache
использовать Base.metadata.drop_all/create_all
```

Разрешено:

```text
точечное расширение Core моделей/схем
безопасная миграция/ensure-columns в стиле проекта
Core API endpoints
Inventory UI
tests
docs/report/log
targeted commit
normal push
```

---

# 6. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04H_SALE_CANCEL_RETURN_REISSUE_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit
C:\tbootit\.agents
C:\tbootit\.agents\received_prompts
C:\tbootit\prompts
C:\tbootit\docs
```

Если найден в Downloads — скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В отчёте указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 7. Preflight

Выполнить:

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

Если worktree dirty — сначала определить причину.

---

# 8. Исследовать текущую модель продаж

Проверить:

```text
core/app/models.py
core/app/schemas.py
core/app/routers/sales.py
core/app/routers/reports.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/sales.py
inventory-sales-module/app/templates/sales_list.html
inventory-sales-module/app/templates/sales_detail.html
inventory-sales-module/app/templates/sale_receipt_preview.html
```

Определить:

```text
как сейчас хранится статус продажи
как sale items связаны с products
как при продаже меняется product.status
как считаются отчёты
как создаётся чек
```

---

# 9. Модель данных

Расширить Sale безопасно.

Минимально нужные поля:

```text
status: str
canceled_at: datetime | null
cancel_reason: text | null
canceled_by: str | null
superseded_by_sale_id: int | null
source_sale_id: int | null
reissued_at: datetime | null
```

Допустимые статусы:

```text
completed
canceled
superseded
reissued
```

Правила:

```text
completed:
обычная завершённая продажа

canceled:
продажа отменена, товар возвращён на склад

superseded:
исходная продажа заменена новой продажей

reissued:
новая продажа, созданная из старой
```

Если архитектурно проще:

```text
новая продажа может иметь status=completed,
а факт reissue хранить через source_sale_id
```

Но API и UI должны однозначно показывать:

```text
это повторное оформление
```

---

# 10. Безопасная миграция

Если таблица уже существует, добавить поля безопасно.

Запрещено:

```text
drop_all
create_all для очистки
удаление существующих данных
```

Допустимо:

```text
проектная startup migration / ALTER TABLE ADD COLUMN
```

Миграция должна быть идемпотентной.

---

# 11. Core API — отмена продажи

Добавить endpoint:

```text
POST /api/sales/{sale_id}/cancel
```

Request:

```json
{
  "reason": "Ошибка в цене",
  "canceled_by": "Администратор"
}
```

Response:

```json
{
  "id": 15,
  "status": "canceled",
  "canceled_at": "...",
  "cancel_reason": "Ошибка в цене",
  "canceled_by": "Администратор",
  "returned_items": [
    {
      "product_id": 70,
      "quantity": 1,
      "new_product_status": "available"
    }
  ]
}
```

---

# 12. Транзакционная логика отмены

Отмена должна выполняться атомарно:

```text
1. Найти продажу.
2. Проверить, что её можно отменить.
3. Проверить, что она ещё не canceled/superseded.
4. Получить sale items.
5. Вернуть товар в остатки.
6. Записать status=canceled.
7. Записать canceled_at.
8. Записать cancel_reason.
9. Записать canceled_by.
10. Создать audit/event.
11. Commit.
```

Если любой шаг падает:

```text
rollback всей операции
```

Нельзя получить состояние:

```text
продажа canceled, но товар не возвращён
или товар возвращён, но продажа completed
```

---

# 13. Возврат товаров в остатки

Для каждого sale item:

```text
product.status должен вернуться в available/in_stock
quantity должен быть восстановлен, если используется количественный учёт
```

Если система пока считает каждый товар уникальной единицей:

```text
достаточно вернуть status=available
```

Если есть quantity:

```text
восстановить точное количество
```

Нельзя вернуть в остатки товар дважды.

Повторный cancel должен вернуть:

```text
409 Conflict
```

или контролируемую ошибку.

---

# 14. Проверки допустимости отмены

Нельзя отменить:

```text
уже canceled
уже superseded
несуществующую продажу
```

Для таких случаев:

```text
404 или 409
```

с понятным сообщением на русском.

---

# 15. Core API — повторное оформление

Добавить endpoint:

```text
POST /api/sales/{sale_id}/reissue
```

или staged flow:

```text
GET /api/sales/{sale_id}/reissue-preview
POST /api/sales/{sale_id}/reissue
```

Новая продажа может позволять изменить:

```text
цену
способ оплаты
гарантию
количество
состав товаров — если безопасно
```

Минимально обязательный MVP:

```text
создать новую продажу на основе исходной
```

Правила:

```text
1. Исходная продажа должна быть canceled.
2. Новая продажа получает source_sale_id.
3. Исходная получает superseded_by_sale_id.
4. Исходная может перейти canceled → superseded.
5. Новая получает reissued или completed + source_sale_id.
6. Товар снова списывается из остатков.
7. Формируется новый товарный чек.
```

---

# 16. Idempotency

Повторный вызов reissue не должен создавать бесконечно новые продажи без предупреждения.

Если уже есть `superseded_by_sale_id`:

```text
409 Conflict
```

или вернуть существующую новую продажу.

---

# 17. Core API — чтение продажи

Расширить `GET /api/sales/{id}`:

```json
{
  "id": 15,
  "status": "superseded",
  "canceled_at": "...",
  "cancel_reason": "...",
  "canceled_by": "...",
  "superseded_by_sale_id": 22,
  "source_sale_id": null
}
```

Для новой продажи:

```json
{
  "id": 22,
  "status": "reissued",
  "source_sale_id": 15
}
```

---

# 18. Список продаж и фильтры

Расширить:

```text
GET /api/sales
```

Фильтры:

```text
status=completed
status=canceled
status=superseded
status=reissued
```

UI:

```text
Все
Завершённые
Отменённые
Заменённые
Повторно оформленные
```

---

# 19. Отчёты

Критическое правило:

```text
В денежные отчёты входят только продажи, которые считаются завершёнными и действующими.
```

Не включать:

```text
canceled
superseded
```

`reissued` включать как действующую продажу, если это фактическая новая продажа.

Обновить:

```text
core/app/routers/reports.py
```

Проверить:

```text
total_amount
money_summary
sales_count
items_count
payment breakdown
```

Отменённые продажи не должны влиять ни на одну денежную сумму.

---

# 20. UI — страница продажи

На странице продажи показать:

```text
Статус
Дата продажи
Способ оплаты
Сумма
Гарантия
```

Для completed:

```text
кнопка "Отменить продажу"
```

Для canceled:

```text
причина отмены
кто отменил
дата отмены
какие товары возвращены
кнопка "Оформить повторно"
```

Для superseded:

```text
ссылка на новую продажу
```

Для reissued:

```text
ссылка на исходную продажу
```

---

# 21. UI — отмена продажи

Добавить форму/модальное подтверждение:

```text
Причина отмены *
Кто отменяет
Подтверждение:
"Товар будет возвращён в остатки. Продолжить?"
```

Кнопки:

```text
Подтвердить отмену
Назад
```

Причина обязательна.

---

# 22. UI — повторное оформление

На canceled продаже кнопка:

```text
Оформить повторно
```

Открывает:

```text
предзаполненную корзину/checkout
```

Пользователь может проверить:

```text
товар
цены
способ оплаты
гарантию
```

После сохранения:

```text
открывается новая продажа
```

---

# 23. Товарный чек

Для canceled/superseded старой продажи:

```text
старый чек сохраняется как исторический
```

Нельзя перезаписывать его данными новой продажи.

Для новой reissued продажи:

```text
формируется новый чек с новым номером
```

В UI можно показывать:

```text
Повторное оформление продажи №...
```

---

# 24. Audit/events

Создать события:

```text
sale.canceled
sale.items_returned
sale.reissued
sale.superseded
```

Payload минимум:

```text
sale_id
source_sale_id
new_sale_id
reason
canceled_by
items
timestamp
```

---

# 25. Tests — Core cancel flow

Создать/обновить:

```text
core/tests/test_sale_cancel_flow.py
```

Покрыть:

```text
1. completed sale can be canceled.
2. cancel requires reason.
3. cancel sets status=canceled.
4. cancel sets canceled_at.
5. cancel saves canceled_by.
6. sold product returns to available.
7. quantity restores correctly.
8. second cancel returns 409.
9. cancel missing sale returns 404.
10. transaction rollback on failure.
11. audit event created.
```

---

# 26. Tests — Core reports

Обновить:

```text
core/tests/test_sales_reports.py
```

Покрыть:

```text
1. canceled sale excluded from total_amount.
2. canceled sale excluded from money_summary.
3. canceled sale excluded from sales_count.
4. canceled sale excluded from items_count.
5. superseded sale excluded.
6. reissued active sale included.
```

---

# 27. Tests — Core reissue

Создать:

```text
core/tests/test_sale_reissue_flow.py
```

Покрыть:

```text
1. canceled sale can be reissued.
2. completed sale cannot be reissued directly.
3. new sale gets source_sale_id.
4. old sale gets superseded_by_sale_id.
5. old status becomes superseded.
6. new status becomes reissued/completed.
7. stock is deducted again.
8. second reissue blocked.
9. new receipt has new sale number.
```

---

# 28. Tests — Inventory UI

Создать/обновить:

```text
inventory-sales-module/tests/test_sale_cancel_ui.py
inventory-sales-module/tests/test_sale_reissue_ui.py
inventory-sales-module/tests/test_sales_status_filters_ui.py
```

Покрыть:

```text
1. completed sale shows cancel button.
2. canceled sale shows reason/date/user.
3. canceled sale shows reissue button.
4. superseded sale links to new sale.
5. reissued sale links to source.
6. cancel form requires reason.
7. successful cancel redirects to sale detail.
8. status filters work.
9. no direct DB access.
```

---

# 29. Docker rebuild

После реализации:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose up -d avito-module
docker compose ps
```

---

# 30. Full regression

Обязательно:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Все должны пройти.

---

# 31. Runtime smoke — cancel

Создать безопасную тестовую продажу через UI/API.

Зафиксировать:

```text
sale_id
product_id
status before cancel
```

Проверить до отмены:

```text
sale.status = completed
product.status = sold
```

Выполнить cancel.

Проверить после:

```text
sale.status = canceled
cancel_reason заполнен
canceled_at заполнен
product.status = available
```

Повторный cancel:

```text
409
```

---

# 32. Runtime smoke — reports

Зафиксировать сумму отчёта до тестовой продажи, после продажи и после отмены.

Должно быть:

```text
после продажи сумма увеличилась
после отмены сумма вернулась к исходной
```

Способ оплаты отменённой продажи не должен оставаться в money_summary.

---

# 33. Runtime smoke — reissue

Для canceled sale:

```text
создать reissue
```

Проверить:

```text
old.status = superseded
old.superseded_by_sale_id = new.id
new.source_sale_id = old.id
new.status = reissued/completed
product.status = sold
new receipt opens
```

---

# 34. Safety scans

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

# 35. Documentation and report

Создать:

```text
docs/stage04h_sale_cancel_return_reissue.md
reports/stage04h_sale_cancel_return_reissue_report.md
```

Обновить:

```text
logs/2026-07-22.md
```

Report structure:

```text
# Stage 04H Sale Cancellation, Stock Return and Reissue Report

## STATUS

## OWNER_REQUIREMENTS

## ARCHITECTURE

## DATA_MODEL

## API

### Cancel
### Reissue
### Status filters

## STOCK_RETURN

## REPORTS_BEHAVIOR

## UI

## AUDIT_EVENTS

## TESTS

Core:
Inventory:
Avito:

## RUNTIME_SMOKE

### Cancel
### Report rollback
### Reissue

## SAFETY_SCAN

## FILES_CHANGED

## COMMIT

## PUSH

## FINAL_GIT_STATUS

## OWNER_CHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04H_SALE_CANCEL_RETURN_REISSUE_READY_FOR_OWNER_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 36. Git

Использовать только targeted add.

Возможные файлы:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/main.py
git add core/app/routers/sales.py
git add core/app/routers/reports.py
git add core/tests/test_sale_cancel_flow.py
git add core/tests/test_sale_reissue_flow.py
git add core/tests/test_sales_reports.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/sales_list.html
git add inventory-sales-module/app/templates/sales_detail.html
git add inventory-sales-module/app/templates/sale_cancel.html
git add inventory-sales-module/app/templates/sale_reissue.html
git add inventory-sales-module/tests/test_sale_cancel_ui.py
git add inventory-sales-module/tests/test_sale_reissue_ui.py
git add inventory-sales-module/tests/test_sales_status_filters_ui.py

git add docs/stage04h_sale_cancel_return_reissue.md
git add reports/stage04h_sale_cancel_return_reissue_report.md
git add logs/2026-07-22.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04H_SALE_CANCEL_RETURN_REISSUE_PROMPT.md
```

Коммит:

```powershell
git commit -m "Implement sale cancellation stock return and reissue flow"
git push
```

После push:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -3
```

Финальный status должен быть пустым.

---

# 37. Definition of Done

Готово только если:

```text
sale statuses implemented
completed sale can be canceled
cancel reason required
cancel metadata saved
stock returned atomically
double cancel blocked
canceled excluded from reports
superseded excluded from reports
canceled visible by status filter
reissue flow works
old and new sales linked
new receipt generated
audit events created
Core tests PASS
Inventory tests PASS
Avito tests PASS
runtime cancel smoke PASS
runtime report smoke PASS
runtime reissue smoke PASS
safety scans clean
targeted commit
push
final git status clean
owner manual check required
```

---

# 38. Final answer required from agent

Финальный ответ должен быть подробным.

Обязательно указать:

```text
какие статусы реализованы
как возвращается товар
как исключаются отменённые продажи из отчётов
как работает повторное оформление
результаты Core/Inventory/Avito tests
результаты runtime smoke
commit hash
push result
final git status
```

Успешный статус:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04H_SALE_CANCEL_RETURN_REISSUE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

При проблеме:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04H_SALE_CANCEL_RETURN_REISSUE_FAIL

BLOCKERS:
...
```
