# PROMPT — Техноребут / Stage 01R Admin Shell Core API Connection Repair

## Роль агента

Ты senior fullstack/debug engineer проекта «Техноребут».

Твоя задача — в репозитории `C:\tbootit` исправить ошибку Admin/Test Shell после реализации Stage 01 Core MVP.

## Контекст

Проект: `C:\tbootit`

Архитектура:

```text
Core API + DB + Storage = единое ядро.
Admin Shell = внешний клиент, работает только через HTTP API.
```

Текущий запуск:

```text
Core API:    http://127.0.0.1:8000
API Docs:    http://127.0.0.1:8000/docs
Admin Shell: http://127.0.0.1:8011
```

Docker status от владельца:

```text
technoreboot-admin-shell   Up   0.0.0.0:8011->8010/tcp
technoreboot-core          Up   0.0.0.0:8000->8000/tcp
```

Core API проверен владельцем и работает:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
# status: ok

Invoke-RestMethod http://127.0.0.1:8000/api/version
# version: 0.1.0

Invoke-RestMethod http://127.0.0.1:8000/api/admin/db/schema
# returns schema for audit_log, categories, customers, product_photos, products, repair_orders, sale_items, sales
```

Проблема в UI:

```text
Admin Shell открывается.
Dashboard показывает Products/Customers/Repairs/Sales = 0.
Списки пустые.
При нажатии Seed Database появляется:
Error connecting to Core API.
```

## Цель ремонта

Исправить Admin Shell так, чтобы кнопка `Seed Database` и все admin/UI actions корректно работали с Core API.

После ремонта пользователь должен открыть:

```text
http://127.0.0.1:8011
```

и нажать:

```text
Seed Database
```

После этого должны появиться тестовые данные:

```text
Products > 0
Customers > 0
Repairs/Sales если seed их создает
```

## Обязательное правило поиска prompt-файлов

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

PowerShell:

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

## Предварительная диагностика

Выполнить:

```powershell
Set-Location C:\tbootit
git status
docker compose ps
docker compose logs --tail=200 core
docker compose logs --tail=200 admin-shell
```

Проверить seed endpoint напрямую:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
Invoke-RestMethod http://127.0.0.1:8000/api/products
```

Если прямой Core API seed работает, проблема только в Admin Shell.

Если прямой Core API seed не работает, исправить Core endpoint `/api/admin/seed`.

## Вероятная причина

Проверить, не делает ли HTML/JS в браузере запрос на Docker DNS-имя:

```text
http://core:8000
```

Из браузера пользователя `core` не резолвится. Docker hostname `core` работает только внутри Docker-сети.

Правильные варианты:

### Вариант А — браузер ходит напрямую на localhost Core API

JS в Admin Shell должен использовать:

```text
http://127.0.0.1:8000
```

Минус: для будущего deploy потребуется конфигурация public core URL.

### Вариант Б — Admin Shell backend проксирует запросы

Браузер вызывает относительные endpoints Admin Shell:

```text
/admin-api/seed
/admin-api/products
/admin-api/stats
```

А backend Admin Shell внутри контейнера ходит на:

```text
http://core:8000
```

Это предпочтительный вариант для MVP, потому что браузер не зависит от Docker DNS.

## Требуемое решение

Рекомендуется реализовать Вариант Б.

Admin Shell должен:

1. Принимать запросы от браузера на свои относительные endpoints.
2. Из backend-кода обращаться к Core API по env:

```text
CORE_API_URL=http://core:8000
```

3. Возвращать результат в браузер.
4. Показывать понятную ошибку, если Core недоступен.

## Что проверить в коде

Проверить файлы:

```text
admin-shell/app/main.py
admin-shell/app/templates/index.html
docker-compose.yml
README.md
docs/manual_test.md
reports/core_mvp_implementation_report.md
```

Искать:

```text
CORE_API_URL
core:8000
127.0.0.1:8000
fetch(
Seed Database
/api/admin/seed
```

## Что исправить

### 1. Исправить Seed Database

Кнопка `Seed Database` должна успешно выполнять:

```text
POST /api/admin/seed
```

через Admin Shell backend proxy или через корректный публичный URL.

### 2. Исправить все UI actions, которые могут иметь такую же проблему

Проверить и исправить:

```text
Load dashboard stats
Load products
Load customers
Load repairs
Load sales
Load DB schema
Load audit log
Seed Database
Backup
Dev Reset
Create product
Create customer
Create repair
Create sale
Change statuses
Upload photo
```

### 3. Улучшить обработку ошибок

Ошибка не должна быть просто:

```text
Error connecting to Core API
```

Нужно показывать:

```text
Action:
Target:
HTTP status:
Response detail:
```

Но без лишней сложности.

### 4. Обновить порт Admin Shell в документации

Так как порт 8010 был занят, текущий рабочий порт:

```text
http://127.0.0.1:8011
```

Обновить:

```text
README.md
docs/manual_test.md
reports/core_mvp_implementation_report.md
```

Если `docker-compose.yml` уже содержит mapping:

```text
8011:8010
```

оставить.

## Самопроверка после исправления

Выполнить:

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

Seed smoke напрямую:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
Invoke-RestMethod http://127.0.0.1:8000/api/products
```

Admin Shell smoke:

Открыть:

```text
http://127.0.0.1:8011
```

Проверить:

```text
Dashboard загружается
Seed Database работает
Products после seed появляются
Customers после seed появляются
DB Structure открывается
Audit log открывается
```

Если возможно, проверить через браузер DevTools Console/Network, что нет запросов на:

```text
http://core:8000
```

из браузера.

## Тесты

Запустить:

```powershell
docker compose exec core pytest
```

Если есть тесты admin-shell — запустить их.  
Если нет — добавить хотя бы простой smoke test для Admin Shell backend proxy, если это быстро и безопасно.

## Отчет

Создать:

```text
reports/stage01r_admin_shell_core_api_connection_repair_report.md
```

В отчете указать:

```text
STATUS:
BRANCH:
COMMIT:
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
ROOT_CAUSE:
WHAT_FIXED:
FILES_CHANGED:
COMMANDS_RUN:
SELF_CHECK_RESULTS:
OWNER_TESTING_READY:
CURRENT_URLS:
KNOWN_LIMITATIONS:
```

## Git

После успешных проверок:

```powershell
git status
git add .
git commit -m "Fix Admin Shell Core API connection"
git status
```

Не выполнять push без команды пользователя.

## Definition of Done

Ремонт считается готовым, если:

```text
Core API работает
Admin Shell работает на http://127.0.0.1:8011
Seed Database из UI работает
после seed появляются товары/клиенты
нет браузерных запросов к http://core:8000
DB Structure работает
Audit Log работает
pytest проходит
отчет создан
git commit создан
```

## Стоп-условия

Остановиться и отчитаться, если:

```text
Core API seed endpoint сам не работает и требует отдельного ремонта
Admin Shell архитектурно сделан так, что проще переписать прокси полностью
Docker ports конфликтуют снова
найден конфликт незакоммиченных изменений
```
