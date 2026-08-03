# PROMPT — Техноребут / Stage05A-R3 Default Intake Text and Diagnostics-to-Ready Transition

## Роль

Ты senior FastAPI/Jinja2 developer, domain workflow engineer, UX engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Выполни две точечные доработки Stage05A перед owner acceptance:

```text
1. Предзаполненные значения полей «Комплектность» и «Внешний вид».
2. Разрешённый переход ремонта «Диагностика -> Готов».
```

Stage05B не начинать.

---

# 1. Уточнение владельца — поля приёмки

В форме нового ремонта поля:

```text
Комплектность
Внешний вид
```

сейчас содержат примерный текст или перечень только как подсказку.

Требование:

```text
текущий примерный текст должен быть сразу записан
в поля как настоящее редактируемое значение по умолчанию.
```

Пользователь при приёмке:

```text
оставляет подходящие пункты;
удаляет то, чего нет;
дописывает недостающее;
может полностью очистить поле.
```

Это не placeholder.

---

# 2. Уточнение владельца — статус после диагностики

После статуса:

```text
Диагностика
```

нужно дополнительно предлагать:

```text
Готов
```

Причина:

```text
иногда неисправность устраняется непосредственно во время диагностики,
и отдельный этап «В ремонте» не нужен.
```

Новый разрешённый переход:

```text
diagnostics -> ready
```

---

# 3. Комментарий при diagnostics -> ready

Для перехода:

```text
diagnostics -> ready
```

комментарий должен быть обязательным.

Примеры:

```text
Неисправность устранена во время диагностики
Контакт восстановлен, дополнительный ремонт не требуется
После чистки и переподключения устройство работает
Сбой устранён сбросом настроек
```

Core должен отклонять пустой комментарий:

```text
HTTP 422 или HTTP 400
понятная ошибка
status не меняется
history не создаётся
```

Комментарий сохраняется в:

```text
RepairStatusHistory.comment
```

---

# 4. Обновлённая матрица переходов

Матрица Stage05A сохраняется, кроме одного нового перехода.

Должно быть:

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
        "ready",
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

Не добавлять другие новые переходы.

---

# 5. Главное правило для default-полей

Найти точные текущие примерные тексты, которые уже отображаются в полях:

```text
Комплектность
Внешний вид
```

И перенести их:

```text
из placeholder/help/example
в фактическое значение textarea/input новой формы.
```

Не придумывать новый текст, если текущий пример уже существует.

Использовать точную текущую формулировку, включая:

```text
цифры;
нумерацию;
переносы строк;
знаки препинания.
```

---

# 6. Ожидаемое поведение новой формы

Страница:

```text
http://localhost:8040/repairs/new
```

При первом открытии:

```text
«Комплектность» уже заполнена текущим примерным перечнем;
«Внешний вид» уже заполнен текущим примерным перечнем;
текст свободно редактируется;
можно удалить один пункт;
можно удалить весь текст;
можно дописать свой текст.
```

При submit сохраняется итоговый отредактированный текст.

---

# 7. Не использовать placeholder как значение

Недостаточно:

```html
<textarea placeholder="..."></textarea>
```

Нужно:

```html
<textarea>текущий текст по умолчанию</textarea>
```

или безопасная передача через Jinja context.

Placeholder можно оставить только как короткую подсказку.

---

# 8. Defaults только для нового ремонта

Значения по умолчанию применяются только:

```text
при первом GET /repairs/new;
когда пользователь ещё ничего не вводил.
```

На:

```text
/repairs/{id}/edit
```

показывать только сохранённые значения.

Запрещено:

```text
подставлять defaults поверх сохранённых данных;
подставлять defaults поверх сохранённой пустой строки.
```

---

# 9. Ошибка формы

При validation/Core error:

```text
сохранить введённые пользователем значения;
не восстанавливать defaults;
не возвращать удалённые пункты;
не терять очищенные поля.
```

Приоритет:

```text
1. submitted form data после ошибки;
2. сохранённые значения при edit;
3. defaults только на чистом первом GET новой формы.
```

---

# 10. Пустые значения разрешены

Пользователь может очистить:

```text
Комплектность
Внешний вид
```

Пустая строка должна корректно сохраниться согласно существующему Core contract:

```text
""
```

или:

```text
null
```

Defaults не должны возвращаться после submit.

---

# 11. Core не должен навязывать UI defaults

Проверить, что:

```text
completeness
appearance
```

остаются обычными пользовательскими полями.

Defaults задаются на уровне repairs-module UI.

Core API не должен автоматически подставлять UI-перечни, потому что:

```text
API-клиенты могут передавать пустое значение;
старые repairs не должны меняться;
edit не должен перезаписываться;
интеграции не должны получать неожиданные строки.
```

---

# 12. UI перехода diagnostics -> ready

На карточке ремонта со статусом:

```text
diagnostics
```

в списке разрешённых следующих статусов должна появиться кнопка/опция:

```text
Готов
```

При выборе:

```text
обязательно показать поле комментария;
пустой комментарий не отправлять;
вывести русскую ошибку;
после успеха показать status=Готов;
в истории показать комментарий.
```

---

# 13. Core API перехода diagnostics -> ready

Endpoint:

```text
POST /api/repairs/{repair_id}/status
```

Request:

```json
{
  "status": "ready",
  "comment": "Неисправность устранена во время диагностики"
}
```

Ожидаемо:

```text
HTTP 200;
status = ready;
updated_at изменён;
history row создана;
old_status = diagnostics;
new_status = ready;
comment сохранён;
audit repair.status_changed создан.
```

Без comment:

```text
HTTP 400/422;
status остаётся diagnostics;
history count не меняется;
audit event не создаётся.
```

---

# 14. Тесты Core — новая матрица

Обновить:

```text
core/tests/test_repairs_status_matrix_complete.py
```

Добавить:

```text
diagnostics -> ready с comment проходит;
diagnostics -> ready без comment отклоняется;
diagnostics -> ready с whitespace-only comment отклоняется;
history создаётся только при успешном переходе;
audit создаётся только при успешном переходе;
ready timestamps не закрывают repair;
после ready доступны in_repair и issued.
```

Не ломать остальные переходы.

---

# 15. Тесты repairs-module — defaults

Создать/обновить:

```text
repairs-module/tests/test_repair_intake_defaults.py
```

Проверить:

```text
1. GET /repairs/new возвращает 200.
2. completeness содержит точный текущий default.
3. appearance содержит точный текущий default.
4. Это содержимое textarea, а не только placeholder.
5. Сохраняются цифры, нумерация и переносы строк.
6. Изменённый текст отправляется.
7. Полностью очищенное поле отправляется пустым.
8. При ошибке изменённый текст сохраняется.
9. При ошибке очищенное поле остаётся пустым.
10. Edit показывает сохранённый текст.
11. Edit не подставляет default поверх пустого значения.
12. Пользовательский HTML экранируется.
```

---

# 16. Тесты repairs-module — diagnostics -> ready

Создать/обновить:

```text
repairs-module/tests/test_repair_diagnostics_ready_ui.py
```

Проверить:

```text
1. Для diagnostics показана опция «Готов».
2. Для received эта опция не показана.
3. При diagnostics -> ready отображается comment field.
4. Пустой comment блокируется.
5. Русская ошибка понятна.
6. Успешный переход открывает карточку со статусом «Готов».
7. История содержит comment.
8. Другие переходы не сломаны.
```

---

# 17. Безопасный Jinja rendering

Текст fields должен:

```text
корректно отображать переносы;
экранироваться Jinja;
не позволять HTML/JS injection;
не ломать textarea.
```

Не использовать:

```text
|safe
```

для пользовательских значений.

---

# 18. Runtime-проверка defaults

Открыть:

```text
http://localhost:8040/repairs/new
```

Проверить:

## Сценарий A

```text
оба поля заполнены точными текущими перечнями;
это реальные значения, не placeholder.
```

## Сценарий B

```text
удалить один пункт completeness;
создать test repair;
в карточке удалённого пункта нет.
```

## Сценарий C

```text
полностью очистить appearance;
создать test repair;
default не восстановился.
```

## Сценарий D

```text
вызвать validation error;
изменённые/очищенные значения сохранились.
```

Тестовую запись пометить:

```text
ТЕСТ Stage05A-R3 DEFAULT FIELDS
```

---

# 19. Runtime-проверка diagnostics -> ready

Создать test repair:

```text
ТЕСТ Stage05A-R3 DIAGNOSTICS READY
```

Провести:

```text
received -> diagnostics
diagnostics -> ready
```

Комментарий:

```text
Неисправность устранена во время диагностики
```

Проверить:

```text
status=ready;
history содержит comment;
repair не закрыт;
issued_at/closed_at не назначены;
в UI отображается «Готов».
```

Отдельно проверить пустой comment:

```text
HTTP 400/422;
status/history не меняются.
```

---

# 20. Регрессии

Не сломать:

```text
создание ремонта;
редактирование;
поиск;
фильтры;
остальные статусы;
Customer reuse;
history;
terminal protection;
Core API;
Inventory;
Avito;
Sales.
```

---

# 21. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05A_R3_DEFAULT_FIELDS_AND_DIAGNOSTICS_READY_TRANSITION_PROMPT.md
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

# 22. Preflight

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
9b431ad
```

Если отличается — указать фактический.

---

# 23. Аудит текущей реализации

Проверить:

```text
core/app/routers/repairs.py
core/app/schemas.py
core/tests/test_repairs_status_matrix_complete.py

repairs-module/app/routers/repairs.py
repairs-module/app/templates/repair_new.html
repairs-module/app/templates/repair_edit.html
repairs-module/app/templates/repair_detail.html
repairs-module/tests/
```

Зафиксировать:

```text
точный текущий completeness example;
точный текущий appearance example;
где они хранятся;
текущую diagnostics transition matrix;
текущую UI-логику allowed statuses.
```

---

# 24. Docker rebuild

```powershell
docker compose up --build -d --force-recreate core repairs-module
docker compose up -d inventory-sales-module avito-module admin-shell
docker compose ps
```

---

# 25. Полные тесты

Core:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

Inventory:

```powershell
docker compose exec -T inventory-sales-module pytest
```

Avito:

```powershell
docker compose exec -T avito-module pytest
```

Repairs:

```powershell
docker compose exec -T repairs-module pytest
```

Проверить live DB до/после tests:

```text
SHA256;
product count;
sale count;
customer count;
repair count;
history count.
```

Значения должны совпасть.

---

# 26. Safety scans

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

# 27. Документация

Создать:

```text
docs/stage05a_r3_default_fields_diagnostics_ready.md
reports/stage05a_r3_default_fields_diagnostics_ready_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report:

```text
# Stage05A-R3 Default Fields and Diagnostics-to-Ready Report

## STATUS
## OWNER_REQUIREMENTS
## PROMPT_DISCOVERY
## PREFLIGHT
## EXACT_COMPLETENESS_DEFAULT
## EXACT_APPEARANCE_DEFAULT
## DEFAULT_FORM_BEHAVIOR
## VALIDATION_ERROR_PRESERVATION
## EDIT_FORM_BEHAVIOR
## EMPTY_VALUE_BEHAVIOR
## STATUS_MATRIX_BEFORE
## STATUS_MATRIX_AFTER
## DIAGNOSTICS_TO_READY_COMMENT_RULE
## CORE_TESTS
## REPAIRS_UI_TESTS
## RUNTIME_DEFAULT_FIELDS
## RUNTIME_DIAGNOSTICS_READY
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

# 28. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/routers/repairs.py
git add core/app/schemas.py
git add core/tests/test_repairs_status_matrix_complete.py

git add repairs-module/app/routers/repairs.py
git add repairs-module/app/templates/repair_new.html
git add repairs-module/app/templates/repair_edit.html
git add repairs-module/app/templates/repair_detail.html
git add repairs-module/tests/test_repair_intake_defaults.py
git add repairs-module/tests/test_repair_diagnostics_ready_ui.py

git add docs/stage05a_r3_default_fields_diagnostics_ready.md
git add reports/stage05a_r3_default_fields_diagnostics_ready_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05A_R3_DEFAULT_FIELDS_AND_DIAGNOSTICS_READY_TRANSITION_PROMPT.md
git add -f logs/2026-08-03.md
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
git commit -m "Improve repair intake defaults and diagnostics flow"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 29. Definition of Done

Готово только если:

```text
current completeness example стал value;
current appearance example стал value;
формулировки и нумерация сохранены точно;
поля редактируются и очищаются;
defaults не возвращаются после очистки;
validation error сохраняет ввод;
edit показывает сохранённые значения;
Core не навязывает UI defaults;

diagnostics -> ready разрешён;
comment для diagnostics -> ready обязателен;
пустой comment отклоняется;
history содержит comment;
audit создаётся;
ready не закрывает repair;
UI предлагает «Готов» после диагностики;

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

# 30. Owner check guide

```text
1. Открыть http://localhost:8040/repairs/new
2. Проверить, что «Комплектность» и «Внешний вид» уже заполнены
3. Удалить один пункт и создать repair
4. Убедиться, что удалённый пункт не вернулся
5. Очистить одно поле и убедиться, что default не восстановился
6. Создать новый repair
7. Перевести «Принят -> Диагностика»
8. Выбрать «Готов»
9. Проверить обязательный комментарий
10. Ввести комментарий и завершить переход
11. Проверить status «Готов» и историю
```

---

# 31. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R3_DEFAULT_FIELDS_AND_DIAGNOSTICS_READY_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05B_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R3_DEFAULT_FIELDS_AND_DIAGNOSTICS_READY_FAIL

BLOCKERS:
...
```
