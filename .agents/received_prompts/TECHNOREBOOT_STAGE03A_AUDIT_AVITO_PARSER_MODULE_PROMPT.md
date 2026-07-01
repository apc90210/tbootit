# PROMPT — Техноребут / Stage 03A-Audit Avito Parser Module MVP

## Роль агента

Ты senior QA/audit engineer, backend reviewer, integration auditor и архитектурный аудитор проекта «Техноребут».

Ты работаешь в репозитории:

```powershell
C:\tbootit
```

Твоя задача — провести независимый аудит уже реализованного этапа:

```text
Stage 03A — Avito Parser Module MVP
```

Это аудит, а не разработка нового функционала.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Главная архитектура:

```text
Core API + DB + Storage = единое ядро системы.
Все остальные модули работают только через HTTP API.
```

Core API уже реализован и проверен как основа для внешних модулей.

Core умеет:

```text
хранить товары
хранить Avito-style карточки
валидировать product_card JSON
импортировать product_card JSON
отдавать карточки товаров через API
хранить историю импортов
```

Avito-модуль должен быть внешним модулем, который работает с Core только через HTTP API.

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
Stage 03A — Avito Parser Module MVP
```

Известный результат Stage 03A:

```text
создан avito-module
добавлен Docker service
порт 8020
/health работает
/api/core/health работает
/api/avito/profiles/parse работает
есть read-only parser MVP
есть samples
есть storage в data/avito-module
есть export parsed ad → product_card JSON
есть core-import-preview без записи в Core
9 pytest в avito-module проходят
отчет создан: reports/stage03a_avito_parser_module_mvp_report.md
commit: feat: complete Stage 03A Avito Parser Module MVP
```

Текущие адреса:

```text
Core API:      http://127.0.0.1:8000
Admin Shell:   http://127.0.0.1:8011
Avito Module:  http://127.0.0.1:8020
```

---

# 3. Цель Stage 03A-Audit

Проверить, что Avito Parser Module MVP реализован правильно и безопасно как отдельный read-only модуль.

Ответить:

```text
можно ли переходить к Stage 03B — Parsed Avito Ads to Core Import?
```

Проверить:

```text
модульная граница Core / Avito Module
read-only поведение Stage 03A
отсутствие прямого доступа к БД Core
отсутствие автоматического импорта в Core
отсутствие браузерной автоматизации
отсутствие обхода капчи/антибот-защиты
storage avito-module
sample parser
product_card export
core validate preview
Docker compose
tests
документацию
git hygiene
```

---

# 4. Что запрещено делать в Stage 03A-Audit

Не делать большую разработку.

Запрещено:

```text
реализовывать Stage 03B
добавлять импорт в Core
добавлять автопубликацию
добавлять браузерную автоматизацию
добавлять Selenium/Playwright
добавлять обход капчи
переписывать avito-module
переписывать Core
делать прямой доступ к БД Core
```

Разрешены только мелкие безопасные исправления:

```text
опечатки
документация
неверные порты
очевидные typos
недостающий отчет
мелкие test/docs fixes
```

Если найдены технические проблемы — зафиксировать и рекомендовать repair-stage.

---

# 5. Архитектурная граница

Правильная схема:

```text
Avito Module → Core API → Core DB
```

Неправильная схема:

```text
Avito Module → Core DB напрямую
```

Avito Module может:

```text
скачивать публичные объявления read-only
сохранять parsed ads в data/avito-module
делать product_card JSON
делать validate preview через Core API
```

Avito Module на Stage 03A не должен:

```text
импортировать товар в Core
писать в Core DB
читать Core DB
управлять браузером
логиниться в Авито
обходить капчу
публиковать объявления
```

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
```

Проверить, что есть отчет Stage 03A:

```text
reports/stage03a_avito_parser_module_mvp_report.md
```

Проверить структуру:

```text
avito-module/
avito-module/app/
avito-module/tests/
avito-module/samples/
data/avito-module/
```

Если есть незакоммиченные изменения — разобраться и зафиксировать в отчете.

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
avito-module запущен
Core порт 8000
Admin Shell порт 8011
Avito Module порт 8020
нет restart loop
```

Логи:

```powershell
docker compose logs --tail=200 core
docker compose logs --tail=200 admin-shell
docker compose logs --tail=200 avito-module
```

---

# 9. Core smoke audit

Выполнить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
```

Проверить, что Core не сломан после добавления avito-module.

---

# 10. Avito Module smoke audit

Выполнить:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/health
Invoke-RestMethod http://127.0.0.1:8020/api/version
Invoke-RestMethod http://127.0.0.1:8020/api/core/health
```

Ожидание:

```text
/health status ok
/api/version показывает avito-module
/api/core/health успешно достучался до Core
```

Если endpoint `/api/version` отсутствует, зафиксировать как issue.

---

# 11. Проверка read-only parser behavior

Проверить sample/local parse.

Выполнить:

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

Если sample mode не поддерживается, использовать моковую ссылку, которую поддерживает реализация, и зафиксировать фактическое поведение.

Проверить:

```text
возвращается run_id
ads_found или status понятен
run сохраняется
parsed ads сохраняются
нет автоматического импорта в Core
```

Проверить runs:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/api/avito/runs | ConvertTo-Json -Depth 10
```

Проверить parsed ads:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads | ConvertTo-Json -Depth 10
```

---

# 12. Product Card export audit

Взять `ad_id` из parsed ads и проверить:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads/<ad_id>/product-card-json | ConvertTo-Json -Depth 10
```

Проверить, что JSON совместим с Core product_card форматом:

```text
source
schema_version
operation
product
avito
site
```

Проверить обязательные поля:

```text
product.sku
product.title
product.sale_price
avito.title
avito.description
avito.price
```

---

# 13. Core import preview audit

Проверить:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8020/api/avito/parsed-ads/<ad_id>/core-import-preview
```

Ожидание:

```text
Avito Module формирует product_card JSON
отправляет его в Core validate-json
получает validation result
НЕ вызывает Core import-json
```

Если endpoint называется иначе — найти и проверить аналог.

---

# 14. Проверка отсутствия автоматического импорта в Core

Проверить код:

```powershell
Get-ChildItem -Path "avito-module" -Recurse -File -Include *.py,*.html,*.js,*.md,requirements.txt |
  Select-String -Pattern "import-json|/api/product-cards/import-json|product-cards/import-json" -CaseSensitive:$false
```

Оценить найденное:

```text
упоминание в docs как будущий Stage 03B — допустимо
упоминание в тесте запрета — допустимо
реальный вызов import-json в runtime Stage 03A — блокер
```

На Stage 03A допустим только:

```text
validate-json
core-import-preview
product-card-json export
```

---

# 15. Проверка отсутствия прямого доступа к Core DB

Выполнить:

```powershell
Get-ChildItem -Path "avito-module" -Recurse -File -Include *.py,*.html,*.js,*.md,requirements.txt |
  Select-String -Pattern "sqlite|technoreboot.db|data/db|SessionLocal|create_engine|sqlalchemy|SELECT .* FROM products|INSERT INTO products" -CaseSensitive:$false
```

Оценить:

```text
документация с запретом — допустимо
runtime прямой доступ к Core DB — блокер
```

Avito Module может иметь свое локальное JSON storage или собственную локальную БД, но не Core DB.

---

# 16. Проверка отсутствия запрещенной автоматизации

Выполнить:

```powershell
Get-ChildItem -Path "core","admin-shell","avito-module" -Recurse -File -Include *.py,*.html,*.js,*.md,requirements.txt |
  Select-String -Pattern "selenium|playwright|webdriver|undetected|pyppeteer|captcha solver|captcha-solver|обход капчи|bypass captcha|автологин|auto login|chromium" -CaseSensitive:$false
```

Оценить:

```text
упоминание в docs как запрет — допустимо
runtime dependency или runtime code — блокер
```

---

# 17. Storage audit

Проверить:

```powershell
Get-ChildItem -Path "data\avito-module" -Recurse -ErrorAction SilentlyContinue |
  Select-Object FullName, Length, LastWriteTime
```

Проверить:

```text
runs сохраняются
parsed ads сохраняются
HTML snapshots сохраняются только если save_html=true
storage отделен от Core data/db
runtime storage не должен быть закоммичен в git
```

Проверить `.gitignore`:

```powershell
Get-Content .gitignore
git status --ignored
```

Нужно убедиться, что runtime `data/avito-module` не попадет в git, кроме intentional sample files.

---

# 18. Tests audit

Запустить:

```powershell
docker compose exec core pytest
docker compose exec avito-module pytest
```

Ожидание:

```text
Core tests pass
Avito Module tests pass
Ориентир: avito-module 9 tests или больше
```

Проверить наличие тестов:

```text
avito-module/tests/test_health.py
avito-module/tests/test_parser_static_html.py
avito-module/tests/test_normalizer.py
avito-module/tests/test_storage.py
avito-module/tests/test_contract_no_core_write.py
```

Проверить, что тесты не требуют реального avito.ru.

---

# 19. Documentation audit

Проверить:

```text
avito-module/README.md
docs/stage03a_avito_parser_module_mvp.md
docs/avito_module_architecture.md
docs/avito_parsed_ad_schema.md
docs/avito_to_product_card_mapping.md
reports/stage03a_avito_parser_module_mvp_report.md
README.md
```

Проверить, что документация явно говорит:

```text
Stage 03A — read-only parser MVP
не импортирует товары в Core
не публикует объявления
не обходит капчу
не использует браузерную автоматизацию
следующий этап — Stage 03B import to Core
```

---

# 20. API contract audit

Проверить, что Avito Module API соответствует смыслу:

```text
GET  /health
GET  /api/version
GET  /api/core/health
POST /api/avito/profiles/parse
GET  /api/avito/runs
GET  /api/avito/runs/{run_id}
GET  /api/avito/parsed-ads
GET  /api/avito/parsed-ads/{ad_id}
GET  /api/avito/parsed-ads/{ad_id}/product-card-json
POST /api/avito/parsed-ads/{ad_id}/core-import-preview
```

Если часть endpoints отсутствует, оценить:

```text
блокер
неблокирующая недоработка
или фактический альтернативный endpoint
```

---

# 21. Git hygiene audit

Выполнить:

```powershell
git status
git diff --stat
git diff
git log --oneline -10
```

Проверить:

```text
нет runtime данных в git
нет pytest.log
нет run_test.py, test_jsonable.py, временных debug files, если они не нужны
нет data/avito-module runtime files в индексе
нет случайных файлов Antigravity brain/task вне expected
```

Если есть временные файлы после Stage 03A, удалить или зафиксировать как issue.

---

# 22. Итоговый отчет

Создать:

```text
reports/stage03a_audit_avito_parser_module_report.md
```

Структура отчета:

```text
# Stage 03A-Audit Avito Parser Module Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## EXECUTIVE SUMMARY

Коротко: можно ли переходить к Stage 03B.

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
Avito Module URL:
Docker status:

## CHECKS RUN

Список команд.

## MODULE BOUNDARY AUDIT

Core responsibilities:
Avito Module responsibilities:
Findings:

## READ_ONLY_POLICY_AUDIT

## CORE_DB_ACCESS_AUDIT

## CORE_IMPORT_POLICY_AUDIT

## FORBIDDEN_AUTOMATION_AUDIT

## DOCKER_AUDIT

## API_SMOKE_AUDIT

## PARSER_SAMPLE_AUDIT

## PRODUCT_CARD_EXPORT_AUDIT

## CORE_VALIDATE_PREVIEW_AUDIT

## STORAGE_AUDIT

## TESTS

## DOCUMENTATION_AUDIT

## GIT_HYGIENE_AUDIT

## BLOCKERS

## NON_BLOCKING_ISSUES

## RECOMMENDED_NEXT_STAGE

Варианты:
- Stage 03A-R — repair, если есть блокеры
- Stage 03B — Parsed Avito Ads to Core Import
- Stage 04 — Inventory/Sales/Price Tags Module
```

---

# 23. Git commit

Если создан отчет или внесены мелкие исправления:

```powershell
git add .
git commit -m "Audit Stage 03A Avito parser module"
git status
```

Не выполнять push без отдельной команды владельца.

---

# 24. Definition of Done

Stage 03A-Audit готов, если:

```text
prompt найден и скопирован при необходимости
preflight выполнен
docker проверен
Core smoke проверен
Avito Module smoke проверен
sample parser проверен
runs проверены
parsed ads проверены
product_card export проверен
core validate preview проверен
отсутствие import-json runtime вызова проверено
отсутствие прямого Core DB доступа проверено
отсутствие запрещенной автоматизации проверено
storage проверен
tests запущены
documentation проверена
git hygiene проверен
отчет создан
commit создан, если были изменения
рекомендован следующий этап
```

---

# 25. Ожидаемая логика результата

Если всё работает и границы соблюдены:

```text
STATUS: PASS
Recommended next stage: Stage 03B — Parsed Avito Ads to Core Import
```

Если есть мелкие замечания:

```text
STATUS: PASS_WITH_NOTES
Recommended next stage: Stage 03B или Stage 03A-R
```

Если найдены блокеры:

```text
STATUS: FAIL
Recommended next stage: Stage 03A-R
```

---

# 26. Главный принцип

Stage 03A должен дать скачанные объявления и нормализованный JSON.

Добавление объявлений в Core — отдельный Stage 03B.

Продажи и ценники — отдельный Stage 04.
