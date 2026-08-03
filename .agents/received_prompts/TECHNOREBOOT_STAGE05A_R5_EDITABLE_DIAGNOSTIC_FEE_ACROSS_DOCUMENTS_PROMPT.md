# PROMPT - Техноребут / Stage05A-R5 Editable Diagnostic Fee Across Repair Documents

## Роль

Ты senior FastAPI developer, SQLite migration engineer, Jinja2 UX developer, print-document engineer и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно выполнить точечную доработку Stage05A:

```text
добавить стоимость диагностики в ремонтный заказ;
по умолчанию 500 рублей;
разрешить изменить сумму при первичном оформлении;
использовать сохраненную сумму во всех связанных экранах и документах.
```

Stage05B не начинать.

---

# 1. Требование владельца

При первоначальном оформлении ремонта должно быть отдельное поле:

```text
Стоимость диагностики
```

Поведение:

```text
по умолчанию: 500;
сотрудник может изменить сумму;
сохраняется сумма конкретного ремонтного заказа;
после сохранения эта сумма используется везде для данного ремонта.
```

Под «везде» понимается минимум:

```text
Core API;
форма новой приёмки;
форма редактирования открытого ремонта;
карточка ремонта;
печатный наряд-заказ;
краткие условия на первой странице;
отрывной талон;
подробные условия на второй странице;
другие существующие представления ремонта, где упоминается стоимость диагностики.
```

---

# 2. Главное бизнес-правило

Стоимость диагностики является snapshot-полем конкретного RepairOrder.

Пример:

```text
Ремонт A:
diagnostic_fee = 500

Ремонт B:
diagnostic_fee = 800
```

Документы ремонта A всегда показывают:

```text
500
```

Документы ремонта B всегда показывают:

```text
800
```

Изменение суммы в одном ремонте не должно менять другие ремонты.

---

# 3. Значение по умолчанию

Для нового ремонта:

```text
500 рублей
```

Требования:

```text
значение уже заполнено в форме;
это реальное value, не placeholder;
значение можно заменить;
значение можно выделить и ввести новое;
Core также безопасно применяет default=500,
если API-клиент не передал сумму.
```

Не хранить default только в HTML.

Нужен единый источник значения по умолчанию в Core, чтобы:

```text
UI и API не расходились;
новые интеграции получали тот же default;
в production templates не было нескольких независимых hardcode.
```

Рекомендуется добавить в:

```text
GET /api/repairs/options
```

поле:

```json
{
  "default_diagnostic_fee": 500
}
```

Repairs-module должен получать default через Core HTTP API.

Допустим совместимый централизованный механизм, если он уже существует.

---

# 4. Название поля

Предпочтительное название:

```text
diagnostic_fee
```

или, если денежные поля проекта имеют другой установленный стиль:

```text
diagnostic_price
diagnostic_amount
```

Выбрать одно имя и использовать его одинаково в:

```text
DB model;
migration;
Pydantic schemas;
Core API;
Core tests;
repairs-module;
templates;
print documents;
reports/docs.
```

В отчете указать фактическое имя.

---

# 5. Денежный тип

Сначала провести аудит существующего денежного соглашения проекта.

Использовать тот же безопасный подход, который принят для:

```text
Product.price;
Sale.total_amount;
денежных настроек.
```

Требования к значению:

```text
число;
не NaN;
не Infinity;
не отрицательное;
не строка с произвольным текстом;
корректно сериализуется в JSON;
корректно сохраняется в SQLite;
не получает двоичную ошибку отображения вроде 499.999999.
```

Если проект поддерживает только целые рубли:

```text
использовать целое число;
input step=1.
```

Если проект уже поддерживает копейки:

```text
разрешить не более двух знаков после запятой;
использовать Decimal-safe validation;
input step=0.01.
```

Не вводить новый несовместимый денежный стандарт без необходимости.

---

# 6. Допустимые значения

Минимум:

```text
0
```

Нулевая диагностика допустима:

```text
бесплатная диагностика;
акция;
решение сотрудника.
```

Запрещены:

```text
отрицательные значения;
пустая строка при submit;
буквы;
NaN;
Infinity;
слишком большое значение, выходящее за безопасный диапазон типа.
```

Для пустого поля форма должна показать понятную русскую ошибку:

```text
Укажите стоимость диагностики
```

Для отрицательной суммы:

```text
Стоимость диагностики не может быть отрицательной
```

---

# 7. Изменение после создания

Стоимость должна быть доступна:

```text
при создании ремонта;
при редактировании открытого ремонта.
```

Редактирование разрешено для тех же незакрытых статусов, что и остальные бизнес-поля RepairOrder.

Для статусов:

```text
issued;
canceled.
```

изменение блокируется существующей terminal protection:

```text
HTTP 409.
```

После изменения открытого ремонта:

```text
карточка сразу показывает новую сумму;
вновь открытый печатный документ показывает новую сумму;
старые сохраненные PDF/бумажные копии, естественно, не изменяются;
audit event repair.updated создается.
```

---

# 8. Core DB migration

Добавить поле в `repair_orders`.

Пример:

```text
diagnostic_fee
```

Миграция только additive.

Для существующих ремонтных заказов:

```text
backfill = 500
```

Причина:

```text
до появления поля все существующие печатные документы
использовали фиксированное условие диагностики 500 рублей.
```

Требования:

```text
поле не null после миграции;
повторный запуск миграции идемпотентен;
существующие repair IDs не меняются;
products/sales/customers не меняются;
никаких DROP;
никакого DELETE;
никакого пересоздания live DB.
```

До миграции создать backup:

```text
C:\tbootit-data-backups\stage05a-r5\<timestamp>\
```

Записать:

```text
BACKUP_PATH
BACKUP_SHA256
```

---

# 9. Core model и schemas

Обновить:

```text
RepairOrder model;
RepairCreate;
RepairUpdate;
RepairRead / response schema;
repair list item schema, если отдельная;
options response.
```

## RepairCreate

Клиент может передать:

```json
{
  "diagnostic_fee": 750
}
```

Если поле отсутствует:

```text
Core устанавливает 500.
```

## RepairUpdate

Разрешить изменение:

```json
{
  "diagnostic_fee": 900
}
```

Только для незакрытого ремонта.

## RepairRead

Всегда возвращать:

```json
{
  "diagnostic_fee": 500
}
```

---

# 10. Core API

Проверить минимум:

```text
POST /api/repairs
GET /api/repairs
GET /api/repairs/{id}
PATCH /api/repairs/{id}
GET /api/repairs/by-number/{number}
GET /api/repairs/options
```

Во всех релевантных response должно присутствовать значение.

`GET /api/repairs/options`:

```json
{
  "default_diagnostic_fee": 500
}
```

Не использовать UI hardcode как единственный default.

---

# 11. Audit

При создании ремонта audit должен содержать:

```text
repair_id;
diagnostic_fee;
```

без полного необработанного request body.

При изменении суммы:

```text
repair.updated
```

желательно с безопасным payload:

```json
{
  "changed_fields": ["diagnostic_fee"],
  "old_diagnostic_fee": 500,
  "new_diagnostic_fee": 800
}
```

Следовать существующему audit contract проекта.

---

# 12. Форма новой приёмки

Страница:

```text
http://localhost:8040/repairs/new
```

Добавить поле:

```text
Стоимость диагностики, ₽
```

Требования:

```text
default value = значение из Core options;
тип number;
понятная подпись;
не placeholder;
доступно с клавиатуры;
сохраняется при submit;
сохраняется при validation/Core error;
0 не заменяется обратно на 500;
кастомная сумма не заменяется обратно на 500.
```

Разместить поле логично рядом с:

```text
Приоритет;
основными условиями приема;
либо отдельным блоком «Условия диагностики».
```

---

# 13. Форма редактирования

Страница:

```text
/repairs/{id}/edit
```

Показывает:

```text
сохраненную сумму конкретного ремонта.
```

Запрещено:

```text
подставлять default=500 поверх сохраненных 0/750/800;
терять значение после ошибки;
менять сумму закрытого ремонта.
```

---

# 14. Карточка ремонта

На:

```text
/repairs/{id}
```

показать отдельную строку:

```text
Стоимость диагностики: 500 ₽
```

или:

```text
Стоимость диагностики: 500 рублей
```

Использовать общий денежный formatter проекта.

Не показывать:

```text
500.0;
500.00 без необходимости;
499.999999.
```

---

# 15. Печатный наряд-заказ

Текущий шаблон:

```text
repairs-module/app/templates/repair_print_order.html
```

Сейчас содержит фиксированное условие:

```text
Стоимость диагностики при отказе от ремонта
или невозможности ремонта - 500 рублей.
```

Заменить фиксированное число на `repair.diagnostic_fee`.

---

# 16. Все места печатного документа

Динамическая сумма должна использоваться во всех местах, где сейчас упомянута диагностика:

```text
1. Краткие условия на первой странице.
2. Отрывной талон.
3. Подробные условия на второй странице,
   если там присутствует стоимость диагностики.
4. Любой отдельный блок стоимости диагностики.
```

Для ремонта с `diagnostic_fee=800` документ нигде не должен продолжать показывать старые `500`.

Требование:

```text
в production template не остается буквальный текст
«500 рублей» как договорная сумма диагностики.
```

Допустимы:

```text
migration default;
Core constant;
tests default;
документация об историческом default.
```

---

# 17. Форматирование суммы в документах

Сохранять формулировку условия, меняя только сумму.

Пример:

```text
Стоимость диагностики при отказе от ремонта или невозможности ремонта -
800 рублей.
```

Допустим универсальный формат:

```text
800 ₽
```

только если он используется одинаково во всем документе.

Предпочтительно использовать общий helper:

```text
format_money
```

или существующий денежный formatter проекта.

Для 0:

```text
0 рублей
```

или:

```text
0 ₽
```

Не выводить:

```text
None;
null;
NaN;
500.0.
```

---

# 18. Отрывной талон

Отрывной талон должен содержать ту же сумму, что и основной документ.

Пример:

```text
Стоимость диагностики при отказе от ремонта или невозможности ремонта -
750 рублей.
```

Нельзя:

```text
в основном наряд-заказе 750;
в талоне 500.
```

---

# 19. Юридический текст

Меняется только числовая сумма диагностики.

Остальной согласованный владельцем текст Stage05A-R4 не менять.

Запрещено:

```text
менять срок 3 дня;
менять срок 45 дней;
менять порог согласования 1500 рублей;
менять 14 дней;
менять пеню 50 рублей;
менять 3 месяца;
добавлять новые условия;
переписывать юридический текст.
```

В отчете:

```text
LEGAL_TEXT_CHANGE:
ONLY_DIAGNOSTIC_FEE_VALUE_BECAME_REPAIR_SPECIFIC
```

---

# 20. Поиск hardcode

Выполнить:

```powershell
git grep -n -I "500 рублей\|500 руб\|500 ₽\|diagnostic.*500" -- core repairs-module
```

Классифицировать каждый match:

```text
allowed default constant;
allowed migration backfill;
allowed tests;
allowed documentation;
forbidden production document hardcode.
```

После исправления:

```text
FORBIDDEN_PRODUCTION_DIAGNOSTIC_FEE_HARDCODE_MATCHES: 0
```

---

# 21. Core tests

Создать:

```text
core/tests/test_repair_diagnostic_fee.py
```

Покрыть:

```text
1. Create без diagnostic_fee -> 500.
2. Create с 750 -> 750.
3. Create с 0 -> 0.
4. Negative -> 422/400.
5. Empty/invalid -> 422.
6. Read detail возвращает сумму.
7. List возвращает сумму.
8. By-number возвращает сумму.
9. PATCH 500 -> 800.
10. PATCH 800 -> 0.
11. PATCH terminal repair -> 409.
12. Audit create содержит сумму.
13. Audit update содержит изменение суммы.
14. Options возвращает default=500.
15. Existing rows backfilled 500.
16. Migration idempotent.
17. Другие repair rows не меняются.
```

---

# 22. Repairs-module tests

Создать:

```text
repairs-module/tests/test_repair_diagnostic_fee_ui.py
```

Покрыть:

```text
1. New form содержит поле.
2. New form default=500 из Core options.
3. Это value, не placeholder.
4. Submit custom 750 передает 750.
5. Submit 0 передает 0.
6. Validation error сохраняет 750.
7. Validation error сохраняет 0.
8. Negative показывает русскую ошибку.
9. Edit form показывает сохраненные 800.
10. Edit form не заменяет 0 на 500.
11. Detail показывает сохраненную сумму.
12. Closed repair не позволяет изменение.
```

---

# 23. Print tests

Обновить:

```text
repairs-module/tests/test_repair_print_order.py
```

Проверить два ремонта.

## Repair A

```text
diagnostic_fee=500
```

Во всех блоках:

```text
500
```

## Repair B

```text
diagnostic_fee=800
```

Во всех блоках:

```text
800
```

И отдельно:

```text
в HTML Repair B нет договорного текста с 500;
основной блок и отрывной талон совпадают;
условия второй страницы совпадают;
нет None/null;
нет внутренней заметки;
остальной юридический текст не изменен.
```

---

# 24. Runtime-сценарий A - default

Создать через UI:

```text
ТЕСТ Stage05A-R5 DIAGNOSTIC DEFAULT
```

Не менять поле стоимости.

Ожидаемо:

```text
API: 500;
карточка: 500;
print page 1: 500;
отрывной талон: 500;
page 2: 500, если сумма там упоминается.
```

---

# 25. Runtime-сценарий B - custom

Создать через UI:

```text
ТЕСТ Stage05A-R5 DIAGNOSTIC CUSTOM
```

Установить:

```text
800
```

Ожидаемо:

```text
API: 800;
карточка: 800;
print page 1: 800;
отрывной талон: 800;
page 2: 800, если сумма там упоминается;
в print HTML нет старого договорного 500.
```

---

# 26. Runtime-сценарий C - edit

На открытом test repair изменить:

```text
800 -> 650
```

Ожидаемо:

```text
API detail: 650;
карточка: 650;
заново открытый print document: 650;
audit repair.updated;
другой ремонт остается 500.
```

---

# 27. Runtime-сценарий D - zero

Создать или изменить открытый test repair:

```text
diagnostic_fee=0
```

Ожидаемо:

```text
сохраняется 0;
не заменяется на 500;
карточка и документы показывают 0;
нет ошибки truthy/falsy в Jinja или Python.
```

---

# 28. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05A_R5_EDITABLE_DIAGNOSTIC_FEE_ACROSS_DOCUMENTS_PROMPT.md
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

В отчете:

```text
PROMPT_SEARCH_DONE
PROMPT_USED
PROMPT_SOURCE
PROMPT_LOCAL_COPY
PROMPT_SHA256
```

---

# 29. Preflight

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

Ожидаемый исходный HEAD:

```text
277e680
```

Если отличается - указать фактический.

---

# 30. Backup и live DB safety

До migration:

```text
создать backup;
снять live DB SHA256;
products count;
sales count;
customers count;
repairs count;
repair history count;
audit count.
```

После migration:

```text
products/sales/customers unchanged;
repair IDs unchanged;
repair count unchanged;
all repairs have diagnostic_fee=500 unless intentionally changed later;
migration second run produces no changes.
```

---

# 31. Полные тесты

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

До и после tests сравнить:

```text
LIVE_DB_SHA256;
product count;
sale count;
customer count;
repair count;
history count;
audit count.
```

Все значения должны совпасть.

---

# 32. Safety scans

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

# 33. Документация

Создать:

```text
docs/stage05a_r5_editable_diagnostic_fee.md
reports/stage05a_r5_editable_diagnostic_fee_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Отчет:

```text
# Stage05A-R5 Editable Diagnostic Fee Report

## STATUS
## OWNER_REQUIREMENT
## PROMPT_DISCOVERY
## PREFLIGHT
## MONEY_CONVENTION
## FIELD_NAME
## DATABASE_MIGRATION
## EXISTING_REPAIR_BACKFILL
## DEFAULT_SOURCE
## CORE_API
## CREATE_FORM
## EDIT_FORM
## REPAIR_DETAIL
## PRINT_DOCUMENT
## DETACHABLE_TICKET
## DETAILED_TERMS
## HARDCODE_SCAN
## AUDIT_EVENTS
## CORE_TESTS
## REPAIRS_TESTS
## PRINT_TESTS
## RUNTIME_DEFAULT_500
## RUNTIME_CUSTOM_800
## RUNTIME_EDIT_650
## RUNTIME_ZERO
## LIVE_DB_TEST_ISOLATION
## SAFETY_SCANS
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_CHECK_GUIDE
## FINAL_STATUS
```

Указать:

```text
LEGAL_TEXT_CHANGE:
ONLY_DIAGNOSTIC_FEE_VALUE_BECAME_REPAIR_SPECIFIC
```

---

# 34. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/routers/repairs.py
git add core/app/services/repair_migration.py
git add core/tests/test_repair_diagnostic_fee.py

git add repairs-module/app/core_client.py
git add repairs-module/app/routers/repairs.py
git add repairs-module/app/templates/repair_new.html
git add repairs-module/app/templates/repair_edit.html
git add repairs-module/app/templates/repair_detail.html
git add repairs-module/app/templates/repair_print_order.html
git add repairs-module/tests/test_repair_diagnostic_fee_ui.py
git add repairs-module/tests/test_repair_print_order.py

git add docs/stage05a_r5_editable_diagnostic_fee.md
git add reports/stage05a_r5_editable_diagnostic_fee_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05A_R5_EDITABLE_DIAGNOSTIC_FEE_ACROSS_DOCUMENTS_PROMPT.md
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
git commit -m "Add editable repair diagnostic fee"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 35. Definition of Done

Готово только если:

```text
RepairOrder хранит diagnostic fee;
default нового ремонта = 500;
default централизован в Core;
форма новой приёмки заполнена 500;
сумму можно изменить;
0 сохраняется;
отрицательная сумма блокируется;
ошибка формы сохраняет значение;
edit открытого ремонта работает;
terminal repair не редактируется;
API возвращает сумму;
карточка показывает сумму;
печатный документ использует сумму ремонта;
отрывной талон использует ту же сумму;
все договорные упоминания используют одну сумму;
старые repairs backfilled 500;
изменение одного ремонта не меняет другие;
нет production hardcode договорного 500;
остальной юридический текст не изменен;
migration additive и идемпотентна;
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

# 36. Owner check guide

```text
1. Открыть http://localhost:8040/repairs/new
2. Проверить поле «Стоимость диагностики, ₽» со значением 500
3. Создать ремонт без изменения суммы
4. Проверить 500 в карточке и всех частях печатного документа
5. Создать второй ремонт со стоимостью 800
6. Проверить 800 в карточке, основном наряд-заказе и отрывном талоне
7. Убедиться, что в документе второго ремонта не осталось договорного 500
8. Изменить открытый ремонт с 800 на 650
9. Снова открыть печать и проверить 650
10. Проверить, что первый ремонт по-прежнему показывает 500
11. Проверить сохранение значения 0
12. Проверить ошибку при отрицательном значении
```

---

# 37. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R5_EDITABLE_DIAGNOSTIC_FEE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05B_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R5_EDITABLE_DIAGNOSTIC_FEE_FAIL

BLOCKERS:
...
```
