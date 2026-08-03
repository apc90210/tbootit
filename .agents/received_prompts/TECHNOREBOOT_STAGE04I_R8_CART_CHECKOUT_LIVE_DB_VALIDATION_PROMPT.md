# PROMPT — Техноребут / Stage04I-R8 Final Cart Checkout and Live DB Consistency Validation

## Роль

Ты senior release auditor, FastAPI runtime validator, API-contract QA engineer и специалист по целостности Core DB проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Нужно выполнить финальную проверку исправлений Stage04I-R7. Новый функционал не добавлять.

---

# 1. Почему R7 пока не принят

R7 сообщил:

```text
Runtime checkout создал Sale ID 34.
```

Но далее тот же отчёт утверждает:

```text
Sales: 33
DB SHA256 после тестов и edits полностью совпал с исходным.
```

Это противоречие.

Возможны варианты:

```text
runtime smoke работал не с live DB;
продажа была удалена/откачена;
hash был снят до runtime smoke;
использовалась другая DB;
отчёт содержит неверные значения.
```

Также prompt R7 требовал, но отчёт не приводит runtime-доказательства:

```text
продажа без гарантии;
отмена созданной продажи;
возврат товара;
reissue;
корректность отчёта после cancel/reissue.
```

---

# 2. Текущий статус

```text
STAGE04I_R7_BLOCKED_RUNTIME_DB_COUNTS_INCONSISTENT_AND_ACCEPTANCE_FLOW_INCOMPLETE
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04I_R8_CART_CHECKOUT_LIVE_DB_VALIDATED_READY_FOR_OWNER_RECHECK
```

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
менять API-контракт без найденного нового бага
удалять runtime-продажи напрямую из DB
использовать DELETE FROM
использовать drop_all
использовать direct DB access из Inventory
запускать небезопасный core pytest
git add .
git add -A
git add -u
git reset
git clean
git rebase
force push
commit --amend
коммитить DB/temp/cache
```

Core tests запускать только:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

---

# 4. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE04I_R8_CART_CHECKOUT_LIVE_DB_VALIDATION_PROMPT.md
```

Если найден в Downloads, скопировать в:

```text
C:\tbootit\.agents\received_prompts\
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
docker compose ps
```

Ожидаемый исходный HEAD:

```text
bfdf26cfdec20f9fb5b7a7d2d8bbe3d14a0b8762
```

---

# 6. Определить единственную live DB

Зафиксировать:

```text
DATABASE_URL Core container
LIVE_DB_PATH
bind mount source
bind mount destination
```

Ожидаемо:

```text
/data/db/technoreboot.db
C:\tbootit\data\db\technoreboot.db
```

Проверить, что Inventory HTTP-запросы направлены в этот Core.

---

# 7. Состояние live DB до runtime

Снять read-only показатели:

```text
LIVE_DB_SHA256_BEFORE
PRODUCT_COUNT_BEFORE
BARCODE_COUNT_BEFORE
SALE_COUNT_BEFORE
MAX_SALE_ID_BEFORE
REPORT_TOTAL_BEFORE
```

Также записать последние 5 sale IDs и statuses.

Важно:

```text
hash снимается непосредственно перед runtime checkout;
counts снимаются из той же DB.
```

---

# 8. Runtime add from products

Через реальный HTTP UI маршрут:

```text
POST /cart/add
```

Использовать доступный товар.

Зафиксировать:

```text
PRODUCT_ID
PRODUCT_PRICE
HTTP_STATUS
REDIRECT
CART_ITEM
```

Ожидаемо:

```text
нет 422 body.price;
цена получена из Core;
товар появился в корзине.
```

---

# 9. Runtime checkout: SBP + 30 дней

Оформить продажу:

```text
payment_method = sbp
warranty_enabled = true
warranty_days = 30
```

Зафиксировать:

```text
SALE_ID
HTTP_STATUS
REDIRECT
SAVED_TOTAL
CALCULATED_TOTAL
PAYMENT_METHOD
WARRANTY_ENABLED
WARRANTY_DAYS
CART_EMPTY_AFTER_SUCCESS
```

Ожидаемо:

```text
нет 422 total_amount;
SAVED_TOTAL = CALCULATED_TOTAL;
sale существует в live DB.
```

Сразу после создания снять:

```text
SALE_COUNT_AFTER_SBP
MAX_SALE_ID_AFTER_SBP
REPORT_TOTAL_AFTER_SBP
LIVE_DB_SHA256_AFTER_SBP
```

Ожидаемо:

```text
SALE_COUNT_AFTER_SBP = SALE_COUNT_BEFORE + 1
MAX_SALE_ID_AFTER_SBP = SALE_ID
REPORT_TOTAL_AFTER_SBP = REPORT_TOTAL_BEFORE + SAVED_TOTAL
hash изменился, потому что live DB получила новую продажу.
```

Если hash не изменился, объяснить точную причину.

---

# 10. Runtime checkout: без гарантии

Использовать другой доступный товар либо безопасно завершить предыдущий цикл через отмену.

Оформить:

```text
warranty_enabled = false
warranty_days = null
```

Зафиксировать:

```text
NO_WARRANTY_SALE_ID
HTTP_STATUS
SALE_STATUS
WARRANTY_ENABLED
WARRANTY_DAYS
RECEIPT_TEXT
```

Ожидаемо:

```text
продажа создаётся;
нет 422;
чек содержит "Без гарантии" или утверждённый текст.
```

---

# 11. Runtime cancel

Отменить SBP-продажу через публичный Core/Inventory flow.

Зафиксировать:

```text
ORIGINAL_SALE_ID
STATUS_AFTER_CANCEL
PRODUCT_STATUS_AFTER_CANCEL
PRODUCT_QUANTITY_AFTER_CANCEL
REPORT_TOTAL_AFTER_CANCEL
PAYMENT_SBP_AFTER_CANCEL
```

Ожидаемо:

```text
status = canceled;
товар возвращён;
сумма продажи исключена;
SBP bucket уменьшен на сумму продажи.
```

Повторная отмена:

```text
HTTP 409
```

---

# 12. Runtime reissue

Выполнить reissue отменённой продажи.

Зафиксировать:

```text
REISSUED_SALE_ID
ORIGINAL_STATUS
REISSUED_STATUS
SOURCE_SALE_ID
SUPERSEDED_BY_SALE_ID
REPORT_TOTAL_AFTER_REISSUE
PAYMENT_BUCKET_AFTER_REISSUE
```

Ожидаемо:

```text
original = superseded;
new = reissued;
двусторонняя связь корректна;
новая продажа входит в отчёт ровно один раз;
superseded не входит.
```

---

# 13. Live DB consistency after runtime

Снять:

```text
LIVE_DB_SHA256_AFTER_RUNTIME
PRODUCT_COUNT_AFTER_RUNTIME
BARCODE_COUNT_AFTER_RUNTIME
SALE_COUNT_AFTER_RUNTIME
MAX_SALE_ID_AFTER_RUNTIME
```

Объяснить изменение sale count с учётом:

```text
SBP sale;
no-warranty sale;
reissued sale.
```

Не заявлять, что DB не изменилась после runtime, если были созданы продажи.

Разделить доказательства:

```text
A. Safe tests не меняют live DB.
B. Runtime business operations ожидаемо меняют live DB.
```

---

# 14. Safe test preservation proof

После runtime-сценариев снять:

```text
LIVE_DB_SHA256_BEFORE_TESTS
COUNTS_BEFORE_TESTS
```

Запустить:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
```

После:

```text
LIVE_DB_SHA256_AFTER_TESTS
COUNTS_AFTER_TESTS
```

Ожидаемо:

```text
hash и counts до/после tests идентичны.
```

Именно это является доказательством test isolation.

---

# 15. Проверка UI владельца

Проверить фактически:

```text
/products → "В корзину"
/cart → оформление
/sales/{id}
/sales/{id}/receipt
/sales/{id}/cancel
/sales/{id}/reissue
/reports/sales
```

Все страницы:

```text
не возвращают 422/500;
имеют русские сообщения;
ссылки "На главную" и "К списку товаров" работают.
```

---

# 16. Полный regression

Финальные числа:

```text
Core safe tests
Inventory tests
Avito tests
```

Не использовать результаты предыдущего запуска.

---

# 17. Safety scans

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests
```

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|__pycache__|\.pytest_cache"
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 18. Документация

Создать:

```text
docs/stage04i_r8_cart_checkout_live_db_validation.md
reports/stage04i_r8_cart_checkout_live_db_validation_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report:

```text
# Stage04I-R8 Cart Checkout and Live DB Validation Report

## STATUS
## WHY_R7_WAS_NOT_ACCEPTED
## LIVE_DB_IDENTITY
## BEFORE_RUNTIME
## ADD_FROM_PRODUCTS
## CHECKOUT_SBP
## CHECKOUT_NO_WARRANTY
## CANCEL
## REISSUE
## REPORT_INTEGRITY
## AFTER_RUNTIME
## SAFE_TEST_PRESERVATION
## UI_LINKS
## FINAL_TESTS
## SAFETY_SCAN
## FILES_CHANGED
## COMMIT
## PUSH
## FINAL_GIT_STATUS
## OWNER_RECHECK_GUIDE
## FINAL_STATUS
```

---

# 19. Git

Если код не менялся, коммитить только prompt/docs/report/log.

Только targeted add:

```powershell
git add docs/stage04i_r8_cart_checkout_live_db_validation.md
git add reports/stage04i_r8_cart_checkout_live_db_validation_report.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04I_R8_CART_CHECKOUT_LIVE_DB_VALIDATION_PROMPT.md
git add -f logs/2026-08-03.md
```

Если найден новый баг, добавить только изменённые файлы и тесты.

Коммит:

```powershell
git commit -m "Validate cart checkout against live Core database"
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 20. Definition of Done

```text
add from products works
no missing body.price
SBP checkout works
no missing total_amount
Core total is server-calculated
sale count increases in live DB
report total increases correctly
no-warranty checkout works
receipt text correct
cancel restores stock
cancel removes revenue
double cancel blocked
reissue linkage correct
reissued included once
live DB runtime changes are honestly reported
safe tests do not change live DB
Core safe tests PASS
Inventory PASS
Avito PASS
UI navigation links work
safety scans clean
targeted commit
push
clean Git
owner recheck required
```

---

# 21. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R8_CART_CHECKOUT_LIVE_DB_VALIDATED_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Проблема:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R8_CART_CHECKOUT_LIVE_DB_VALIDATION_FAIL

BLOCKERS:
...
```
