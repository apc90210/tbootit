# PROMPT — Stage 01A Core MVP Internal Self-Check

## Роль

Ты QA/dev auditor и backend reviewer проекта «Техноребут».

Твоя задача — проверить уже реализованный Core MVP в `C:\tbootit`.

## Цель

Убедиться, что ядро системы и внешняя тестовая оболочка реально работают.

## Проверки

### 1. Git и структура

```powershell
Set-Location C:\tbootit
git status
Get-ChildItem
```

Проверить наличие:

```text
docker-compose.yml
core/
admin-shell/
docs/
reports/
data/
```

### 2. Docker

```powershell
docker compose config
docker compose up --build
```

Проверить, что сервисы не падают.

### 3. Core health

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
```

### 4. Admin Shell

Открыть:

```text
http://127.0.0.1:8010
```

Проверить, что shell загружается и видит Core API.

### 5. DB schema

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/admin/db/schema
```

Проверить таблицы:

```text
categories
products
product_photos
customers
repair_orders
sales
sale_items
audit_log
```

### 6. Products smoke

Проверить через API или shell:

- создать категорию;
- создать товар;
- получить список;
- открыть карточку;
- изменить статус;
- проверить audit log.

### 7. Photos smoke

Проверить:

- загрузить фото к товару;
- получить список фото;
- открыть media URL;
- убедиться, что файл физически появился в `data/storage`.

### 8. Customers smoke

Проверить:

- создать клиента;
- получить список клиентов;
- открыть клиента.

### 9. Repairs smoke

Проверить:

- создать ремонтную заявку;
- изменить статус;
- проверить список.

### 10. Sales smoke

Проверить:

- создать товар в наличии;
- провести продажу;
- убедиться, что товар стал `sold`;
- проверить audit log.

### 11. Persistence smoke

Проверить:

```powershell
docker compose down
docker compose up
```

Данные должны сохраниться.

### 12. Tests

Если есть pytest:

```powershell
pytest
```

## Отчет

Создать:

```text
reports/core_mvp_self_check_report.md
```

В отчете указать:

```text
STATUS: PASS / FAIL / PARTIAL
WHAT_CHECKED
COMMANDS_RUN
RESULTS
BROKEN_ITEMS
FIXES_APPLIED
REMAINING_LIMITATIONS
OWNER_TESTING_READY: true/false
```

## Если найдены ошибки

Исправить ошибки, если это безопасно.  
После исправления повторить проверки.  
Сделать отдельный commit:

```powershell
git add .
git commit -m "Fix Core MVP self-check issues"
```

Не выполнять push без команды пользователя.
