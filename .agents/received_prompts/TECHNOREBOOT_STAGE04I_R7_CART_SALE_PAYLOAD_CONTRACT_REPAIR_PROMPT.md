# PROMPT — Техноребут / Stage04I-R7 Cart and Sale Payload Contract Repair

## Роль

Ты senior FastAPI engineer, fullstack bugfix developer, API-contract auditor, специалист по продажам и корзине, Docker runtime validator и release QA проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить два критических регрессионных дефекта, обнаруженных владельцем при ручной проверке Stage04I.

Новый функциональный этап не начинать.

---

# 1. Ошибки владельца

## Ошибка 1 — оформление продажи из корзины

В UI появляется:

```text
Ошибка
[{
  'type': 'missing',
  'loc': ['body', 'total_amount'],
  'msg': 'Field required',
  'input': {
    'customer_id': None,
    'payment_method': 'sbp',
    'comment': '',
    'warranty_days': 30,
    'warranty_enabled': True,
    'items': [{
      'product_id': 46,
      'title': 'Report Test Product 43bdfedf',
      'price': 1000.0,
      'quantity': 1
    }]
  }
}]
```

Фактический результат:

```text
Продажа не создаётся.
Core требует total_amount, но Inventory payload его не отправляет.
```

## Ошибка 2 — добавление товара в корзину из списка товаров

При нажатии действия продажи/добавления в корзину:

```json
{
  "detail": [{
    "type": "missing",
    "loc": ["body", "price"],
    "msg": "Field required",
    "input": null
  }]
}
```

Фактический результат:

```text
Товар не добавляется в корзину.
Маршрут или API-клиент требует price в body, но UI отправляет пустой запрос.
```

---

# 2. Текущий статус

```text
STAGE04I_OWNER_CHECK_FAILED_CART_AND_SALE_API_CONTRACT_REGRESSION
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04I_R7_CART_SALE_CONTRACT_REPAIRED_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Архитектурные правила

```text
Core API + DB является источником истины.
inventory-sales-module работает с Core только через HTTP.
Прямой доступ Inventory к Core DB запрещён.
Итог продажи должен рассчитываться из фактических строк продажи.
Клиентский total_amount нельзя слепо считать доверенным источником истины.
Цена товара должна получаться из Core или явно передаваться как ручная цена пользователя.
Пустой POST body не должен приводить к 422 при обычном действии "Добавить в корзину".
```

---

# 4. Запреты

Запрещено:

```text
начинать следующий этап
обходить ошибку жёстко заданным total_amount
доверять клиентскому total_amount без пересчёта
создавать продажу с total_amount = 0
использовать direct DB access из inventory-sales-module
менять рабочую DB тестами
запускать небезопасный docker compose exec core pytest
использовать drop_all
использовать DROP TABLE
использовать массовый DELETE
git add .
git add -A
git add -u
git commit --amend
git reset
git clean
rebase
force push
коммитить DB/temp/cache
```

Core tests запускать только безопасным способом:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

---

# 5. Prompt discovery

Найти только:

```text
TECHNOREBOOT_STAGE04I_R7_CART_SALE_PAYLOAD_CONTRACT_REPAIR_PROMPT.md
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
  C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04I_R7_CART_SALE_PAYLOAD_CONTRACT_REPAIR_PROMPT.md `
  C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_R7_CART_SALE_PAYLOAD_CONTRACT_REPAIR_PROMPT.md `
  -Force
```

В отчёте указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
PROMPT_SHA256:
```

---

# 6. Preflight

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -15
git diff --name-status
git diff --stat
docker compose ps
```

Ожидаемый исходный HEAD:

```text
69ee92686b49e2c39ecb6a2643d4c795a6c5af23
```

Если фактический HEAD другой — зафиксировать.

---

# 7. Защитить рабочую DB перед изменениями

Зафиксировать live DB до тестов:

```text
DB_SHA256_BEFORE
PRODUCT_COUNT_BEFORE
BARCODE_COUNT_BEFORE
SALE_COUNT_BEFORE
```

Использовать read-only audit.

Не создавать runtime записи до завершения анализа API-контрактов.

---

# 8. Воспроизведение ошибки 1

Открыть:

```text
http://localhost:8030/cart
```

Добавить доступный товар.

Оформить продажу с:

```text
payment_method = sbp
warranty_enabled = true
warranty_days = 30
customer_id = null
comment = ""
```

Зафиксировать:

```text
Inventory route
Inventory payload
Core endpoint
Core response status
Core response body
```

Подтвердить 422:

```text
loc = body.total_amount
```

---

# 9. Анализ контракта продажи

Проверить:

```text
core/app/schemas.py
core/app/routers/sales.py
core/app/models.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/cart.py
inventory-sales-module/app/routers/sales.py
inventory-sales-module/app/templates/cart.html
inventory-sales-module/app/templates/sales_new.html
```

Найти:

```text
SaleCreate
SaleItemCreate
total_amount
price
quantity
payment_method
warranty fields
```

Ответить:

```text
Почему Core требует total_amount?
Кто должен вычислять итог?
Есть ли дублирование расчёта?
Есть ли проверка суммы по строкам?
```

---

# 10. Правильный контракт total_amount

Предпочтительная архитектура:

```text
Core самостоятельно вычисляет:
total_amount = sum(item.price * item.quantity)
```

Допустимые варианты:

## Вариант A — рекомендуемый

В Core schema:

```text
total_amount становится optional или исключается из обязательного create payload.
```

В Core router/service:

```python
calculated_total = sum(item.price * item.quantity for item in payload.items)
```

Именно `calculated_total` сохраняется в Sale.

## Вариант B — совместимость

Inventory отправляет `total_amount`, но Core всё равно:

```text
пересчитывает сумму;
сравнивает с клиентской;
не доверяет расхождению;
сохраняет серверный результат.
```

Выбрать наиболее безопасный вариант с минимальным breaking change.

Нельзя:

```text
просто добавить total_amount в UI без серверной проверки.
```

---

# 11. Валидация строк продажи

Core обязан проверить:

```text
items не пустой
quantity > 0
price >= 0
product существует
product доступен
достаточный остаток
один product_id не дублируется неконтролируемо
итог совпадает с рассчитанным
```

Если цена может быть ручной:

```text
она должна передаваться явно в строке продажи;
быть валидирована;
сохраняться в SaleItem;
не менять Product.sale_price автоматически.
```

---

# 12. Воспроизведение ошибки 2

Открыть:

```text
http://localhost:8030/products
```

На доступном товаре нажать:

```text
Продать
Добавить в корзину
```

Зафиксировать:

```text
HTML form action
HTTP method
form fields
Inventory route signature
CoreClient call
response status/body
```

Подтвердить ошибку:

```text
loc = body.price
input = null
```

---

# 13. Исправление добавления в корзину

Обычное действие «Добавить в корзину» не должно требовать JSON body с `price`.

Правильные варианты:

## Вариант A — рекомендуемый

Маршрут:

```text
POST /cart/add/{product_id}
```

Inventory получает товар из Core:

```text
id
title
sale_price/price
quantity
status
storage_location
```

В корзину записывается текущая цена товара.

## Вариант B — ручная цена

Если действие предусматривает ручную цену:

```text
форма должна явно содержать price;
price передаётся как Form field;
отсутствие price должно использовать текущую цену Core.
```

Нельзя:

```text
обязательный Body(price) для HTML form с пустым POST.
```

---

# 14. Унификация цены

Проверить, какое поле является актуальным:

```text
price
sale_price
```

Не допускать ситуации:

```text
один маршрут читает product.price;
другой product.sale_price;
третий требует body.price.
```

Определить единый контракт и документировать.

Поддержать обратную совместимость, если старые response schemas используют другое имя.

---

# 15. Корзина и scanner flow

После исправления проверить оба пути:

```text
1. Добавление из списка товаров.
2. Добавление по barcode через scanner.
```

Оба пути должны создавать одинаковую структуру строки корзины:

```json
{
  "product_id": 46,
  "title": "...",
  "price": 1000.0,
  "quantity": 1
}
```

Не должно быть различий в обязательных полях.

---

# 16. Payment method SBP

Проверить, что:

```text
sbp
```

является допустимым payment method во всех слоях:

```text
HTML select
Inventory schema
Core schema
Core model
reports payment breakdown
receipt
```

Ошибка `total_amount` не должна скрывать дополнительную ошибку payment method.

---

# 17. Warranty contract

Проверить payload:

```text
warranty_enabled = true
warranty_days = 30
```

И сценарий:

```text
warranty_enabled = false
warranty_days = null
```

Оба должны создавать продажу без 422.

---

# 18. Core tests

Создать/обновить:

```text
core/tests/test_sales_payload_contract.py
```

Покрыть:

```text
1. SaleCreate без total_amount успешно создаёт продажу.
2. Core вычисляет total_amount по строкам.
3. Несколько строк суммируются правильно.
4. quantity учитывается в сумме.
5. Клиентский total_amount не может подменить серверный итог.
6. Пустые items отклоняются.
7. quantity <= 0 отклоняется.
8. price < 0 отклоняется.
9. payment_method=sbp принимается.
10. warranty 30 дней принимается.
11. без гарантии принимается.
12. stock списывается ровно один раз.
```

Если total_amount остаётся обязательным ради совместимости:

```text
добавить отдельный тест пересчёта и несовпадения.
```

---

# 19. Inventory tests — cart add

Создать/обновить:

```text
inventory-sales-module/tests/test_cart_add_contract.py
```

Покрыть:

```text
1. POST add product без body.price не возвращает 422.
2. Цена берётся из Core.
3. Товар добавляется в session cart.
4. Недоступный товар блокируется.
5. quantity=0 блокируется.
6. reserved блокируется.
7. wrong location блокируется.
8. повторное добавление корректно увеличивает quantity или не дублирует уникальный товар.
9. HTML form содержит правильный action/method.
10. Ошибки показываются по-русски.
```

---

# 20. Inventory tests — checkout

Создать/обновить:

```text
inventory-sales-module/tests/test_cart_checkout_contract.py
```

Покрыть:

```text
1. checkout payload содержит все нужные поля.
2. total_amount не обязателен на стороне UI, если считает Core.
3. payment_method=sbp.
4. warranty_enabled=true / 30 days.
5. no warranty.
6. успешный redirect на sale detail/receipt.
7. после успеха корзина очищается.
8. при ошибке корзина не очищается.
9. Core 422 показывается в читаемом виде.
```

---

# 21. Regression tests

Не сломать:

```text
scanner barcode add
ручная продажа через /sales/new
sale cancellation
stock return
reissue
sales reports
receipt
price tag
```

Особенно проверить:

```text
canceled/superseded не входят в отчёт
reissued входит ровно один раз
```

---

# 22. Docker rebuild

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose up -d avito-module
docker compose ps
```

---

# 23. Безопасные тесты

Core:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
```

Inventory:

```powershell
docker compose exec -T inventory-sales-module pytest
```

Avito:

```powershell
docker compose exec -T avito-module pytest
```

После Core tests проверить, что live DB не изменилась:

```text
DB_SHA256_AFTER_TESTS
PRODUCT_COUNT_AFTER_TESTS
BARCODE_COUNT_AFTER_TESTS
SALE_COUNT_AFTER_TESTS
```

---

# 24. Runtime smoke — добавление из списка товаров

Использовать реальный доступный товар.

Если Product ID 46 существует и доступен, воспроизвести на нём. Иначе выбрать другой.

Зафиксировать:

```text
PRODUCT_ID
PRODUCT_TITLE
PRODUCT_PRICE
STATUS
QUANTITY
STORAGE_LOCATION
```

Нажать «Добавить в корзину».

Ожидаемо:

```text
HTTP 200/303
нет 422 body.price
строка появилась в корзине
цена корректна
quantity = 1
```

---

# 25. Runtime smoke — scanner add

Ввести barcode того же товара.

Ожидаемо:

```text
используется та же цена;
структура cart item идентична;
нет дублирования уникального товара;
нет 422.
```

---

# 26. Runtime smoke — checkout SBP

Из корзины оформить продажу:

```text
payment_method = sbp
warranty_enabled = true
warranty_days = 30
```

Зафиксировать:

```text
SALE_ID
ITEMS
CALCULATED_TOTAL
SAVED_TOTAL
PAYMENT_METHOD
WARRANTY_ENABLED
WARRANTY_DAYS
HTTP_STATUS
REDIRECT_TARGET
```

Ожидаемо:

```text
нет 422 total_amount
SALE создана
SAVED_TOTAL = sum(price * quantity)
payment_method = sbp
товар списан
корзина очищена
```

---

# 27. Runtime smoke — no warranty

Создать отдельную тестовую продажу или отменить/вернуть предыдущую безопасным flow.

Проверить:

```text
warranty_enabled = false
warranty_days = null
```

Ожидаемо:

```text
продажа создаётся
чек показывает "Без гарантии"
```

---

# 28. Runtime regression — cancel/reissue

Для созданной продажи:

```text
отменить;
проверить возврат остатка;
проверить уменьшение отчёта;
выполнить reissue;
проверить old/new linkage;
проверить сумму отчёта.
```

---

# 29. Safety scans

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core/app core/tests inventory-sales-module/app inventory-sales-module/tests
```

Ожидаемо:

```text
0 matches
```

Также:

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

# 30. Документация

Создать:

```text
docs/stage04i_r7_cart_sale_payload_contract_repair.md
reports/stage04i_r7_cart_sale_payload_contract_repair_report.md
```

Обновить:

```text
logs/2026-08-03.md
```

Report structure:

```text
# Stage04I-R7 Cart and Sale Payload Contract Repair Report

## STATUS

## OWNER_REPORTED_ERRORS

### Missing total_amount
### Missing price

## ROOT_CAUSE

## API_CONTRACT_BEFORE

## API_CONTRACT_AFTER

## TOTAL_AMOUNT_CALCULATION

## CART_PRICE_SOURCE

## SBP_AND_WARRANTY

## TESTS

Core safe:
Inventory:
Avito:

## LIVE_DB_PRESERVATION

Before:
After:

## RUNTIME_CART_ADD

## RUNTIME_SCANNER_ADD

## RUNTIME_CHECKOUT_SBP

## RUNTIME_NO_WARRANTY

## RUNTIME_CANCEL_REISSUE

## SAFETY_SCAN

## FILES_CHANGED

## COMMIT

## PUSH

## FINAL_GIT_STATUS

## OWNER_RECHECK_GUIDE

## FINAL_STATUS
```

---

# 31. Git

Только targeted add.

Возможные файлы:

```powershell
git add core/app/schemas.py
git add core/app/routers/sales.py
git add core/tests/test_sales_payload_contract.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/cart.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/templates/cart.html
git add inventory-sales-module/tests/test_cart_add_contract.py
git add inventory-sales-module/tests/test_cart_checkout_contract.py

git add docs/stage04i_r7_cart_sale_payload_contract_repair.md
git add reports/stage04i_r7_cart_sale_payload_contract_repair_report.md
git add logs/2026-08-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04I_R7_CART_SALE_PAYLOAD_CONTRACT_REPAIR_PROMPT.md
```

Если log ignored:

```powershell
git add -f logs/2026-08-03.md
```

Коммит:

```powershell
git commit -m "Repair cart and sale payload contracts"
git push origin main
```

После push:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 32. Definition of Done

Готово только если:

```text
добавление товара из products работает;
нет 422 missing body.price;
scanner add работает;
оба пути создают одинаковую cart item;
checkout из корзины работает;
нет 422 missing total_amount;
Core рассчитывает итог;
SBP принимается;
warranty 30 days работает;
no warranty работает;
товар списывается ровно один раз;
корзина очищается только после успеха;
cancel работает;
stock return работает;
reissue работает;
reports корректны;
Core safe tests PASS;
Inventory tests PASS;
Avito tests PASS;
live DB не меняется от tests;
destructive scans clean;
targeted commit;
push;
clean Git;
owner manual recheck required.
```

---

# 33. Финальный статус

Успех:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R7_CART_SALE_CONTRACT_REPAIRED_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

При проблеме:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04I_R7_CART_SALE_CONTRACT_REPAIR_FAIL

BLOCKERS:
...
```
