# PROMPT — Техноребут / Stage 01A Independent Core MVP Audit

## Роль агента

Ты senior QA/audit engineer, backend reviewer и архитектурный аудитор проекта «Техноребут».

Ты работаешь в репозитории:

```powershell
C:\tbootit
```

Твоя задача — провести независимый аудит уже реализованного Core MVP после этапов:

```text
Stage 01  — Core MVP Big Module
Stage 01R — Admin Shell Core API Connection Repair
Stage 01S — Admin Shell CRUD & Seed Completion Repair
```

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Главная архитектурная фиксация:

```text
Core API + DB + Storage = единое ядро системы.
Все остальные модули работают только через HTTP API.
```

Core API владеет БД, файлами, фото, бизнес-логикой, audit log, admin endpoints и API.

Admin Shell — временная внешняя тестовая оболочка для проверки Core MVP.

---

# 2. Текущий известный статус

Текущие адреса:

```text
Core API:    http://127.0.0.1:8000
API Docs:    http://127.0.0.1:8000/docs
Admin Shell: http://127.0.0.1:8011
```

Важно:

```text
Порт Admin Shell изменён с 8010 на 8011, потому что 8010 был занят.
```

Stage 01R исправил:

```text
Admin Shell Core API connection
backend proxy inside Admin Shell
unique constraint bug in /api/admin/seed
```

Stage 01S исправил:

```text
расширенный idempotent seed
proxy routes Admin Shell
CRUD UI для Products
CRUD UI для Customers
CRUD UI для Repairs
CRUD UI для Sales
test_seed.py
```

---

# 3. Важное требование владельца

Все будущие клиентские/пользовательские модули должны быть полностью на русском языке.

Проверить текущий Admin Shell как первый клиентский интерфейс.

Правило:

```text
Все, что видит обычный пользователь, должно быть на русском.
```

Проверить:

```text
меню
кнопки
заголовки
таблицы
формы
ошибки
подсказки
статусы на экране
seed-данные
пользовательская документация
```

Допустимо оставлять на английском только внутренние технические сущности:

```text
API endpoints
имена таблиц
имена полей
имена переменных
docker service names
статусы в БД
техническая документация для разработчика
```

Если Admin Shell сейчас на английском, это не блокер для Core API, но должно быть зафиксировано как обязательный repair-stage перед разработкой клиентских модулей.

---

# 4. Цель Stage 01A

Провести независимый аудит Core MVP и определить:

```text
готово ли ядро к разработке внешних модулей
что реально работает
что не работает
что недоделано
что нарушает архитектуру
что нужно исправить до следующего большого этапа
```

Stage 01A — это аудит, а не большая разработка.

Разрешено делать только мелкие безопасные исправления:

```text
очевидные опечатки
сломанные ссылки в документации
неверные порты в README/docs
мелкие тестовые правки
явные typos
```

Запрещено:

```text
переписывать архитектуру
начинать новый внешний модуль
переписывать весь Admin Shell
делать крупные изменения БД
делать опасный reset данных без необходимости
```

Если найдено много проблем — создать отдельный repair-prompt/repair-report, но не маскировать проблемы.

---

# 5. Обязательное правило поиска prompt-файлов

Перед началом работы обязательно найти актуальные prompt-файлы.

Искать в:

```text
C:\tbootit
C:\tbootit\.agents
C:\tbootit\docs
C:\tbootit\docs\obsidian
C:\tbootit\prompts
C:\tbootit\logs\prompts
C:\Users\Apc\Downloads
```

Выполни:

```powershell
Set-Location C:\tbootit

$PromptSearchRoots = @(
  "C:\tbootit",
  "C:\tbootit\.agents",
  "C:\tbootit\docs",
  "C:\tbootit\docs\obsidian",
  "C:\tbootit\prompts",
  "C:\tbootit\logs\prompts",
  "C:\Users\Apc\Downloads"
)

$PromptFiles = foreach ($Root in $PromptSearchRoots) {
  if (Test-Path $Root) {
    Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Name -match "prompt|PROMPT|промт|ПРОМТ" -or
        $_.Extension -in ".md", ".txt"
      } |
      Select-Object FullName, LastWriteTime, Length
  }
}

$PromptFiles | Sort-Object LastWriteTime -Descending | Format-Table -AutoSize
```

Если этот prompt найден в `C:\Users\Apc\Downloads`, скопировать его в:

```text
C:\tbootit\.agents\received_prompts\
```

В итоговом отчете указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 6. Preflight

Выполни:

```powershell
Set-Location C:\tbootit

git status
git branch
git log --oneline -10

docker compose ps
docker compose config
```

Проверить, что есть ожидаемые отчеты:

```text
reports/core_mvp_implementation_report.md
reports/stage01r_admin_shell_core_api_connection_repair_report.md
reports/stage01s_admin_shell_crud_seed_completion_report.md
```

Если какого-то отчета нет — зафиксировать.

---

# 7. Проверка структуры проекта

Проверить наличие и качество структуры:

```text
docker-compose.yml
.env.example
.gitignore
README.md

core/
core/Dockerfile
core/requirements.txt
core/app/
core/app/main.py
core/app/config.py
core/app/database.py
core/app/models.py
core/app/schemas.py
core/app/storage.py
core/app/routers/
core/tests/

admin-shell/
admin-shell/Dockerfile
admin-shell/requirements.txt
admin-shell/app/
admin-shell/app/main.py
admin-shell/app/templates/index.html

data/
docs/
reports/
.agents/
```

Проверить:

```text
нет ли секретов в git
.env не закоммичен
data/db и runtime files не должны быть закоммичены, если это не intentional test files
нет ли мусорных временных файлов
нет ли лишних Antigravity brain/task файлов внутри repo
```

---

# 8. Docker-аудит

Выполнить:

```powershell
docker compose down
docker compose up --build -d
docker compose ps
```

Проверить:

```text
core up
admin-shell up
Core на 8000
Admin Shell на 8011
нет restart loop
логи без критических ошибок
```

Логи:

```powershell
docker compose logs --tail=200 core
docker compose logs --tail=200 admin-shell
```

---

# 9. Core API smoke-аудит

Выполнить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/admin/db/schema
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
Invoke-RestMethod http://127.0.0.1:8000/api/products
Invoke-RestMethod http://127.0.0.1:8000/api/customers
Invoke-RestMethod http://127.0.0.1:8000/api/repairs
Invoke-RestMethod http://127.0.0.1:8000/api/sales
```

Проверить:

```text
ответы валидные
нет 500 ошибок
поля соответствуют MVP
```

---

# 10. Seed-аудит

Проверить idempotent seed:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed

Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
Invoke-RestMethod http://127.0.0.1:8000/api/products
Invoke-RestMethod http://127.0.0.1:8000/api/customers
```

Проверить:

```text
seed не падает
нет unique constraint error
не плодит бесконечные дубли
создает несколько товаров
создает несколько клиентов
создает категории
создает ремонты, если заявлено
audit log пишет seed-событие
```

---

# 11. CRUD-аудит Core API

## 11.1 Product

Проверить через API:

```powershell
$product = @{
  sku = "AUDIT-T480-001"
  title = "Аудит Ноутбук Lenovo ThinkPad T480"
  brand = "Lenovo"
  model = "ThinkPad T480"
  serial_number = "AUDIT-SN-T480-001"
  condition = "БУ, рабочий"
  description = "Тестовый товар аудита"
  purchase_price = 15000
  sale_price = 25000
  status = "in_stock"
  storage_location = "Склад аудит"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/products `
  -ContentType "application/json" `
  -Body $product
```

Проверить:

```text
создание товара
получение списка
получение карточки
смена статуса
```

Статусы проверить минимум:

```text
draft
in_stock
reserved
sold
in_repair
for_parts
written_off
published_site
published_avito
```

## 11.2 Customer

Проверить:

```powershell
$customer = @{
  name = "Аудит Клиент"
  phone = "+7 900 222-33-44"
  email = "audit-customer@example.local"
  comment = "Клиент для аудита"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/customers `
  -ContentType "application/json" `
  -Body $customer
```

Проверить:

```text
клиент создается
клиент появляется в списке
```

## 11.3 Repair

Проверить:

```text
создание ремонта
список ремонтов
смена статуса ремонта
```

Статусы:

```text
new
accepted
diagnostics
waiting_parts
in_progress
ready
issued
cancelled
```

## 11.4 Sale

Проверить:

```text
создание продажи
создание sale_items
товар после продажи становится sold
audit log содержит событие продажи
```

---

# 12. Storage/photo-аудит

Проверить:

```text
POST /api/products/{product_id}/photos
GET /api/products/{product_id}/photos
GET /media/products/{product_id}/{filename}
DELETE /api/products/{product_id}/photos/{photo_id}
```

Если быстро возможно — создать временный тестовый файл и загрузить через PowerShell/curl.

Проверить:

```text
файл физически появляется в data/storage
media URL открывается
после удаления запись/файл удаляются или корректно помечаются
ошибка на несуществующий product_id понятная
```

---

# 13. Admin Shell аудит

Открыть:

```text
http://127.0.0.1:8011
```

Проверить:

```text
Dashboard
Seed Database
Products
Add Product
Product status actions
Customers
Add Customer
Repairs
Create Repair
Repair status actions
Sales
Create Sale
DB Structure
Audit Log
Backup
Dev Reset — только если безопасно и понятно, что данные тестовые
```

Важно: проверить, что браузер не обращается к:

```text
http://core:8000
```

Все browser fetch-запросы должны быть относительными к Admin Shell или к доступному публичному адресу.

---

# 14. Русификация UI-аудит

Проверить текущий Admin Shell.

Классифицировать все английские пользовательские тексты:

```text
критично
средне
можно отложить
```

Критично для будущих клиентских модулей:

```text
кнопки
меню
заголовки
сообщения ошибок
названия таблиц
подсказки форм
статусы на экране
```

Если Admin Shell содержит английский:

```text
Dashboard
Products
Customers
Repairs
Sales
Seed Database
Mark Sold
Write Off
Add Product
Add Customer
```

зафиксировать как требование Stage 01T:

```text
Stage 01T — Russian UI Localization for Admin Shell
```

Не обязательно чинить в Stage 01A, если это большой объем, но обязательно зафиксировать.

---

# 15. Документация-аудит

Проверить:

```text
README.md
docs/architecture.md
docs/api_contract.md
docs/database.md
docs/storage.md
docs/manual_test.md
docs/obsidian если есть
.agents если есть
```

Проверить:

```text
указан порт 8011
нет старого 8010 как основного адреса
описана архитектура Core API + DB + Storage
описан запрет прямого доступа внешних модулей к БД
описан русский UI для будущих клиентских модулей
manual_test соответствует реальному UI
```

Если документация расходится с реальностью — исправить мелкие расхождения или зафиксировать.

---

# 16. Test-аудит

Запустить:

```powershell
docker compose exec core pytest
```

Проверить наличие тестов:

```text
test_health.py
test_products.py
test_admin_schema.py
test_seed.py
test_customers.py если есть
test_repairs.py если есть
test_sales.py если есть
test_photos.py если есть
```

Если отсутствуют важные тесты, зафиксировать как recommendations.

---

# 17. Persistence-аудит

Проверить сохранение данных:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats

docker compose down
docker compose up -d

Start-Sleep -Seconds 5

Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
```

Проверить:

```text
данные не исчезли после restart/down/up
БД находится в data/db
storage находится в data/storage
```

---

# 18. Git-аудит

Проверить:

```powershell
git status
git log --oneline -10
git diff --stat
git diff
```

Ожидается:

```text
после аудита либо чисто,
либо есть только осознанные изменения аудита/отчета/документации
```

Не оставлять случайные незакоммиченные изменения.

---

# 19. Итоговый отчет

Создать:

```text
reports/stage01a_independent_core_mvp_audit_report.md
```

Структура отчета:

```text
# Stage 01A Independent Core MVP Audit Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## EXECUTIVE SUMMARY

Коротко: можно ли переходить к следующему этапу.

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## ENVIRONMENT

Branch:
Head:
Docker compose:
Core URL:
Admin Shell URL:

## CHECKS RUN

Список команд.

## ARCHITECTURE AUDIT

Что соответствует.
Что нарушено.

## DOCKER AUDIT

Результат.

## CORE API AUDIT

Результат.

## DATABASE AUDIT

Результат.

## STORAGE/PHOTO AUDIT

Результат.

## ADMIN SHELL AUDIT

Результат.

## RUSSIAN UI AUDIT

Результат.
Список найденного английского пользовательского текста.
Рекомендация: нужен ли Stage 01T.

## SEED AUDIT

Результат.

## CRUD AUDIT

Результат.

## TESTS

Результат pytest и список тестов.

## DOCUMENTATION AUDIT

Результат.

## GIT STATUS

Результат.

## BLOCKERS

Список блокеров.

## NON-BLOCKING ISSUES

Список неблокирующих замечаний.

## RECOMMENDED NEXT STAGE

Один из вариантов:

- Stage 01T — Russian UI Localization for Admin Shell
- Stage 02 — Inventory/Product Module Hardening
- Stage 01 Repair — если найдены блокеры
```

---

# 20. Git commit

Если отчет создан или внесены мелкие правки:

```powershell
git add .
git commit -m "Audit Core MVP stage 01A"
```

Если изменений нет, commit не нужен, но отчет должен быть создан. Обычно отчет — это изменение, значит commit нужен.

Не выполнять push без отдельной команды владельца.

---

# 21. Definition of Done

Stage 01A готов, если:

```text
prompt найден и скопирован при необходимости
preflight выполнен
docker проверен
Core API проверен
seed проверен
CRUD проверен
Admin Shell проверен
русский UI аудит выполнен
документация проверена
pytest запущен
persistence проверен
git status проверен
отчет создан
commit создан, если были изменения
рекомендован следующий этап
```

---

# 22. Ожидаемая логика решения

Если Core MVP технически работает, но UI на английском:

```text
STATUS: PASS_WITH_NOTES
Recommended next stage: Stage 01T — Russian UI Localization for Admin Shell
```

Если есть технические поломки CRUD/API/Docker:

```text
STATUS: FAIL
Recommended next stage: repair stage
```

Если всё работает и UI достаточно русский:

```text
STATUS: PASS
Recommended next stage: Stage 02 — Inventory/Product Module Hardening
```

---

# 23. Главный принцип

Не переходить к разработке внешних модулей, пока ядро не проверено и не зафиксировано.

Аудит должен быть честным: лучше найти проблемы сейчас, чем тащить их во все будущие модули.
