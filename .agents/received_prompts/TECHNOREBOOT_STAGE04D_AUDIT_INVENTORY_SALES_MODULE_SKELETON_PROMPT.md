# PROMPT — Техноребут / Stage 04D-Audit Inventory/Sales Module Skeleton

## Роль агента

Ты senior QA/audit engineer, fullstack reviewer, Docker integration auditor и архитектурный аудитор проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — провести независимый аудит реализованного этапа:

```text
Stage 04D — Inventory/Sales Module Skeleton
```

Это аудит, а не новая разработка.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ.

Главная архитектура:

```text
Core API + DB + Storage = единое ядро.
Все остальные модули работают только через HTTP API.
```

`inventory-sales-module` должен быть отдельным внешним модулем и работать только через Core API.

Правильная схема:

```text
inventory-sales-module → Core API → Core DB
```

Неправильная схема:

```text
inventory-sales-module → Core DB напрямую
```

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
Stage 04A — Core Product API Gaps
Stage 04A-Audit — Core Product API Gaps Audit
Stage 04B — Inventory/Sales/Price Tags Module Planning
Stage 04C — Core Sales Flow Hardening
Stage 04C-Audit — Core Sales Flow Hardening Audit
Stage 04D — Inventory/Sales Module Skeleton
```

Известный заявленный результат Stage04D:

```text
создан inventory-sales-module
добавлен Docker service на порт 8030
реализован Core API client через httpx
реализованы русские Jinja2 templates
реализованы health/products/product_detail routes
реализован fallback при недоступном Core
созданы tests: test_products_routes.py, test_health.py, test_core_client.py, test_no_direct_db_access.py
созданы docs/report
заявлено: 8 tests passed
commit: 9888c38 / feat(module): stage 04D inventory-sales-module skeleton
UI: http://localhost:8030
```

Важные caveats из execution log:

```text
агент использовал git add . хотя это было запрещено prompt'ом
после git commit агент дописал final entry в logs/2026-07-01.md
нужно проверить, действительно ли worktree clean
агент написал "pushed securely to main", но в логе нет git push; вероятно был только локальный commit on main
```

---

# 3. Цель Stage04D-Audit

Проверить, что `inventory-sales-module` skeleton реализован корректно, изолированно и безопасно.

Ответить:

```text
можно ли переходить к Stage04E — Sales UI MVP?
```

Проверить:

```text
модуль отдельный
Docker service 8030 работает
UI routes работают
Core API client работает
прямого DB access нет
продажи не реализованы
ценники не реализованы
UI на русском
Core/Avito regressions не сломаны
tests проходят
docs/report корректны
git hygiene после git add . не нарушена
runtime data не закоммичена
```

---

# 4. Что запрещено делать в аудите

Не делать новую разработку.

Запрещено:

```text
начинать Stage04E Sales UI
начинать Stage04F Price Tags
реализовывать продажу через UI
реализовывать печать ценников
менять Core sales logic без явного audit bug
менять avito-module runtime
менять admin-shell
делать прямой DB access
использовать git add .
использовать git add -u
использовать git reset / git clean / amend / rebase / force push
```

Разрешены только мелкие audit fixes:

```text
отчет
документация
лог
очевидные typos
малые тестовые правки
минимальная правка 500 bug, если smoke нашел проблему
```

Если найден серьезный баг — зафиксировать `FAIL` и рекомендовать `Stage04D-R`.

---

# 5. Обязательное правило поиска prompt-файлов

Перед началом работы найти актуальные prompt-файлы.

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

Выполнить:

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

В отчете указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 6. Preflight / Git state

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -15
git show --name-status --oneline --stat HEAD

docker compose ps
docker compose config
```

Проверить:

```text
HEAD действительно Stage04D commit или последующий log commit
worktree clean после final log
нет untracked/unstaged logs
нет runtime files
```

Особо проверить последствия `git add .`:

```powershell
git show --name-status --oneline --stat 9888c38
git show --name-only 9888c38
```

Если HEAD другой — найти Stage04D commit в последних 10 commits.

---

# 7. Scope audit

Ожидаемые изменения Stage04D:

```text
inventory-sales-module/**
docker-compose.yml
docs/stage04d_inventory_sales_module_skeleton.md
docs/inventory_sales_module_architecture.md
docs/inventory_sales_module_ui_map.md
reports/stage04d_inventory_sales_module_skeleton_report.md
logs/2026-07-01.md
.agents/received_prompts/TECHNOREBOOT_STAGE04D_INVENTORY_SALES_MODULE_SKELETON_PROMPT.md
```

Проверить, что не попали:

```text
runtime DB
data/db/**
data/avito-module/**
__pycache__
.pytest_cache
downloaded HTML
temporary brain artifacts
implementation_plan.md в корень, если не предусмотрен правилами проекта
task.md в корень, если не предусмотрен правилами проекта
walkthrough.md в корень, если не предусмотрен правилами проекта
```

Команды:

```powershell
git status --short --untracked-files=all
git show --name-status --oneline --stat HEAD
git ls-files | Select-String -Pattern "data/db|data/avito-module|__pycache__|pytest_cache|technoreboot.db|\.sqlite|downloaded|implementation_plan|walkthrough"
```

---

# 8. Docker rebuild audit

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
avito-module up
inventory-sales-module up
Core: 8000
Admin Shell: 8011
Avito Module: 8020
Inventory/Sales Module: 8030
нет restart loop
```

Логи:

```powershell
docker compose logs --tail=150 inventory-sales-module
docker compose logs --tail=100 core
docker compose logs --tail=100 avito-module
```

---

# 9. API smoke

Проверить новый модуль:

```powershell
Invoke-RestMethod http://127.0.0.1:8030/health
Invoke-RestMethod http://127.0.0.1:8030/api/version
Invoke-RestMethod http://127.0.0.1:8030/api/core/health
```

Ожидание:

```text
/health ok
/api/version показывает inventory-sales-module
/api/core/health показывает связь с Core
```

Проверить Core:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/products | ConvertTo-Json -Depth 5
```

---

# 10. HTML UI smoke

Открыть в браузере или проверить HTTP:

```text
http://127.0.0.1:8030/
http://127.0.0.1:8030/products
http://127.0.0.1:8030/products/<existing_product_id>
```

Для existing product id взять:

```powershell
$products = Invoke-RestMethod http://127.0.0.1:8000/api/products
$productId = $products.items[0].id
$productId
```

Проверить через curl/Invoke-WebRequest:

```powershell
Invoke-WebRequest http://127.0.0.1:8030/ | Select-Object StatusCode
Invoke-WebRequest http://127.0.0.1:8030/products | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products/$productId" | Select-Object StatusCode
```

Проверить:

```text
страницы открываются 200
нет 500
русский текст виден
товары из Core отображаются
карточка товара отображается
```

---

# 11. Read-only boundary audit

Проверить, что Stage04D не делает write operations.

Искать в `inventory-sales-module`:

```powershell
git grep -n -I "post\|patch\|delete\|put\|create_sale\|cancel_sale\|/api/sales\|/status\|import-json" -- inventory-sales-module
```

Оценить:

```text
тестовый mock или docs placeholder — допустимо
реальный write call в runtime code — блокер
```

На Stage04D допустимы только read-only вызовы:

```text
Core health
GET /api/products
GET /api/products/{id}
GET /api/products/{id}/details
```

---

# 12. Direct DB access audit

Выполнить:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Ожидание:

```text
нет прямого DB access
requirements.txt не содержит sqlalchemy/sqlite db deps
```

Если `sqlite` встречается только в test name/comment как запрет — допустимо.

---

# 13. Russian UI audit

Проверить templates:

```powershell
Get-ChildItem inventory-sales-module\app\templates -Recurse -File |
  Select-String -Pattern "Products|Sales|Price Tags|Open|Sell|Print|Error|Back|Search|Status|Price" -CaseSensitive:$false
```

Оценить:

```text
пользовательский английский текст — issue
технические переменные/classes — допустимо
```

UI должен быть на русском:

```text
Товары
Продажи — скоро
Ценники — скоро
Открыть
Продать — скоро
Ценник — скоро
Ошибка
Назад
Поиск
Статус
Цена
```

---

# 14. Placeholder audit

Проверить:

```text
кнопка Продать не выполняет sale
кнопка Ценник не печатает
они disabled или явно "будет реализовано позже"
```

Искать:

```powershell
git grep -n -I "Продать\|Ценник\|Stage04E\|Stage04F\|disabled" -- inventory-sales-module/app/templates inventory-sales-module/app/static
```

---

# 15. Tests audit

Запустить:

```powershell
docker compose exec inventory-sales-module pytest
docker compose exec core pytest
docker compose exec avito-module pytest
```

Ожидание:

```text
inventory-sales-module tests pass, ориентир 8 tests или больше
core tests pass
avito-module tests pass
```

---

# 16. Safety scans

Выполнить:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

Ожидание:

```text
нет browser automation / captcha bypass
```

Проверить runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

---

# 17. Documentation audit

Проверить:

```text
inventory-sales-module/README.md
docs/stage04d_inventory_sales_module_skeleton.md
docs/inventory_sales_module_architecture.md
docs/inventory_sales_module_ui_map.md
reports/stage04d_inventory_sales_module_skeleton_report.md
logs/2026-07-01.md
```

Проверить, что docs явно говорят:

```text
Stage04D — read-only skeleton
продажи будут Stage04E
ценники будут Stage04F
нет прямого DB access
модуль работает через Core API
```

---

# 18. Final report

Создать:

```text
reports/stage04d_audit_inventory_sales_module_skeleton_report.md
```

Структура:

```text
# Stage 04D-Audit Inventory/Sales Module Skeleton Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## EXECUTIVE SUMMARY

Коротко: можно ли переходить к Stage04E.

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
Inventory/Sales Module URL:
Docker status:

## GIT_STATE_AUDIT

Stage04D commit:
Worktree status:
git add dot impact:
Findings:

## SCOPE_AUDIT

Expected files:
Actual files:
Unexpected files:
Findings:

## DOCKER_AUDIT

## API_SMOKE_AUDIT

## HTML_UI_AUDIT

## READ_ONLY_BOUNDARY_AUDIT

## DIRECT_DB_ACCESS_AUDIT

## RUSSIAN_UI_AUDIT

## PLACEHOLDER_AUDIT

## TESTS

## SAFETY_SCAN

## RUNTIME_DATA_AUDIT

## DOCUMENTATION_AUDIT

## BLOCKERS

## NON_BLOCKING_ISSUES

## RECOMMENDED_NEXT_STAGE

Варианты:
- Stage04D-R — repair, если есть блокеры
- Stage04E — Sales UI MVP
```

---

# 19. Git commit

Если создан audit report/log:

```powershell
git add reports/stage04d_audit_inventory_sales_module_skeleton_report.md
git add logs/2026-07-01.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04D_AUDIT_INVENTORY_SALES_MODULE_SKELETON_PROMPT.md
git commit -m "Audit Stage 04D inventory sales module skeleton"
git status --short --untracked-files=all
```

Не использовать:

```text
git add .
git add -u
git commit --amend
```

Не выполнять push без отдельной команды владельца.

---

# 20. Definition of Done

Stage04D-Audit готов, если:

```text
prompt найден и скопирован
preflight выполнен
git add . последствия проверены
worktree clean проверен
Docker rebuild выполнен
inventory-sales-module работает на 8030
/health работает
/api/version работает
/api/core/health работает
/ открывается
/products открывается
/products/{id} открывается
read-only boundary проверен
direct DB access отсутствует
UI на русском проверен
продажи/ценники только placeholder
inventory-sales-module tests pass
core tests pass
avito-module tests pass
safety scan выполнен
runtime data проверена
docs/report проверены
audit report создан
commit создан
```

---

# 21. Ожидаемый итог

Если всё хорошо:

```text
STATUS: PASS
Recommended next stage: Stage04E — Sales UI MVP
```

Если есть мелкие замечания:

```text
STATUS: PASS_WITH_NOTES
Recommended next stage: Stage04E или Stage04D-R
```

Если есть блокеры:

```text
STATUS: FAIL
Recommended next stage: Stage04D-R
```

---

# 22. Главный принцип

Stage04D должен доказать:

```text
отдельный рабочий модуль магазина видит товары из Core
карточки открываются
модуль не пишет в БД
модуль не продает
модуль не печатает ценники
```

Только после этого можно делать Stage04E — продажу через UI.
