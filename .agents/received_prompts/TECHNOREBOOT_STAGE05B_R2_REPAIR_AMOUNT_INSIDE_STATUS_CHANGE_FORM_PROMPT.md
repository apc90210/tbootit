# PROMPT - Техноребут / Stage05B-R2 Repair Amount Inside Status Change Form

## Роль

Ты senior FastAPI/Jinja2 developer, transactional business-rule engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно выполнить точечную UX- и backend-доработку Stage05B.

Stage05C не начинать.

---

# 1. Решение владельца

Стоимость ремонта должна вводиться прямо в блоке смены статуса ремонта.

Сотрудник не должен для этого:

```text
открывать полное редактирование наряд-заказа;
заполнять диагностику;
заполнять работы;
заполнять детали;
заполнять комментарий.
```

В карточке ремонта, рядом с выбором следующего статуса, должно быть поле:

```text
Стоимость ремонта, ₽
```

После ввода суммы сотрудник одной кнопкой:

```text
сохраняет сумму;
переводит ремонт из «Диагностика» в выбранный следующий статус.
```

---

# 2. Главное бизнес-правило

Для любого перехода ИЗ статуса:

```text
diagnostics
```

в любой разрешённый следующий статус должно быть заполнено:

```text
estimated_repair_amount
```

Проверка:

```python
estimated_repair_amount is not None
```

Значение `0` допустимо.

---

# 3. Разрешённые переходы из diagnostics

Не менять существующую матрицу.

Текущие разрешённые переходы из `diagnostics`:

```text
waiting_customer
waiting_parts
in_repair
ready
unrepairable
canceled
```

Русские названия использовать из существующего status options contract.

Для каждого из этих переходов действует одинаковое правило:

```text
стоимость ремонта должна быть заполнена;
0 допустим;
текстовые поля и комментарий необязательны.
```

Не добавлять новый статус «Отказ».

Использовать только уже существующие статусы проекта.

---

# 4. Поле в форме смены статуса

На странице:

```text
/repairs/{id}
```

в существующем блоке смены статуса добавить:

```html
Стоимость ремонта, ₽
```

Требования:

```text
input type=number;
step=1;
min=0;
целые рубли;
поле находится рядом с выбором статуса;
поле отправляется той же формой;
не требуется переходить на /edit.
```

---

# 5. Начальное значение поля

## Если сумма ещё не сохранена

Показать:

```text
пустое поле
```

Не подставлять:

```text
0;
500;
стоимость диагностики;
любое другое значение.
```

## Если сумма уже сохранена

Показать сохранённое значение:

```text
0
2800
5000
```

Сотрудник может изменить его непосредственно перед сменой статуса.

Критически важно:

```text
value=0 должно отображаться как 0;
не использовать `value or ''`;
не использовать truthy fallback;
использовать явную проверку `is not none`.
```

---

# 6. Одна операция

При отправке формы нужно одной операцией:

```text
1. Провалидировать стоимость.
2. Сохранить estimated_repair_amount.
3. Изменить статус.
4. Создать RepairStatusHistory.
5. Создать audit.
```

Операция должна быть атомарной.

Запрещено делать в repairs-module последовательность:

```text
PATCH amount;
затем отдельный POST status.
```

Причина:

```text
если второй запрос упадёт, сумма сохранится, а статус нет;
возникнет частичное изменение.
```

Правильный вариант:

```text
расширить Core status endpoint;
передавать amount вместе со следующим статусом;
выполнить всё в одной DB transaction.
```

---

# 7. Core API

Обновить endpoint:

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

Для другого статуса:

```json
{
  "status": "waiting_parts",
  "comment": null,
  "estimated_repair_amount": 0
}
```

Поле:

```text
estimated_repair_amount
```

может быть optional в общем status request, но обязательно по business rule при выходе из `diagnostics`.

---

# 8. Логика Core

Если текущий статус:

```text
diagnostics
```

и новый статус отличается от `diagnostics`, Core должен определить итоговую сумму.

## Если сумма передана в request

Использовать переданное значение:

```text
0;
2800;
5000.
```

## Если сумма не передана

Допустимо использовать уже сохранённое значение ремонта, если оно не `null`.

Это нужно для:

```text
повторной смены статуса через API;
совместимости с существующими клиентами;
ремонтов, где сумма была сохранена ранее.
```

Итоговое правило:

```python
effective_amount = (
    request.estimated_repair_amount
    if request.estimated_repair_amount is not None
    else repair.estimated_repair_amount
)

if effective_amount is None:
    block transition
```

Критически важно:

```text
0 не должен заменяться сохранённым значением;
использовать `is not None`, а не `or`.
```

---

# 9. Валидация суммы

Допустимо:

```text
0
1
2800
10000
```

Запрещено:

```text
пустое значение при отсутствии сохранённой суммы;
-1;
500.5;
NaN;
Infinity;
буквы;
пробелы вместо числа.
```

Денежный контракт:

```text
Python int;
Pydantic strict integer;
SQLAlchemy Integer;
SQLite INTEGER;
JSON integer.
```

Не округлять и не обрезать дробное значение.

---

# 10. Поведение при пустой сумме

Если:

```text
current status = diagnostics;
request amount отсутствует;
saved amount = null.
```

Переход блокируется.

Сообщение:

```text
Для выхода из статуса «Диагностика» укажите стоимость ремонта.
Можно указать 0 ₽.
```

При ошибке:

```text
status не меняется;
estimated_repair_amount остаётся null;
history не создаётся;
audit status change не создаётся.
```

---

# 11. Текстовые поля остаются необязательными

Не требовать:

```text
diagnosis_text;
planned_works_text;
planned_parts_text;
comment.
```

Переход должен проходить при:

```text
diagnosis_text = null;
planned_works_text = null;
planned_parts_text = null;
comment = null;
estimated_repair_amount = 0.
```

---

# 12. Комментарий к статусу

Поле комментария в форме смены статуса можно оставить.

Оно:

```text
необязательное;
не блокирует переход;
если заполнено - сохраняется в RepairStatusHistory.comment;
если пустое - history создаётся с null/пустым comment по текущему контракту.
```

Не восстанавливать старое правило обязательного комментария.

---

# 13. UI-поведение

## Текущий статус diagnostics

Показывать:

```text
Следующий статус
Стоимость ремонта, ₽
Комментарий - необязательно
Кнопка изменения статуса
```

## Текущий статус не diagnostics

Поле стоимости можно:

```text
не показывать;
либо показывать только для информации.
```

Предпочтительно:

```text
показывать редактируемое поле только при current status=diagnostics.
```

Не менять UI других статусных переходов.

---

# 14. Сохранение суммы

После успешного перехода:

```text
estimated_repair_amount сохраняется в RepairOrder;
карточка показывает сохранённую сумму;
GET /api/repairs/{id} возвращает сумму;
последующие документы используют сохранённую сумму.
```

Если сотрудник ввёл новую сумму поверх старой:

```text
сохранить новое значение;
audit должен отражать изменение поля.
```

---

# 15. Audit

Одна успешная операция должна создать:

```text
repair.status_changed
```

И отразить изменение суммы согласно существующему audit contract.

Допустимо:

```json
{
  "old_status": "diagnostics",
  "new_status": "ready",
  "changed_fields": ["status", "estimated_repair_amount"],
  "old_estimated_repair_amount": null,
  "new_estimated_repair_amount": 2800
}
```

Не создавать два несвязанных audit события, если проект использует одно агрегированное событие.

Следовать существующему формату audit.

---

# 16. Существующая форма редактирования

Поле `estimated_repair_amount` в `/repairs/{id}/edit` можно оставить для ручной корректировки.

Но основной пользовательский сценарий должен работать без открытия этой страницы:

```text
карточка ремонта;
выбор статуса;
ввод суммы;
одна кнопка.
```

Не заставлять пользователя сначала сохранять `/edit`, затем возвращаться к статусу.

---

# 17. Не менять другие правила

Не менять:

```text
матрицу переходов;
terminal protection;
правила received;
правила waiting_customer;
правила waiting_parts;
правила in_repair;
правила ready;
правила unrepairable;
правила issued;
правила canceled.
```

Новое требование действует только:

```text
для переходов ИЗ diagnostics.
```

---

# 18. Core tests

Создать или обновить:

```text
core/tests/test_diagnostics_exit_amount_inline.py
```

Проверить:

```text
1. diagnostics -> ready с request amount=2800 проходит.
2. diagnostics -> ready с request amount=0 проходит.
3. diagnostics -> waiting_customer с amount=0 проходит.
4. diagnostics -> waiting_parts с amount=500 проходит.
5. diagnostics -> in_repair с amount=1000 проходит.
6. diagnostics -> unrepairable с amount=0 проходит.
7. diagnostics -> canceled с amount=0 проходит.
8. Все текстовые поля могут быть null.
9. Comment может быть null.
10. Пустой request amount и saved amount=null блокирует.
11. Пустой request amount и saved amount=2800 разрешает.
12. Request amount=0 не заменяется saved amount=2800.
13. Negative rejected.
14. Decimal rejected.
15. Status и amount сохраняются атомарно.
16. При ошибке amount/status/history/audit не меняются.
17. History создаётся при успехе.
18. Audit отражает сумму и статус.
19. Другие переходы не изменились.
```

---

# 19. Repairs-module tests

Создать или обновить:

```text
repairs-module/tests/test_diagnostics_exit_amount_inline_ui.py
```

Проверить:

```text
1. При diagnostics поле суммы находится в status form.
2. Поле пустое при saved null.
3. Поле показывает 0 при saved 0.
4. Поле показывает 2800 при saved 2800.
5. Поле type=number.
6. step=1.
7. min=0.
8. Одна форма отправляет status + amount + comment.
9. Не требуется переход на edit.
10. amount=0 проходит.
11. amount=2800 проходит.
12. Пустое поле блокируется при отсутствии saved amount.
13. Показывается новая русская ошибка.
14. Диагностика/работы/детали не проверяются.
15. Comment не required.
16. Для статусов не diagnostics поведение не сломано.
17. Raw Core JSON не показывается пользователю.
```

---

# 20. Runtime A - ready с 2800

Создать:

```text
ТЕСТ Stage05B-R2 READY 2800
```

Провести:

```text
received -> diagnostics;
на карточке выбрать ready;
в поле стоимости ввести 2800;
оставить comment пустым;
отправить одну форму.
```

Ожидаемо:

```text
status=ready;
estimated_repair_amount=2800;
text fields пустые;
history создана;
audit создан;
closed_at=null;
issued_at=null.
```

---

# 21. Runtime B - canceled с 0

Создать:

```text
ТЕСТ Stage05B-R2 CANCELED ZERO
```

Провести:

```text
received -> diagnostics;
выбрать canceled;
ввести 0;
comment пустой;
отправить.
```

Ожидаемо:

```text
status=canceled;
estimated_repair_amount=0;
0 не считается пустым.
```

---

# 22. Runtime C - waiting_parts

Создать:

```text
ТЕСТ Stage05B-R2 WAITING PARTS
```

Провести:

```text
received -> diagnostics;
выбрать waiting_parts;
ввести 1500;
отправить.
```

Ожидаемо:

```text
status=waiting_parts;
estimated_repair_amount=1500.
```

---

# 23. Runtime D - пустая сумма

Создать:

```text
ТЕСТ Stage05B-R2 EMPTY
```

Провести:

```text
received -> diagnostics;
saved amount=null;
оставить inline amount пустым;
выбрать любой следующий статус;
отправить.
```

Ожидаемо:

```text
blocked;
status=diagnostics;
amount=null;
history/audit не меняются;
русская ошибка отображается.
```

---

# 24. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05B_R2_REPAIR_AMOUNT_INSIDE_STATUS_CHANGE_FORM_PROMPT.md
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

# 25. Preflight

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
dc0d3b4
```

Если отличается - указать фактический.

---

# 26. Полные тесты

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

# 27. Safety scans

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

# 28. Документация

Создать:

```text
docs/stage05b_r2_inline_repair_amount_status_change.md
reports/stage05b_r2_inline_repair_amount_status_change_report.md
```

Обновить:

```text
logs/2026-08-05.md
```

Report:

```text
# Stage05B-R2 Inline Repair Amount in Status Change Report

## STATUS
## OWNER_REQUIREMENT
## PROMPT_DISCOVERY
## PREFLIGHT
## PREVIOUS_FLOW
## NEW_INLINE_FLOW
## CORE_REQUEST_CONTRACT
## ATOMIC_TRANSACTION
## ZERO_HANDLING
## EMPTY_AMOUNT_HANDLING
## ALL_DIAGNOSTICS_TRANSITIONS
## OPTIONAL_TEXT_FIELDS
## OPTIONAL_COMMENT
## UI
## AUDIT
## TESTS
## RUNTIME_READY_2800
## RUNTIME_CANCELED_ZERO
## RUNTIME_WAITING_PARTS
## RUNTIME_EMPTY
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

# 29. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/schemas.py
git add core/app/routers/repairs.py
git add core/tests/test_diagnostics_exit_amount_inline.py

git add repairs-module/app/routers/repairs.py
git add repairs-module/app/templates/repair_detail.html
git add repairs-module/tests/test_diagnostics_exit_amount_inline_ui.py

git add docs/stage05b_r2_inline_repair_amount_status_change.md
git add reports/stage05b_r2_inline_repair_amount_status_change_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05B_R2_REPAIR_AMOUNT_INSIDE_STATUS_CHANGE_FORM_PROMPT.md
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
git commit -m "Add repair amount to status change flow"
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

Готово только если:

```text
стоимость вводится прямо в status form;
не требуется открывать полный edit;
при diagnostics поле пустое, если amount=null;
saved 0 показывается как 0;
saved amount показывается в поле;
одна операция сохраняет amount и status;
операция атомарная;
для любого выхода из diagnostics amount обязателен;
0 допустим;
null блокирует;
diagnosis/work/parts необязательны;
comment необязателен;
матрица статусов не изменена;
другие переходы не сломаны;
Core safe tests PASS;
Inventory PASS;
Avito PASS;
Repairs PASS;
live DB не меняется от tests;
safety scans clean;
targeted commit;
push;
clean Git;
owner manual check required.
```

---

# 31. Owner check guide

```text
1. Открыть ремонт в статусе «Диагностика».
2. В блоке смены статуса найти поле «Стоимость ремонта, ₽».
3. Не открывать «Редактировать».
4. Выбрать «Готов».
5. Ввести 2800.
6. Оставить комментарий пустым.
7. Нажать смену статуса.
8. Проверить status=Готов и amount=2800.
9. Повторить для «Отменён» с amount=0.
10. Повторить для «Ожидание деталей» с amount=1500.
11. Оставить поле пустым и проверить блокировку.
```

---

# 32. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_R2_INLINE_REPAIR_AMOUNT_STATUS_CHANGE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05C_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_R2_INLINE_REPAIR_AMOUNT_STATUS_CHANGE_FAIL

BLOCKERS:
...
```
