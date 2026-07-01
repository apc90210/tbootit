# PROMPT — Техноребут / Stage 02A Independent Audit for Avito-Style Product Cards & JSON Import

## Роль агента

Ты senior QA/audit engineer, backend reviewer, API contract auditor и архитектурный аудитор проекта «Техноребут».

Ты работаешь в репозитории:

```powershell
C:\tbootit
```

Твоя задача — провести независимый аудит Stage 02 v2 после реализации Avito-style карточек товара и JSON-импорта.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Главная архитектура проекта:

```text
Core API + DB + Storage = единое ядро системы.
Все остальные модули работают только через HTTP API.
```

Core API должен:

```text
хранить товары
хранить карточки товара
хранить Avito-style данные
принимать JSON импорт
отдавать данные через API
хранить фото
хранить audit log
хранить product events
```

Core API не должен:

```text
парсить Авито
логиниться в Авито
управлять браузером
автоматически публиковать объявления
обходить капчу
использовать скрытые API Авито
содержать Playwright/Selenium-логику
```

Вся будущая работа с Авито должна быть вынесена в отдельный внешний модуль:

```text
avito-module
```

Core должен быть только готов работать с ним через API.

---

# 2. Уже выполненные этапы

В проекте уже выполнены:

```text
Stage 01  — Core MVP Big Module
Stage 01R — Admin Shell Core API Connection Repair
Stage 01S — Admin Shell CRUD & Seed Completion Repair
Stage 01A — Independent Core MVP Audit
Stage 01T — Russian UI Localization for Admin Shell
Stage 02 v2 — Avito-Style Product Cards & JSON Import
```

Текущие адреса:

```text
Core API:    http://127.0.0.1:8000
API Docs:    http://127.0.0.1:8000/docs
Admin Shell: http://127.0.0.1:8011
```

Известный результат Stage 02 v2:

```text
28/28 тестов прошли
live API smoke прошёл
seed imported 5 cards
JSON validate работает
JSON import работает
create_or_update по SKU работает
карточка товара с Avito-данными работает
Admin Shell получил раздел «Импорт JSON-карточки»
```

---

# 3. Ключевое решение владельца

Владелец зафиксировал:

```text
Парсинг Авито, браузерная автоматизация и автозаполнение объявлений должны быть в отдельном Avito-модуле.
Core должен быть просто готов работать с этим модулем через API.
```

Проверить это как отдельный архитектурный пункт.

---

# 4. Цель Stage 02A

Провести независимый аудит и ответить:

```text
готов ли Core после Stage 02 v2 как API-основа для будущего Avito-модуля?
```

Проверить:

```text
JSON-import
Avito-style поля
детальную карточку товара
историю импортов
поиск/фильтры
seed
Admin Shell
русский UI
тесты
документацию
границу ответственности Core/Avito Module
```

Stage 02A — это аудит, а не большая разработка.

Разрешены только мелкие безопасные исправления:

```text
опечатки
неверные ссылки
неверные порты в docs
очевидные typos
мелкие корректировки отчета/документации
```

Запрещено:

```text
добавлять парсер Авито
добавлять браузерную автоматизацию
переписывать Stage 02
добавлять новый внешний модуль
делать крупные изменения БД
ломать существующие API
```

Если есть проблемы — зафиксировать их и рекомендовать repair-stage.

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

Если этот prompt найден в:

```text
C:\Users\Apc\Downloads
```

скопировать его в:

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
git log --oneline -15

docker compose ps
docker compose config
```

Проверить наличие отчетов:

```text
reports/core_mvp_implementation_report.md
reports/stage01r_admin_shell_core_api_connection_repair_report.md
reports/stage01s_admin_shell_crud_seed_completion_report.md
reports/stage01a_independent_core_mvp_audit_report.md
reports/stage01t_russian_ui_localization_report.md
reports/stage02_avito_style_product_cards_json_import_report.md
```

Если отчет Stage 02 v2 называется иначе — найти его в `reports`.

Если есть незакоммиченные изменения — разобраться. Не начинать аудит поверх непонятного dirty state.

---

# 7. Проверка архитектурной границы Core / Avito Module

Проверить код на наличие запрещенной логики внутри Core:

```powershell
Get-ChildItem -Path "core","admin-shell" -Recurse -File -Include *.py,*.html,*.js,*.md |
  Select-String -Pattern "playwright|selenium|browser|captcha|avito.ru|webdriver|chromium|login|авторизац|капча|парс" -CaseSensitive:$false
```

Оценить найденное:

```text
технический текст в документации/комментарии — допустимо
код браузерной автоматизации внутри Core — блокер
код парсинга Авито внутри Core — блокер
```

Core может содержать:

```text
avito_* поля
Avito-style JSON
готовность к публикации
external_url
external_id
publication_status
```

Core не должен содержать:

```text
скрейпер
браузерный бот
логин на Авито
автопубликацию
```

---

# 8. Docker audit

Выполнить:

```powershell
docker compose down
docker compose up --build -d
docker compose ps
```

Проверить:

```text
core запущен
admin-shell запущен
Core на 8000
Admin Shell на 8011
нет restart loop
```

Логи:

```powershell
docker compose logs --tail=200 core
docker compose logs --tail=200 admin-shell
```

---

# 9. Core API smoke audit

Выполнить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
Invoke-RestMethod http://127.0.0.1:8000/api/admin/db/schema
```

Проверить, что нет 500 ошибок.

---

# 10. JSON validate audit

Найти пример JSON:

```text
docs/examples/product_card_lenovo_t480.json
```

Если такого файла нет, найти похожий пример в `docs/examples`.

Выполнить:

```powershell
$json = Get-Content .\docs\examples\product_card_lenovo_t480.json -Raw

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/product-cards/validate-json `
  -ContentType "application/json" `
  -Body $json
```

Проверить:

```text
valid = true
errors = []
warnings допустимы
```

Проверить невалидный JSON:

```powershell
$badJson = '{"source":"chatgpt","schema_version":"1.0","product":{"title":""}}'

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/product-cards/validate-json `
  -ContentType "application/json" `
  -Body $badJson
```

Проверить:

```text
возвращаются ошибки валидации
ничего не импортируется
нет 500 ошибки
```

---

# 11. JSON import audit

Выполнить импорт валидного JSON:

```powershell
$json = Get-Content .\docs\examples\product_card_lenovo_t480.json -Raw

$res1 = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/product-cards/import-json `
  -ContentType "application/json" `
  -Body $json

$res1 | ConvertTo-Json -Depth 10
```

Проверить:

```text
status = imported / success
operation = created или updated
product_id есть
sku есть
```

Повторить импорт того же JSON:

```powershell
$res2 = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/product-cards/import-json `
  -ContentType "application/json" `
  -Body $json

$res2 | ConvertTo-Json -Depth 10
```

Проверить:

```text
не создан дубль
operation = updated или idempotent behavior
product_id тот же или корректно найденный
```

---

# 12. Details endpoint audit

Проверить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/products/$($res2.product_id)/details | ConvertTo-Json -Depth 10
```

В ответе должны быть:

```text
product
category или category data
photos
product_card / card import data
avito / avito fields
site / site fields
events
computed
```

Проверить computed:

```text
margin
available_quantity
has_photos
avito_ready
site_ready
```

Если структура другая, оценить, соответствует ли она задаче Stage 02 v2.

---

# 13. Imports history audit

Проверить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/product-cards/imports | ConvertTo-Json -Depth 10
```

Проверить:

```text
история импортов есть
source_type/source_json/validation_status или аналоги есть
можно понять, что было импортировано
```

Если есть endpoint:

```text
GET /api/product-cards/imports/{import_id}
```

проверить его.

---

# 14. Product search/filter audit

Проверить:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products?q=Lenovo"
Invoke-RestMethod "http://127.0.0.1:8000/api/products?status=in_stock"
Invoke-RestMethod "http://127.0.0.1:8000/api/products?min_price=10000&max_price=30000"
Invoke-RestMethod "http://127.0.0.1:8000/api/products?avito_ready=true"
Invoke-RestMethod "http://127.0.0.1:8000/api/products?site_ready=true"
```

Проверить:

```text
нет 500 ошибок
фильтры реально влияют на результат
пустые результаты возвращаются корректно
```

---

# 15. Seed audit

Выполнить:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/products
Invoke-RestMethod http://127.0.0.1:8000/api/product-cards/imports
```

Проверить:

```text
seed импортирует несколько карточек
seed idempotent
нет unique constraint ошибок
карточки содержат Avito-style данные
```

---

# 16. Admin Shell audit

Открыть:

```text
http://127.0.0.1:8011
```

Проверить вручную:

```text
UI на русском
раздел "Импорт JSON-карточки" есть
можно вставить JSON
кнопка проверки JSON работает
кнопка импорта JSON работает
после импорта товар появляется/обновляется
карточка товара открывается
видны вкладки/блоки Авито, Сайт, Остатки, История
нет пользовательского английского текста в основных действиях
нет браузерных запросов к http://core:8000
```

Если есть DevTools/Network — проверить, что browser fetch идет на Admin Shell proxy или публичный localhost, а не на Docker DNS `core`.

---

# 17. Russian UI audit

Проверить основной шаблон:

```powershell
Select-String -Path "admin-shell\app\templates\index.html" `
  -Pattern "Dashboard|Products|Customers|Repairs|Sales|Seed Database|Import JSON|Validate JSON|Product|Customer|Repair|Sale|Actions|No products|Error connecting" `
  -CaseSensitive:$false
```

Если найдено — оценить:

```text
пользовательский текст на английском — issue
техническое имя переменной/endpoint — допустимо
```

Критерий:

```text
обычный пользователь не должен видеть английские кнопки/меню/ошибки
```

---

# 18. Tests audit

Запустить:

```powershell
docker compose exec core pytest
```

Ожидание:

```text
все тесты проходят
ожидаемый ориентир: 28/28 passed или больше
```

Проверить наличие тестов:

```text
test_product_card_json_validate.py
test_product_card_json_import.py
test_product_details_avito_card.py
test_products_search_filters.py
```

Если тесты называются иначе — оценить покрытие по смыслу.

---

# 19. Persistence audit

Проверить сохранение данных:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
$statsBefore = Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats

docker compose down
docker compose up -d

Start-Sleep -Seconds 5

$statsAfter = Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats

$statsBefore
$statsAfter
```

Проверить:

```text
данные не исчезли
БД не попала обратно в git index
storage сохраняется
```

---

# 20. Documentation audit

Проверить:

```text
README.md
docs/api_contract.md
docs/database.md
docs/manual_test.md
docs/stage02_avito_style_product_cards.md
docs/product_card_json_schema.md
docs/examples/product_card_lenovo_t480.json
```

Проверить:

```text
описан JSON import
описана структура карточки
описаны endpoints
описано, что Core не публикует Авито сам
описано, что Avito automation будет отдельным модулем
указан Admin Shell port 8011
пользовательские инструкции на русском
```

---

# 21. Git audit

Выполнить:

```powershell
git status
git diff --stat
git diff
git log --oneline -10
```

Проверить:

```text
нет runtime DB в индексе
нет data/db/technoreboot.db в git
нет временных файлов
нет случайных test_photo.jpg
```

---

# 22. Итоговый отчет

Создать:

```text
reports/stage02a_independent_avito_style_cards_json_import_audit_report.md
```

Структура:

```text
# Stage 02A Independent Audit Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## EXECUTIVE SUMMARY

Коротко: готов ли Core как API-основа для Avito-модуля.

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## ENVIRONMENT

Branch:
Head:
Core URL:
Admin Shell URL:
Docker status:

## CHECKS RUN

Список команд.

## ARCHITECTURE BOUNDARY AUDIT

Core does:
Core does not:
Findings:

## JSON VALIDATION AUDIT

## JSON IMPORT AUDIT

## CREATE_OR_UPDATE_BY_SKU AUDIT

## PRODUCT DETAILS AUDIT

## IMPORT HISTORY AUDIT

## SEARCH/FILTER AUDIT

## SEED AUDIT

## ADMIN SHELL AUDIT

## RUSSIAN UI AUDIT

## TESTS

## PERSISTENCE

## DOCUMENTATION AUDIT

## GIT STATUS

## BLOCKERS

## NON_BLOCKING_ISSUES

## RECOMMENDED_NEXT_STAGE

Варианты:
- Stage 02B — repair, если найдены проблемы
- Stage 03A — Avito Module Contract & Skeleton
- Stage 03 — Repair Module Hardening
- Stage 04 — Sales Module Hardening
```

---

# 23. Git commit

Если создан отчет или внесены мелкие исправления:

```powershell
git add .
git commit -m "Audit Stage 02 Avito-style cards JSON import"
git status
```

Не выполнять push без отдельной команды владельца.

---

# 24. Definition of Done

Stage 02A готов, если:

```text
prompt найден и скопирован при необходимости
preflight выполнен
архитектурная граница Core/Avito Module проверена
docker проверен
Core API проверен
JSON validate проверен
JSON import проверен
повторный import по SKU проверен
details endpoint проверен
imports history проверена
search/filter проверены
seed проверен
Admin Shell проверен
Russian UI проверен
pytest запущен
persistence проверен
documentation проверена
git status проверен
отчет создан
commit создан, если были изменения
рекомендован следующий этап
```

---

# 25. Ожидаемая логика результата

Если всё работает, а Core не содержит парсинг/браузерную автоматизацию:

```text
STATUS: PASS
Recommended next stage: Stage 03A — Avito Module Contract & Skeleton
```

Если всё работает, но есть мелкие замечания:

```text
STATUS: PASS_WITH_NOTES
Recommended next stage: Stage 02B repair или Stage 03A
```

Если есть блокеры:

```text
STATUS: FAIL
Recommended next stage: Stage 02B repair
```

---

# 26. Главный принцип

Core должен быть стабильной API-основой.

Avito-парсер, браузерный помощник и публикация — отдельный внешний модуль, не часть Core.
