# PROMPT — Техноребут / Stage 01S Admin Shell CRUD & Seed Completion Repair

## Роль агента

Ты senior fullstack/debug engineer и MVP product engineer проекта «Техноребут».

Ты работаешь в репозитории:

```powershell
C:\tbootit
```

Твоя задача — исправить функциональные недоработки Admin/Test Shell после Stage 01 и Stage 01R.

---

# 1. Контекст

Проект: `C:\tbootit`

Архитектура:

```text
Core API + DB + Storage = единое ядро системы.
Admin Shell = внешняя тестовая оболочка, работает только через HTTP API/proxy.
```

Текущие адреса:

```text
Core API:    http://127.0.0.1:8000
API Docs:    http://127.0.0.1:8000/docs
Admin Shell: http://127.0.0.1:8011
```

Stage 01R уже выполнил:

```text
исправил связь Admin Shell с Core API
добавил backend proxy внутри Admin Shell
исправил unique constraint bug в /api/admin/seed
pytest проходил
commit: Fix Admin Shell Core API connection
```

---

# 2. Проблемы, найденные владельцем при ручном тестировании

Владелец проверил Admin Shell и сообщил:

```text
1. В Products отображается только один продукт.
2. В Actions у товара доступны только два действия:
   - Mark Sold
   - Write Off
3. Пользователи/клиенты не добавляются.
```

Фраза владельца:

```text
Mark Sold Write Off только один продукт и два действия, пользователей не добавляется
```

Под "пользователями" в текущем MVP, скорее всего, имеются в виду `customers`, потому что отдельной полноценной users/roles-модели в Stage 01 еще нет.

Если в коде уже есть `users`, проверь и его тоже, но основной MVP-контур — `customers`.

---

# 3. Цель ремонта Stage 01S

Довести Admin/Test Shell до состояния полноценной тестовой оболочки MVP.

После ремонта через UI должно быть возможно:

```text
1. Создать несколько товаров.
2. Видеть несколько товаров после seed.
3. Создать категорию или выбрать существующую.
4. Создать клиента/customer.
5. Видеть клиентов в списке.
6. Создать ремонтную заявку.
7. Менять статусы товара не только Mark Sold / Write Off.
8. Менять статусы ремонта.
9. Провести продажу товара.
10. Видеть обновленные счетчики Dashboard.
11. Смотреть DB Structure.
12. Смотреть Audit Log.
13. Работать через Admin Shell без прямого доступа к БД.
```

---

# 4. Обязательное правило поиска prompt-файлов

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

В отчете указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 5. Preflight

Выполни:

```powershell
Set-Location C:\tbootit
git status
git log --oneline -5
docker compose ps
docker compose logs --tail=100 core
docker compose logs --tail=100 admin-shell
```

Проверить текущие endpoints:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
Invoke-RestMethod http://127.0.0.1:8000/api/products
Invoke-RestMethod http://127.0.0.1:8000/api/customers
Invoke-RestMethod http://127.0.0.1:8000/api/admin/db/schema
```

---

# 6. Диагностика проблемы клиентов/customers

Проверить, работает ли создание клиента напрямую через Core API:

```powershell
$body = @{
  name = "Иван Тестовый"
  phone = "+7 900 000-00-00"
  email = "ivan-test@example.local"
  comment = "Manual API smoke customer"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/customers `
  -ContentType "application/json" `
  -Body $body

Invoke-RestMethod http://127.0.0.1:8000/api/customers
```

Если Core API customer creation не работает — исправить Core API.

Если Core API работает, но UI не работает — исправить Admin Shell proxy/form/JS/template.

---

# 7. Диагностика seed

Проверить:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/products
Invoke-RestMethod http://127.0.0.1:8000/api/customers
Invoke-RestMethod http://127.0.0.1:8000/api/repairs
Invoke-RestMethod http://127.0.0.1:8000/api/sales
```

Seed должен создавать не один продукт, а набор тестовых данных.

Минимальный seed после ремонта:

```text
Categories:
- Ноутбуки
- Принтеры
- Мониторы
- Комплектующие

Products:
- Lenovo ThinkPad T480
- HP LaserJet 2055dn
- Dell P2419H
- Kingston SSD 480GB
- Logitech K120

Customers:
- Иван Тестовый
- Мария Проверочная
- ООО Ромашка

Repairs:
- HP LaserJet 2055dn / не захватывает бумагу
- Lenovo ThinkPad T480 / замена клавиатуры

Sales:
Можно не создавать продажи автоматически, если это усложняет проверку.
Но продажа должна создаваться вручную из UI.
```

Seed должен быть идемпотентным:

```text
повторное нажатие Seed Database не должно падать на unique constraint
и не должно плодить бесконечные дубли
```

Допустимое поведение:

```text
если запись с таким SKU/phone/slug уже есть — пропустить или обновить
```

---

# 8. Требуемые исправления в Admin Shell

Проверить и исправить:

```text
admin-shell/app/main.py
admin-shell/app/templates/index.html
```

## 8.1 Dashboard

Dashboard должен показывать актуальные счетчики:

```text
Products
Customers
Repairs
Sales
```

После seed счетчики должны обновляться.

## 8.2 Products

В UI должны быть:

```text
список товаров
форма добавления товара
поля title, sku, category, brand, model, serial_number, condition, description, purchase_price, sale_price, status, storage_location
кнопка Add Product / Create Product
статус товара
действия со статусами
```

### Действия товара

Сейчас есть только:

```text
Mark Sold
Write Off
```

Нужно добавить минимум:

```text
Set Draft
Set In Stock
Reserve
Mark Sold
Send To Repair
For Parts
Write Off
Publish Site
Publish Avito
```

Статусы должны вызывать:

```text
PATCH /api/products/{product_id}/status
```

с одним из статусов:

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

## 8.3 Customers

Должно работать:

```text
список клиентов
форма добавления клиента
поля name, phone, email, comment
кнопка Add Customer / Create Customer
```

После добавления клиент должен появиться без ручного перезапуска Docker.

Если есть ошибка API, показать ее понятно.

## 8.4 Repairs

Должно работать:

```text
список ремонтов
форма создания ремонта
выбор customer_id или ввод ID клиента
device_title
device_serial
problem_description
price
status
```

Статусы ремонта:

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

UI-действия минимум:

```text
Accept
Diagnostics
In Progress
Ready
Issued
Cancel
```

## 8.5 Sales

Должно работать:

```text
список продаж
форма создания продажи
выбор product_id или ввод ID товара
customer_id опционально
payment_method
comment
кнопка Create Sale
```

После продажи товар должен перейти в:

```text
sold
```

## 8.6 DB Structure

Должно работать:

```text
показать таблицы
показать поля
показать количество записей
```

## 8.7 Audit Log

Добавить или починить раздел Audit Log:

```text
последние 20-50 событий
entity_type
entity_id
action
comment
created_at
```

## 8.8 Admin

Должны работать:

```text
Seed Database
Backup
Dev Reset
```

Dev Reset должен быть явно помечен как опасный dev-only action.

---

# 9. Proxy requirements

Admin Shell должен использовать backend proxy.

Браузер не должен обращаться напрямую к:

```text
http://core:8000
```

Из браузера допустимы только:

```text
относительные URL Admin Shell
```

Например:

```text
/shell-api/products
/shell-api/customers
/shell-api/repairs
/shell-api/sales
/shell-api/admin/seed
/shell-api/admin/stats
```

Admin Shell backend внутри Docker может обращаться к:

```text
http://core:8000
```

через env:

```text
CORE_API_URL=http://core:8000
```

Проверь `fetch(...)` в `index.html`.

Если там есть `http://core:8000`, исправить.

---

# 10. Улучшить ошибки UI

Ошибка не должна быть просто:

```text
Error connecting to Core API
```

Нужно показывать:

```text
Action:
Endpoint:
HTTP status:
Detail:
```

Например:

```text
Create customer failed: 422 — field required: name
```

---

# 11. Обновить документацию

Обновить:

```text
README.md
docs/manual_test.md
docs/api_contract.md
reports/core_mvp_implementation_report.md
```

Добавить новый отчет:

```text
reports/stage01s_admin_shell_crud_seed_completion_report.md
```

Документация должна указывать рабочий порт:

```text
Admin Shell: http://127.0.0.1:8011
```

---

# 12. Самопроверка после ремонта

Запустить:

```powershell
Set-Location C:\tbootit

docker compose config
docker compose up --build -d
docker compose ps
```

Core smoke:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/admin/db/schema
```

Seed smoke:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
Invoke-RestMethod http://127.0.0.1:8000/api/products
Invoke-RestMethod http://127.0.0.1:8000/api/customers
```

Customer creation smoke:

```powershell
$body = @{
  name = "Петр UI Smoke"
  phone = "+7 900 111-22-33"
  email = "petr-ui-smoke@example.local"
  comment = "Created by smoke"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/customers `
  -ContentType "application/json" `
  -Body $body
```

Tests:

```powershell
docker compose exec core pytest
```

Admin Shell manual smoke:

```text
http://127.0.0.1:8011
```

Проверить в браузере:

```text
Seed Database
Products > 1
Customers > 1
Add Product
Add Customer
Change product status to reserved
Change product status to in_stock
Create Repair
Change repair status
Create Sale
DB Structure
Audit Log
```

---

# 13. Добавить тесты, если быстро

Если это безопасно, добавить/обновить тесты:

```text
core/tests/test_seed.py
core/tests/test_customers.py
core/tests/test_repairs.py
core/tests/test_sales.py
```

Минимум проверить:

```text
seed idempotent
customers create/list
products status change
sales marks product sold
```

---

# 14. Отчет

Создать:

```text
reports/stage01s_admin_shell_crud_seed_completion_report.md
```

Содержимое:

```text
STATUS:
BRANCH:
COMMIT:
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
OWNER_REPORTED_ISSUES:
ROOT_CAUSE:
WHAT_FIXED:
SEED_DATA_CREATED:
UI_SECTIONS_FIXED:
FILES_CHANGED:
COMMANDS_RUN:
SELF_CHECK_RESULTS:
OWNER_TESTING_READY:
CURRENT_URLS:
KNOWN_LIMITATIONS:
NEXT_STEP:
```

---

# 15. Git

После успешных проверок:

```powershell
git status
git add .
git commit -m "Complete Admin Shell CRUD and seed flows"
git status
```

Не выполнять push без отдельной команды пользователя.

---

# 16. Definition of Done

Stage 01S считается готовым, если:

```text
Admin Shell открывается на http://127.0.0.1:8011
Seed Database создает несколько товаров и клиентов
Products показывает больше одного товара
Customers показывает больше одного клиента
клиент добавляется из UI
товар добавляется из UI
у товара есть все основные действия статусов
ремонт создается из UI
статус ремонта меняется из UI
продажа создается из UI
товар после продажи становится sold
DB Structure работает
Audit Log работает
ошибки UI стали понятнее
pytest проходит
отчет создан
git commit создан
```

---

# 17. Стоп-условия

Остановиться и отчитаться, если:

```text
Core API endpoints отсутствуют и требуют крупной переработки
Admin Shell проще переписать полностью, чем чинить точечно
есть конфликт незакоммиченных изменений
Docker не запускается
порт 8011 снова занят
```

---

# 18. Приоритет

Главный приоритет — сделать Admin Shell реальным рабочим инструментом для ручного тестирования Core MVP.

Не надо делать красивый дизайн.  
Нужно сделать удобно и полно для проверки данных.
