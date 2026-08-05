# PROMPT - Техноребут / Stage05B-R1 Diagnostics-to-Ready Requires Only Repair Amount

## Роль

Ты senior FastAPI/Jinja2 developer, business-rule auditor и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно выполнить точечную доработку Stage05B.

Stage05C не начинать.

---

# 1. Уточнение владельца

При переходе ремонта:

```text
Диагностика -> Готов
```

не нужно требовать:

```text
комментарий к смене статуса;
результат диагностики;
перечень выполненных или предполагаемых работ;
перечень деталей и материалов;
любые другие текстовые поля.
```

Единственное обязательное условие:

```text
должна быть заполнена предполагаемая стоимость ремонта.
```

Поле:

```text
estimated_repair_amount
```

---

# 2. Главное правило

Переход разрешён, если:

```text
estimated_repair_amount is not null
```

Допустимые значения:

```text
0
1
500
2800
10000
```

Недопустимое состояние:

```text
estimated_repair_amount = null
```

Критически важно:

```text
0 - это заполненное допустимое значение;
0 нельзя считать пустым;
не использовать truthy/falsy проверку;
не использовать `if not estimated_repair_amount`;
использовать явную проверку `is None`.
```

---

# 3. Новое поведение перехода

## Разрешено

```text
status = diagnostics
estimated_repair_amount = 0
diagnosis_text = null
planned_works_text = null
planned_parts_text = null
comment = null
```

Результат:

```text
Диагностика -> Готов проходит.
```

Также разрешено:

```text
status = diagnostics
estimated_repair_amount = 2800
все текстовые поля пустые
comment пустой
```

Результат:

```text
Диагностика -> Готов проходит.
```

## Запрещено

```text
status = diagnostics
estimated_repair_amount = null
```

Результат:

```text
переход блокируется;
status остаётся diagnostics;
history не создаётся;
audit status change не создаётся.
```

---

# 4. Сообщение об ошибке

Убрать текущее сообщение:

```text
Для перехода из диагностики в статус 'Готов'
требуется указать комментарий с описанием выполненных работ
```

Новое сообщение:

```text
Для перехода в статус «Готов» укажите предполагаемую стоимость ремонта.
Можно указать 0 ₽.
```

HTTP:

```text
400 или 409
```

Использовать существующее соглашение Core для business-rule conflict.

---

# 5. Комментарий к переходу

Комментарий при:

```text
diagnostics -> ready
```

становится необязательным.

Если комментарий введён:

```text
сохранить его в RepairStatusHistory.comment.
```

Если комментарий не введён:

```text
переход всё равно разрешить;
history row создать с comment=null или пустым значением
согласно текущему контракту.
```

Не требовать автоматически сгенерированный комментарий.

---

# 6. Текстовые поля Stage05B

Поля:

```text
diagnosis_text
planned_works_text
planned_parts_text
```

остаются полностью необязательными.

Они не участвуют в разрешении перехода:

```text
diagnostics -> ready
```

Нельзя блокировать переход из-за:

```text
пустой диагностики;
пустого перечня работ;
пустого перечня деталей;
пустого комментария.
```

---

# 7. Предполагаемая стоимость

Поле:

```text
estimated_repair_amount
```

остаётся:

```text
nullable до заполнения;
integer;
min=0;
0 допустимо;
дробные значения запрещены;
отрицательные значения запрещены.
```

После заполнения `0` или любым другим допустимым integer переход в «Готов» разрешается.

---

# 8. Core validation

Обновить business-rule проверки в:

```text
POST /api/repairs/{repair_id}/status
```

Для перехода:

```text
diagnostics -> ready
```

проверять только:

```python
repair.estimated_repair_amount is not None
```

Не проверять:

```text
comment;
diagnosis_text;
planned_works_text;
planned_parts_text.
```

Проверку выполнить до изменения:

```text
repair.status;
updated_at;
history;
audit.
```

Операция должна оставаться атомарной.

---

# 9. UI

На карточке ремонта в статусе:

```text
Диагностика
```

опция:

```text
Готов
```

должна отображаться всегда.

При попытке перехода:

## Если сумма пустая

Показать русское сообщение:

```text
Для перехода в статус «Готов» укажите предполагаемую стоимость ремонта.
Можно указать 0 ₽.
```

Добавить удобную ссылку или кнопку:

```text
Указать стоимость ремонта
```

ведущую на:

```text
/repairs/{id}/edit
```

## Если сумма заполнена

Переход разрешить без обязательного комментария.

Поле комментария можно оставить:

```text
необязательным.
```

---

# 10. Не менять другие переходы

Не менять правила:

```text
received -> diagnostics;
in_repair -> ready;
ready -> issued;
terminal protection;
остальные переходы матрицы.
```

Если для других переходов комментарий уже обязателен по отдельному правилу, сохранить это правило.

Точечная доработка касается только:

```text
diagnostics -> ready
```

---

# 11. Core tests

Обновить:

```text
core/tests/test_repairs_status_matrix_complete.py
core/tests/test_repair_simple_diagnosis.py
```

или создать:

```text
core/tests/test_diagnostics_ready_amount_rule.py
```

Проверить:

```text
1. diagnostics -> ready с amount=null -> blocked.
2. status после ошибки остаётся diagnostics.
3. history count после ошибки не меняется.
4. audit status event после ошибки не создаётся.
5. diagnostics -> ready с amount=0 и comment=null -> PASS.
6. diagnostics -> ready с amount=1 и comment=null -> PASS.
7. diagnostics -> ready с amount=2800 и comment="" -> PASS.
8. diagnostics -> ready с пустыми diagnosis/work/parts -> PASS.
9. comment, если передан, сохраняется в history.
10. ready не закрывает repair.
11. closed_at остаётся null.
12. issued_at остаётся null.
13. другие status transitions не изменились.
```

---

# 12. Repairs-module tests

Создать или обновить:

```text
repairs-module/tests/test_diagnostics_ready_amount_rule_ui.py
```

Проверить:

```text
1. Опция «Готов» видна в diagnostics.
2. Comment field не required.
3. При пустой сумме показывается новое сообщение.
4. Старое сообщение про обязательный комментарий отсутствует.
5. Есть ссылка «Указать стоимость ремонта».
6. amount=0 разрешает переход.
7. amount=2800 разрешает переход.
8. Пустые diagnosis/work/parts не блокируют переход.
9. Введённый необязательный comment передаётся.
10. Русская ошибка не показывает raw Core JSON.
```

---

# 13. Runtime-сценарий A - пустая сумма

Создать test repair:

```text
ТЕСТ Stage05B-R1 EMPTY AMOUNT
```

Провести:

```text
received -> diagnostics;
diagnosis_text = null;
planned_works_text = null;
planned_parts_text = null;
estimated_repair_amount = null;
попытка diagnostics -> ready.
```

Ожидаемо:

```text
blocked;
новая русская ошибка;
status=diagnostics;
history/audit не изменились.
```

---

# 14. Runtime-сценарий B - сумма 0

На том же или новом ремонте указать:

```text
estimated_repair_amount = 0
```

Оставить пустыми:

```text
diagnosis_text;
planned_works_text;
planned_parts_text;
status comment.
```

Провести:

```text
diagnostics -> ready
```

Ожидаемо:

```text
HTTP 200;
status=ready;
history создана;
comment необязателен;
closed_at=null;
issued_at=null.
```

---

# 15. Runtime-сценарий C - обычная сумма

Создать test repair:

```text
ТЕСТ Stage05B-R1 AMOUNT 2800
```

Заполнить только:

```text
estimated_repair_amount=2800
```

Оставить все текстовые поля пустыми.

Провести:

```text
received -> diagnostics -> ready
```

Ожидаемо:

```text
успешно;
никаких требований к работам, деталям и comment.
```

---

# 16. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05B_R1_DIAGNOSTICS_READY_REQUIRES_ONLY_AMOUNT_PROMPT.md
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

# 17. Preflight

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
bfae593
```

Если отличается - указать фактический.

---

# 18. Полные тесты

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

# 19. Safety scans

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

# 20. Документация

Создать:

```text
docs/stage05b_r1_diagnostics_ready_amount_rule.md
reports/stage05b_r1_diagnostics_ready_amount_rule_report.md
```

Обновить:

```text
logs/2026-08-05.md
```

Report:

```text
# Stage05B-R1 Diagnostics-to-Ready Amount Rule Report

## STATUS
## OWNER_REQUIREMENT
## PROMPT_DISCOVERY
## PREFLIGHT
## PREVIOUS_RULE
## NEW_RULE
## ZERO_VALUE_HANDLING
## CORE_VALIDATION
## UI_BEHAVIOR
## OPTIONAL_TEXT_FIELDS
## OPTIONAL_STATUS_COMMENT
## TESTS
## RUNTIME_EMPTY_AMOUNT
## RUNTIME_ZERO
## RUNTIME_2800
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

# 21. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/routers/repairs.py
git add core/tests/test_repairs_status_matrix_complete.py
git add core/tests/test_diagnostics_ready_amount_rule.py

git add repairs-module/app/routers/repairs.py
git add repairs-module/app/templates/repair_detail.html
git add repairs-module/tests/test_diagnostics_ready_amount_rule_ui.py

git add docs/stage05b_r1_diagnostics_ready_amount_rule.md
git add reports/stage05b_r1_diagnostics_ready_amount_rule_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05B_R1_DIAGNOSTICS_READY_REQUIRES_ONLY_AMOUNT_PROMPT.md
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
git commit -m "Require repair amount before ready status"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 22. Definition of Done

Готово только если:

```text
diagnostics -> ready не требует comment;
diagnostics -> ready не требует diagnosis_text;
diagnostics -> ready не требует planned_works_text;
diagnostics -> ready не требует planned_parts_text;
единственный критерий - estimated_repair_amount is not None;
0 считается заполненным допустимым значением;
null блокирует переход;
при null status/history/audit не меняются;
новая русская ошибка отображается;
старая ошибка про комментарий удалена;
другие transition rules не изменены;
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

# 23. Owner check guide

```text
1. Открыть ремонт в статусе «Диагностика».
2. Оставить сумму ремонта пустой.
3. Попробовать перевести в «Готов».
4. Убедиться, что переход заблокирован.
5. Убедиться, что ошибка просит указать только сумму.
6. Указать сумму 0.
7. Не заполнять диагностику, работы, детали и комментарий.
8. Перевести в «Готов».
9. Убедиться, что переход прошёл.
10. Повторить с суммой 2800.
```

---

# 24. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_R1_DIAGNOSTICS_READY_AMOUNT_RULE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05C_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05B_R1_DIAGNOSTICS_READY_AMOUNT_RULE_FAIL

BLOCKERS:
...
```
