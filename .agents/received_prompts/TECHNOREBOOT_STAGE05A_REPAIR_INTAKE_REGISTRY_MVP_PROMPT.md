# PROMPT — Техноребут / Stage05A Repair Intake and Registry MVP

## Роль

Ты senior solution architect, FastAPI backend engineer, SQLite data-integrity engineer, Jinja2 fullstack developer, Docker engineer и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — начать следующий крупный модуль системы:

```text
Stage05A — Приём техники в ремонт и реестр ремонтных заказов
```

Это первый этап модуля ремонтов. Не реализовывать диагностику, смету, запчасти, оплату и выдачу сверх указанного scope.

---

# 1. Принятое состояние проекта

Владелец принял:

```text
Stage04J-R1 — быстрое добавление товаров в корзину
и локальная кнопка «Перейти в корзину» возле добавленного товара.
```

Последний подтверждённый commit:

```text
0f0ab37
```

Принятые возможности продаж:

```text
товары и остатки;
корзина;
продажа;
способы оплаты;
гарантия;
чеки;
отчёты;
отмена продажи;
возврат товара;
переоформление;
штрихкоды;
сканер;
ценники 58×40;
быстрое добавление без перехода.
```

Следующий модуль по архитектурному плану:

```text
ремонты.
```

---

# 2. Архитектурные принципы

Проект строго модульный:

```text
Core API + DB владеет данными и бизнес-логикой.
repairs-module работает с Core только через HTTP API.
Прямой доступ repairs-module к Core DB запрещён.
Каждый модуль работает в отдельном Docker-контейнере.
Во время разработки всё работает локально.
Позже контейнеры будут развёрнуты на внешнем сервере.
```

Новая структура:

```text
core
inventory-sales-module
avito-module
admin-shell
repairs-module
```

Предлагаемый порт:

```text
repairs-module: 8040
```

Если порт занят или проект уже закрепил другой порт — выбрать свободный, документировать причину и обновить ссылки.

---

# 3. Цель Stage05A

Создать минимально полноценный рабочий процесс:

```text
1. Принять технику клиента в ремонт.
2. Автоматически присвоить номер ремонтного заказа.
3. Сохранить данные клиента и устройства.
4. Сохранить заявленную неисправность, комплектность и внешний вид.
5. Показать список ремонтных заказов.
6. Открыть карточку ремонта.
7. Менять разрешённые данные.
8. Переводить ремонт по статусам.
9. Хранить историю статусов.
10. Искать и фильтровать ремонты.
11. Работать через отдельный repairs-module.
12. Добавить переход в модуль из главного меню.
```

---

# 4. Что НЕ входит в Stage05A

Не реализовывать:

```text
диагностические работы и заключения;
смету;
согласование цены с клиентом;
список выполненных работ;
списание запчастей;
резервирование товаров со склада;
оплату ремонта;
кассовую продажу услуг;
финансовые отчёты ремонтов;
SMS/Telegram уведомления;
фотографии устройства;
электронную подпись;
печатный акт приёма;
гарантию на ремонт;
публичное отслеживание ремонта клиентом;
пароли, PIN-коды и графические ключи устройства.
```

Эти функции будут отдельными этапами Stage05B–Stage05D.

Критически:

```text
не хранить пароль устройства в обычном текстовом поле;
не добавлять поле password/device_password/pin.
```

На Stage05A допускается только:

```text
access_code_provided: true/false
```

без сохранения самого секрета.

---

# 5. Модель RepairOrder

Добавить в Core сущность ремонтного заказа.

Минимальные поля:

```text
id
number
status

customer_id nullable
customer_name
customer_phone
customer_email nullable

device_type
brand nullable
model nullable
serial_number nullable

reported_issue
completeness nullable
appearance nullable
customer_comment nullable
internal_note nullable

access_code_provided boolean

assigned_to nullable
priority

accepted_at
created_at
updated_at
closed_at nullable
issued_at nullable
canceled_at nullable
```

Ограничения:

```text
number unique, indexed, immutable;
customer_name required;
customer_phone required;
device_type required;
reported_issue required;
status required;
priority из allowlist;
timestamps назначаются сервером;
закрытые записи нельзя бесконтрольно редактировать;
пароли и секреты запрещены.
```

---

# 6. Номер ремонта

Core генерирует номер автоматически.

Рекомендуемый формат:

```text
R-20260803-0001
```

Где:

```text
R — ремонт;
20260803 — дата приёма;
0001 — последовательный номер за день.
```

Допустим более простой формат:

```text
R-000001
```

Но формат должен быть:

```text
читаемым;
уникальным;
генерироваться только Core;
не зависеть от клиента;
не приниматься слепо из UI;
иметь regression tests.
```

Документировать выбранный формат.

---

# 7. Клиент

Сначала провести аудит существующей customer-модели Core.

Если Core уже имеет клиентов:

```text
использовать существующий customer_id;
позволить выбрать клиента;
позволить создать нового клиента через существующий Core API;
не создавать вторую таблицу клиентов внутри repairs-module.
```

При этом в RepairOrder сохранить snapshot:

```text
customer_name
customer_phone
customer_email
```

Чтобы историческая карточка ремонта не изменилась при последующем редактировании клиента.

Если customer API пока недостаточен:

```text
добавить только минимальные безопасные Core endpoints;
не создавать обходную локальную БД.
```

---

# 8. Типы устройств

На Stage05A использовать простой allowlist с возможностью ручного значения:

```text
Ноутбук
Системный блок
Моноблок
Монитор
Принтер
МФУ
Планшет
Телефон
Сетевое оборудование
Комплектующее
Другое
```

UI полностью на русском.

---

# 9. Приоритет

Allowlist:

```text
normal
urgent
```

Русские подписи:

```text
Обычный
Срочный
```

По умолчанию:

```text
normal
```

Срочный ремонт должен визуально выделяться, но Stage05A не рассчитывает доплату.

---

# 10. Статусы ремонта

Использовать статусы:

```text
received
diagnostics
waiting_customer
waiting_parts
in_repair
ready
unrepairable
issued
canceled
```

Русские подписи:

```text
received         — Принят
diagnostics      — Диагностика
waiting_customer — Ожидает клиента
waiting_parts    — Ожидает запчасти
in_repair        — В ремонте
ready            — Готов
unrepairable     — Ремонт невозможен
issued           — Выдан
canceled         — Отменён
```

---

# 11. Матрица переходов

Разрешить:

```text
received:
  diagnostics
  canceled

diagnostics:
  waiting_customer
  waiting_parts
  in_repair
  unrepairable
  canceled

waiting_customer:
  diagnostics
  waiting_parts
  in_repair
  unrepairable
  canceled

waiting_parts:
  waiting_customer
  in_repair
  unrepairable
  canceled

in_repair:
  waiting_customer
  waiting_parts
  ready
  unrepairable
  canceled

ready:
  in_repair
  issued

unrepairable:
  issued
  canceled

issued:
  terminal

canceled:
  terminal
```

Недопустимый переход:

```text
HTTP 409
понятное русское сообщение в repairs-module.
```

UI не должен назначать произвольный статус.

---

# 12. История статусов

Создать сущность:

```text
RepairStatusHistory
```

Поля:

```text
id
repair_id
old_status nullable
new_status
comment nullable
changed_by nullable
changed_at
```

При создании ремонта:

```text
old_status = null
new_status = received
```

При каждом переходе:

```text
создаётся новая строка истории;
история не перезаписывается;
история сортируется по времени;
в карточке отображается временная шкала.
```

---

# 13. Audit/event model

Использовать существующий механизм аудита Core.

События:

```text
repair.created
repair.updated
repair.status_changed
repair.canceled
repair.issued
```

Payload не должен содержать:

```text
пароли;
секреты;
лишние персональные данные;
полный необработанный request body.
```

---

# 14. Core API

Добавить:

```text
POST   /api/repairs
GET    /api/repairs
GET    /api/repairs/{repair_id}
PATCH  /api/repairs/{repair_id}
POST   /api/repairs/{repair_id}/status
GET    /api/repairs/{repair_id}/history
GET    /api/repairs/by-number/{number}
GET    /api/repairs/options
```

---

# 15. POST /api/repairs

Пример request:

```json
{
  "customer_id": null,
  "customer_name": "Иванов Иван",
  "customer_phone": "+7 900 000-00-00",
  "customer_email": null,
  "device_type": "Ноутбук",
  "brand": "Lenovo",
  "model": "ThinkPad T480",
  "serial_number": "PF123456",
  "reported_issue": "Не включается",
  "completeness": "Ноутбук и зарядное устройство",
  "appearance": "Потёртости на крышке",
  "customer_comment": "",
  "internal_note": "",
  "access_code_provided": false,
  "assigned_to": null,
  "priority": "normal"
}
```

Core должен:

```text
валидировать данные;
генерировать number;
ставить status=received;
назначать accepted_at/created_at/updated_at;
создавать history;
создавать audit event;
возвращать созданную карточку.
```

Клиент не может передать:

```text
id
number
status
created_at
updated_at
issued_at
canceled_at
closed_at
```

---

# 16. GET /api/repairs

Поддержать фильтры:

```text
q
status
priority
device_type
assigned_to
date_from
date_to
customer_phone
serial_number
page
page_size
sort
```

`q` ищет по:

```text
номеру ремонта;
имени клиента;
телефону;
типу устройства;
бренду;
модели;
серийному номеру;
заявленной неисправности.
```

Сортировка по умолчанию:

```text
accepted_at desc;
id desc.
```

---

# 17. PATCH /api/repairs/{id}

Разрешить редактировать только:

```text
customer_name
customer_phone
customer_email
device_type
brand
model
serial_number
reported_issue
completeness
appearance
customer_comment
internal_note
access_code_provided
assigned_to
priority
```

Запретить менять через PATCH:

```text
number
status
timestamps
history
```

Для:

```text
issued
canceled
```

запретить изменение бизнес-полей:

```text
HTTP 409
```

---

# 18. POST /api/repairs/{id}/status

Request:

```json
{
  "status": "diagnostics",
  "comment": "Передан мастеру"
}
```

Core:

```text
проверяет переход;
обновляет status;
обновляет updated_at;
ставит issued_at при issued;
ставит canceled_at при canceled;
ставит closed_at для issued/canceled;
создаёт history;
создаёт audit event;
возвращает обновлённый ремонт.
```

---

# 19. Options endpoint

Возвращать:

```json
{
  "statuses": [],
  "priorities": [],
  "device_types": []
}
```

UI не должен дублировать справочники в нескольких местах без необходимости.

---

# 20. База данных и миграция

После предыдущего инцидента с рабочей DB требования строгие.

До изменения схемы:

```text
остановить операции записи;
создать резервную копию live Core DB вне Git;
сохранить SHA256;
сохранить counts существующих таблиц;
зафиксировать путь backup.
```

Рекомендуемый каталог:

```text
C:\tbootit-data-backups\stage05a\<timestamp>\
```

Миграция только добавочная:

```text
создание новых таблиц;
создание новых индексов;
никаких DROP;
никакого пересоздания существующих таблиц;
никакого удаления данных.
```

Использовать существующий механизм миграций проекта.

Если Alembic отсутствует:

```text
реализовать безопасную идемпотентную additive migration;
документировать механизм;
повторный запуск не меняет существующие данные.
```

Запрещено:

```text
Base.metadata.drop_all
DROP TABLE
DELETE FROM
пересоздание live DB
копирование test DB поверх live DB.
```

---

# 21. Отдельный repairs-module

Создать:

```text
repairs-module/
```

Минимальная структура:

```text
repairs-module/
  app/
    main.py
    config.py
    core_client.py
    routers/
      repairs.py
    templates/
      base.html
      repairs_list.html
      repair_new.html
      repair_detail.html
      repair_edit.html
    static/
      styles.css
  tests/
  Dockerfile
  requirements.txt или pyproject.toml
```

Следовать существующему стилю inventory-sales-module.

---

# 22. Страницы repairs-module

Добавить:

```text
GET  /health
GET  /
GET  /repairs
GET  /repairs/new
POST /repairs/new
GET  /repairs/{id}
GET  /repairs/{id}/edit
POST /repairs/{id}/edit
POST /repairs/{id}/status
```

Главная `/` может перенаправлять на:

```text
/repairs
```

---

# 23. Список ремонтов

Страница:

```text
http://localhost:8040/repairs
```

Показывает:

```text
номер;
дата приёма;
клиент;
телефон;
устройство;
бренд/модель;
краткая неисправность;
статус;
приоритет;
ответственный;
время последнего изменения;
кнопка «Открыть».
```

Быстрые фильтры:

```text
Все
Приняты
Диагностика
Ожидают клиента
Ожидают запчасти
В ремонте
Готовы
Ремонт невозможен
Выданы
Отменены
```

Сверху поиск:

```text
номер / клиент / телефон / устройство / серийный номер.
```

---

# 24. Новая приёмка

Страница:

```text
/repairs/new
```

Форма полностью на русском.

Обязательные поля:

```text
ФИО клиента
Телефон
Тип устройства
Заявленная неисправность
```

Дополнительные:

```text
Email
Бренд
Модель
Серийный номер
Комплектность
Внешний вид
Комментарий клиента
Внутренняя заметка
Код доступа передан — да/нет
Ответственный
Приоритет
```

После успешного создания:

```text
redirect на /repairs/{id};
показать номер ремонта;
показать сообщение «Ремонт принят».
```

При ошибке:

```text
форма сохраняет введённые значения;
ошибка понятная и русская;
нет raw JSON/Pydantic.
```

---

# 25. Карточка ремонта

Показывает:

```text
номер;
статус;
приоритет;
даты;
клиента;
контакты;
устройство;
серийный номер;
неисправность;
комплектность;
внешний вид;
комментарий клиента;
внутреннюю заметку;
ответственного;
признак передачи кода доступа;
историю статусов.
```

Действия:

```text
Редактировать
Изменить статус
К списку ремонтов
На главную
```

Показывать только разрешённые следующие статусы.

---

# 26. Цвета статусов

Использовать понятные badges:

```text
Принят — нейтральный
Диагностика — синий
Ожидает клиента — жёлтый
Ожидает запчасти — оранжевый
В ремонте — фиолетовый/синий
Готов — зелёный
Ремонт невозможен — красный
Выдан — серый/зелёный
Отменён — серый/красный
```

Не полагаться только на цвет:

```text
всегда отображать текст статуса.
```

---

# 27. Главная навигация

Добавить в admin-shell ссылку:

```text
Ремонты
```

Она открывает:

```text
http://localhost:8040/repairs
```

Не ломать существующие ссылки:

```text
Товары
Продажи
Отчёты
Avito
```

---

# 28. Docker Compose

Добавить service:

```yaml
repairs-module:
```

Требования:

```text
отдельный контейнер;
CORE_API_URL через environment;
порт 8040;
healthcheck;
depends_on Core health;
никакого volume с Core DB;
никакого доступа к /data/db;
restart policy согласовать с другими модулями.
```

Проверить:

```powershell
docker compose config
docker compose up --build -d
docker compose ps
```

---

# 29. Core tests

Создать тесты минимум для:

```text
создание ремонта;
автоматический номер;
уникальность номера;
обязательные поля;
запрет клиентского status/number;
получение списка;
поиск по номеру;
поиск по телефону;
поиск по serial;
фильтр status;
фильтр priority;
получение карточки;
редактирование;
запрет изменения number;
переход received -> diagnostics;
недопустимый переход -> 409;
history при создании;
history при переходе;
issued timestamps;
canceled timestamps;
terminal status protections;
options endpoint;
audit events;
отсутствие полей password/pin.
```

Предлагаемые файлы:

```text
core/tests/test_repairs_create.py
core/tests/test_repairs_search_filters.py
core/tests/test_repairs_status_flow.py
core/tests/test_repairs_security.py
```

---

# 30. Test isolation

Core tests запускать только:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

Нельзя запускать против live DB:

```text
docker compose exec core pytest
```

После Core tests доказать:

```text
live DB SHA256 до/после одинаков;
product count одинаков;
sales count одинаков;
repair count одинаков.
```

---

# 31. Repairs-module tests

Покрыть:

```text
health;
список;
пустой список;
форма новой приёмки;
успешное создание;
ошибки формы;
карточка;
редактирование;
status transition;
русские статусы;
фильтры;
поиск;
история;
Core unavailable;
отсутствие direct DB imports;
навигационные ссылки.
```

---

# 32. Полный regression

Запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
```

Если admin-shell имеет тесты:

```powershell
docker compose exec -T admin-shell pytest
```

Указать фактические количества.

---

# 33. Runtime smoke

Создать один явно тестовый ремонт через UI/API:

```text
Клиент: ТЕСТ Stage05A
Телефон: +7 900 000-05-05
Устройство: Ноутбук
Бренд: Lenovo
Модель: ThinkPad Test
Серийный номер: TEST-STAGE05A
Неисправность: Не включается
Комплектность: Ноутбук и блок питания
Внешний вид: Тестовая запись
Приоритет: Обычный
```

Проверить:

```text
создание;
автоматический number;
status=received;
history created;
список;
поиск по номеру;
поиск по телефону;
поиск по serial;
карточка;
редактирование;
received -> diagnostics;
diagnostics -> in_repair;
in_repair -> ready;
ready -> issued;
terminal protection.
```

Не удалять запись напрямую.

Оставить тестовую запись с явной маркировкой и указать:

```text
repair ID
repair number
final status
```

---

# 34. Runtime regression существующих модулей

Проверить HTTP 200:

```text
Core health
Admin shell
Products
Cart
Sales
Sales reports
Avito module
Repairs module health
Repairs list
```

Не создавать новую продажу без необходимости.

---

# 35. Security and safety scans

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests repairs-module
```

Ожидаемо:

```text
0 matches
```

DB/temp/cache:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
```

Прямой DB access:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- repairs-module
```

Ожидаемо:

```text
0 matches
```

Секретные поля:

```powershell
git grep -n -I "device_password\|password.*device\|unlock_code\|pin_code\|graphic_key" -- core repairs-module
```

Допустимы только:

```text
security tests, проверяющие запрет;
access_code_provided boolean.
```

Секретные файлы:

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 36. Документация

Создать:

```text
docs/stage05a_repair_intake_registry_mvp.md
reports/stage05a_repair_intake_registry_mvp_report.md
```

Обновить:

```text
README.md
docker-compose.yml
logs/2026-08-03.md
```

Report:

```text
# Stage05A Repair Intake and Registry MVP Report

## STATUS
## PROMPT_DISCOVERY
## PREFLIGHT
## ARCHITECTURE
## LIVE_DB_BACKUP
## DATABASE_MIGRATION
## REPAIR_MODEL
## NUMBER_GENERATION
## CUSTOMER_INTEGRATION
## STATUS_MODEL
## STATUS_TRANSITIONS
## STATUS_HISTORY
## CORE_API
## REPAIRS_MODULE
## ADMIN_NAVIGATION
## TESTS
## LIVE_DB_PRESERVATION
## RUNTIME_CREATE
## RUNTIME_SEARCH
## RUNTIME_EDIT
## RUNTIME_STATUS_FLOW
## EXISTING_MODULE_REGRESSION
## SAFETY_SCAN
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_CHECK_GUIDE
## FINAL_STATUS
```

---

# 37. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE05A_REPAIR_INTAKE_REGISTRY_MVP_PROMPT.md
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
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE05A_REPAIR_INTAKE_REGISTRY_MVP_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE05A_REPAIR_INTAKE_REGISTRY_MVP_PROMPT.md `
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

# 38. Preflight

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

Ожидаемый исходный HEAD:

```text
0f0ab37
```

Если HEAD другой — указать фактический.

---

# 39. Git

Только targeted add.

Пример:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/main.py
git add core/app/routers/repairs.py
git add core/app/services/repair_service.py
git add core/app/services/repair_number_service.py
git add core/app/migrations/*
git add core/tests/test_repairs_create.py
git add core/tests/test_repairs_search_filters.py
git add core/tests/test_repairs_status_flow.py
git add core/tests/test_repairs_security.py

git add repairs-module
git add admin-shell
git add docker-compose.yml
git add README.md
git add docs/stage05a_repair_intake_registry_mvp.md
git add reports/stage05a_repair_intake_registry_mvp_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE05A_REPAIR_INTAKE_REGISTRY_MVP_PROMPT.md
git add -f logs/2026-08-03.md
```

Не добавлять файлы, которых нет.

Запрещено:

```text
git add .
git add -A
git add -u
```

Коммит:

```powershell
git commit -m "Add repair intake and registry MVP"
git push origin main
```

После push:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

Worktree должен быть чистым.

---

# 40. Definition of Done

Готово только если:

```text
live DB backup создан до миграции;
migration только additive;
существующие товары и продажи сохранены;
RepairOrder существует в Core;
номер ремонта генерируется Core;
номер уникален;
создание ремонта работает;
список работает;
поиск работает;
фильтры работают;
карточка работает;
редактирование работает;
status transitions контролируются Core;
недопустимый переход даёт 409;
история статусов сохраняется;
issued/canceled terminal protection работает;
отдельный repairs-module работает;
repairs-module не имеет direct DB access;
admin-shell содержит ссылку «Ремонты»;
Docker service healthy;
UI полностью на русском;
пароли и PIN не сохраняются;
Core safe tests PASS;
Inventory tests PASS;
Avito tests PASS;
Repairs tests PASS;
live DB не меняется от tests;
runtime smoke PASS;
safety scans clean;
targeted commit;
push;
clean Git;
owner manual check required.
```

---

# 41. Owner check guide

В отчёте дать короткую инструкцию:

```text
1. Открыть http://localhost:8040/repairs
2. Нажать «Принять технику»
3. Заполнить обязательные поля
4. Проверить автоматически присвоенный номер
5. Найти ремонт по номеру и телефону
6. Открыть карточку
7. Изменить данные
8. Перевести:
   Принят -> Диагностика -> В ремонте -> Готов -> Выдан
9. Проверить историю статусов
10. Убедиться, что после «Выдан» редактирование и переходы заблокированы
```

---

# 42. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_REPAIR_INTAKE_REGISTRY_MVP_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_REPAIR_INTAKE_REGISTRY_MVP_FAIL

BLOCKERS:
...
```
