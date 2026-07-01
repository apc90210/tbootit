# PROMPT — Техноребут / Stage 03A Avito Parser Module MVP

## Роль агента

Ты senior backend/fullstack developer, интеграционный инженер и архитектор внешних модулей проекта «Техноребут».

Ты работаешь в репозитории:

```powershell
C:\tbootit
```

Твоя задача — создать отдельный внешний Avito-модуль для read-only парсинга публичных объявлений Авито с указанного аккаунта/профиля, сохранения скачанных объявлений и подготовки их к будущему импорту в Core.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Главная архитектура проекта:

```text
Core API + DB + Storage = единое ядро системы.
Все остальные модули работают только через HTTP API.
```

Core уже умеет:

```text
хранить товары
хранить Avito-style карточки
валидировать JSON-карточки
импортировать JSON-карточки
отдавать карточки товаров через API
хранить историю импортов
```

Внешние модули не должны ходить напрямую в БД Core.

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
Stage 02A — Independent Audit for Avito-Style Product Cards & JSON Import
```

Текущие адреса:

```text
Core API:    http://127.0.0.1:8000
Admin Shell: http://127.0.0.1:8011
```

---

# 3. Новый порядок модулей

Владелец зафиксировал следующий порядок:

```text
1. Парсинг объявлений с Авито.
2. Добавление скачанных объявлений в базу Core через API.
3. Модуль работы с базой/товарами: просмотр, продажа, ценники для печати.
```

Следовательно, текущий этап:

```text
Stage 03A — Avito Parser Module MVP
```

После него будет:

```text
Stage 03B — Parsed Avito Ads to Core Import
Stage 04  — Inventory/Sales/Price Tags Module
```

---

# 4. Главная архитектурная граница

Avito-модуль — отдельный внешний модуль.

Core не должен:

```text
парсить Авито
логиниться в Авито
управлять браузером
скачивать объявления
публиковать объявления
иметь Playwright/Selenium-зависимости
```

Avito-модуль может:

```text
загружать публичную страницу/профиль
извлекать публичные данные объявлений
сохранять raw parsed ads внутри своего storage
показывать предпросмотр
экспортировать результат в JSON
позже отправлять JSON в Core API
```

На Stage 03A Avito-модуль НЕ должен писать товары в Core автоматически.  
Это будет Stage 03B.

---

# 5. Ограничения Stage 03A

Разрешено:

```text
read-only загрузка публично доступных страниц
ручной запуск парсинга по URL
низкая частота запросов
сохранение HTML snapshot для отладки
сохранение parsed ads в локальное хранилище avito-module
нормализация данных в промежуточный JSON
предпросмотр в русскоязычном UI/API
```

Запрещено:

```text
обход капчи
обход антибот-защиты
скрытые/private API
автологин
использование украденных cookies/session
массовый спам-запросы
автопубликация
автоматическое нажатие финальных кнопок публикации
обход платных ограничений
```

Если Avito показывает капчу, блокировку или требует авторизацию — модуль должен остановиться и вернуть понятный статус:

```text
blocked_or_captcha
auth_required
parse_failed
```

Нельзя пытаться обходить защиту.

---

# 6. Обязательное правило поиска prompt-файлов

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

# 7. Preflight

Выполнить:

```powershell
Set-Location C:\tbootit

git status
git branch
git log --oneline -15

docker compose ps
docker compose config
docker compose exec core pytest
```

Проверить наличие отчетов:

```text
reports/stage02_avito_style_product_cards_json_import_report.md
reports/stage02a_independent_avito_style_cards_json_import_audit_report.md
```

Если отчеты называются иначе — найти их в `reports`.

Не начинать работу поверх непонятного dirty state.

---

# 8. Структура нового модуля

Создать отдельный модуль:

```text
avito-module/
```

Структура:

```text
avito-module/
  Dockerfile
  requirements.txt
  README.md
  app/
    __init__.py
    main.py
    config.py
    storage.py
    schemas.py
    parser.py
    normalizer.py
    core_client.py
    routers/
      __init__.py
      health.py
      profiles.py
      parsed_ads.py
      exports.py
      core_sync_stub.py
  tests/
    test_health.py
    test_parser_static_html.py
    test_normalizer.py
    test_storage.py
    test_contract_no_core_write.py
  samples/
    avito_profile_sample.html
    avito_item_sample.html
    parsed_ads_sample.json
```

Добавить в корневой `docker-compose.yml` сервис:

```text
avito-module
```

Порт:

```text
8020
```

URL:

```text
http://127.0.0.1:8020
```

---

# 9. Docker Compose

Добавить сервис:

```yaml
  avito-module:
    build:
      context: ./avito-module
    container_name: technoreboot-avito-module
    environment:
      AVITO_MODULE_NAME: technoreboot-avito-module
      AVITO_MODULE_MODE: parser_mvp
      CORE_API_BASE_URL: http://core:8000
      AVITO_STORAGE_DIR: /app/data
      AVITO_REQUEST_DELAY_SECONDS: 3
      AVITO_MAX_PAGES_PER_RUN: 2
    ports:
      - "8020:8020"
    volumes:
      - ./data/avito-module:/app/data
    depends_on:
      - core
```

Важно:

```text
данные avito-module хранить отдельно в data/avito-module
не использовать data/db Core
не читать SQLite напрямую
```

---

# 10. Технологии

Рекомендуемый стек:

```text
FastAPI
httpx
selectolax или beautifulsoup4
pydantic
pytest
```

Не использовать на Stage 03A:

```text
playwright
selenium
webdriver
undetected-chromedriver
pyppeteer
```

Можно использовать обычный HTTP GET публичной страницы.

Если HTTP GET не позволяет получить публичные данные — честно вернуть статус:

```text
parse_failed
blocked_or_captcha
auth_required
```

---

# 11. API Avito-модуля

## 11.1 Health

```text
GET /health
GET /api/version
```

Response:

```json
{
  "status": "ok",
  "module": "avito-module",
  "mode": "parser_mvp"
}
```

## 11.2 Связь с Core

```text
GET /api/core/health
```

Должен сходить в Core:

```text
GET http://core:8000/health
```

## 11.3 Запуск парсинга профиля

```text
POST /api/avito/profiles/parse
```

Body:

```json
{
  "profile_url": "https://www.avito.ru/...",
  "max_pages": 1,
  "save_html": true
}
```

Response:

```json
{
  "status": "parsed",
  "run_id": "....",
  "profile_url": "...",
  "ads_found": 10,
  "ads_saved": 10,
  "warnings": []
}
```

Если не удалось:

```json
{
  "status": "blocked_or_captcha",
  "run_id": "...",
  "profile_url": "...",
  "ads_found": 0,
  "warnings": ["Страница похожа на капчу или защитную страницу. Обход не выполнялся."]
}
```

## 11.4 Список запусков

```text
GET /api/avito/runs
GET /api/avito/runs/{run_id}
```

## 11.5 Список скачанных объявлений

```text
GET /api/avito/parsed-ads
GET /api/avito/parsed-ads/{ad_id}
```

Фильтры:

```text
run_id
status
q
limit
offset
```

## 11.6 Экспорт объявления в product_card JSON

```text
GET /api/avito/parsed-ads/{ad_id}/product-card-json
```

Должен вернуть JSON, совместимый с Core:

```text
POST /api/product-cards/import-json
```

Но на Stage 03A не отправлять его в Core автоматически.

## 11.7 Проверка импорта в Core — stub only

```text
POST /api/avito/parsed-ads/{ad_id}/core-import-preview
```

Должен:

```text
сформировать product_card JSON
отправить в Core validate-json
вернуть результат validate
НЕ импортировать в Core
```

Это подготовка к Stage 03B.

---

# 12. Модель parsed ad

Внутренняя модель скачанного объявления:

```json
{
  "id": "local-generated-id",
  "run_id": "run-id",
  "source": "avito",
  "source_url": "https://www.avito.ru/...",
  "external_id": "если удалось определить",
  "title": "Ноутбук Lenovo ThinkPad T480",
  "price": 25000,
  "currency": "RUB",
  "description": "Описание объявления",
  "location": "Екатеринбург",
  "seller_name": "Техноребут",
  "published_at_text": "сегодня",
  "category_path": ["Электроника", "Ноутбуки"],
  "parameters": {
    "Производитель": "Lenovo",
    "Модель": "ThinkPad T480"
  },
  "photos": [
    {
      "url": "https://...",
      "local_path": null,
      "downloaded": false
    }
  ],
  "raw_html_path": "runs/.../item.html",
  "parse_status": "parsed",
  "parse_errors": [],
  "created_at": "..."
}
```

---

# 13. Product Card JSON mapping

Создать normalizer:

```text
parsed ad → product_card JSON
```

Mapping:

```text
parsed.title            → product.title
parsed.title            → avito.title
parsed.description      → product.description / avito.description
parsed.price            → product.sale_price / avito.price
parsed.category_path    → product.category_path / avito.category_path
parsed.parameters       → avito.parameters
parsed.photos           → avito.photos
parsed.source_url       → source metadata / notes
parsed.external_id      → external_id metadata if available
```

SKU генерация:

```text
если внешнего SKU нет, сгенерировать:
AVITO-{external_id}
или
AVITO-{hash(source_url)}
```

Не создавать дубли внутри parsed storage:

```text
если source_url уже есть — обновить parsed ad
```

---

# 14. Хранилище Avito-модуля

На Stage 03A можно использовать JSON-файлы в:

```text
data/avito-module/
```

Структура:

```text
data/avito-module/
  runs/
    <run_id>/
      run.json
      profile_page_1.html
      ads/
        <ad_id>.json
        <ad_id>.html
  parsed_ads_index.json
```

Не использовать БД Core.

Если удобно, можно использовать SQLite внутри avito-module, но проще JSON-файлы.

---

# 15. Русский UI / простая страница

Если быстро и безопасно — добавить простую HTML-страницу Avito-модуля:

```text
http://127.0.0.1:8020/
```

На русском:

```text
Модуль Авито
Ссылка на профиль Авито
Максимум страниц
Кнопка "Скачать объявления"
Список скачанных объявлений
Кнопка "Показать JSON карточки"
Кнопка "Проверить импорт в Core"
```

Это UI Avito-модуля, не Admin Shell Core.

Если UI затягивает этап — достаточно API + README, но лучше сделать минимальный UI.

---

# 16. Безопасность и ограничения

Добавить в код ограничения:

```text
max_pages не больше AVITO_MAX_PAGES_PER_RUN
delay между запросами не меньше AVITO_REQUEST_DELAY_SECONDS
user-agent обычный, без маскировки под скрытые клиенты
не повторять запросы бесконечно
не обходить капчу
не ретраить агрессивно
```

Статусы run:

```text
created
running
parsed
partial
blocked_or_captcha
auth_required
failed
```

Статусы ad:

```text
parsed
partial
failed
duplicate_updated
```

---

# 17. Тесты

Добавить тесты:

```text
avito-module/tests/test_health.py
avito-module/tests/test_parser_static_html.py
avito-module/tests/test_normalizer.py
avito-module/tests/test_storage.py
avito-module/tests/test_contract_no_core_write.py
```

Тесты должны работать без реального avito.ru.

Использовать samples:

```text
avito-module/samples/avito_profile_sample.html
avito-module/samples/avito_item_sample.html
```

Проверить:

```text
health ok
parser извлекает объявления из sample html
normalizer делает product_card JSON
storage сохраняет parsed ads
core-import-preview вызывает validate-json или корректно мокается
Stage 03A не вызывает Core import-json
```

---

# 18. Документация

Создать/обновить:

```text
avito-module/README.md
docs/stage03a_avito_parser_module_mvp.md
docs/avito_module_architecture.md
docs/avito_parsed_ad_schema.md
docs/avito_to_product_card_mapping.md
README.md
```

В документации явно написать:

```text
Stage 03A — read-only parser MVP.
Не выполняет импорт товаров в Core.
Не выполняет публикацию.
Не обходит капчу.
Не использует браузерную автоматизацию.
```

---

# 19. Самопроверка

После реализации выполнить:

```powershell
Set-Location C:\tbootit

docker compose config
docker compose up --build -d
docker compose ps
```

Проверить Core:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
```

Проверить Avito Module:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/health
Invoke-RestMethod http://127.0.0.1:8020/api/version
Invoke-RestMethod http://127.0.0.1:8020/api/core/health
```

Проверить parser endpoint на stub/sample/local mode, если реализован:

```powershell
$body = @{
  profile_url = "sample://avito_profile_sample"
  max_pages = 1
  save_html = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8020/api/avito/profiles/parse `
  -ContentType "application/json" `
  -Body $body
```

Проверить parsed ads:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/api/avito/runs
Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads
```

Проверить product_card export:

```powershell
# взять ad_id из предыдущего ответа
Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads/<ad_id>/product-card-json
```

Проверить tests:

```powershell
docker compose exec core pytest
docker compose exec avito-module pytest
```

---

# 20. Проверка запрещенной логики

Выполнить:

```powershell
Get-ChildItem -Path "core","admin-shell","avito-module" -Recurse -File -Include *.py,*.html,*.js,*.md,requirements.txt |
  Select-String -Pattern "selenium|webdriver|undetected|pyppeteer|captcha solver|captcha-solver|обход капчи|bypass captcha|автологин|auto login" -CaseSensitive:$false
```

Если встречается только в документации как запрет — допустимо.  
Если в runtime code или requirements — блокер.

---

# 21. Отчет

Создать:

```text
reports/stage03a_avito_parser_module_mvp_report.md
```

Структура:

```text
# Stage 03A Avito Parser Module MVP Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## BRANCH

## COMMIT

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## WHAT IMPLEMENTED

## MODULE BOUNDARY

Core responsibilities:
Avito Module responsibilities:

## FILES CREATED

## DOCKER COMPOSE CHANGES

## AVITO MODULE API

## PARSER BEHAVIOR

## STORAGE

## PRODUCT_CARD_EXPORT

## CORE_IMPORT_POLICY

Должно быть:
Stage 03A does not import into Core automatically.
Only validate/preview is allowed.

## TESTS

## COMMANDS RUN

## SELF_CHECK_RESULTS

## FORBIDDEN_LOGIC_CHECK

## DOCUMENTATION

## KNOWN_LIMITATIONS

## OWNER_TESTING_GUIDE

## NEXT_RECOMMENDED_STAGE

Варианты:
- Stage 03A-Audit — independent audit
- Stage 03B — Parsed Avito Ads to Core Import
- Stage 03C — Browser Publish Assistant
- Stage 04 — Inventory/Sales/Price Tags Module
```

---

# 22. Git

После успешной проверки:

```powershell
git status
git add .
git commit -m "Add Avito parser module MVP"
git status
```

Не выполнять push без отдельной команды владельца.

---

# 23. Definition of Done

Stage 03A готов, если:

```text
создан avito-module
модуль запускается отдельным Docker service
порт 8020 работает
/health работает
/api/version работает
/api/core/health работает
можно запустить parse по sample или публичному URL
скачанные объявления сохраняются в data/avito-module
есть список runs
есть список parsed ads
есть export parsed ad → product_card JSON
нет автоматического import-json в Core
Core tests проходят
Avito module tests проходят
документация создана
отчет создан
git commit создан
```

---

# 24. Главный принцип

Stage 03A — это read-only парсинг и подготовка данных.

Не смешивать:

```text
парсинг Авито
импорт в Core
продажи
ценники
публикацию
```

Текущий этап должен дать скачанные объявления и нормализованный JSON.  
Добавление этих объявлений в базу Core будет отдельным Stage 03B.
