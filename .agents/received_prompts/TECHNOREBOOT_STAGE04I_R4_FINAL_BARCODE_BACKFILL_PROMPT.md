# PROMPT — Техноребут / Stage04I-R4 Final Barcode Backfill and Clean Acceptance State

## Роль

Ты senior release auditor, FastAPI runtime validator и data-integrity engineer проекта «Техноребут».

Репозиторий:

```powershell
C:\tbootit
```

Твоя задача — устранить последний блокер Stage04I: после runtime-тестов в Core осталось 7 товаров без barcode.

Новый функциональный этап не начинать.

---

# 1. Причина отказа в приёмке

В Stage04I-R3 report указано:

```text
TOTAL_PRODUCTS: 66
WITH_BARCODE: 59
WITHOUT_BARCODE: 7
DUPLICATES: 0
```

Это нарушает owner requirement:

```text
У каждого товара должен быть уникальный штрихкод.
```

И нарушает Definition of Done предыдущего prompt:

```text
WITHOUT_BARCODE = 0
DUPLICATES = 0
```

Фраза:

```text
7 fresh test products
```

не является исключением. Тестовые товары также находятся в рабочей Core DB и должны получить barcode либо быть корректно удалены только через разрешённый публичный API, если это специально созданные временные данные и удаление безопасно.

Предпочтительное решение:

```text
сгенерировать недостающие barcode через существующий Core API
```

---

# 2. Текущий статус

```text
STAGE04I_R3_OWNER_CHECK_BLOCKED_7_PRODUCTS_WITHOUT_BARCODE
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04I_R4_FINAL_BARCODE_BACKFILL_READY_FOR_OWNER_CHECK
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
оставлять товары без barcode
назначать barcode напрямую через Inventory DB
использовать direct DB access из inventory-sales-module
перезаписывать существующие barcode
удалять реальные товары
выполнять DROP TABLE
использовать Base.metadata.drop_all/create_all
git add .
git add -A
git add -u
git commit --amend
git reset
git clean
rebase
force push
коммитить runtime DB/temp/cache
```

Допустимо:

```text
использовать Core API generate-missing
использовать служебный read-only audit внутри Core container
исправить баг генератора, если он обнаружится
добавить regression test
создать docs/report/log
targeted commit/push
```

---

# 4. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE04I_R4_FINAL_BARCODE_BACKFILL_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit\.agents\received_prompts
C:\tbootit
```

Если найден в Downloads:

```powershell
Copy-Item `
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04I_R4_FINAL_BARCODE_BACKFILL_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_R4_FINAL_BARCODE_BACKFILL_PROMPT.md `
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
853c07a202103596017ba993890e6e8d95559ccd
```

Если HEAD другой - указать фактический.

---

# 6. Read-only audit перед backfill

Через Core container или Core API получить:

```text
TOTAL_PRODUCTS_BEFORE
WITH_BARCODE_BEFORE
WITHOUT_BARCODE_BEFORE
DUPLICATES_BEFORE
```

Также вывести 7 товаров без barcode:

```text
id
title/name
sku
status
quantity
storage_location
created_at
```

Нельзя использовать Inventory DB access.

Ожидаемое исходное значение:

```text
WITHOUT_BARCODE_BEFORE = 7
```

Если другое - зафиксировать фактическое.

---

# 7. Выполнить backfill только через Core

Вызвать:

```text
POST /api/products/barcodes/generate-missing
```

Зафиксировать response:

```text
processed
generated
skipped_existing
errors
```

Ожидаемо:

```text
generated = количество товаров без barcode
errors = []
```

Существующие barcode не должны измениться.

Перед backfill сохранить контрольную выборку минимум из 5 существующих:

```text
product_id
barcode_before
```

После backfill проверить:

```text
barcode_after == barcode_before
```

---

# 8. Повторный read-only audit

После первого backfill:

```text
TOTAL_PRODUCTS_AFTER
WITH_BARCODE_AFTER
WITHOUT_BARCODE_AFTER
DUPLICATES_AFTER
```

Обязательное ожидаемое состояние:

```text
WITHOUT_BARCODE_AFTER = 0
DUPLICATES_AFTER = 0
WITH_BARCODE_AFTER = TOTAL_PRODUCTS_AFTER
```

Также проверить:

```text
каждый barcode непустой
каждый barcode соответствует принятому формату
существующий unique index активен
```

---

# 9. Идемпотентность

Повторно вызвать:

```text
POST /api/products/barcodes/generate-missing
```

Ожидаемо:

```text
generated = 0
errors = []
WITHOUT_BARCODE = 0
DUPLICATES = 0
```

---

# 10. Strict lookup smoke

Выбрать один из 7 ранее пустых товаров, получивший новый barcode.

Зафиксировать:

```text
PRODUCT_ID
NEW_BARCODE
SKU
```

Проверить:

```text
GET /api/products/by-barcode/{NEW_BARCODE} -> 200, правильный product_id
GET /api/products/by-barcode/{SKU} -> 404
GET /api/products/by-barcode/{PRODUCT_ID} -> 404
```

Generic search:

```text
GET /api/products?q={SKU} -> товар найден
GET /api/products?q={PRODUCT_ID} -> товар найден
```

---

# 11. Scanner smoke нового barcode

Для товара, который реально доступен к продаже:

```text
status = in_stock или available
quantity > 0
storage_location = store
```

Проверить новый barcode через:

```text
POST /cart/scan
```

Ожидаемо:

```text
товар добавлен
нет 500
поле scanner остаётся рабочим
```

Если среди 7 товаров нет продаваемого, выбрать другой товар после общего backfill.

Также кратко повторно проверить:

```text
reserved -> blocked
wrong location -> blocked
unknown -> blocked
```

---

# 12. Price-tag smoke

Открыть ценник товара с новым barcode:

```text
/products/{id}/price-tag/58x40
```

Проверить:

```text
HTTP 200
barcode SVG присутствует
цифровой barcode присутствует
@page 58mm 40mm
цена присутствует
гарантия присутствует
```

---

# 13. Fresh tests

Выполнить:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Указать единственные финальные фактические числа.

Если код не изменялся, тесты всё равно обязательны.

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

# 15. Документация

Создать:

```text
docs/stage04i_r4_final_barcode_backfill.md
reports/stage04i_r4_final_barcode_backfill_report.md
```

Обновить:

```text
logs/2026-07-23.md
```

Report structure:

```text
# Stage04I-R4 Final Barcode Backfill Report

## STATUS

## PREFLIGHT

## BEFORE_BACKFILL

TOTAL_PRODUCTS:
WITH_BARCODE:
WITHOUT_BARCODE:
DUPLICATES:

## PRODUCTS_WITHOUT_BARCODE

## CONTROL_SAMPLE_EXISTING_BARCODES

## FIRST_BACKFILL

processed:
generated:
skipped_existing:
errors:

## AFTER_BACKFILL

TOTAL_PRODUCTS:
WITH_BARCODE:
WITHOUT_BARCODE:
DUPLICATES:

## EXISTING_BARCODES_UNCHANGED

## SECOND_BACKFILL

generated:
errors:

## STRICT_LOOKUP_SMOKE

## SCANNER_SMOKE

## PRICE_TAG_SMOKE

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

Если код не менялся, коммитить только:

```powershell
git add docs/stage04i_r4_final_barcode_backfill.md
git add reports/stage04i_r4_final_barcode_backfill_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04I_R4_FINAL_BARCODE_BACKFILL_PROMPT.md
git add -f logs/2026-07-23.md
```

Если исправлялся код - добавить только конкретные файлы.

Коммит:

```powershell
git commit -m "Complete barcode backfill for Stage 04I"
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
все товары имеют barcode
WITHOUT_BARCODE = 0
DUPLICATES = 0
существующие barcode не изменились
first bulk generated missing count
second bulk generated = 0
strict barcode lookup работает
SKU/ID через by-barcode отклоняются
scanner нового barcode работает
reserved блокируется
wrong location блокируется
price tag нового barcode работает
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

# 18. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R4_FINAL_BARCODE_BACKFILL_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

При проблеме:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R4_FINAL_BARCODE_BACKFILL_FAIL

BLOCKERS:
...
```
