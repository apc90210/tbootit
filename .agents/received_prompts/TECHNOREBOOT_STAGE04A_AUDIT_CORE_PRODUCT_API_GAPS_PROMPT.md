# PROMPT — Техноребут / Stage 04A-Audit Core Product API Gaps

## Роль агента

Ты senior QA/audit engineer, backend reviewer, API contract auditor и архитектурный аудитор проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — провести независимый аудит реализованного этапа:

```text
Stage 04A — Core Product API Gaps
```

Это аудит, а не разработка нового функционала.

---

# 1. Контекст

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ.

Главная архитектура:

```text
Core API + DB + Storage = единое ядро.
Все остальные модули работают только через HTTP API.
```

Внешние модули не должны писать напрямую в БД.

---

# 2. Уже выполнено

В проекте уже были выполнены:

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
```

Известный итог Stage04A:

```text
FINAL_STATUS: TECHNOREBOOT_STAGE04A_CORE_PRODUCT_API_GAPS_READY_FOR_AUDIT
BRANCH: main
HEAD: f04a6fd
WORKTREE_CLEAN: true
commit_message: Implement Stage 04A Core product API gaps
```

Заявленная реализация:

```text
product_list_endpoint: yes
product_detail_endpoint: yes
product_patch_endpoint: yes
product_status_endpoint: yes
status_lifecycle_validation: yes
import_json_backward_compatible: yes
admin_ui_started: no
mark_sold_started: no
price_tags_started: no
```

Заявленные проверки:

```text
core_pytest: passed
avito_module_pytest: passed
product_list: passed
product_filter_status: passed
product_detail: passed
product_patch_safe_fields: passed
product_patch_rejects_unsafe: passed
product_status_valid: passed
product_status_invalid: passed
import_json_regression: passed
```

---

# 3. Цель аудита

Проверить, что Stage04A безопасно закрыл gaps Core Product API и готовит основу для будущего модуля работы с товарами, продажами и ценниками.

Ответить:

```text
можно ли переходить к Stage04B — Inventory/Sales/Price Tags Module Planning?
```

Проверить:

```text
GET /api/products
GET /api/products/{id}
PATCH /api/products/{id}
POST /api/products/{id}/status
pagination
filters
sorting
status lifecycle validation
safe patch validation
import-json backward compatibility
Core tests
Avito module regression tests
git hygiene
runtime data safety
Stage04B/04C/04D не начаты
```

---

# 4. Что запрещено делать

Не делать новую разработку.

Запрещено:

```text
начинать Stage04B UI
начинать Stage04C sale/mark-sold flow
начинать Stage04D price tag printing
менять admin-shell
менять avito-module, кроме test-only проверки
добавлять прямой доступ к БД из внешних модулей
делать browser automation
делать crawling
коммитить runtime data
коммитить *.db / *.sqlite / __pycache__ / downloaded HTML
использовать git add .
```

Разрешены только мелкие безопасные исправления:

```text
опечатки
документация
неверные порты
очевидные typos
мелкие test/docs fixes
недостающий audit report
```

Если найдены проблемы — зафиксировать и рекомендовать Stage04A-R repair.

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

# 6. Preflight

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

Проверить наличие:

```text
reports/stage04a_core_product_api_gaps_report.md
logs/2026-07-01.md
```

Проверить, что HEAD — commit Stage04A:

```text
Implement Stage 04A Core product API gaps
```

---

# 7. Scope audit

Проверить, что изменены только ожидаемые файлы:

```text
core/app/routers/products.py
core/app/schemas.py
core/tests/test_products.py
core/tests/test_products_search_filters.py
reports/stage04a_core_product_api_gaps_report.md
logs/2026-07-01.md
.agents/received_prompts/TECHNOREBOOT_STAGE04A_CORE_PRODUCT_API_GAPS_IMPLEMENTATION_PROMPT.md
```

Команда:

```powershell
git show --name-status --oneline HEAD
```

Если изменены `admin-shell` или `avito-module` runtime files — зафиксировать как issue.

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
core up
admin-shell up
avito-module up
Core: 8000
Admin Shell: 8011
Avito Module: 8020
нет restart loop
```

Логи:

```powershell
docker compose logs --tail=200 core
docker compose logs --tail=200 avito-module
```

---

# 9. Core product API smoke

Выполнить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/products | ConvertTo-Json -Depth 10
```

Если `/api/products` теперь возвращает paginated wrapper, проверить:

```text
items
total
limit
offset
```

---

# 10. Product filters/sort/pagination audit

Выполнить:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products?status=in_stock" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/products?q=Lenovo" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/products?source_type=chatgpt" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/products?sort=title" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/products?limit=5&offset=0" | ConvertTo-Json -Depth 10
```

Проверить:

```text
фильтры не падают
sort работает
limit/offset работают
пустой результат корректный
```

---

# 11. Product detail audit

Взять id товара из списка.

Выполнить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/products/<id> | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:8000/api/products/<id>/details | ConvertTo-Json -Depth 10
```

Проверить:

```text
обычная карточка работает
details Stage02 не сломан
Avito-style поля не потеряны
```

---

# 12. Product patch audit

Создать тестовый товар через `import-json` или взять тестовый товар.

Безопасный PATCH:

```powershell
$patch = @{
  title = "Аудит Stage04A товар"
  sale_price = 12345
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Patch `
  -Uri http://127.0.0.1:8000/api/products/<id> `
  -ContentType "application/json" `
  -Body $patch
```

Проверить reject cases:

```powershell
Invoke-RestMethod -Method Patch -Uri http://127.0.0.1:8000/api/products/<id> -ContentType "application/json" -Body '{"sale_price":-100}'
Invoke-RestMethod -Method Patch -Uri http://127.0.0.1:8000/api/products/<id> -ContentType "application/json" -Body '{"title":"   "}'
Invoke-RestMethod -Method Patch -Uri http://127.0.0.1:8000/api/products/<id> -ContentType "application/json" -Body '{"status":"sold"}'
```

Ожидание:

```text
валидный PATCH проходит
некорректные запросы отклоняются 400/422
status нельзя менять через generic PATCH
```

---

# 13. Product status lifecycle audit

Проверить валидный transition:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/products/<id>/status `
  -ContentType "application/json" `
  -Body '{"status":"in_stock","reason":"Stage04A audit"}'
```

Проверить валидные переходы по возможности:

```text
draft/imported -> in_stock
in_stock -> reserved
reserved -> in_stock
in_stock -> sold
in_stock -> in_repair
in_repair -> in_stock
in_stock -> written_off
```

Проверить невалидные:

```text
sold -> in_stock
written_off -> in_stock
in_stock -> draft
```

Ожидание:

```text
валидные переходы проходят
невалидные отклоняются
reason принимается
```

---

# 14. Import-json backward compatibility

Выполнить:

```powershell
$json = Get-Content .\docs\examples\product_card_lenovo_t480.json -Raw

$res = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/product-cards/import-json `
  -ContentType "application/json" `
  -Body $json

$res | ConvertTo-Json -Depth 10
```

Проверить:

```text
import-json работает
повторный import по SKU не создает дубль
товар появляется в /api/products
```

---

# 15. Avito module regression

Выполнить:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/health
Invoke-RestMethod http://127.0.0.1:8020/api/core/health
Invoke-RestMethod http://127.0.0.1:8020/api/avito/parsed-ads | ConvertTo-Json -Depth 10
```

Если есть `core-import-preview`, проверить, что validate preview работает.

---

# 16. Tests audit

Запустить:

```powershell
docker compose exec core pytest
docker compose exec avito-module pytest
```

Ожидание:

```text
Core tests pass
Avito Module tests pass
Ориентир: core 28 passed, avito-module 12 passed или больше
```

---

# 17. Safety scans

Выполнить:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module
```

Ожидание:

```text
нет runtime browser automation / captcha bypass
упоминания в docs как запрет допустимы
```

Проверить runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/avito-module
git status --ignored --short --untracked-files=all -- data/db
```

Ожидание:

```text
runtime data ignored
*.db не в индексе
```

---

# 18. Documentation/report audit

Проверить:

```text
reports/stage04a_core_product_api_gaps_report.md
logs/2026-07-01.md
```

Отчет должен содержать:

```text
FINAL_STATUS
branch/head
tests
scope
safety
commit
next step
```

---

# 19. Git hygiene audit

Выполнить:

```powershell
git status --short --untracked-files=all
git diff --stat
git diff
git log --oneline -10
```

Проверить:

```text
worktree clean или только audit report/log после аудита
нет временных файлов pytest.log/run_test.py/test_jsonable.py
нет runtime data
нет запрещенных файлов
```

---

# 20. Итоговый отчет

Создать:

```text
reports/stage04a_audit_core_product_api_gaps_report.md
```

Структура:

```text
# Stage 04A-Audit Core Product API Gaps Report

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
Core URL:
Admin Shell URL:
Avito Module URL:
Docker status:

## CHECKS RUN

## SCOPE AUDIT

Expected files:
Actual files:
Findings:

## PRODUCT LIST API AUDIT

## FILTERS_SORT_PAGINATION_AUDIT

## PRODUCT DETAIL AUDIT

## PRODUCT PATCH AUDIT

## PRODUCT STATUS LIFECYCLE AUDIT

## IMPORT_JSON_REGRESSION_AUDIT

## AVITO_MODULE_REGRESSION_AUDIT

## TESTS

## SAFETY_SCAN

## RUNTIME_DATA_AUDIT

## DOCUMENTATION_AUDIT

## GIT_HYGIENE_AUDIT

## BLOCKERS

## NON_BLOCKING_ISSUES

## RECOMMENDED_NEXT_STAGE

Варианты:
- Stage 04A-R — repair, если есть блокеры
- Stage 04B — Inventory/Sales/Price Tags Module Planning
- Stage 04B — Inventory Product Browser UI
```

---

# 21. Git commit

Если создан отчет или внесены мелкие исправления:

```powershell
git add reports\stage04a_audit_core_product_api_gaps_report.md
git add logs\2026-07-01.md
git commit -m "Audit Stage 04A Core product API gaps"
git status --short --untracked-files=all
```

Не использовать:

```text
git add .
```

Не выполнять push без отдельной команды владельца.

---

# 22. Definition of Done

Stage 04A-Audit готов, если:

```text
prompt найден и скопирован при необходимости
preflight выполнен
scope проверен
docker проверен
Core product list проверен
filters/sort/pagination проверены
product detail проверен
PATCH validation проверен
status lifecycle проверен
import-json regression проверен
Avito module regression проверен
tests запущены
safety scans выполнены
runtime data проверена
docs/report проверены
git hygiene проверен
отчет создан
commit создан, если были изменения
рекомендован следующий этап
```

---

# 23. Ожидаемая логика результата

Если всё работает и scope соблюден:

```text
STATUS: PASS
Recommended next stage: Stage 04B — Inventory/Sales/Price Tags Module Planning
```

Если есть мелкие замечания:

```text
STATUS: PASS_WITH_NOTES
Recommended next stage: Stage 04B или Stage 04A-R
```

Если найдены блокеры:

```text
STATUS: FAIL
Recommended next stage: Stage 04A-R
```

---

# 24. Главный принцип

Stage04A закрывает API gaps Core для будущего рабочего модуля товаров.

Не начинать UI, продажи и ценники до аудита Stage04A.
