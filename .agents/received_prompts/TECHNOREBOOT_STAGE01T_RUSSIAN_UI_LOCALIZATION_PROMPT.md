# PROMPT — Техноребут / Stage 01T Russian UI Localization for Admin Shell

## Роль агента

Ты senior frontend/fullstack developer, UX reviewer и technical writer проекта «Техноребут».

Ты работаешь в репозитории:

```powershell
C:\tbootit
```

Твоя задача — выполнить обязательную русификацию Admin/Test Shell после аудита Stage 01A.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Архитектурная фиксация:

```text
Core API + DB + Storage = единое ядро системы.
Все остальные модули работают только через HTTP API.
```

Текущие адреса:

```text
Core API:    http://127.0.0.1:8000
API Docs:    http://127.0.0.1:8000/docs
Admin Shell: http://127.0.0.1:8011
```

Выполненные этапы:

```text
Stage 01  — Core MVP Big Module
Stage 01R — Admin Shell Core API Connection Repair
Stage 01S — Admin Shell CRUD & Seed Completion Repair
Stage 01A — Independent Core MVP Audit
```

Stage 01A выявил:

```text
Технически Core MVP проходит аудит.
Критичная неблокирующая проблема: Admin Shell полностью/частично на английском.
Следующий этап: Stage 01T — Russian UI Localization for Admin Shell.
```

---

# 2. Главное требование владельца

Все клиентские/пользовательские модули должны быть полностью на русском языке, потому что конечные пользователи не знают английский.

Правило:

```text
Все, что видит обычный пользователь, должно быть на русском.
```

Это касается:

```text
меню
заголовков
кнопок
форм
лейблов
placeholder
подсказок
ошибок
успешных сообщений
таблиц
статусов на экране
seed-данных
пользовательской документации
manual_test
```

Допустимо оставить на английском только внутренние технические сущности:

```text
API endpoints
имена таблиц
имена полей
имена переменных
docker service names
статусы в БД
техническая документация для разработчика
pytest names
кодовые enum значения
```

Но если технический статус показывается пользователю, рядом должен быть русский человекочитаемый вариант.

Пример:

```text
В БД: in_stock
В UI: В наличии
```

---

# 3. Цель Stage 01T

Сделать Admin Shell полноценной русскоязычной тестовой оболочкой Core MVP.

После этапа пользователь должен открыть:

```text
http://127.0.0.1:8011
```

и видеть интерфейс на русском языке.

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

В итоговом отчете указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 5. Preflight

Выполнить:

```powershell
Set-Location C:\tbootit

git status
git log --oneline -10
docker compose ps
```

Проверить наличие отчета аудита:

```text
reports/stage01a_independent_core_mvp_audit_report.md
```

Открыть и прочитать его перед изменениями.

---

# 6. Область изменений

Основной файл:

```text
admin-shell/app/templates/index.html
```

Возможные файлы:

```text
admin-shell/app/main.py
README.md
docs/manual_test.md
docs/api_contract.md
docs/architecture.md
reports/stage01t_russian_ui_localization_report.md
```

Если seed-данные на английском, исправлять:

```text
core/app/routers/admin.py
```

Не менять без необходимости:

```text
core/app/models.py
core/app/schemas.py
core/app/database.py
API endpoints
DB field names
docker-compose service names
```

---

# 7. Что нужно русифицировать в Admin Shell

Проверить весь UI и заменить пользовательские английские тексты.

## 7.1 Основные заголовки

Заменить:

```text
Technoreboot Admin Shell → Техноребут — панель управления MVP
Dashboard → Обзор
Products → Товары
Customers → Клиенты
Repairs → Ремонты
Sales → Продажи
DB Structure → Структура БД
Audit Log → Журнал действий
Admin → Администрирование
```

## 7.2 Кнопки

Примеры переводов:

```text
Seed Database → Заполнить тестовыми данными
Add Product → Добавить товар
Create Product → Создать товар
Add Customer → Добавить клиента
Create Customer → Создать клиента
Create Repair → Создать ремонт
Create Sale → Провести продажу
Backup → Создать резервную копию
Dev Reset → Сбросить тестовые данные
Refresh → Обновить
Save → Сохранить
Cancel → Отмена
Delete → Удалить
Upload Photo → Загрузить фото
```

## 7.3 Действия товара

Показывать на русском:

```text
Set Draft → Черновик
Set In Stock → В наличии
Reserve → Зарезервировать
Mark Sold → Продан
Send To Repair → В ремонт
For Parts → На запчасти
Write Off → Списать
Publish Site → Опубликовать на сайте
Publish Avito → Опубликовать на Авито
```

Внутренние значения статусов оставить как есть:

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

Но в UI показывать человекочитаемые названия:

```text
draft → Черновик
in_stock → В наличии
reserved → Зарезервирован
sold → Продан
in_repair → В ремонте
for_parts → На запчасти
written_off → Списан
published_site → На сайте
published_avito → На Авито
```

## 7.4 Статусы ремонта

В UI показывать:

```text
new → Новая заявка
accepted → Принято
diagnostics → Диагностика
waiting_parts → Ожидание запчастей
in_progress → В работе
ready → Готово
issued → Выдано
cancelled → Отменено
```

Кнопки:

```text
Accept → Принять
Diagnostics → Диагностика
In Progress → В работу
Ready → Готово
Issued → Выдано
Cancel → Отменить
```

## 7.5 Таблицы

Перевести заголовки:

```text
ID → ID
SKU → Артикул
Title → Название
Status → Статус
Actions → Действия
Name → Имя
Phone → Телефон
Email → Email
Device → Устройство
Problem → Неисправность
Price → Цена
Payment → Оплата
Comment → Комментарий
Created At → Создано
```

## 7.6 Формы

Все labels и placeholders должны быть на русском.

Примеры:

```text
Title → Название
Brand → Бренд
Model → Модель
Serial Number → Серийный номер
Condition → Состояние
Description → Описание
Purchase Price → Цена закупки
Sale Price → Цена продажи
Storage Location → Место хранения
Customer Name → Имя клиента
Phone → Телефон
Comment → Комментарий
Device Title → Устройство
Problem Description → Описание неисправности
Payment Method → Способ оплаты
```

## 7.7 Сообщения

Перевести:

```text
No products found. → Товары не найдены.
No customers found. → Клиенты не найдены.
No repairs found. → Ремонтные заявки не найдены.
No sales found. → Продажи не найдены.
Error connecting to Core API → Ошибка подключения к Core API.
Product created → Товар создан.
Customer created → Клиент создан.
Repair created → Ремонт создан.
Sale created → Продажа создана.
Database seeded → Тестовые данные добавлены.
```

Ошибки должны быть понятными:

```text
Не удалось создать клиента: <детали>
Не удалось загрузить товары: <детали>
Не удалось выполнить действие: <детали>
```

---

# 8. Seed-данные

Проверить seed.

Если seed создаёт данные на английском, заменить на русские тестовые данные.

Пример:

## Категории

```text
Ноутбуки
Принтеры
Мониторы
Комплектующие
Периферия
```

## Товары

```text
Ноутбук Lenovo ThinkPad T480
Принтер HP LaserJet 2055dn
Монитор Dell P2419H
SSD Kingston 480 ГБ
Клавиатура Logitech K120
```

## Клиенты

```text
Иван Тестовый
Мария Проверочная
ООО Ромашка
```

## Ремонты

```text
Принтер HP LaserJet 2055dn — не захватывает бумагу
Ноутбук Lenovo ThinkPad T480 — требуется замена клавиатуры
```

Технические поля `sku`, `slug`, `status` могут остаться на английском.

---

# 9. Русская карта статусов

Если в Admin Shell нет helper-функций, добавить их в JS/template:

```javascript
const PRODUCT_STATUS_LABELS = {
  draft: "Черновик",
  in_stock: "В наличии",
  reserved: "Зарезервирован",
  sold: "Продан",
  in_repair: "В ремонте",
  for_parts: "На запчасти",
  written_off: "Списан",
  published_site: "На сайте",
  published_avito: "На Авито",
};

const REPAIR_STATUS_LABELS = {
  new: "Новая заявка",
  accepted: "Принято",
  diagnostics: "Диагностика",
  waiting_parts: "Ожидание запчастей",
  in_progress: "В работе",
  ready: "Готово",
  issued: "Выдано",
  cancelled: "Отменено",
};
```

Использовать эти labels в таблицах, карточках, select и кнопках.

---

# 10. Документация

Обновить:

```text
README.md
docs/manual_test.md
docs/architecture.md если нужно
reports/stage01a_independent_core_mvp_audit_report.md не переписывать, но можно ссылаться
```

В `docs/manual_test.md` сценарии должны быть на русском и соответствовать реальному UI.

Обязательно указать:

```text
Admin Shell: http://127.0.0.1:8011
```

---

# 11. Самопроверка

После изменений выполнить:

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
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
```

Seed smoke:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/products
Invoke-RestMethod http://127.0.0.1:8000/api/customers
```

Tests:

```powershell
docker compose exec core pytest
```

Manual UI smoke:

Открыть:

```text
http://127.0.0.1:8011
```

Проверить:

```text
все меню на русском
все кнопки на русском
таблицы на русском
формы на русском
статусы товаров на русском
статусы ремонтов на русском
ошибки/успешные сообщения на русском
seed-данные на русском
основные действия не сломались
```

---

# 12. Проверка отсутствия английского пользовательского текста

Выполнить поиск:

```powershell
Select-String -Path "admin-shell\app\templates\index.html" `
  -Pattern "Dashboard|Products|Customers|Repairs|Sales|Seed Database|Mark Sold|Write Off|Add Product|Add Customer|Create Repair|Create Sale|No products found|No customers found|Error connecting" `
  -CaseSensitive:$false
```

Если найдено — оценить:

```text
это пользовательский текст или технический код?
```

Если пользовательский — перевести.  
Если технический — можно оставить.

---

# 13. Отчет

Создать:

```text
reports/stage01t_russian_ui_localization_report.md
```

Структура:

```text
# Stage 01T Russian UI Localization Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## BRANCH

## COMMIT

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## WHAT LOCALIZED

- menus
- buttons
- forms
- tables
- status labels
- errors
- seed data
- documentation

## FILES CHANGED

## COMMANDS RUN

## SELF_CHECK_RESULTS

## REMAINING_ENGLISH_TEXT

Указать, если что-то осталось.
Разделить:
- allowed technical English
- remaining user-facing English

## OWNER_TESTING_READY

true/false

## NEXT RECOMMENDED STAGE

Один из вариантов:
- Stage 02 — Inventory/Product Module Hardening
- Stage 01T Repair — если русификация неполная
```

---

# 14. Git

После успешных проверок:

```powershell
git status
git add .
git commit -m "Localize Admin Shell UI to Russian"
git status
```

Не выполнять push без отдельной команды владельца.

---

# 15. Definition of Done

Stage 01T считается готовым, если:

```text
Admin Shell открывается на http://127.0.0.1:8011
пользовательский UI на русском
кнопки на русском
формы на русском
таблицы на русском
статусы на русском
ошибки на русском
seed-данные на русском
manual_test на русском
Core API не сломан
pytest проходит
отчет создан
git commit создан
```

---

# 16. Стоп-условия

Остановиться и отчитаться, если:

```text
UI устроен так, что русификация требует полной переработки шаблона
после русификации ломаются CRUD-действия
Docker не запускается
есть конфликт незакоммиченных изменений
```

---

# 17. Главный принцип

Не менять внутреннюю архитектуру без необходимости.

Задача Stage 01T — не новый функционал, а сделать текущую тестовую оболочку понятной русскоязычному пользователю.
