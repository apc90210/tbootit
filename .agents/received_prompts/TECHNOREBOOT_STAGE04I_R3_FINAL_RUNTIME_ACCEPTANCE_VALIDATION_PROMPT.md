# PROMPT — Техноребут / Stage04I-R3 Final Runtime Acceptance Validation

## Роль

Ты senior release auditor, FastAPI runtime validator, QA engineer и Git release checker проекта «Техноребут».

Репозиторий:

```powershell
C:\tbootit
```

Твоя задача — выполнить финальную runtime-валидацию Stage04I-R2 без расширения функционала.

Новый функциональный этап не начинать.

---

# 1. Текущий статус

Предыдущий отчёт заявил:

```text
TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_LOOKUP_RUNTIME_AUDIT_READY_FOR_OWNER_RECHECK
```

Основные исправления подтверждены:

```text
reserved блокируется
/by-barcode ищет только точный barcode
bulk generation идемпотентен
manual print price не меняет Product.price
Core / Inventory / Avito tests проходят
commit f6a7100 pushed
worktree clean
```

Но в отчёте отсутствуют два обязательных runtime-доказательства:

```text
1. Денежная корректность Stage04G после sale / cancel / reissue.
2. Блокировка товара из неправильной storage location.
```

---

# 2. Целевой статус

```text
TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_READY_FOR_OWNER_CHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Запреты

Запрещено:

```text
начинать следующий этап
добавлять новый функционал без необходимости
ссылаться только на старый отчёт
использовать старые runtime результаты
direct DB access из inventory-sales-module
git add .
git add -A
git add -u
git commit --amend
git reset
git clean
rebase
force push
Base.metadata.drop_all/create_all
коммитить runtime DB/temp/cache
```

Если проверка выявляет баг — исправить точечно, добавить тест и заново прогнать полный regression.

---

# 4. Prompt discovery

Найти точный prompt:

```text
TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_VALIDATION_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit\.agents\received_prompts
C:\tbootit
```

Если найден в Downloads — скопировать:

```powershell
Copy-Item `
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_VALIDATION_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_VALIDATION_PROMPT.md `
  -Force
```

В отчёте:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
PROMPT_SHA256:
```

---

# 5. Preflight

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Ожидаемый исходный HEAD:

```text
f6a7100
```

Если другой — зафиксировать фактический HEAD и объяснить.

---

# 6. Fresh Docker state

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose up -d avito-module
docker compose ps
```

Проверить health всех сервисов.

---

# 7. Runtime validation — wrong storage location

Создать или выбрать реальный товар со следующими условиями:

```text
status = in_stock или available
quantity > 0
storage_location != store
```

Зафиксировать:

```text
PRODUCT_ID:
BARCODE:
STATUS:
QUANTITY:
STORAGE_LOCATION:
```

Отправить barcode через:

```text
POST /cart/scan
```

Ожидаемо:

```text
товар не добавлен в корзину
HTTP не 500
русское сообщение:
"Товар находится не в магазине и недоступен для продажи."
```

Допустима эквивалентная понятная русская формулировка.

После проверки убедиться:

```text
cart не изменился
quantity товара не изменилась
status товара не изменился
```

---

# 8. Runtime validation — Stage04G money integrity

Создать отдельный тестовый товар и выполнить полный цикл.

Зафиксировать до начала:

```text
PRODUCT_ID:
BARCODE:
SALE_PRICE:
PAYMENT_METHOD:
REPORT_TOTAL_BEFORE:
PAYMENT_BUCKET_BEFORE:
SALES_COUNT_BEFORE:
ITEMS_COUNT_BEFORE:
```

## 8.1 Создание продажи

Создать продажу.

Зафиксировать:

```text
ORIGINAL_SALE_ID:
REPORT_TOTAL_AFTER_SALE:
PAYMENT_BUCKET_AFTER_SALE:
SALES_COUNT_AFTER_SALE:
ITEMS_COUNT_AFTER_SALE:
```

Ожидаемо:

```text
REPORT_TOTAL_AFTER_SALE = REPORT_TOTAL_BEFORE + SALE_PRICE
PAYMENT_BUCKET_AFTER_SALE = PAYMENT_BUCKET_BEFORE + SALE_PRICE
SALES_COUNT_AFTER_SALE = SALES_COUNT_BEFORE + 1
ITEMS_COUNT_AFTER_SALE увеличился на количество товара
```

## 8.2 Отмена продажи

Отменить продажу с причиной:

```text
Stage04I-R3 runtime acceptance validation
```

Зафиксировать:

```text
SALE_STATUS_AFTER_CANCEL:
PRODUCT_STATUS_AFTER_CANCEL:
REPORT_TOTAL_AFTER_CANCEL:
PAYMENT_BUCKET_AFTER_CANCEL:
SALES_COUNT_AFTER_CANCEL:
ITEMS_COUNT_AFTER_CANCEL:
```

Ожидаемо:

```text
SALE_STATUS_AFTER_CANCEL = canceled
товар вернулся в наличие
REPORT_TOTAL_AFTER_CANCEL = REPORT_TOTAL_BEFORE
PAYMENT_BUCKET_AFTER_CANCEL = PAYMENT_BUCKET_BEFORE
SALES_COUNT_AFTER_CANCEL = SALES_COUNT_BEFORE
ITEMS_COUNT_AFTER_CANCEL = ITEMS_COUNT_BEFORE
```

Проверить:

```text
canceled sale отсутствует в денежной детализации действующих продаж
```

## 8.3 Повторное оформление

Выполнить reissue.

Зафиксировать:

```text
REISSUED_SALE_ID:
ORIGINAL_STATUS_AFTER_REISSUE:
REISSUED_STATUS:
SOURCE_SALE_ID:
SUPERSEDED_BY_SALE_ID:
REPORT_TOTAL_AFTER_REISSUE:
PAYMENT_BUCKET_AFTER_REISSUE:
SALES_COUNT_AFTER_REISSUE:
ITEMS_COUNT_AFTER_REISSUE:
```

Ожидаемо:

```text
original status = superseded
reissued sale связана с original
original связана с reissued
REPORT_TOTAL_AFTER_REISSUE = REPORT_TOTAL_BEFORE + новая сумма
новая сумма входит ровно один раз
superseded sale не входит в деньги
reissued sale входит в деньги
```

---

# 9. Runtime report filter validation

Проверить Core и UI:

```text
/reports/sales
/reports/sales?period=today
/reports/sales?period=week
/reports/sales?period=month
/reports/sales?period=year
```

Для каждого:

```text
HTTP 200
date_from корректна
date_to = сегодня
money_summary существует
total_amount существует
sales существует
```

Точные правила:

```text
default:
1 января текущего года — сегодня

today:
сегодня — сегодня

week:
понедельник текущей недели — сегодня

month:
первое число текущего месяца — сегодня

year:
1 января текущего года — сегодня
```

---

# 10. Runtime barcode acceptance recheck

Повторно проверить после bulk generation:

```text
TOTAL_PRODUCTS:
WITH_BARCODE:
WITHOUT_BARCODE:
DUPLICATES:
```

Ожидаемо:

```text
WITHOUT_BARCODE = 0
DUPLICATES = 0
```

Проверить:

```text
реальный barcode через /by-barcode → 200
SKU через /by-barcode → 404
Product ID через /by-barcode → 404
```

---

# 11. Runtime scanner acceptance recheck

Проверить:

```text
in_stock → добавляется
reserved → блокируется
sold → блокируется
draft → блокируется
quantity=0 → блокируется
wrong storage_location → блокируется
unknown barcode → блокируется
SKU → блокируется
Product ID → блокируется
```

Для каждого указать:

```text
barcode/input
HTTP status
UI message
cart changed: yes/no
```

---

# 12. Runtime price-tag acceptance recheck

Выбрать реальный товар.

Зафиксировать:

```text
PRODUCT_ID:
BARCODE:
PRODUCT_PRICE_BEFORE:
PRINT_PRICE:
PRODUCT_PRICE_AFTER:
```

Проверить HTML:

```text
@page size 58mm 40mm
price-tag width 58mm
price-tag height 40mm
SVG barcode
barcode digits
title
price
warranty
Печать
Закрыть
```

Ожидаемо:

```text
PRODUCT_PRICE_AFTER == PRODUCT_PRICE_BEFORE
```

---

# 13. Fresh full regression

После runtime validation выполнить:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Указать только финальные фактические числа.

Если что-либо исправлялось:

```text
пересобрать контейнеры
повторить runtime сценарий
повторить полный regression
```

---

# 14. Safety scans

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
```

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 15. Documentation and report

Создать:

```text
docs/stage04i_r3_final_runtime_acceptance_validation.md
reports/stage04i_r3_final_runtime_acceptance_validation_report.md
```

Обновить:

```text
logs/2026-07-23.md
```

Report structure:

```text
# Stage04I-R3 Final Runtime Acceptance Validation Report

## STATUS

## PREFLIGHT

## WRONG_STORAGE_LOCATION_RUNTIME

PRODUCT_ID:
BARCODE:
STATUS:
QUANTITY:
STORAGE_LOCATION:
HTTP:
MESSAGE:
CART_CHANGED:

## STAGE04G_MONEY_INTEGRITY

### Before sale
### After sale
### After cancel
### After reissue

## REPORT_FILTERS

Default:
Today:
Week:
Month:
Year:

## BARCODE_RUNTIME

TOTAL_PRODUCTS:
WITH_BARCODE:
WITHOUT_BARCODE:
DUPLICATES:
Strict barcode:
SKU rejected:
ID rejected:

## SCANNER_RUNTIME

in_stock:
reserved:
sold:
draft:
quantity_zero:
wrong_location:
unknown:
SKU:
ID:

## PRICE_TAG_RUNTIME

PRODUCT_ID:
PRODUCT_PRICE_BEFORE:
PRINT_PRICE:
PRODUCT_PRICE_AFTER:
UNCHANGED:
PRINT_CSS:
BARCODE_SVG:

## FINAL_TESTS

Core:
Inventory:
Avito:

## SAFETY_SCAN

## FILES_CHANGED

## COMMIT

## PUSH

## FINAL_GIT_STATUS

## OWNER_CHECK_GUIDE

## FINAL_STATUS
```

---

# 16. Git finalization

Если код не изменялся, закоммитить только prompt/report/docs/log.

Если код исправлялся, добавить только конкретные файлы.

Запрещены wildcard staging и массовый add.

Пример targeted add:

```powershell
git add docs/stage04i_r3_final_runtime_acceptance_validation.md
git add reports/stage04i_r3_final_runtime_acceptance_validation_report.md
git add logs/2026-07-23.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_VALIDATION_PROMPT.md
```

Если лог ignored:

```powershell
git add -f logs/2026-07-23.md
```

Коммит:

```powershell
git commit -m "Validate Stage 04I runtime acceptance"
git push origin main
```

После push:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

Финальный Git status должен быть пустым.

---

# 17. Definition of Done

Готово только если:

```text
wrong storage location реально блокируется
cart не меняется
Stage04G total проверен до/после sale
Stage04G total возвращается после cancel
payment bucket возвращается после cancel
canceled не входит в отчёт
superseded не входит в отчёт
reissued входит ровно один раз
report filter dates корректны
WITHOUT_BARCODE = 0
DUPLICATES = 0
strict barcode lookup подтверждён
все scanner статусы подтверждены
manual print price isolation подтверждена
Core tests PASS
Inventory tests PASS
Avito tests PASS
safety scans clean
targeted commit
push
clean git
owner manual check required
```

---

# 18. Final answer required

Обязательно указать:

```text
wrong-location runtime result
реальные report totals before/sale/cancel/reissue
payment bucket before/sale/cancel/reissue
sales/items counts
report filter date ranges
barcode totals and duplicates
scanner matrix
Product.price before/print/after
Core/Inventory/Avito tests
commit hash
push result
final git status
```

Успешный статус:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

При проблеме:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_FAIL

BLOCKERS:
...
```
